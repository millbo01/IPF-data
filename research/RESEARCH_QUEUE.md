# IPF Trading Bot — active research queue

Updated: 2026-10-02

## 1. V3 NDX forward shadow — ACTIVE MONITORING

Primary rule remains frozen P90 / 09:31-10:00 New York.

Current operating mode:
- QuantConnect Research provides the authoritative rolling state;
- the provisional source bridge is allowed only for the immediately missing current session;
- formal V3 inclusion waits for later QC confirmation;
- minimum adjudication sample remains 30 P90 events and 12 months.

Do not optimize this historical sample further.

## 2. R1 mandated rebalancing — NEXT INDEPENDENT HYPOTHESIS

Status: frozen before first project result; no project result yet.

Question:
Does predictable 60/40 equity/bond rebalancing forecast next-day ES-minus-ZN returns in the post-paper 2023-2026 holdout, and does the frozen rebalancing construction add materially more information than a generic 5-day cross-asset reversal control?

Run:
- QuantConnect Research
- research/r1_mandated_rebalancing/qc_research.py
- return full first output before changing any parameter.

Decision:
- deprioritize if Threshold relationship loses predicted negative sign in holdout, or Combined offers no meaningful advantage over the frozen 5-day reversal control;
- only if R1 survives may R1.1 add realistic futures execution and then test the IPF-specific pressure/capacity interaction.

## 3. After R1

There is currently no other fully frozen, untouched high-priority hypothesis in the canonical repo.

Surviving but not yet promoted ideas:
- MAIN directional/state signal as a research prior;
- LC1 receiving-capacity mechanism as a possible future independent interaction test;
- compelled-flow / receiving-capacity hypotheses only where they beat simpler controls.

Do not revive broad MAIN-on-£2k-IG, LC1 standalone trading, VIX-ETP late-equity, or LETF-pressure causal variants without genuinely new evidence.

## User action tonight

See research/index_large_move_reversal/forward_shadow/NEXT_ACTION.md.