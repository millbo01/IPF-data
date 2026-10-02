# IPF Trading Bot — Consolidated Research Report and Meta-Analysis Handover

**Scope:** research performed and reviewed in the current project/chat sequence through 2026-10-02.  
**Purpose:** preserve the experimental chain, data provenance, corrections, negative results, surviving mechanisms, and current best trading candidate so a new agent can continue without relying on conversational memory.

---

## 1. Executive summary

The research began with a validated multi-market futures strategy, **MAIN**, and attempted to turn it into something economically executable on a small UK account, particularly through IG spread betting. That exercise separated an important distinction:

1. **The original futures research strategy still has a positive edge in its research representation.**
2. **The broad, continuously rebalanced £2,000 IG implementation fails economically because transaction costs overwhelm the strategy.**
3. Expanding from 22 to 36 markets weakens the underlying signal, especially the Forced book, and does not solve implementation economics.
4. A series of explicitly IPF-style forced-flow/capacity studies then tested whether compelled market flows produce more directly tradable opportunities.
5. **LC1 strongly validated a market-impact mechanism:** comparable aggressive flow produces larger immediate displacement when receiving-side capacity is lower. That mechanism did not become a stable standalone trading rule.
6. **VIX-ETP forced flow was killed as a current late-equity trading architecture.** Completing the modern product complex with UVIX/SVIX did not rescue it.
7. **Equity leveraged-ETF rebalancing looked promising initially but failed the causal ablation:** most of the signal was simply large intraday index moves, not incremental LETF pressure.
8. The control revealed the strongest current candidate: **after an unusually large Nasdaq move, fading the previous move from approximately 09:31 to 10:00 New York the next session**. The effect is strongest at extreme P90/P95 thresholds in recent years, but has not yet been subjected to realistic IG execution costs or full trade-level risk analysis.

The project should therefore resume with **NDX/QQQ next-session 09:31–10:00 reversal execution testing**, not with further tuning of VIX ETP or leveraged-ETF forced-flow stories.

---

## 2. Canonical research architecture

Repository: `millbo01/IPF-data`

Important branches:

| Branch | Purpose |
|---|---|
| `research/main-ig-translation` | MAIN -> IG translation, census, expanded-universe and diagnostics |
| `research/lc1-liquidity-capacity` | LC1-A immediate impact and LC1-B reversal/capacity-restoration work |
| `research/vix-etp-flow-v2` | VIX ETP public data, corrected historical leverage, UVIX/SVIX reconstruction, final result |
| `research/equity-letf-rebalance` | Equity leveraged-ETF AUM data, screen and ablation |
| `research/index-large-move-reversal` | Current plain-index continuation/reversal candidate |
| `research/meta-analysis` | Consolidated report, experiment ledger, provenance notes and handover |

Where a dataset is stored in GitHub, that branch/path is the preferred source. QuantConnect-provided minute/tick data are not duplicated as raw files in the repo; reproducibility is via exact methods/scripts where archived, dated windows, algorithm IDs and output result files.

---

## 3. MAIN — original validated futures strategy

### 3.1 Universe

Original 22 futures markets:

`ES, NQ, YM, ZT, ZF, ZN, ZB, 6E, 6J, 6B, 6A, 6C, GC, SI, HG, CL, NG, HO, RB, ZC, ZS, ZW`

### 3.2 Books

**T1:** 12-month trend.

**Forced:** requires true-range percentile >=80, volume percentile >=80, matched-contract OI-change percentile <=20, 5-day vol > 20-day vol, then 10-trading-day hold in the forced-move direction.

Frozen Forced exclusions:
`SI, GC, 6C, HG, CL`.

**Dip:** prior 20-day range break against T1; enter with T1; 10-day hold.

Existing Strain and Overwhelmed filters were retained. Overwhelmed uses one-third of currently valid markets within a 3-day window.

Frozen 10% portfolio-vol multipliers:

`M_MAIN = {"T1": 1.4335, "F": 4.54643, "Dip": 3.64361}`

Production MAIN nets T1/F/Dip by market before sizing and uses a 10% rebalance band rather than continuously resizing every day.

