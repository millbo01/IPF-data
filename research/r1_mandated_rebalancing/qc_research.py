# ============================================================
# IPF-R1: MANDATED REBALANCING
# Frozen first-pass mechanism / post-paper holdout test
#
# Run in a QuantConnect Research notebook.
# Do not tune parameters before returning the first output.
# See SPEC.md in this directory for the frozen design.
# ============================================================

from AlgorithmImports import *
from QuantConnect.Research import QuantBook

import math
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 0. FROZEN PARAMETERS
# ------------------------------------------------------------

START = pd.Timestamp("2010-01-01")
PAPER_END = pd.Timestamp("2023-03-17")
END = pd.Timestamp("2026-10-01")

TARGET_EQUITY = 0.60
TARGET_BOND = 0.40

# HMM baseline: 0.0%, 0.1%, ... 2.5%
THRESHOLDS = np.arange(0.000, 0.0251, 0.001)

# HMM strategy scaling
THRESHOLD_SCALE = 0.015

TRADING_DAYS = 252


# ------------------------------------------------------------
# 1. LOAD CONTINUOUS FUTURES
# ------------------------------------------------------------

qb = QuantBook()

es = qb.add_future(
    Futures.Indices.SP_500_E_MINI,
    Resolution.DAILY,
    data_mapping_mode=DataMappingMode.OPEN_INTEREST,
    data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
    contract_depth_offset=0,
)

zn = qb.add_future(
    Futures.Financials.Y_10_TREASURY_NOTE,
    Resolution.DAILY,
    data_mapping_mode=DataMappingMode.OPEN_INTEREST,
    data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
    contract_depth_offset=0,
)


def get_continuous_close(future, start, end):
    """Return one continuous-future close per trading date."""
    h = qb.history(
        future.symbol,
        start=start.to_pydatetime(),
        end=end.to_pydatetime(),
        resolution=Resolution.DAILY,
        fill_forward=False,
        extended_market_hours=True,
        data_mapping_mode=DataMappingMode.OPEN_INTEREST,
        data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
        contract_depth_offset=0,
    )

    if h is None or len(h) == 0:
        raise RuntimeError(f"No history returned for {future.symbol}")

    dfh = h.reset_index()
    lower = {str(c).lower(): c for c in dfh.columns}

    time_col = None
    for candidate in ("time", "endtime"):
        if candidate in lower:
            time_col = lower[candidate]
            break

    if time_col is None:
        raise RuntimeError(
            f"Couldn't identify time column for {future.symbol}. "
            f"Columns returned: {list(dfh.columns)}"
        )

    close_col = lower.get("close")
    if close_col is None:
        raise RuntimeError(
            f"Couldn't identify close column for {future.symbol}. "
            f"Columns returned: {list(dfh.columns)}"
        )

    out = dfh[[time_col, close_col]].copy()
    out.columns = ["date", "close"]

    dt = pd.to_datetime(out["date"])
    try:
        dt = dt.dt.tz_localize(None)
    except TypeError:
        # Already timezone-naive on some QC builds.
        pass

    # Align ES and ZN by trading date even if daily-bar timestamps differ.
    out["date"] = dt.dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")

    out = (
        out.dropna(subset=["date", "close"])
        .drop_duplicates("date", keep="last")
        .set_index("date")
        .sort_index()
    )

    return out["close"].astype(float)


print("Loading ES...")
es_close = get_continuous_close(es, START, END)

print("Loading ZN...")
zn_close = get_continuous_close(zn, START, END)

prices = pd.concat(
    [es_close.rename("ES"), zn_close.rename("ZN")],
    axis=1,
    join="inner",
).dropna()

if len(prices) < 1000:
    raise RuntimeError(
        f"Only {len(prices)} common ES/ZN daily observations returned. "
        "Do not continue; return this message for diagnosis."
    )

print(
    f"Common daily observations: {len(prices):,} "
    f"({prices.index.min().date()} to {prices.index.max().date()})"
)


# ------------------------------------------------------------
# 2. RETURNS
# ------------------------------------------------------------

rets = prices.pct_change()

df = pd.DataFrame(index=prices.index)
df["ES"] = prices["ES"]
df["ZN"] = prices["ZN"]
df["r_es"] = rets["ES"]
df["r_zn"] = rets["ZN"]
df["spread_return"] = df["r_es"] - df["r_zn"]


