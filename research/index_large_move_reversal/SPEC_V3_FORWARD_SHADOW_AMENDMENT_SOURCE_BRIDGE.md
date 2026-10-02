# V3 forward shadow amendment — provisional current-day source bridge

Date frozen: 2026-10-02

## Problem

QuantConnect Research on the Free plan exposes current historical minute data later than required for same-morning 09:31 New York shadow capture. On 2026-10-02 before the US open, the latest Research data were through 2026-09-30 16:00 New York.

The formal V3 signal definition and QuantConnect data source remain unchanged.

## Bridge rule

When QuantConnect Research has not yet published the immediately preceding US session:

1. Export from QuantConnect Research the authoritative rolling state through the latest available completed session:
   - previous regular-session close;
   - the last 252 prior 15:45-return observations;
   - their mean and sample standard deviation.
2. Obtain only the missing most-recent QQQ intraday observations from a free external recent-minute feed:
   - 15:45 New York price;
   - 16:00 New York close when available.
3. Compute a **provisional** z-score using the frozen QuantConnect rolling state.
4. If provisional |z| >= P90 = 1.7796, arm the read-only IG quote capture for the following morning.
5. The captured event is not admitted to the formal V3 event count until QuantConnect later exposes that signal date and independently confirms the frozen P90 trigger.
6. If QuantConnect later rejects a provisional trigger, keep the raw IG capture as a source-bridge false positive and exclude it from formal V3 performance.
7. If the provisional bridge says NO_SIGNAL but later QuantConnect shows P90, record the formal event as missed due to data-latency/source-bridge failure. Do not backfill or silently drop it.

## No model change

This amendment does not alter:
- QQQ return definition;
- 15:45 timestamp;
- prior-only 252-session rolling z-score;
- P90/P95 thresholds;
- fade direction;
- 09:31 entry;
- 10:00 exit;
- IG instrument;
- sizing;
- margin;
- V3 minimum sample or pass/fail criteria.

The external source is an operational capture trigger only. QuantConnect remains the authoritative source for formal V3 inclusion.
