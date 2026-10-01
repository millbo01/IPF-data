from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


OUT_ROOT = Path("data/vix_etp_flow")

PROSHARES_HOLDINGS = "https://accounts.profunds.com/etfdata/psdlyhld.csv"
PROSHARES_NAV = "https://accounts.profunds.com/etfdata/historical_nav.csv"
PROSHARES_TARGETS = {"UVXY", "VIXY", "SVXY"}

VS_PAGES = {
    "UVIX": "https://www.volatilityshares.com/uvix/",
    "SVIX": "https://www.volatilityshares.com/svix/",
}

UA = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; IPF-data research collector; "
        "+https://github.com/millbo01/IPF-data)"
    )
}


def get_text(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r.text


def find_ticker_column(df: pd.DataFrame, tickers: set[str]) -> str:
    best = None
    best_hits = -1
    for c in df.columns:
        vals = df[c].astype(str).str.strip().str.upper()
        hits = int(vals.isin(tickers).sum())
        if hits > best_hits:
            best = c
            best_hits = hits
    if best is None or best_hits <= 0:
        raise RuntimeError("Could not identify ProShares ticker column")
    return best


def collect_proshares(day_dir: Path) -> dict:
    raw = get_text(PROSHARES_HOLDINGS)
    df = pd.read_csv(io.StringIO(raw), dtype=str, keep_default_na=False)

    ticker_col = find_ticker_column(df, PROSHARES_TARGETS)
    tickers = df[ticker_col].astype(str).str.strip().str.upper()
    out = df.loc[tickers.isin(PROSHARES_TARGETS)].copy()
    out.insert(0, "provider", "ProShares")

    if out.empty:
        raise RuntimeError("ProShares target rows were empty")

    out.to_csv(day_dir / "proshares_holdings.csv", index=False)

    # Historical NAV is downloaded once per run but only the relevant rows are retained.
    nav_raw = get_text(PROSHARES_NAV)
    nav = pd.read_csv(io.StringIO(nav_raw), dtype=str, keep_default_na=False)
    nav_ticker_col = find_ticker_column(nav, PROSHARES_TARGETS)
    nav_tickers = nav[nav_ticker_col].astype(str).str.strip().str.upper()
    nav_out = nav.loc[nav_tickers.isin(PROSHARES_TARGETS)].copy()
    nav_out.insert(0, "provider", "ProShares")
    nav_out.to_csv(day_dir / "proshares_nav_history.csv", index=False)

    return {
        "source": PROSHARES_HOLDINGS,
        "rows": int(len(out)),
        "tickers": sorted(set(out[ticker_col].astype(str).str.strip().str.upper())),
        "nav_rows": int(len(nav_out)),
    }


def extract_date(text: str) -> str | None:
    matches = re.findall(r"Data as of\s+(\d{1,2}/\d{1,2}/\d{4})", text, flags=re.I)
    if not matches:
        return None
    # The final 'Data as of' near holdings is normally the holdings date.
    return matches[-1]


def normalize_name(x: object) -> str:
    return re.sub(r"\s+", " ", str(x)).strip()


def collect_vs_product(ticker: str, url: str) -> tuple[pd.DataFrame, dict]:
    html = get_text(url)
    tables = pd.read_html(io.StringIO(html))

    holdings = None
    pricing = None

    for t in tables:
        cols = [normalize_name(c).lower() for c in t.columns]
        if any("description" == c for c in cols) and any("shares/contracts" in c for c in cols):
            holdings = t.copy()
        # Product pages usually expose a 2-column Fund Data & Pricing table.
        vals = " ".join(normalize_name(x) for x in t.astype(str).values.flatten())
        if "Net Assets" in vals and "Shares Outstanding" in vals:
            pricing = t.copy()

    if holdings is None:
        raise RuntimeError(f"{ticker}: holdings table not found")

    holdings.columns = [normalize_name(c) for c in holdings.columns]
    holdings.insert(0, "ticker", ticker)
    holdings.insert(0, "provider", "Volatility Shares")
    holdings["source_url"] = url
    holdings["source_holdings_date"] = extract_date(re.sub(r"<[^>]+>", " ", html)) or ""

    meta = {
        "ticker": ticker,
        "source": url,
        "holdings_rows": int(len(holdings)),
        "source_holdings_date": holdings["source_holdings_date"].iloc[0],
    }

    if pricing is not None:
        # Preserve raw pricing table separately in normalized long form.
        pricing.columns = [normalize_name(c) for c in pricing.columns]
        pricing.insert(0, "ticker", ticker)
        pricing.insert(0, "provider", "Volatility Shares")
        meta["pricing_rows"] = int(len(pricing))
    else:
        pricing = pd.DataFrame()
        meta["pricing_rows"] = 0

    return holdings, {"meta": meta, "pricing": pricing}


def collect_volatilityshares(day_dir: Path) -> dict:
    hold_frames = []
    price_frames = []
    product_meta = []

    for ticker, url in VS_PAGES.items():
        holdings, payload = collect_vs_product(ticker, url)
        hold_frames.append(holdings)
        if not payload["pricing"].empty:
            price_frames.append(payload["pricing"])
        product_meta.append(payload["meta"])

    all_holdings = pd.concat(hold_frames, ignore_index=True, sort=False)
    all_holdings.to_csv(day_dir / "volatilityshares_holdings.csv", index=False)

    if price_frames:
        all_pricing = pd.concat(price_frames, ignore_index=True, sort=False)
        all_pricing.to_csv(day_dir / "volatilityshares_pricing.csv", index=False)

    return {
        "products": product_meta,
        "holdings_rows": int(len(all_holdings)),
    }


def main() -> None:
    now = datetime.now(timezone.utc)
    snapshot_date = now.date().isoformat()
    day_dir = OUT_ROOT / snapshot_date
    day_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "snapshot_utc": now.isoformat(),
        "snapshot_date": snapshot_date,
        "purpose": "Prospective public-data archive for VIX ETP mechanical-flow research",
    }

    errors = []

    try:
        manifest["proshares"] = collect_proshares(day_dir)
    except Exception as exc:
        errors.append(f"ProShares: {type(exc).__name__}: {exc}")

    try:
        manifest["volatilityshares"] = collect_volatilityshares(day_dir)
    except Exception as exc:
        errors.append(f"VolatilityShares: {type(exc).__name__}: {exc}")

    manifest["errors"] = errors
    (day_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Require at least one provider to succeed. A partial failure is recorded in the manifest
    # so the action can still archive available public data without silently losing the day.
    if "proshares" not in manifest and "volatilityshares" not in manifest:
        raise RuntimeError("All VIX ETP public-data sources failed: " + " | ".join(errors))

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
