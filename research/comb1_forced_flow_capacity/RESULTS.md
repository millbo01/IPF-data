# COMB1 — Forced membership flow × absorption capacity

## Final verdict
**FAIL** under the frozen gate.

## Coverage
- Development (RUS1 2023–2025 complete observations): 178
- 2026 frozen sample: 60
- 2026 resolved: 60
- 2026 complete: 59
- Missing 2026 observation: ALIT deletion (no minute history); not replaced.

## Continuous capacity test
Expected coefficient on inverse capacity: positive.

### Development 2023–2025
- N = 178
- beta = -26.3021 bp/z
- 95% CI = [-98.5494, +45.9453]
- t = -0.714
- p ~= 0.4755

### Holdout 2026
- N = 59
- beta = +41.4555 bp/z
- 95% CI = [-99.3541, +182.2651]
- t = +0.577
- p ~= 0.5639

## Quartile check
Expected low-capacity minus high-capacity median pressure: positive.

### Development
- low-capacity N = 45
- high-capacity N = 45
- low-capacity median = +137.0718 bp
- high-capacity median = +31.4821 bp
- spread = +105.5897 bp
- low-capacity fraction positive = 0.6222
- low-capacity addition median = -10.8202 bp
- low-capacity deletion median = +157.7372 bp

### Holdout 2026
- low-capacity N = 15
- high-capacity N = 15
- low-capacity median = +296.3424 bp
- high-capacity median = +312.9747 bp
- spread = -16.6323 bp
- low-capacity fraction positive = 0.6000
- low-capacity addition median = +134.6484 bp
- low-capacity deletion median = +296.3424 bp

## Holdout leave-one-out
- both beta > 0 and capacity spread > 0: 8 / 59
- share = 0.136
- beta range = +0.6059 to +79.4404 bp/z
- spread range = -277.3272 to +16.5441 bp

## Frozen gate components
1. Development beta > 0: **FAIL**
2. Development spread > 0: PASS
3. 2026 beta > 0: PASS
4. 2026 spread > 0: **FAIL**
5. 2026 low-capacity median > 0: PASS
6. 2026 low-capacity fraction positive >= 0.60: PASS
7. 2026 low-capacity additions median > 0: PASS
8. 2026 low-capacity deletions median > 0: PASS
9. 2026 LOO >= 80%: **FAIL**

## Interpretation
COMB1 does not support the specific claim that low pre-event ADV20 reliably identifies larger signed Russell closing displacement. The continuous and quartile forms disagree in development, the 2026 quartile spread has the wrong sign, and the holdout leave-one-out robustness is far below the frozen requirement.

This failure does not reverse RUS1's mechanism result (forced closing-volume concentration remains supported) and does not reverse LC1's separate order-book-capacity result. It rejects this coarse cross-domain composition using ADV20 as the capacity proxy for Russell reconstitution directionality.

No rescue/tuning is permitted under the frozen specification.
