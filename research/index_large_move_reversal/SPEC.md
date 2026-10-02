# Index large-move continuation / reversal track

## Origin

This track emerged as the control in the leveraged-ETF forced-rebalance experiment.

The LETF pressure signal was highly overlapping with plain intraday return and contributed little incremental predictive information in holdout. The economically stronger observation was therefore retained without a forced-flow causal attribution.

## Signal

At 15:45 New York:
- compute return from previous regular-session close to 15:45
- standardize magnitude using only prior observations
- direction is the sign of that return

Markets:
- SPY as S&P 500 proxy
- QQQ as Nasdaq-100 proxy

## Windows

Measure separately:
1. 15:45 -> 16:00 continuation, same direction
2. 16:00 -> next 09:31 reversal, opposite direction
3. next 09:31 -> 10:00 reversal, opposite direction
4. 16:00 -> next 10:00 total reversal

This decomposition is essential because overnight gap exposure has different execution risk and cost from an opening-session trade.

## Threshold ladder

Report fixed build-derived absolute intraday-return z thresholds:
- 80th percentile
- 90th percentile
- 95th percentile

Do not choose a winner from the same sample. The purpose is to test monotonicity and event sparsity.

## Chronology

Build threshold calibration:
- 2012-2018

Later evaluation:
- 2019-2021
- 2022-2024
- 2025-2026

## Economics

Report raw mean/median basis points, hit rate, event count, cumulative unlevered return, and break-even round-trip transaction cost in basis points for each window.

No claim about live profitability is made until venue-specific spread/financing/slippage is applied.
