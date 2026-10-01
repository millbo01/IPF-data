# MAIN-IG Expanded v1 — freeze amendment 1

**Date:** 2026-10-01  
**Timing:** frozen before any Expanded v1 historical P&L has been viewed.

This amendment reduces implementation discretion in `EXPANDED_V1_SPEC.md`. It does not change any T1 / Forced / Dip trading rule, threshold, hold, multiplier, stake rule, spread treatment, margin treatment or economic gate.

## A1. Forestry is in scope

Section 3's macro source-market families also includes **forestry**. Lumber was already present in `EXPANDED_V1_EXPOSURES.csv`; the omission of the word forestry from the prose list was clerical.

The source-market families are therefore:

- currencies;
- financials / interest rates;
- broad equity indices;
- energy;
- grains;
- meats;
- metals;
- soft commodities;
- forestry.

All original exclusions in section 3 remain unchanged.

## A2. Duplicate-underlying root resolution is deterministic

This amendment supersedes the duplicate-underlying ranking in section 3 of `EXPANDED_V1_SPEC.md`.

For each `exposure_id` in `EXPANDED_V1_EXPOSURES.csv`, `qc_candidates` is an **ordered structural fallback list**. Select the first candidate root in that order that satisfies the minimum source-data rule through the freeze date:

1. valid point-in-time lead-contract prices;
2. valid aggregate chain volume;
3. valid aggregate chain open interest;
4. at least 252 valid daily price observations by 2026-09-29.

If the first root fails, test the next listed root. If every listed root fails, exclude the exposure as `SOURCE_DATA_FAIL`.

The ordering was fixed before Expanded v1 P&L and generally places the existing benchmark or standard-size benchmark root before mini/micro substitutes. No return, Sharpe, drawdown, strategy event result, spread profitability or translated P&L may be used to choose among roots.

This replaces the earlier longest-history / median-OI / median-volume tie-break because that ranking would require a second source-universe research pass without changing the economic exposure. The ordered fallback produces the same required property for this experiment: exactly one source root per economic underlying, chosen without reference to strategy performance.

## A3. Original 22 remain benchmark anchors in Expanded v1

The 22 already authenticated and frozen mappings are retained in the Expanded v1 universe whenever their existing source root satisfies the source-data rule. A transient IG search/API failure during the expanded census must not erase an already frozen benchmark mapping.

For those 22, use `FROZEN_22_CONFIG.csv` for quote transform, spread and margin. The expanded live census is a cross-check only.

New markets must pass all Expanded v1 IG eligibility rules and transform validation. No analogous grandfathering applies to them.
