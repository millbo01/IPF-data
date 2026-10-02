# IPF Trading Bot — Canonical Meta-Analysis Index

This file is the default-branch entry point for the trading research archive.

## Canonical handover branch

Read branch:

`research/meta-analysis`

Files:
- `research/meta_analysis/DETAILED_RESEARCH_REPORT.md` — full research narrative and findings
- `research/meta_analysis/EXPERIMENT_LEDGER.csv` — one-row-per-experiment ledger
- `research/meta_analysis/DATA_PROVENANCE.md` — what raw/derived data are actually stored
- `research/meta_analysis/HANDOVER_PROMPT.md` — copy/paste prompt for a new ChatGPT/agent session

## Primary evidence branches

### MAIN -> IG
Branch `research/main-ig-translation`

Key files:
- `research/main_ig_translation/MAIN_IG_DIAGNOSTIC_2026-10-01.md`
- `research/main_ig_translation/EXPANDED_V1_RESULT_2026-10-01.md`
- `research/main_ig_translation/RISK_PROBE_RESULTS_2026-10-01.md`

### LC1 capacity
Branch `research/lc1-liquidity-capacity`

Key files:
- `research/lc1_liquidity_capacity/RESULTS_LC1A.md`
- `research/lc1_liquidity_capacity/RESULTS_LC1B.md`

### VIX ETP
Branch `research/vix-etp-flow-v2`

Key files:
- `research/vix_etp_flow/RESULTS_V2_FINAL.md`
- `data/vix_etp_flow/backfill/`

### Equity LETF
Branch `research/equity-letf-rebalance`

Key files:
- `research/equity_letf_rebalance/RESULTS_V1_SCREEN.md`
- `research/equity_letf_rebalance/RESULTS_V2_ABLATION.md`
- `data/equity_letf_rebalance/`

### Current active candidate
Branch `research/index-large-move-reversal`

Key files:
- `research/index_large_move_reversal/SPEC.md`
- `research/index_large_move_reversal/RESULTS_V1_ANATOMY.md`

## Current state in one paragraph

Original MAIN still has a positive unrounded research edge, but broad £2,000 IG implementation fails under observed spreads. LC1 validates receiving-capacity effects on immediate price impact but did not produce a stable standalone trade. Modern VIX ETP and equity LETF forced-flow trading stories were tested and demoted. The current active candidate is simpler: after an unusually large Nasdaq move, fade the prior move during the next session's opening half hour, with 09:31-10:00 New York the leading window. The next test is realistic IG/Nasdaq execution using the frozen P80/P90/P95 thresholds from the anatomy study.

## Rule for future agents

Do not infer the project state from branch names alone. Read the detailed meta-analysis report first, then inspect the primary result files on the relevant branch before changing or reviving a hypothesis.
