# FlashAlpha MCP Server — Real-Time Options Analytics for AI Assistants

Connect Claude, ChatGPT, Cursor, Windsurf, or any MCP-compatible AI assistant to live options market data. **70+ tools** covering gamma exposure (GEX), delta/vanna/charm exposure, max pain, key dealer-positioning levels, IV surfaces (SVI parameters), VRP analytics + history, expected move, volatility skew & term structure, spot-vol correlation, dispersion / index-vs-component vol arbitrage, liquidity scoring, VIX macro state, the tradeable universe, exposure sheet / term-structure / multi-symbol basket / open-interest diff, Black-Scholes greeks, Kelly sizing, real-time options & stock order flow (sweeps, blocks, dealer premium), 0DTE intraday flow (snapshot, time series, hedge flow, heatmap, strike flow), **10 actionable options-strategy signals** (flow-anomaly, expiry-positioning, 0DTE, dealer-regime, vol-carry, yield-enhancement, surface-anomaly, skew, term-structure, tail-pricing), a full **earnings analytics suite** (calendar, expected move, history, IV crush, VRP, dealer positioning, strategies, screener), multi-leg **structure P&L + greeks** calculators, a multi-factor options **screener** with field taxonomy, plus minute-resolution **historical replay back to April 2018** for backtesting.

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

## Tool Catalog (70+ tools)

Tool names below are the **exact strings sent via `tools/call`** — snake_case, not the PascalCase C# method names. Copy verbatim.

### Live tools

#### Market Data (6)
| Tool | Description |
|---|---|
| `get_stock_quote` | Real-time stock quote (bid, ask, mid, last) |
| `get_tickers` | List/search available tickers |
| `get_symbols` | Full list of supported underlying symbols |
| `get_option_chain` | Available expirations + strikes metadata |
| `get_option_quote` | Live option quote: bid, ask, mid, IV, greeks, OI, volume (`expiry`, `strike`, `type`) |
| `get_account` | Plan, daily quota, usage today, remaining calls |

#### Exposure Analytics (13)
| Tool | Description |
|---|---|
| `get_gex` | Gamma exposure (GEX) by strike — call/put walls, gamma flip (`expiration`, `min_oi`) |
| `get_dex` | Delta exposure (DEX) by strike — net dealer delta (`expiration`) |
| `get_vex` | Vanna exposure (VEX) by strike — dealer hedging response to vol moves (`expiration`) |
| `get_chex` | Charm exposure (CHEX) by strike — time-decay-driven flows (`expiration`) |
| `get_levels` | Gamma flip, call/put walls, max pain, highest OI strike, 0DTE magnet |
| `get_exposure_summary` | Net GEX/DEX/VEX/CHEX, regime, hedging estimates, top strikes, 0DTE breakdown |
| `get_exposure_sheet` | Per-strike greeks exposure sheet (GEX/DEX/VEX/CHEX side by side) with `expiration`, `min_oi` filters |
| `get_term_structure` | Exposure term structure — net GEX/DEX/VEX/CHEX bucketed by expiry/DTE |
| `get_exposure_basket` | Aggregate dealer exposure across a multi-symbol basket (`symbols` required, optional `weights`) |
| `get_oi_diff` | Day-over-day open-interest change by strike — top OI builders/unwinds (`topN`) |
| `get_narrative` | Verbal analysis: regime, levels, dealer positioning, implications |
| `get_max_pain` | Max pain strike, pain curve, put/call OI ratio, dealer alignment, pin probability (`expiration`) |
| `get_zero_dte` | 0DTE analytics: intraday gamma, time-decay acceleration, pin risk, hedging pressure (`expiry`, `strike_range`) |

#### Volatility & Pricing (19)
| Tool | Description |
|---|---|
| `get_surface` | Live 50×50 implied-volatility surface grid over (tenor, log-moneyness) |
| `get_svi_params` | SVI (stochastic-volatility-inspired) calibrated surface parameters per tenor (Alpha) |
| `get_volatility` | ATM IV, realized vol (5/10/20/30d), VRP, 25-δ skew, term structure, GEX-by-DTE |
| `get_advanced_volatility` | SVI parameters, forward prices, variance surface, arbitrage flags, vanna/charm/volga surfaces, variance-swap fair values (Alpha) |
| `get_expected_move` | Straddle-implied expected move (1σ) by expiry — bands, % move, breakevens (`expiry`) |
| `get_skew_term` | Volatility skew across strikes and term structure across expiries in one call |
| `get_spot_vol_correlation` | Realized spot-vol correlation / leverage effect for the underlying |
| `get_realized_vol` | Realized-vol estimators (close-to-close, Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang) at 10/20/30-day windows (Alpha) |
| `get_volatility_forecast` | Volatility forecasts: EWMA, HAR-RV, GARCH with multi-horizon term structure (`dist` = student_t default, gaussian) (Alpha) |
| `get_liquidity` | Options-chain liquidity score: spreads, depth, volume/OI quality |
| `get_dispersion` | Index-vs-component dispersion / correlation vol-arbitrage (`index`, `symbols` required, `weights`, `horizon_days`) (Alpha) |
| `get_vix_state` | VIX macro state: level, term structure, percentile, contango/backwardation regime |
| `get_universe` | Tradeable universe ranked by liquidity/coverage (`sort`, `limit`) |
| `get_vrp` | Volatility risk premium dashboard: IV vs RV, percentiles, regime, strategy scores (`date`) |
| `get_vrp_history` | Historical VRP time series for charting + backtesting (`days`) |
| `get_stock_summary` | One-call combined summary: price, IV, VRP, skew, term, exposure, macro context |
| `calculate_greeks` | Black-Scholes greeks (Δ, Γ, Θ, ν, ρ, vanna, charm, speed, zomma, color) |
| `solve_iv` | Solve implied volatility from market price (BSM inversion) |
| `calculate_kelly` | Kelly criterion optimal sizing for an option trade |