### 3.3 Current benchmark from the corrected/direct-load diagnostic

Original 22 unrounded research representation:
- build Sharpe: **0.956**
- holdout Sharpe: **0.906**
- holdout annualised return: **9.92%**
- holdout vol: **10.94%**

Component holdout Sharpe:
- T1: **0.622**
- Forced: **0.548**
- Dip: **0.387**

A prior run reported holdout Sharpe 0.990. The later direct-load diagnostic reports 0.906; use **0.906** for the currently reproduced diagnostic dataset.

---

## 4. IG spread-bet translation

### 4.1 Live venue facts

Authenticated IG REST probing established:
- `minDealSize = 0.01` on mapped markets.
- starting-account translation tests used **£2,000**.

Target handling:
- combine desired stake by market first;
- absolute desired stake <0.01 -> zero;
- otherwise round to nearest £0.01/point, half away from zero.

Transaction costs:
- target change = half spread × absolute stake change;
- roll = half spread old close + half spread new open;
- both 1× and 2× spread scenarios considered.

Margin:
- `abs(stake × IG quote) × margin rate`.

No retrospective resizing was allowed.

### 4.2 Quote transforms

Original 22 mapping classes:
- ES/NQ/YM ×1
- ZT/ZF/ZN/ZB ×100
- 6E/6B/6A ×10000
- 6J inverse `100 / CME_price`, position sign reversed
- 6C inverse `10000 / CME_price`, position sign reversed
- GC ×1
- SI ×100
- HG ×10000
- CL ×100
- NG ×1000
- HO/RB ×10000
- ZC/ZS/ZW ×1

Frozen spread assumptions:
ES 1.0, NQ 3.0, YM 6.0, ZT 2.0, ZF 2.0, ZN 4.0, ZB 4.0, 6E 10.6, 6J 10.0, 6B 9.9, 6A 8.6, 6C 7.3, GC 0.8, SI 10, HG 40, CL 6, NG 10, HO 30, RB 30, ZC 1, ZS 2, ZW 1.

Margins:
- indices 5%
- US Treasuries 3.33%
- EUR/JPY/GBP/CAD FX 3.33%
- AUD 5%
- GC 5%
- SI/HG, energy and grains 10%

### 4.3 Initial risk/granularity probe

At the authenticated £0.01 minimum stake, many component exposures were technically expressible:
- T1: 9/15 directly observed markets
- Dip: 11/15
- Forced: 8/10 directly observed eligible markets

Minimum-stake annualised-risk examples:
6E £4.81; 6J £13.74; 6B £5.83; GC £9.14; SI £23.32; HG £147.13; CL £33.69; HO £194.11; RB £159.93; ZC £1.08; ZS £2.01; ZW £2.06.

This justified the historical economic rerun rather than rejecting IG on granularity alone.

---

## 5. Expanded-v1 universe test

### 5.1 Expansion

Original 22 plus 14 accepted additions:

`6S, 6N, 6Z, AJY, EAD, ECD, ESK, BZ, UB, ZO, ZM, ZL, PA, PL`

Final universe: **36 markets**.

Four candidate transforms failed:
Lumber, Nikkei, Russell 2000, Lean Hogs.

### 5.2 Frozen £2,000 result

Original 22 holdout, 1× observed spreads:
- annualised return **-40.81%**
- vol **8.18%**
- Sharpe **-4.990**
- max DD **-96.20%**
- end equity **£0.35**

Expanded 36 holdout, 1×:
- annualised return **-33.60%**
- vol **5.27%**
- Sharpe **-6.377**
- max DD **-93.19%**
- max margin **31.27%**
- end equity **£5.18**

Expanded 36 holdout, 2× stress:
- annualised return **-22.28%**
- Sharpe **-3.120**
- max DD **-83.34%**
- end equity **£0.40**

Execution diagnostics:
- total 1× spread cost **£2,382.96**
- roll cost included **£573.03**
- desired non-zero targets rounded to zero **81.84%**
- monthly correlation with unrounded MAIN **0.076**

