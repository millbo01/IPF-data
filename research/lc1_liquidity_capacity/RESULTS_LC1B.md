# LC1-B — Final results

## Status

**Reversal-mechanism gate: PASS (2/3 markets).**

- ES: PASS
- CL: PASS under the frozen gate
- ZN: FAIL

LC1-B tested whether, after a high pressure / low-capacity displacement, reversal is stronger when same-direction pressure decays and contra-side displayed capacity restores during the following 30 seconds.

## Data and frozen structure

- New dates only; LC1-A dates were not reused.
- Build: 24 preselected dates in 2024; Good Friday 2024-03-29 produced no usable data in all three markets and was not replaced.
- Holdout: 12 preselected dates in 2026; all usable.
- Initial pressure/displacement window: 30 seconds.
- Release-observation window: following 30 seconds.
- Trading decision time: only after the release window completes, at t+60s.
- High-stress events: top 30% by build-calibrated combination of pressure magnitude and inverse pre-existing capacity.
- Release variables: contra-side capacity restoration and same-direction pressure decay.
- Primary outcome: 5-minute reversal from t+60s.
- Primary regression inference: day-clustered standard errors.
- Non-parametric check: joint release (restoration>0 and decay>0) versus stalled (restoration<=0 and decay<=0), within frozen stress terciles.
- Holdout robustness: leave one day out; market passes only if at least 10/12 versions retain both positive regression interaction and positive matched difference.

## Extraction summary

| Market | Split | Attempted | Usable | Failed | Mean valid windows |
|---|---|---:|---:|---:|---:|
| ES | Build | 24 | 23 | 1 | 89.87 |
| ES | Holdout | 12 | 12 | 0 | 89.50 |
| ZN | Build | 24 | 23 | 1 | 89.61 |
| ZN | Holdout | 12 | 12 | 0 | 89.42 |
| CL | Build | 24 | 23 | 1 | 88.83 |
| CL | Holdout | 12 | 12 | 0 | 88.83 |

## Holdout primary 5-minute result

| Market | Release interaction beta | 95% CI | p approx | Joint-release minus stalled | LOO both-positive | Frozen market verdict |
|---|---:|---:|---:|---:|---:|---|
| ES | +0.3283 bp | [-0.3856, +1.0422] | 0.3674 | +1.3961 bp | 12/12 | PASS |
| ZN | +0.0460 bp | [-0.4288, +0.5207] | 0.8495 | -0.1644 bp | 1/12 | FAIL |
| CL | +2.0484 bp | [-0.1431, +4.2399] | 0.0669 | +1.2699 bp | 10/12 | PASS |

The frozen gate did not require the clustered regression p-value itself to be below 0.05; it required positive regression and matched directions plus the pre-specified leave-one-day-out robustness rule.

## ES detail

ES is the strongest candidate for economic follow-up.

Build primary 5m:
- interaction: -0.2976 bp
- matched joint-release minus stalled: +0.5249 bp

Holdout primary 5m:
- interaction: +0.3283 bp
- matched joint-release minus stalled: +1.3961 bp
- leave-one-day-out both-positive: 12/12

Holdout joint-release absolute mean reversal by stress tercile:
- T0: +1.6748 bp
- T1: +2.1999 bp
- T2: +0.4751 bp

Holdout stalled means:
- T0: -0.7017 bp
- T1: -0.0038 bp
- T2: +0.8669 bp

ES therefore passes the frozen gate robustly, although the regression interaction itself is imprecise and the highest-stress tercile does not show the largest matched advantage.

## ZN detail

ZN fails the primary mechanism:
- holdout interaction positive but near zero (+0.0460 bp)
- matched difference negative (-0.1644 bp)
- only 1/12 leave-one-day-out variants retain both positive directions
- only 75 holdout observations qualify as high stress under build calibration

ZN is not promoted.

## CL detail

CL formally passes the frozen gate:
- holdout interaction +2.0484 bp
- matched difference +1.2699 bp
- 10/12 leave-one-day-out variants retain both positive directions

However, absolute 5-minute joint-release reversal is less economically convincing than ES and is non-monotone across stress terciles:
- T0: +0.1468 bp
- T1: +0.6009 bp
- T2: +1.8785 bp

The build matched difference was negative (-2.4749 bp), while the holdout turned positive. CL is therefore retained as supporting evidence but is not the first market for an execution-feasibility screen.

## Adjudication

LC1-B survives its frozen cross-market gate: ES and CL pass, ZN fails.

The practical promotion decision is narrower than the formal mechanism gate. ES is advanced first because it combines:

1. a validated LC1-A immediate capacity effect;
2. positive absolute 5-minute reversal after joint release in every holdout stress tercile;
3. a positive holdout matched difference;
4. 12/12 leave-one-day-out robustness.

CL remains secondary because its build/holdout behavior is less stable and the absolute reversal magnitude is likely more vulnerable to transaction costs. ZN is stopped.

## Next step

Before any further tick-data extraction, run an in-memory ES-only economic feasibility screen using the already extracted LC1-B panel. Measure signal count, overlap, gross 5-minute reversal distribution, break-even round-trip cost in basis points, and a simple non-overlapping event stream. Only if the gross edge leaves credible room for real execution costs should additional tick extraction or venue-specific backtesting be performed.
