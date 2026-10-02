# NDX/QQQ next-session morning fade — IG execution V2 results

## Result status

Completed from QuantConnect backtest result JSON using the frozen V2 rules and the live-account IG DFB metadata already captured on the research branch.

Primary rule remains:
- NDX/QQQ signal with fixed build-derived thresholds P80 1.2681, P90 1.7796, P95 2.3646;
- fade on T+1;
- 09:31 New York entry, 10:00 exit;
- IG US Tech 100 DFB representative spread schedule;
- £2,000 account;
- 1x account-notional stake rounded to the confirmed £0.01/point increment;
- 5% margin.

09:32 and 09:35 are sensitivity checks only. They are not used to replace 09:31.

## Bottom line

**P80 fails as an executable general rule.** In the current 2022-2026 regime it is only 0.22 bp net per trade, and under 2x spread stress it turns negative.

**P90 is the strongest executable candidate under the frozen 09:31 rule.** Across 2022-2026 it has 104 trades, 7.09 bp net mean, -0.35 bp median, 50.0% net hit rate, and the £2,000 1x-notional path ends at £2146.23 with -3.6% max closed-trade drawdown. Under 2x spread stress the mean remains positive.

**P95 retains the larger conditional effect but is too sparse and regime-sensitive to stand alone.** Across 2022-2026 it has only 47 trades. Its net mean is 13.02 bp, but 2019-2021 was sharply negative and 2026-to-date is also negative on only four events.

The chronology matters: P90 was +22.45 bp net in 2025 (19 trades) but -9.82 bp in 2026-to-date (10 trades). This is not a smooth stationary edge.

The 09:35 sensitivity looks much stronger in the recent/holdout samples, but it was worse in build. It therefore **must not be promoted** from this sample; doing so would be timestamp optimization.

SPX is weaker overall and does not provide a reason to broaden the rule beyond Nasdaq.

## Primary 09:31 results

| Period | Threshold | n | Gross mean bp | Net mean bp | Net median bp | Net hit | End £ | Max DD | BE cost pts |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BUILD | P80 | 337 | 0.70 | -1.88 | -6.79 | 43.3% | 1870.28 | -13.1% | 0.71 |
| BUILD | P90 | 169 | 3.06 | 0.57 | -5.26 | 45.0% | 2012.21 | -6.7% | 2.09 |
| BUILD | P95 | 85 | 7.71 | 5.24 | -8.75 | 47.1% | 2084.76 | -4.6% | 4.65 |
| 2019_2021 | P80 | 98 | 2.81 | 1.51 | 5.12 | 54.1% | 2026.51 | -5.8% | 3.44 |
| 2019_2021 | P90 | 52 | 0.03 | -1.42 | 6.54 | 55.8% | 1981.27 | -6.5% | 0.27 |
| 2019_2021 | P95 | 28 | -16.13 | -17.73 | 2.01 | 50.0% | 1898.96 | -6.9% | -14.99 |
| 2022_2024 | P80 | 161 | -0.09 | -0.83 | -1.48 | 47.2% | 1967.43 | -6.5% | -0.27 |
| 2022_2024 | P90 | 75 | 6.18 | 5.46 | -2.11 | 48.0% | 2079.60 | -3.6% | 8.90 |
| 2022_2024 | P95 | 34 | 8.95 | 8.25 | 14.07 | 52.9% | 2056.19 | -2.1% | 10.68 |
| 2025_2026 | P80 | 68 | 3.23 | 2.73 | 1.51 | 51.5% | 2038.80 | -4.2% | 3.07 |
| 2025_2026 | P90 | 29 | 11.81 | 11.32 | 10.50 | 55.2% | 2066.64 | -1.4% | 15.28 |
| 2025_2026 | P95 | 13 | 26.01 | 25.50 | 10.50 | 53.8% | 2066.55 | -0.8% | 41.63 |
| HOLDOUT | P80 | 327 | 1.47 | 0.61 | 0.29 | 50.2% | 2028.05 | -6.4% | 1.54 |
| HOLDOUT | P90 | 156 | 5.17 | 4.26 | 3.01 | 51.9% | 2125.38 | -6.5% | 7.21 |
| HOLDOUT | P95 | 75 | 2.55 | 1.54 | 9.67 | 52.0% | 2018.48 | -6.9% | 6.46 |
| CURRENT_2022_2026 | P80 | 229 | 0.89 | 0.22 | -0.87 | 48.5% | 2001.38 | -6.5% | 0.72 |
| CURRENT_2022_2026 | P90 | 104 | 7.75 | 7.09 | -0.35 | 50.0% | 2146.23 | -3.6% | 10.68 |
| CURRENT_2022_2026 | P95 | 47 | 13.67 | 13.02 | 12.31 | 53.2% | 2124.18 | -2.1% | 19.24 |

## P90 holdout account economics

