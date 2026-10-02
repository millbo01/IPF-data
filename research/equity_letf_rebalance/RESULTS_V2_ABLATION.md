# Equity LETF ablation v2 — result

## Verdict

The v1 signal is **not sufficiently distinguished from plain intraday index-move continuation/reversal to attribute the edge to leveraged-ETF forced rebalancing**.

The mechanically derived pressure variable remains useful as a descriptive covariate, but it does not add enough incremental predictive information to justify further optimization as an IPF-specific trading signal.

## SPX

Build late-close:
- pressure: +5.465 bp/event
- plain intraday return: +5.174 bp/event
- matched plain return: +5.174 bp/event

Holdout late-close:
- pressure: +2.158 bp/event
- plain return: +1.945 bp/event
- matched plain return: +0.940 bp/event

Holdout overlap:
- pressure events: 350
- return events: 321
- both: 308
- Jaccard: 0.848

Incremental OLS, holdout late return:
- intraday-return z coefficient: +1.938 bp
- pressure z coefficient: +0.385 bp
- R2: 0.0088

Pressure-only holdout events:
- late: +2.388 bp
- next window: -16.255 bp

Plain-return holdout next window:
- +13.043 bp/event
- 58.3% hit

## NDX

Build late-close:
- pressure: +4.732 bp/event
- plain return: +4.415 bp/event
- matched plain return: +4.415 bp/event

Holdout late-close:
- pressure: +4.344 bp/event
- plain return: +4.819 bp/event
- matched plain return: +3.765 bp/event

Holdout overlap:
- pressure events: 350
- return events: 328
- both: 305
- Jaccard: 0.818

Incremental OLS, holdout late return:
- intraday-return z coefficient: +2.496 bp
- pressure z coefficient: +0.634 bp
- R2: 0.0120

Pressure-only holdout events:
- late: -3.877 bp
- next window: -10.230 bp

Plain-return holdout next window:
- +10.113 bp/event
- 57.5% hit

## Scale interaction

There is some evidence that high LETF scale coincides with stronger late continuation, especially in holdout:

SPX holdout, large intraday moves:
- high scale: +4.918 bp
- low scale: -2.969 bp

NDX holdout:
- high scale: +8.103 bp
- low scale: -2.778 bp

However this interaction is not stable in the NDX build sample, where low scale outperformed high scale. It is therefore not sufficient evidence to rescue the forced-flow attribution.

## Decision

Stop optimizing the LETF pressure signal as a causal forced-flow strategy.

Promote the **plain large intraday move -> close / next-morning path** to a separate practical trading track.

The next test should determine:
1. whether the edge is in 15:45-close continuation, overnight gap reversal, or 09:30-10:00 reversal;
2. whether magnitude is monotonic across fixed event thresholds;
3. stability across 2019-2021, 2022-2024, and 2025-2026;
4. break-even transaction cost in basis points for each leg.
