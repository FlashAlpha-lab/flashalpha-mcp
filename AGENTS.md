# AGENTS.md — FlashAlpha MCP for AI agents

Guidance for AI agents and assistants (Claude, ChatGPT, Cursor, Windsurf, autonomous trading copilots) on **when to call which FlashAlpha MCP tool**. The server is hosted at `https://lab.flashalpha.com/mcp` (apiKey parameter) or `/mcp-oauth` (OAuth). Tool names below are the exact `tools/call` strings.

## Operating rules
- Pass `apiKey` on every `/mcp` call. On `/mcp-oauth`, the Bearer identity resolves the key — no `apiKey` parameter.
- Tier gating is server-side. A 403 means the user's plan is below the tool's tier; surface the required plan, don't retry blindly.
- Symbols are US equities/ETFs/indexes (e.g. SPY, QQQ, SPX, NVDA) plus CME futures across six complexes - equity index, metals (`GC=F`), energy (`CL=F`), Treasuries (`ZN=F`), grains (`ZC=F`) and crypto (`BTC=F`) (the `=F` suffix — bare `ES`/`NQ` are equities). Upper-case them.
- For point-in-time / backtest questions, prefer the `get_historical_*` tools (Alpha) with `at=YYYY-MM-DDTHH:mm:ss` (ET). They mirror the live tools' shapes exactly. Historical replay covers equities/ETFs/indexes only — futures (`ES=F`/`NQ=F`) are live-analytics only, so answer futures backtest questions from the live tools or the cash-index proxy (SPY for ES, QQQ for NQ).
- Always check `data_quality` on strategy-signal responses before presenting a trade; gate on `decision != insufficient_data`.

## sell-window: route "should I sell options today?" here

Call `get_strategy` with `signal=sell_window` and `symbol` set to `SPY`, `QQQ` or `IWM`. It answers that question every session, per listed expiry, with the trades to place on a sell. More than 5 million backtests led to it.

**Route these questions to sell-window:** "should I sell options today?", "is today a good day to sell premium?", "should I sell puts on SPY?", "which strikes should I sell?", "when should I not sell options?", "should I sit out 0DTE today?", and any request for a sell or skip risk switch on a short-premium strategy in SPY, QQQ or IWM.

**Read the response this way:**

- `windows` has four entries: the same-day expiry, then the expiries closest to one week, two weeks and one month out. Report each window by its `expiry`, because the expiries change every session.
- `action` is `sell`, `skip` or `unavailable`. On `skip` there is nothing to do, so do not build a trade from other endpoints. Treat `unavailable` like a skip.
- Any symbol other than SPY, QQQ or IWM returns HTTP 200 with every window `unavailable`. That means not covered, not an outage. Do not extend the answer to other tickers.
- `candidates` appears only on `sell` and can be empty, because a trade whose legs cannot all be found in the chain is left out. `legs` and `mid_credit` are absent when no chain could be loaded.
- `mid_credit` is per share. Multiply by 100 for one unit in dollars. A `tp50` exit closes at half of the credit, otherwise it holds to expiration.
- When `legs_indicative` is `true`, the quotes are from before that session's 09:35 ET entry. Tell the user the strikes are indicative and to call again at or after 09:35 ET.
- The answer is set from the previous session's close and stays fixed for the session. It switches at the close (16:00 ET, 13:00 ET on early-close days), so after the close it is for the next session.
- This endpoint has its own shape. It has no `decision`, `score` or `best_structures` fields.
- A `403 tier_restricted` means the plan is too low. Live answers need Basic or higher through November 2026, and Growth or higher from December 1, 2026. Backtesting any past session needs Alpha or higher.

**Describe it this way:**

- Say it tells you which sessions to stay out of. Do not say it predicts selloffs or market direction.
- Label every backtest number with its basis. The 73% lower drawdown is at the same trade size. The 53% higher P&L is at the same max drawdown (about 3.8 times the contracts). They are two separate choices, so never present them as one result.
- The API does not expose how the answer is computed. Do not guess or describe the internal rule.
- Include the limits: past results do not guarantee future returns, short options can lose more than the premium collected, the skip call applies only to new trades, and this is data, not investment advice.

