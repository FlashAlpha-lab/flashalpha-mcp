# FlashAlpha MCP Server — Real-Time Options Analytics for AI Assistants

Connect Claude, Cursor, Windsurf, or any MCP-compatible AI assistant to live options market data. Access gamma exposure (GEX), delta exposure (DEX), vanna exposure (VEX), charm exposure (CHEX), Black-Scholes greeks, implied volatility, 0DTE analytics, volatility surfaces, dealer positioning, and more — all through natural language.

---

## What Is This

This repository provides documentation, setup instructions, and test scripts for the FlashAlpha MCP server. The server itself runs at `https://lab.flashalpha.com/mcp` and is not open source. It exposes 14 tools covering options analytics, greeks, exposure metrics, and market data through the Model Context Protocol so that AI assistants can answer quantitative finance questions using live data.

---

## Server URL

```
https://lab.flashalpha.com/mcp
```

- **Transport:** Streamable HTTP
- **Protocol version:** MCP 2025-03-26
- **Auth:** API key passed as a parameter on each tool call (see [Authentication](#authentication))

---

## Quick Setup

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "flashalpha": {
      "type": "http",
      "url": "https://lab.flashalpha.com/mcp"
    }
  }
}
```

See `examples/claude_desktop_config.json` for a complete template.

### Claude Code CLI

```bash
claude mcp add flashalpha --transport http https://lab.flashalpha.com/mcp
```

Verify it was added:

```bash
claude mcp list
```

### Cursor

Open **Settings > MCP** and add a new server entry:

```json
{
  "flashalpha": {
    "transport": "http",
    "url": "https://lab.flashalpha.com/mcp"
  }
}
```

See `examples/cursor_settings.json` for the full settings block.

### VS Code (Copilot / Continue)

Add the server to your VS Code MCP settings (`.vscode/mcp.json` or user settings):

```json
{
  "servers": {
    "flashalpha": {
      "type": "http",
      "url": "https://lab.flashalpha.com/mcp"
    }
  }
}
```

See `examples/vscode_mcp_settings.json` for a complete example.

### Windsurf (Cascade > MCP)

Open **Cascade settings**, navigate to **MCP Servers**, and add:

```json
{
  "flashalpha": {
    "transport": "http",
    "url": "https://lab.flashalpha.com/mcp"
  }
}
```

---

## Authentication

Every tool call requires an `apiKey` parameter. Pass your FlashAlpha API key as a string argument to each tool:

```
apiKey: "fa_your_key_here"
```

Get a free API key at [flashalpha.com](https://flashalpha.com).

The key is passed per-call rather than in a header so that it works uniformly across all MCP clients without requiring transport-level configuration.

---

## Available Tools

| Tool | Category | Description |
|---|---|---|
| `GetStockQuote` | Market Data | Real-time or delayed stock quote for a ticker |
| `GetTickers` | Market Data | Search for tickers by name or symbol |
| `GetOptionChain` | Market Data | Full option chain with strikes, expiries, bids, asks, OI, volume |
| `GetAccount` | Account | Account info and subscription plan details |
| `GetGex` | Exposure | Gamma exposure (GEX) by strike and expiry for dealer positioning |
| `GetDex` | Exposure | Delta exposure (DEX) aggregated across the chain |
| `GetVex` | Exposure | Vanna exposure (VEX) — sensitivity of delta to implied volatility |
| `GetLevels` | Exposure | Key price levels derived from dealer exposure (call wall, put wall, zero gamma) |
| `GetExposureSummary` | Exposure | Aggregate exposure summary across GEX, DEX, VEX, and CHEX |
| `GetNarrative` | Exposure | Natural language narrative describing current dealer positioning |
| `GetVolatility` | Volatility | Implied volatility surface, term structure, and skew data |
| `GetStockSummary` | Summary | Combined summary of price, greeks, and exposure for a ticker |
| `CalculateGreeks` | Pricing | Black-Scholes greeks for a given option (delta, gamma, theta, vega, rho) |
| `SolveIV` | Pricing | Solve implied volatility from an observed option price |

---

## Tool Reference

### GetStockQuote

Retrieves the current market price and basic quote data for a stock.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Stock symbol (e.g., `SPY`, `AAPL`) |

Returns: bid, ask, last price, volume, change, change percent.

---

### GetTickers

Searches for tickers matching a query string.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `query` | string | yes | Name or partial symbol to search |

Returns: list of matching tickers with symbol, name, and exchange.

---

### GetOptionChain

Fetches the full option chain for a ticker, including all available expiry dates and strikes.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `expiry` | string | no | Filter to a specific expiry date (YYYY-MM-DD) |
| `strike` | number | no | Filter to a specific strike price |
| `optionType` | string | no | `call`, `put`, or omit for both |

Returns: strikes, expiries, bid, ask, mid, implied volatility, open interest, volume, delta, gamma for each contract.

---

### GetAccount

Returns account details and the active subscription plan.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |

Returns: plan name, rate limits, enabled tools, account status.

---

### GetGex

Returns gamma exposure (GEX) by strike and expiry date. GEX measures the estimated dollar gamma that market makers must hedge, which influences intraday volatility and price pinning behavior.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `expiry` | string | no | Filter to a specific expiry (YYYY-MM-DD) |

Returns: GEX values by strike, aggregate GEX, flip point (zero gamma level), call wall, put wall.

---

### GetDex

Returns delta exposure (DEX) aggregated across all strikes and expiries. DEX represents the net delta that dealers carry and must hedge directionally.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `expiry` | string | no | Filter to a specific expiry (YYYY-MM-DD) |

Returns: aggregate DEX, DEX by strike, directional bias indicator.

---

### GetVex

Returns vanna exposure (VEX) — the second-order greek measuring how delta changes as implied volatility moves. VEX matters most around large IV events like earnings.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `expiry` | string | no | Filter to a specific expiry (YYYY-MM-DD) |

Returns: VEX by strike, aggregate VEX, vanna-weighted exposure profile.

---

### GetLevels

Returns key price levels derived from dealer exposure: call wall, put wall, zero gamma level, and high-gamma strike clusters.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |

Returns: call wall price, put wall price, zero gamma (flip) level, gamma-weighted support and resistance zones.

---

### GetExposureSummary

Returns an aggregate summary of all exposure metrics — GEX, DEX, VEX, and charm exposure (CHEX) — in a single call.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |

Returns: combined GEX, DEX, VEX, and CHEX values with directional and volatility regime interpretation.

---

### GetNarrative

Returns a natural language narrative summarizing current dealer positioning and what it implies for near-term price action.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |

Returns: text narrative describing the exposure regime, key levels, and implied volatility dynamics.

---

### GetVolatility

Returns implied volatility surface data, term structure, and skew for a ticker.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `expiry` | string | no | Filter to a specific expiry (YYYY-MM-DD) |

Returns: IV by strike and expiry, ATM IV, 25-delta skew, term structure, realized vs. implied spread.

---

### GetStockSummary

Returns a combined summary of current price, key greeks, and exposure metrics for a ticker in a single response.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |

Returns: price, ATM IV, GEX, DEX, VEX, CHEX, key levels, and a short positioning narrative.

---

### CalculateGreeks

Computes Black-Scholes greeks for a specified option contract given market inputs.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `strike` | number | yes | Strike price |
| `expiry` | string | yes | Expiry date (YYYY-MM-DD) |
| `optionType` | string | yes | `call` or `put` |
| `spotPrice` | number | no | Spot price override (uses live price if omitted) |
| `volatility` | number | no | IV override as decimal (e.g., `0.25` for 25%) |
| `riskFreeRate` | number | no | Risk-free rate as decimal (defaults to current T-bill rate) |

Returns: delta, gamma, theta (per day), vega, rho, price (theoretical).

---

### SolveIV

Solves implied volatility from an observed market price using numerical inversion of the Black-Scholes formula.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `apiKey` | string | yes | Your FlashAlpha API key |
| `ticker` | string | yes | Underlying stock symbol |
| `strike` | number | yes | Strike price |
| `expiry` | string | yes | Expiry date (YYYY-MM-DD) |
| `optionType` | string | yes | `call` or `put` |
| `optionPrice` | number | yes | Observed market price of the option |
| `spotPrice` | number | no | Spot price override (uses live price if omitted) |
| `riskFreeRate` | number | no | Risk-free rate as decimal |

Returns: implied volatility as a decimal, convergence status, number of iterations.

---

## Example Prompts

Once connected, you can ask your AI assistant questions like these:

1. "What is the current gamma exposure for SPY?"
2. "Where is the zero gamma level for QQQ today?"
3. "Show me the call wall and put wall for AAPL."
4. "What does dealer positioning look like for SPY right now?"
5. "Calculate the delta and gamma for the SPY 540 call expiring this Friday."
6. "What is the implied volatility for TSLA's at-the-money options?"
7. "Give me a narrative of current SPY options market structure."
8. "What is the vanna exposure for NDX ahead of FOMC?"
9. "Solve the implied volatility for an NVDA 900 put trading at $12.50 with spot at $875."
10. "Show me SPY's full option chain for the nearest expiry."
11. "What is the DEX for IWM and what does it imply for direction?"
12. "Give me an exposure summary for AMZN."
13. "What are the key support and resistance levels for SPX based on GEX?"
14. "How does SPY's realized volatility compare to implied volatility this week?"

---

## Rate Limits

| Plan | Daily Requests | Access |
|---|---|---|
| Free | 5 | Stock quotes, GEX/DEX/VEX/CHEX by strike, levels, BSM greeks, IV solver, tickers, options meta, surface, stock summary |
| Basic | 100 | Everything in Free + index symbols (SPX, VIX, RUT) |
| Growth | 2,500 | + Exposure summary, narrative, 0DTE analytics, volatility analytics, option quotes, full-chain GEX, Kelly sizing |
| Alpha | Unlimited | + Advanced volatility (SVI, variance surfaces, arbitrage detection, greeks surfaces, variance swap), VRP analytics |
| Enterprise | Unlimited | Full access + admin endpoints |

---

## Plans & Tool Access

| Tool | Free | Basic | Growth | Alpha |
|---|---|---|---|---|
| GetStockQuote | yes | yes | yes | yes |
| GetTickers | yes | yes | yes | yes |
| GetOptionChain | yes | yes | yes | yes |
| GetAccount | yes | yes | yes | yes |
| CalculateGreeks | yes | yes | yes | yes |
| SolveIV | yes | yes | yes | yes |
| GetGex | yes | yes | yes | yes |
| GetDex | yes | yes | yes | yes |
| GetVex | yes | yes | yes | yes |
| GetLevels | yes | yes | yes | yes |
| GetStockSummary | cached | cached | yes | yes |
| GetExposureSummary | no | no | yes | yes |
| GetNarrative | no | no | yes | yes |
| GetVolatility | no | no | yes | yes |

---

## Links

- **FlashAlpha:** [flashalpha.com](https://flashalpha.com)
- **API Documentation:** [flashalpha.com/docs](https://flashalpha.com/docs)
- **Python SDK:** [github.com/FlashAlpha-lab/flashalpha-python](https://github.com/FlashAlpha-lab/flashalpha-python)
- **JavaScript SDK:** [github.com/FlashAlpha-lab/flashalpha-js](https://github.com/FlashAlpha-lab/flashalpha-js)
- **.NET SDK:** [github.com/FlashAlpha-lab/flashalpha-dotnet](https://github.com/FlashAlpha-lab/flashalpha-dotnet)
- **Java SDK:** [github.com/FlashAlpha-lab/flashalpha-java](https://github.com/FlashAlpha-lab/flashalpha-java)
- **Go SDK:** [github.com/FlashAlpha-lab/flashalpha-go](https://github.com/FlashAlpha-lab/flashalpha-go)
