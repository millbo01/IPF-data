# Index large-move continuation / reversal anatomy — v1 result

## Status
Promising market-pattern candidate; next step is executable venue/cost validation, with NDX 09:31-10:00 reversal the primary candidate.

This track was promoted from the plain-return control in the leveraged-ETF ablation. It does not currently carry a forced-flow/IPF causal attribution.

## Data and construction
- Market proxies: SPY for S&P 500; QQQ for Nasdaq-100.
- QuantConnect minute data.
- Total rows: 7,224.
- Available sample: 2012-01-04 through 2026-07-02.
- Signal fixed at 15:45 New York: return from previous regular-session close to 15:45.
- Signal standardized with a rolling z-score using prior observations only.
- Build/calibration: 2012-2018.
- Fixed build-derived absolute-z thresholds:
  - SPX: P80 1.2278; P90 1.7595; P95 2.2530.
  - NDX: P80 1.2681; P90 1.7796; P95 2.3646.
- Windows: 15:45-close continuation; close-next 09:31 reversal; 09:31-10:00 reversal; close-next 10:00 total reversal.
- No orders or costs were applied.

## NDX
### Build 2012-2018
P80: n=337; late +4.415 bp; overnight -0.434 bp; morning +2.118 bp; total +1.201 bp; total hit 51.9%.
P90: n=169; late +8.734 bp; overnight +0.738 bp; morning +6.083 bp; total +5.876 bp; total hit 56.2%.
P95: n=85; late +11.322 bp; overnight -4.887 bp; morning +13.739 bp; total +6.973 bp; total hit 54.1%.

### 2019-2021
P80 total +25.879 bp, driven by +28.270 bp overnight.
P90 total +39.034 bp, driven by +48.702 bp overnight.
P95 total +59.806 bp, driven by +95.082 bp overnight; 09:31-10:00 gives back -34.916 bp.
Treat this as a distinct regime rather than a current expected-return estimate.

### 2022-2024
P80: n=161; late +1.841 bp; overnight +3.998 bp; morning -0.993 bp; total +2.972 bp; hit 55.9%.
P90: n=75; late +5.106 bp; overnight -2.265 bp; morning +4.786 bp; total +2.363 bp; hit 56.0%.
P95: n=34; late +3.206 bp; overnight +3.277 bp; morning +7.036 bp; total +10.000 bp; hit 61.8%.

### 2025-2026
P80: n=69; late +0.382 bp; overnight +1.176 bp; morning +3.284 bp; total +4.299 bp; hit 58.8%.
P90: n=30; late -3.105 bp; overnight -7.698 bp; morning +11.553 bp; total +3.515 bp; hit 55.2%.
P95: n=13; late +0.191 bp; overnight -9.854 bp; morning +27.290 bp; total +16.585 bp; hit 76.9%.

The current-era result is concentrated in the post-open 09:31-10:00 fade, especially on the most extreme prior-day moves. The higher-threshold overnight leg is adverse.

Direction split across post-2018 P80 events:
- after up days: n=153; total reversal +9.661 bp; hit 52.3%.
- after down days: n=175; total reversal +10.511 bp; hit 62.1%.

## SPX comparison
Recent SPX is less clean:
- 2025-2026 P80: morning +5.752 bp; total +6.973 bp.
- P90: morning +7.958 bp but overnight -10.329 bp; total -2.635 bp.
- P95: morning +20.695 bp but overnight -32.499 bp; total -12.264 bp.

SPX is a robustness comparison, not the primary implementation candidate.

## Interpretation
The strongest descriptive candidate is:

Following an unusually large previous-day Nasdaq move, fade the move after the next session opens and exit around 10:00 New York.

This has not yet passed realistic spread/slippage, IG minimum stake/margin, event-level drawdown, or entry-time sensitivity.

## Next test
Primary:
- NDX/QQQ.
- Enter fade after the open, initially 09:31.
- Exit 10:00.
- Fixed P80/P90/P95 thresholds inherited from this study.
- Apply realistic small-account IG NASDAQ spread, slippage, minimum stake and margin.
- Report gross/net expectancy, hit rate, drawdown, trade count, yearly chronology and break-even cost.
- Do not use the extraordinary 2019-2021 overnight returns as the basis for expected profitability.
