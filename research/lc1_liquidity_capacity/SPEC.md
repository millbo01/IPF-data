# LC1 — Liquidity Capacity

## Status

Pre-registered mechanism test. The ES data-access diagnostic has been run, but **no LC1 outcome relationship has been examined** at the time this post-diagnostic specification was frozen.

The diagnostic confirmed tick trades and side-specific quote updates with usable bid/ask prices and sizes. It also showed that each quote row normally updates only one side of the book. LC1-A therefore reconstructs the prevailing BBO by carrying the most recent bid and ask updates forward separately.

## IPF mechanism

The market analogue of a capacity-saturation claim is:

> The same incoming pressure should produce a larger and more persistent state change when the system has less capacity to absorb that pressure.

For a limit-order market, incoming pressure is aggressive signed trade flow. Observable absorption capacity is the displayed contra-side best-quote size immediately before the pressure arrives.

The first test is deliberately narrower than a trading strategy. It asks whether capacity modifies the price impact of aggressive flow. It does not optimize entries, exits, leverage, indicators, or PnL.

## Primary hypothesis (LC1-A)

For observations with comparable absolute aggressive signed flow, price movement in the direction of that flow is larger when pre-existing observable contra-side capacity is lower.

Equivalently, conditional on pressure, the interaction between pressure magnitude and inverse capacity should positively predict same-direction price movement.

## Trading-relevance extension inside LC1-A

A mechanism can be real but already completed before a trader can act. Therefore LC1-A separately measures:

1. **Immediate impact** during the 30-second pressure window; and
2. **Forward continuation** after that window closes.

A positive immediate interaction with no positive forward continuation is not sufficient for promotion to a bot.

## LC1-B

Only if LC1-A survives will LC1-B test whether replenishment/restoration of capacity identifies the end or reversal of the move. LC1-B will be separately frozen before its outcomes are opened.

## Markets

The same frozen construction is tested independently on:

- ES — S&P 500 E-mini futures
- ZN — 10-Year U.S. Treasury Note futures
- CL — WTI Crude Oil futures

The cross-market requirement is intentional: a result dependent on one contract is not enough to support an IPF-level mechanism.

## Sampling plan

Tick volume is very large (the diagnostic returned about 1.36 million ES rows in one hour), so raw ticks are processed one instrument-day at a time and discarded after aggregation.

### Daily measurement interval

For every sampled date:

- raw tick request: 09:59:00 through 11:00:00 in the QuantConnect history timestamp convention used by the successful diagnostic;
- signal windows: 10:00:00 through 10:44:30;
- aggregation: non-overlapping 30-second windows;
- this yields up to 90 observations per instrument-day;
- the remaining history through 11:00 supplies the frozen 15-minute forward horizon.

No other hours are examined in LC1-A. If LC1-A survives, another hour can later be used as a separately frozen replication.

### Build dates — 2025

These 24 dates were selected before outcome analysis using a fixed RNG seed (1701) from US federal-business dates in 2025:

- 2025-01-06
- 2025-01-21
- 2025-01-24
- 2025-02-04
- 2025-02-26
- 2025-04-01
- 2025-04-14
- 2025-04-24
- 2025-05-06
- 2025-05-08
- 2025-05-13
- 2025-05-14
- 2025-05-21
- 2025-06-02
- 2025-07-01
- 2025-07-17
- 2025-08-04
- 2025-08-15
- 2025-09-29
- 2025-09-30
- 2025-10-27
- 2025-11-19
- 2025-12-10
- 2025-12-12

### Holdout dates — 2026

These 12 dates were selected by the same frozen procedure from 2026-01-02 through 2026-08-31:

- 2026-01-02
- 2026-01-23
- 2026-03-06
- 2026-03-10
- 2026-03-11
- 2026-03-30
- 2026-05-14
- 2026-05-21
- 2026-06-10
- 2026-06-24
- 2026-07-30
- 2026-08-31

The 2026-09-29 diagnostic date is not part of either analysis sample.

If a sampled date lacks sufficient usable tick data, it is skipped and **not replaced** after outcomes are seen.

## BBO reconstruction

The diagnostic established that quote rows are side-specific. LC1-A therefore:

1. sorts all rows by timestamp while preserving original row order for ties;
2. treats a positive bid price as a bid-side update and a positive ask price as an ask-side update;
3. carries the most recent bid price/size and ask price/size forward separately;
4. retains only states with positive bid and ask, ask >= bid, and positive side sizes;
5. samples the reconstructed BBO onto a 1-second grid using the last known state.

Mid-price is `(bid + ask) / 2`.

## Pressure classification

For every strict trade row (`quantity > 0` and `lastprice > 0`), the most recent reconstructed BBO at or before the trade is attached.

Primary aggressor classification:

