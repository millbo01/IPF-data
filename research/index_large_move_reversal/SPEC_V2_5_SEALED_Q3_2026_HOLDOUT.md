# V2.5 sealed Q3 2026 holdout — pre-registered before unsealing

Date frozen: 2026-10-02

## Why this test exists

The QuantConnect Free-tier forward checker was run on 2026-10-02 with an algorithm end date of 2026-10-02, but the backtest stopped at 2026-07-02.

The exact three-month truncation is consistent with QuantConnect's organization-level **Backtesting Out of Sample Period** setting. Therefore the period after 2026-07-02 has not yet been exposed through the project's QC backtests.

This creates a useful accidental sealed holdout. It must be tested before the organization holdout is removed for ongoing V3 monitoring.

## Holdout window

Primary sealed holdout:
- signal dates: **2026-07-03 through 2026-09-29**
- trade dates may extend through **2026-09-30**
- no October 2026 observation is included.

This is a fixed calendar window chosen before any outcome in that window is examined.

## Frozen rule

Signal:
- QQQ regular-session return from previous close to 15:45 New York;
- rolling z-score over the prior 252 observations only;
- minimum 60 prior observations.

Primary threshold:
- **P90 = 1.7796**

Secondary subset:
- **P95 = 2.3646**

Trade:
- fade the sign of the signal-day move;
- enter NDX at 09:31 New York on the next regular session;
- exit at 10:00 New York;
- no overnight exposure.

Execution model:
- IG US Tech 100 DFB;
- base full round-trip spread = the frozen V2 public schedule (1 point during the core US cash session; otherwise 2);
- stress = 2x spread;
- £2,000 starting account;
- 1x account-notional stake, rounded half-up to £0.01/point;
- 5% margin model.

## Required outputs

For P90 primary and P95 secondary:
- trade count;
- gross mean and median bp;
- net mean and median bp;
- gross/net hit rate;
- break-even round-trip cost in bp and NDX points;
- base and 2x-spread net mean;
- £2,000 ending equity;
- max closed-trade drawdown;
- max margin utilisation;
- event-by-event ledger.

## Interpretation

This short holdout is **supplementary** to V3 prospective validation.

It is not large enough to replace the frozen V3 requirement of at least 30 P90 events and 12 calendar months.

No threshold, timestamp, direction, volatility, weekday, or other filter may be changed after seeing this holdout.

A negative result is retained as evidence; it is not a reason to select 09:35 or P95 as the new primary rule.
