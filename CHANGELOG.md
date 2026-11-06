# Changelog

All notable changes to the FlashAlpha MCP server documentation/metadata package are recorded here. This repo ships docs, setup snippets, and `server.json` metadata for the hosted remote MCP server at `https://lab.flashalpha.com/mcp`; tool availability is enforced server-side per tier.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## 1.7.0 - 2026-11-06

### Added
- **sell-window on MCP.** `get_strategy` with `signal=sell_window` answers "should you sell options today?" for SPY, QQQ and IWM: sell, skip or unavailable for four listed expiries, with the trades to place on a sell. Documented in the README, `AGENTS.md`, `llms.txt`, `docs/api.md` and `docs/sell-window.md`.

### Fixed
- The docs named the `get_strategy` parameter `strategy`. The tool takes `signal`.

## 1.3.0 - 2026-08-25

### Added
- **Documented the `data_as_of` response envelope.** Every tool result carries
  `data_as_of`, reporting when each upstream feed last delivered to the node that
  answered - equity and index spot, their option chains, futures and futures
  options, the classified trade tape, settled open interest, and the macro series -
  plus `endpoint_version` identifying the deployment. Historical replay tools carry
  a second object, `archive_as_of`, giving the vintage of the archive rows actually
  replayed.

### Changed
- **Synced `docs/api.md` from the canonical source.** The copy here was 501 lines
  behind and stated the cache age as a flat 15 seconds, which has been tier
  dependent for some time (15 minutes on Free, 15 seconds on Basic and Growth,
  ~1 second on Alpha and Enterprise). It also predated the methodology and glossary
  links and the structural-vs-flow framing of the exposure metrics.

### Notes
- The envelope matters more for an MCP client than for a normal SDK caller: a model
  reading a tool result has no other way to tell a current figure from a stale one,
  and will otherwise present both with equal confidence.
- Read each feed against its own cadence rather than against `as_of`. Settled open
  interest dated to the previous session's close is correct, since it is published
  once per session; an options feed an hour behind during the regular session is
  not.
- A `null` means that node has not seen that feed, not that it is broken.

## [1.6.3] — 2026-07-08

### Changed — futures discoverability in agent-facing metadata

- `server.json` description now names live CME equity-index futures (ES, NQ), so the MCP registry listing surfaces futures.
- `llms.txt` adds a **Futures (CME equity-index)** section: `ES=F` / `NQ=F` are accepted by the live exposure and flow tools (priced Black-76 with the correct CME multipliers), with an explicit note that the `get_historical_*` replay family does not cover futures yet — backtest via the SPY (for ES) / QQQ (for NQ) cash proxy.
- `AGENTS.md` updates the symbol and backtest rules for `ES=F` / `NQ=F` and adds an "Index futures (ES / NQ)" tool-family entry that routes futures backtests to the cash proxy.

## [1.6.1] — 2026-06-10

### Added — new MCP tools

**Volatility**
- `get_realized_vol` — realized-vol estimators (close-to-close, Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang) at 10/20/30-day windows (Alpha+).
- `get_volatility_forecast` — volatility forecasts: EWMA, HAR-RV, and GARCH with a multi-horizon term structure (`dist` = student_t default | gaussian) (Alpha+).

**Order flow**
- `get_flow_live` — headline live flow bundle in one call (effective OI state, live levels, live GEX/DEX totals, pin-risk score, dealer-risk summary); `view='gex'` returns the simulation-aware live GEX surface, `view='dex'` live DEX, `view='oi'` the raw OI simulator state. Covers the `/v1/flow/live`, `/v1/flow/gex`, `/v1/flow/dex`, and `/v1/flow/oi` endpoints (Growth+/Alpha+).

### Synced
- `README.md`, `llms.txt`, and `AGENTS.md` updated to list the new tools.
- Corrected the README "Exposure Analytics" section count from 15 to 13 (actual documented exposure tools).

