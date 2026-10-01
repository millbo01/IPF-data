# IG demo venue probe — 2026-10-01

## Purpose
Read-only feasibility probe for translating the validated traditional-futures MAIN engine to IG spread betting/CFDs for an approximately £2,000 account.

## Input
User-supplied `ig_main_probe.csv` generated from the IG demo REST API. No orders were placed.

## Observed probe coverage
- 31 rows total.
- 13 rows with status `OK`.
- 3 rows with status `DETAIL_FAILED`.
- 15 rows with status `NO_MATCH`.
- Only six CME roots produced at least one fully detailed candidate: ES, NQ, YM, ZB, 6E, 6J.
- GBP/USD candidates were discovered but market-detail retrieval failed.
- All later roots were returned as `NO_MATCH`, a pattern consistent with the probe swallowing API/search failures and/or throttling rather than proving those IG markets are unavailable.

## Important correction
The demo API minimum-deal-size values are not accepted as live-account sizing evidence. For example, the demo returned `0.04` for US 500 futures, while IG's current UK retail product specifications state standard live minimum bets of £1/point for US 500 futures and US Tech 100 futures and £0.20/point for Wall Street futures.

The initial probe also read the IG v4 market schema while attempting to extract margin fields available in older schemas, so `margin_pct_first_band` is not usable from this file.

## Interim verdict
- API connectivity: PASS.
- Demo EPIC discovery: PARTIAL.
- Live £2k sizing feasibility: NOT YET ADJUDICATED.
- Do not promote MAIN to IG on the basis of demo minima.

## Next gate
Run a read-only production-account probe using exact IG market names, conservative request pacing, explicit HTTP-error reporting, and a market-detail schema that returns live account minimum size and margin. No order endpoints are required.
