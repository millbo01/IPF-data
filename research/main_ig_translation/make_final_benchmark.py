#!/usr/bin/env python3
"""Merge the original unrounded MAIN/ES series with the 22-market IG translation.

Inputs:
- original-22 QuantConnect benchmark export: date,unrounded_main_return,es_return
- original-22 IG simulator 1x daily output: date,return,...
Output:
- date,unrounded_main_return,ig22_return_1x,es_return

No fitting or selection occurs here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main-benchmark", required=True, type=Path)
    ap.add_argument("--ig22-daily", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("expanded_gate_benchmark.csv"))
    a = ap.parse_args()

    b = pd.read_csv(a.main_benchmark)
    i = pd.read_csv(a.ig22_daily, usecols=["date", "return"]).rename(columns={"return": "ig22_return_1x"})
    b["date"] = pd.to_datetime(b["date"])
    i["date"] = pd.to_datetime(i["date"])
    z = b.merge(i, on="date", how="inner")
    z = z[["date", "unrounded_main_return", "ig22_return_1x", "es_return"]].sort_values("date")
    z.to_csv(a.out, index=False)
    print(f"Wrote {len(z)} matched benchmark days to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
