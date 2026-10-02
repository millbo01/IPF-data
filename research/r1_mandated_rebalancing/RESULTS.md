# R1 results — mandated rebalancing

## Status

**Killed as a trading strategy in the frozen post-paper holdout.**

The historical mechanism replicated directionally in the paper-era sample, but it did not survive the post-paper holdout strongly enough to justify promotion or tuning.

## Frozen periods

- Paper-era/project replication sample: 2010-01-04 to 2023-03-17
- Post-paper holdout: 2023-03-20 to 2026-09-29

## Paper-era/project sample

Threshold predictive relationship:
- N = 3,322
- Corr = -0.1151
- Slope = -0.3310
- HC1 t = -3.5760
- Approx p = 0.000349
- 95% CI = [-0.5125, -0.1496]

Calendar predictive relationship, final five trading days:
- N = 790
- Corr = -0.0954
- Slope = -0.1020
- HC1 t = -1.5323
- Approx p = 0.12546
- 95% CI = [-0.2325, 0.0285]

Before-cost Sharpe:
- Threshold: 0.824
- Calendar: 0.375
- Combined: 0.817
- Frozen 5-day reversal control: 0.714
- ES buy-and-hold: 0.673

## Post-paper holdout

Threshold predictive relationship:
- N = 898
- Corr = -0.0673
- Slope = -0.1876
- HC1 t = -1.1030
- Approx p = 0.2700
- 95% CI = [-0.5208, 0.1457]

Calendar predictive relationship, final five trading days:
- N = 214
- Corr = -0.0254
- Slope = -0.0281
- HC1 t = -0.3366
- Approx p = 0.7364
- 95% CI = [-0.1914, 0.1353]

Before-cost performance:

| Strategy | AnnRet | AnnVol | Sharpe | MaxDD | CumRet |
|---|---:|---:|---:|---:|---:|
| Threshold | -0.59% | 5.85% | -0.101 | -11.21% | -2.68% |
| Calendar | 2.16% | 7.51% | 0.288 | -8.45% | 6.92% |
| Combined | 0.78% | 5.07% | 0.154 | -6.65% | 2.36% |
| 5-day reversal control | 5.26% | 15.38% | 0.342 | -17.68% | 15.68% |
| ES buy-and-hold | 15.74% | 14.56% | 1.081 | -19.52% | 68.74% |

Holdout yearly Combined Sharpe:
- 2023: 0.873
- 2024: 0.487
- 2025: 0.097
- 2026 through 2026-09-29: -0.968

Frozen reversal-control Sharpe by year:
- 2023: 0.672
- 2024: 1.455
- 2025: 0.262
- 2026 through 2026-09-29: -1.403

## Adjudication

The post-paper Threshold coefficient kept the expected negative sign but was not statistically distinguishable from zero and the Threshold strategy lost money before transaction costs. The Combined book produced only Sharpe 0.154 before costs and was weaker than both the frozen generic reversal control and passive ES over the same holdout. Performance deteriorated across the later holdout years and turned negative in 2026.

This is therefore not promoted to execution, and no parameter optimisation, cost modelling, or liquidity-conditioned enhancement is performed on R1. Any future return to this family should be treated as a new, separately pre-specified hypothesis rather than tuning R1 after the holdout was opened.

## Next research priority

Move to **LC1 — Liquidity Capacity**, testing whether equal signed aggressive flow has greater and more persistent price impact when observable absorption capacity is low. This is a distinct IPF mechanism rather than another forced-flow/strain variant.
