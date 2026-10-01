#!/usr/bin/env python3
"""Combine the two outcome-blind censuses into the exact Expanded-v1 source universe.

Inputs:
  EXPANDED_V1_EXPOSURES.csv       frozen exposure/fallback list
  ig_expanded_census.csv          authenticated IG census
  main_ig_source_census.csv       decompressed QuantConnect source-data census

Outputs:
  expanded_tickers.txt            direct `tickers` parameter for main_ig_ledger.py
  expanded_admitted.csv
  expanded_excluded.csv

No strategy P&L or return statistics are read.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Sequence

HERE = Path(__file__).resolve().parent


def read(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path: Path, rows: Sequence[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=Path, default=HERE / "EXPANDED_V1_EXPOSURES.csv")
    ap.add_argument("--ig-census", type=Path, default=HERE / "ig_expanded_census.csv")
    ap.add_argument("--source-census", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=HERE)
    a = ap.parse_args()

    seed = read(a.seed)
    ig = {r["exposure_id"].strip(): r for r in read(a.ig_census)
          if r.get("exposure_id") and str(r.get("eligible_live", "1")) != "0"}
    src = {r["ticker"].strip().upper(): str(r.get("source_data_ok", "0")).strip() == "1"
           for r in read(a.source_census) if r.get("ticker")}

    admitted, excluded = [], []
    for s in seed:
        exp = s["exposure_id"].strip()
        bench = str(s.get("benchmark22", "0")).strip() == "1"
        candidates = [x.strip().upper() for x in s["qc_candidates"].split("|") if x.strip()]
        tk = next((x for x in candidates if src.get(x, False)), "")
        if not tk:
            excluded.append({**s, "reason": "SOURCE_DATA_FAIL_ALL_ORDERED_ROOTS"})
            continue
        live = ig.get(exp)
        if bench:
            admitted.append({**s, "ticker": tk, "mapping_source": "FROZEN_22_CONFIG",
                             "epic": (live or {}).get("epic", ""), "ig_name": (live or {}).get("ig_name", "")})
        elif live:
            admitted.append({**s, "ticker": tk, "mapping_source": "EXPANDED_LIVE_CENSUS",
                             "epic": live.get("epic", ""), "ig_name": live.get("ig_name", ""),
                             "spread_points": live.get("spread_points", ""),
                             "margin_pct_first_band": live.get("margin_pct_first_band", ""),
                             "expiry": live.get("expiry", ""),
                             "last_dealing_date": live.get("last_dealing_date", "")})
        else:
            excluded.append({**s, "ticker": tk, "reason": "IG_NOT_ADMITTED_BY_LIVE_CENSUS"})

    # Exposure IDs already remove economic duplicates. Reject only accidental duplicate source roots.
    final, roots, seen = [], [], set()
    for r in admitted:
        if r["ticker"] in seen:
            excluded.append({**r, "reason": "DUPLICATE_QC_ROOT_AFTER_RESOLUTION"}); continue
        seen.add(r["ticker"]); roots.append(r["ticker"]); final.append(r)

    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / "expanded_tickers.txt").write_text(",".join(roots) + "\n", encoding="utf-8")
    write(a.out_dir / "expanded_admitted.csv", final)
    write(a.out_dir / "expanded_excluded.csv", excluded)
    print(f"Expanded v1 admitted {len(final)} exposures: {sum(str(r.get('benchmark22')) == '1' for r in final)} benchmark + {sum(str(r.get('benchmark22')) != '1' for r in final)} new")
    print("tickers=" + ",".join(roots))
    print(f"Excluded {len(excluded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
