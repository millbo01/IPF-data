from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/vix_etp_flow/backfill")
IN = ROOT / "proshares_daily_aum.csv"
OUT = ROOT / "proshares_forced_flow_daily.csv"

BETA = {"UVXY": 1.5, "VIXY": 1.0, "SVXY": -0.5}


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

    pieces = []
    for ticker, beta in BETA.items():
        aum = piv_aum[ticker] if ticker in piv_aum else pd.Series(index=out.index, dtype=float)
        lag_aum = aum.shift(1)
        coef = beta * (beta - 1.0)
        flow = coef * lag_aum * out["benchmark_return_proxy"]
        out[f"{ticker.lower()}_lag_aum"] = lag_aum
        out[f"{ticker.lower()}_beta"] = beta
        out[f"{ticker.lower()}_rebalance_usd"] = flow
        pieces.append(flow.rename(ticker))

    flow_df = pd.concat(pieces, axis=1)
    out["aggregate_rebalance_usd"] = flow_df.sum(axis=1, min_count=1)
    out["aggregate_abs_component_usd"] = flow_df.abs().sum(axis=1, min_count=1)
    out["products_present"] = flow_df.notna().sum(axis=1)
    out["signal_quality"] = np.where(
        out["products_present"] >= 2,
        "PROSHARES_DAILY_AUM_VIXY_PROXY",
        "PARTIAL_PROSHARES",
    )

    # The 1x VIXY product has beta*(beta-1)=0 for leverage rebalancing. It remains
    # useful as the public benchmark-return proxy; calendar roll is a separate signal.
    out = out.reset_index()
    out.to_csv(OUT, index=False)

    z = out.dropna(subset=["aggregate_rebalance_usd"])
    print(f"rows={len(out)} usable={len(z)} start={z.date.min() if len(z) else None} end={z.date.max() if len(z) else None}")
    if len(z):
        print(z[["date", "benchmark_return_proxy", "aggregate_rebalance_usd", "products_present"]].tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
