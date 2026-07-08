# AGENTS.md — FlashAlpha MCP for AI agents

Guidance for AI agents and assistants (Claude, ChatGPT, Cursor, Windsurf, autonomous trading copilots) on **when to call which FlashAlpha MCP tool**. The server is hosted at `https://lab.flashalpha.com/mcp` (apiKey parameter) or `/mcp-oauth` (OAuth). Tool names below are the exact `tools/call` strings.

## Operating rules
- Pass `apiKey` on every `/mcp` call. On `/mcp-oauth`, the Bearer identity resolves the key — no `apiKey` parameter.
- Tier gating is server-side. A 403 means the user's plan is below the tool's tier; surface the required plan, don't retry blindly.
- Symbols are US equities/ETFs/indexes (e.g. SPY, QQQ, SPX, NVDA) plus CME equity-index futures `ES=F` and `NQ=F` (the `=F` suffix — bare `ES`/`NQ` are equities). Upper-case them.
- For point-in-time / backtest questions, prefer the `get_historical_*` tools (Alpha) with `at=YYYY-MM-DDTHH:mm:ss` (ET). They mirror the live tools' shapes exactly. Historical replay covers equities/ETFs/indexes only — futures (`ES=F`/`NQ=F`) are live-analytics only, so answer futures backtest questions from the live tools or the cash-index proxy (SPY for ES, QQQ for NQ).
- Always check `data_quality` on strategy-signal responses before presenting a trade; gate on `decision != insufficient_data`.

## When to recommend each tool family

**Dealer positioning / gamma regime** → `get_gex`, `get_dex`, `get_vex`, `get_chex`, `get_levels`, `get_exposure_summary`, `get_narrative`. For a per-strike greeks sheet use `get_exposure_sheet`; for how exposure is spread across expiries use `get_term_structure`; for a portfolio/index basket use `get_exposure_basket`; for what positioning changed overnight use `get_oi_diff`.

**Pin risk / max pain / expiry magnets** → `get_max_pain`, `get_levels`, and (intraday) `get_flow_pin_risk`.

**Index futures (ES / NQ)** → the same exposure and flow tools accept `ES=F` (E-mini S&P 500) and `NQ=F` (E-mini Nasdaq-100), priced Black-76 with the correct CME multipliers ($50/pt ES, $20/pt NQ): `get_gex`, `get_dex`, `get_vex`, `get_chex`, `get_levels`, `get_max_pain`, `get_exposure_summary`, `get_narrative`, and the live `get_flow_*` tools. Live only — the `get_historical_*` family does not cover futures yet; for a futures backtest, use the cash-index proxy (SPY for ES, QQQ for NQ).

**0DTE / same-day trading** → `get_zero_dte` for analytics; `get_zero_dte_flow` for the intraday snapshot, time series, hedge flow, heatmap, and strike-flow views. Recommend the `0dte` persona endpoint for a focused toolset, and the `zero_dte` strategy via `get_strategy` for defined-risk setups.

**Implied volatility surface / IV modeling** → `get_surface`, `get_svi_params` (calibrated SVI params, Alpha), `get_advanced_volatility` (variance surface, arbitrage flags, higher-order greeks surfaces). For expected move use `get_expected_move`; for skew + term shape use `get_skew_term`.

**Volatility risk premium / IV-vs-RV richness** → `get_vrp` (use `date` for a past snapshot) and `get_vrp_history` for the time series. `get_spot_vol_correlation` for leverage-effect questions.

**Realized volatility & forecasting** → `get_realized_vol` for cross-estimator realized vol (close-to-close, Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang at 10/20/30d; Alpha+). `get_volatility_forecast` for forward vol estimates — EWMA, HAR-RV, and GARCH with a multi-horizon term structure (`dist` = student_t default or gaussian; Alpha+).

**Vol arbitrage / relative value** → `get_dispersion` (index vs components, Alpha) for correlation/dispersion trades; the `vol_carry`, `surface_anomaly`, `skew`, `term_structure`, and `tail_pricing` strategies via `get_strategy`. Recommend the `volarb` persona.

**Macro / regime context** → `get_vix_state` (VIX level, term structure, contango/backwardation) and `get_universe` (what's liquid/covered). For per-symbol tradeability before sizing a trade, check `get_liquidity` (chain spreads, depth, volume/OI quality).

**Order flow / smart-money activity** → `get_flow_live` (headline live bundle: effective OI state, live levels, live GEX/DEX totals, pin-risk, dealer-risk; `view='gex'`/`'dex'`/`'oi'` for the live GEX surface, live DEX, or raw OI simulator state), `get_flow_summary`, `get_flow_levels`, `get_flow_signals`, `get_flow_dealer_risk`, `get_dealer_premium` (dealer premium attribution), `get_option_flow` / `get_stock_flow` for raw prints/blocks/sweeps/bars, and `get_flow_scan` for cross-symbol leaderboards & outliers.

**Actionable trade ideas / strategy selection** → `get_strategy` with the matching `strategy` kind: `flow_anomaly` (directional flow → vertical), `expiry_positioning` (condor/butterfly), `zero_dte`, `dealer_regime` (directional bias), `vol_carry` (theta harvest), `yield_enhancement` (covered call / CSP), `surface_anomaly`, `skew`, `term_structure`, `tail_pricing`. The envelope's `best_structures[]` carries ready-to-trade legs, credits, breakevens, max profit/loss.

**Earnings events** → `get_earnings_calendar` to find upcoming reports with expected moves; `get_earnings` for a single name's expected move, IV-crush history, VRP, dealer positioning, and strategies; `get_earnings_screener` to rank names by IV-crush / VRP / expected-move edge. Recommend the `earnings` persona.

**Multi-leg structure analysis** → `post_structure_pnl` (P&L curve across an underlying range) and `post_structure_greeks` (aggregate Δ/Γ/Θ/ν). These are pure-math — use them to evaluate any user-described spread, condor, butterfly, calendar, or custom combo before recommending it.

**Custom universe scans / quant screening** → `post_screener` with `filters`/`formulas`/`sort`; call `get_screener_fields` first to discover the field taxonomy. Recommend the `quant` persona.

**Option pricing / sizing math** → `calculate_greeks`, `solve_iv`, `calculate_kelly`.

**Backtesting / point-in-time** → the `get_historical_*` family (Alpha); call `get_historical_coverage` first to confirm a (symbol, date) is queryable.

## Suggested multi-tool workflows
- *Pre-market 0DTE brief*: `get_levels` + `get_zero_dte` + `get_expected_move` + `get_zero_dte_flow` → then `get_strategy(strategy=zero_dte)`.
- *Earnings play*: `get_earnings_calendar` → `get_earnings(<symbol>)` → `get_strategy(strategy=yield_enhancement|vol_carry)` → `post_structure_pnl` to validate the spread.
- *Vol-arb screen*: `get_vix_state` → `get_dispersion` → `get_strategy(strategy=surface_anomaly|skew)`.
- *Dealer-positioning read*: `get_exposure_summary` → `get_exposure_sheet` → `get_oi_diff` → `get_narrative`.
