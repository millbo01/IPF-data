# VIX ETP collector patch

Follow-up parser fixes after the first production run exposed provider-format drift.

- ProShares: locate the actual holdings CSV header after metadata/preamble rows.
- Volatility Shares: prefer official downloadable holdings endpoints, with page parsing only as fallback.
- Workflow: install Excel parsers (`openpyxl`, `xlrd`).
- Partial provider/product success is archived rather than discarding the whole day.
- Historical NAV was removed from the daily critical path; it is not required for prospective collection.

This note exists only to make the follow-up patch explicit in the PR history.
