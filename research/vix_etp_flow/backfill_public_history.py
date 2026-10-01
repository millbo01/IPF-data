from __future__ import annotations

import io
import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

OUT = Path("data/vix_etp_flow/backfill")
OUT.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (compatible; IPF-data research collector; +https://github.com/millbo01/IPF-data)"}

PROSHARES = ["UVXY", "VIXY", "SVXY"]
PROSHARES_URL = "https://accounts.profunds.com/etfdata/ByFund/{ticker}-historical_nav.csv"
VS_DOCS = "https://www.volatilityshares.com/filings-and-documents.php?sort=asc"


def norm(s: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def get(url: str) -> requests.Response:
    r = requests.get(url, headers=UA, timeout=90)
    r.raise_for_status()
    return r


def first_col(cols: list[str], *needles: str) -> str | None:
    for c in cols:
        n = norm(c)
        if all(x in n for x in needles):
            return c
    return None


def exact_col(cols: list[str], normalized_name: str) -> str | None:
    for c in cols:
        if norm(c) == normalized_name:
            return c
    return None


def numeric(s: pd.Series) -> pd.Series:
    # Provider CSVs have historically used both plain numerics and formatted strings.
    return pd.to_numeric(
        s.astype(str).str.replace(r"[^0-9eE+\-.]", "", regex=True),
        errors="coerce",
    )


def backfill_proshares() -> pd.DataFrame:
    frames = []
    for ticker in PROSHARES:
        url = PROSHARES_URL.format(ticker=ticker)
        r = get(url)
        raw_path = OUT / f"{ticker.lower()}_historical_nav_raw.csv"
        raw_path.write_bytes(r.content)

        df = pd.read_csv(io.BytesIO(r.content))
        cols = list(df.columns)
        date_col = exact_col(cols, "date") or first_col(cols, "date")
        nav_col = exact_col(cols, "nav") or first_col(cols, "nav")
        ticker_col = exact_col(cols, "ticker") or first_col(cols, "ticker")
        shares_col = first_col(cols, "shares", "outstanding")
        aum_col = first_col(cols, "assets", "management") or first_col(cols, "net", "assets")

        if not date_col:
            raise RuntimeError(f"{ticker}: date column not found: {cols}")
        if not aum_col:
            raise RuntimeError(f"{ticker}: AUM column not found: {cols}")

        out = pd.DataFrame()
        out["date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
        out["ticker"] = ticker
        out["nav"] = numeric(df[nav_col]) if nav_col else pd.NA
        out["shares_outstanding_source"] = numeric(df[shares_col]) if shares_col else pd.NA
        out["aum"] = numeric(df[aum_col])
        out["source_ticker"] = df[ticker_col].astype(str) if ticker_col else ticker
        out["source_url"] = url
        out["quality"] = "OFFICIAL_PROSHARES_DAILY"
        out = out.dropna(subset=["date", "aum"]).sort_values("date")

        if out.empty:
            raise RuntimeError(f"{ticker}: parsed zero AUM rows from {cols}")
        frames.append(out)

    z = pd.concat(frames, ignore_index=True).sort_values(["date", "ticker"])
    z.to_csv(OUT / "proshares_daily_aum.csv", index=False)
    return z


def index_volatilityshares_statements() -> pd.DataFrame:
    r = get(VS_DOCS)
    soup = BeautifulSoup(r.text, "lxml")
    rows = []

    # Preserve a complete official-page link index. The monthly table often uses
    # image-only anchors, so assignment to UVIX/SVIX is deliberately conservative.
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = " ".join(a.stripped_strings)
        blob = (text + " " + href).upper()
        if "download-filings-and-documents" not in href.lower() and not href.lower().endswith(".pdf"):
            continue

        if "UVIX" in blob:
            ticker = "UVIX"
        elif "SVIX" in blob:
            ticker = "SVIX"
        else:
            ticker = "UNASSIGNED"

        rows.append({
            "ticker": ticker,
            "label": text,
            "url": urljoin(VS_DOCS, href),
            "quality": "OFFICIAL_VS_DOCUMENT_INDEX",
        })

    z = pd.DataFrame(rows).drop_duplicates(subset=["ticker", "url"])
    z.to_csv(OUT / "volatilityshares_statement_index.csv", index=False)
    (OUT / "volatilityshares_filings_page.html").write_text(r.text, encoding="utf-8")
    return z


def main() -> None:
    ps = backfill_proshares()
    vs = index_volatilityshares_statements()
    summary = pd.DataFrame([
        {
            "dataset": "proshares_daily_aum",
            "rows": len(ps),
            "tickers": ",".join(sorted(ps.ticker.unique())),
            "start": str(ps.date.min()),
            "end": str(ps.date.max()),
        },
        {
            "dataset": "volatilityshares_statement_index",
            "rows": len(vs),
            "tickers": ",".join(sorted(vs.ticker.astype(str).unique())) if len(vs) else "",
            "start": "",
            "end": "",
        },
    ])
    summary.to_csv(OUT / "backfill_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
