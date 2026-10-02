# Equity leveraged-ETF forced rebalance — research specification

## Objective

Test a direct forced-flow mechanism that is mechanically stronger and simpler than the VIX-ETP cross-market channel.

Leveraged and inverse equity ETFs target fixed daily multiples of their benchmark. After an intraday index move they must rebalance exposure toward the direction of that move near the close. The first practical question is whether the predictable aggregate rebalance notional is large enough relative to receiving-market capacity to produce a repeatable late-day continuation effect.

## Products

### S&P 500 complex
- UPRO: +3x
- SPXU: -3x
- SSO: +2x
- SDS: -2x

### Nasdaq-100 complex
- TQQQ: +3x
- SQQQ: -3x
- QLD: +2x
- QID: -2x

All eight are ProShares products with public historical NAV/AUM downloads.

## Mechanical signal

For product i with daily leverage beta:

`convexity_scale_i = beta_i * (beta_i - 1) * AUM_{i,t-1}`

At a decision time before the close:

`predicted_rebalance_i = convexity_scale_i * benchmark_intraday_return_t`

Aggregate separately within S&P and Nasdaq complexes.

Unlike the VIX-ETP experiment, this is a direct same-market mechanism. The expected late-day equity direction is **the same direction as predicted rebalance pressure**.

## Capacity

The first capacity proxy is pre-decision dollar turnover in the traded benchmark proxy over the preceding 15 minutes:

- SPY for S&P
- QQQ for Nasdaq-100

Define:

`capacity_normalized_pressure = predicted_rebalance_usd / prior_15m_proxy_dollar_volume`

This is a practical first-order receiving-capacity measure, not a claim that SPY/QQQ is the only execution venue. If the signal survives, later work can replace this with futures/auction capacity.

## Timing

Initial screen:
- benchmark return observed from previous close to 15:45 New York
- capacity window: 15:30 to 15:45
- trade observation begins 15:45
- primary late-close outcome: 15:45 to 16:00
- secondary reversal outcome: close to next trading day 10:00

No post-close information enters the same-day signal.

## Tests

For SPX and Nasdaq separately:

1. Raw predicted rebalance pressure versus 15:45-close return.
2. Capacity-normalized pressure versus 15:45-close return.
3. Extreme-pressure event trade in the mechanically implied same direction.
4. Subsequent close-to-next-10:00 reversal.
5. Stability by calendar subperiod and year.

The raw and capacity-normalized versions are both reported. The capacity version is the IPF-preferred signal if it improves stability without simply cherry-picking a threshold.

## Economic intent

The desired production form is sparse:
- trade only on unusually large pressure/capacity days;
- hold minutes to hours, not daily portfolio rebalancing;
- execute through a small-account venue such as an index spread bet/CFD if costs are viable.

## Development rule

This is a practical optimization project. Iteration is allowed, but each material change is versioned and chronological stability is reported. A weak or unstable first screen should not be rescued by adding unrelated technical indicators.
