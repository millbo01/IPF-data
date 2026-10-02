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
Research result branch: `research/index-morning-fade-ig`

Key files:
- `research/index_large_move_reversal/SPEC.md`
- `research/index_large_move_reversal/RESULTS_V1_ANATOMY.md`
- `research/index_large_move_reversal/SPEC_V2_IG_EXECUTION.md`
- `research/index_large_move_reversal/SPEC_V2_IG_EXECUTION_AMENDMENT_1.md`
- `research/index_large_move_reversal/SPEC_V2_IG_EXECUTION_AMENDMENT_2.md`
- `research/index_large_move_reversal/VENUE_FACTS_2026-10-02.md`
- `research/index_large_move_reversal/IG_DFB_PROBE_LATEST.md`
- `research/index_large_move_reversal/main.py`
- `research/index_large_move_reversal/RESULTS_V2_IG_EXECUTION.md`
- `research/index_large_move_reversal/results_v2/NDX_IG_FADE_V2_TRADE_LEDGER.csv`
- `research/index_large_move_reversal/results_v2/NDX_IG_FADE_V2_SUMMARY.csv`
- `research/index_large_move_reversal/results_v2/NDX_IG_FADE_V2_YEARLY.csv`
- `research/index_large_move_reversal/results_v2/SPX_IG_FADE_V2_SUMMARY.csv`
- `research/index_large_move_reversal/SPEC_V3_FORWARD_SHADOW.md`
- `research/index_large_move_reversal/forward_shadow/README.md`
- `.github/workflows/ndx-forward-shadow-qc-signal.yml`
- `.github/workflows/ndx-forward-shadow-ig-capture.yml`

V2 executable-economics result:
- live IG GBP spread-bet account confirms US Tech 100 DFB at 0.01 POINTS minimum and 5% first-band margin;
- P80 is not robust enough after execution costs;
- P90 is the strongest surviving 09:31 candidate;
- P95 has a larger post-2021 effect but is sparse and regime-sensitive;
- 09:35 looks stronger recently but failed stability against build and must not be selected from this sample;
- the next clean step is forward paper/live-shadow validation of frozen P90/09:31, retaining P95 only as a pre-specified high-conviction subset.

## Current state in one paragraph

Original MAIN still has a positive unrounded research edge, but broad £2,000 IG implementation fails under observed spreads. LC1 validates receiving-capacity effects on immediate price impact but did not produce a stable standalone trade. Modern VIX ETP and equity LETF forced-flow trading stories were tested and demoted. The surviving active candidate is the plain Nasdaq large-move next-session morning fade. Its live IG venue gate passed, and V2 shows that the broad P80 version is too weak, while frozen P90/09:31 survives representative costs and 2x spread stress in the post-2021 regime. P95 is stronger but sparse and unstable across regimes. 2026-to-date is negative, so the result is not a deployment green light. The next stage is the frozen V3 forward shadow/paper validation. GitHub automation is in place to run the QuantConnect signal job after the US close and capture read-only live IG quotes at 09:31-10:00 on triggered sessions; activation requires the QuantConnect API credentials to be stored as repository secrets.

## Rule for future agents

Do not infer the project state from branch names alone. Read the detailed meta-analysis report first, then inspect the primary result files on the relevant branch before changing or reviving a hypothesis.