For 2019-2026:
- trades: 156
- gross mean: 5.17 bp
- net mean: 4.26 bp
- net median: 3.01 bp
- net hit rate: 51.9%
- break-even full round-trip cost: 5.17 bp / 7.21 index points
- base ending equity: £2125.38
- base max drawdown: -6.5%
- base margin utilisation, 95th percentile / max: 5.17% / 5.25%
- 2x-spread net mean: 3.34 bp
- 2x-spread ending equity: £2096.86
- 2x-spread max drawdown: -6.8%

At the live minimum stake of £0.01/point, the same holdout P90 path earns only a few pounds; the edge is economically too small at minimum size. The 1x-notional convention is therefore the useful small-account representation.

## Entry-time sensitivity

| Period | Threshold | 09:31 net bp | 09:32 net bp | 09:35 net bp |
|---|---|---:|---:|---:|
| BUILD | P80 | -1.88 | -2.73 | -4.11 |
| BUILD | P90 | 0.57 | -1.04 | -3.84 |
| BUILD | P95 | 5.24 | 1.69 | -2.31 |
| 2022_2024 | P80 | -0.83 | -1.79 | 1.79 |
| 2022_2024 | P90 | 5.46 | 3.14 | 8.47 |
| 2022_2024 | P95 | 8.25 | 6.28 | 13.33 |
| 2025_2026 | P80 | 2.73 | 3.66 | 10.90 |
| 2025_2026 | P90 | 11.32 | 11.13 | 21.97 |
| 2025_2026 | P95 | 25.50 | 24.84 | 31.68 |
| HOLDOUT | P80 | 0.61 | 0.29 | 4.89 |
| HOLDOUT | P90 | 4.26 | 3.58 | 11.00 |
| HOLDOUT | P95 | 1.54 | 1.98 | 10.92 |
| CURRENT_2022_2026 | P80 | 0.22 | -0.17 | 4.49 |
| CURRENT_2022_2026 | P90 | 7.09 | 5.37 | 12.23 |
| CURRENT_2022_2026 | P95 | 13.02 | 11.41 | 18.40 |

## Year-by-year chronology

Cells are `trade count / net mean bp` for the frozen 09:31 rule.

| Year | P80 n / net bp | P90 n / net bp | P95 n / net bp |
|---:|---:|---:|---:|
| 2012 | 52 / -7.54 | 23 / -14.63 | 12 / -14.25 |
| 2013 | 35 / -12.55 | 13 / -17.68 | 5 / -23.92 |
| 2014 | 51 / -5.66 | 26 / +6.11 | 13 / +7.76 |
| 2015 | 63 / +8.53 | 30 / +18.95 | 12 / +45.83 |
| 2016 | 33 / -6.70 | 14 / -22.14 | 8 / -30.88 |
| 2017 | 34 / -1.16 | 14 / -11.30 | 7 / -19.43 |
| 2018 | 69 / +3.01 | 49 / +8.24 | 28 / +16.72 |
| 2019 | 23 / -7.33 | 9 / +3.83 | 3 / -4.72 |
| 2020 | 51 / +4.20 | 35 / -6.07 | 23 / -19.18 |
| 2021 | 24 / +4.26 | 8 / +13.00 | 2 / -20.67 |
| 2022 | 89 / +1.78 | 49 / +6.88 | 22 / +12.64 |
| 2023 | 18 / -11.49 | 1 / -47.33 | — |
| 2024 | 54 / -1.58 | 25 / +4.78 | 12 / +0.20 |
| 2025 | 40 / +11.84 | 19 / +22.45 | 9 / +41.43 |
| 2026 | 28 / -10.30 | 10 / -9.82 | 4 / -10.33 |

## Interpretation

1. The broad low-threshold version (P80) does not survive execution strongly enough.
2. P90 survives representative IG costs and 2x spread stress in the post-2021 regime and in the full 2019-2026 holdout aggregate.
3. P95 is stronger in post-2021 averages but has too few observations and a large regime failure in 2019-2021.
4. The return distribution is heavy-tailed. Median and hit-rate evidence are much less dramatic than the mean, especially in build.
5. 2026-to-date is negative at all three thresholds, which prevents treating the strong 2025 result as a stable current expectation.
6. The observed 09:35 improvement is not stable through build and cannot be selected without a new pre-specified experiment.
7. SPX is a weaker comparator; the candidate remains Nasdaq-specific.

## Research disposition

**Do not deploy this as a finished live strategy yet.**

The candidate is not dead: P90, and secondarily P95, survive the small-account execution translation far better than MAIN did. But the next research question is now about **stability and forward validation**, not transaction costs or minimum stake.

The clean next step is to freeze P90/09:31 as the primary candidate and run a genuinely forward paper/live-shadow phase, while retaining P95 as a pre-specified high-conviction subset. No threshold, timestamp, direction or volatility optimization should be added on this historical sample.
