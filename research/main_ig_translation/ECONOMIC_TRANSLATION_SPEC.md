# MAIN → IG economic translation test

## Status
Frozen after the live IG venue/risk probes and before running any translated historical P&L simulation.

## Question
Does the already-validated MAIN futures engine remain economically viable when its unchanged target exposures are implemented as IG UK spread bets on an approximately £2,000 account, using the authenticated live minimum stake of 0.01 and observed IG futures/forward spreads?

This is an execution/venue translation test, not a new strategy test. No signal, threshold, hold period, market membership, or MAIN multiplier may be retuned.

## Frozen source engine
Use the existing point-in-time MAIN engine and implementation:
- T1 12-month trend;
- F forced continuation;
- Dip trend dips;
- `M_MAIN = {"T1": 1.4335, "F": 4.54643, "Dip": 3.64361}`;
- full 22-market universe;
- F exclusions unchanged;
- original build 2010-2018 and holdout 2019-2026;
- original timing/lags and event holds unchanged.

## Account and target
- Starting account equity: £2,000.
- Frozen MAIN portfolio volatility target: 10% annualised.
- Equity compounds through time; target notional uses current translated account equity.

## IG stake construction
For each market/day, first compute the exact combined MAIN notional fraction implied by the frozen engine and the daily live-market denominators. Convert that combined market fraction to an IG £/point stake. Do not round T1/F/Dip separately; they net into one market target first, matching the production MAIN logic.

Authenticated live `minDealSize`: 0.01 on all 22 mapped markets.

Rounding rule:
1. compute the signed combined desired stake;
2. if `abs(desired_stake) < 0.01`, target stake = 0;
3. otherwise round to the nearest 0.01 stake increment, half away from zero;
4. never force a sub-minimum desired stake up to 0.01.

This rule is frozen before translated outcomes are viewed.

## IG quote transforms
Use the same underlying futures returns/signals as MAIN, translated into IG quote points using fixed quote conventions:
- ES, NQ, YM: linear ×1
- ZT, ZF, ZN, ZB: linear ×100
- 6E, 6B, 6A: linear ×10,000
- 6J: inverse quote, `IG = 100 / CME_price`; IG position sign reversed
- 6C: inverse quote, `IG = 10,000 / CME_price`; IG position sign reversed
- GC: linear ×1
- SI: linear ×100
- HG: linear ×10,000
- CL: linear ×100
- NG: linear ×1,000
- HO, RB: linear ×10,000
- ZC, ZS, ZW: linear ×1

On a lead-contract roll, compute the day return from the existing engine's same-contract return. Do not book the price-level gap between two different contracts as P&L.

## Costs
Use fixed observed authenticated-live IG futures/forward spreads from 2026-10-01:
- ES 1.0
- NQ 3.0
- YM 6.0
- ZT 2.0
- ZF 2.0
- ZN 4.0
- ZB 4.0
- 6E 10.6
- 6J 10.0
- 6B 9.9
- 6A 8.6
- 6C 7.3
- GC 0.8
- SI 10.0
- HG 40.0
- CL 6.0
- NG 10.0
- HO 30.0
- RB 30.0
- ZC 1.0
- ZS 2.0
- ZW 1.0

Execution cost at a normal target change is half the quoted spread times the absolute change in stake. A sign flip naturally pays both sides through the absolute stake change. On a futures/forward roll, charge half-spread to close the old stake plus half-spread to open the new stake even if the target size is unchanged.

Run both:
- **1× cost**: observed spreads above;
- **2× cost stress**: double every execution/roll spread cost.

No overnight DFB financing is included because the translation uses dated futures/forward spread bets.

## Margin
Use the authenticated first-band retail margin rates observed on 2026-10-01:
- indices 5%;
- US Treasuries 3.33%;
- 6E/6J/6B/6C 3.33%; 6A 5%;
- GC 5%;
- SI/HG and all energy/grains 10%.

Approximate daily margin = `abs(stake × IG_quote_level) × margin_rate` summed over markets.

Report maximum margin utilisation as a percentage of translated account equity. Do not retrospectively resize positions to fit margin. If the frozen translated targets exceed 100% margin utilisation, record the day and classify the translation as infeasible under the gate.

## Comparators
Report on the same dates:
1. unrounded original MAIN research model at 10% target;
2. IG-rounded MAIN at 1× observed spreads;
3. IG-rounded MAIN at 2× spreads;
4. ES/S&P benchmark, scaled ex post to the same realised volatility as the 1× translated IG book for descriptive return/DD comparison only.

## Required outputs
For build, holdout, and full period report:
- number of trading days;
- annualised return/CAGR above cash;
- annualised volatility;
- Sharpe ratio;
- max drawdown;
- ending £2,000 equity;
- correlation to unrounded MAIN;
- total spread costs and 2× spread costs;
- turnover/stake changes;
- percentage of desired non-zero market targets rounded to zero;
- percentage rounded by more than 25% in magnitude;
- maximum and 95th-percentile margin utilisation;
- market-level P&L contributions.

## Frozen economic gate
Classify **PASS TO DEMO PAPER TRADING** only if all of the following hold on the 2019-2026 holdout:
1. 1× IG-cost Sharpe >= 0.50;
2. 2× IG-cost Sharpe >= 0.40;
3. 1× annualised return above cash > 0;
4. 2× annualised return above cash > 0;
5. max drawdown at 1× costs is no worse than -20%;
6. correlation of monthly returns with unrounded MAIN >= 0.70;
7. maximum estimated margin utilisation < 100%;
8. no single market contributes more than 40% of absolute positive holdout P&L;
9. 1× translated MAIN has a higher return per unit of realised volatility than the same-period ES benchmark.

If any item fails, the venue translation does not graduate to demo paper trading under this frozen test. A failure may still identify a smaller implementable subset, but testing that subset is a new pre-registered test rather than a rescue.

## No rescue/tuning
After translated outcomes are viewed, do not:
- alter 0.01 rounding/minimum rules;
- remove coarse markets;
- change current observed spreads;
- switch selected markets from futures/forwards to DFB to improve costs;
- change MAIN multipliers, thresholds, holds, volatility windows, or exclusions;
- change the pass thresholds above.
