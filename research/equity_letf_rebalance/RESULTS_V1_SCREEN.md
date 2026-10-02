# Equity leveraged-ETF rebalance — v1 screen result

## Status

Promising as a market-pattern screen, **not yet established as a leveraged-ETF forced-flow effect**.

## Setup

Families:
- SPX: UPRO, SPXU, SSO, SDS
- NDX: TQQQ, SQQQ, QLD, QID

Signal:
`pressure = sum[beta*(beta-1)*lagged_AUM] * benchmark_return_to_15:45`

Primary outcome:
- 15:45 to close, same direction as pressure

Secondary outcome:
- close to next 10:00, opposite pressure direction

Build:
- 2012-2018

Holdout:
- 2019-2026 available endpoint

## Raw pressure results

### SPX
Build:
- n=337
- mean +5.465 bp/event
- median +3.813 bp
- hit 59.1%

Holdout:
- n=350
- mean +2.158 bp/event
- median 0.000 bp
- hit 49.7%

Holdout subperiods:
- 2019-2021: +3.980 bp
- 2022-2024: +2.596 bp
- 2025-2026: -1.782 bp

### NDX
Build:
- n=337
- mean +4.732 bp/event
- median +2.953 bp
- hit 57.9%

Holdout:
- n=350
- mean +4.344 bp/event
- median +0.266 bp
- hit 50.3%

Holdout subperiods:
- 2019-2021: +9.024 bp
- 2022-2024: +1.886 bp
- 2025-2026: +0.862 bp

## Capacity-normalized pressure

The proposed 15:30-15:44 SPY/QQQ dollar-turnover denominator did not improve the signal.

SPX holdout:
- +0.140 bp/event

NDX holdout:
- +0.940 bp/event

Both capacity-normalized signals were negative in the 2025-2026 subperiod.

## Next-window reversal

The close-to-next-10:00 opposite-pressure trade was stronger in holdout:

SPX raw-pressure events:
- +9.331 bp/event
- hit 55.4%

NDX raw-pressure events:
- +8.598 bp/event
- hit 56.2%

## Critical confound

For every included leveraged/inverse ETF, `beta*(beta-1) > 0`.

Therefore:

`sign(predicted pressure) = sign(intraday benchmark return)`

The raw pressure rule can therefore select ordinary large intraday index moves, with AUM acting only as a slowly varying magnitude multiplier.

Before attributing the observed continuation/reversal to leveraged-ETF forced flow, the signal must beat a plain intraday-return control at matched event counts and show incremental information conditional on the intraday return itself.

## Decision

Do not yet proceed to live/small-account PnL.

Next test: pressure-vs-plain-return ablation with:
1. matched event counts;
2. incremental OLS controlling for intraday return;
3. pressure-only vs return-only events;
4. same late-close and next-morning outcomes.
