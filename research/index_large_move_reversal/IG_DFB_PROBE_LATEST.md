# IG DFB live-account probe

Checked UTC: 2026-10-02T08:26:23.098038+00:00

Read-only market/account metadata probe. No dealing/order endpoint was called.

Account type: SPREADBET
Account currency: GBP

## Selected candidates

| Family | Name | EPIC | Expiry | Status | Bid | Offer | Spread pts | Min deal | Unit | First margin % |
|---|---|---|---|---|---:|---:|---:|---:|---|---:|
| NDX | US Tech 100 | IX.D.NASDAQ.CASH.IP | DFB | TRADEABLE | 30725.9 | 30728.1 | 2.1999999999970896 | 0.01 | POINTS | 5.0 |
| SPX | US 500 | IX.D.SPTRD.DAILY.IP | DFB | TRADEABLE | 7698.88 | 7699.58 | 0.6999999999998181 | 0.01 | POINTS | 5.0 |

## Gate interpretation

- The NDX row must be the US Tech 100 DFB (expiry DFB) to settle the implementation question.
- If min deal is 0.01 POINTS on that DFB, use the small-stake scenario as executable.
- If min deal is 1 POINTS (or larger), the public-minimum scenario remains the executable case.
- The full CSV retains nearby index candidates for auditability.
