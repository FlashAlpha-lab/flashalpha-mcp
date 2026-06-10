"""Exercise the new FlashAlpha MCP tool families: strategy signals, earnings
analytics, and multi-leg structure math — over the hosted Streamable-HTTP MCP server.

What it does:
  1. get_strategy(strategy="flow_anomaly")  -> uniform strategy-decision envelope
  2. get_earnings_calendar(days=7)          -> upcoming earnings with expected moves
  3. post_structure_pnl(legs=...)           -> P&L curve for a short call spread

Usage:
    python strategy_earnings_structures.py YOUR_API_KEY
    FLASHALPHA_API_KEY=key python strategy_earnings_structures.py
"""

import json
import os
import sys

try:
    import requests
except ImportError:
    print("Error: 'requests' is not installed. Run: pip install requests")
    sys.exit(1)

MCP_URL = "https://lab.flashalpha.com/mcp"
TICKER = os.environ.get("TEST_TICKER", "SPY")


def get_api_key() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    key = os.environ.get("FLASHALPHA_API_KEY", "")
    if not key:
        print(
            "Error: No API key provided.\n"
            "Usage: python strategy_earnings_structures.py YOUR_API_KEY\n"
            "   or: FLASHALPHA_API_KEY=key python strategy_earnings_structures.py"
        )
        sys.exit(1)
    return key


def call_tool(session: requests.Session, name: str, arguments: dict) -> dict:
    """Send a JSON-RPC 2.0 tools/call request and return the parsed result."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    resp = session.post(MCP_URL, json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        err = body["error"]
        raise RuntimeError(f"RPC error {err.get('code')}: {err.get('message')}")
    return body.get("result", {})


def text_of(result: dict) -> str:
    parts = [
        item.get("text", "")
        for item in result.get("content", [])
        if isinstance(item, dict) and item.get("type") == "text"
    ]
    return "\n".join(parts)


def main() -> None:
    api_key = get_api_key()
    base = {"apiKey": api_key}

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    print(f"== Strategy signal: flow_anomaly on {TICKER} ==")
    res = call_tool(session, "get_strategy", {**base, "ticker": TICKER, "strategy": "flow_anomaly"})
    print(text_of(res) or json.dumps(res)[:600])

    print("\n== Earnings calendar (next 7 days) ==")
    res = call_tool(session, "get_earnings_calendar", {**base, "days": 7})
    print(text_of(res) or json.dumps(res)[:600])

    print(f"\n== Structure P&L: short {TICKER} call spread ==")
    res = call_tool(
        session,
        "post_structure_pnl",
        {
            **base,
            "legs": [
                {"action": "sell", "type": "call", "strike": 580, "premium": 5.0, "quantity": 1},
                {"action": "buy", "type": "call", "strike": 590, "premium": 2.0, "quantity": 1},
            ],
            "minUnderlying": 550,
            "maxUnderlying": 610,
            "points": 50,
        },
    )
    print(text_of(res) or json.dumps(res)[:600])


if __name__ == "__main__":
    main()
