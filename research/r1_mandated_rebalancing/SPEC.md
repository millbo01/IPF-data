# R1 — Mandated Rebalancing

Status: **FROZEN BEFORE FIRST PROJECT RUN**

This directory contains the first independent IPF trading-mechanism challenge outside the existing forced-flow/crypto/futures family.

## Question

Does predictable institutional equity/bond rebalancing still forecast the next trading day's S&P 500 minus 10-year Treasury futures return after the sample used by Harvey, Mazzoleni & Melone (HMM)?

The IPF interpretation is that target-allocation rules create an effective constraint: when asset weights drift, some institutional actors lose discretion and must sell the overweight asset and buy the underweight asset. R1 tests the published base mechanism before adding any IPF-specific liquidity-capacity interaction.

## Literature anchor

HMM, *The Unintended Consequences of Rebalancing*, NBER Working Paper 33554 (2025; revised 2026).

Paper sample: 1997-09-10 to 2023-03-17.

The paper constructs 60/40 equity/bond portfolios from S&P 500 and 10-year Treasury-note futures returns. The Threshold signal is the equity-weight deviation from 60% for threshold-rebalancing policies; the baseline signal averages thresholds from 0.0% through 2.5% in 0.1 percentage-point increments. The Calendar signal uses a portfolio reset on the final business day of each month. Signals available at the prior close predict the following trading day's S&P 500 minus 10-year Treasury futures return.

The paper's implementable front-running strategy rescales the Threshold signal by -1/1.5%, uses the signed inverse Calendar signal in the last week of the month, and uses a first-business-day reversal based on the Calendar signal four trading observations earlier.

## Project sample

QuantConnect/LEAN continuous futures:

- ES — S&P 500 E-mini
- ZN — 10-Year U.S. Treasury Note
- daily resolution
- front contract selected by open interest
- backwards-ratio normalization

Project start: 2010-01-01, chosen to match the existing traditional-futures project horizon and avoid inventing a new start date after seeing results.

### Frozen split

- **Paper-era replication/proxy:** 2010-01-01 through 2023-03-17
- **Project holdout:** 2023-03-18 through latest available data, capped at 2026-10-01 for this run

The holdout is out of sample relative to HMM's reported data window and is unopened by this IPF project before R1. It is not claimed to be globally literature-blind: other researchers/commentators may have examined post-2023 month-end/rebalancing patterns.

## Signal construction

Target equity weight = 60%; bond weight = 40%.

After each day's ES and ZN returns, update the simulated equity weight.

### Threshold

For each delta in {0.0%, 0.1%, ..., 2.5%}:

1. Record the resulting equity-weight deviation from 60% as that policy's signal.
2. If the absolute deviation is at least delta, reset the simulated portfolio to 60/40 for the next trading day.
3. Otherwise allow the weight to drift.

Average the 26 policy signals to form the baseline Threshold signal.

### Calendar

Record the simulated equity-weight deviation each day. Reset the portfolio to 60/40 after the final observed trading day of each month for the next trading day.

### Predictive return

Next-trading-day spread return = ES return minus ZN return.

HMM prediction: positive rebalancing signals (equities overweight) forecast a negative next-day ES-minus-ZN return; negative signals forecast a positive spread return.

## Frozen strategy proxies

### Threshold arm

`threshold_trade = -threshold_signal / 0.015`

### Calendar arm

- during the final five observed trading days of a month: `-sign(calendar_signal)`
- on the first observed trading day of a new month: `sign(calendar_signal.shift(4))`
- otherwise: 0

### Combined

Equal average of Threshold and Calendar strategy weights.

These are research return proxies, not yet a realistic contract-level execution model.

## Frozen control

Generic cross-asset short-term reversal:

- compute trailing 5-trading-day compounded ES-minus-ZN return
- trade the opposite sign for the next trading day

This control is deliberately simple. It asks whether the rebalancing construction adds information beyond ordinary short-horizon equity/bond reversal.

## Required outputs

For paper-era and holdout periods separately:

1. Threshold -> next-day spread: N, slope, heteroskedasticity-robust t-statistic, approximate p-value, correlation.
2. Calendar -> next-day spread during final five trading days: same statistics.
3. Strategy metrics before costs for Threshold, Calendar, Combined, 5-day reversal control, and ES buy-and-hold: N, annualized arithmetic return, annualized volatility, Sharpe, maximum drawdown, hit rate, cumulative compounded return.
4. Holdout calendar-year breakdown for Combined and control.
5. Sanity checks for signal means, standard deviations, and Threshold/Calendar correlation.

## Decision gates

R1 is an existence/mechanism screen, not final strategy approval.

### Fail / deprioritize

Deprioritize mandated rebalancing if, in the project holdout, either:

- the Threshold relationship does not have the predicted negative sign; or
- the Combined strategy has no meaningful advantage over the frozen 5-day reversal control.

A weak Calendar arm alone does not automatically fail the mechanism if Threshold survives, because the two represent different institutional rules.

### Survive to R1.1

Advance only if the holdout shows the predicted mechanism and the rebalancing construction is materially more informative than generic reversal.

R1.1 will then add realistic futures contract selection, rolls, commissions/slippage and risk normalization. Only after that may we test the IPF-specific extension: estimated compulsory rebalancing pressure divided by contemporaneous absorption/liquidity capacity.

## Prohibited before first result

Do not change after observing output:

- sample split
- 60/40 target
- threshold range or step
- 1.5% Threshold rescaling
- final-five-day Calendar window
- four-observation first-day reversal reference
- 5-day reversal-control horizon
- ES/ZN instruments

Any later modification must be labelled a new exploratory or shadow variant, never substituted into R1.
