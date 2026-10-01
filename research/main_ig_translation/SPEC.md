# MAIN→IG translation — frozen feasibility rules

## Status
Frozen before inspecting account-specific IG market metadata or running any IG-based P&L simulation.

## Objective
Translate the already-validated 22-market CME MAIN engine into a venue with fine enough sizing for approximately £2,000 capital, without changing the underlying trading rules to make the venue fit.

This is a venue/economic translation exercise, not new signal discovery.

## Source engine
MAIN uses 22 CME futures markets:
- Equity indices: ES, NQ, YM
- Treasuries: ZT, ZF, ZN, ZB
- FX: 6E, 6J, 6B, 6A, 6C
- Metals: GC, SI, HG
- Energy: CL, NG, HO, RB
- Grains: ZC, ZS, ZW

The signal logic remains unchanged:
- 12-month trend;
- forced continuation;
- trend dips;
- existing exclusions/filters and frozen weighting logic.

No thresholds, hold periods or signal definitions may be changed in this translation stage.

## IG venue preference
For multi-day/longer holds, prefer IG spread-bet/CFD **futures or forward contracts** when an economically equivalent market is available, because DFB/cash markets incur overnight funding while futures/forwards do not.

Use DFB/cash only when no suitable future/forward exists; record that explicitly and include overnight funding in any later economic simulation.

## Mapping rules
Map by underlying economic exposure, not by whichever IG search result appears first.

Orientation relative to CME must be recorded.
- Same orientation: ES, NQ, YM, ZT, ZF, ZN, ZB, 6E (EUR/USD), 6B (GBP/USD), 6A (AUD/USD), GC, SI, HG, CL, NG, HO, RB, ZC, ZS, ZW.
- Inverted if IG uses the conventional USD quote: 6J versus USD/JPY; 6C versus USD/CAD. Any signal/return sign must be inverted accordingly.

If more than one IG contract is plausible, retain all candidates until exact instrument metadata are inspected.

## Stage 1 — read-only account/instrument feasibility probe
Use the IG **demo** REST API only. No order endpoints may be called.

For each MAIN market record, where available:
- IG epic;
- instrument name and type;
- expiry / DFB status;
- market status;
- bid and offer snapshot;
- minimum deal size;
- deal-size unit;
- contract size / lot size;
- value of one pip / one-pip meaning;
- account currency / instrument currency;
- margin deposit bands or margin factor;
- minimum normal stop distance;
- whether controlled-risk stops are allowed;
- dealing hours if exposed by the API.

Also record the active demo account type (spread bet / CFD), currency and whether dealing is enabled.

The probe is descriptive only. It does not place or simulate trades.

## Stage 2 — capital feasibility
After exact IG metadata are captured, compute the minimum tradable exposure and minimum practical risk contribution for each mapped market using the unchanged MAIN sizing target.

A market may be excluded from the translated universe only for pre-defined venue constraints such as:
- unavailable equivalent underlying;
- minimum stake too coarse for the £2,000 account under the frozen risk budget;
- unavailable required long/short direction;
- economically incompatible product construction;
- execution/funding costs that make the minimum position structurally uneconomic.

Do not exclude a market because its historical translated return is poor.

## Stage 3 — economic translation
Run the unchanged MAIN signals on the feasible mapped universe with IG-specific economics:
- actual/published IG spreads for the mapped product;
- roll/expiry treatment for futures/forwards;
- overnight funding for any DFB/cash product used;
- currency-conversion costs where applicable;
- minimum-stake rounding;
- realistic next-executable-price treatment;
- a 2× cost stress.

Report:
- compounded return;
- annualised return and volatility;
- Sharpe;
- max/open-position drawdown;
- turnover/costs;
- 2× cost result;
- number of active markets and average concurrent positions;
- fraction of ideal positions rounded to zero or minimum size.

Compare with the original MAIN result over matched dates and with the S&P benchmark at matched risk.

## Promotion rule
Do not promote to IG demo paper trading unless the translated engine remains economically credible after minimum-stake rounding and 2× costs, and the result is not dependent on one market or one sector.

If translation fails because too many markets cannot be sized, record MAIN as strategy-valid but capital-incompatible at £2,000 and do not retune the strategy to force a fit.
