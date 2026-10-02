# O1 — SPXW dealer-gamma data feasibility result

Date evaluated: 2026-10-02

## Decision

**FAIL — DATA GATE FAILED. Do not run an outcome test from this branch.**

The frozen feasibility gate required both fixed dates to provide:
- a non-empty SPXW chain;
- same-day-expiry contracts;
- usable open interest and gamma fields;
- and at least 100 minute rows for the selected 0DTE contract.

Both dates passed the chain/Greeks/OI requirements but failed the minute-history requirement with exactly zero trade and quote rows.

Under the pre-registered rule, O1 does not advance.

## Fixed probe dates

- 2025-11-05
- 2026-09-24

No alternative dates were tried.

## 2025-11-05

- chain rows: 16,921
- 0DTE rows: 441
- open interest non-null: 441
- gamma non-null: 441
- delta non-null: 441
- IV non-null: 441
- volume non-null: 441
- selected contract: SPXW 251105P06575000
- strike: 6575
- right: PUT
- volume: 3,821
- open interest: 3,802
- gamma: 0.000239
- trade minute rows: **0**
- quote minute rows: **0**

Result: **FAIL**

## 2026-09-24

- chain rows: 20,171
- 0DTE rows: 496
- open interest non-null: 496
- gamma non-null: 496
- delta non-null: 496
- IV non-null: 496
- volume non-null: 496
- selected contract: SPXW 260924P07610000
- strike: 7610
- right: PUT
- volume: 7,417
- open interest: 1,415
- gamma: 0.00084
- trade minute rows: **0**
- quote minute rows: **0**

Result: **FAIL**

## Interpretation

The QuantConnect Free-tier Research environment exposes rich SPXW option-chain snapshots on both fixed dates, including 0DTE contracts with open interest, gamma, delta, IV and volume.

However, the selected 0DTE contracts return no minute TradeBar or QuoteBar history in the requested regular-session window.

This prevents the pre-registered O1 design from establishing a contract-level intraday exposure/hedging test using QC alone.

## Disposition

- O1 static-chain data access: **PASS**
- O1 minute contract history access: **FAIL**
- overall O1 feasibility: **FAIL**
- do not change probe dates
- do not relax the 100-row gate
- do not run a historical outcome test from this branch
- do not infer dealer net gamma sign from unsigned OI/gross volume as a workaround

The options/dealer-gamma mechanism may remain conceptually interesting, but this QC-based implementation path is closed.
