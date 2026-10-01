#!/usr/bin/env python3
"""Economic simulator for MAIN -> IG translation.

Consumes a point-in-time source ledger exported by the unchanged futures engine plus a
frozen IG market config. It does not generate or retune signals.

Required ledger columns (one row per source market per processed date):
  date,ticker,frac,raw,r,lead
where `frac` is the exact combined MAIN target fraction after T1/F/Dip netting using
that day's frozen-engine live denominators, `raw` is the source lead-contract close,
`r` is the engine's same-contract daily return, and `lead` identifies the source lead.

Required config columns:
  ticker,ig_name,epic,transform,scale,spread_points,margin_pct
`transform` is LINEAR or INVERSE. INVERSE reverses position sign.

Optional ledger columns used for reporting when present:
  family,t1_w,f_w,dip_w,nlive_t1,nlive_f,nlive_dip

Outputs a summary JSON, daily portfolio CSV and market-contribution CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

START_EQUITY = 2000.0
STAKE_STEP = Decimal("0.01")
SQ252 = math.sqrt(252.0)


@dataclass(frozen=True)
class Market:
    ticker: str
    ig_name: str
    epic: str
    transform: str
    scale: float
    spread: float
    margin_pct: float
    family: str = ""

    def level(self, raw: float) -> float:
        if self.transform == "LINEAR":
            return self.scale * raw
        if self.transform == "INVERSE":
            return self.scale / raw
        raise ValueError(f"{self.ticker}: unknown transform {self.transform}")

    def point_change(self, raw: float, r: float) -> float:
        """IG-point change implied by the engine's same-contract source return."""
        if not (math.isfinite(raw) and raw > 0 and math.isfinite(r) and r > -1):
            return 0.0
        prev_raw = raw / (1.0 + r)
        if self.transform == "LINEAR":
            return self.scale * (raw - prev_raw)
        return self.scale / raw - self.scale / prev_raw

    @property
    def sign(self) -> float:
        return -1.0 if self.transform == "INVERSE" else 1.0


def ff(x, default=0.0) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def round_stake(x: float) -> float:
    if not math.isfinite(x) or abs(x) < 0.01 - 1e-12:
        return 0.0
    q = Decimal(str(abs(x))).quantize(STAKE_STEP, rounding=ROUND_HALF_UP)
    return float(q) * (1.0 if x >= 0 else -1.0)


def max_drawdown(equity: Sequence[float]) -> float:
    if not equity:
        return float("nan")
    a = np.asarray(equity, dtype=float)
    peak = np.maximum.accumulate(a)
    return float(np.min(a / peak - 1.0))


def metrics(df: pd.DataFrame, start: str, end: Optional[str] = None) -> Dict[str, float]:
    z = df[df["date"] >= pd.Timestamp(start)].copy()
    if end:
        z = z[z["date"] <= pd.Timestamp(end)]
    if z.empty:
        return {"days": 0}
    r = z["return"].to_numpy(float)
    vol = float(np.std(r, ddof=1) * SQ252) if len(r) > 1 else float("nan")
    ann_mean = float(np.mean(r) * 252.0)
    sharpe = float(np.mean(r) / np.std(r, ddof=1) * SQ252) if len(r) > 1 and np.std(r, ddof=1) > 0 else float("nan")
    years = max((z["date"].iloc[-1] - z["date"].iloc[0]).days / 365.2425, 1 / 252)
    eq0 = float(z["equity_start"].iloc[0])
    eq1 = float(z["equity"].iloc[-1])
    cagr = (eq1 / eq0) ** (1.0 / years) - 1.0 if eq0 > 0 and eq1 > 0 else float("nan")
    return {
        "days": int(len(z)),
        "annualized_mean_return": ann_mean,
        "cagr": float(cagr),
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(z["equity"].tolist()),
        "ending_equity": eq1,
        "spread_cost": float(z["spread_cost"].sum()),
        "roll_cost": float(z["roll_cost"].sum()),
        "turnover_abs_stake": float(z["turnover_abs_stake"].sum()),
        "max_margin_utilization": float(z["margin_utilization"].max()),
        "p95_margin_utilization": float(z["margin_utilization"].quantile(0.95)),
        "max_concurrent_positions": int(z["positions"].max()),
        "rounded_zero_fraction": float(z["rounded_zero_count"].sum() / max(1, z["desired_nonzero_count"].sum())),
        "rounded_gt25pct_fraction": float(z["rounded_gt25_count"].sum() / max(1, z["desired_nonzero_count"].sum())),
    }