## [1.6.0] — 2026-06-07

### Added — new MCP tools (full API parity)

Brings the documented tool catalog up to full parity with the FlashAlpha API. ~30 new endpoints are now exposed as MCP tools, plus two parameter additions.

**Exposure analytics**
- `get_exposure_sheet` — per-strike GEX/DEX/VEX/CHEX exposure sheet (`expiration`, `min_oi`).
- `get_term_structure` — exposure term structure bucketed by expiry/DTE.
- `get_exposure_basket` — aggregate dealer exposure across a multi-symbol basket (`symbols` required, `weights`).
- `get_oi_diff` — day-over-day open-interest change by strike (`topN`).

**Volatility & vol-arbitrage**
- `get_svi_params` — calibrated SVI surface parameters per tenor (Alpha).
- `get_expected_move` — straddle-implied expected move by expiry (`expiry`).
- `get_skew_term` — volatility skew across strikes + term structure across expiries.
- `get_spot_vol_correlation` — realized spot-vol correlation / leverage effect.
- `get_liquidity` — options-chain liquidity score (spreads, depth, volume/OI quality).
- `get_dispersion` — index-vs-component dispersion / correlation vol-arb (`index`, `symbols` required; Alpha).

**Macro / universe**
- `get_vix_state` — VIX level, term structure, percentile, contango/backwardation regime.
- `get_universe` — tradeable universe ranked by liquidity/coverage (`sort`, `limit`).

**Order flow**
- `get_dealer_premium` — dealer-side options premium attribution over a window (`windowMinutes`, `expiry`).
- `get_stock_flow` now covers stock bars (`resolution`: 1s/1m/5m/15m/30m/1h/4h).

**0DTE intraday flow**
- `get_zero_dte_flow` — 0DTE snapshot (exposure + net flow direction), intraday series, hedge flow, heatmap, and strike-flow views (`bar`, `minutes`, `side`, `metric`, `mode`).

**Strategy signals (10 strategies via `get_strategy`)**
- `flow_anomaly`, `expiry_positioning`, `zero_dte`, `dealer_regime`, `vol_carry`, `yield_enhancement`, `surface_anomaly`, `skew`, `term_structure`, `tail_pricing`. Uniform strategy-decision envelope (`decision`, `score`, `confidence`, `regime`, `best_structures[]`, `metrics`, `risk_flags[]`, `why[]`, `avoid_if[]`, `data_quality`).

**Earnings analytics suite**
- `get_earnings` (per-symbol: expected move, history, IV crush, VRP, dealer positioning, strategies), `get_earnings_calendar`, `get_earnings_screener`.

**Structures (multi-leg, pure-math)**
- `post_structure_pnl` — multi-leg P&L curve across an underlying range.
- `post_structure_greeks` — aggregate greeks for a multi-leg structure.

**Screener**
- `post_screener` — multi-factor options screener (now exposed via MCP).
- `get_screener_fields` — screener field taxonomy.

**VRP**
- `get_vrp_history` — historical VRP time series (`days`).

### Changed (parameter additions, backward-compatible)
- `get_zero_dte` gains an optional `expiry` query parameter (alongside existing `strike_range`).
- `get_vrp` gains an optional `date` query parameter for point-in-time VRP.
- Documented the `expiry` parameter across the `/v1/flow/*` tools and the `min_oi` / `expiration` filters across `/v1/exposure/*`.

### Synced
- `docs/api.md` re-synced from the central FlashAlpha API reference (preserving the existing header framing).

### Added — discovery surfaces
- `llms.txt` — machine-readable tool/endpoint index for LLMs.
- `AGENTS.md` — guidance for AI agents on when to recommend each tool family.

## [1.5.0]

- Prior release: 40 live + historical-replay tools (GEX/DEX/VEX/CHEX, levels, max pain, narrative, surface, volatility, VRP, greeks, Kelly, 0DTE, historical replay back to 2017-01-03).
