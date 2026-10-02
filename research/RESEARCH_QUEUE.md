# IPF Trading Bot — Research Queue

Updated: 2026-10-02

## Active monitoring

### V3 Nasdaq morning fade
Status: **PROSPECTIVE VALIDATION**

Frozen primary:
- QQQ prior close -> 15:45 NY return
- prior-only 252-session z-score
- P90 = 1.7796
- fade next session 09:31 -> 10:00 NY
- P95 secondary subset only

Do not optimize threshold, timestamp, direction, volatility or weekday inside the forward sample.

Formal adjudication requires at least 30 P90 events and at least 12 calendar months.

## Closed / deprioritized

### R1 mandated rebalancing
Status: **DEPRIORITIZED**

The post-paper holdout retained the predicted negative Threshold sign, but the Combined strategy did not show a meaningful advantage over the frozen 5-day reversal control.

Do not run R1.1 execution realism or the IPF liquidity-capacity extension from this branch.

### Previously closed/demoted
- broad MAIN -> £2k IG translation
- LC1 standalone trading rules
- VIX ETP late-equity strategy
- LETF pressure as incremental signal beyond plain intraday move
- crypto-perpetual forced-liquidation strategy as a deployable system

Negative findings are retained; do not rescue them through same-sample parameter changes.

## Next new research direction

### O1 — Options dealer gamma / forced hedging
Status: **FEASIBILITY + LITERATURE PHASE, NOT YET FROZEN**

Why it is worth examining:
- externally documented forced hedging mechanism;
- naturally intraday;
- direct interaction between forced hedge demand and underlying liquidity/capacity;
- index-level implementation could be represented economically through a small IG spread-bet account;
- QuantConnect documents SPX/SPXW index-option history including daily chains, open interest, Greeks and 0DTE universes.

Before any outcome test:
1. establish whether the Free-tier QC Research environment can retrieve the required SPXW option-chain history over a usable sample;
2. define an ex-ante dealer-gamma proxy that does not assume unknown customer/dealer trade signs;
3. define a same-drift control;
4. define build/holdout split and economic pass/fail gate;
5. check £2,000 IG execution feasibility before running the historical outcome test.

Do not begin historical optimization until the feasibility and specification are frozen.

## Current project rule

There is no other high-priority, already-frozen untouched hypothesis waiting to be run.

The next stage is therefore deliberate hypothesis formation and cheap feasibility testing, while V3 continues prospectively.
