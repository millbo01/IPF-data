# V2.5 sealed Q3 2026 holdout — result

Date evaluated: 2026-10-02

## Status

**Supplementary positive but fragile. Not a V3 pass/fail.**

The sealed Q3 2026 window was unsealed through QuantConnect Research after the cloud backtester remained capped at 2026-07-02.

Research data access reached 2026-09-30 16:00 New York for both QQQ and NDX.

Frozen window:
- signal dates 2026-07-02 through 2026-09-29;
- P90 primary threshold 1.7796;
- P95 secondary threshold 2.3646;
- fade next session 09:31 -> 10:00 New York;
- NDX execution;
- IG representative 1-point base round-trip spread;
- 2x spread stress;
- £2,000 / 1x-notional shadow account.

## P90 primary

Eight qualifying events.

Base:
- gross mean: +3.802 bp
- gross median: +8.201 bp
- gross hit rate: 62.5%
- net mean: **+3.460 bp**
- net median: **+7.856 bp**
- net hit rate: **62.5%**
- break-even round-trip cost: 3.802 bp / 10.151 NDX points
- ending equity: **£2,005.12**
- cumulative P&L: **+£5.12**
- max closed-trade drawdown: **0.71%**
- max margin utilisation: **5.31%**

2x spread stress:
- net mean: **+3.118 bp**
- ending equity: **£2,004.56**
- cumulative P&L: **+£4.56**
- max closed-trade drawdown: **0.71%**

## Fragility check

The best event was the 2026-07-31 trade after the 2026-07-30 signal:
- z = +2.719397
- fade SELL
- base net return = +85.415 bp

Removing that single best event:
- remaining seven-event mean net return ≈ **-8.25 bp**
- reconstructed £2,000 1x-notional ending equity ≈ **£1,988.10**
- reconstructed P&L ≈ **-£11.90**

Therefore the positive Q3 aggregate depends materially on one large winner.

This does **not** formally fail V3 because the forward minimum sample (30 P90 events and 12 months) has not been reached. It is recorded as evidence that the edge remains heavy-tailed.

## P95 secondary subset

Only three events.

Base:
- net mean: +6.726 bp
- net median: -27.354 bp
- net hit rate: 33.3%
- ending equity: £2,003.22

2x spread:
- net mean: +6.388 bp
- ending equity: £2,003.01

P95 is too sparse for inference and remains secondary.

## Event ledger

| signal date | trade date | z | fade | P95 | gross bp | base net bp | 2x net bp |
|---|---|---:|---|---|---:|---:|---:|
| 2026-07-02 | 2026-07-06 | -1.885367 | BUY | no | +24.392 | +24.054 | +23.717 |
| 2026-07-07 | 2026-07-08 | -1.967288 | BUY | no | +39.707 | +39.363 | +39.019 |
| 2026-07-13 | 2026-07-14 | -1.779664 | BUY | no | +2.114 | +1.776 | +1.438 |
| 2026-07-16 | 2026-07-17 | -1.784248 | BUY | no | +14.288 | +13.937 | +13.585 |
| 2026-07-23 | 2026-07-24 | -2.003746 | BUY | no | -71.274 | -71.627 | -71.979 |
| 2026-07-30 | 2026-07-31 | +2.719397 | SELL | yes | +85.766 | +85.415 | +85.064 |
| 2026-08-04 | 2026-08-05 | +2.916013 | SELL | yes | -27.019 | -27.354 | -27.689 |
| 2026-09-21 | 2026-09-22 | +2.387417 | SELL | yes | -37.555 | -37.883 | -38.211 |

## Interpretation

Q3 does not kill the candidate: frozen P90 remained positive after base costs and 2x spread stress.

However, the positive aggregate is not broad-based. The sample is small and the result flips negative when the single best event is removed. That is exactly why the pre-registered V3 forward sample requires both 30 P90 events and 12 months before formal adjudication.

No timestamp, threshold, direction, volatility or other filter changes are permitted based on this result.
