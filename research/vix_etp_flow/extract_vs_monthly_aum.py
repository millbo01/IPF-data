from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd
import requests
from pypdf import PdfReader

ROOT = Path("data/vix_etp_flow/backfill")
INDEX = ROOT / "volatilityshares_statement_index.csv"
PS = ROOT / "proshares_daily_aum.csv"
OUT_AUM = ROOT / "volatilityshares_monthly_aum.csv"
OUT_MAT = ROOT / "vix_etp_monthly_convexity_materiality.csv"

UA = {"User-Agent": "Mozilla/5.0 (compatible; IPF-data research collector; +https://github.com/millbo01/IPF-data)"}


def money(x: str) -> float:
    s = x.replace("$", "").replace(",", "").replace(" ", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    v = float(s)
    return -v if neg else v


def month_end(label: str) -> pd.Timestamp:
    return pd.Timestamp(pd.to_datetime(label, format="%B %Y")) + pd.offsets.MonthEnd(0)


def extract_text(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=90)
    r.raise_for_status()
    reader = PdfReader(io.BytesIO(r.content))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def parse_end_assets(text: str) -> tuple[float | None, float | None, str]:
    flat = re.sub(r"\s+", " ", text)
    pos = flat.lower().find("end of period")
    if pos < 0:
        return None, None, "NO_END_OF_PERIOD"

    # The official statement table has two columns in fixed order:
    # -1x Short VIX Futures ETF (SVIX), then 2x Long VIX Futures ETF (UVIX).
    window = flat[pos : pos + 500]
    tokens = re.findall(r"\$?\s*\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?", window)

    vals = []
    for t in tokens:
        try:
            v = money(t)
        except Exception:
            continue
        if abs(v) >= 100_000:
            vals.append(v)
        if len(vals) >= 2:
            break

    if len(vals) >= 2:
        return vals[0], vals[1], "OK"

    # Fallback: search specifically inside the NET ASSETS block.
    m = re.search(
        r"NET ASSETS.{0,500}?End of Period.{0,300}",
        flat,
        flags=re.I | re.S,
    )
    if m:
        tokens = re.findall(r"\$?\s*\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?", m.group(0))
        vals = []
        for t in tokens:
            try:
                v = money(t)
            except Exception:
                continue
            if abs(v) >= 100_000:
                vals.append(v)
        if len(vals) >= 2:
            return vals[-2], vals[-1], "OK_FALLBACK"

    return None, None, "PARSE_FAIL"


def build_monthly_aum() -> pd.DataFrame:
    idx = pd.read_csv(INDEX)
    idx = idx[
        (idx["ticker"].eq("SVIX"))
        & (idx["quality"].eq("OFFICIAL_VS_MONTHLY_STATEMENT_INDEX"))
    ].copy()

    rows = []
    for _, r in idx.iterrows():
        label = str(r["label"]).strip()
        url = str(r["url"]).strip()
        try:
            text = extract_text(url)
            svix, uvix, status = parse_end_assets(text)
            flat = re.sub(r"\s+", " ", text)
            p = flat.lower().find("end of period")
            snippet = flat[max(0, p - 120): p + 320] if p >= 0 else flat[:320]
        except Exception as exc:
            svix = uvix = None
            status = f"ERROR_{type(exc).__name__}"
            snippet = str(exc)[:320]

        rows.append({
            "date": month_end(label).date(),
            "label": label,
            "svix_aum": svix,
            "uvix_aum": uvix,
            "parse_status": status,
            "source_url": url,
            "snippet": snippet,
        })

    out = pd.DataFrame(rows).sort_values("date")
    out.to_csv(OUT_AUM, index=False)
    return out


def beta(ticker: str, d: pd.Timestamp) -> float:
    if ticker == "UVXY":
        return 2.0 if d < pd.Timestamp("2018-02-28") else 1.5
    if ticker == "SVXY":
        return -1.0 if d < pd.Timestamp("2018-02-28") else -0.5
    if ticker == "VIXY":
        return 1.0
    raise KeyError(ticker)


def build_materiality(vs: pd.DataFrame) -> pd.DataFrame:
    ps = pd.read_csv(PS)
    ps["date"] = pd.to_datetime(ps["date"])
    ps["ticker"] = ps["ticker"].str.upper()
    ps["aum"] = pd.to_numeric(ps["aum"], errors="coerce")

    rows = []
    good = vs[vs["parse_status"].str.startswith("OK", na=False)].copy()
    for _, r in good.iterrows():
        d = pd.Timestamp(r["date"])

        # Use latest official ProShares observation on or before statement month-end.
        q = ps[ps["date"] <= d]
        if q.empty:
            continue
        last_dates = q.groupby("ticker")["date"].max()
        ps_scale = 0.0
        ps_parts = {}
        for ticker in ("UVXY", "SVXY", "VIXY"):
            if ticker not in last_dates:
                continue
            rr = q[(q["ticker"] == ticker) & (q["date"] == last_dates[ticker])]
            if rr.empty:
                continue
            aum = float(rr.iloc[-1]["aum"])
            b = beta(ticker, d)
            part = b * (b - 1.0) * aum
            ps_parts[ticker] = part
            ps_scale += part

        # UVIX beta=+2 and SVIX beta=-1, so both have beta*(beta-1)=+2.
        vs_scale = 2.0 * float(r["uvix_aum"]) + 2.0 * float(r["svix_aum"])
        total = ps_scale + vs_scale

        rows.append({
            "date": d.date(),
            "svix_aum": float(r["svix_aum"]),
            "uvix_aum": float(r["uvix_aum"]),
            "vs_convexity_scale_usd": vs_scale,
            "proshares_convexity_scale_usd": ps_scale,
            "total_convexity_scale_usd": total,
            "vs_share_total": vs_scale / total if total else None,
            "vs_to_proshares_ratio": vs_scale / ps_scale if ps_scale else None,
            "uvxy_component_usd": ps_parts.get("UVXY"),
            "svxy_component_usd": ps_parts.get("SVXY"),
        })

    out = pd.DataFrame(rows).sort_values("date")
    out.to_csv(OUT_MAT, index=False)
    return out


def main() -> None:
    vs = build_monthly_aum()
    good = vs[vs["parse_status"].str.startswith("OK", na=False)]
    print(
        f"VS monthly statements: total={len(vs)} parsed={len(good)} "
        f"failed={len(vs)-len(good)}"
    )

    mat = build_materiality(vs)
    if len(mat):
        print(
            "Materiality: "
            f"months={len(mat)} "
            f"median_vs_share={mat['vs_share_total'].median():.3f} "
            f"median_vs_to_ps={mat['vs_to_proshares_ratio'].median():.3f} "
            f"max_vs_share={mat['vs_share_total'].max():.3f}"
        )
        print(mat.tail(12).to_string(index=False))
    else:
        print("No materiality rows produced.")


if __name__ == "__main__":
    main()