- trade price >= prevailing ask: +1 buyer initiated;
- trade price <= prevailing bid: -1 seller initiated;
- otherwise use the tick rule based on change from the previous trade price;
- zero trade-price changes inherit the last non-zero tick-rule sign when available;
- trades still unresolved receive sign 0 and their quantity is excluded from signed pressure.

For each 30-second window:

`pressure = sum(classification_sign * quantity)`

`pressure_abs = abs(pressure)`

Windows with zero net pressure are excluded from the primary LC1 relationship.

A sampled instrument-day is usable only if at least 80% of strict-trade quantity is classified and at least 60 of its 90 signal windows have valid pressure, capacity, and prices. Failed days are reported and skipped without replacement.

## Pre-existing capacity

Capacity is deliberately measured **before** the pressure window to reduce simultaneity/endogeneity.

At each 30-second window start, using the immediately preceding 30 seconds of the reconstructed 1-second BBO:

- `pre_bid_size` = median displayed bid size;
- `pre_ask_size` = median displayed ask size;
- `pre_spread` = median ask minus bid;
- `pre_rv` = standard deviation of 1-second log-mid returns over the preceding 60 seconds.

If pressure is positive, contra capacity is `pre_ask_size`.
If pressure is negative, contra capacity is `pre_bid_size`.

The frozen inverse-capacity variable is:

`inv_capacity = -log1p(contra_capacity)`

so larger values represent lower capacity.

Pressure magnitude is:

`log_pressure = log1p(abs(pressure))`.

## Outcomes

All returns use reconstructed mid-prices to avoid bid/ask bounce.

For a pressure window beginning at `t` and ending at `t+30s`:

### Mechanism outcome

`impact_30s = sign(pressure) * log(mid[t+30s] / mid[t])`

Positive values mean price moved in the direction of aggressive pressure while the pressure was occurring.

### Forward trading-relevance outcomes

Measured from the end of the pressure window:

- `fwd_30s = sign(pressure) * log(mid[t+60s] / mid[t+30s])`
- `fwd_60s = sign(pressure) * log(mid[t+90s] / mid[t+30s])`
- `fwd_5m = sign(pressure) * log(mid[t+330s] / mid[t+30s])`
- `fwd_15m = sign(pressure) * log(mid[t+930s] / mid[t+30s])`

Positive values mean continuation in the original pressure direction after the signal window has closed.

## Primary regression

Each instrument is estimated separately, separately in build and holdout.

Predictors are standardized within that instrument/sample using predictor data only.

For each outcome:

`directional_return ~ log_pressure + inv_capacity + log_pressure*inv_capacity + pre_spread + pre_rv + five-minute time-bucket dummies`

The coefficient of interest is the interaction:

`beta_interaction > 0` expected.

HC1 heteroskedasticity-robust standard errors are reported.

The immediate-impact regression is the primary mechanism test. The four forward regressions determine whether the relationship remains potentially tradable after the 30-second signal window.

## Matched comparison

As a non-parametric check, observations are divided within each instrument/sample into quintiles of `log_pressure` using predictor data only.

Within each pressure quintile:

- low capacity = bottom 30% of contra capacity;
- high capacity = top 30% of contra capacity.

For each outcome, report mean directional return for low capacity minus high capacity within each pressure quintile and the equal-weight average across available quintiles.

Expected difference: positive.

This directly asks whether otherwise comparably sized flow has more impact when capacity is low.

## Pass/fail logic

LC1-A is not considered supported merely because one coefficient is significant in one market.

### Mechanism gate

The mechanism gate requires, in the **2026 holdout**:

1. positive immediate-impact interaction coefficient in at least 2 of ES, ZN, CL; and
2. positive matched low-capacity-minus-high-capacity immediate-impact difference in at least 2 of the 3 markets; and
3. no single instrument or extreme observation obviously accounts for the entire pooled descriptive result.

If fewer than 2 markets satisfy both directional conditions, LC1-A is killed and richer market-by-order data are not purchased for this mechanism.

### Trading-relevance gate

If the mechanism gate passes, promotion requires evidence that can be acted on after the signal window closes:

1. in at least 2 markets, at least one of the frozen forward horizons has both a positive interaction coefficient and positive matched low-minus-high capacity difference in holdout; and
2. the effect is not isolated to one sampled day; and
3. the estimated effect is large enough to justify a subsequent realistic-cost backtest.

If immediate impact passes but all forward effects fail, LC1 is recorded as a real-time impact mechanism but **not promoted as a trading edge**.

No strategy optimization occurs inside LC1-A.

## Research hygiene

- Do not tune LC1 using the R1 or crypto results.
- Do not change the 30-second window or the four forward horizons after outcome data are opened.
- Do not add RSI, MACD, moving averages, OI, funding, or other filters to LC1-A.
- Do not replace failed sampled dates after outcomes are seen.
- Raw QuantConnect/AlgoSeek licensed tick data must not be committed to this public repository.
- Only code, specifications, and permissible aggregated summaries belong here.
