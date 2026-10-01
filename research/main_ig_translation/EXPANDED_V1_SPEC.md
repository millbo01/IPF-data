# MAIN-IG Expanded v1 — frozen specification

**Freeze date:** 2026-10-01  
**Status:** frozen before any expanded-market historical P&L is viewed.

## 1. Question

Can the already-validated MAIN mechanism be translated to a ~£2,000 UK IG spread-bet account more effectively by applying the **unchanged T1 / Forced / Dip rules** to every mechanically eligible additional macro futures market that IG can implement at 0.01 stake granularity?

The original 22-market MAIN is the validated benchmark, not a sacred universe. Expanded v1 is a **universe / execution translation test**, not a strategy-discovery exercise.

## 2. Rules that may not change

Use the existing point-in-time engine without retuning:

- T1: sign of 12-month return; 60-day volatility scaling; weekly resize as already implemented.
- Forced: true-range percentile >=80, volume percentile >=80, matched-contract open-interest change percentile <=20, and 5-day volatility >20-day volatility; 10-trading-day hold in the forced move direction.
- Dip: break of the prior 20-day range against T1, enter with T1, 10-trading-day hold; existing Strain and Overwhelmed filters retained.
- Percentile windows, warm-ups, lags, roll/expiry exclusions, bad-move handling and all other engine mechanics remain unchanged.
- `M_MAIN = {"T1": 1.4335, "F": 4.54643, "Dip": 3.64361}` remains unchanged.
- Starting equity £2,000.
- No post-result rescaling to force Expanded v1 back to 10% realised volatility.

`Overwhelmed` keeps its validated **one-third of currently valid markets within the 3-day window** definition. In Expanded v1 its breadth denominator is therefore the mechanically expanded live universe; the threshold itself is unchanged. The original 22-market benchmark is also run separately with its original universe so any effect of this mechanical breadth change is visible.

## 3. Source-market census — mechanical, no return selection

Start from the futures roots available in QuantConnect's US Futures / Security Master data through these macro groups:

- currencies;
- financials / interest rates;
- broad equity indices;
- energy;
- grains;
- meats;
- metals;
- soft commodities.

Do **not** admit:

- crypto futures;
- volatility futures;
- single-name / sector / thematic equity derivatives;
- options;
- BTIC, TAS, calendar-spread, basis, premium, differential, freight, weather, emissions or dividend-only contracts;
- synthetic commodity-index contracts;
- a second contract-size variant of an economic underlying already represented.

### Duplicate-underlying rule

Where several roots represent the same economic underlying (standard / E-mini / mini / micro or equivalent), retain exactly one source root. Choose mechanically by:

1. longest usable history through the freeze date;
2. if tied, highest trailing-252-day median aggregate open interest;
3. if still tied, highest trailing-252-day median aggregate volume;
4. if still tied, the larger contract size.

No return or strategy result may be used in this choice.

### Minimum source-data rule

A source root may enter the IG mapping census only if the point-in-time chain can produce:

- a valid lead-contract price series;
- aggregate chain volume;
- aggregate chain open interest;
- at least 252 valid daily price observations by 2026-09-29.

T1 and Dip remain eligible whenever their required inputs are valid. Forced is eligible on a new root only when its volume/OI features become `ready` under the existing engine. No market is removed from Forced because its historical Forced returns are poor.

The five existing benchmark Forced exclusions remain excluded for the 22-market benchmark. For new roots there is no discretionary exclusion list: missing/invalid inputs simply prevent `ready` from becoming true under the engine's existing logic.

## 4. IG eligibility — authenticated live account

For each surviving source exposure, query the user's authenticated **live UK SPREADBET** account through the IG REST API.

A source exposure enters Expanded v1 only when all of the following are true at the census:

1. a directly corresponding IG market is found by underlying identity, not by historical return similarity;
2. it is a dated futures / forward spread-bet instrument (`expiry` is not `DFB`);
3. the market is not `OFFLINE` or permanently unavailable; normal `CLOSED` status outside its trading session is allowed;
4. both a valid bid and offer can be retrieved;
5. authenticated `dealingRules.minDealSize.value <= 0.01`;
6. first-band margin is available from the market detail response;
7. the exposure can be held long and short as a normal directional spread bet.

If no unambiguous IG match exists, the source root is excluded as **UNMAPPED**, not manually rescued after results are known.

IG search, market detail and historical price endpoints are read-only; no order endpoint is used during census.

## 5. IG mapping and contract choice

Mapping is by economic underlying and asset family. Text matching may use normalized names / aliases, but an IG market must represent the same underlying exposure.

If several dated IG expiries exist for one underlying, choose the nearest listed expiry whose last-dealing date is at least 20 calendar days after the census date. If none meets that buffer, choose the next available dated expiry and flag it. This choice is made without reference to returns or spread size.

If multiple source roots map to the same IG economic exposure, apply the duplicate-underlying rule in section 3 and keep one.

## 6. Quote orientation and point transform

The historical signal and same-contract return continue to come from the futures engine. IG P&L is expressed in IG quote points.

For each mapped market determine one fixed transform of the form:

- linear: `IG_points = a * futures_price`, or
- inverse: `IG_points = a / futures_price`,

where `a` is a power of 10.

