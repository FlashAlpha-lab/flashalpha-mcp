# FlashAlpha MCP Server — Real-Time Options Analytics for AI Assistants

Connect Claude, ChatGPT, Cursor, Windsurf, or any MCP-compatible AI assistant to live options market data. **40 tools** covering gamma exposure (GEX), delta/vanna/charm exposure, max pain, key dealer-positioning levels, IV surfaces (SVI), VRP analytics, Black-Scholes greeks, Kelly sizing, 0DTE intraday flow, plus minute-resolution **historical replay back to April 2018** for backtesting.

---

## What is this repo

Documentation, setup snippets, and `server.json` metadata for the FlashAlpha remote MCP server. The server itself runs at `https://lab.flashalpha.com/mcp` (and `/mcp-oauth` for OAuth-authenticated clients) — its source is not open. Use this repo as a reference for how to wire FlashAlpha into your AI client of choice.

---

## Server URLs

Two endpoints, identical tool catalog, different authentication:

| Endpoint | Auth | When to use |
|---|---|---|
| `https://lab.flashalpha.com/mcp` | `apiKey` tool parameter | Self-hosted clients: Claude Desktop, Claude Code CLI, Cursor, Windsurf, VS Code Copilot |
| `https://lab.flashalpha.com/mcp-oauth` | OAuth 2.1 + PKCE + DCR (RFC 7591) | Claude Connector Directory, ChatGPT Apps, Perplexity custom connectors, any host that requires OAuth-authenticated remote MCP |

