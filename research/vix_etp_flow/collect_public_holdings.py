from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


OUT_ROOT = Path("data/vix_etp_flow")

PROSHARES_PAGES = {
    "UVXY": "https://www.proshares.com/our-etfs/strategic/uvxy",
    "VIXY": "https://www.proshares.com/our-etfs/strategic/vixy",
    "SVXY": "https://www.proshares.com/our-etfs/strategic/svxy",
}

VS_PAGES = {
    "UVIX": "https://www.volatilityshares.com/uvix/",
    "SVIX": "https://www.volatilityshares.com/svix/",
}

VS_DOWNLOADS = {
    "UVIX": "https://www.volatilityshares.com/download-holdings-usbanks-1933.php?fund=uvix",
    "SVIX": "https://www.volatilityshares.com/download-holdings-usbanks-1933.php?fund=svix",
}

UA = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; IPF-data research collector; "
        "+https://github.com/millbo01/IPF-data)"
    )
}


def get_response(url: str) -> requests.Response:
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r


def get_text(url: str) -> str:
    return get_response(url).text


def normalize_name(x: object) -> str:
    if isinstance(x, tuple):
        x = " ".join(str(v) for v in x if str(v).lower() != "nan")
    return re.sub(r"\s+", " ", str(x)).strip()


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [normalize_name(c) for c in out.columns]
    return out


def flat_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "lxml")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def parse_money(text: str) -> float | None:
    if not text:
        return None
    x = re.sub(r"[^0-9.\-]", "", text)
    if x in {"", "-", ".", "-."}:
        return None
    try:
        return float(x)
    except ValueError:
        return None


def extract_page_meta(ticker: str, provider: str, raw_html: str) -> dict:
    text = flat_text(raw_html)
    meta: dict = {"ticker": ticker, "provider": provider}

    for p in [
        r"Holdings\s+as of\s+(\d{1,2}/\d{1,2}/\d{4})",
        r"Top Holdings.*?Data as of\s+(\d{1,2}/\d{1,2}/\d{4})",
        r"Data as of\s+(\d{1,2}/\d{1,2}/\d{4})",
    ]:
        m = re.search(p, text, flags=re.I)
        if m:
            meta["holdings_date"] = m.group(1)
            break

    for p in [
        r"Net Assets as of\s+\d{1,2}/\d{1,2}/\d{4}\s+\$?([\d,]+(?:\.\d+)?)",
        r"Net Assets\s+\$?([\d,]+(?:\.\d+)?)",
    ]:
        m = re.search(p, text, flags=re.I)
        if m:
            meta["net_assets"] = parse_money(m.group(1))
            break

    m = re.search(r"\bNAV\s+\$?([\d,]+(?:\.\d+)?)", text, flags=re.I)
    if m:
        meta["nav"] = parse_money(m.group(1))

    m = re.search(r"Shares Outstanding\s+([\d,]+(?:\.\d+)?)", text, flags=re.I)
    if m:
        meta["shares_outstanding"] = parse_money(m.group(1))

    return meta


def table_score(df: pd.DataFrame) -> int:
    cols = " | ".join(normalize_name(c).lower() for c in df.columns)
    vals = " ".join(
        normalize_name(x).lower()
        for x in df.astype(str).head(40).values.flatten()
    )
    text = cols + " " + vals

    score = 0
    if "description" in cols:
        score += 3
    if "shares/contracts" in cols or "shares contracts" in cols:
        score += 3
    if "vix future" in text or "cboe vix future" in text:
        score += 5
    if "market value" in cols or "notional" in cols or "exposure value" in cols:
        score += 2
    return score


def best_holdings_table(raw_html: str) -> pd.DataFrame:
    tables = pd.read_html(io.StringIO(raw_html))
    if not tables:
        raise RuntimeError("No HTML tables found")

    scored = [(table_score(clean_columns(t)), clean_columns(t)) for t in tables]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored or scored[0][0] < 5:
        raise RuntimeError("Holdings table not found")

    return scored[0][1]


