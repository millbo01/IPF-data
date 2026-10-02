# V3 NDX forward shadow

This directory is the canonical prospective ledger for the frozen V3 validation defined in `../SPEC_V3_FORWARD_SHADOW.md`.

## Frozen rule

- QQQ previous regular close -> 15:45 New York return
- 252-session rolling z-score using prior observations only
- primary threshold P90 = 1.7796
- secondary subset P95 = 2.3646
- fade on next XNYS session
- 09:31 New York entry
- 10:00 New York exit
- IG US Tech 100 DFB `IX.D.NASDAQ.CASH.IP`
- £2,000 starting shadow equity
- 1x account notional, rounded to the confirmed £0.01/point live minimum
- 5% margin model
- no live orders

## Automation

### Nightly signal

Default-branch workflow:
`.github/workflows/ndx-forward-shadow-qc-signal.yml`

Research-branch code:
- `../qc_forward_signal.py` — frozen QuantConnect signal algorithm
- `../qc_cloud_forward.py` — QuantConnect Cloud API runner

The workflow runs after the US close, creates/reuses a QuantConnect project named `IPF NDX Forward Shadow`, syncs the frozen signal code, compiles it, runs it, and records:

- `latest_signal.json`
- `signal_history.csv`
- `pending_signal.json` only when a current-session P90 trigger fires

QuantConnect API credentials are stored only as GitHub secrets and are never written to the repository.

Required GitHub secrets:
- `QC_USER_ID`
- `QC_API_TOKEN`

Optional:
- `QC_ORGANIZATION_ID`

### Morning IG capture

Default-branch workflow:
`.github/workflows/ndx-forward-shadow-ig-capture.yml`

Research-branch code:
- `../shadow_ig_capture.py`

On an armed P90 event, the read-only IG process:
1. waits for 09:31 New York;
2. records live bid/offer;
3. samples the market about once per minute for prospective MAE;
4. records live bid/offer at 10:00;
5. computes mid-price gross return and executable bid/offer net return;
6. applies the frozen 1x-notional shadow stake;
7. appends `FORWARD_LEDGER.csv`;
8. writes the raw quote path to `raw/YYYY-MM-DD.json`;
9. removes the consumed pending signal.

Existing IG repository secrets are reused.

No dealing/order endpoint is called by either workflow.

## Timing discipline

The IG workflow is scheduled at both 13:15 and 14:15 UTC so one trigger is 09:15 New York regardless of US daylight saving time. The script exits harmlessly on the wrong-DST trigger.

If the correct job starts more than 90 seconds after 09:31:05, the event is recorded as missed rather than backfilled or silently dropped.

## Formal adjudication

Do not make a final V3 pass/fail call until both are true:
- at least 30 P90 events;
- at least 12 calendar months from the first forward-eligible signal.

See `../SPEC_V3_FORWARD_SHADOW.md` for the complete frozen adjudication rules.
