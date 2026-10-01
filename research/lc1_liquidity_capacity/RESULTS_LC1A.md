# LC1-A — Final results

## Status

**Immediate mechanism: PASS across ES, ZN and CL.**  
**Forward-continuation trading edge: FAIL under the frozen specification.**

LC1-A tested whether the same aggressive signed flow causes larger price displacement when pre-existing observable contra-side capacity is lower.

The original continuous-ZN extraction failed because the mapped continuous symbol supplied quotes but no usable signal-period trades. A pre-signal data-access repair selected the live ZN contract with greatest strict-trade quantity during the five minutes immediately before the signal window. This did not change dates, windows, outcomes, thresholds, or the hypothesis.

## Frozen construction

- Markets: ES, ZN, CL
- Build: 24 preselected dates in 2025
- Holdout: 12 preselected dates in 2026
- Signal interval: 10:00–10:44:30
- Non-overlapping window: 30 seconds
- Capacity: median contra-side displayed top-of-book size during the preceding 30 seconds
- Pressure: aggressive signed trade quantity during the 30-second window
- Primary interaction: standardized log pressure × inverse capacity
- Immediate outcome: signed 30-second contemporaneous mid-price return
- Forward outcomes: 30s, 60s, 5m, 15m after the signal window
- Matched check: low-capacity minus high-capacity directional return within pressure quintiles

## Holdout immediate-mechanism results

| Market | Interaction beta | 95% CI | p approx | Matched low-high | LOO joint-positive |
|---|---:|---:|---:|---:|---:|
| ES | +0.3854 bp | [+0.1807, +0.5901] | 0.0002 | +1.7245 bp | 12/12 |
| ZN | +0.0596 bp | [+0.0200, +0.0991] | 0.0032 | +0.2396 bp | 12/12 |
| CL | +1.7635 bp | [+0.7754, +2.7517] | 0.0005 | +4.3664 bp | 12/12 |

All three markets therefore satisfy both frozen directional conditions in the holdout, and all three remain joint-positive after dropping each holdout day in turn.

## Build-sample immediate results

- ES: interaction +0.3296 bp; matched +1.1355 bp.
- ZN: interaction +0.1541 bp; matched +0.3571 bp.
- CL: interaction +0.0040 bp; matched +0.9696 bp.

The ES and ZN immediate effects replicate from build into holdout. CL's matched effect is positive in both periods, while its regression interaction is near zero in build and strongly positive in holdout, indicating more regime variation.

## Forward-continuation results

No market satisfied the frozen forward-structure promotion gate.

### ES holdout

- 30s: interaction -0.1382 bp; matched +0.0115 bp
- 60s: interaction -0.3020 bp; matched -0.2100 bp
- 5m: interaction -0.6447 bp; matched -1.3155 bp
- 15m: interaction -1.1437 bp; matched +0.5045 bp
- No forward horizon survived the leave-one-day-out joint-positive rule.

### ZN holdout

- 30s: interaction -0.0315 bp; matched -0.0498 bp
- 60s: interaction -0.0244 bp; matched +0.0076 bp
- 5m: interaction -0.0650 bp; matched +0.1154 bp
- 15m: interaction -0.1614 bp; matched +0.4206 bp
- No forward horizon survived the leave-one-day-out joint-positive rule.

### CL holdout

- 30s: interaction -0.5223 bp; matched +0.3706 bp
- 60s: interaction -1.4579 bp; matched -0.9263 bp
- 5m: interaction +1.2332 bp; matched -0.4767 bp
- 15m: interaction +1.9805 bp; matched +2.6589 bp
- No forward horizon met the strict all-days leave-one-day-out rule.

## Adjudication

The IPF-level mechanism survives strongly:

> For comparable aggressive flow, lower pre-existing contra-side capacity is associated with greater immediate same-direction price displacement.

This result appears in all three frozen markets and all three 2026 holdouts, with leave-one-day-out robustness.

However, the simple trading interpretation — enter after observing the 30-second high-pressure/low-capacity episode and continue in the same direction — is rejected. The effect appears largely contemporaneous, and several forward estimates are negative.

Therefore LC1-A is recorded as a **validated immediate-impact mechanism, not a promoted trading strategy**.

## Next pre-specified research step

Proceed to LC1-B: test whether restoration/replenishment of contra-side capacity, combined with pressure decay, identifies the end or reversal of the temporary displacement. LC1-B must be frozen before its outcomes are examined.