def parse_excelish_response(content: bytes) -> pd.DataFrame:
    errors = []

    for engine in (None, "xlrd", "openpyxl"):
        try:
            kwargs = {} if engine is None else {"engine": engine}
            df = pd.read_excel(io.BytesIO(content), **kwargs)
            if len(df.columns) >= 2 and len(df) > 0:
                return clean_columns(df)
        except Exception as exc:
            errors.append(f"read_excel[{engine}]: {type(exc).__name__}")

    text = None
    for enc in ("utf-8-sig", "utf-8", "latin1"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if text:
        try:
            tables = pd.read_html(io.StringIO(text))
            if tables:
                scored = [
                    (table_score(clean_columns(t)), clean_columns(t))
                    for t in tables
                ]
                scored.sort(key=lambda x: x[0], reverse=True)
                if scored[0][0] >= 5:
                    return scored[0][1]
        except Exception as exc:
            errors.append(f"read_html: {type(exc).__name__}")

        for sep in (",", "\t", ";"):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                df = clean_columns(df)
                if table_score(df) >= 5:
                    return df
            except Exception as exc:
                errors.append(f"read_csv[{repr(sep)}]: {type(exc).__name__}")

    raise RuntimeError("Could not parse downloadable holdings: " + ", ".join(errors))


def add_common_columns(
    df: pd.DataFrame,
    provider: str,
    ticker: str,
    source_url: str,
    holdings_date: str | None,
) -> pd.DataFrame:
    out = clean_columns(df)
    out.insert(0, "ticker", ticker)
    out.insert(0, "provider", provider)
    out["source_url"] = source_url
    out["source_holdings_date"] = holdings_date or ""
    return out


def collect_proshares(day_dir: Path) -> dict:
    """Collect each target fund from its official product page.

    The aggregate ProShares CSV has provider-format drift and does not reliably
    expose fund identifiers in a stable table. The public product pages expose
    the exact holdings table we need, so collect each fund independently.
    """
    hold_frames = []
    product_meta = []
    product_errors = []

    for ticker, url in PROSHARES_PAGES.items():
        try:
            page_html = get_text(url)
            meta = extract_page_meta(ticker, "ProShares", page_html)
            meta["source"] = url

            holdings = best_holdings_table(page_html)
            holdings = add_common_columns(
                holdings,
                "ProShares",
                ticker,
                url,
                meta.get("holdings_date"),
            )

            meta["holdings_rows"] = int(len(holdings))
            hold_frames.append(holdings)
            product_meta.append(meta)
        except Exception as exc:
            product_errors.append(f"{ticker}: {type(exc).__name__}: {exc}")

    if not hold_frames:
        raise RuntimeError(
            "No ProShares products succeeded: " + " | ".join(product_errors)
        )

    all_holdings = pd.concat(hold_frames, ignore_index=True, sort=False)
    all_holdings.to_csv(day_dir / "proshares_holdings.csv", index=False)

    pd.DataFrame(product_meta).to_csv(
        day_dir / "proshares_product_meta.csv",
        index=False,
    )

    return {
        "products": product_meta,
        "product_errors": product_errors,
        "holdings_rows": int(len(all_holdings)),
    }


def collect_vs_product(
    ticker: str,
    page_url: str,
    download_url: str,
) -> tuple[pd.DataFrame, dict]:
    page_html = get_text(page_url)
    meta = extract_page_meta(ticker, "Volatility Shares", page_html)
    meta["source"] = page_url

    source_used = download_url

    try:
        r = get_response(download_url)
        holdings = parse_excelish_response(r.content)
    except Exception as download_exc:
        try:
            holdings = best_holdings_table(page_html)
            source_used = page_url
            meta["download_error"] = f"{type(download_exc).__name__}: {download_exc}"
        except Exception as page_exc:
            raise RuntimeError(
                f"{ticker}: download failed ({type(download_exc).__name__}: {download_exc}); "
                f"page fallback failed ({type(page_exc).__name__}: {page_exc})"
            )

    holdings = add_common_columns(
        holdings,
        "Volatility Shares",
        ticker,
        source_used,
        meta.get("holdings_date"),
    )

    meta["holdings_rows"] = int(len(holdings))
    meta["holdings_source"] = source_used

    return holdings, meta


def collect_volatilityshares(day_dir: Path) -> dict:
    hold_frames = []
    product_meta = []
    product_errors = []

    for ticker, page_url in VS_PAGES.items():
        try:
            holdings, meta = collect_vs_product(
                ticker,
                page_url,
                VS_DOWNLOADS[ticker],
            )
            hold_frames.append(holdings)
            product_meta.append(meta)
        except Exception as exc:
            product_errors.append(f"{ticker}: {type(exc).__name__}: {exc}")

    if not hold_frames:
        raise RuntimeError(
            "No Volatility Shares products succeeded: " + " | ".join(product_errors)
        )

    all_holdings = pd.concat(hold_frames, ignore_index=True, sort=False)
    all_holdings.to_csv(day_dir / "volatilityshares_holdings.csv", index=False)

    pd.DataFrame(product_meta).to_csv(
        day_dir / "volatilityshares_product_meta.csv",
        index=False,
    )

    return {
        "products": product_meta,
        "product_errors": product_errors,
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
        "collector_version": 3,
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

    (day_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    if "proshares" not in manifest and "volatilityshares" not in manifest:
        raise RuntimeError(
            "All VIX ETP public-data sources failed: " + " | ".join(errors)
        )

    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
