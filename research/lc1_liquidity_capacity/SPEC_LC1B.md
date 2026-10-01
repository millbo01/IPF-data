# LC1-B — Capacity restoration / release

## Status

Frozen after LC1-A and before LC1-B outcomes are examined.

LC1-A established, across ES, repaired ZN and CL, that comparable aggressive flow produces greater immediate same-direction displacement when pre-existing contra-side capacity is lower. LC1-A did not support a simple post-window continuation strategy.

LC1-B tests the previously stated next mechanism: whether the end of the capacity constraint can identify reversal of that temporary displacement.

Because LC1-A forward returns on its original dates have now been seen, LC1-B uses **new sampled dates not used in LC1-A**.

## Hypothesis

Among high-stress pressure/capacity episodes, subsequent reversal should be greater when both of the following occur during the next 30 seconds:

1. same-direction aggressive pressure decays; and
2. contra-side displayed capacity restores.

The trading decision is therefore made only after the 30-second pressure episode and the following 30-second release-observation window have completed.

## Markets

- ES — S&P 500 E-mini futures
- ZN — 10-Year U.S. Treasury Note futures
- CL — WTI Crude Oil futures

ZN uses the LC1-A data-access repair: among live ZN contracts expiring within 185 days, select the contract with greatest strict-trade quantity during 09:55–10:00, before any signal window begins. No outcome information is used for contract selection.

## Sampling

### Build — 24 newly sampled 2024 dates

Selected with fixed RNG seed 1702 from US federal-business dates in 2024:

- 2024-01-16
- 2024-02-05
- 2024-02-16
- 2024-02-29
- 2024-03-01
- 2024-03-06
- 2024-03-21
- 2024-03-29
- 2024-04-09
- 2024-04-30
- 2024-06-03
- 2024-07-02
- 2024-07-31
- 2024-08-12
- 2024-08-13
- 2024-09-25
- 2024-10-09
- 2024-10-18
- 2024-10-21
- 2024-11-08
- 2024-12-05
- 2024-12-20
- 2024-12-26
- 2024-12-31

### Holdout — 12 newly sampled 2026 dates

Selected with the same fixed RNG procedure from 2026-01-02 through 2026-08-31 after excluding all LC1-A holdout dates:

- 2026-01-13
- 2026-01-28
- 2026-01-29
- 2026-02-17
- 2026-02-24
- 2026-03-02
- 2026-04-16
- 2026-04-28
- 2026-06-04
- 2026-07-09
- 2026-07-21
- 2026-08-11

Failed dates are reported and not replaced after outcomes are seen.

## Time structure

- Contract-selection history for ZN: 09:55–10:00.
- Raw analysis history: 09:59–11:01.
- Initial pressure-window starts: 10:00:00 through 10:44:30.
- Initial pressure window: `[t, t+30s)`.
- Release-observation window: `[t+30s, t+60s)`.
- Earliest trading/reversal outcome begins at `t+60s`.

## Initial stress

LC1-A variables are retained:

- `P0` = aggressive signed quantity during `[t,t+30s)`;
- `log_pressure = log1p(abs(P0))`;
- `pre_capacity` = median original contra-side best-quote size during `[t-30s,t)`;
- `inv_capacity = -log1p(pre_capacity)`, so larger values mean less capacity.

For each market, using build predictor data only:

1. standardize `log_pressure` and `inv_capacity` using their build means/SDs;
2. `stress_score = z(log_pressure) + z(inv_capacity)`;
3. define high-stress episodes as those at or above the build 70th percentile of `stress_score`.

The build means, SDs and 70th-percentile cutoff are then applied unchanged to holdout.

## Release variables

All capacity measurements retain the side implied by the original pressure direction.

### Capacity restoration

- `event_capacity` = median original contra-side displayed size during `[t,t+30s)`;
- `release_capacity` = median same contra-side displayed size during `[t+30s,t+60s)`;
- `restoration = log1p(release_capacity) - log1p(event_capacity)`.

Positive restoration means contra-side capacity is greater after the pressure episode than while it was being absorbed.

### Pressure decay

- `P1` = aggressive signed quantity during `[t+30s,t+60s)`;
- `residual_same = max(sign(P0) * P1, 0)`;
- `decay = log1p(abs(P0)) - log1p(residual_same)`.

This deliberately treats opposite-direction P1 as full exhaustion of the original-direction pressure rather than using the reversal itself as a predictor.

For each market, restoration and decay are standardized using **high-stress build episodes only**. Those build means/SDs are applied unchanged to holdout.

The frozen joint-release interaction is:

`release_interaction = z(restoration) * z(decay)`.

## Outcomes

All outcomes use reconstructed mid-prices and are signed so positive means reversal against the original P0 direction.

Trading observation becomes available at `t+60s`.

Primary outcome:

`rev_5m = -sign(P0) * log(mid[t+360s] / mid[t+60s])`

Secondary descriptive outcomes:

- `rev_30s = -sign(P0) * log(mid[t+90s] / mid[t+60s])`
- `rev_60s = -sign(P0) * log(mid[t+120s] / mid[t+60s])`
- `rev_15m = -sign(P0) * log(mid[t+960s] / mid[t+60s])`

The 5-minute horizon is the sole primary statistical gate; the other horizons describe timing and are not alternative routes to pass the test.

## Primary regression

Within high-stress episodes, separately by market and sample:

`rev_5m ~ z(restoration) + z(decay) + z(restoration)*z(decay) + z(stress_score) + z(impact_30s) + z(pre_spread) + z(pre_rv) + five-minute time-bucket dummies`

Coefficient of interest:

`beta_release_interaction > 0`.

Inference uses day-clustered CR1 standard errors, not HC1, because event outcomes overlap within day.

## Matched / rule-like check

Using build high-stress episodes only, freeze the means of restoration and decay used for standardization.

For both build and holdout:

- **joint release**: `z(restoration) > 0` AND `z(decay) > 0`;
- **stalled constraint**: `z(restoration) <= 0` AND `z(decay) <= 0`.

Within terciles of `stress_score`, compare mean `rev_5m` for joint release minus stalled constraint, then equal-weight the available tercile differences.

Expected difference: positive.

This check is intentionally close to an eventual executable rule while remaining a mechanism test.

## Robustness

For each holdout market, repeat the primary regression and matched difference after dropping each holdout day in turn. Report the fraction of leave-one-day-out versions where both the interaction and matched difference remain positive.

## Frozen pass/fail rule

LC1-B passes its **reversal-mechanism gate** only if at least 2 of ES, ZN and CL satisfy all three holdout conditions:

1. primary 5-minute release-interaction coefficient > 0;
2. matched joint-release minus stalled-constraint 5-minute reversal difference > 0;
3. both conditions remain positive in at least 10 of 12 leave-one-day-out versions (or all available versions if fewer than 12 dates are usable).

Statistical p-values and confidence intervals are reported but do not substitute for the cross-market and leave-one-day-out requirements.

If fewer than 2 markets pass, LC1-B is killed as a trading mechanism under this specification.

If at least 2 markets pass, do not trade immediately. The next step is a separately frozen executable backtest using the joint-release rule with actual futures tick values, commissions, slippage, exposure overlap, and matched-risk S&P comparison.

## Research hygiene

- LC1-A dates are not reused.
- The 5-minute outcome is the only primary outcome for pass/fail.
- Secondary horizons cannot rescue a failed 5-minute result.
- No RSI, moving averages, OI, funding, trend, news or other filters are introduced.
- No failed date is replaced after outcome inspection.
- No threshold is optimized on returns.
- Raw licensed QuantConnect/AlgoSeek tick data are not committed to GitHub.