Frozen verdict: **FAIL_EXPANDED_V1_GATE**.

Interpretation: failure of the specific small-account pro-rata IG implementation, not rejection of the underlying MAIN research edge.

---

## 6. Practical-v2 concentration/risk sweep

### 6.1 Design

75 configurations:
- risks: 10%, 15%, 20%, 25%, 30%
- active caps: 3, 5, 8, 12, 36
- modes: BAND10, BAND20, SIGNAL

Each tested at 1× and 2× spread stress.

Selection:
- rank markets by absolute intended MAIN fraction;
- select top K;
- L2-renormalize selected fractions to preserve full daily target-weight norm;
- apply risk scale.

IG analogue of the old 0.75-lot floor: `0.0075` stake.

### 6.2 Result

Correct V4 direct-Train run:
- original unrounded MAIN holdout Sharpe **0.906**
- **positive holdout: 0/75**
- **positive 2× holdout: 0/75**
- **positive build + holdout + 2×: 0/75**

Representative best robust:
- risk 10%, cap 3, BAND20
- build Sharpe about **-1.20**
- holdout Sharpe about **-1.13**
- holdout return about **-4.98%**
- max DD about **-36.5%**
- max margin about **26.6%**
- end equity about **£821**
- 2× Sharpe about **-1.87**
- trades about **3,278**
- correlation to MAIN about **0.35**

At cap=3 and 10–15% risk, rounding-to-zero was only around 3–4%, yet the strategy remained negative. Concentration and higher risk did not solve implementation.

Best concentrated contribution diagnostics:
positive ES +52.52, ZT +42.96, ZF +21.83, 6E +19.42, 6J +16.73; negative ZC -247.32, ZS -179.45, ZW -89.13, 6B -22.02, 6S -21.37.

These rankings were not used to delete markets post hoc.

---

## 7. MAIN -> IG diagnostic decomposition

This separated ideal strategy behaviour, £0.01 rounding and spreads.

### 7.1 Original 22 at 10% risk

Exact fractional, zero cost:
- holdout Sharpe **1.115**
- annualised return **12.03%**
- max DD **-11.83%**

£0.01-rounded, zero cost:
- holdout Sharpe **1.197**
- annualised return **12.64%**
- max DD **-11.77%**
- **13.74%** of desired non-zero targets round to zero

£0.01-rounded with observed IG spreads:
- daily execution holdout Sharpe **-4.957**
- signal-only **-4.919**
- 20% band **-4.923**

At 20% risk, zero-cost versions remain strong but margin rises to roughly 105%.
At 30%, zero-cost versions remain strong but margin reaches roughly 158%.

### 7.2 Expanded 36

At 10% risk:
- exact zero-cost holdout Sharpe **0.792**
- rounded zero-cost holdout Sharpe **0.882**
- observed-spread versions destroyed

### 7.3 Conclusion

The dominant £2k IG failure is **transaction cost, not stake rounding**.

The 36-market expansion also weakens the research strategy:
- original 22 holdout Sharpe **0.906**
- expanded 36 **0.601**
- Forced falls from **0.548** to **0.163**

Portfolio implication:
retain original 22 as the stronger research universe; MAIN can remain a directional/state prior; do not express broad continuous MAIN through IG at ~£2k under tested spread assumptions.

---

## 8. LC1 — liquidity/capacity mechanism

### 8.1 LC1-A hypothesis

For comparable aggressive signed flow, does lower pre-existing contra-side displayed capacity produce greater immediate same-direction price displacement?

Markets: ES, ZN, CL.  
Build: 24 preselected 2025 dates.  
Holdout: 12 preselected 2026 dates.  
Signal window: 30 seconds.  
Capacity: median contra-side best-quote size during prior 30 seconds.  
Pressure: aggressive signed trade quantity.

### 8.2 LC1-A holdout

| Market | Interaction beta | 95% CI | matched low-high | LOO |
|---|---:|---:|---:|---:|
| ES | +0.3854 bp | [+0.1807,+0.5901] | +1.7245 bp | 12/12 |
| ZN | +0.0596 bp | [+0.0200,+0.0991] | +0.2396 bp | 12/12 |
| CL | +1.7635 bp | [+0.7754,+2.7517] | +4.3664 bp | 12/12 |

