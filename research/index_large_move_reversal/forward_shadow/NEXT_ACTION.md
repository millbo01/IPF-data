# NEXT ACTION — V3 forward shadow

Updated: 2026-10-02

## Tonight after the US close

Run the current V3 source-bridge check:

1. QuantConnect Research: run the QC bridge-state script and copy the full `QC_BRIDGE_BUNDLE,...` line.
2. Google Colab: run the provisional bridge script, paste that bundle, and return:
   - `BRIDGE_FEED_CHECK,...`
   - `BRIDGE_CHECK,...`

If `BRIDGE_CHECK` says `PROVISIONAL_NO_SIGNAL`, stop.

If it says `PROVISIONAL_P90_TRIGGER`, arm the next-session read-only IG capture in GitHub before the 09:31 New York window.

Formal V3 inclusion remains QuantConnect-authoritative; provisional bridge results are confirmed later when QC publishes the session.

## Current state

- 2026-09-30: formal QC NO_SIGNAL, z = +0.493675.
- 2026-10-01: provisional bridge NO_SIGNAL, z = +0.266705.
- Feed overlap validation: six matched sessions, maximum return discrepancy 0.238 bp.
