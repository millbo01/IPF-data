# R1 — Mandated Rebalancing: first frozen run

Date evaluated: 2026-10-02

## Decision

**DEPRIORITIZE. Do not advance to R1.1.**

The holdout retains the predicted negative Threshold sign, but the rebalancing construction does not show a meaningful advantage over the frozen generic 5-day reversal control.

This meets the frozen R1 deprioritization gate.

## Data

QuantConnect continuous futures:
- ES
- ZN
- daily
- open-interest mapped front contract
- backwards-ratio normalization

Common observations:
- 4,223
- 2010-01-04 to 2026-09-30

Frozen split:
- paper-era proxy: 2010-01-04 to 2023-03-17
- post-paper holdout: 2023-03-20 to 2026-09-30

## Predictive relationships

### Paper-era project sample

Threshold -> next-day ES minus ZN:
- N 3,322
- correlation -0.1151
- slope -0.3310
- HC1 t -3.576
- approximate p 0.00035
- 95% CI [-0.5125, -0.1496]

Calendar -> next-day ES minus ZN during final 5 trading days:
- N 790
- correlation -0.0954
- slope -0.1020
- HC1 t -1.532
- approximate p 0.1255
- 95% CI [-0.2325, 0.0285]

### Post-paper holdout

Threshold -> next-day ES minus ZN:
- N 899
- correlation -0.0673
- slope -0.1876
- HC1 t -1.103
- approximate p 0.2700
- 95% CI [-0.5208, 0.1457]

Calendar -> next-day ES minus ZN during final 5 trading days:
- N 214
- correlation -0.0258
- slope -0.02845
- HC1 t -0.341
- approximate p 0.7329
- 95% CI [-0.1918, 0.1349]

Interpretation:
- Threshold keeps the predicted negative sign in holdout.
- Magnitude is weaker and uncertainty is wide.
- Calendar is weak in both project periods.

## Strategy proxies before transaction costs

### Paper-era

| Strategy | AnnRet | AnnVol | Sharpe | MaxDD | CumRet |
|---|---:|---:|---:|---:|---:|
| Threshold | 9.08% | 11.02% | 0.824 | -11.33% | 206.97% |
| Calendar | 3.95% | 10.52% | 0.375 | -22.96% | 56.49% |
| Combined | 6.52% | 7.98% | 0.817 | -12.69% | 126.50% |
| 5d reversal control | 14.45% | 20.22% | 0.714 | -45.86% | 411.65% |
| ES buy-and-hold | 11.99% | 17.81% | 0.673 | -34.21% | 293.84% |

### Post-paper holdout

| Strategy | AnnRet | AnnVol | Sharpe | MaxDD | CumRet |
|---|---:|---:|---:|---:|---:|
| Threshold | -0.60% | 5.84% | -0.102 | -11.21% | -2.70% |
| Calendar | 2.20% | 7.50% | 0.294 | -8.45% | 7.10% |
| Combined | 0.80% | 5.07% | 0.158 | -6.65% | 2.44% |
| 5d reversal control | 5.24% | 15.37% | 0.341 | -17.68% | 15.60% |
| ES buy-and-hold | 15.66% | 14.56% | 1.076 | -19.52% | 68.38% |

The Combined proxy has lower drawdown than the control, but substantially lower annualized return, cumulative return and Sharpe. Under the frozen decision rule this is not a meaningful informational advantage over generic reversal.

## Holdout chronology

Combined annualized return / Sharpe:
- 2023: +4.11% / 0.873
- 2024: +2.28% / 0.487
- 2025: +0.59% / 0.097
- 2026: -4.28% / -0.945

5d reversal control:
- 2023: +8.97% / 0.672
- 2024: +19.45% / 1.455
- 2025: +5.25% / 0.262
- 2026: -17.32% / -1.406

The Combined proxy deteriorates monotonically across the observed holdout years.

## Frozen-gate adjudication

R1 says to deprioritize if either:
1. Threshold loses the predicted negative sign; or
2. Combined has no meaningful advantage over the frozen 5-day reversal control.

Gate 1 does **not** fail: Threshold remains negative.

Gate 2 **fails**:
- Combined holdout Sharpe 0.158 vs control 0.341;
- Combined annualized return 0.80% vs control 5.24%;
- Combined cumulative return 2.44% vs control 15.60%.

The lower Combined drawdown does not offset the lack of predictive/economic advantage for the purpose of this mechanism screen.

## Disposition

- **R1 mechanism:** weak descriptive survival only.
- **R1 strategy:** fail/deprioritize.
- **R1.1 execution realism:** do not run.
- **IPF capacity interaction extension:** do not run from this R1 branch because the base rebalancing construction did not clear its own control gate.
- No threshold, calendar-window, scaling or control-horizon tuning on this sample.
