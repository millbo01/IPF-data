# VIX ETP forced-flow pipeline v2

## Objective
Build a practical, auditable VIX-ETP forced-flow signal for a small-capital trading system.

The primary object is not a generic volatility indicator. It is mechanically implied issuer rebalancing demand and its size relative to receiving-market capacity.

## Signal stack

For product i on day t:

`rebalance_notional_i ~= beta_i * (beta_i - 1) * AUM_{i,t-1} * benchmark_return_t`

where beta is the stated daily leverage multiple. Aggregate across UVXY, VIXY, SVXY, UVIX and SVIX.

The first practical state variable is:

`pressure_t = aggregate_rebalance_notional_t / receiving_capacity_t`

Receiving capacity should be measured in the relevant VIX-futures close window. Until intraday VX capacity is available, daily front-two VX dollar volume is an explicit provisional denominator, not a final implementation.

## Products
- UVXY +1.5x
- VIXY +1x
- SVXY -0.5x
- UVIX +2x
- SVIX -1x

## Data layers

### A. Prospective daily provider archive
Official public product pages / holdings downloads are collected daily. This is append-only and is the cleanest source for current holdings, AUM/NAV and shares outstanding.

### B. Historical ProShares AUM/NAV backfill
Use the official per-fund ProShares historical NAV CSVs. These files include daily NAV, shares outstanding and assets under management, so UVXY/VIXY/SVXY can be reconstructed directly rather than estimated from market price.

### C. Volatility Shares historical anchor layer
UVIX/SVIX are commodity-pool products, not N-PORT funds. Do **not** use SEC Form N-PORT as their historical holdings source. Use official Volatility Shares monthly account statements plus VS Trust SEC 10-Q/10-K filings as periodic holdings/exposure anchors. Any daily interpolation/reconstruction between anchors must be explicit and quality-flagged.

### D. Market receiving-capacity layer
Ultimately use VX futures price/volume and, where available, intraday near-close volume/depth. ES/SPX outcome data are kept separate from the signal construction.

## First economic panel
One row per trading day, with at least:
- date
- per-product beta
- per-product lagged AUM
- benchmark return known before the trade window
- per-product implied rebalance notional
- aggregate implied VX demand
- capacity denominator
- capacity-normalised pressure
- VX late-close return
- ES late-close return
- ES next-window reversal
- data-quality / provenance flags

## Initial tests
1. Monotonicity: larger signed pressure should align with same-direction late VX displacement.
2. Transmission: pressure should contain incremental information for late ES returns beyond contemporaneous VX return/level and ES recent return.
3. Reversal: unusually large pressure/capacity episodes should show subsequent reversal if the move is temporary forced-flow impact.
4. MAIN interaction: evaluate whether MAIN direction/state improves or attenuates the forced-flow trade, but do not require MAIN for signal construction.
5. LC1 interaction: when intraday capacity data are available, test whether low receiving capacity amplifies displacement.

## Small-account implementation rule
Standalone P&L testing must use a venue/position size appropriate to approximately GBP 2,000. Do not assume CME contract sizing. A signal can graduate as an indicator even if standalone execution is uneconomic.

## Development policy
This is an optimization project, not an academic publication. Parameters may be iterated. However, every material change gets a version tag and walk-forward/out-of-sample comparison so improvements are distinguishable from in-sample fitting.
