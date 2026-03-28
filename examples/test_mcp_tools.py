"""Test all FlashAlpha MCP tools via HTTP.

Usage:
    python test_mcp_tools.py YOUR_API_KEY
    FLASHALPHA_API_KEY=key python test_mcp_tools.py
"""

import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("Error: 'requests' is not installed. Run: pip install requests")
    sys.exit(1)

MCP_URL = "https://lab.flashalpha.com/mcp"

# Default test ticker. Override with TEST_TICKER env var.
TEST_TICKER = os.environ.get("TEST_TICKER", "SPY")

# A near-term expiry for tools that accept one. Adjust as needed.
TEST_EXPIRY = os.environ.get("TEST_EXPIRY", "")  # Leave empty to use server default.

# A sample strike for greek/IV tests.
TEST_STRIKE = float(os.environ.get("TEST_STRIKE", "540"))
TEST_OPTION_TYPE = os.environ.get("TEST_OPTION_TYPE", "call")
TEST_OPTION_PRICE = float(os.environ.get("TEST_OPTION_PRICE", "5.00"))

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


def get_api_key() -> str:
    """Return API key from CLI arg or environment variable."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    key = os.environ.get("FLASHALPHA_API_KEY", "")
    if not key:
        print(
            "Error: No API key provided.\n"
            "Usage: python test_mcp_tools.py YOUR_API_KEY\n"
            "   or: FLASHALPHA_API_KEY=key python test_mcp_tools.py"
        )
        sys.exit(1)
    return key


def call_tool(session: requests.Session, tool_name: str, arguments: dict) -> dict:
    """Send a JSON-RPC 2.0 tools/call request to the MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    response = session.post(MCP_URL, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_text(result: dict) -> str:
    """Pull the text content from a tools/call result."""
    content = result.get("result", {}).get("content", [])
    parts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(item.get("text", ""))
    return "\n".join(parts)


def run_test(
    session: requests.Session,
    tool_name: str,
    arguments: dict,
    description: str,
) -> str:
    """Run a single tool test and return PASS/FAIL."""
    print(f"  Testing {tool_name}: {description} ... ", end="", flush=True)
    try:
        result = call_tool(session, tool_name, arguments)
        if "error" in result:
            err = result["error"]
            print(f"{FAIL} — RPC error {err.get('code')}: {err.get('message')}")
            return FAIL
        text = extract_text(result)
        if not text:
            # Some tools return structured content. Accept non-empty result.
            if result.get("result"):
                print(PASS)
                return PASS
            print(f"{FAIL} — empty response")
            return FAIL
        preview = text[:120].replace("\n", " ")
        print(f"{PASS} — {preview}")
        return PASS
    except requests.exceptions.Timeout:
        print(f"{FAIL} — request timed out")
        return FAIL
    except requests.exceptions.HTTPError as exc:
        print(f"{FAIL} — HTTP {exc.response.status_code}")
        return FAIL
    except Exception as exc:  # noqa: BLE001
        print(f"{FAIL} — {exc}")
        return FAIL


def build_tests(api_key: str) -> list[tuple[str, dict, str]]:
    """Return list of (tool_name, arguments, description) tuples."""
    base = {"apiKey": api_key}
    ticker_args = {**base, "ticker": TEST_TICKER}

    expiry_args = {**ticker_args}
    if TEST_EXPIRY:
        expiry_args["expiry"] = TEST_EXPIRY

    greek_args = {
        **base,
        "ticker": TEST_TICKER,
        "strike": TEST_STRIKE,
        "optionType": TEST_OPTION_TYPE,
    }
    if TEST_EXPIRY:
        greek_args["expiry"] = TEST_EXPIRY

    iv_args = {
        **greek_args,
        "optionPrice": TEST_OPTION_PRICE,
    }

    return [
        ("GetAccount", base, "fetch account and plan info"),
        ("GetTickers", {**base, "query": TEST_TICKER}, f"search for '{TEST_TICKER}'"),
        ("GetStockQuote", ticker_args, f"live quote for {TEST_TICKER}"),
        ("GetOptionChain", expiry_args, f"option chain for {TEST_TICKER}"),
        ("GetGex", expiry_args, f"gamma exposure for {TEST_TICKER}"),
        ("GetDex", expiry_args, f"delta exposure for {TEST_TICKER}"),
        ("GetVex", expiry_args, f"vanna exposure for {TEST_TICKER}"),
        ("GetLevels", ticker_args, f"key levels (call wall, put wall, flip) for {TEST_TICKER}"),
        ("GetExposureSummary", ticker_args, f"aggregate GEX/DEX/VEX/CHEX for {TEST_TICKER}"),
        ("GetNarrative", ticker_args, f"positioning narrative for {TEST_TICKER}"),
        ("GetVolatility", expiry_args, f"IV surface for {TEST_TICKER}"),
        ("GetStockSummary", ticker_args, f"combined summary for {TEST_TICKER}"),
        ("CalculateGreeks", greek_args, f"BS greeks for {TEST_TICKER} {TEST_STRIKE} {TEST_OPTION_TYPE}"),
        ("SolveIV", iv_args, f"solve IV for {TEST_TICKER} {TEST_STRIKE} {TEST_OPTION_TYPE} @ {TEST_OPTION_PRICE}"),
    ]


def main() -> None:
    api_key = get_api_key()

    print(f"FlashAlpha MCP Tool Test")
    print(f"Server : {MCP_URL}")
    print(f"Ticker : {TEST_TICKER}")
    if TEST_EXPIRY:
        print(f"Expiry : {TEST_EXPIRY}")
    print("-" * 60)

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    tests = build_tests(api_key)
    results = []

    for tool_name, arguments, description in tests:
        status = run_test(session, tool_name, arguments, description)
        results.append((tool_name, status))
        # Brief pause to avoid hammering rate limits on free plans.
        time.sleep(0.25)

    print("-" * 60)
    passed = sum(1 for _, s in results if s == PASS)
    failed = sum(1 for _, s in results if s == FAIL)
    total = len(results)
    print(f"Results: {passed}/{total} passed, {failed} failed")

    if failed:
        print("\nFailed tools:")
        for tool_name, status in results:
            if status == FAIL:
                print(f"  - {tool_name}")
        sys.exit(1)
    else:
        print("All tools passed.")


if __name__ == "__main__":
    main()
