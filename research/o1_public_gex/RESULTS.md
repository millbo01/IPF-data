# O1 — Public SPX GEX as a regime indicator — Results

## Final status
**INDICATOR GATE: FAIL** under the frozen rule.

This is an indicator verdict only. It does **not** reject the broader options/dealer-hedging mechanism and does not speak to standalone tradability beyond this proxy.

## Data access
QuantConnect option-universe access was validated for SPX/SPXW. A retrieval quirk caused several target dates to return no option-universe rows, especially around Monday/holiday boundaries. A retrieval-only repair using a wider four-calendar-day lookback was frozen and attempted before final adjudication, but it did not recover the missing dates. Failed dates were not replaced.

Usable observations:
- BUILD: 16 / 24
- HOLDOUT: 22 / 24

Remaining BUILD failures: 2024-01-22, 2024-03-18, 2024-04-08, 2024-05-13, 2024-05-28, 2024-07-05, 2024-07-29, 2024-09-23.

Remaining HOLDOUT failures:
- 2025-01-09: no SPX minute history
- 2025-02-03: no target-date option-universe rows

## Frozen primary results
Primary outcome: continuation over the hour after the first ~30-minute SPX move.

Expected directions:
- beta on public GEX ratio < 0
- low-GEX minus high-GEX continuation > 0

BUILD (N=16):
- beta on GEX: -95.3454 bp
- 95% interval: [-211.5297, 20.8389] bp
- p ~= 0.1077
- matched low-minus-high: +13.4933 bp
- directional build gate: PASS

HOLDOUT (N=22):
- beta on GEX: -10.5592 bp
- 95% interval: [-110.5947, 89.4763] bp
- p ~= 0.8361
- matched low-minus-high: +3.6555 bp
- directional holdout gate: PASS

Holdout leave-one-day-out:
- both expected directions: 15/22
- share: 0.682
- frozen requirement: >= 0.80
- beta range: -33.4832 to +22.4519 bp
- matched-difference range: -4.3303 to +13.0840 bp
- robustness gate: FAIL

## Final adjudication
Frozen O1 rule required all three:
1. BUILD expected directions;
2. HOLDOUT expected directions;
3. >=80% of valid HOLDOUT leave-one-day-out versions retaining both expected directions.

Results:
- BUILD directions: PASS
- HOLDOUT directions: PASS
- HOLDOUT LOO >=80%: FAIL (68.2%)

Therefore:

> The static call-minus-put gamma × open-interest proxy is not sufficiently stable as an indicator under O1.

## Research interpretation
The expected sign appears in both build and holdout, but the holdout effect is weak and unstable to individual-day removal. Do not promote this static public GEX construction into the indicator library as a validated input, and do not spend further time optimizing this same proxy on these samples.

A future options-hedging test would need materially better information about directional dealer inventory or a different dynamic construction; that would be a new hypothesis/test, not a rescue of O1.
