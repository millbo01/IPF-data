# IG venue facts for the index morning-fade test — 2026-10-02

## Decision

For a 09:31–10:00 New York trade that is always flat overnight, the preferred IG representation is the **US Tech 100 Daily Funded Bet (DFB)**, not the dated US Tech 100 futures spread bet.

This is an execution choice, not a signal change.

## Current public IG UK specification

Source: IG UK Help Centre, "Spread bet: Indices product details", checked 2026-10-02.

US Tech 100 DFB:
- standard minimum bet: **£1/point**
- available spread: **1 point from 14:30–21:00 London**
- available spread: **2 points in the surrounding non-core period relevant to the US open**
- available spread: **5 points from 22:00–23:00**
- retail margin: **5%**

US Tech 100 futures spread bet:
- standard minimum bet: **£1/point**
- normal spread: **3 points**
- retail margin: **5%**

US 500 DFB comparator:
- standard minimum bet: **£1/point**
- available spread: **0.4 point from 14:30–21:00 London**
- available spread: **0.6 point in the surrounding non-core period relevant to the US open**
- retail margin: **5%**

Public product page:
https://www.ig.com/uk/help-and-support/articles/682128-spread-bet-indices-product-details

## Prior authenticated account-specific evidence

The earlier read-only live IG probe is archived on branch `research/main-ig-translation` in:

`research/main_ig_translation/LIVE_PROBE_2026-10-01.md`

That probe found:
- the mapped NQ / US Tech 100 market was tradeable;
- `dealingRules.minDealSize.value = 0.01`;
- the unit was `POINTS`;
- first-band index margin was 5%.

However, that work deliberately selected dated futures/forward instruments and rejected DFB/no-expiry candidates. Therefore it **does not prove that the US Tech 100 DFB also has an account-specific £0.01/point minimum**.

Until the DFB EPIC is queried directly, treat:
- £1/point as the confirmed public executable minimum;
- £0.01/point as a conditional account-specific scenario only.

## Representative small-account scale

For orientation only, using a Nasdaq-100 level of about **30,501.56** on 2026-10-01:

- 1 index point is about **0.328 bp**;
- a 1-point full spread therefore costs about **0.328 bp**;
- at £1/point and 5% margin, margin is about **£1,525**, or **76.3% of a £2,000 account**;
- at £0.01/point, the same margin is about **£15.25**, or **0.76% of a £2,000 account**.

These are scale illustrations, not historical backtest results. The actual experiment uses each trade's historical index level and historical London/New York clock relationship.

## Preliminary implication

At the current index level, the public 1-point DFB spread is small in basis-point terms relative to the previously observed P90/P95 gross morning means. The potentially binding small-account issue is therefore **stake granularity and margin/risk**, not obviously the headline spread itself.

That is only a preliminary venue diagnosis. Full trade-level drawdown, chronology, MAE and net expectancy must be computed before any deployment conclusion.
