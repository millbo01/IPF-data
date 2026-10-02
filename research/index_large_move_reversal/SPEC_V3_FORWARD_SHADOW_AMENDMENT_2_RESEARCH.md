# V3 forward shadow amendment 2 — use QuantConnect Research for current signals

Date: 2026-10-02

## Reason

The QuantConnect Free cloud backtester remained capped at 2026-07-02 even after attempting to expose the later period. QuantConnect Research, using `QuantBook.history`, successfully accessed QQQ and NDX minute data through 2026-09-30.

Therefore the authoritative Free-tier current-signal transport is changed from a backtest to a Research notebook/script.

## Active process

1. After the US regular close, manually run the frozen Research checker.
2. Use the single `FORWARD_CHECK` line as the authoritative signal record.
3. If `NO_SIGNAL`, no further action occurs.
4. If `P90_TRIGGER`, arm `forward_shadow/pending_signal.json` in GitHub before the next US session.
5. The scheduled read-only IG workflow captures the 09:31-10:00 quote path and appends the forward ledger.

## No research-rule change

Unchanged:
- QQQ previous close -> 15:45 New York return;
- prior-only 252-session rolling z-score;
- P90 = 1.7796;
- P95 = 2.3646 secondary;
- fade direction;
- 09:31 entry;
- 10:00 exit;
- 1x-notional sizing;
- IG instrument;
- minimum forward sample and adjudication rules.

This is an operational/data-access amendment only.
