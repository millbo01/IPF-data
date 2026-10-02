# VIX ETP forced-flow — final practical result

## Status

**Mechanism as a modern standalone late-close trading signal: KILLED under this implementation.**

The research question was whether mechanically predictable daily VIX-ETP rebalancing demand could be reconstructed before the close and used to trade the late equity-index move, with subsequent reversal considered separately.

## Data

### ProShares
Official historical daily AUM/NAV:
- UVXY
- VIXY
- SVXY

Historical leverage correction:
- UVXY: +2.0x before 2018-02-28; +1.5x from 2018-02-28
- SVXY: -1.0x before 2018-02-28; -0.5x from 2018-02-28
- VIXY: +1.0x

### Volatility Shares
Official monthly statements were parsed into month-end net-asset anchors for:
- UVIX (+2x)
- SVIX (-1x)

51 usable monthly anchors were available in the QuantConnect modern-complex run.

## Signal

For each product:

`convexity_scale_i = beta_i * (beta_i - 1) * lagged_AUM_i`

At 15:45 New York:

`predicted_rebalance_i = convexity_scale_i * intraday_VIX_benchmark_return`

For the modern UVIX/SVIX reconstruction, prior official month-end AUM was marked forward using the ETF's subsequent return until the next monthly anchor.

The equity-direction hypothesis was fixed as **opposite signed VIX-futures pressure**.

## Early-history diagnostic

With corrected historical leverage, the ProShares-only chronology suggested a structural change:

- 2012-2017: opposite-pressure extreme-event trade approximately +6.0 bp/event
- 2018: approximately +35.4 bp/event on only 10 extreme observations
- 2019-2021: approximately +2.3 bp/event, unstable
- 2022-2026: approximately -2.3 bp/event

This motivated reconstructing the missing UVIX/SVIX complex rather than immediately killing the mechanism.

## Complete modern-complex result

QuantConnect run:
- Build: 2022-05 through 2023-12
- Holdout: 2024-01 through 2026-07 available data
- Same-date comparison between ProShares-only and complete ProShares + UVIX + SVIX pressure
- No orders; mechanism/economic-information screen only

### ProShares-only
Build extreme events:
- n = 72
- mean late-close trade = -3.694 bp
- median = -4.373 bp
- hit rate = 33.3%

Holdout:
- n = 155
- mean = -4.423 bp
- median = -2.670 bp
- hit rate = 42.6%

### Complete complex
Build extreme events:
- n = 72
- mean = -4.149 bp
- median = -4.869 bp
- hit rate = 31.9%

Holdout:
- n = 164
- mean = -3.287 bp
- median = -1.619 bp
- hit rate = 45.1%

Yearly complete-complex means were negative in 2022, 2023, 2024, 2025 and 2026 through the available endpoint.

## Materiality of the missing products

The UVIX/SVIX addition was economically large:
- median UVIX/SVIX convexity scale / ProShares convexity scale = 1.321
- interquartile range = 0.638 to 2.194
- median UVIX/SVIX share of reconstructed total convexity scale = 56.9%

Therefore the modern failure is **not** explained by UVIX/SVIX being too small to matter. Adding them materially changes the estimated forced-flow complex but does not restore the expected late-equity displacement.

## Reversal leg

The next-morning leg does not rescue the strategy:
- complete-complex holdout mean = -4.312 bp under the pre-specified reversal direction
- hit rate = 51.8%

## Decision

Do not spend further time optimizing this exact VIX-ETP -> late-equity rule.

Retain the historical observation that the relationship was stronger in the earlier leveraged-VIX-product regime, but do not promote it as a current trading strategy.

The key limitation is that the modern historical UVIX/SVIX AUM series is reconstructed from official monthly anchors rather than exact daily provider AUM. That is sufficient for the present stop/go decision because the missing products are shown to be large, and adding their reconstructed pressure does not improve either build or holdout economics.

## Next track

Move to **direct equity leveraged-ETF rebalancing**, where the forced flow acts directly in the same underlying equity index rather than requiring a VIX-futures-to-equity transmission channel.