#### Order Flow — Options & Stocks (real-time, simulation-aware)
| Tool | Description |
|---|---|
| `get_flow_live` | Headline live flow bundle in one call: effective OI state, live levels, live GEX/DEX totals, pin-risk score, dealer-risk summary. `view='gex'` returns the full simulation-aware live GEX surface, `view='dex'` live DEX, `view='oi'` the raw OI simulator state |
| `get_flow_summary` | Net signed options premium, call/put flow, sweep vs block breakdown (`expiry`) |
| `get_flow_levels` | Flow-derived support/resistance and dealer hedging levels (`expiry`) |
| `get_flow_signals` | Scored actionable flow signals — intent, structure, conviction (`minScore`, `intent`, `structure`, `windowMinutes`, `limit`, `expiry`) |
| `get_flow_pin_risk` | Real-time pin-risk estimate from live flow + positioning (`expiry`) |
| `get_flow_dealer_risk` | Live dealer gamma/delta risk from intraday flow (`expiry`) |
| `get_dealer_premium` | Dealer-side options premium attribution (sold/bought) over a window (`windowMinutes`, `expiry`) |
| `get_option_flow` | Raw recent option prints, blocks, sweeps, cumulative & history (`minSize`, `minutes`, `limit`, `expiry`) |
| `get_stock_flow` | Raw recent stock prints, blocks, bars, cumulative & history (`resolution`, `minSize`, `minutes`, `limit`) |
| `get_flow_scan` | Cross-symbol flow leaderboards & outliers (`n`, `limit`, `minTrades`, `windowMinutes`) |

#### 0DTE Intraday Flow
| Tool | Description |
|---|---|
| `get_zero_dte_flow` | 0DTE flow snapshot: live exposure + net flow direction by strike, plus intraday series, hedge flow, heatmap, and strike-flow views (`bar`, `minutes`, `side`, `metric`, `mode`) |

#### Strategy Signals (10 strategies via `get_strategy`)
One tool, parameterized by `strategy` kind, returning the uniform strategy-decision envelope (`decision`, `score`, `confidence`, `regime`, `best_structures[]`, `metrics`, `risk_flags[]`, `why[]`, `avoid_if[]`, `data_quality`).
| `strategy` value | Description |
|---|---|
| `flow_anomaly` | Directional options-flow imbalance → matching short vertical spread (`expiry`) |
| `expiry_positioning` | Dealer expiry positioning → iron-condor / butterfly candidates (`expiry`, `minOpenInterest`, `wingWidth`) |
| `zero_dte` | 0DTE intraday setup → defined-risk spreads (`expiry`, `minOpenInterest`, `wingWidth`) |
| `dealer_regime` | Gamma regime read (long/short gamma) → directional bias (`expiry`) |
| `vol_carry` | Vol carry / theta harvest → short-premium structures (`targetShortDelta`, `maxWidth`, `minCredit`, ...) |
| `yield_enhancement` | Covered-call / cash-secured-put yield (`targetDelta`, `structure`, `excludeEarningsBeforeExpiry`, ...) |
| `surface_anomaly` | IV-surface mispricing / arbitrage candidates (`expiry`) |
| `skew` | Skew steepness/richness → risk-reversal / ratio ideas (`expiry`) |
| `term_structure` | Calendar / diagonal opportunities from term-structure shape |
| `tail_pricing` | Tail-risk richness → cheap-convexity / hedge candidates (`expiry`) |

#### Earnings Analytics
| Tool | Description |
|---|---|
| `get_earnings` | Per-symbol earnings analytics: expected move, history, IV crush, VRP, dealer positioning, and strategies (parameterized) |
| `get_earnings_calendar` | Upcoming earnings calendar with expected moves (`days`, `symbols`, `importance`) |
| `get_earnings_screener` | Rank earnings names by IV-crush edge / VRP / expected move (`sort`, `limit`, `days`, `min_importance`) |

#### Structures (multi-leg, pure-math)
| Tool | Description |
|---|---|
| `post_structure_pnl` | Multi-leg structure P&L curve across an underlying range (`legs[]`, `minUnderlying`, `maxUnderlying`, `points`) |
| `post_structure_greeks` | Aggregate greeks for a multi-leg structure (`legs[]` with `expiry`+`impliedVol`, `spot`, `today`, `rate`, `dividendYield`) |

#### Screener
| Tool | Description |
|---|---|
| `post_screener` | Multi-factor options screener: `universe`, `filters`, `formulas`, `sort`, `select`, `limit`, `offset` |
| `get_screener_fields` | Screener field taxonomy — every filterable/selectable field and type |

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

**Note:** The multi-factor options screener is now exposed as the `post_screener` MCP tool (with `get_screener_fields` for the field taxonomy), in addition to `POST /v1/screener`. The historical replay tools cover analytics only; for raw historical tick data use the historical REST endpoints directly.

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
11. *"Run the flow-anomaly strategy signal on TSLA and show me the best defined-risk structure."*
12. *"What's the expected move for NVDA into Friday expiry, and what's IV crush looked like the last 8 earnings?"*
13. *"Show this week's earnings calendar with expected moves, then screen for the best IV-crush short-premium setups."*
14. *"Price the P&L curve and aggregate greeks for an SPY iron condor: short 580/590 call spread, short 560/550 put spread."*
15. *"Give me the SPX dealer exposure sheet and term structure, plus the day-over-day OI diff."*
16. *"What's the dispersion / index-vs-component vol-arb read on SPX against its top components?"*
17. *"Show the VIX macro state and the dealer-premium flow on QQQ over the last 30 minutes."*

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
