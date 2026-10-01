# ============================================================
# LC1 DATA-ACCESS DIAGNOSTIC
#
# Purpose only:
#   Verify that QuantConnect returns ES futures tick trades + quotes
#   with usable bid/ask prices and sizes before LC1-A is implemented.
#
# This script MUST NOT calculate forward returns or test the LC1
# pressure/capacity relationship.
# ============================================================

from AlgorithmImports import *
from QuantConnect.Research import QuantBook
from datetime import datetime
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Frozen diagnostic interval
# ------------------------------------------------------------
# One hour during the US cash session on the final full day used by R1.
# If your QC entitlement cannot return this interval, send the error/output
# back unchanged. Do not substitute another date before we review it.

START = datetime(2026, 9, 29, 10, 0, 0)
END   = datetime(2026, 9, 29, 11, 0, 0)

qb = QuantBook()

es = qb.add_future(
    Futures.Indices.SP_500_E_MINI,
    Resolution.TICK,
    data_mapping_mode=DataMappingMode.OPEN_INTEREST,
    data_normalization_mode=DataNormalizationMode.RAW,
    contract_depth_offset=0,
)

print("LC1 tick diagnostic")
print("Canonical symbol:", es.symbol)
print("Requested interval:", START, "to", END)

# QuantConnect documents tick history on both individual and continuous
# futures symbols. DataFrame tick history includes fields such as
# askprice, asksize, bidprice, bidsize, lastprice and quantity.
h = qb.history(es.symbol, START, END, Resolution.TICK)

if h is None:
    print("HISTORY IS NONE")
    raise RuntimeError("QC returned None for ES tick history")

print("History object type:", type(h))
print("Rows returned:", len(h))

if len(h) == 0:
    raise RuntimeError(
        "QC returned zero ES tick rows for the frozen interval. "
        "Return this output unchanged for diagnosis."
    )

print("Index names:", list(h.index.names) if hasattr(h.index, "names") else None)
print("Columns:", list(h.columns))
print("Dtypes:")
print(h.dtypes)

# Reset index so we can inspect timestamps/expiry/symbol fields regardless
# of the exact MultiIndex layout returned by the current QC Research build.
df = h.reset_index().copy()

# Lower-case lookup while preserving original QC column names.
lookup = {str(c).lower(): c for c in df.columns}

print("\nReset-index columns:", list(df.columns))

expected = [
    "time",
    "expiry",
    "symbol",
    "askprice",
    "asksize",
    "bidprice",
    "bidsize",
    "lastprice",
    "quantity",
]

print("\nExpected-field presence:")
for name in expected:
    print(f"  {name:12s}: {name in lookup}")


