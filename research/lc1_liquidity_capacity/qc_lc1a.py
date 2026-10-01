# ============================================================
# LC1-A — LIQUIDITY CAPACITY
# Frozen post-diagnostic QuantConnect Research test
#
# Run unchanged in a QuantConnect Research notebook.
# See SPEC.md in the research/lc1_liquidity_capacity directory.
#
# This script:
#   1) reconstructs BBO state from side-specific quote updates,
#   2) classifies aggressive trades,
#   3) aggregates 30-second pressure windows,
#   4) measures pre-existing contra-side capacity,
#   5) tests whether capacity modifies price impact,
#   6) reports build (2025) and untouched holdout (2026).
#
# It does NOT optimize a trading strategy.
# ============================================================

from AlgorithmImports import *
from QuantConnect.Research import QuantBook

from datetime import datetime, time
import gc
import math
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 0. FROZEN DESIGN
# ------------------------------------------------------------

BUILD_DATES = [
    "2025-01-06", "2025-01-21", "2025-01-24", "2025-02-04",
    "2025-02-26", "2025-04-01", "2025-04-14", "2025-04-24",
    "2025-05-06", "2025-05-08", "2025-05-13", "2025-05-14",
    "2025-05-21", "2025-06-02", "2025-07-01", "2025-07-17",
    "2025-08-04", "2025-08-15", "2025-09-29", "2025-09-30",
    "2025-10-27", "2025-11-19", "2025-12-10", "2025-12-12",
]

HOLDOUT_DATES = [
    "2026-01-02", "2026-01-23", "2026-03-06", "2026-03-10",
    "2026-03-11", "2026-03-30", "2026-05-14", "2026-05-21",
    "2026-06-10", "2026-06-24", "2026-07-30", "2026-08-31",
]

FETCH_START = time(9, 59, 0)
FETCH_END = time(11, 0, 0)
SIGNAL_START = time(10, 0, 0)
SIGNAL_LAST_START = time(10, 44, 30)

MIN_CLASSIFIED_QTY_SHARE = 0.80
MIN_VALID_WINDOWS = 60

OUTCOMES = [
    "impact_30s",
    "fwd_30s",
    "fwd_60s",
    "fwd_5m",
    "fwd_15m",
]

EPS = 1e-12


# ------------------------------------------------------------
# 1. QUANTCONNECT FUTURES
# ------------------------------------------------------------

qb = QuantBook()

futures = {
    "ES": qb.add_future(
        Futures.Indices.SP_500_E_MINI,
        Resolution.TICK,
        data_mapping_mode=DataMappingMode.OPEN_INTEREST,
        data_normalization_mode=DataNormalizationMode.RAW,
        contract_depth_offset=0,
    ),
    "ZN": qb.add_future(
        Futures.Financials.Y_10_TREASURY_NOTE,
        Resolution.TICK,
        data_mapping_mode=DataMappingMode.OPEN_INTEREST,
        data_normalization_mode=DataNormalizationMode.RAW,
        contract_depth_offset=0,
    ),
    "CL": qb.add_future(
        Futures.Energy.CRUDE_OIL_WTI,
        Resolution.TICK,
        data_mapping_mode=DataMappingMode.OPEN_INTEREST,
        data_normalization_mode=DataNormalizationMode.RAW,
        contract_depth_offset=0,
    ),
}


# ------------------------------------------------------------
# 2. HELPERS
# ------------------------------------------------------------

def combine_date_time(date_string, t):
    d = pd.Timestamp(date_string)
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)


