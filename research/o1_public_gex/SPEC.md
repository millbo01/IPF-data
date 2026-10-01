# O1 — Public SPX GEX as a regime indicator

## Status
Frozen before outcome inspection; data-access repair recorded after incomplete extraction and before repaired outcomes are inspected.

## Research role
O1 is an **indicator test**, not a dealer-inventory measurement and not a standalone trading backtest.

The project now separates three verdicts:
1. mechanism validity;
2. indicator usefulness;
3. standalone tradability.

A failure of standalone tradability does not invalidate indicator usefulness. Conversely, a pass here does not establish a standalone trading edge.

## Question
After SPX has already moved during the first ~30 minutes of the regular session, does a static public options gamma/open-interest proxy help distinguish subsequent continuation from reversal?

## Public GEX proxy
Use both standard SPX and SPXW daily option universes.

For each target date:
- retrieve each option universe over a widened bracket and retain rows labelled with the target date only;
- keep contracts with positive gamma and positive open interest and a decodable call/put right;
- de-duplicate symbols across SPX/SPXW before aggregation if any overlap occurs;
- call sign = +1, put sign = -1;
- weight = gamma × open interest;
- `gex_ratio = sum(sign × weight) / sum(weight)`.

This is explicitly a **public static GEX proxy**. Open interest does not reveal actual dealer inventory, so no claim is made that the sign equals observed dealer gamma.

## Data-access repair
The first full extraction used `[date-1 calendar day, date+1 day]`. It recovered most dates but systematically missed Monday targets and sessions immediately following market holidays because the bracket did not reach the preceding trading session.

Before inspecting any repaired outcomes, the retrieval rule is therefore repaired as follows:
- for dates already successfully extracted, keep the existing observations unchanged;
- for dates that failed specifically with `No target-date option-universe rows`, retry only those dates using `[date-4 calendar days, date+1 day]`;
- after retrieval, still retain **only rows labelled with the original frozen target date**;
- do not replace frozen dates and do not alter any predictor, outcome, threshold, regression, matched comparison or pass/fail rule;
- dates failing for another reason remain failed unless the reason is independently identified as a data-access issue.

This is a retrieval-only repair intended to recover the same frozen observations across weekend/holiday boundaries.

## Timing and look-ahead
QuantConnect daily option-universe Greeks/open interest for a row dated `t` are used as information available for the following session. Retrieval widening is a data-access repair only; rows are filtered to the target date.

SPX minute timestamps in QuantBook display with an observed one-hour offset in this environment. To avoid hard-coding timezone corrections, morning outcomes are defined by regular-session-relative bar positions rather than displayed clock labels.

## SPX path construction
Request the regular session with the same history call used in the diagnostic. Sort returned minute bars.

- session start price: first returned minute close;
- ~30 minute price: 30th returned minute close (index 29);
- ~90 minute price: 90th returned minute close (index 89);
- session close price: final returned minute close.

Require at least 90 returned minute bars.

Define:
- `early_return = log(P30 / Popen)`;
- `direction = sign(early_return)`;
- `cont_1h = direction × log(P90 / P30)`;
- `cont_close = direction × log(Pclose / P30)`.

Positive continuation outcomes mean the initial morning move continues; negative values mean reversal.

## Frozen samples
### Build — 24 dates in 2024
2024-01-10, 2024-01-11, 2024-01-18, 2024-01-22, 2024-01-30, 2024-02-07, 2024-02-29, 2024-03-01, 2024-03-15, 2024-03-18, 2024-04-03, 2024-04-08, 2024-04-17, 2024-05-07, 2024-05-13, 2024-05-28, 2024-06-06, 2024-07-05, 2024-07-24, 2024-07-29, 2024-09-05, 2024-09-10, 2024-09-20, 2024-09-23.

### Holdout — 24 dates in 2025
2025-01-07, 2025-01-09, 2025-01-23, 2025-01-28, 2025-01-31, 2025-02-03, 2025-02-05, 2025-02-11, 2025-03-19, 2025-04-02, 2025-04-10, 2025-04-23, 2025-04-29, 2025-05-09, 2025-06-03, 2025-06-11, 2025-07-08, 2025-08-06, 2025-08-13, 2025-09-04, 2025-10-10, 2025-11-20, 2025-12-18, 2025-12-24.

Failed data dates are reported and not replaced.

## Primary test
Primary outcome: `cont_1h`.

OLS with HC1 standard errors:
`cont_1h ~ gex_ratio + abs(early_return)`.

Expected sign: beta on `gex_ratio` < 0.

Interpretation under the proxy hypothesis:
- lower/more negative public GEX -> greater continuation;
- higher/more positive public GEX -> greater damping/reversal.

P-values are descriptive and do not substitute for the directional gate.

## Non-parametric check
Compute build-sample 33rd and 67th percentile cutpoints of `gex_ratio`. Apply those cutpoints unchanged to holdout.

Compare mean continuation in:
- low-GEX group: `gex_ratio <= build q33`;
- high-GEX group: `gex_ratio >= build q67`.

Expected `low minus high > 0`.

## Secondary outcome
`cont_close` is descriptive only and cannot rescue a failed primary test.

## Holdout robustness
Leave one holdout date out at a time and recompute the primary regression and frozen matched check.

Count a leave-one-out version as directionally successful only when:
- beta on GEX < 0; and
- low-GEX minus high-GEX > 0.

## Frozen indicator gate
O1 indicator PASS requires all three:
1. BUILD primary regression beta < 0 and matched low-minus-high > 0;
2. HOLDOUT primary regression beta < 0 and matched low-minus-high > 0;
3. at least 80% of valid HOLDOUT leave-one-day-out versions retain both expected directions.

Otherwise the **public static GEX proxy fails as an indicator under O1**.

Failure does not reject the broader dealer-hedging mechanism; it rejects this cheap public proxy for the intended use.

## No trading promotion from O1 alone
Even if O1 passes, do not infer standalone tradability. Any later economic test must be separately frozen and must consider execution, costs, sizing, capital feasibility, and whether GEX is better used as a filter/state variable than as a direct signal.
