# MAIN -> IG Expanded v1 economic result

## Status
Final frozen result from the preregistered £2,000 IG translation test. No rescue/tuning applied after viewing P&L.

## Final universe
- Original benchmark: 22 markets.
- Expanded source/IG census: 18 new candidates reached quote-transform testing.
- Quote-transform gate: 14 passed, 4 failed (Lumber, Nikkei, Russell 2000, Lean Hogs).
- Final Expanded v1 universe: 36 markets = original 22 + 14 additions.

## QuantConnect run
LEAN Engine v2.5.0.0.18149, Algorithm Id `37fa66588151b43ad509280b2c3d534c`.

QA:
- original snapshot days: 4579
- expanded snapshot days: 4580
- original unit fixes: 924
- expanded unit fixes: 932
- original bad days: 0
- expanded bad days: 4

## Benchmark
Original unrounded MAIN holdout Sharpe: **0.990**.

## IG translated results
### Original 22, holdout, 1x observed IG spreads
- annualised mean return: **-40.81%**
- realised vol: **8.18%**
- Sharpe: **-4.990**
- max drawdown: **-96.20%**
- max margin utilisation: **7.27%**
- ending equity from £2,000: **£0.35**

### Expanded 36, build, 1x
- annualised mean return: **-35.29%**
- realised vol: **6.97%**
- Sharpe: **-5.062**
- max drawdown: **-96.22%**
- ending equity: **£75.60**

### Expanded 36, holdout, 1x
- annualised mean return: **-33.60%**
- realised vol: **5.27%**
- Sharpe: **-6.377**
- max drawdown: **-93.19%**
- max margin utilisation: **31.27%**
- p95 margin utilisation: **2.64%**
- maximum concurrent positions: **5**
- ending equity from £2,000: **£5.18**

### Expanded 36, holdout, 2x spread stress
- annualised mean return: **-22.28%**
- realised vol: **7.14%**
- Sharpe: **-3.120**
- max drawdown: **-83.34%**
- max margin utilisation: **3.65%**
- ending equity from £2,000: **£0.40**

### Expanded 36, full period, 1x
- annualised mean return: **-34.51%**
- realised vol: **6.24%**
- Sharpe: **-5.529**
- max drawdown: **-99.74%**
- ending equity: **£5.18**

## Execution diagnostics
- total 1x spread cost: **£2,382.96**
- roll cost included within that: **£573.03**
- desired non-zero targets rounded to zero: **81.84%**
- desired targets rounded by >25% (among non-zero desired targets): **1.52%**
- monthly correlation to unrounded MAIN: **0.076**
- single positive-market concentration: **100%**
- Expanded return/vol: **-6.386**
- ES same-period return/vol: **0.750**
- top positive holdout contribution: ZT **+£0.06**; remaining reported top markets approximately zero.

## Frozen gate
- G1 1x Sharpe >= 0.50: FAIL
- G2 2x Sharpe >= 0.40: FAIL
- G3a 1x return > 0: FAIL
- G3b 2x return > 0: FAIL
- G4 1x max drawdown no worse than -20%: FAIL
- G5 monthly correlation to MAIN >= 0.60 (Expanded-v1 gate): FAIL
- G6 max margin < 100%: PASS
- G7 no single positive market > 40%: FAIL
- G8 return per vol > ES: FAIL
- G9 Expanded Sharpe no more than 0.10 below original-22 IG: FAIL

## Verdict
**FAIL_EXPANDED_V1_GATE**

This failure applies to the frozen pro-rata MAIN -> IG implementation at approximately £2,000 with 0.01 stake increments and the frozen observed spread/margin assumptions. It does not invalidate the underlying futures MAIN mechanism: the same run reports original unrounded MAIN holdout Sharpe 0.990. The dominant implementation symptoms are coarse stake granularity and transaction-cost destruction: 81.84% of desired non-zero market targets round to zero and total 1x spread cost exceeds the initial account equity.

Any smaller/sparser executable subset, different rebalance architecture, different capital level, or new signal/overlay is a new preregistered test rather than a rescue of Expanded v1.
