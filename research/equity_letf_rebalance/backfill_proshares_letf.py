from __future__ import annotations

import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

OUT = Path("data/equity_letf_rebalance")
OUT.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (compatible; IPF-data research collector; +https://github.com/millbo01/IPF-data)"}

PRODUCTS = {
    "UPRO": ("SPX", 3.0),
    "SPXU": ("SPX", -3.0),
    "SSO": ("SPX", 2.0),
    "SDS": ("SPX", -2.0),
    "TQQQ": ("NDX", 3.0),
    "SQQQ": ("NDX", -3.0),
    "QLD": ("NDX", 2.0),
    "QID": ("NDX", -2.0),
}

URL = "https://accounts.profunds.com/etfdata/ByFund/{ticker}-historical_nav.csv"


def norm(s: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def exact_col(cols: list[str], name: str) -> str | None:
    for c in cols:
        if norm(c) == name:
            return c
    return None


def first_col(cols: list[str], *needles: str) -> str | None:
    for c in cols:
        n = norm(c)
        if all(x in n for x in needles):
            return c
    return None


def numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(r"[^0-9eE+\-.]", "", regex=True),
        errors="coerce",
    )


def get(url: str) -> requests.Response:
    r = requests.get(url, headers=UA, timeout=90)
    r.raise_for_status()
    return r


def collect() -> pd.DataFrame:
    frames = []

    for ticker, (family, beta) in PRODUCTS.items():
        url = URL.format(ticker=ticker)
        r = get(url)
        (OUT / f"{ticker.lower()}_historical_nav_raw.csv").write_bytes(r.content)

        df = pd.read_csv(io.BytesIO(r.content))
        cols = list(df.columns)
        date_col = exact_col(cols, "date") or first_col(cols, "date")
        nav_col = exact_col(cols, "nav") or first_col(cols, "nav")
        aum_col = (
            first_col(cols, "assets", "management")
            or first_col(cols, "net", "assets")
        )

        if not date_col or not aum_col:
            raise RuntimeError(f"{ticker}: required columns not found: {cols}")

        z = pd.DataFrame({
            "date": pd.to_datetime(df[date_col], errors="coerce").dt.date,
            "ticker": ticker,
            "family": family,
            "beta": beta,
            "nav": numeric(df[nav_col]) if nav_col else pd.NA,
            "aum": numeric(df[aum_col]),
            "source_url": url,
            "quality": "OFFICIAL_PROSHARES_DAILY",
        })
        z = z.dropna(subset=["date", "aum"]).sort_values("date")
        if z.empty:
            raise RuntimeError(f"{ticker}: zero usable rows")
        frames.append(z)

    out = pd.concat(frames, ignore_index=True).sort_values(["date", "family", "ticker"])
    out.to_csv(OUT / "letf_daily_aum.csv", index=False)
    return out


def build_signal(x: pd.DataFrame) -> pd.DataFrame:
    x = x.copy()
    x["date"] = pd.to_datetime(x["date"])
    x["aum"] = pd.to_numeric(x["aum"], errors="coerce")

    pieces = []
    for ticker, (family, beta) in PRODUCTS.items():
        q = x[x["ticker"] == ticker].set_index("date").sort_index()
        lag_aum = q["aum"].shift(1)
        coef = beta * (beta - 1.0)
        z = pd.DataFrame(index=q.index)
        z["ticker"] = ticker
        z["family"] = family
        z["beta"] = beta
        z["lag_aum"] = lag_aum
        z["convexity_scale_usd"] = coef * lag_aum
        pieces.append(z.reset_index())

    long = pd.concat(pieces, ignore_index=True)
    long.to_csv(OUT / "letf_convexity_components.csv", index=False)

    agg = (
        long.groupby(["date", "family"], as_index=False)
        .agg(
            convexity_scale_usd=("convexity_scale_usd", "sum"),
            products_present=("convexity_scale_usd", lambda s: int(s.notna().sum())),
        )
        .sort_values(["date", "family"])
    )

    wide = agg.pivot(index="date", columns="family", values="convexity_scale_usd").sort_index()
    counts = agg.pivot(index="date", columns="family", values="products_present").sort_index()

    out = pd.DataFrame(index=wide.index)
    for fam in ("SPX", "NDX"):
        out[f"{fam.lower()}_convexity_scale_usd"] = wide[fam] if fam in wide else np.nan
        out[f"{fam.lower()}_products_present"] = counts[fam] if fam in counts else 0

    out = out.reset_index()
    out.to_csv(OUT / "letf_daily_signal_scale.csv", index=False)
    return out


def main() -> None:
    daily = collect()
    sig = build_signal(daily)

    summary = (
        daily.groupby("ticker")
        .agg(rows=("date", "size"), start=("date", "min"), end=("date", "max"))
        .reset_index()
    )
    summary.to_csv(OUT / "backfill_summary.csv", index=False)

    print(summary.to_string(index=False))
    print()
    print(
        f"signal_rows={len(sig)} "
        f"start={sig['date'].min()} end={sig['date'].max()}"
    )
    print(sig.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
