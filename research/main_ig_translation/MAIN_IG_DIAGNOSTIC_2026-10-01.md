# MAIN -> IG diagnostic decomposition — 2026-10-01

## Purpose
Identify where the validated MAIN futures edge is lost when translated to a GBP 2,000 IG implementation.

QuantConnect run: Algorithm Id `2ea501702af7a8009a98c0e63addd87c`, LEAN 2.5.0.0.18149.

## Unrounded research books

### Original 22
- MAIN: build Sharpe 0.956, holdout Sharpe 0.906; holdout annualised return 9.92%, vol 10.94%.
- T1: holdout Sharpe 0.622.
- Forced: holdout Sharpe 0.548.
- Dip: holdout Sharpe 0.387.

### Expanded 36
- MAIN: build Sharpe 0.730, holdout Sharpe 0.601; holdout annualised return 5.13%, vol 8.54%.
- T1: holdout Sharpe 0.450.
- Forced: holdout Sharpe 0.163.
- Dip: holdout Sharpe 0.440.

The 36-market expansion weakens MAIN materially, especially the Forced book.

## Original 22: exact / rounding / costs

At 10% risk:
- exact fractional, zero cost: holdout Sharpe 1.115, annualised return 12.03%, max DD -11.83%.
- GBP0.01-rounded, zero cost: holdout Sharpe 1.197, annualised return 12.64%, max DD -11.77%; 13.74% of non-zero desired targets round to zero.
- GBP0.01-rounded with observed IG spreads: account is destroyed; daily execution holdout Sharpe -4.957, signal-only -4.919, 20% band -4.923.

At 20% risk:
- zero-cost versions remain strong (holdout Sharpe about 1.12, annualised return about 24%), but max margin rises to roughly 105% and observed IG spreads still destroy the account before/through holdout.

At 30% risk:
- zero-cost versions remain strong, but margin reaches roughly 158%, while spread-cost versions are already effectively dead before holdout.

## Expanded 36
At 10% risk:
- exact fractional, zero cost: holdout Sharpe 0.792, return 6.71%.
- GBP0.01-rounded, zero cost: holdout Sharpe 0.882, return 6.52%.
- observed IG spreads destroy the book across daily, signal-only and 20% band execution.

The same qualitative result persists at 20% and 30% risk.

## Diagnostic conclusion
1. MAIN itself remains profitable in the research representation.
2. GBP0.01 stake rounding is not the core failure: zero-cost rounded implementations remain profitable.
3. Expanding from 22 to 36 weakens the underlying signal, particularly Forced.
4. The dominant GBP2k IG failure is transaction-cost / minimum-stake economics. Once spreads start eroding equity, the fixed GBP0.01 stake floor creates a nonlinear death spiral as the account shrinks.
5. Higher risk does not rescue the observed-spread implementation and quickly collides with margin limits.

## Portfolio implication
For future use of MAIN, retain the original 22 as the stronger research universe unless a new independent expansion study says otherwise. MAIN remains useful as a directional/state input, but broad continuous IG expression on approximately GBP2k is not economically viable under the tested spread assumptions.