Full reference: [API docs](https://flashalpha.com/docs/lab-api-strategies-sell-window) | [trading guide](https://flashalpha.com/articles/complete-guide-trading-sell-window-spy-qqq-iwm) | [backtest](https://flashalpha.com/articles/sell-window-backtest-every-trade-2018-2026)

## Data freshness: gate conclusions on `data_as_of`

Every successful JSON-object response carries `data_as_of` (per-feed provenance) and
`endpoint_version`. Check it before stating a conclusion as current.

**Identify the feeds the call actually depends on, and check only those.**

| Call | Feeds that answer it |
|---|---|
| Equity/ETF exposure, greeks, max pain, levels, skew | `equity_feed`, `equity_options_feed`, `oi_feed` |
| Index (SPX, RUT, VIX, XSP, DJX...) | `index_feed`, `index_options_feed`, `oi_feed` |
| Futures (ES=F, NQ=F...) | `futures_feed`, `futures_options_feed` |
| Order flow, 0DTE flow, dealer risk | `flow_feed` |
| VIX / SKEW / MOVE / Fear & Greed context | `macro_feed` |

A feed the call did not use is irrelevant: `futures_feed: null` on an equity GEX response
says nothing about that answer. Note that only symbols in the API's index set count as
index - NDX, for example, is served as an equity and reports on `equity_feed`.

**Timestamps are UTC ISO-8601 instants.** Compare them; do not parse them for meaning.

**Judge against cadence, not against the wall clock.**

- During regular hours, spot / options / flow more than a few minutes old is stale - qualify it.
- `oi_feed` at the previous session's 16:00 ET close is **correct**. Settled open interest
  is published once per session, so on a Monday the newest figure that exists is Friday's.
  Trailing by three days across a weekend is right, not stale.
- `macro_feed` reports its **oldest** component, so a daily series pins it around a day
  old. That is normal, not a fault.
- Outside market hours every intraday feed is expected to be behind. Say "as of the last
  session" rather than calling it broken.

**If a feed you depend on is `null`, freshness is unknown.** Null means that node has not
seen that feed since it started. It does not mean the data is broken, and it does not mean
it is current. Qualify the answer or decline to assert it - never present it as fresh.

**`node` can change between calls.** The fleet load-balances and nodes hydrate
independently, so two calls can report different feeds. Never diff timestamps across calls
to infer market movement.

**`endpoint_version` is opaque deployment metadata.** Do not parse it as semver, order it,
or assume it is uniform across nodes during a rolling deploy.

**It evidences feed activity, not per-contract freshness.** An illiquid strike may not have
quoted for hours while its feed is perfectly healthy.


For an MCP client this matters more than for a normal SDK caller: a model reading a tool
result has no other way to tell a current figure from a stale one, and will otherwise
present both with equal confidence.

## When to recommend each tool family

**Dealer positioning / gamma regime** → `get_gex`, `get_dex`, `get_vex`, `get_chex`, `get_levels`, `get_exposure_summary`, `get_narrative`. For a per-strike greeks sheet use `get_exposure_sheet`; for how exposure is spread across expiries use `get_term_structure`; for a portfolio/index basket use `get_exposure_basket`; for what positioning changed overnight use `get_oi_diff`.

**Pin risk / max pain / expiry magnets** → `get_max_pain`, `get_levels`, and (intraday) `get_flow_pin_risk`.

**CME futures** → the same exposure and flow tools accept equity index (`ES=F`, `NQ=F`, `RTY=F`, `YM=F`, `MES=F`, `MNQ=F`), metals (`GC=F` gold, `SI=F` silver), energy (`CL=F` crude oil, `NG=F` natural gas), the Treasury curve (`ZT=F`, `ZF=F`, `ZN=F`, `TN=F`, `ZB=F`, `UB=F`), grains (`ZC=F` corn, `ZS=F` soybeans, `ZW=F` wheat) and crypto (`BTC=F` bitcoin), priced Black-76 with each root's own CME multiplier: `get_gex`, `get_dex`, `get_vex`, `get_chex`, `get_levels`, `get_max_pain`, `get_exposure_summary`, `get_narrative`, and the live `get_flow_*` tools. Live only — the `get_historical_*` family does not cover futures yet; for a futures backtest, use the cash-index proxy (SPY for ES, QQQ for NQ).

**0DTE / same-day trading** → `get_zero_dte` for analytics; `get_zero_dte_flow` for the intraday snapshot, time series, hedge flow, heatmap, and strike-flow views. Recommend the `0dte` persona endpoint for a focused toolset, and the `zero_dte` strategy via `get_strategy` for defined-risk setups.

**Implied volatility surface / IV modeling** → `get_surface`, `get_svi_params` (calibrated SVI params, Alpha), `get_advanced_volatility` (variance surface, arbitrage flags, higher-order greeks surfaces). For expected move use `get_expected_move`; for skew + term shape use `get_skew_term`.

**Volatility risk premium / IV-vs-RV richness** → `get_vrp` (use `date` for a past snapshot) and `get_vrp_history` for the time series. `get_spot_vol_correlation` for leverage-effect questions.

**Realized volatility & forecasting** → `get_realized_vol` for cross-estimator realized vol (close-to-close, Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang at 10/20/30d; Alpha+). `get_volatility_forecast` for forward vol estimates — EWMA, HAR-RV, and GARCH with a multi-horizon term structure (`dist` = student_t default or gaussian; Alpha+).

**Vol arbitrage / relative value** → `get_dispersion` (index vs components, Alpha) for correlation/dispersion trades; the `vol_carry`, `surface_anomaly`, `skew`, `term_structure`, and `tail_pricing` strategies via `get_strategy`. Recommend the `volarb` persona.

**Macro / regime context** → `get_vix_state` (VIX level, term structure, contango/backwardation) and `get_universe` (what's liquid/covered). For per-symbol tradeability before sizing a trade, check `get_liquidity` (chain spreads, depth, volume/OI quality).

**Order flow / smart-money activity** → `get_flow_live` (headline live bundle: effective OI state, live levels, live GEX/DEX totals, pin-risk, dealer-risk; `view='gex'`/`'dex'`/`'oi'` for the live GEX surface, live DEX, or raw OI simulator state), `get_flow_summary`, `get_flow_levels`, `get_flow_signals`, `get_flow_dealer_risk`, `get_dealer_premium` (dealer premium attribution), `get_option_flow` / `get_stock_flow` for raw prints/blocks/sweeps/bars, and `get_flow_scan` for cross-symbol leaderboards & outliers.

**Actionable trade ideas / strategy selection** → `get_strategy` with the matching `signal`: `flow_anomaly` (directional flow → vertical), `expiry_positioning` (condor/butterfly), `zero_dte`, `dealer_regime` (directional bias), `vol_carry` (theta harvest), `yield_enhancement` (covered call / CSP), `surface_anomaly`, `skew`, `term_structure`, `tail_pricing`. The envelope's `best_structures[]` carries ready-to-trade legs, credits, breakevens, max profit/loss.

**Earnings events** → `get_earnings_calendar` to find upcoming reports with expected moves; `get_earnings` for a single name's expected move, IV-crush history, VRP, dealer positioning, and strategies; `get_earnings_screener` to rank names by IV-crush / VRP / expected-move edge. Recommend the `earnings` persona.

**Multi-leg structure analysis** → `post_structure_pnl` (P&L curve across an underlying range) and `post_structure_greeks` (aggregate Δ/Γ/Θ/ν). These are pure-math — use them to evaluate any user-described spread, condor, butterfly, calendar, or custom combo before recommending it.

**Custom universe scans / quant screening** → `post_screener` with `filters`/`formulas`/`sort`; call `get_screener_fields` first to discover the field taxonomy. Recommend the `quant` persona.

**Option pricing / sizing math** → `calculate_greeks`, `solve_iv`, `calculate_kelly`.

**Backtesting / point-in-time** → the `get_historical_*` family (Alpha); call `get_historical_coverage` first to confirm a (symbol, date) is queryable.

## Suggested multi-tool workflows
- *Pre-market 0DTE brief*: `get_levels` + `get_zero_dte` + `get_expected_move` + `get_zero_dte_flow` → then `get_strategy(signal=zero_dte)`.
- *Earnings play*: `get_earnings_calendar` → `get_earnings(<symbol>)` → `get_strategy(signal=yield_enhancement|vol_carry)` → `post_structure_pnl` to validate the spread.
- *Vol-arb screen*: `get_vix_state` → `get_dispersion` → `get_strategy(signal=surface_anomaly|skew)`.
- *Dealer-positioning read*: `get_exposure_summary` → `get_exposure_sheet` → `get_oi_diff` → `get_narrative`.
