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


def _period_from_cells(cells: list) -> str:
    if not cells:
        return ""
    text = " ".join(cells[0].stripped_strings).strip()
    return re.sub(r"\s+", " ", text)


def index_volatilityshares_statements() -> pd.DataFrame:
    r = get(VS_DOCS)
    soup = BeautifulSoup(r.text, "lxml")
    rows = []

    # The official archive renders year/month in the first column and separate
    # SVIX / UVIX download cells. The anchors themselves are often image-only,
    # which is why the older generic link scraper lost ticker assignment.
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        svix_col = None
        uvix_col = None

        for tr in trs:
            cells = tr.find_all(["th", "td"])
            labels = [" ".join(c.stripped_strings).strip().upper() for c in cells]
            if "SVIX" in labels and "UVIX" in labels:
                svix_col = labels.index("SVIX")
                uvix_col = labels.index("UVIX")
                continue

            if svix_col is None or uvix_col is None:
                continue
            if len(cells) <= max(svix_col, uvix_col):
                continue

            period = _period_from_cells(cells)
            for ticker, idx in (("SVIX", svix_col), ("UVIX", uvix_col)):
                a = cells[idx].find("a", href=True)
                if not a:
                    continue
                href = a["href"]
                if "download-filings-and-documents" not in href.lower() and not href.lower().endswith(".pdf"):
                    continue
                rows.append({
                    "ticker": ticker,
                    "label": period,
                    "url": urljoin(VS_DOCS, href),
                    "quality": "OFFICIAL_VS_MONTHLY_STATEMENT_INDEX",
                })

    # Preserve other official PDF/download links separately for audit/provenance,
    # but never use them as UVIX/SVIX observations without an assigned ticker.
    assigned_urls = {x["url"] for x in rows}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "download-filings-and-documents" not in href.lower() and not href.lower().endswith(".pdf"):
            continue
        url = urljoin(VS_DOCS, href)
        if url in assigned_urls:
            continue
        text = " ".join(a.stripped_strings)
        blob = (text + " " + href).upper()
        if "UVIX" in blob:
            ticker = "UVIX"
        elif "SVIX" in blob:
            ticker = "SVIX"
        else:
            ticker = "UNASSIGNED"
        rows.append({
            "ticker": ticker,
            "label": text,
            "url": url,
            "quality": "OFFICIAL_VS_DOCUMENT_INDEX",
        })

    z = pd.DataFrame(rows).drop_duplicates(subset=["ticker", "url"])
    z.to_csv(OUT / "volatilityshares_statement_index.csv", index=False)
    (OUT / "volatilityshares_filings_page.html").write_text(r.text, encoding="utf-8")
    return z


def main() -> None:
    ps = backfill_proshares()
    vs = index_volatilityshares_statements()

    assigned = vs[vs["ticker"].isin(["UVIX", "SVIX"])] if len(vs) else vs
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
        {
            "dataset": "volatilityshares_assigned_monthly",
            "rows": len(assigned),
            "tickers": ",".join(sorted(assigned.ticker.astype(str).unique())) if len(assigned) else "",
            "start": "",
            "end": "",
        },
    ])
    summary.to_csv(OUT / "backfill_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
