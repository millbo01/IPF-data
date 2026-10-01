# IG live-account venue probe — 2026-10-01

## Purpose
Read-only production-account feasibility probe for translating the validated traditional-futures MAIN engine to IG spread betting for an approximately £2,000 account.

## Results from user-supplied `ig_main_live_probe.csv`
- 22 frozen MAIN roots attempted.
- 14 roots returned complete live market detail before the API allowance was exceeded: ES, NQ, YM, ZT, ZF, ZN, ZB, 6E, 6J, 6B, 6A, 6C, GC, SI.
- 8 later roots returned `SEARCH_403`: HG, CL, NG, HO, RB, ZC, ZS, ZW. The sequential pattern is treated as API allowance exhaustion, not evidence of market absence.
- All 14 successfully detailed markets were tradeable at probe time.
- All 14 returned account-specific `dealingRules.minDealSize.value = 0.01` with unit `POINTS`.
- First-band retail margin factors were 3.33%, 5%, or 10%.
- All allowed stops/limits and controlled-risk trades.

## Important discrepancy
IG's public UK product specification pages show higher standard minimum bets for several of these products (for example US 500 futures £1/point, US Tech 100 futures £1/point and Wall Street futures £0.20/point). The live REST API nevertheless returned `minDealSize=0.01` for the user's active spread-bet account. Until order-ticket validation or further account metadata confirms durability, treat 0.01 as the current account-specific API dealing rule, not as a guaranteed permanent platform minimum.

## Next gate
1. Retry only the eight throttled roots with slower pacing after the allowance resets.
2. Retrieve approximately 60 daily prices for every mapped live IG instrument.
3. Compute 60-day annualized underlying volatility and translate `minDealSize` into annualized P&L volatility at the smallest current stake.
4. Compare that minimum-risk quantum with MAIN's frozen per-market target for a £2,000 account (10% annualized volatility = approximately £200 annualized P&L volatility per active market before combination/scaling).
5. Do not change MAIN signals or holding periods.

No order endpoints were used.