def numeric_col(df, lookup, name):
    col = lookup.get(name)
    if col is None:
        return pd.Series(np.nan, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def fetch_tick_frame(future, date_string):
    start = combine_date_time(date_string, FETCH_START)
    end = combine_date_time(date_string, FETCH_END)

    h = qb.history(future.symbol, start, end, Resolution.TICK)

    if h is None or len(h) == 0:
        return None, {"reason": "no_history", "raw_rows": 0}

    raw_rows = len(h)
    df = h.reset_index().copy()
    df["_row_order"] = np.arange(len(df), dtype=np.int64)

    lookup = {str(c).lower(): c for c in df.columns}
    required = [
        "time", "askprice", "asksize", "bidprice",
        "bidsize", "lastprice", "quantity",
    ]
    missing = [x for x in required if x not in lookup]
    if missing:
        return None, {
            "reason": "missing_columns:" + ",".join(missing),
            "raw_rows": raw_rows,
        }

    out = pd.DataFrame({
        "time": pd.to_datetime(df[lookup["time"]], errors="coerce"),
        "askprice": numeric_col(df, lookup, "askprice"),
        "asksize": numeric_col(df, lookup, "asksize"),
        "bidprice": numeric_col(df, lookup, "bidprice"),
        "bidsize": numeric_col(df, lookup, "bidsize"),
        "lastprice": numeric_col(df, lookup, "lastprice"),
        "quantity": numeric_col(df, lookup, "quantity"),
        "_row_order": df["_row_order"].values,
    })

    out = (
        out.dropna(subset=["time"])
        .sort_values(["time", "_row_order"], kind="mergesort")
        .reset_index(drop=True)
    )

    return out, {"reason": "ok", "raw_rows": raw_rows}


def reconstruct_stream_state(df):
    """
    Reconstruct prevailing two-sided BBO on every raw row, preserving
    original row order for equal timestamps. This avoids ambiguity when
    trade and quote rows share the same timestamp.
    """
    work = df

    bid_update = work["bidprice"].fillna(0).gt(0)
    ask_update = work["askprice"].fillna(0).gt(0)

    work["bid_px"] = work["bidprice"].where(bid_update).ffill()
    work["bid_sz"] = work["bidsize"].where(bid_update).ffill()
    work["ask_px"] = work["askprice"].where(ask_update).ffill()
    work["ask_sz"] = work["asksize"].where(ask_update).ffill()

    work["valid_bbo"] = (
        work["bid_px"].gt(0)
        & work["ask_px"].gt(0)
        & work["bid_sz"].gt(0)
        & work["ask_sz"].gt(0)
        & work["ask_px"].ge(work["bid_px"])
    )

    work["mid"] = np.where(
        work["valid_bbo"],
        (work["bid_px"] + work["ask_px"]) / 2.0,
        np.nan,
    )
    work["spread"] = np.where(
        work["valid_bbo"],
        work["ask_px"] - work["bid_px"],
        np.nan,
    )

    return work


def classify_trades(stream):
    strict = (
        stream["quantity"].fillna(0).gt(0)
        & stream["lastprice"].fillna(0).gt(0)
    )

    tr = stream.loc[
        strict,
        [
            "time", "_row_order", "lastprice", "quantity",
            "bid_px", "ask_px", "valid_bbo",
        ],
    ].copy()

    if len(tr) == 0:
        return pd.DataFrame(), 0.0

    unlocked = (
        tr["valid_bbo"]
        & tr["ask_px"].gt(tr["bid_px"] + EPS)
    )

    direct = np.zeros(len(tr), dtype=np.int8)

    at_or_above_ask = (
        unlocked
        & tr["lastprice"].ge(tr["ask_px"] - EPS)
    )
    at_or_below_bid = (
        unlocked
        & tr["lastprice"].le(tr["bid_px"] + EPS)
    )

    direct[at_or_above_ask.to_numpy()] = 1
    direct[at_or_below_bid.to_numpy()] = -1

    # Deterministic tick-rule fallback for unresolved trades.
    price_diff = tr["lastprice"].diff()
    tick_sign = np.sign(price_diff)
    tick_sign = (
        pd.Series(tick_sign, index=tr.index)
        .replace(0, np.nan)
        .ffill()
        .fillna(0)
        .astype(np.int8)
    )

    unresolved = direct == 0
    sign = direct.copy()
    sign[unresolved] = tick_sign.to_numpy()[unresolved]

    tr["aggr_sign"] = sign
    tr["signed_qty"] = tr["quantity"] * tr["aggr_sign"]

    total_qty = float(tr["quantity"].sum())
    classified_qty = float(tr.loc[tr["aggr_sign"].ne(0), "quantity"].sum())
    classified_share = classified_qty / total_qty if total_qty > 0 else 0.0

    return tr, classified_share


def one_second_bbo(stream, date_string):
    fetch_start = combine_date_time(date_string, FETCH_START)
    fetch_end = combine_date_time(date_string, FETCH_END)

    idx = pd.date_range(fetch_start, fetch_end, freq="1s")

    q = stream.loc[
        stream["valid_bbo"],
        ["time", "_row_order", "bid_px", "bid_sz", "ask_px", "ask_sz", "mid", "spread"],
    ].copy()

    q = q.sort_values(["time", "_row_order"], kind="mergesort")
    q = q.drop_duplicates("time", keep="last")
    q = q.set_index("time")[["bid_px", "bid_sz", "ask_px", "ask_sz", "mid", "spread"]]

    state = q.reindex(idx, method="ffill")

    # Frozen pre-window measures; shift(1) ensures the second at the
    # signal boundary is not used in the preceding-capacity statistic.
    state["pre_bid_size"] = (
        state["bid_sz"].rolling(30, min_periods=20).median().shift(1)
    )
    state["pre_ask_size"] = (
        state["ask_sz"].rolling(30, min_periods=20).median().shift(1)
    )
    state["pre_spread"] = (
        state["spread"].rolling(30, min_periods=20).median().shift(1)
    )

    log_mid = np.log(state["mid"].where(state["mid"].gt(0)))
    one_sec_ret = log_mid.diff()
    state["pre_rv"] = (
        one_sec_ret.rolling(60, min_periods=40).std().shift(1)
    )

    return state


def build_windows(trades, state, date_string):
    signal_start = combine_date_time(date_string, SIGNAL_START)
    signal_last = combine_date_time(date_string, SIGNAL_LAST_START)
    window_starts = pd.date_range(signal_start, signal_last, freq="30s")

    pressure_trades = trades[
        (trades["time"] >= signal_start)
        & (trades["time"] < signal_last + pd.Timedelta(seconds=30))
    ].copy()

    if len(pressure_trades):
        pressure_trades["window"] = pressure_trades["time"].dt.floor("30s")
        grouped = pressure_trades.groupby("window").agg(
            pressure=("signed_qty", "sum"),
            total_qty=("quantity", "sum"),
            trades=("quantity", "size"),
        )
    else:
        grouped = pd.DataFrame(columns=["pressure", "total_qty", "trades"])

    rows = []

    for t in window_starts:
        if t in grouped.index:
            pressure = float(grouped.loc[t, "pressure"])
            total_qty = float(grouped.loc[t, "total_qty"])
            trade_count = int(grouped.loc[t, "trades"])
        else:
            pressure = 0.0
            total_qty = 0.0
            trade_count = 0

        if not np.isfinite(pressure) or pressure == 0:
            continue

        direction = 1.0 if pressure > 0 else -1.0

        try:
            s0 = state.loc[t]
            mid0 = float(s0["mid"])
            mid_end = float(state.loc[t + pd.Timedelta(seconds=30), "mid"])
            mid_fwd30 = float(state.loc[t + pd.Timedelta(seconds=60), "mid"])
            mid_fwd60 = float(state.loc[t + pd.Timedelta(seconds=90), "mid"])
            mid_fwd5m = float(state.loc[t + pd.Timedelta(seconds=330), "mid"])
            mid_fwd15m = float(state.loc[t + pd.Timedelta(seconds=930), "mid"])
        except Exception:
            continue

        mids = [mid0, mid_end, mid_fwd30, mid_fwd60, mid_fwd5m, mid_fwd15m]
        if not all(np.isfinite(x) and x > 0 for x in mids):
            continue

        pre_bid_size = float(s0["pre_bid_size"])
        pre_ask_size = float(s0["pre_ask_size"])
        pre_spread = float(s0["pre_spread"])
        pre_rv = float(s0["pre_rv"])

        if direction > 0:
            capacity = pre_ask_size
        else:
            capacity = pre_bid_size

        if not (
            np.isfinite(capacity)
            and capacity > 0
            and np.isfinite(pre_spread)
            and pre_spread >= 0
            and np.isfinite(pre_rv)
            and pre_rv >= 0
        ):
            continue

        impact_30s = direction * math.log(mid_end / mid0)
        fwd_30s = direction * math.log(mid_fwd30 / mid_end)
        fwd_60s = direction * math.log(mid_fwd60 / mid_end)
        fwd_5m = direction * math.log(mid_fwd5m / mid_end)
        fwd_15m = direction * math.log(mid_fwd15m / mid_end)

        minute_from_start = int((t - signal_start).total_seconds() // 60)
        time_bucket = minute_from_start // 5

        rows.append({
            "date": date_string,
            "window_start": t,
            "time_bucket": int(time_bucket),
            "pressure": pressure,
            "pressure_abs": abs(pressure),
            "total_qty": total_qty,
            "trade_count": trade_count,
            "capacity": capacity,
            "pre_bid_size": pre_bid_size,
            "pre_ask_size": pre_ask_size,
            "pre_spread": pre_spread,
            "pre_rv": pre_rv,
            "impact_30s": impact_30s,
            "fwd_30s": fwd_30s,
            "fwd_60s": fwd_60s,
            "fwd_5m": fwd_5m,
            "fwd_15m": fwd_15m,
        })

    return pd.DataFrame(rows)


def process_day(instrument, future, split, date_string):
    df, meta = fetch_tick_frame(future, date_string)

    if df is None:
        return None, {
            "instrument": instrument,
            "split": split,
            "date": date_string,
            "raw_rows": meta.get("raw_rows", 0),
            "classified_share": np.nan,
            "valid_windows": 0,
            "status": meta.get("reason", "fetch_fail"),
        }

    raw_rows = meta["raw_rows"]

    try:
        stream = reconstruct_stream_state(df)
        trades, classified_share = classify_trades(stream)

        if classified_share < MIN_CLASSIFIED_QTY_SHARE:
            return None, {
                "instrument": instrument,
                "split": split,
                "date": date_string,
                "raw_rows": raw_rows,
                "classified_share": classified_share,
                "valid_windows": 0,
                "status": "fail_classification_share",
            }

        state = one_second_bbo(stream, date_string)
        obs = build_windows(trades, state, date_string)

        if len(obs) < MIN_VALID_WINDOWS:
            return None, {
                "instrument": instrument,
                "split": split,
                "date": date_string,
                "raw_rows": raw_rows,
                "classified_share": classified_share,
                "valid_windows": len(obs),
                "status": "fail_valid_windows",
            }

        obs["instrument"] = instrument
        obs["split"] = split
        obs["classified_share_day"] = classified_share

        return obs, {
            "instrument": instrument,
            "split": split,
            "date": date_string,
            "raw_rows": raw_rows,
            "classified_share": classified_share,
            "valid_windows": len(obs),
            "status": "PASS",
        }

    finally:
        gc.collect()


# ------------------------------------------------------------
# 3. REGRESSION / MATCHED TESTS
# ------------------------------------------------------------

def robust_interaction_regression(d, outcome):
    use = d[
        [
            outcome, "pressure_abs", "capacity", "pre_spread",
            "pre_rv", "time_bucket",
        ]
    ].replace([np.inf, -np.inf], np.nan).dropna().copy()

    use = use[
        use["pressure_abs"].gt(0)
        & use["capacity"].gt(0)
    ].copy()

    n = len(use)
    if n < 100:
        return {
            "N": n,
            "beta_interaction": np.nan,
            "beta_bps": np.nan,
            "se_hc1": np.nan,
            "t_hc1": np.nan,
            "p_approx": np.nan,
            "ci95_lo": np.nan,
            "ci95_hi": np.nan,
        }

    use["log_pressure"] = np.log1p(use["pressure_abs"])
    use["inv_capacity"] = -np.log1p(use["capacity"])

    continuous = [
        "log_pressure", "inv_capacity", "pre_spread", "pre_rv",
    ]

    for c in continuous:
        sd = float(use[c].std(ddof=1))
        if not np.isfinite(sd) or sd <= 0:
            use["z_" + c] = 0.0
        else:
            use["z_" + c] = (use[c] - use[c].mean()) / sd

    use["interaction"] = (
        use["z_log_pressure"] * use["z_inv_capacity"]
    )

    tod = pd.get_dummies(
        use["time_bucket"].astype(int),
        prefix="tb",
        drop_first=True,
        dtype=float,
    )

    Xdf = pd.concat(
        [
            pd.Series(1.0, index=use.index, name="intercept"),
            use[
                [
                    "z_log_pressure",
                    "z_inv_capacity",
                    "interaction",
                    "z_pre_spread",
                    "z_pre_rv",
                ]
            ],
            tod,
        ],
        axis=1,
    )

    X = Xdf.to_numpy(dtype=float)
    y = use[outcome].to_numpy(dtype=float)

    keep = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X = X[keep]
    y = y[keep]

    n = len(y)
    k = X.shape[1]
    if n <= k + 2:
        return {
            "N": n,
            "beta_interaction": np.nan,
            "beta_bps": np.nan,
            "se_hc1": np.nan,
            "t_hc1": np.nan,
            "p_approx": np.nan,
            "ci95_lo": np.nan,
            "ci95_hi": np.nan,
        }

    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    resid = y - X @ beta

    meat = X.T @ ((resid ** 2)[:, None] * X)
    cov = (n / (n - k)) * (xtx_inv @ meat @ xtx_inv)
    se = np.sqrt(np.maximum(np.diag(cov), 0))

    interaction_idx = list(Xdf.columns).index("interaction")

    b = float(beta[interaction_idx])
    s = float(se[interaction_idx])
    t = b / s if s > 0 else np.nan
    p = math.erfc(abs(t) / math.sqrt(2.0)) if np.isfinite(t) else np.nan

    return {
        "N": n,
        "beta_interaction": b,
        "beta_bps": b * 10000.0,
        "se_hc1": s,
        "t_hc1": t,
        "p_approx": p,
        "ci95_lo": b - 1.96 * s,
        "ci95_hi": b + 1.96 * s,
    }


def matched_capacity_test(d, outcome):
    use = d[
        [outcome, "pressure_abs", "capacity"]
    ].replace([np.inf, -np.inf], np.nan).dropna().copy()

    use = use[
        use["pressure_abs"].gt(0)
        & use["capacity"].gt(0)
    ].copy()

    if len(use) < 100:
        return {
            "N": len(use),
            "bins": 0,
            "low_mean_bps": np.nan,
            "high_mean_bps": np.nan,
            "diff_bps": np.nan,
        }

    use["log_pressure"] = np.log1p(use["pressure_abs"])

    try:
        use["pbin"] = pd.qcut(
            use["log_pressure"],
            5,
            labels=False,
            duplicates="drop",
        )
    except Exception:
        return {
            "N": len(use),
            "bins": 0,
            "low_mean_bps": np.nan,
            "high_mean_bps": np.nan,
            "diff_bps": np.nan,
        }

    bin_results = []

    for pbin, g in use.groupby("pbin", observed=True):
        if len(g) < 30:
            continue

        q30 = g["capacity"].quantile(0.30)
        q70 = g["capacity"].quantile(0.70)

        low = g[g["capacity"] <= q30][outcome]
        high = g[g["capacity"] >= q70][outcome]

        if len(low) < 5 or len(high) < 5:
            continue

        low_mean = float(low.mean())
        high_mean = float(high.mean())

        bin_results.append({
            "pbin": int(pbin),
            "low_n": len(low),
            "high_n": len(high),
            "low_mean": low_mean,
            "high_mean": high_mean,
            "diff": low_mean - high_mean,
        })

    if not bin_results:
        return {
            "N": len(use),
            "bins": 0,
            "low_mean_bps": np.nan,
            "high_mean_bps": np.nan,
            "diff_bps": np.nan,
        }

    br = pd.DataFrame(bin_results)

    return {
        "N": len(use),
        "bins": len(br),
        "low_mean_bps": float(br["low_mean"].mean() * 10000.0),
        "high_mean_bps": float(br["high_mean"].mean() * 10000.0),
        "diff_bps": float(br["diff"].mean() * 10000.0),
    }


def daily_matched_sign(d, outcome="impact_30s"):
    """
    Descriptive stability check only: within each day, pressure quintiles
    and capacity 30/70 groups are rebuilt using predictor data only.
    """
    vals = []

    for date, g in d.groupby("date"):
        r = matched_capacity_test(g, outcome)
        if np.isfinite(r["diff_bps"]):
            vals.append((date, r["diff_bps"]))

    if not vals:
        return {
            "usable_days": 0,
            "positive_days": 0,
            "median_daily_diff_bps": np.nan,
            "max_abs_daily_diff_bps": np.nan,
        }

    arr = np.array([v[1] for v in vals], dtype=float)

    return {
        "usable_days": len(arr),
        "positive_days": int((arr > 0).sum()),
        "median_daily_diff_bps": float(np.median(arr)),
        "max_abs_daily_diff_bps": float(np.max(np.abs(arr))),
    }


# ------------------------------------------------------------
# 4. EXTRACT FROZEN SAMPLES
# ------------------------------------------------------------

print("=" * 80)
print("LC1-A LIQUIDITY CAPACITY — FROZEN EXTRACTION")
print("=" * 80)
print("Markets: ES, ZN, CL")
print("Build dates:", len(BUILD_DATES), "| Holdout dates:", len(HOLDOUT_DATES))
print("Signal windows: 10:00:00 through 10:44:30, 30-second non-overlap")
print("Raw ticks are processed one instrument-day at a time.")
print()

all_obs = []
day_logs = []

for instrument, future in futures.items():
    for split, dates in [("BUILD", BUILD_DATES), ("HOLDOUT", HOLDOUT_DATES)]:
        print(f"\n--- {instrument} {split} ---")

        for i, date_string in enumerate(dates, start=1):
            obs, log = process_day(
                instrument,
                future,
                split,
                date_string,
            )

            day_logs.append(log)

            share = log["classified_share"]
            share_text = (
                f"{share:.1%}" if np.isfinite(share) else "NA"
            )

            print(
                f"{i:02d}/{len(dates):02d} {date_string} "
                f"rows={int(log['raw_rows']):,} "
                f"classified={share_text} "
                f"windows={int(log['valid_windows'])} "
                f"{log['status']}"
            )

            if obs is not None and len(obs):
                all_obs.append(obs)

            gc.collect()


logs = pd.DataFrame(day_logs)

if not all_obs:
    raise RuntimeError(
        "No usable LC1 observations were produced. "
        "Return the full output unchanged."
    )

data = pd.concat(all_obs, ignore_index=True)

print("\n" + "=" * 80)
print("EXTRACTION SUMMARY")
print("=" * 80)

summary = (
    logs.groupby(["instrument", "split"])
    .agg(
        selected_days=("date", "size"),
        passed_days=("status", lambda s: int((s == "PASS").sum())),
        raw_rows=("raw_rows", "sum"),
        median_classified_share=("classified_share", "median"),
        valid_windows=("valid_windows", "sum"),
    )
)

print(summary.to_string(float_format=lambda x: f"{x:.4f}"))

failed = logs[logs["status"] != "PASS"]
if len(failed):
    print("\nFailed/skipped sampled dates:")
    print(
        failed[
            [
                "instrument", "split", "date", "raw_rows",
                "classified_share", "valid_windows", "status",
            ]
        ].to_string(index=False)
    )
else:
    print("\nNo sampled dates failed the frozen data-quality gates.")


# ------------------------------------------------------------
# 5. ANALYSIS — BUILD AND HOLDOUT SEPARATELY
# ------------------------------------------------------------

reg_rows = []
match_rows = []
stability_rows = []

for instrument in ["ES", "ZN", "CL"]:
    for split in ["BUILD", "HOLDOUT"]:
        d = data[
            (data["instrument"] == instrument)
            & (data["split"] == split)
        ].copy()

        print("\n" + "=" * 80)
        print(f"{instrument} — {split}")
        print("=" * 80)
        print(
            f"Observations: {len(d):,} | "
            f"Days: {d['date'].nunique() if len(d) else 0}"
        )

        if len(d) == 0:
            continue

        print("\nRegression interaction: pressure x inverse-capacity")
        print("Expected sign: POSITIVE")

        reg_table_rows = []
        match_table_rows = []

        for outcome in OUTCOMES:
            rr = robust_interaction_regression(d, outcome)
            rr.update({
                "instrument": instrument,
                "split": split,
                "outcome": outcome,
            })
            reg_rows.append(rr)

            mr = matched_capacity_test(d, outcome)
            mr.update({
                "instrument": instrument,
                "split": split,
                "outcome": outcome,
            })
            match_rows.append(mr)

            reg_table_rows.append({
                "outcome": outcome,
                "N": rr["N"],
                "beta_bps": rr.get("beta_bps", np.nan),
                "HC1_t": rr["t_hc1"],
                "p": rr["p_approx"],
                "CI95_lo_bps": rr["ci95_lo"] * 10000.0 if np.isfinite(rr["ci95_lo"]) else np.nan,
                "CI95_hi_bps": rr["ci95_hi"] * 10000.0 if np.isfinite(rr["ci95_hi"]) else np.nan,
            })

            match_table_rows.append({
                "outcome": outcome,
                "N": mr["N"],
                "bins": mr["bins"],
                "low_cap_mean_bps": mr["low_mean_bps"],
                "high_cap_mean_bps": mr["high_mean_bps"],
                "low_minus_high_bps": mr["diff_bps"],
            })

        print(
            pd.DataFrame(reg_table_rows)
            .set_index("outcome")
            .to_string(float_format=lambda x: f"{x: .5f}")
        )

        print("\nMatched capacity comparison within pressure quintiles")
        print("Expected low-capacity minus high-capacity sign: POSITIVE")
        print(
            pd.DataFrame(match_table_rows)
            .set_index("outcome")
            .to_string(float_format=lambda x: f"{x: .5f}")
        )

        stability = daily_matched_sign(d, "impact_30s")
        stability.update({
            "instrument": instrument,
            "split": split,
        })
        stability_rows.append(stability)

        print("\nImmediate-impact daily stability check:")
        print(stability)


reg = pd.DataFrame(reg_rows)
matched = pd.DataFrame(match_rows)
stability = pd.DataFrame(stability_rows)


# ------------------------------------------------------------
# 6. FROZEN HOLDOUT ADJUDICATION
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("LC1-A HOLDOUT ADJUDICATION")
print("=" * 80)

instrument_results = []

for instrument in ["ES", "ZN", "CL"]:
    r_i = reg[
        (reg["instrument"] == instrument)
        & (reg["split"] == "HOLDOUT")
        & (reg["outcome"] == "impact_30s")
    ]

    m_i = matched[
        (matched["instrument"] == instrument)
        & (matched["split"] == "HOLDOUT")
        & (matched["outcome"] == "impact_30s")
    ]

    if len(r_i) == 0 or len(m_i) == 0:
        mech = False
        beta = np.nan
        diff = np.nan
    else:
        beta = float(r_i.iloc[0]["beta_interaction"])
        diff = float(m_i.iloc[0]["diff_bps"])
        mech = bool(
            np.isfinite(beta)
            and np.isfinite(diff)
            and beta > 0
            and diff > 0
        )

    forward_passes = []

    for outcome in ["fwd_30s", "fwd_60s", "fwd_5m", "fwd_15m"]:
        r_o = reg[
            (reg["instrument"] == instrument)
            & (reg["split"] == "HOLDOUT")
            & (reg["outcome"] == outcome)
        ]
        m_o = matched[
            (matched["instrument"] == instrument)
            & (matched["split"] == "HOLDOUT")
            & (matched["outcome"] == outcome)
        ]

        if len(r_o) and len(m_o):
            b = float(r_o.iloc[0]["beta_interaction"])
            md = float(m_o.iloc[0]["diff_bps"])
            if np.isfinite(b) and np.isfinite(md) and b > 0 and md > 0:
                forward_passes.append(outcome)

    instrument_results.append({
        "instrument": instrument,
        "mechanism_direction_pass": mech,
        "impact_beta_bps": beta * 10000.0 if np.isfinite(beta) else np.nan,
        "impact_matched_diff_bps": diff,
        "forward_direction_passes": ",".join(forward_passes) if forward_passes else "NONE",
    })

inst = pd.DataFrame(instrument_results)
print(inst.to_string(index=False))

mechanism_markets = int(inst["mechanism_direction_pass"].sum())
trading_markets = int(
    inst["forward_direction_passes"].ne("NONE").sum()
)

print("\nFrozen directional gate counts:")
print(
    "  Mechanism markets passing both immediate directional checks:",
    mechanism_markets,
    "/ 3",
)
print(
    "  Markets with >=1 forward horizon passing both directional checks:",
    trading_markets,
    "/ 3",
)

if mechanism_markets < 2:
    verdict = (
        "FAIL MECHANISM GATE — LC1-A is killed under the frozen directional rule. "
        "Do not buy richer order-book data for this mechanism."
    )
elif trading_markets < 2:
    verdict = (
        "MECHANISM PASS / TRADING-RELEVANCE FAIL — capacity appears to modify "
        "immediate impact, but the frozen forward evidence is insufficient for "
        "promotion as a bot edge."
    )
else:
    verdict = (
        "DIRECTIONAL GATES PASS — inspect statistical precision, daily stability, "
        "and economic magnitude before any costed strategy test. This is not yet "
        "a trading-strategy approval."
    )

print("\nFROZEN LC1-A VERDICT:")
print(verdict)

print("\nReturn the complete output from EXTRACTION SUMMARY onward before changing code.")
