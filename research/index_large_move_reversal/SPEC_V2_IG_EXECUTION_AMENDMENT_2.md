# V2 IG execution amendment 2 — output transport only

Date: 2026-10-02

The first V2 QuantConnect run completed the underlying analysis but exhausted the account's 10 KB backtest log allowance while emitting the event ledger, before aggregate summaries could be retrieved.

Evidence from that run:
- 7,224 source rows;
- 7,222 completed next-session observations;
- NDX usable rows: 3,551;
- SPX/NDX cash-index minute data loaded successfully through 2026-07-02.

No signal, threshold, timestamp, cost, stake, period or interpretation rule is changed.

## Output-only amendment

The canonical `main.py` now exports the event-level result through a custom QuantConnect chart named `IGFADE_EXPORT` rather than logging every trade.

It uses exactly 10 custom series, within the Free-tier chart quota:

NDX P80+ events:
- NDX_Z
- NDX_SIGRET_BP
- NDX_ENTRY0931
- NDX_GROSS0931_BP
- NDX_MAE0931_BP
- NDX_GROSS0932_BP
- NDX_GROSS0935_BP

SPX P80+ comparator events:
- SPX_Z
- SPX_ENTRY0931
- SPX_GROSS0931_BP

The x-axis is trade date. Threshold membership is reconstructed from the frozen absolute-z cutoffs. NDX direction is reconstructed from raw signal return. Exit price, gross points, spread-adjusted net return, stake, margin and equity path are reconstructable exactly from the frozen rules.

The backtest's **Download Results** JSON is therefore the canonical output artifact for V2. This amendment changes only transport of results and was made after observing the logging-limit failure, not after observing aggregate V2 performance.