**Immediate mechanism: PASS across all three markets.**

Durable result:
> For comparable aggressive flow, lower pre-existing contra-side capacity is associated with greater immediate same-direction price displacement.

No market met the frozen forward-continuation promotion rule. The effect was largely contemporaneous.

Final: **validated market-impact mechanism, not a promoted trading strategy.**

---

## 9. LC1-B — restoration/pressure-decay reversal

Hypothesis: after a high-pressure/low-capacity displacement, is reversal stronger when same-direction pressure decays and contra-side capacity restores?

Decision: t+60s after release observation.  
Primary outcome: 5-minute reversal.

Holdout:

| Market | release interaction | matched joint-release minus stalled | LOO | verdict |
|---|---:|---:|---:|---|
| ES | +0.3283 bp | +1.3961 bp | 12/12 | PASS |
| ZN | +0.0460 bp | -0.1644 bp | 1/12 | FAIL |
| CL | +2.0484 bp | +1.2699 bp | 10/12 | PASS |

Mechanism gate: **PASS 2/3 markets.**

ES non-overlapping executable screen:

Build:
- 69 trades
- mean gross **-0.2251 bp/trade**
- gross/sample-day **-0.6753 bp**
- positive-day share **30.43%**

Holdout:
- 62 trades
- mean gross **+2.4782 bp/trade**
- gross/sample-day **+12.8040 bp**
- positive-day share **83.33%**

Build leave-one-day-out mean positive only **1/23** versions.

Final: **candidate killed by economic triage**. LC1-B remains mechanism evidence only.

---

## 10. VIX ETP forced-flow track

### 10.1 Hypothesis and products

Leveraged/inverse VIX ETPs mechanically rebalance VIX-futures exposure.

Convexity scale:
`beta * (beta - 1) * AUM`

Predicted rebalance:
`beta * (beta - 1) * lagged_AUM * intraday_benchmark_return`

Products:
- UVXY +1.5x current; +2x before 2018-02-28
- VIXY +1x
- SVXY -0.5x current; -1x before 2018-02-28
- UVIX +2x
- SVIX -1x

### 10.2 Public data archive

ProShares:
- 11,502 official daily AUM/NAV rows
- SVXY, UVXY, VIXY
- 2011-01-03 to 2026-10-01

Volatility Shares:
- 347 archived document links
- 106 assigned SVIX/UVIX monthly statements
- 51 usable monthly AUM anchors in the modern QC reconstruction

Branch: `research/vix-etp-flow-v2`  
Data: `data/vix_etp_flow/backfill/`

### 10.3 First screen and correction

Initial fixed-modern-beta screen:
- build extreme pressure +6.08 bp/event, 64.1% hit
- holdout +0.07 bp/event, 43.2% hit

Historical leverage was then corrected:
- UVXY 2x before 2018-02-28, 1.5x after
- SVXY -1x before, -0.5x after

Corrected early chronology:
- 2012-2017 approximately +6.0 bp/event in expected opposite-equity direction
- 2018 approximately +35.4 bp/event, only 10 events
- 2019-2021 approximately +2.3 bp/event, unstable
- 2022-2026 approximately -2.3 bp/event

### 10.4 Complete modern complex

UVIX/SVIX were economically material:
- median VS/ProShares convexity ratio **1.321**
- IQR **0.638–2.194**
- median VS share of total **56.9%**

Complete modern result:

Build 2022-05 to 2023-12:
- n 72
- late **-4.149 bp/event**
- hit 31.9%

Holdout 2024-01 to 2026-07:
- n 164
- late **-3.287 bp/event**
- hit 45.1%
- next-morning reversal **-4.312 bp/event**

Annual complete-complex means were negative in every reported year 2022–2026.

Final: **VIX ETP -> late-equity standalone architecture killed.**

---

## 11. Equity leveraged-ETF rebalancing

### 11.1 Universe and data

SPX:
UPRO +3x, SPXU -3x, SSO +2x, SDS -2x.

