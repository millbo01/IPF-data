# Next user action

Updated: 2026-10-02

## Tonight after the US close

After approximately 21:00 UK time:

1. Run the QuantConnect Research bridge-state script.
2. Run the Google Colab provisional-bridge script using the QC_BRIDGE_BUNDLE output.
3. Return the two final lines:
   - BRIDGE_FEED_CHECK,...
   - BRIDGE_CHECK,...

Purpose: determine whether the 2026-10-02 QQQ move creates a frozen P90 trigger for the next US session.

If BRIDGE_CHECK says PROVISIONAL_NO_SIGNAL, stop.

If BRIDGE_CHECK says PROVISIONAL_P90_TRIGGER, arm the existing read-only IG capture for the following session.

Do not alter thresholds, timestamps, signal definition, or data-source bridge rules.