# ------------------------------------------------------------
# 3. 60/40 PORTFOLIO WEIGHT DYNAMICS
# ------------------------------------------------------------

def update_equity_weight(equity_weight, r_e, r_b):
    bond_weight = 1.0 - equity_weight
    equity_value = equity_weight * (1.0 + r_e)
    bond_value = bond_weight * (1.0 + r_b)
    total = equity_value + bond_value

    if not np.isfinite(total) or total <= 0:
        return np.nan

    return equity_value / total


# ------------------------------------------------------------
# 4. THRESHOLD SIGNAL
# ------------------------------------------------------------

threshold_series = {}
threshold_rebalances = {}

for delta in THRESHOLDS:
    current_weight = TARGET_EQUITY
    signal = []
    rebalance_count = 0

    for _, row in df.iterrows():
        r_e = row["r_es"]
        r_b = row["r_zn"]

        if not np.isfinite(r_e) or not np.isfinite(r_b):
            signal.append(np.nan)
            continue

        new_weight = update_equity_weight(current_weight, r_e, r_b)
        deviation = new_weight - TARGET_EQUITY
        signal.append(deviation)

        # Record the end-of-day drift first; then reset for the next day
        # when the threshold policy has been triggered.
        if abs(deviation) >= delta:
            current_weight = TARGET_EQUITY
            rebalance_count += 1
        else:
            current_weight = new_weight

    threshold_series[float(delta)] = pd.Series(signal, index=df.index)
    threshold_rebalances[float(delta)] = rebalance_count

threshold_matrix = pd.DataFrame(threshold_series)
df["threshold"] = threshold_matrix.mean(axis=1)


# ------------------------------------------------------------
# 5. CALENDAR SIGNAL
# ------------------------------------------------------------

current_weight = TARGET_EQUITY
calendar_signal = []
dates = list(df.index)

for i, (_, row) in enumerate(df.iterrows()):
    r_e = row["r_es"]
    r_b = row["r_zn"]

    if not np.isfinite(r_e) or not np.isfinite(r_b):
        calendar_signal.append(np.nan)
        continue

    new_weight = update_equity_weight(current_weight, r_e, r_b)
    deviation = new_weight - TARGET_EQUITY
    calendar_signal.append(deviation)

    if i == len(dates) - 1:
        month_end = True
    else:
        month_end = dates[i + 1].to_period("M") != dates[i].to_period("M")

    if month_end:
        current_weight = TARGET_EQUITY
    else:
        current_weight = new_weight


df["calendar"] = pd.Series(calendar_signal, index=df.index)


# ------------------------------------------------------------
# 6. MONTH-POSITION FLAGS
# ------------------------------------------------------------

periods = pd.Series(df.index.to_period("M"), index=df.index)

days_to_month_end = periods.groupby(periods).transform(
    lambda x: np.arange(len(x) - 1, -1, -1)
)

df["days_to_month_end"] = days_to_month_end.astype(int)
df["last_5_days"] = df["days_to_month_end"] <= 4
df["first_day_month"] = periods.ne(periods.shift(1))


# ------------------------------------------------------------
# 7. NO-LOOKAHEAD FORWARD RETURN TEST
# ------------------------------------------------------------

# Signal after today's completed bar predicts the next trading day.
df["spread_fwd"] = df["spread_return"].shift(-1)
df["es_fwd"] = df["r_es"].shift(-1)

# Positive Threshold = equities overweight -> expected negative ES-ZN.
df["threshold_trade"] = -df["threshold"] / THRESHOLD_SCALE

# Paper-style modified Calendar arm.
df["calendar_trade"] = 0.0

df.loc[df["last_5_days"], "calendar_trade"] = -np.sign(
    df.loc[df["last_5_days"], "calendar"]
)

calendar_lag4 = df["calendar"].shift(4)
first_day = df["first_day_month"]
df.loc[first_day, "calendar_trade"] = np.sign(calendar_lag4.loc[first_day])

# Equal average of the modified signals.
df["combo_weight"] = (
    df["threshold_trade"] + df["calendar_trade"]
) / 2.0


