# New-chat handover prompt — IPF Trading Bot

You are taking over an ongoing quantitative trading research project.

Repository: `millbo01/IPF-data`

## Read first

Default branch:
- `META_ANALYSIS_INDEX.md`
- `research/RESEARCH_QUEUE.md`

Canonical handover branch:
- branch `research/meta-analysis`
- `research/meta_analysis/DETAILED_RESEARCH_REPORT.md`
- `research/meta_analysis/EXPERIMENT_LEDGER.csv`
- `research/meta_analysis/DATA_PROVENANCE.md`

For primary evidence, inspect exact branch result files rather than relying on conversational memory.

## Current research state

- Original MAIN futures research edge survives in idealized futures form, but broad £2,000 IG implementation failed because observed spreads dominate.
- LC1 strongly supports the mechanism that lower receiving-side capacity amplifies immediate displacement, but its trading rules failed stability/economics.
- Modern VIX-ETP and LETF forced-flow trading stories were tested and demoted.
- R1 mandated 60/40 rebalancing reproduced the expected sign weakly in the post-paper holdout but failed its frozen control gate: Combined holdout Sharpe 0.158 vs generic 5-day reversal 0.341. R1 is **DEPRIORITIZED**; do not run R1.1 or tune it.
- The only active candidate is the plain Nasdaq large-move next-session morning fade.

## Active V3 candidate

Branch: `research/index-morning-fade-ig`

Frozen primary:
- QQQ previous regular close -> 15:45 NY return
- prior-only 252-session z-score
- P90 = 1.7796
- fade next regular session
- 09:31 NY entry
- 10:00 NY exit
- P95 = 2.3646 secondary subset only
- no threshold/timestamp/direction/volatility/weekday optimization

Execution:
- IG US Tech 100 DFB
- 1x account-notional representation
- confirmed live minimum £0.01/point
- 5% margin model

V2 result:
- P80 weak/dead
- P90 strongest surviving frozen rule
- full holdout P90 +4.26 bp net mean; +3.34 bp at 2x spread
- current 2022-26 P90 +7.09 bp net mean
- P95 stronger post-2021 but sparse/regime-sensitive
- 09:35 historical sensitivity must **not** be promoted

Sealed Q3 2026:
- 8 P90 events
- +3.46 bp base net mean; +3.12 bp at 2x spread
- result turns negative after removing the single best event
- supplementary positive but fragile, not a V3 pass

Formal V3 adjudication requires both:
- >=30 P90 events
- >=12 calendar months

## Current Free-tier operating workflow

QuantConnect Research is authoritative.

Because QC Research can lag one session, the pre-registered source bridge may use a free recent QQQ minute feed only to decide whether to arm the next morning's **read-only IG capture**. QuantConnect later confirms formal inclusion. Never silently substitute the bridge source for the canonical QC signal.

Current durable action:
- read `research/index_large_move_reversal/forward_shadow/NEXT_ACTION.md`

Current known state as of 2026-10-02:
- 2026-09-30 formal QC: NO_SIGNAL, z +0.493675
- 2026-10-01 provisional bridge: NO_SIGNAL, z +0.266705
- bridge overlap validation max discrepancy: 0.238 bp across six sessions

## Next new hypothesis

`research/RESEARCH_QUEUE.md` defines O1 — **options dealer gamma / forced hedging** — as the next new direction.

O1 has a **frozen data-feasibility gate, but no frozen outcome test**.

Branch: `research/options-dealer-gamma`
- `research/options_dealer_gamma/SPEC_O1_FEASIBILITY.md`
- `research/options_dealer_gamma/qc_research_o1_spxw_feasibility.py`

Before any outcome analysis:
1. run the exact two-date Free QC Research feasibility diagnostic without changing the probe dates;
2. define an ex-ante gamma-pressure proxy without pretending gross 0DTE volume or unsigned OI directly equals dealer exposure;
3. define a simple same-drift control;
4. freeze build/holdout split and pass/fail rule;
5. check £2,000 IG execution feasibility.

If the data-access/identification gate fails, kill O1 cheaply.

## Working rules

- Lead the workflow and minimize user manual work.
- Anything the user personally must run in QC or Colab must also be supplied in chat as a complete downloadable file; do not require manual copying from GitHub.
- GitHub is the canonical archive/source of truth.
- Preserve negative findings.
- No same-sample rescue optimization.
- Do not revive closed mechanism stories without genuinely new evidence.
