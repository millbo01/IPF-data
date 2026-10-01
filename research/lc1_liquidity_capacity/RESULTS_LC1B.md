# LC1-B — Final results

## Status

**Reversal-mechanism gate: PASS (2/3 markets).**  
**Trading candidate: KILLED by economic triage.**

- ES: mechanism PASS, exact trade FAIL economically across build/holdout
- CL: mechanism PASS under the frozen gate, not advanced after ES economic failure
- ZN: mechanism FAIL

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

## ES detail before economic triage

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

These mechanism comparisons justified one cheap in-memory economic screen, but not further data extraction.

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

However, build matched difference was negative (-2.4749 bp) while holdout turned positive. CL remains supporting mechanism evidence but is not advanced after the ES economic screen fails.

## ES economic triage — no new history requests

The exact already-defined ES trading candidate was evaluated using the LC1-B panel already in memory.

Signal:
- ES only
- high-stress = true
- joint release = restoration z > 0 and pressure-decay z > 0
- fade original P0 direction at t+60s
- exit 5 minutes later
- take only the first eligible signal while flat; ignore overlapping signals

### Raw eligible events

| Split | Events | Mean gross bp | Median gross bp | Hit rate |
|---|---:|---:|---:|---:|
| Build | 135 | -0.8779 | -0.4900 | 45.93% |
| Holdout | 144 | +1.2213 | +0.8646 | 52.08% |

### Non-overlapping executable stream

| Split | Trades | Trades/sample day | Mean gross bp/trade | Median bp | Hit rate | Gross bp/sample day | Positive-day share |
|---|---:|---:|---:|---:|---:|---:|---:|
| Build | 69 | 3.000 | -0.2251 | +0.4188 | 52.17% | -0.6753 | 30.43% |
| Holdout | 62 | 5.167 | +2.4782 | +1.7958 | 58.06% | +12.8040 | 83.33% |

Build leave-one-day-out mean expectancy was positive in only 1/23 versions; the minimum LOO mean was -0.9869 bp/trade and maximum +0.0771 bp/trade.

Holdout leave-one-day-out mean expectancy was positive in 12/12 versions; the minimum LOO mean was +1.9993 bp/trade and maximum +2.7362 bp/trade.

The exact candidate therefore exhibits a severe build/holdout regime split. Crucially, the build stream has **negative gross expectancy before any transaction cost**.

## Final adjudication

LC1-B is retained as a **conditional reversal mechanism result**, especially in ES and CL, but it is **not promoted as a trading strategy**.

The exact executable ES rule fails the economic requirement because build expectancy is negative before transaction costs. Strong 2026 holdout performance is not sufficient justification to tune the already-opened sample.

No further QuantConnect tick extraction, parameter optimization, venue research, or live implementation should be performed for this LC1 trading rule on the same sample.

## Durable LC1 conclusion

LC1-A remains the strongest result:

> For comparable aggressive flow, lower pre-existing contra-side capacity produces larger immediate price displacement across ES, ZN and CL.

LC1-B adds evidence that restoration/pressure decay can condition later reversal in some markets, but that conditional relationship did not translate into a stable positive-expectancy trading rule across build and holdout.
