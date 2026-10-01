# COMB1 — Forced membership flow × absorption capacity

## Status
Frozen after RUS1 outcomes were inspected and before any 2026 price/volume outcomes were inspected.

## Research role
COMB1 is the first formal combination test. It asks whether the robust Russell reconstitution forced-flow mechanism becomes directionally useful when conditioned on a pre-event absorption-capacity proxy.

RUS1 established:
- closing-volume concentration: PASS;
- raw membership-direction pressure: FAIL;
- raw next-session reversal: FAIL.

COMB1 therefore does **not** rescue raw RUS1 by changing its verdict. It tests a new conditional claim against a new untouched year.

## Hypothesis
For the same rule-driven Russell 3000 membership flow, lower pre-event trading capacity should produce larger signed closing displacement.

Operationally:
- addition sign = +1;
- deletion sign = -1;
- outcome = the same placebo-adjusted, SPY-adjusted signed last-30-minute closing pressure used in RUS1;
- capacity proxy = pre-event 20-session median daily dollar volume (ADV20).

Prediction: as ADV20 falls, signed closing pressure rises.

ADV20 is a coarse public absorption-capacity proxy, not the BBO capacity measure used in LC1.

## Development and validation split
### Development
Use the already-inspected RUS1 observations from 2023, 2024 and 2025. These years are model-development data only and cannot serve as validation for COMB1.

### Untouched holdout
2026 Russell 3000 annual June reconstitution, effective after the US market close on 26 June 2026.

Use the first 30 rows of the official final Russell 3000 additions table and first 30 rows of the official final deletions table, matching the amended RUS1 deterministic sampling rule.

2026 additions, rows 1–30:
DIBS, ARX, ACHV, ABOS, AMTX, AVEX, AGEN, ALMR, ALM, ALTO, ANRO, ALXO, AREC, AP, AMPY, ASYS, ANTX, APC, ARMP, ARTV, ASND, ASMB, ATAI, AUGO, AVTX, AVLN, AVBC, AXTI, BW, BH.A.

2026 deletions, rows 1–30:
AARD, ARAY, ACTU, AISP, ALDX, ALIT, AOUT, AVD, CRMT, AREN, ARQ, ARAI, ACNT, ATLN, ATYR, AEYE, RCEL, BARK, BSET, BYND, BTMD, BYRN, CRDF, CLAR, CLPR, CSPI, DH, BOOM, DCGO, EML.

If a sampled security cannot be resolved or lacks the required windows, report it unavailable and do not replace it.

## Event construction
2026 event Friday: 2026-06-26.
Placebo Friday: 2026-06-19.

Use the same RUS1 construction:
- last-30-minute stock return, market-adjusted by SPY;
- signed by +1 addition / -1 deletion;
- subtract the same-security signed placebo-week value;
- call this `pressure_excess_bp`.

ADV20 is the median of close × volume over the 20 completed trading sessions before the event Friday.

## Capacity transform
For each year separately:
1. compute `log_adv = ln(ADV20)`;
2. compute `inv_capacity_z = -(log_adv - yearly_mean(log_adv)) / yearly_sd(log_adv)`.

Thus larger `inv_capacity_z` means lower capacity.

This within-year standardization is fixed before 2026 outcomes are viewed.

## Primary continuous check
### Development
OLS with HC1 errors on pooled 2023–2025 complete observations:

`pressure_excess_bp ~ inv_capacity_z + deletion_dummy + year_fixed_effects`

Expected coefficient on `inv_capacity_z`: positive.

### Holdout
OLS with HC1 errors on 2026 complete observations:

`pressure_excess_bp ~ inv_capacity_z + deletion_dummy`

Expected coefficient on `inv_capacity_z`: positive.

P-values and confidence intervals are descriptive; the gate is directional/robustness based.

## Frozen non-parametric capacity check
Within each year, rank observations by ADV20 using predictor values only.

- low-capacity group = bottom ADV20 quartile;
- high-capacity group = top ADV20 quartile.

For development, pool the within-year low-capacity observations across 2023–2025 and similarly pool the high-capacity observations.

For 2026, use 2026 quartiles only.

Define `capacity_spread = median(pressure_excess_bp in low-capacity) - median(pressure_excess_bp in high-capacity)`.

Expected sign: positive.

Also report within the 2026 low-capacity group:
- median pressure;
- fraction pressure > 0;
- addition median;
- deletion median.

## Holdout robustness
Leave one complete 2026 observation out at a time. Recompute:
- holdout coefficient on `inv_capacity_z`;
- holdout capacity spread using the fixed quartile rule on the remaining predictor values.

A leave-one-out version succeeds only if both are positive.

## Frozen COMB1 gate
PASS requires all of:
1. development coefficient on `inv_capacity_z` > 0;
2. development capacity spread > 0;
3. 2026 holdout coefficient on `inv_capacity_z` > 0;
4. 2026 capacity spread > 0;
5. 2026 low-capacity median pressure > 0;
6. 2026 low-capacity fraction pressure > 0 >= 0.60;
7. 2026 low-capacity addition median > 0;
8. 2026 low-capacity deletion median > 0;
9. at least 80% of valid 2026 leave-one-out versions retain both positive coefficient and positive capacity spread.

Otherwise COMB1 fails.

## No rescue/tuning
After 2026 outcomes are viewed, do not:
- change the 2026 event or placebo date;
- change the first-30-per-side sample;
- replace unavailable securities;
- change ADV20 to another liquidity variable;
- change the 20-session window;
- change within-year z-scoring;
- change quartiles;
- drop additions or deletions;
- introduce market-cap, sector, price, volatility or other filters to rescue the gate.

## Economic promotion
COMB1 is still an indicator/mechanism interaction test, not a P&L backtest. If COMB1 passes, the next step is a separately frozen economic simulation using entry before the closing auction, realistic execution/slippage, position limits, and a venue compatible with approximately £2,000 capital.