NDX:
TQQQ +3x, SQQQ -3x, QLD +2x, QID -2x.

Official ProShares rows:

| Ticker | Rows | Start | End |
|---|---:|---|---|
| QID | 5,089 | 2006-07-11 | 2026-10-01 |
| QLD | 5,104 | 2006-06-19 | 2026-10-01 |
| SDS | 5,089 | 2006-07-11 | 2026-10-01 |
| SPXU | 4,346 | 2009-06-23 | 2026-10-01 |
| SQQQ | 4,187 | 2010-02-09 | 2026-10-01 |
| SSO | 5,104 | 2006-06-19 | 2026-10-01 |
| TQQQ | 4,187 | 2010-02-09 | 2026-10-01 |
| UPRO | 4,346 | 2009-06-23 | 2026-10-01 |

Branch: `research/equity-letf-rebalance`  
Data: `data/equity_letf_rebalance/`

### 11.2 Initial screen

Signal:
`sum(beta*(beta-1)*lagged_AUM) * intraday_index_return_to_15:45`

SPX:
- build +5.465 bp/event, 59.1% hit
- holdout +2.158 bp/event, 49.7% hit
- 2019-21 +3.980
- 2022-24 +2.596
- 2025-26 -1.782

NDX:
- build +4.732 bp/event, 57.9% hit
- holdout +4.344 bp/event, 50.3% hit
- 2019-21 +9.024
- 2022-24 +1.886
- 2025-26 +0.862

Capacity normalization using SPY/QQQ 15:30-15:44 dollar turnover did not improve stability:
SPX holdout +0.140 bp; NDX +0.940 bp; both negative in 2025-26.

Next-window reversal looked stronger:
SPX +9.331 bp/event, 55.4%; NDX +8.598 bp/event, 56.2%.

### 11.3 Ablation

Because `beta(beta-1) > 0` for all included LETFs:

`sign(predicted pressure) = sign(intraday benchmark return)`

The apparent forced-flow signal could simply be a large-move pattern.

SPX holdout:
- pressure late +2.158
- plain return +1.945
- matched plain +0.940
- event-overlap Jaccard **0.848**
- incremental pressure coefficient **+0.385 bp/z**
- plain-return next-window reversal **+13.043 bp**, 58.3%

NDX holdout:
- pressure late +4.344
- plain return +4.819
- matched plain +3.765
- overlap **0.818**
- incremental pressure coefficient **+0.634 bp/z**
- plain-return next-window reversal **+10.113 bp**, 57.5%

Pressure-only NDX holdout events:
- late **-3.877 bp**
- next **-10.230 bp**

Final: **LETF forced-flow causal attribution not supported strongly enough.**

The plain large-move control was promoted.

---

## 12. Index large-move continuation/reversal anatomy

This is the **current active candidate**.

### 12.1 Data and signal

QuantConnect minute data:
- SPY and QQQ
- 7,224 rows
- 2012-01-04 to 2026-07-02

Signal at 15:45 NY:
return from previous regular-session close to 15:45.

Rolling z-score uses prior observations only.

Build: 2012-2018.

Fixed build-derived thresholds:

SPX:
P80 1.2278; P90 1.7595; P95 2.2530.

NDX:
P80 1.2681; P90 1.7796; P95 2.3646.

Windows:
1. 15:45-close continuation
2. close-next 09:31 reversal
3. next 09:31-10:00 reversal
4. close-next 10:00 total reversal

### 12.2 NDX build

| Threshold | n | Late | Overnight | Morning | Total | Total hit |
|---|---:|---:|---:|---:|---:|---:|
| P80 | 337 | +4.415 | -0.434 | +2.118 | +1.201 | 51.9% |
| P90 | 169 | +8.734 | +0.738 | +6.083 | +5.876 | 56.2% |
| P95 | 85 | +11.322 | -4.887 | +13.739 | +6.973 | 54.1% |

The 09:31–10:00 reversal strengthens with event extremity in build.

### 12.3 NDX 2019-2021

