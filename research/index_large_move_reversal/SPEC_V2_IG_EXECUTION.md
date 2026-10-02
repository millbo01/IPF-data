# NDX/QQQ next-session morning fade — IG execution test v2

## Status

Pre-specified executable-economics test. This document freezes the next experiment before its trade-level results are viewed.

The parent result is `RESULTS_V1_ANATOMY.md`. The plain large-move pattern remains the hypothesis under test; no VIX-ETP or leveraged-ETF causal attribution is carried into this experiment.

## Primary question

Can the previously observed Nasdaq large-move next-session morning fade survive realistic IG UK spread-bet execution on an approximately £2,000 account?

Primary market: **Nasdaq-100 / NDX**.

SPX is retained only as a robustness comparator. It must not be used to choose or tune Nasdaq rules.

## Signal — unchanged from v1

On session T at 15:45 New York:

1. use QQQ as the Nasdaq-100 signal proxy;
2. compute return from the previous regular-session close to the 15:45 minute close;
3. standardize it with a 252-session rolling z-score whose mean and standard deviation use prior observations only, with the existing minimum of 60 prior observations;
4. retain the sign of the move.

SPX comparator: identical construction using SPY.

No signal information from T+1 may enter the trigger.

## Frozen thresholds

Do not re-estimate these on later data.

NDX:
- P80 = **1.2681**
- P90 = **1.7796**
- P95 = **2.3646**

SPX comparator:
- P80 = **1.2278**
- P90 = **1.7595**
- P95 = **2.2530**

All three thresholds are reported. Do not select a threshold winner from the same sample.

## Trade

On the next regular session T+1:

- direction: opposite the sign of T's 15:45 move;
- primary entry: **09:31 New York**;
- exit: **10:00 New York**;
- no overnight exposure.

Entry sensitivity is descriptive and pre-specified:
- 09:31
- 09:32
- 09:35

All three are reported side-by-side. **09:31 remains the primary rule regardless of which timestamp performs best.** A better 09:32 or 09:35 result on this sample does not replace it.

## Price series used for execution analysis

The trigger remains QQQ/SPY to preserve the v1 signal exactly.

For trade P&L, use QuantConnect cash-index minute series:
- NDX for the Nasdaq candidate;
- SPX for the robustness comparator.

This gives point changes that are closer to IG's US Tech 100 / US 500 cash DFB quote convention than QQQ/SPY share-price points.

No synthetic overnight leg is used.

## Venue representation

Primary venue representation: **IG US Tech 100 Daily Funded Bet (DFB)**.

Reason: the experiment is flat overnight and the public IG cash-index spread is materially narrower during the US cash session than the corresponding futures spread-bet spread. Financing is irrelevant for a position opened and closed within the same session.

SPX comparator: IG US 500 DFB.

The exact live DFB EPIC and account-specific minimum stake remain an account-metadata question; they are not inferred from the earlier futures/forward probe.

## Cost model

### Base public spread schedule

Use the current public IG UK index spread-bet product table as the base case.

US Tech 100 DFB:
- 1.0 point during 14:30–21:00 London;
- 2.0 points in the surrounding non-core period relevant to the US open;
- 5.0 points during 22:00–23:00, which is outside this test.

US 500 DFB comparator:
- 0.4 point during 14:30–21:00 London;
- 0.6 point in the surrounding non-core period relevant to the US open;
- 1.5 points during 22:00–23:00, outside this test.

Because the US and UK change daylight-saving time on different dates, convert each New York entry timestamp to Europe/London on that historical date before assigning the spread. This prevents silently assuming 14:31 London throughout the year.

The quoted spread is treated as the full round-trip spread cost in index points for a market entry followed by an exit, before extra slippage.

### Stress

Run:
- **BASE** = public spread schedule above;
- **STRESS2X** = twice the full spread cost.

Do not reduce the public spread retrospectively because a particular trade occurred in a liquid minute.

## Stake and small-account cases

Starting equity: **£2,000**.

