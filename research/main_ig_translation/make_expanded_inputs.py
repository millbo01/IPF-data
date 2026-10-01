#!/usr/bin/env python3
"""Build deterministic MAIN-IG Expanded v1 inputs after the live IG census.

This script contains no strategy-performance logic. It:
- keeps all frozen original-22 benchmark mappings;
- admits new exposures only when the live census marked them eligible;
- resolves each exposure to the first ordered QC root in qc_candidates;
- emits the ticker parameter for the QuantConnect ledger exporter;
- emits a new-market mapping table for transform validation.

Source-data validation remains the responsibility of the QuantConnect exporter run. If an
ordered source root fails the frozen source-data rule, rerun this helper with an explicit
SOURCE_DATA_FAILS file so the next ordered root is selected without looking at P&L.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Sequence, Set

HERE = Path(__file__).resolve().parent


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


def load_failures(path: Path | None) -> Set[str]:
    if path is None or not path.exists():
        return set()
    rows = read_csv(path)
    out = set()
    for r in rows:
        root = (r.get("ticker") or r.get("root") or r.get("qc_root") or "").strip().upper()
        reason = (r.get("reason") or "").strip().upper()
        if root and (not reason or "SOURCE_DATA" in reason or "FAIL" in reason):
            out.add(root)
    return out


def first_root(candidates: str, failed: Set[str]) -> str:
    for root in [x.strip().upper() for x in candidates.split("|") if x.strip()]:
        if root not in failed:
            return root
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=Path, default=HERE / "EXPANDED_V1_EXPOSURES.csv")
    ap.add_argument("--census", type=Path, default=HERE / "ig_expanded_census.csv")
    ap.add_argument("--source-data-fails", type=Path, help="optional CSV of roots that failed the frozen source-data rule")
    ap.add_argument("--out-dir", type=Path, default=HERE)
    args = ap.parse_args()

    seed = read_csv(args.seed)
    census = read_csv(args.census) if args.census.exists() else []
    failed = load_failures(args.source_data_fails)
    census_by_exposure: Dict[str, dict] = {
        r["exposure_id"].strip(): r for r in census if r.get("exposure_id") and str(r.get("eligible_live", "1")) != "0"
    }

    admitted: List[dict] = []
    excluded: List[dict] = []
    for s in seed:
        exp = s["exposure_id"].strip()
        bench = str(s.get("benchmark22", "0")).strip() == "1"
        root = first_root(s["qc_candidates"], failed)
        if not root:
            excluded.append({**s, "reason": "SOURCE_DATA_FAIL_ALL_ORDERED_ROOTS"})
            continue

        live = census_by_exposure.get(exp)
        if bench:
            # Amendment 1: original 22 are anchored by the already frozen authenticated mapping.
            admitted.append({
                **s,
                "ticker": root,
                "mapping_source": "FROZEN_22_CONFIG",
                "epic": (live or {}).get("epic", ""),
                "ig_name": (live or {}).get("ig_name", ""),
            })
        elif live is not None:
            admitted.append({
                **s,
                "ticker": root,
                "mapping_source": "EXPANDED_LIVE_CENSUS",
                "epic": live.get("epic", ""),
                "ig_name": live.get("ig_name", ""),
                "spread_points": live.get("spread_points", ""),
                "margin_pct_first_band": live.get("margin_pct_first_band", ""),
                "expiry": live.get("expiry", ""),
                "last_dealing_date": live.get("last_dealing_date", ""),
            })
        else:
            excluded.append({**s, "ticker": root, "reason": "IG_NOT_ADMITTED_BY_LIVE_CENSUS"})

    # Stable seed order is the universe order. There can be only one row per chosen QC root.
    roots = []
    seen = set()
    duplicate_rows = []
    final = []
    for r in admitted:
        tk = r["ticker"]
        if tk in seen:
            duplicate_rows.append({**r, "reason": "DUPLICATE_QC_ROOT_AFTER_EXPOSURE_RESOLUTION"})
            continue
        seen.add(tk)
        roots.append(tk)
        final.append(r)
    excluded.extend(duplicate_rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "expanded_tickers.txt").write_text(",".join(roots) + "\n", encoding="utf-8")
    write_csv(args.out_dir / "expanded_admitted.csv", final)
    write_csv(args.out_dir / "expanded_excluded.csv", excluded)

    print(f"Expanded v1: {len(final)} admitted exposures ({sum(str(r.get('benchmark22')) == '1' for r in final)} benchmark, {sum(str(r.get('benchmark22')) != '1' for r in final)} new)")
    print("QC parameter tickers=" + ",".join(roots))
    print(f"Excluded: {len(excluded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
