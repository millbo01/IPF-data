# LC1 — Liquidity Capacity

## Status

Pre-registered mechanism test. No outcome data have been examined for LC1 at the time this specification was written.

## IPF mechanism

The market analogue of a capacity-saturation claim is:

> The same incoming pressure should produce a larger and more persistent state change when the system has less capacity to absorb that pressure.

For a limit-order market, the incoming pressure is aggressive signed trade flow and the immediately observable absorption capacity is displayed contra-side liquidity plus replenishment of that liquidity.

The first test is deliberately narrower than a trading strategy. It asks whether capacity modifies the price impact of aggressive flow. It does not begin by optimizing entries, exits, indicators, leverage, or PnL.

## Primary hypothesis (LC1-A)

For observations with comparable absolute aggressive signed flow, subsequent price movement in the direction of that flow is larger when observable contra-side liquidity capacity is lower.

Equivalently, conditional on pressure, a higher pressure-to-capacity ratio should predict greater same-direction forward return.

Expected interaction sign:

- signed pressure × inverse capacity: positive with same-direction forward return.

## Secondary hypothesis (LC1-B; only tested if LC1-A survives)

After a high pressure-to-capacity episode, same-direction continuation should weaken or reverse when aggressive pressure subsides and contra-side capacity replenishes.

LC1-B will be separately specified before its outcomes are opened.

## Initial markets

The same frozen construction will be tested independently on:

- ES — S&P 500 E-mini futures
- ZN — 10-Year U.S. Treasury Note futures
- CL — WTI Crude Oil futures

These are chosen before seeing LC1 outcomes to span three different futures market structures.

## Intended LC1-A time structure

Subject to the data-access diagnostic confirming the required tick fields:

- aggregation window: 30 seconds
- forward horizons: 30 seconds, 60 seconds, 5 minutes, 15 minutes
- regular comparison is within instrument and time-of-day, not pooled raw quantities across instruments

## Intended observables

### Pressure

Aggressive signed trade quantity during each 30-second window.

Trade direction will be inferred using the prevailing best bid/ask observed immediately before each trade. Primary classification:

- trade price >= prevailing ask: buyer-initiated
- trade price <= prevailing bid: seller-initiated
- inside-spread or otherwise unresolved trades: deterministic tick-rule fallback; zero-change unresolved trades inherit the last non-zero trade sign when available

Pressure is buy-initiated quantity minus sell-initiated quantity.

### Capacity

Primary capacity is contra-side displayed top-of-book size relative to the direction of signed pressure, summarized from quote ticks during the same 30-second window.

For net buying pressure, contra capacity is ask-side size. For net selling pressure, contra capacity is bid-side size.

A separate replenishment measure will quantify quote-size restoration after depletion. The exact statistic will be frozen after the access diagnostic confirms quote-tick structure; the diagnostic is not allowed to inspect forward returns.

### Pressure-to-capacity ratio

A normalized pressure/capacity measure will be constructed within instrument and time-of-day after the diagnostic confirms scale and sparsity. The normalization rule will be frozen before outcome analysis.

## Controls

The LC1-A analysis must separate the capacity interaction from the known predictive content of order flow itself.

At minimum, the primary regression/matching design will include:

1. signed aggressive pressure;
2. capacity;
3. pressure × inverse-capacity interaction;
4. recent realized volatility;
5. spread;
6. time-of-day controls.

A matched comparison will also compare high- and low-capacity windows within narrow pressure bins.

The key question is not whether aggressive flow predicts returns. It is whether capacity materially changes the impact of otherwise comparable flow.

## Pass/fail logic

LC1-A is not considered supported merely because a coefficient is statistically significant in one contract.

A useful result should show all of the following:

1. the interaction has the predicted sign in the primary specification;
2. the matched high-pressure/low-capacity group has greater same-direction forward movement than comparable high-pressure/high-capacity observations;
3. the effect is visible in more than one of ES, ZN, and CL rather than depending entirely on a single instrument;
4. it is not confined to one short period or a handful of extreme observations;
5. it survives a chronological holdout defined before the full analysis is run;
6. estimated effect size is large enough to plausibly exceed realistic futures transaction costs before any strategy optimization.

If the capacity interaction adds no meaningful predictive information beyond pressure itself, LC1 is killed and richer market-by-order data will not be purchased for this mechanism.

## Data-access diagnostic

Before freezing the exact capacity/replenishment statistic, run `qc_tick_diagnostic.py` on a short ES interval only. The diagnostic may inspect:

- whether tick history is accessible;
- columns/index layout;
- number of trade and quote rows;
- bid/ask price and size availability;
- timestamps and contract mapping;
- sample trade/quote records.

It must not calculate forward returns, signal performance, or any pressure/capacity outcome relationship.

## Research hygiene

- Do not tune LC1 using the R1 or crypto results.
- Do not optimize window lengths after looking at LC1 outcomes.
- Do not introduce RSI, MACD, moving averages, OI, or other filters into LC1-A unless separately pre-specified as a later experiment.
- Raw QuantConnect/AlgoSeek licensed tick data must not be committed to this public repository.
- Only code, specifications, and permissible derived summaries belong here.