Retail margin rate: **5%**.

Report two fixed-stake cases:

1. **PUBLIC_MIN = £1/point.** This is the current public standard minimum for the US Tech 100 DFB and US 500 DFB.
2. **API_0p01_CONDITIONAL = £0.01/point.** The prior authenticated live-account probe returned 0.01 POINTS on the mapped NQ futures/forward market. This smaller stake may be reported as a conditional scenario only; it is not considered executable for the DFB until a read-only live DFB market-detail query confirms it.

No ex-post risk targeting or stake optimization is allowed in this test. The purpose is first to establish the economics and granularity of the actual venue.

Approximate opening margin per trade:
`abs(stake × index_level) × 5%`.

Report margin utilisation against the running £2,000 equity curve.

## Return and P&L definitions

For each event and entry timestamp:

- fade sign = `-sign(day-T intraday return)`
- gross index-point P&L per £1/point = `fade_sign × (exit_index - entry_index)`
- gross return bp = `fade_sign × (exit_index / entry_index - 1) × 10,000`
- net index points = gross points - spread cost
- net bp = gross bp - `spread_points / entry_index × 10,000`
- £ P&L = stake × net points

Break-even transaction cost is the gross mean:
- in bp, gross mean bp;
- in index points, gross mean index-point P&L.

## Risk accounting

For each trade, capture the most adverse NDX/SPX minute high/low after the selected entry through 10:00 and report MAE in bp.

Portfolio max drawdown is computed on the sequential closed-trade equity curve. Because only one index position is active at a time in each market-specific simulation, also report maximum and 95th-percentile margin utilisation.

A negative or zero account balance is a failure; do not truncate or resize prior trades to prevent it.

## Chronology

Retain the existing non-overlapping interpretation periods:

- BUILD: 2012–2018
- 2019–2021: extraordinary regime, reported but not used as the current expected-return anchor
- 2022–2024
- 2025–2026
- HOLDOUT: 2019–2026
- ALL: 2012–2026

Also report every calendar year separately.

## Required outputs

For NDX P80/P90/P95, and SPX as comparator, report for 09:31, 09:32 and 09:35:

- gross mean bp
- gross median bp
- gross hit rate
- net mean bp
- net median bp
- net hit rate
- trade count
- trades/year
- gross and net mean index points
- break-even round-trip cost in bp and points
- mean and worst MAE
- £ P&L
- ending £2,000 equity
- max drawdown
- 95th-percentile and maximum margin utilisation
- year-by-year chronology
- up-day/down-day split if emitted in the result summary
- full event ledger

The full ledger must include at least:
signal date, trade date, z-score, signal return, fade direction, P80/P90/P95 membership, entry prices, exit price, applied spread, gross/net bp, gross index points and MAE.

## Interpretation rule

This run is an **execution/economics test**, not a search over thresholds or timestamps.

- P80/P90/P95 remain a ladder; do not promote whichever threshold happens to look best on the same sample.
- 09:31 is primary; 09:32/09:35 are sensitivity checks only.
- 2019–2021 is reported, but its extraordinary overnight behavior does not set the current expected return.
- A positive gross result that turns negative after the frozen cost model is an execution failure, not a reason to lower the cost assumption.
- A public-minimum stake that produces unacceptable margin/drawdown cannot be rescued by claiming £0.01/point unless the DFB itself is live-confirmed at that minimum.
- Do not add MAIN, LC1, VIX-ETP, LETF pressure, day-of-week, volatility, direction, or other filters in this experiment.

Any later filter, threshold, exit, stake rule or entry-time change is a new pre-specified experiment.

## Reproducibility

The companion script is `qc_ig_execution_v2.py`.

It places no orders. It emits:
- `IGFADE_QA`
- `IGFADE_SUMMARY`
- `IGFADE_YEAR`
- `IGFADE_TRADE`

The raw SPY/QQQ and SPX/NDX minute histories are supplied by QuantConnect and are not duplicated in this repository.