This period is abnormal and dominated by overnight reversal:
- P80 total +25.879 bp, overnight +28.270
- P90 total +39.034, overnight +48.702
- P95 total +59.806, overnight +95.082, morning -34.916

Do not use this period as the basis for current expected return.

### 12.4 NDX 2022-2024

| Threshold | n | Late | Overnight | Morning | Total | Total hit |
|---|---:|---:|---:|---:|---:|---:|
| P80 | 161 | +1.841 | +3.998 | -0.993 | +2.972 | 55.9% |
| P90 | 75 | +5.106 | -2.265 | +4.786 | +2.363 | 56.0% |
| P95 | 34 | +3.206 | +3.277 | +7.036 | +10.000 | 61.8% |

### 12.5 NDX 2025-2026

| Threshold | n | Late | Overnight | Morning | Total | Total hit |
|---|---:|---:|---:|---:|---:|---:|
| P80 | 69 | +0.382 | +1.176 | +3.284 | +4.299 | 58.8% |
| P90 | 30 | -3.105 | -7.698 | +11.553 | +3.515 | 55.2% |
| P95 | 13 | +0.191 | -9.854 | +27.290 | +16.585 | 76.9% |

The modern edge is most clearly located in the **09:31–10:00 next-session fade**, not in holding overnight.

At P90/P95, the overnight position is adverse while the opening-session reversal is strongly positive.

### 12.6 Direction split

Post-2018 NDX P80:
- after up days: n 153; total reversal +9.661 bp; hit 52.3%
- after down days: n 175; total reversal +10.511 bp; hit 62.1%

The broad effect is not confined to only one sign, although down-day reversals show a higher hit rate.

### 12.7 SPX comparison

Recent SPX is less clean:
- 2025-26 P80 morning +5.752 bp; total +6.973
- P90 morning +7.958 but overnight -10.329; total -2.635
- P95 morning +20.695 but overnight -32.499; total -12.264

SPX remains a robustness comparison rather than primary target.

---

## 13. Current best candidate

Highest-priority next experiment:

> **NDX/QQQ: after a sufficiently large prior-day move, enter a fade after the next regular-session open, initially 09:31 NY, and exit around 10:00 NY.**

Carry forward all three fixed thresholds:
P80, P90, P95.

Do not optimize threshold yet.

Why this is preferable:
- no need for overnight exposure in the contemporary regime;
- larger gross edge at P90/P95 in the recent sample;
- candidate appears in original build and recent periods;
- simpler signal;
- sparse turnover;
- potentially compatible with a small account if IG NASDAQ economics are acceptable.

---

## 14. Required next test

Perform an **executable IG/Nasdaq morning-fade study**.

Signal:
on day T, determine whether the 15:45 rolling-z move crossed P80/P90/P95.

Trade day T+1:
- direction opposite day T move
- initial entry 09:31 NY
- exit 10:00 NY
- do not assume overnight exposure

Execution realism:
- identify/confirm IG NASDAQ / US Tech spread-bet instrument
- minimum stake
- margin
- opening-session spread
- spread widening around 09:30
- conservative slippage/cost stress

Required outputs:
- gross and net mean/median bp
- hit rate
- trade count and trades/year
- £2,000 equity curve
- max drawdown
- margin utilisation
- break-even cost
- year-by-year results
- up-day/down-day split
- entry sensitivity 09:31/09:32/09:35 if possible, without selecting the best timestamp on the same sample
- full trade ledger

---

## 15. Dead / demoted tracks

Do not spend more same-sample optimization effort on:

**Broad MAIN -> £2k IG:** dead under tested spreads. MAIN itself remains a research prior.

**Expanded 36 MAIN:** underlying quality weaker than original 22 and translation still fails.

**LC1 continuation:** mechanism passes; forward rule fails.

**LC1-B ES reversal:** strong 2026 holdout but negative-gross build expectancy.

**VIX ETP -> late equity:** modern complete complex fails even after adding material UVIX/SVIX.

**LETF pressure as distinct forced-flow signal:** ablation shows insufficient increment beyond plain intraday return.

---

## 16. Surviving mechanisms / useful inputs

