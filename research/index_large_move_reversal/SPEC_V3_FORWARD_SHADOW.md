# V3 forward shadow validation — frozen after V2 IG execution result

Date frozen: 2026-10-02

## Purpose

Test whether the surviving NDX/QQQ morning-fade rule continues to work prospectively, with no retrospective optimization.

V2 established that transaction costs and IG stake granularity do not kill the candidate. The unresolved question is stability.

## Primary rule

Market:
- Nasdaq / NDX candidate only.

Signal:
- QQQ regular-session return from previous close to 15:45 New York.
- 252-session rolling z-score.
- Mean and standard deviation use prior observations only.
- Minimum 60 prior observations.

Primary threshold:
- **P90 = 1.7796**

Direction:
- fade the sign of the prior-day move.

Trade window:
- entry **09:31 New York**
- exit **10:00 New York**
- no overnight exposure.

Execution representation:
- IG US Tech 100 DFB
- live account EPIC previously confirmed as `IX.D.NASDAQ.CASH.IP`
- actual bid/offer at the event should be recorded when available
- no assumption that historical representative spreads will equal future live spreads.

Sizing:
- shadow account starts at **£2,000**
- 1x account notional:
  `stake_raw = running_equity / index_level`
- round positive stake magnitude to nearest **£0.01/point**, half-up
- floor £0.01/point
- retail margin model 5%.

## Secondary subset

P95 = **2.3646**.

P95 is reported separately as a high-conviction subset. It is not allowed to replace P90 based on the forward sample unless a new experiment is explicitly pre-registered.

P80 is demoted and is not part of the primary forward strategy.

## Forbidden changes during the forward phase

Do not add or change:
- 09:32 / 09:35 entry selection
- volatility filters
- direction filters
- weekday filters
- overnight exposure
- threshold re-estimation
- P90 threshold
- 10:00 exit
- risk scaling based on realized forward performance
- VIX-ETP / LETF causal filters
- discretionary event exclusions.

Any change is a new experiment and begins a new forward sample.

## Required event record

For every P90 trigger, record:
- signal date
- trade date
- QQQ 15:45 return
- rolling z-score
- signal sign
- P95 membership
- intended 1x stake
- IG US Tech 100 bid/offer at 09:31
- IG US Tech 100 bid/offer at 10:00
- actual observed spread at entry and exit
- gross index-point result
- gross bp
- net result after observed spread
- net bp
- £ P&L
- equity before / after
- margin used
- maximum adverse excursion if minute data are available
- missed/untradeable flag and reason.

A missed signal remains in the ledger; it must not be silently dropped.

## Minimum forward sample before formal adjudication

Do not make a final pass/fail call until both conditions are satisfied:
- at least **30 P90 events**, and
- at least **12 calendar months** from the first forward-eligible signal.

Interim monitoring is allowed but does not change the rule.

## Forward adjudication

Primary P90 passes the forward stage only if, at the minimum sample:
1. mean net return per event is > 0;
2. cumulative £ P&L on the frozen 1x-notional £2,000 shadow account is > 0;
3. removing the single best event leaves cumulative £ P&L > 0;
4. max closed-trade drawdown is < 10%;
5. applying an additional spread penalty equal to the observed average round-trip spread still leaves mean net return > 0.

Fail if any of conditions 1-4 fails. Condition 5 is an economic stress check; failure there demotes rather than automatically kills unless the observed spread itself has materially widened from V2 assumptions.

## Interpretation discipline

The forward sample is for validation, not search.

P95 performance, 09:35 historical sensitivity, direction asymmetries and volatility states may be described, but none may alter the P90 primary rule inside this sample.
