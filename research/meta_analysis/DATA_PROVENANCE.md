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

## Supplied by QuantConnect, not duplicated as raw files
- futures history for MAIN
- tick/quote/trade data for LC1
- SPY/QQQ minute history for LETF and index-reversal studies

For those datasets, the retained reproducibility material is the exact algorithm logic, date windows, algorithm IDs and output logs/result summaries.

## Local handover bundle
A companion downloadable ZIP produced at handover time contains all QC scripts and logs still present in the working session, including Practical-v2, MAIN decomposition, VIX screens, LETF screen/ablation and index-reversal anatomy.