# ------------------------------------------------------------
# 8. RESEARCH STRATEGY RETURNS — BEFORE COSTS
# ------------------------------------------------------------

df["ret_threshold"] = df["threshold_trade"] * df["spread_fwd"]
df["ret_calendar"] = df["calendar_trade"] * df["spread_fwd"]
df["ret_combo"] = df["combo_weight"] * df["spread_fwd"]


# ------------------------------------------------------------
# 9. FROZEN GENERIC REVERSAL CONTROL
# ------------------------------------------------------------

# Five-day compounded spread proxy.  Because ES-ZN is a difference
# rather than a directly compounded asset, compounding 1+spread is an
# approximation used only to set the sign of the control.
df["spread_5d"] = (
    (1.0 + df["spread_return"])
    .rolling(5)
    .apply(np.prod, raw=True)
    - 1.0
)

df["control_weight"] = -np.sign(df["spread_5d"])
df["ret_control"] = df["control_weight"] * df["spread_fwd"]

# Passive comparison over the same next-day alignment.
df["ret_es_buyhold"] = df["es_fwd"]


# ------------------------------------------------------------
# 10. METRICS
# ------------------------------------------------------------

def max_drawdown(r):
    r = pd.Series(r).dropna()
    if len(r) == 0:
        return np.nan

    wealth = (1.0 + r).cumprod()
    peak = wealth.cummax()
    return (wealth / peak - 1.0).min()


def metrics(r):
    r = pd.Series(r).replace([np.inf, -np.inf], np.nan).dropna()

    if len(r) < 2:
        return {
            "N": len(r),
            "AnnRet": np.nan,
            "AnnVol": np.nan,
            "Sharpe": np.nan,
            "MaxDD": np.nan,
            "Hit": np.nan,
            "CumRet": np.nan,
        }

    mean = r.mean()
    vol = r.std(ddof=1)
    ann_ret = mean * TRADING_DAYS
    ann_vol = vol * np.sqrt(TRADING_DAYS)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan

    return {
        "N": len(r),
        "AnnRet": ann_ret,
        "AnnVol": ann_vol,
        "Sharpe": sharpe,
        "MaxDD": max_drawdown(r),
        "Hit": (r > 0).mean(),
        "CumRet": (1.0 + r).prod() - 1.0,
    }


def predictive_stats(x, y):
    """OLS slope with HC1 heteroskedasticity-robust standard error."""
    z = pd.concat(
        [pd.Series(x, name="x"), pd.Series(y, name="y")],
        axis=1,
    ).replace([np.inf, -np.inf], np.nan).dropna()

    n = len(z)
    if n < 10 or z["x"].std(ddof=1) == 0:
        return {
            "N": n,
            "Corr": np.nan,
            "Slope": np.nan,
            "HC1_t": np.nan,
            "ApproxP": np.nan,
            "CI95_lo": np.nan,
            "CI95_hi": np.nan,
        }

    xv = z["x"].to_numpy(dtype=float)
    yv = z["y"].to_numpy(dtype=float)
    X = np.column_stack([np.ones(n), xv])

    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ yv
    residuals = yv - X @ beta

    # HC1 sandwich covariance.
    meat = X.T @ ((residuals ** 2)[:, None] * X)
    k = X.shape[1]
    cov_hc1 = (n / (n - k)) * (xtx_inv @ meat @ xtx_inv)
    se = np.sqrt(np.diag(cov_hc1))

    slope = float(beta[1])
    slope_se = float(se[1])
    tstat = slope / slope_se if slope_se > 0 else np.nan

    # Normal approximation is effectively identical here at daily-sample N.
    approx_p = math.erfc(abs(tstat) / math.sqrt(2.0)) if np.isfinite(tstat) else np.nan
    ci_lo = slope - 1.96 * slope_se
    ci_hi = slope + 1.96 * slope_se

    return {
        "N": n,
        "Corr": float(np.corrcoef(xv, yv)[0, 1]),
        "Slope": slope,
        "HC1_t": tstat,
        "ApproxP": approx_p,
        "CI95_lo": ci_lo,
        "CI95_hi": ci_hi,
    }


# ------------------------------------------------------------
# 11. FROZEN SPLITS
# ------------------------------------------------------------

