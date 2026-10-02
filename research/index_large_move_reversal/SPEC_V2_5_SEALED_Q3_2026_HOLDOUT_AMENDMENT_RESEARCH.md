# V2.5 sealed Q3 holdout amendment — QC Research transport

Date: 2026-10-02

## Trigger for this amendment

The sealed Q3 backtest was attempted after the holdout was pre-registered, but QuantConnect still terminated the backtest at 2026-07-02. The run therefore produced zero Q3 events because the withheld period was not accessible to the backtest engine.

This is a platform-access issue, not a strategy outcome.

## Transport change

The same frozen sealed-Q3 test will now be run in the QuantConnect Research Environment with `QuantBook.History`.

Canonical notebook:

`research/index_large_move_reversal/qc_research_sealed_q3.ipynb`

The notebook first performs a hard access gate:
- QQQ minute history must extend through 2026-09-30 16:00 New York;
- NDX minute history must extend through 2026-09-30 10:00 New York.

If either condition fails, it stops with `STOP_NO_CURRENT_DATA` and produces no strategy adjudication.

If the access gate passes, it runs the already-frozen sealed Q3 rule exactly as specified in `SPEC_V2_5_SEALED_Q3_2026_HOLDOUT.md`.

## No research-rule change

This amendment changes only the QuantConnect interface used to retrieve the data.

It does not change:
- holdout dates;
- QQQ signal definition;
- prior-only 252-session z-score;
- P90 or P95 thresholds;
- 09:31 entry;
- 10:00 exit;
- NDX execution series;
- spread assumptions;
- sizing;
- margin;
- required outputs;
- interpretation discipline.

If QC Research also cannot access the period on the Free tier, the Q3 sealed test remains unrun and must not be coded as a failure.
