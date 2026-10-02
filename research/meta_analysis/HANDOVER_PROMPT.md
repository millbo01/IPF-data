# New-chat handover prompt — IPF Trading Bot

You are taking over an ongoing quantitative trading research project from another ChatGPT session.

Repository: `millbo01/IPF-data`

Before doing any new work, read the canonical project summary on the repository default branch:
- `META_ANALYSIS_INDEX.md`

Then inspect the detailed research report on branch:
- `research/meta-analysis`
- `research/meta_analysis/DETAILED_RESEARCH_REPORT.md`
- `research/meta_analysis/EXPERIMENT_LEDGER.csv`
- `research/meta_analysis/DATA_PROVENANCE.md`

For primary evidence, inspect the exact branch result files referenced by that report rather than relying on conversational memory.

Current state:
- Original 22-market MAIN futures strategy still has a positive research edge; later direct-load holdout Sharpe 0.906.
- Broad £2,000 IG implementation is dead under tested spreads. Diagnostic showed transaction costs, not £0.01 rounding, are the dominant failure.
- LC1 robustly supports the mechanism that lower receiving-side capacity amplifies immediate price displacement, but LC1 trading rules did not survive economic stability tests.
- Modern VIX-ETP -> late-equity forced-flow strategy was killed after adding UVIX/SVIX.
- Equity leveraged-ETF pressure looked promising but ablation showed too little incremental information beyond plain intraday index moves.
- Current active candidate is a plain Nasdaq large-move reversal pattern.

Important repository update:
- PR #15, `Research/index morning fade ig`, has now been merged to `main`.
- It already contains the frozen next experiment and companion code:
  - `research/index_large_move_reversal/SPEC_V2_IG_EXECUTION.md`
  - `research/index_large_move_reversal/VENUE_FACTS_2026-10-02.md`
  - `research/index_large_move_reversal/ig_dfb_probe.py`
  - `research/index_large_move_reversal/qc_ig_execution_v2.py`
- Review those files first. Do not independently redesign the experiment before reading them.

Immediate task:
Execute/review the small-account IG version of the NDX/QQQ next-session morning fade using the already-frozen PR #15 specification.

Signal:
- prior day 15:45 New York return from previous regular-session close, standardized with a rolling z-score using prior observations only.
- fixed NDX thresholds:
  - P80 = 1.2681
  - P90 = 1.7796
  - P95 = 2.3646

Trade:
- day T+1, fade the sign of day T's move.
- primary entry = 09:31 New York.
- exit = 10:00 New York.
- no overnight exposure.
- 09:32 and 09:35 are sensitivity checks only.

Key prior results:
- NDX build 2012-18 morning reversal: P80 +2.118 bp, P90 +6.083, P95 +13.739.
- 2022-24: P80 -0.993, P90 +4.786, P95 +7.036.
- 2025-26: P80 +3.284, P90 +11.553, P95 +27.290.
- 2025-26 P95 has only 13 events, so do not overstate certainty.
- 2019-21 is a distinct extraordinary overnight-reversal regime and should not set current expected returns.

Execution requirements are already frozen in PR #15:
- IG US Tech 100 DFB as the preferred venue representation.
- Public-minimum and conditional 0.01-point stake cases.
- Base and 2x spread stress.
- Full trade ledger, MAE, margin, drawdown, yearly chronology and SPX comparator.
- Do not add MAIN, LC1, VIX-ETP, LETF pressure or other filters in this experiment.

Working preference:
Lead the workflow and minimize manual tasks. Use GitHub as the canonical source of truth. Preserve negative findings rather than optimizing around them.
