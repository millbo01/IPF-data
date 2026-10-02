# O1 — Options dealer gamma / forced hedging: feasibility gate

Status: **FROZEN BEFORE FIRST QC FEASIBILITY RUN**

Date frozen: 2026-10-02

## Purpose

Determine whether the current QuantConnect Free-tier Research environment exposes enough historical SPXW index-option data to support a defensible later test of dealer-gamma / forced-hedging hypotheses.

This is a **data-access diagnostic only**. It does not test returns or any trading outcome.

## Fixed probe dates

Two ordinary US trading sessions are used:

- 2025-11-05 — older probe, roughly eleven months before the feasibility run
- 2026-09-24 — recent probe

The dates are fixed before viewing data-access results.

## Required data

For each date, request the SPXW weekly index-option chain and verify:

1. non-empty chain;
2. same-day-expiry (0DTE) contracts are present;
3. fields needed for a later exposure proxy are present for 0DTE contracts:
   - strike
   - option right
   - open interest
   - delta
   - gamma
   - implied volatility
   - volume;
4. at least one 0DTE contract has usable open interest and gamma;
5. after selecting the most actively traded 0DTE contract, minute history can be retrieved through the regular session.

No underlying return or predictive outcome is calculated.

## Contract selection for the minute-data diagnostic

Within the 0DTE chain:
- select the contract with the highest reported volume;
- break ties by higher open interest.

This selection is only to maximize the chance of observing minute history. It is not a proposed trading rule.

## Pass gate

O1 data feasibility **passes** only if both fixed dates satisfy all of the following:

- non-empty SPXW chain;
- at least one 0DTE contract;
- non-null open-interest and gamma observations exist among 0DTE contracts;
- the selected 0DTE contract returns at least 100 minute history rows during 09:30–16:01 New York.

If either date fails, record the exact failure. Do not change probe dates to find a working example.

## What passing does NOT mean

A pass does not establish that dealer gamma is identifiable.

Before any outcome test, O1 still requires a separately frozen specification that addresses the central identification problem: unsigned open interest and gross volume do not reveal whether dealers are net long or short gamma.

No assumption such as “all calls are dealer short / all puts are dealer short” may be silently adopted.

## Next step if passed

Only after this feasibility gate passes:
1. literature-map defensible exposure-sign methods;
2. freeze an ex-ante gamma-pressure proxy;
3. define a same-drift/simple-price control;
4. freeze build/holdout split;
5. define an economic kill rule and £2,000 IG translation;
6. then run the first outcome test.