def load_config(path: Path) -> Dict[str, Market]:
    out: Dict[str, Market] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tk = r["ticker"].strip()
            m = Market(
                ticker=tk,
                ig_name=r.get("ig_name", "").strip(),
                epic=r.get("epic", "").strip(),
                transform=r["transform"].strip().upper(),
                scale=float(r["scale"]),
                spread=float(r["spread_points"]),
                margin_pct=float(r["margin_pct"]),
                family=r.get("family", "").strip(),
            )
            if m.transform not in {"LINEAR", "INVERSE"} or m.scale <= 0 or m.spread < 0 or m.margin_pct <= 0:
                raise ValueError(f"Bad config row for {tk}: {r}")
            out[tk] = m
    return out


def simulate(ledger: pd.DataFrame, markets: Dict[str, Market], cost_mult: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    ledger = ledger.copy()
    ledger["date"] = pd.to_datetime(ledger["date"])
    ledger = ledger.sort_values(["date", "ticker"])
    missing = sorted(set(ledger["ticker"]) - set(markets))
    if missing:
        raise ValueError("Ledger contains markets missing from IG config: " + ", ".join(missing))

    equity = START_EQUITY
    stakes: Dict[str, float] = defaultdict(float)
    leads: Dict[str, str] = {}
    daily: List[dict] = []
    contrib: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for d, g in ledger.groupby("date", sort=True):
        equity_start = equity
        gross_pnl = 0.0
        market_gross: Dict[str, float] = {}

        # Existing stakes earn today's same-contract source move. This deliberately ignores
        # level gaps between different source contracts on a roll day.
        for _, row in g.iterrows():
            tk = str(row["ticker"])
            m = markets[tk]
            dp = m.point_change(ff(row["raw"], float("nan")), ff(row["r"], 0.0))
            pnl = stakes[tk] * dp
            gross_pnl += pnl
            market_gross[tk] = pnl
            contrib[tk]["gross_pnl"] += pnl

        equity += gross_pnl
        spread_cost = 0.0
        roll_cost = 0.0
        turnover = 0.0
        desired_nonzero = rounded_zero = rounded_gt25 = 0
        margin = 0.0
        positions = 0

        # Re-target after today's source signal is known. Each cost scenario compounds and
        # sizes independently because its equity path is different.
        for _, row in g.iterrows():
            tk = str(row["ticker"])
            m = markets[tk]
            raw = ff(row["raw"], float("nan"))
            if not (math.isfinite(raw) and raw > 0):
                continue
            level = m.level(raw)
            frac = ff(row["frac"], 0.0)
            desired = m.sign * frac * equity / level if level > 0 else 0.0
            target = round_stake(desired)
            prev = stakes[tk]
            lead = str(row.get("lead", ""))
            rolled = bool(leads.get(tk)) and lead and lead != leads[tk]

            if abs(desired) > 1e-15:
                desired_nonzero += 1
                if target == 0:
                    rounded_zero += 1
                elif abs(target - desired) / abs(desired) > 0.25:
                    rounded_gt25 += 1

            if rolled:
                c = 0.5 * m.spread * (abs(prev) + abs(target)) * cost_mult
                roll_cost += c
                turnover += abs(prev) + abs(target)
            else:
                c = 0.5 * m.spread * abs(target - prev) * cost_mult
                turnover += abs(target - prev)
            spread_cost += c
            contrib[tk]["spread_cost"] += c
            contrib[tk]["net_pnl"] += market_gross.get(tk, 0.0) - c
            stakes[tk] = target
            if lead:
                leads[tk] = lead

            if target != 0:
                positions += 1
                margin += abs(target * level) * (m.margin_pct / 100.0)

        equity -= spread_cost
        ret = equity / equity_start - 1.0 if equity_start else 0.0
        daily.append({
            "date": d,
            "equity_start": equity_start,
            "gross_pnl": gross_pnl,
            "spread_cost": spread_cost,
            "roll_cost": roll_cost,
            "net_pnl": equity - equity_start,
            "return": ret,
            "equity": equity,
            "turnover_abs_stake": turnover,
            "margin": margin,
            "margin_utilization": margin / equity if equity > 0 else float("inf"),
            "positions": positions,
            "desired_nonzero_count": desired_nonzero,
            "rounded_zero_count": rounded_zero,
            "rounded_gt25_count": rounded_gt25,
        })

    ddf = pd.DataFrame(daily)
    crows = []
    for tk, vals in sorted(contrib.items()):
        m = markets[tk]
        crows.append({"ticker": tk, "family": m.family, "ig_name": m.ig_name, **vals})
    return ddf, pd.DataFrame(crows)


def monthly_returns(df: pd.DataFrame) -> pd.Series:
    z = df.set_index("date")["return"]
    return (1.0 + z).resample("ME").prod() - 1.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("ig_translation_results"))
    ap.add_argument("--benchmark", type=Path, help="optional daily CSV with date,unrounded_main_return,ig22_return_1x,es_return")
    args = ap.parse_args()

    markets = load_config(args.config)
    ledger = pd.read_csv(args.ledger)
    ledger = ledger[ledger["ticker"].isin(markets)].copy()
    args.out.mkdir(parents=True, exist_ok=True)

    summaries: Dict[str, dict] = {}
    simulated: Dict[str, pd.DataFrame] = {}
    for mult, label in ((1.0, "1x"), (2.0, "2x")):
        ddf, cdf = simulate(ledger, markets, mult)
        simulated[label] = ddf
        ddf.to_csv(args.out / f"daily_{label}.csv", index=False)
        cdf.to_csv(args.out / f"market_contrib_{label}.csv", index=False)
        summaries[label] = {
            "build": metrics(ddf, "2010-01-01", "2018-12-31"),
            "holdout": metrics(ddf, "2019-01-01", "2026-09-29"),
            "full": metrics(ddf, "2010-01-01", "2026-09-29"),
        }

    corr = {}
    es_ratio = None
    if args.benchmark:
        b = pd.read_csv(args.benchmark)
        b["date"] = pd.to_datetime(b["date"])
        b = b.set_index("date").sort_index()
        m1 = monthly_returns(simulated["1x"])
        for col in ("unrounded_main_return", "ig22_return_1x"):
            if col in b:
                bm = (1.0 + b[col]).resample("ME").prod() - 1.0
                q = pd.concat([m1.rename("x"), bm.rename("y")], axis=1).dropna()
                corr[col] = float(q.corr().iloc[0, 1]) if len(q) > 1 else float("nan")
        if "es_return" in b:
            h = b.loc[b.index >= pd.Timestamp("2019-01-01"), "es_return"].dropna()
            x = simulated["1x"].set_index("date").loc[lambda z: z.index >= pd.Timestamp("2019-01-01"), "return"]
            ix = x.index.intersection(h.index)
            if len(ix) > 1:
                xr, er = x.loc[ix].to_numpy(float), h.loc[ix].to_numpy(float)
                xv, ev = np.std(xr, ddof=1) * SQ252, np.std(er, ddof=1) * SQ252
                xret, eret = np.mean(xr) * 252, np.mean(er) * 252
                es_ratio = {
                    "expanded_return_per_vol": float(xret / xv) if xv else float("nan"),
                    "es_return_per_vol": float(eret / ev) if ev else float("nan"),
                }

    hold1 = summaries["1x"]["holdout"]
    hold2 = summaries["2x"]["holdout"]
    c1 = pd.read_csv(args.out / "market_contrib_1x.csv")
    pos = c1.loc[c1["net_pnl"] > 0, "net_pnl"] if not c1.empty else pd.Series(dtype=float)
    concentration = float(pos.max() / pos.sum()) if len(pos) and pos.sum() > 0 else float("nan")
    gate = {
        "1x_sharpe_ge_0_50": bool(hold1.get("sharpe", -999) >= 0.50),
        "2x_sharpe_ge_0_40": bool(hold2.get("sharpe", -999) >= 0.40),
        "1x_return_positive": bool(hold1.get("annualized_mean_return", -999) > 0),
        "2x_return_positive": bool(hold2.get("annualized_mean_return", -999) > 0),
        "1x_max_dd_ge_minus_20pct": bool(hold1.get("max_drawdown", -999) >= -0.20),
        "max_margin_lt_100pct": bool(hold1.get("max_margin_utilization", 999) < 1.0),
        "single_market_positive_contribution_le_40pct": bool(math.isfinite(concentration) and concentration <= 0.40),
    }
    if "unrounded_main_return" in corr:
        gate["monthly_corr_unrounded_main_ge_0_60"] = bool(corr["unrounded_main_return"] >= 0.60)
    if es_ratio:
        gate["return_per_vol_gt_es"] = bool(es_ratio["expanded_return_per_vol"] > es_ratio["es_return_per_vol"])

    result = {
        "starting_equity": START_EQUITY,
        "market_count": len(markets),
        "summaries": summaries,
        "monthly_correlations": corr,
        "es_comparison": es_ratio,
        "positive_pnl_concentration": concentration,
        "gate_partial": gate,
        "pass_partial_gate": all(gate.values()),
        "note": "Expanded-v1 gate item comparing Sharpe to the original 22-market IG translation requires benchmark input or separate comparison.",
    }
    (args.out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=True), encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