1. **MAIN directional/state signal** — positive unrounded futures research edge.
2. **LC1 receiving capacity** — robust immediate market-impact amplifier.
3. **Forced-flow research discipline** — known compelled actor + measurable receiving capacity remains attractive only if it beats simpler controls.
4. **Large-move path dependence** — current actionable empirical candidate, especially NDX next-session morning reversal.

Do not add MAIN or LC1 as filters to the new candidate until the candidate survives standalone economics.

---

## 17. Data provenance and reproducibility

### Public data stored in GitHub

VIX:
branch `research/vix-etp-flow-v2`, path `data/vix_etp_flow/backfill/`.

LETF:
branch `research/equity-letf-rebalance`, path `data/equity_letf_rebalance/`.

MAIN/IG:
branch `research/main-ig-translation`, including frozen configs, expanded exposures, census/transform scripts and result summaries.

### QuantConnect data not stored raw

The repository does not contain complete standalone raw copies of:
- futures history used by MAIN
- tick/quote/trade history used by LC1
- SPY/QQQ minute history used by LETF and index reversal

For these, reproducibility rests on exact algorithm logic where archived, sample windows, algorithm IDs and output result files/logs.

A companion handover ZIP generated from the working session contains the QC scripts and logs that were still locally available.

---

## 18. Important corrections

1. MAIN direct-Train loading became the stable QC method after earlier loader issues.
2. Use MAIN holdout Sharpe 0.906 for the later direct-load diagnostic; older documentation records 0.990 from a different exact run/dataset.
3. VIX historical leverage corrected: UVXY 2x and SVXY -1x before 2018-02-28.
4. One VIX regime diagnostic selected orientation from the controlled OLS coefficient and produced a sign contradiction; subsequent interpretation and the modern test fixed the economic direction explicitly.
5. Volatility Shares archive parser was repaired to assign image-only links by SVIX/UVIX table column.
6. LETF causal confound was explicitly tested rather than assumed away.
7. Current reversal interpretation is **not** simply overnight mean reversion: the strongest recent NDX component is 09:31–10:00.

---

## 19. File map

### MAIN
Branch `research/main-ig-translation`
- `research/main_ig_translation/MAIN_IG_DIAGNOSTIC_2026-10-01.md`
- `research/main_ig_translation/EXPANDED_V1_RESULT_2026-10-01.md`
- `research/main_ig_translation/RISK_PROBE_RESULTS_2026-10-01.md`

### LC1
Branch `research/lc1-liquidity-capacity`
- `research/lc1_liquidity_capacity/RESULTS_LC1A.md`
- `research/lc1_liquidity_capacity/RESULTS_LC1B.md`
- `research/lc1_liquidity_capacity/SPEC.md`
- `research/lc1_liquidity_capacity/SPEC_LC1B.md`

### VIX
Branch `research/vix-etp-flow-v2`
- `research/vix_etp_flow/RESULTS_V2_FINAL.md`
- `research/vix_etp_flow/PIPELINE_V2.md`
- `data/vix_etp_flow/backfill/`

### LETF
Branch `research/equity-letf-rebalance`
- `research/equity_letf_rebalance/RESULTS_V1_SCREEN.md`
- `research/equity_letf_rebalance/RESULTS_V2_ABLATION.md`
- `data/equity_letf_rebalance/`

### Current candidate
Branch `research/index-large-move-reversal`
- `research/index_large_move_reversal/SPEC.md`
- `research/index_large_move_reversal/RESULTS_V1_ANATOMY.md`

---

## 20. Bottom line

The research progressively simplified the live question.

MAIN remains profitable in a research futures representation but broad £2k IG execution is uneconomic under tested spreads.

LC1 provides the strongest IPF mechanism evidence — receiving capacity changes immediate impact — but did not yield a stable trade.

VIX and LETF forced-flow ideas were corrected, extended and then demoted rather than overfit.

The best current candidate is simpler:

**after an unusually large Nasdaq move, fade it during the next session’s first half-hour, with the current leading implementation window approximately 09:31–10:00 NY.**

That candidate now needs execution realism, not another mechanism story.
