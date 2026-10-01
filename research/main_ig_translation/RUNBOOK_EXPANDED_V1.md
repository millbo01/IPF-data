# MAIN-IG Expanded v1 — execution runbook

This runbook executes the frozen experiment. Candidate discovery is closed. Do not add/remove markets using strategy results.

## Files

Frozen definitions:
- `EXPANDED_V1_SPEC.md`
- `EXPANDED_V1_FREEZE_AMENDMENT_1.md`
- `EXPANDED_V1_EXPOSURES.csv`
- `FROZEN_22_CONFIG.csv`

Automation:
- `ig_expanded_census.py`
- `qc_source_census.py`
- `make_expanded_inputs_v2.py`
- `main_ig_ledger.py`
- `build_expanded_config.py`
- `ig_translation_sim_v2.py`
- `make_final_benchmark.py`

## Step 1 — authenticated IG census (read-only)

Run locally from this directory with the same live spread-bet credentials used for the original 22 probe. Credentials remain in environment variables and are not written to output.

```bash
export IG_IDENTIFIER='...'
export IG_PASSWORD='...'
export IG_API_KEY='...'
# optional only when account auto-selection is not sufficient:
# export IG_ACCOUNT_ID='...'
python ig_expanded_census.py --with-history
```

Outputs:
- `ig_expanded_census.csv`
- `ig_expanded_exclusions.csv`
- `ig_expanded_all_detail_candidates.csv`
- `ig_expanded_history.csv`

No order/dealing endpoint is used.

## Step 2 — QuantConnect source-data census (no signals, no orders)

In a QuantConnect research/backtest project, use `qc_source_census.py` as the algorithm. Run once through 2026-09-29.

Download/decompress Object Store output:

`main_ig_source_census.csv.gz` → `main_ig_source_census.csv`

This file contains only source-data coverage. It contains no strategy returns.

## Step 3 — freeze the exact expanded source universe mechanically

```bash
python make_expanded_inputs_v2.py \
  --source-census main_ig_source_census.csv
```

The script combines source availability with the already frozen IG census and writes:
- `expanded_tickers.txt`
- `expanded_admitted.csv`
- `expanded_excluded.csv`

Do not edit these outputs after seeing P&L.

## Step 4 — export the original-22 and expanded target ledgers from QuantConnect

Put `main_ig_ledger.py` and the existing frozen `ipf_engine.py` in a QuantConnect project.

### 4a. Original 22 benchmark
Run `main_ig_ledger.py` with no `tickers` parameter. Download/decompress:
- `main_ig_original22_ledger.csv.gz`
- `main_ig_original22_benchmark.csv.gz`

### 4b. Expanded v1
Set the QuantConnect backtest parameter `tickers` to the single comma-separated line in `expanded_tickers.txt`. Run the same unchanged exporter. Download/decompress:
- `main_ig_expanded_ledger.csv.gz`
- `main_ig_expanded_benchmark.csv.gz`

The exporter places no orders. The ledger contains exact net MAIN target fractions after the frozen T1/F/Dip denominator logic.

## Step 5 — build the expanded IG economics config

```bash
python build_expanded_config.py \
  --ledger main_ig_expanded_ledger.csv
```

Outputs:
- `EXPANDED_V1_CONFIG.csv`
- `expanded_transform_exclusions.csv`

Original 22 economics come unchanged from `FROZEN_22_CONFIG.csv`. New markets use the census spread/margin and the frozen mechanical quote-transform test. A transform failure is excluded before P&L and is not a rescue decision.

## Step 6 — run the original-22 IG translation

```bash
python ig_translation_sim_v2.py \
  --ledger main_ig_original22_ledger.csv \
  --config FROZEN_22_CONFIG.csv \
  --out results_ig22
```

This generates the original 22-market translated 1x/2x return paths under the same £2,000 / 0.01-rounding implementation.

## Step 7 — construct the frozen comparison file automatically

```bash
python make_final_benchmark.py \
  --main-benchmark main_ig_original22_benchmark.csv \
  --ig22-daily results_ig22/daily_1x.csv \
  --out expanded_gate_benchmark.csv
```

## Step 8 — run Expanded v1 and adjudicate the gate

```bash
python ig_translation_sim_v2.py \
  --ledger main_ig_expanded_ledger.csv \
  --config EXPANDED_V1_CONFIG.csv \
  --benchmark expanded_gate_benchmark.csv \
  --out results_expanded_v1
```

Read `results_expanded_v1/summary.json`.

The final fields are:
- `gate_complete`
- `gate` (each frozen condition separately)
- `pass_to_demo_paper_trading`

Also retain:
- `daily_1x.csv`, `daily_2x.csv`
- `market_contrib_1x.csv`, `market_contrib_2x.csv`

These contain the margin, spread-cost, rounding and contribution diagnostics required by the frozen specification.

## Stop rule

If `pass_to_demo_paper_trading` is false, do not rescue Expanded v1 by deleting weak/expensive markets, changing stake rounding, changing margins, changing spreads, changing signals/holds/multipliers, or introducing a margin allocator. Record the failed gate(s). Any revised subset or sizing method is a separately pre-registered experiment.