Infer orientation/scale from overlapping pre-test source and IG levels, choosing the candidate transform with the lowest median absolute relative level error. Require at least 20 overlapping daily observations where the same economic contract convention is comparable and require median relative error <=5%; otherwise classify the mapping **TRANSFORM_UNRESOLVED** and exclude it before P&L.

For an inverse transform the IG position sign is reversed. Once inferred, the transform is frozen for the historical run.

The original 22 mappings remain as already frozen in `ECONOMIC_TRANSLATION_SPEC.md`; the inference procedure is a cross-check for them, not permission to alter their mapping after outcomes.

## 7. Stake construction — fractional IG exposure

For each market/day:

1. compute each frozen book's exact target under the Expanded v1 live-market denominator;
2. sum/net T1 + F + Dip into one signed desired market notional fraction **before** stake conversion;
3. convert the combined desired notional to £/IG-point stake using current translated equity and the frozen quote transform;
4. if `abs(desired_stake) < 0.01`, target stake = 0;
5. otherwise round to the nearest 0.01, half away from zero;
6. never force a sub-minimum desired stake up to 0.01.

No integer-contract rounding is used. Partial/fractional exposure is the point of the IG translation.

## 8. Spreads and execution costs

For every newly admitted IG market freeze the authenticated-live quoted spread observed in the census (`offer - bid`) in IG points. Do not remove a market because that spread later proves economically damaging.

Historical simulation uses:

- **1x cost:** half the frozen quoted spread times the absolute change in stake at each target change;
- **2x cost stress:** double the spread cost;
- sign flips naturally pay both sides through absolute stake change;
- on a source/IG roll, pay half-spread to close and half-spread to reopen even if target stake is unchanged;
- no DFB overnight financing, because DFB instruments are excluded.

The original 22 retain the spreads already frozen on 2026-10-01 in `ECONOMIC_TRANSLATION_SPEC.md` so the validated benchmark is unchanged.

## 9. Margin

For each market use the authenticated first-band retail margin percentage returned by IG at the census. Approximate daily margin as:

`abs(stake * IG_quote_level) * margin_rate`

summed across the portfolio.

Do **not** retrospectively resize, skip or prioritise positions to fit the £2,000 account. If estimated margin utilisation reaches or exceeds 100% of translated equity, record the date and the portfolio fails the feasibility gate.

Also report 95th-percentile margin utilisation and the maximum number of concurrent non-zero positions.

## 10. Historical periods and comparators

Run:

- build: 2010-01-01 to 2018-12-31;
- holdout: 2019-01-01 to latest common date through the freeze;
- full period.

Comparators:

1. original unrounded 22-market MAIN research model;
2. original 22-market IG-rounded translation at 1x and 2x spreads;
3. MAIN-IG Expanded v1 at 1x and 2x spreads;
4. ES/S&P benchmark scaled ex post to Expanded v1's realised volatility for descriptive return/drawdown comparison only.

## 11. Required reporting

For build, holdout and full period report:

- admitted source roots and mapped IG instruments;
- structural exclusions and reason codes;
- trading days;
- annualised return above cash / CAGR;
- annualised volatility;
- Sharpe;
- max drawdown;
- ending £2,000 equity;
- monthly correlation to the original unrounded MAIN;
- monthly correlation to the original 22-market IG translation;
- total spread cost, turnover and roll cost;
- fraction of desired non-zero targets rounded to zero;
- fraction rounded by >25% in magnitude;
- maximum and 95th-percentile margin utilisation;
- maximum concurrent positions;
- P&L by market and asset family;
- contribution concentration;
- number of new markets with T1, Forced and Dip activity.

## 12. Frozen economic gate

Expanded v1 advances to demo paper trading only if, on the 2019-2026 holdout, all are true:

1. 1x-cost Sharpe >= 0.50;
2. 2x-cost Sharpe >= 0.40;
3. annualised return above cash >0 at both 1x and 2x costs;
4. max drawdown at 1x is no worse than -20%;
5. monthly correlation with the original unrounded MAIN >=0.60 (lower than the original translation's 0.70 gate because the universe is intentionally expanded, but still requires the same engine to dominate the behaviour);
6. maximum estimated margin utilisation <100%;
7. no single market contributes >40% of absolute positive holdout P&L;
8. 1x Expanded v1 has higher return per unit realised volatility than same-period ES;
9. 1x Expanded v1 Sharpe is not more than 0.10 below the original 22-market IG translation Sharpe on the same holdout dates.

The benchmark 22-market translation retains its own already-frozen gate in `ECONOMIC_TRANSLATION_SPEC.md`; this file does not rewrite it.

## 13. No rescue / no selection after results

After any Expanded v1 P&L is viewed, do not:

- add or remove markets because of their returns;
- change market-family boundaries or duplicate rules;
- change 0.01 rounding;
- change T1 / Forced / Dip thresholds, holds, filters, multipliers or lags;
- change breadth threshold;
- substitute DFB instruments for failing dated instruments;
- replace the frozen spread snapshot with a more favourable one;
- cap positions or introduce a margin allocator to rescue a margin failure;
- change the pass thresholds.

If Expanded v1 fails, record why. Any smaller subset, alternative weighting, margin allocator, or different execution venue is a separately pre-registered experiment.