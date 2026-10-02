# V2 IG execution amendment 1 — frozen before trade-level results

Date: 2026-10-02

The read-only live-account DFB probe passed the granularity gate:

- US Tech 100 DFB EPIC: `IX.D.NASDAQ.CASH.IP`
- expiry: `DFB`
- status at probe: `TRADEABLE`
- account-specific minimum: **0.01 POINTS**
- first-band retail margin: **5%**
- GBP spread-bet account confirmed

Because the actual DFB minimum is now known before any V2 trade-level outcomes have been viewed, the £2,000 economics test is amended as follows.

## Primary sizing

Use **ONE_X_NOTIONAL** as the primary account-sizing rule:

`stake_raw = running_equity / entry_index_level`

Round the positive stake magnitude to the nearest **£0.01/point**, half-up, with a floor of the confirmed live minimum **£0.01/point**.

This targets approximately 1x index notional exposure. With 5% retail margin it therefore uses approximately 5% of account equity as margin before stake-step rounding. A 1% index move corresponds approximately to a 1% account move before spread cost.

This is a sizing convention, not a tuned parameter. It is fixed before V2 trade outcomes are viewed.

## Diagnostic sizing

Also report **LIVE_MIN_0p01**, fixed at £0.01/point, to show the economics at the smallest executable stake.

The earlier PUBLIC_MIN £1/point scenario is no longer the relevant executable minimum for this account and is dropped from the primary output.

## Everything else remains frozen

- NDX P80 1.2681 / P90 1.7796 / P95 2.3646.
- 09:31 entry remains primary.
- 09:32 and 09:35 remain sensitivity checks only.
- 10:00 exit.
- no overnight exposure.
- BASE representative DFB spread schedule and 2x spread stress unchanged.
- SPX remains a robustness comparator.
- no MAIN, LC1, VIX-ETP, LETF, volatility, day-of-week, direction or other filters.
- no threshold or timestamp winner may be selected from this sample.

Canonical QC file after this amendment:
`research/index_large_move_reversal/main.py`
