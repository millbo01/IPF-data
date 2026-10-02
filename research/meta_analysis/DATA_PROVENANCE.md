# Data provenance

## Stored directly in GitHub

### VIX ETP public provider data
Branch `research/vix-etp-flow-v2`, path `data/vix_etp_flow/backfill/`.
Contains official ProShares historical NAV/AUM data for UVXY/VIXY/SVXY, Volatility Shares document indexes and parsed UVIX/SVIX monthly AUM anchors, plus derived signal/materiality files.

### Equity leveraged-ETF provider data
Branch `research/equity-letf-rebalance`, path `data/equity_letf_rebalance/`.
Contains official ProShares history for UPRO, SPXU, SSO, SDS, TQQQ, SQQQ, QLD and QID; normalized AUM and derived convexity scales.

### MAIN -> IG configuration / translation inputs
Branch `research/main-ig-translation`.
Includes frozen 22-market configuration, expanded-universe exposures, quote-transform/census scripts, translation specs and result summaries.

### Index morning-fade execution outputs
Branch `research/index-morning-fade-ig`, path `research/index_large_move_reversal/results_v2/`.

Contains the reconstructed V2 event-level NDX trade ledger plus complete threshold/timestamp/cost/sizing summaries, yearly chronology, direction split and SPX comparator. These are derived from the frozen QuantConnect output and IG venue rules; they do not duplicate the vendor minute history.

### V3 prospective shadow data
Branch `research/index-morning-fade-ig`, path `research/index_large_move_reversal/forward_shadow/`.

This path is the canonical prospective record:
- QuantConnect Research authoritative QQQ signal checks;
- provisional source-bridge checks when QC Research is one session behind;
- pending P90 trigger records;
- read-only live IG US Tech 100 quote paths on triggered mornings;
- the cumulative `FORWARD_LEDGER.csv`;
- `NEXT_ACTION.md` for the current user/agent handoff step.

Formal V3 event inclusion remains QuantConnect-authoritative. External recent-minute data may only be used under the pre-registered source-bridge amendment to decide whether to arm a read-only capture, and provisional events must later be confirmed or rejected by QC.

## Supplied by QuantConnect, not duplicated as raw files
- futures history for MAIN
- tick/quote/trade data for LC1
- SPY/QQQ minute history for LETF and index-reversal studies

For those datasets, the retained reproducibility material is the exact algorithm logic, date windows, algorithm IDs and output logs/result summaries. For INDEX-IG-V2, the derived event ledger is now retained in GitHub even though the raw QQQ/NDX minute history is not.


### R1 mandated rebalancing
Branch `research/r1-mandated-rebalancing`.

The exact frozen Research script, specification and result summary are stored in GitHub. ES/ZN vendor history itself is supplied by QuantConnect and is not duplicated raw.
