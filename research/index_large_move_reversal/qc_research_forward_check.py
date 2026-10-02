# QuantConnect Research forward signal checker
# Frozen V3 NDX/QQQ morning-fade signal only. No orders.
# Run in QuantConnect Research after the US regular close.
#
# Output:
# FORWARD_CHECK,NO_SIGNAL,...
# or
# FORWARD_CHECK,P90_TRIGGER,...,P95=yes/no,...

from AlgorithmImports import *
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

P90 = 1.7796
P95 = 2.3646

qb = QuantBook()
qb.set_time_zone(TimeZones.NEW_YORK)
qqq = qb.add_equity("QQQ", Resolution.MINUTE).symbol

end = datetime.utcnow()
start = end - timedelta(days=600)

h = qb.history(qqq, start, end, Resolution.MINUTE)

def normalize_history(hist):
    if hist is None or len(hist) == 0:
        return pd.DataFrame(columns=["time", "close"])
    df = hist.copy().reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    if "time" not in df.columns:
        candidates = [c for c in df.columns if "time" in c or "date" in c]
        if not candidates:
            raise RuntimeError(f"Could not identify time column. Columns={list(df.columns)}")
        df = df.rename(columns={candidates[0]: "time"})
    if "close" not in df.columns:
        raise RuntimeError(f"Could not identify close column. Columns={list(df.columns)}")
    df["time"] = pd.to_datetime(df["time"])
    try:
        if df["time"].dt.tz is not None:
            df["time"] = df["time"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    except Exception:
        pass
    return df[["time", "close"]].sort_values("time").reset_index(drop=True)

q = normalize_history(h)
if q.empty:
    raise RuntimeError("FORWARD_CHECK,ERROR,no_history")

print(f"QC_RESEARCH_ACCESS,rows={len(q)},max_time={q['time'].max()}")

q["date"] = q["time"].dt.normalize()

q1545 = (
    q[(q["time"].dt.hour == 15) & (q["time"].dt.minute == 45)]
    [["date", "close"]]
    .drop_duplicates("date", keep="last")
    .rename(columns={"close": "px1545"})
)
q1600 = (
    q[(q["time"].dt.hour == 16) & (q["time"].dt.minute == 0)]
    [["date", "close"]]
    .drop_duplicates("date", keep="last")
    .rename(columns={"close": "close1600"})
)

daily = q1545.merge(q1600, on="date", how="inner").sort_values("date").reset_index(drop=True)

if len(daily) < 61:
    raise RuntimeError(f"FORWARD_CHECK,ERROR,insufficient_sessions={len(daily)}")

daily["prev_close"] = daily["close1600"].shift(1)
daily["signal_return"] = daily["px1545"] / daily["prev_close"] - 1.0

s = daily["signal_return"]
mu = s.shift(1).rolling(252, min_periods=60).mean()
sd = s.shift(1).rolling(252, min_periods=60).std()
daily["z"] = (s - mu) / sd

valid = daily.dropna(subset=["z"]).copy()
if valid.empty:
    raise RuntimeError("FORWARD_CHECK,ERROR,no_valid_z")

r = valid.iloc[-1]
z = float(r["z"])
abs_z = abs(z)
ret = float(r["signal_return"])

status = "P90_TRIGGER" if abs_z >= P90 else "NO_SIGNAL"
signal = "UP" if ret > 0 else "DOWN"
fade = "SELL" if ret > 0 else "BUY"
p95 = "yes" if abs_z >= P95 else "no"

print(
    f"FORWARD_CHECK,{status},"
    f"signal_date={r['date'].date()},"
    f"ret_bp={ret*10000:.3f},"
    f"z={z:.6f},abs_z={abs_z:.6f},"
    f"signal={signal},fade={fade},P95={p95}"
)