replication = (df.index >= START) & (df.index <= PAPER_END)
holdout = df.index > PAPER_END


# ------------------------------------------------------------
# 12. REPORT
# ------------------------------------------------------------

def print_period(name, mask):
    d = df.loc[mask].copy()

    print("\n" + "=" * 78)
    print(name)
    print(
        f"{d.index.min().date()} to {d.index.max().date()} "
        f"| {len(d):,} rows"
    )
    print("=" * 78)

    print("\nPREDICTIVE RELATIONSHIPS")
    print("Expected sign for both rebalancing signals: NEGATIVE")

    p_threshold = predictive_stats(d["threshold"], d["spread_fwd"])
    p_calendar = predictive_stats(
        d.loc[d["last_5_days"], "calendar"],
        d.loc[d["last_5_days"], "spread_fwd"],
    )

    print("\nThreshold -> next-day ES minus ZN")
    print(p_threshold)

    print("\nCalendar -> next-day ES minus ZN, final 5 trading days")
    print(p_calendar)

    print("\nRESEARCH RETURN METRICS — BEFORE TRANSACTION COSTS")

    rows = {}
    for label, col in [
        ("Threshold", "ret_threshold"),
        ("Calendar", "ret_calendar"),
        ("Combined", "ret_combo"),
        ("5d reversal control", "ret_control"),
        ("ES buy-and-hold", "ret_es_buyhold"),
    ]:
        rows[label] = metrics(d[col])

    table = pd.DataFrame(rows).T
    print(table.to_string(float_format=lambda x: f"{x: .5f}"))


print_period("R1A — PAPER-ERA PROJECT SAMPLE", replication)
print_period("R1B — POST-PAPER PROJECT HOLDOUT", holdout)


# ------------------------------------------------------------
# 13. HOLDOUT YEAR BREAKDOWN
# ------------------------------------------------------------

print("\n" + "=" * 78)
print("HOLDOUT CALENDAR-YEAR BREAKDOWN")
print("=" * 78)

hold = df.loc[holdout].copy()

for year in sorted(hold.index.year.unique()):
    yr = hold.loc[hold.index.year == year]
    combo = metrics(yr["ret_combo"])
    control = metrics(yr["ret_control"])

    print(
        year,
        {
            "Combined_AnnRet": round(combo["AnnRet"], 5) if np.isfinite(combo["AnnRet"]) else np.nan,
            "Combined_Sharpe": round(combo["Sharpe"], 3) if np.isfinite(combo["Sharpe"]) else np.nan,
            "Combined_MaxDD": round(combo["MaxDD"], 5) if np.isfinite(combo["MaxDD"]) else np.nan,
            "Control_AnnRet": round(control["AnnRet"], 5) if np.isfinite(control["AnnRet"]) else np.nan,
            "Control_Sharpe": round(control["Sharpe"], 3) if np.isfinite(control["Sharpe"]) else np.nan,
        },
    )


# ------------------------------------------------------------
# 14. SANITY CHECKS
# ------------------------------------------------------------

print("\n" + "=" * 78)
print("SANITY CHECKS")
print("=" * 78)

print("Threshold policies:", len(THRESHOLDS))
print("Threshold range:", float(THRESHOLDS.min()), "to", float(THRESHOLDS.max()))
print("Threshold signal mean:", round(float(df["threshold"].mean()), 7))
print("Threshold signal SD:", round(float(df["threshold"].std()), 7))
print("Calendar signal mean:", round(float(df["calendar"].mean()), 7))
print("Calendar signal SD:", round(float(df["calendar"].std()), 7))
print(
    "Threshold-calendar correlation:",
    round(float(df[["threshold", "calendar"]].dropna().corr().iloc[0, 1]), 5),
)

for delta in (0.0, 0.011, 0.025):
    # Floating-point-safe lookup.
    key = min(threshold_rebalances.keys(), key=lambda k: abs(k - delta))
    n_years = max((df.index.max() - df.index.min()).days / 365.25, 1.0)
    print(
        f"Approx rebalances/year at delta={key:.3%}:",
        round(threshold_rebalances[key] / n_years, 2),
    )

print("\nR1 COMPLETE — RETURN THE FULL TEXT OUTPUT BEFORE CHANGING PARAMETERS.")
