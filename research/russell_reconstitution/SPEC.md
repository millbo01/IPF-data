# RUS1 — Russell reconstitution closing-flow test

## Status
Frozen before price/volume outcome inspection.

## Research role
RUS1 separates three questions:
1. **Mechanism validity** — does annual Russell reconstitution concentrate abnormal trading into the closing auction?
2. **Directional usefulness** — do additions experience positive and deletions negative market-adjusted price pressure into the reconstitution close, relative to a same-security placebo week?
3. **Reversal opportunity** — does that signed closing pressure reverse after the forced-flow event ends?

A pass/fail on any one question does not determine the other two.

## Institutional mechanism
FTSE Russell announces final annual Russell US index changes in advance and implements the reconstitution after the close of the final Friday in June. FTSE Russell states that NYSE-listed securities use the NYSE closing auction and Nasdaq-listed securities use the Nasdaq Closing Cross for the reconstitution close.

The forced-flow prediction is therefore:
- Russell 3000 **addition**: passive/index-tracking demand is mechanically positive into the effective close;
- Russell 3000 **deletion**: passive/index-tracking demand is mechanically negative into the effective close.

The test does not assume that all price impact is temporary.

## Official event sources
Use only FTSE Russell final Russell 3000 addition/deletion PDFs:

### 2023
- event close: 2023-06-23
- additions: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-additions-final-20230623.pdf
- deletions: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-deletions-final-20230623.pdf

### 2024
- event close: 2024-06-28
- additions: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-additions-final-20240628.pdf
- deletions: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-deletions-final-20240628.pdf

### 2025
- event close: 2025-06-27
- additions: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-additions-20250627.pdf
- deletions: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ru3000-deletions-20250627.pdf

The repo stores source references and rules, not copies of FTSE Russell constituent lists.

## Temporal split
- **BUILD:** 2023 and 2024.
- **HOLDOUT:** 2025, untouched until the frozen test is run.

No year may be replaced.

## Event universe
Parse every unique ordinary ticker that can be recovered from the official final PDF tables.

Direction sign:
- addition = +1
- deletion = -1

If QuantConnect cannot resolve a ticker or does not provide sufficient minute history for the required windows, report the observation as unavailable and do not replace it.

Do not exclude observations based on their realised returns.

## Price-data construction
Use QuantConnect US equity minute history plus SPY as market control.

To avoid timezone/display assumptions, define intraday windows by bar position within each sorted regular-session history rather than displayed clock labels.

For each security:

### Event close window
On the reconstitution Friday:
- `P_pre` = close 30 one-minute bars before the final bar;
- `P_close` = final regular-session minute close;
- `V_close30` = volume over the final 30 one-minute bars;
- `V_day` = total regular-session minute volume.

### Next-session window
On the next available US trading session:
- `P_next30` = close of the 30th regular-session minute bar.

### Placebo
Use the same stock and the same construction on the immediately preceding Friday and its next available trading session.

The placebo date is fixed by calendar/event timing, not selected by returns.

## Market adjustment
Construct the same return windows for SPY.

For a stock return `r_stock` and corresponding SPY return `r_spy`, market-adjusted return is:

`r_abn = r_stock - r_spy`.

## Variables
### 1. Closing-volume concentration — mechanism variable
`close_share = V_close30 / V_day`.

`volume_excess = close_share_event - close_share_placebo`.

Expected sign: positive.

### 2. Signed closing pressure — directional variable
`pressure = sign × abnormal_return(P_pre -> P_close)`.

`pressure_placebo` uses the placebo Friday.

`pressure_excess = pressure_event - pressure_placebo`.

Expected sign: positive.

### 3. Signed post-event reversal — reversal variable
`reversal = -sign × abnormal_return(P_close -> P_next30)`.

`reversal_placebo` uses the placebo Friday and its next trading session.

`reversal_excess = reversal_event - reversal_placebo`.

Expected sign: positive.

## Pre-event liquidity descriptor
For each security, compute median daily dollar volume over the 20 completed trading sessions before the event Friday:

`ADV20 = median(close × volume)`.

This is descriptive in RUS1 and cannot rescue a failed primary gate. A later combination test may use capacity explicitly, but only under a separately frozen specification.

## Summary statistics
For each year and pooled BUILD report, for each of `volume_excess`, `pressure_excess`, and `reversal_excess`:
- N;
- mean;
- median;
- fraction > 0;
- addition median;
- deletion median.

Also report data coverage from source ticker -> QC-resolved -> complete required windows.

## Frozen gates
### A. Mechanism gate — closing concentration
PASS requires:
1. 2023 median `volume_excess > 0`;
2. 2024 median `volume_excess > 0`;
3. pooled BUILD median `volume_excess > 0`;
4. 2025 HOLDOUT median `volume_excess > 0`;
5. 2025 fraction `volume_excess > 0` is at least 0.60.

### B. Directional indicator gate — closing pressure
PASS requires:
1. 2023 median `pressure_excess > 0`;
2. 2024 median `pressure_excess > 0`;
3. pooled BUILD median `pressure_excess > 0`;
4. 2025 HOLDOUT median `pressure_excess > 0`;
5. 2025 fraction `pressure_excess > 0` is at least 0.55;
6. in 2025, both addition median and deletion median `pressure_excess > 0`.

### C. Reversal gate
PASS requires:
1. 2023 median `reversal_excess > 0`;
2. 2024 median `reversal_excess > 0`;
3. pooled BUILD median `reversal_excess > 0`;
4. 2025 HOLDOUT median `reversal_excess > 0`;
5. 2025 fraction `reversal_excess > 0` is at least 0.55;
6. in 2025, both addition median and deletion median `reversal_excess > 0`.

The three gates are adjudicated separately.

## No rescue/tuning
After outcomes are seen, do not:
- change the event years;
- substitute preliminary membership lists for final lists;
- alter the 30-minute windows;
- select stocks based on realised returns;
- change the placebo week;
- introduce market-cap/ADV thresholds to rescue the result;
- reinterpret a failed directional/reversal gate as a pass because volume concentration succeeds.

## Economic promotion
RUS1 is not yet an economic backtest. If the directional or reversal gate passes, the next step must be a separately frozen economic test including costs, realistic entry timing, position overlap/capital constraints, and feasibility for approximately £2,000 capital using fine-grained sizing.