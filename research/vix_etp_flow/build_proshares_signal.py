from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/vix_etp_flow/backfill")
IN = ROOT / "proshares_daily_aum.csv"
OUT = ROOT / "proshares_forced_flow_daily.csv"

# Historical daily objectives. ProShares changed both UVXY and SVXY effective
# after the close on 2018-02-27:
#   UVXY: 2.0x -> 1.5x
#   SVXY: -1.0x -> -0.5x
CHANGE_DATE = pd.Timestamp("2018-02-28")


def beta_series(ticker: str, index: pd.DatetimeIndex) -> pd.Series:
    if ticker == "UVXY":
        vals = np.where(index < CHANGE_DATE, 2.0, 1.5)
    elif ticker == "SVXY":
        vals = np.where(index < CHANGE_DATE, -1.0, -0.5)
    elif ticker == "VIXY":
        vals = np.ones(len(index), dtype=float)
    else:
        raise KeyError(ticker)
    return pd.Series(vals, index=index, dtype=float)


def main() -> None:
    x = pd.read_csv(IN)
    x["date"] = pd.to_datetime(x["date"])
    x["ticker"] = x["ticker"].str.upper()
    x["aum"] = pd.to_numeric(x["aum"], errors="coerce")
    x["nav"] = pd.to_numeric(x["nav"], errors="coerce")

    piv_aum = x.pivot_table(index="date", columns="ticker", values="aum", aggfunc="last").sort_index()
    piv_nav = x.pivot_table(index="date", columns="ticker", values="nav", aggfunc="last").sort_index()

    if "VIXY" not in piv_nav:
        raise RuntimeError("VIXY NAV is required as the public 1x benchmark-return proxy")

    benchmark_return = piv_nav["VIXY"].pct_change(fill_method=None)

    out = pd.DataFrame(index=piv_aum.index)
    out["benchmark_return_proxy"] = benchmark_return.reindex(out.index)
    out["benchmark_proxy_source"] = "VIXY_NAV_RETURN"

    flow_pieces = []
    scale_pieces = []
    present_pieces = []

    for ticker in ("UVXY", "VIXY", "SVXY"):
        aum = piv_aum[ticker] if ticker in piv_aum else pd.Series(index=out.index, dtype=float)
        lag_aum = aum.shift(1)
        beta = beta_series(ticker, out.index)
        coef = beta * (beta - 1.0)
        scale = coef * lag_aum
        flow = scale * out["benchmark_return_proxy"]

        out[f"{ticker.lower()}_lag_aum"] = lag_aum
        out[f"{ticker.lower()}_beta"] = beta
        out[f"{ticker.lower()}_convexity_scale_usd"] = scale
        out[f"{ticker.lower()}_rebalance_usd"] = flow

        flow_pieces.append(flow.rename(ticker))
        scale_pieces.append(scale.rename(ticker))
        present_pieces.append(lag_aum.notna().rename(ticker))

    flow_df = pd.concat(flow_pieces, axis=1)
    scale_df = pd.concat(scale_pieces, axis=1)
    present_df = pd.concat(present_pieces, axis=1)

    # Tradable state known before the close once today's intraday VIX-futures/index
    # return is observed: multiply this scale by the intraday benchmark return.
    out["aggregate_convexity_scale_usd"] = scale_df.sum(axis=1, min_count=1)
    out["aggregate_convexity_per_1pct_usd"] = out["aggregate_convexity_scale_usd"] * 0.01

    # Full-day diagnostic using VIXY NAV return. This is for validation/QA, not a
    # same-day trade input because the full NAV return is known only at the close.
    out["aggregate_rebalance_usd"] = flow_df.sum(axis=1, min_count=1)
    out["aggregate_abs_component_usd"] = flow_df.abs().sum(axis=1, min_count=1)
    out["products_present"] = present_df.sum(axis=1)
    out["signal_quality"] = np.where(
        out["products_present"] >= 2,
        "PROSHARES_DAILY_AUM_HISTORICAL_BETA",
        "PARTIAL_PROSHARES",
    )

    out = out.reset_index()
    out.to_csv(OUT, index=False)

    z = out.dropna(subset=["aggregate_convexity_scale_usd"])
    print(
        f"rows={len(out)} usable={len(z)} "
        f"start={z.date.min() if len(z) else None} "
        f"end={z.date.max() if len(z) else None}"
    )
    if len(z):
        print(
            z[
                [
                    "date",
                    "uvxy_beta",
                    "svxy_beta",
                    "aggregate_convexity_per_1pct_usd",
                    "benchmark_return_proxy",
                    "aggregate_rebalance_usd",
                    "products_present",
                ]
            ].tail(10).to_string(index=False)
        )


if __name__ == "__main__":
    main()