def numeric(name):
    col = lookup.get(name)
    if col is None:
        return pd.Series(np.nan, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce")

askprice = numeric("askprice")
asksize = numeric("asksize")
bidprice = numeric("bidprice")
bidsize = numeric("bidsize")
lastprice = numeric("lastprice")
quantity = numeric("quantity")

# Per QC documentation, trade ticks have non-zero trade price/quantity and
# quote ticks have non-zero bid or ask price/size fields. We report both
# broad and stricter counts to expose any data-shape quirks.
trade_like = lastprice.fillna(0).ne(0) | quantity.fillna(0).ne(0)
quote_like = (
    askprice.fillna(0).ne(0)
    | bidprice.fillna(0).ne(0)
    | asksize.fillna(0).ne(0)
    | bidsize.fillna(0).ne(0)
)

strict_trade = quantity.fillna(0).gt(0) & lastprice.fillna(0).gt(0)
strict_quote = (
    (askprice.fillna(0).gt(0) & asksize.fillna(0).gt(0))
    | (bidprice.fillna(0).gt(0) & bidsize.fillna(0).gt(0))
)

print("\nTick-type proxy counts:")
print("  trade-like rows:", int(trade_like.sum()))
print("  strict trade rows:", int(strict_trade.sum()))
print("  quote-like rows:", int(quote_like.sum()))
print("  strict quote rows:", int(strict_quote.sum()))
print("  rows containing both trade-like and quote-like fields:", int((trade_like & quote_like).sum()))

print("\nUsable quote-field counts:")
print("  bidprice > 0:", int(bidprice.fillna(0).gt(0).sum()))
print("  bidsize  > 0:", int(bidsize.fillna(0).gt(0).sum()))
print("  askprice > 0:", int(askprice.fillna(0).gt(0).sum()))
print("  asksize  > 0:", int(asksize.fillna(0).gt(0).sum()))
print("  both bid+ask price > 0:", int((bidprice.fillna(0).gt(0) & askprice.fillna(0).gt(0)).sum()))
print("  both bid+ask size  > 0:", int((bidsize.fillna(0).gt(0) & asksize.fillna(0).gt(0)).sum()))

# Timestamp / contract coverage.
time_col = lookup.get("time")
expiry_col = lookup.get("expiry")
symbol_col = lookup.get("symbol")

if time_col is not None:
    times = pd.to_datetime(df[time_col], errors="coerce").dropna()
    print("\nTime coverage:")
    print("  first:", times.min() if len(times) else None)
    print("  last: ", times.max() if len(times) else None)
    if len(times) > 1:
        diffs = times.sort_values().diff().dropna().dt.total_seconds()
        print("  median inter-row seconds:", float(diffs.median()))
        print("  95th pct inter-row seconds:", float(diffs.quantile(0.95)))

if expiry_col is not None:
    expiries = pd.to_datetime(df[expiry_col], errors="coerce").dropna().unique()
    print("\nUnique expiries in interval:", len(expiries))
    print("Expiries:", sorted([str(pd.Timestamp(x)) for x in expiries])[:10])

if symbol_col is not None:
    symbols = df[symbol_col].astype(str).dropna().unique()
    print("Unique mapped symbols in interval:", len(symbols))
    print("Symbols:", list(symbols)[:10])

# Basic non-outcome descriptive checks needed to design the capacity proxy.
q = pd.DataFrame({
    "bidprice": bidprice,
    "bidsize": bidsize,
    "askprice": askprice,
    "asksize": asksize,
})
q = q[quote_like].copy()

if len(q):
    print("\nQuote-size descriptive values (diagnostic only):")
    for side in ["bidsize", "asksize"]:
        s = q[side]
        s = s[s > 0].dropna()
        if len(s):
            print(
                f"  {side}: n={len(s)}, median={s.median():.4f}, "
                f"p10={s.quantile(0.10):.4f}, p90={s.quantile(0.90):.4f}, "
                f"max={s.max():.4f}"
            )

    both = q[(q["bidprice"] > 0) & (q["askprice"] > 0)]
    if len(both):
        spread = both["askprice"] - both["bidprice"]
        print(
            "  spread: n=", len(spread),
            "median=", float(spread.median()),
            "p90=", float(spread.quantile(0.90)),
        )

print("\nFirst 8 rows:")
print(df.head(8).to_string(index=False))

print("\nFirst 8 strict trade rows:")
print(df.loc[strict_trade].head(8).to_string(index=False))

print("\nFirst 8 strict quote rows:")
print(df.loc[strict_quote].head(8).to_string(index=False))

# Explicit diagnostic gates.
required_columns = all(name in lookup for name in [
    "askprice", "asksize", "bidprice", "bidsize", "lastprice", "quantity"
])

quote_sizes_usable = (
    bidsize.fillna(0).gt(0).sum() >= 100
    and asksize.fillna(0).gt(0).sum() >= 100
)

trades_usable = strict_trade.sum() >= 100

print("\n" + "=" * 72)
print("DIAGNOSTIC GATES")
print("=" * 72)
print("Required tick columns present:", bool(required_columns))
print("At least 100 strict trade rows:", bool(trades_usable))
print("At least 100 non-zero bid AND ask size observations:", bool(quote_sizes_usable))
print("LC1-A BASIC DATA GATE:", "PASS" if (required_columns and trades_usable and quote_sizes_usable) else "FAIL")
print("\nReturn the complete output before changing the date or code.")
