# V3 forward shadow amendment — QuantConnect Free-tier transport

Date: 2026-10-02

## Reason

The frozen V3 protocol originally included an optional GitHub -> QuantConnect Cloud API runner for unattended nightly signal calculation.

The active QuantConnect account is on the Free tier. Paid API access is not required to test the V3 hypothesis, so the project will not upgrade solely for automation.

## Change

Only the **transport/execution of the signal calculation** changes.

Current active process:

1. after the regular US close, manually run `main_free_forward_check.py` in the QuantConnect Free backtester;
2. use its single `FORWARD_CHECK` output line as the authoritative frozen signal record;
3. if it reports `NO_SIGNAL`, no further action occurs;
4. if it reports `P90_TRIGGER`, write the signal fields into `forward_shadow/pending_signal.json`;
5. the existing scheduled GitHub Action captures read-only live IG US Tech 100 DFB quotes at 09:31-10:00 New York and appends the prospective shadow ledger.

The paid QuantConnect API workflow remains in the repository but its schedule is disabled.

## No research-rule change

This amendment does **not** change:

- QQQ signal definition;
- prior-only 252-session z-score;
- P90 = 1.7796;
- P95 = 2.3646;
- 09:31 entry;
- 10:00 exit;
- fade direction;
- 1x-notional sizing;
- IG instrument;
- margin model;
- minimum forward sample;
- pass/fail criteria;
- prohibition on same-sample optimization.

The manual checker is therefore an operational substitute for the API runner, not a new experiment.