- **Transport:** Streamable HTTP
- **Protocol version:** MCP 2025-06-18
- **OAuth discovery:** [`https://lab.flashalpha.com/.well-known/oauth-protected-resource`](https://lab.flashalpha.com/.well-known/oauth-protected-resource) (RFC 9728)
- **Authorization server:** `https://flashalpha.com/oauth`

### Persona-scoped endpoints

Each base endpoint also has nine **persona** variants that expose a curated subset of the catalog for a specific trading style. Same auth model — `/mcp/<persona>` takes the `apiKey` parameter, `/mcp-oauth/<persona>` uses OAuth. Point your client at a persona URL instead of the base URL to load just that toolset.

| Persona | API-key URL | OAuth URL |
|---|---|---|
| 🧲 Gamma Exposure | `https://lab.flashalpha.com/mcp/gex` | `https://lab.flashalpha.com/mcp-oauth/gex` |
| 🎯 Directional | `https://lab.flashalpha.com/mcp/directional` | `https://lab.flashalpha.com/mcp-oauth/directional` |
| 💵 Premium Seller | `https://lab.flashalpha.com/mcp/premium` | `https://lab.flashalpha.com/mcp-oauth/premium` |
| ⚖️ Spreads & Condors | `https://lab.flashalpha.com/mcp/spreads` | `https://lab.flashalpha.com/mcp-oauth/spreads` |
| ⚡ 0DTE | `https://lab.flashalpha.com/mcp/0dte` | `https://lab.flashalpha.com/mcp-oauth/0dte` |
| 📈 Dealer-Positioning Swing | `https://lab.flashalpha.com/mcp/swing` | `https://lab.flashalpha.com/mcp-oauth/swing` |
| 🌊 Volatility / Relative Value | `https://lab.flashalpha.com/mcp/volarb` | `https://lab.flashalpha.com/mcp-oauth/volarb` |
| 💻 Quant / Systematic | `https://lab.flashalpha.com/mcp/quant` | `https://lab.flashalpha.com/mcp-oauth/quant` |
| 📅 Earnings | `https://lab.flashalpha.com/mcp/earnings` | `https://lab.flashalpha.com/mcp-oauth/earnings` |

---

## Quick Setup (self-hosted clients → `/mcp` + `apiKey`)

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

### Claude Code CLI

```bash
claude mcp add flashalpha --transport http https://lab.flashalpha.com/mcp
claude mcp list
```

### Cursor

**Settings → MCP** → Add server:

```json
{
  "flashalpha": {
    "transport": "http",
    "url": "https://lab.flashalpha.com/mcp"
  }
}
```

### VS Code (Copilot / Continue)

`.vscode/mcp.json` or user settings:

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

### Windsurf

**Cascade settings → MCP Servers**:

```json
{
  "flashalpha": {
    "transport": "http",
    "url": "https://lab.flashalpha.com/mcp"
  }
}
```

### Perplexity (Pro/Max/Enterprise)

**Settings → Connectors → + Custom connector → Remote**

- URL: `https://lab.flashalpha.com/mcp-oauth`
- Auth: OAuth (walks the consent flow at `flashalpha.com/oauth/login`)

---

## Authentication

### `/mcp` (apiKey)

Every tool call takes `apiKey` as a string parameter. Get a free key at [flashalpha.com](https://flashalpha.com).

```
apiKey: "fa_your_key_here"
```

Key passes per-call rather than in a header so it works uniformly across all MCP clients without transport-level configuration.

### `/mcp-oauth` (Bearer)

OAuth 2.1 + PKCE + Dynamic Client Registration (RFC 7591). The client registers itself, walks the authorization-code + PKCE flow, and presents a Bearer JWT on each request. **No `apiKey` parameter needed** — the server resolves the user's account from the OAuth identity and forwards the API key internally for upstream `/v1/*` calls. Same per-user tier gating and rate limits apply as the apiKey flow.

Discovery + endpoints:

| | |
|---|---|
| RFC 9728 protected-resource metadata | `https://lab.flashalpha.com/.well-known/oauth-protected-resource` |
| OIDC discovery | `https://flashalpha.com/oauth/.well-known/openid-configuration` |
| JWKS | `https://flashalpha.com/oauth/.well-known/jwks` |
| Dynamic Client Registration | `POST https://flashalpha.com/oauth/register` |
| Authorization endpoint | `https://flashalpha.com/oauth/authorize` |
| Token endpoint | `https://flashalpha.com/oauth/token` |
| Scope | `flashalpha.mcp` |

---

## Tool Catalog (40 tools)

Tool names below are the **exact strings sent via `tools/call`** — snake_case, not the PascalCase C# method names. Copy verbatim.

### Live tools (23)

#### Market Data (5)
| Tool | Description |
|---|---|
| `get_stock_quote` | Real-time stock quote (bid, ask, mid, last) |
| `get_tickers` | List/search available tickers |
| `get_option_chain` | Available expirations + strikes metadata |
| `get_option_quote` | Live option quote: bid, ask, mid, IV, greeks, OI, volume |
| `get_account` | Plan, daily quota, usage today, remaining calls |

#### Exposure Analytics (9)
| Tool | Description |
|---|---|
| `get_gex` | Gamma exposure (GEX) by strike — call/put walls, gamma flip |
| `get_dex` | Delta exposure (DEX) by strike — net dealer delta |
| `get_vex` | Vanna exposure (VEX) by strike — dealer hedging response to vol moves |
| `get_chex` | Charm exposure (CHEX) by strike — time-decay-driven flows |
| `get_levels` | Gamma flip, call/put walls, max pain, highest OI strike, 0DTE magnet |
| `get_exposure_summary` | Net GEX/DEX/VEX/CHEX, regime, hedging estimates, top strikes, 0DTE breakdown |
| `get_narrative` | Verbal analysis: regime, levels, dealer positioning, implications |
| `get_max_pain` | Max pain strike, pain curve, put/call OI ratio, dealer alignment, pin probability |
| `get_zero_dte` | 0DTE analytics: intraday gamma, time-decay acceleration, pin risk, hedging pressure |

#### Volatility & Pricing (9)
| Tool | Description |
|---|---|
| `get_surface` | Live 50×50 implied-volatility surface grid over (tenor, log-moneyness) |
| `get_volatility` | ATM IV, realized vol (5/10/20/30d), VRP, 25-δ skew, term structure, GEX-by-DTE |
| `get_advanced_volatility` | SVI parameters, forward prices, variance surface, arbitrage flags, vanna/charm/volga surfaces, variance-swap fair values (Alpha) |
| `get_vrp` | Volatility risk premium dashboard: IV vs RV, percentiles, regime, strategy scores |
| `get_vrp_history` | Historical VRP time series for charting + backtesting |
| `get_stock_summary` | One-call combined summary: price, IV, VRP, skew, term, exposure, macro context |
| `calculate_greeks` | Black-Scholes greeks (Δ, Γ, Θ, ν, ρ, vanna, charm, speed, zomma, color) |
| `solve_iv` | Solve implied volatility from market price (BSM inversion) |
| `calculate_kelly` | Kelly criterion optimal sizing for an option trade |

### Historical replay tools (17, Alpha tier)

All historical tools take a required `at=YYYY-MM-DDTHH:mm:ss` parameter (ET wall-clock) and replay the matching live analytic at any minute since 2018-04-16. Response shapes are identical to the live counterparts — backtesting code that parses live responses works on historical with a tool-name swap.

| Tool | Mirrors |
|---|---|
| `get_historical_gex` | `get_gex` |
| `get_historical_dex` | `get_dex` |
| `get_historical_vex` | `get_vex` |
| `get_historical_chex` | `get_chex` |
| `get_historical_levels` | `get_levels` |
| `get_historical_exposure_summary` | `get_exposure_summary` |
| `get_historical_narrative` | `get_narrative` |
| `get_historical_zero_dte` | `get_zero_dte` |
| `get_historical_max_pain` | `get_max_pain` |
| `get_historical_volatility` | `get_volatility` |
| `get_historical_advanced_volatility` | `get_advanced_volatility` |
| `get_historical_vrp` | `get_vrp` |
| `get_historical_surface` | `get_surface` |
| `get_historical_stock_quote` | `get_stock_quote` |
| `get_historical_option_quote` | `get_option_quote` |
| `get_historical_stock_summary` | `get_stock_summary` |
| `get_historical_coverage` | List symbols backfilled with coverage windows and gaps — call first to check whether (symbol, date range) is queryable |

**Note:** The multi-factor options screener is REST-only at `POST /v1/screener` — no MCP tool wraps it (yet). The historical replay tools cover analytics only; for raw historical tick data use the historical REST endpoints directly.

---

## MCP Resources (5)

The server publishes 5 markdown documents as MCP Resources so connected clients can pull the full reference into context with one call instead of relying on tool descriptions:

| URI | Title |
|---|---|
| `flashalpha://docs/api` | Live API reference (every REST endpoint at api.flashalpha.com) |
| `flashalpha://docs/historical` | Historical replay reference |
| `flashalpha://docs/mcp` | This document |
| `flashalpha://docs/screener` | Live screener spec (filter DSL, sorts, formulas) |
| `flashalpha://docs/screener-fields` | Screener field taxonomy |

---

## MCP Prompts (4)

Canonical workflow templates that surface in Claude Desktop / Cursor / Windsurf UI as one-click recipes:

| Prompt | Description |
|---|---|
| `analyze_exposure(symbol)` | Full dealer-positioning walkthrough — gamma regime, key levels, hedging pressure, 0DTE contribution |
| `vrp_regime_check(symbol)` | VRP percentile, IV-vs-RV richness, strategy scoring conditioned on the gamma regime |
| `historical_comparison(symbol, reference_date)` | Side-by-side current vs past date, with VIX-context sanity check |
| `zero_dte_brief(symbol)` | Pre-session 0DTE brief — pin risk, expected move, gamma acceleration, ±0.5% hedging tilts |

---

## Example Prompts

Once connected, ask your AI assistant questions like:

1. *"What is SPX dealer gamma positioning right now?"*
2. *"Show me 0DTE setup for SPY today — pin risk, expected move, gamma acceleration."*
3. *"Give me a full options picture for NVDA — IV, RV, VRP, skew, term, exposure, macro."*
4. *"Replay SPY gamma exposure on 2020-03-16 at 14:00 ET."*
5. *"Calculate Black-Scholes greeks for SPY 580 calls expiring next Friday at 18% IV."*
6. *"What is implied volatility for an NVDA 900 put trading at $12.50 with spot $875?"*
7. *"Where is the gamma flip and call/put walls for QQQ today?"*
8. *"Compare current SPX dealer positioning to 2024-04-19."*
9. *"What's the VRP percentile for AAPL vs its 90-day distribution?"*
10. *"Generate a 0DTE brief for SPY before the open."*

---

## Plans & Pricing

Four tiers. Annual saves 20% and locks the price for 12 months.

| Plan | Monthly | Annual (per month) | Annual total | Daily quota | Freshness |
|---|---|---|---|---|---|
| **Free** | $0 | — | — | 5 / day | 15-minute |
| **Basic** | $79/mo | $63/mo | $756/yr | 100 / day | 15-second |
| **Growth** | $299/mo | $239/mo | $2,868/yr | 2,500 / day | 15-second |
| **Alpha** | $1,499/mo | $1,199/mo | $14,388/yr | Unlimited | No cache (real-time) |

### What unlocks at each tier

| Capability | Free | Basic | Growth | Alpha |
|---|:-:|:-:|:-:|:-:|
| Single-stock GEX (single expiry), call/put walls, gamma flip | ✓ | ✓ | ✓ | ✓ |
| BSM greeks, IV solver, stock quotes | ✓ | ✓ | ✓ | ✓ |
| ETFs / indexes (SPY, QQQ, IWM, SPX) | — | ✓ | ✓ | ✓ |
| DEX / VEX / CHEX, max pain, Market Overview | — | ✓ | ✓ | ✓ |
| Full-chain GEX, 0DTE analytics, option quotes, volatility analytics, AI narrative, Kelly criterion | — | — | ✓ | ✓ |
| Live Screener — 20-symbol Tier 1 universe | — | — | ✓ | ✓ |
| Live Screener — full ~250-symbol universe (REST) | — | — | — | ✓ |
| Advanced volatility (SVI, variance surfaces, arbitrage detection, higher-order greeks surfaces) | — | — | — | ✓ |
| VRP analytics + history | — | — | — | ✓ |
| Historical API — minute-resolution replay since 2018-04-16 | — | — | — | ✓ |
| 99.9% uptime SLA | — | — | — | ✓ |

Tier gating is enforced server-side per tool. Callers hitting a tool above their tier receive a 403 with the required plan in the response body. Current pricing: [flashalpha.com/pricing](https://flashalpha.com/pricing).

---

## SDKs

| Language | Package | Repository |
|----------|---------|------------|
| Python | `pip install flashalpha` | [flashalpha-python](https://github.com/FlashAlpha-lab/flashalpha-python) |
| JavaScript | `npm i flashalpha` | [flashalpha-js](https://github.com/FlashAlpha-lab/flashalpha-js) |
| .NET | `dotnet add package FlashAlpha` | [flashalpha-dotnet](https://github.com/FlashAlpha-lab/flashalpha-dotnet) |
| Java | Maven Central | [flashalpha-java](https://github.com/FlashAlpha-lab/flashalpha-java) |
| Go | `go get github.com/FlashAlpha-lab/flashalpha-go` | [flashalpha-go](https://github.com/FlashAlpha-lab/flashalpha-go) |

---

## Links

- [FlashAlpha](https://flashalpha.com) — API keys, docs, pricing
- [API Documentation](https://flashalpha.com/docs)
- [MCP server docs (canonical)](https://flashalpha.com/docs/mcp)
- [llms.txt](https://flashalpha.com/llms.txt) — machine-readable index for LLMs
- [Examples](https://github.com/FlashAlpha-lab/flashalpha-examples) — runnable tutorials
- [GEX Explained](https://github.com/FlashAlpha-lab/gex-explained)
- [0DTE Options Analytics](https://github.com/FlashAlpha-lab/0dte-options-analytics)
- [Volatility Surface Python](https://github.com/FlashAlpha-lab/volatility-surface-python)
- [Awesome Options Analytics](https://github.com/FlashAlpha-lab/awesome-options-analytics)

## What the Alpha tier unlocks

Free and entry tiers cover live exposure analytics. The **Alpha tier ($1,499/mo)**
adds the data you cannot get anywhere else:

- **Aggregate vanna and charm exposure.** FlashAlpha is the only public source for
  these dealer-positioning aggregates.
- **Point-in-time replay since 2018.** Backtest and trade the same code, with no
  look-ahead and no training-serving skew.
- **SVI vol surfaces, VRP analytics, higher-order Greeks**, uncached and unlimited.

Built for quants, prop desks, and vol funds. See the full picture and get a key:
**[flashalpha.com/for-quant-teams](https://flashalpha.com/for-quant-teams?utm_source=github&utm_medium=readme&utm_campaign=repo-flashalpha-mcp)**
