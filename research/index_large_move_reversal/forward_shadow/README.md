# V3 NDX forward shadow

This directory is the canonical prospective ledger for the frozen V3 validation defined in `../SPEC_V3_FORWARD_SHADOW.md`.

## Current operating mode — QuantConnect Free plan

The project is currently running the forward phase with **manual QuantConnect signal checks plus automated read-only IG capture**.

QuantConnect Cloud API automation is not required for the V3 research design. The paid-API runner remains in the repository as dormant infrastructure only.

### User workflow after each US trading session

Run the QuantConnect **Research** checker after the regular US close:

`../qc_research_forward_check.py`

A chat-attached `.ipynb` version is supplied whenever the user needs to run it manually.

It places no orders and prints one authoritative line beginning:

`FORWARD_CHECK,`

Expected outcomes:

- `FORWARD_CHECK,NO_SIGNAL,...`
- `FORWARD_CHECK,P90_TRIGGER,...,P95=yes/no,...`

If there is **NO_SIGNAL**, nothing else is required.

If there is a **P90_TRIGGER**, pass that single output line to the research agent. The agent records the frozen signal in `pending_signal.json` on this branch. The scheduled read-only IG capture workflow then handles the next morning automatically.

Do not edit thresholds, timestamps, dates, or signal logic in the checker.

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

## Signal checker

Research-branch code:

- `../main_free_forward_check.py` — current Free-tier manual checker
- `../qc_forward_signal.py` — API-runner version of the same frozen signal logic
- `../qc_cloud_forward.py` — dormant QuantConnect Cloud API runner

The Research checker uses `QuantBook.history` over a rolling current window long enough to calculate the frozen 252-session prior-only z-score. It emits only the latest completed session's status. The backtest checker is retained only as legacy/dormant code because the Free backtester is currently capped three months out of sample.

## Paid QuantConnect API automation — dormant

Default-branch workflow:

`.github/workflows/ndx-forward-shadow-qc-signal.yml`

This workflow is **manual-dispatch only** on the current Free plan. Its old nightly schedule has been disabled so it cannot generate failed jobs or imply that an upgrade is required.

If paid QuantConnect API access is ever available later, the workflow can be re-enabled without changing the frozen trading rule.

## Morning IG capture

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

No dealing/order endpoint is called.

## Timing discipline

The IG workflow is scheduled at both 13:15 and 14:15 UTC so one trigger is 09:15 New York regardless of US daylight saving time. The script exits harmlessly on the wrong-DST trigger.

If the correct job starts more than 90 seconds after 09:31:05, the event is recorded as missed rather than backfilled or silently dropped.

## Formal adjudication

Do not make a final V3 pass/fail call until both are true:

- at least 30 P90 events;
- at least 12 calendar months from the first forward-eligible signal.

See `../SPEC_V3_FORWARD_SHADOW.md` for the complete frozen adjudication rules.
