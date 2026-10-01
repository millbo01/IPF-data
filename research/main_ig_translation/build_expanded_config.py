#!/usr/bin/env python3
"""Build the frozen economic config for MAIN-IG Expanded v1.

Original 22 use FROZEN_22_CONFIG.csv unchanged. New markets use:
- spread and first-band margin from the authenticated live census;
- quote orientation/scale inferred mechanically from overlapping IG daily mid closes and
  source-ledger raw closes, as frozen in EXPANDED_V1_SPEC.md.

No strategy returns or P&L are read by this script.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
POWERS = [10.0 ** k for k in range(-8, 9)]


def read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: List[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def infer_transform(source: pd.Series, ig: pd.Series) -> Tuple[str, float, float, int]:
    q = pd.concat([source.rename("src"), ig.rename("ig")], axis=1).dropna()
    q = q[(q["src"] > 0) & (q["ig"] > 0)]
    if len(q) < 20:
        return "", float("nan"), float("nan"), len(q)

    src = q["src"].to_numpy(float)
    tgt = q["ig"].to_numpy(float)
    best = None
    for kind in ("LINEAR", "INVERSE"):
        base = src if kind == "LINEAR" else 1.0 / src
        for scale in POWERS:
            pred = scale * base
            rel = np.abs(pred / tgt - 1.0)
            err = float(np.median(rel))
            cand = (err, kind, scale)
            if best is None or cand < best:
                best = cand
    assert best is not None
    err, kind, scale = best
    return kind, float(scale), float(err), len(q)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--admitted", type=Path, default=HERE / "expanded_admitted.csv")
    ap.add_argument("--census", type=Path, default=HERE / "ig_expanded_census.csv")
    ap.add_argument("--ig-history", type=Path, default=HERE / "ig_expanded_history.csv")
    ap.add_argument("--ledger", required=True, type=Path, help="expanded QuantConnect ledger CSV (decompressed)")
    ap.add_argument("--frozen22", type=Path, default=HERE / "FROZEN_22_CONFIG.csv")
    ap.add_argument("--out", type=Path, default=HERE / "EXPANDED_V1_CONFIG.csv")
    ap.add_argument("--excluded", type=Path, default=HERE / "expanded_transform_exclusions.csv")
    args = ap.parse_args()

    admitted = read_csv(args.admitted)
    census = {r["exposure_id"]: r for r in read_csv(args.census)}
    frozen_rows = read_csv(args.frozen22)
    frozen = {r["ticker"]: r for r in frozen_rows}

    ledger = pd.read_csv(args.ledger)
    ledger["date"] = pd.to_datetime(ledger["date"]).dt.normalize()
    ledger["raw"] = pd.to_numeric(ledger["raw"], errors="coerce")

    hist = pd.read_csv(args.ig_history)
    hist["date"] = pd.to_datetime(hist["snapshot_time"], errors="coerce").dt.normalize()
    hist["close_mid"] = pd.to_numeric(hist["close_mid"], errors="coerce")

    out: List[dict] = []
    excluded: List[dict] = []

    for a in admitted:
        tk = a["ticker"].strip().upper()
        exp = a["exposure_id"].strip()
        family = a.get("family", "")
        if str(a.get("benchmark22", "0")) == "1":
            if tk not in frozen:
                excluded.append({**a, "reason": "FROZEN_22_CONFIG_MISSING"})
                continue
            r = dict(frozen[tk])
            if not r.get("family"):
                r["family"] = family
            # Fill display identifiers from the census when available, but never alter economics.
            c = census.get(exp, {})
            if not r.get("epic"):
                r["epic"] = c.get("epic", "")
            if not r.get("ig_name"):
                r["ig_name"] = c.get("ig_name", exp)
            r["exposure_id"] = exp
            r["transform_median_rel_error"] = 0.0
            r["transform_overlap_days"] = "FROZEN"
            r["config_source"] = "FROZEN_22_CONFIG"
            out.append(r)
            continue

        c = census.get(exp)
        if c is None:
            excluded.append({**a, "reason": "CENSUS_ROW_MISSING"})
            continue
        epic = c.get("epic", "")
        hs = hist[(hist["exposure_id"] == exp) & (hist["epic"] == epic)].copy()
        ls = ledger[ledger["ticker"] == tk].copy()
        # Use only days for which the source market itself updated. Carry-forward raw levels are
        # intentionally excluded from quote-transform fitting.
        if "updated" in ls.columns:
            ls = ls[pd.to_numeric(ls["updated"], errors="coerce").fillna(0) > 0]
        src = ls.drop_duplicates("date").set_index("date")["raw"]
        igs = hs.dropna(subset=["date"]).drop_duplicates("date").set_index("date")["close_mid"]
        kind, scale, err, n = infer_transform(src, igs)
        if not kind:
            excluded.append({**a, "reason": "TRANSFORM_UNRESOLVED_LT20_OVERLAPS", "overlap_days": n})
            continue
        if not math.isfinite(err) or err > 0.05:
            excluded.append({**a, "reason": "TRANSFORM_UNRESOLVED_GT5PCT_ERROR", "overlap_days": n, "median_rel_error": err, "best_kind": kind, "best_scale": scale})
            continue
        try:
            spread = float(c["spread_points"])
            margin = float(c["margin_pct_first_band"])
        except Exception:
            excluded.append({**a, "reason": "MISSING_FROZEN_IG_ECONOMICS"})
            continue
        out.append({
            "ticker": tk,
            "family": family,
            "exposure_id": exp,
            "ig_name": c.get("ig_name", ""),
            "epic": epic,
            "transform": kind,
            "scale": "%.14g" % scale,
            "spread_points": "%.14g" % spread,
            "margin_pct": "%.14g" % margin,
            "transform_median_rel_error": "%.8g" % err,
            "transform_overlap_days": n,
            "config_source": "EXPANDED_LIVE_CENSUS_AND_LEVEL_FIT",
        })

    write_csv(args.out, out)
    write_csv(args.excluded, excluded)
    print(f"Config: {len(out)} markets; transform exclusions: {len(excluded)}")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
