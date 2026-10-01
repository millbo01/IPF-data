#!/usr/bin/env python3
"""Holdout-exact economic simulator for MAIN -> IG Expanded v1.

Consumes the point-in-time target ledger from `main_ig_ledger.py`. It does not generate
signals or select markets. Net T1/F/Dip exposure is converted to one IG stake and rounded
once to £0.01/point.

Required ledger columns: date,ticker,frac,raw,r,lead
Required config columns: ticker,ig_name,epic,transform,scale,spread_points,margin_pct
Optional benchmark columns: date,unrounded_main_return,ig22_return_1x,es_return
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

START_EQUITY = 2000.0
STEP = Decimal("0.01")
SQ252 = math.sqrt(252.0)
HOLD_START = pd.Timestamp("2019-01-01")
FREEZE = pd.Timestamp("2026-09-29")


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
        return self.scale * raw if self.transform == "LINEAR" else self.scale / raw

    def point_change(self, raw: float, r: float) -> float:
        if not (math.isfinite(raw) and raw > 0 and math.isfinite(r) and r > -1):
            return 0.0
        prev = raw / (1.0 + r)
        if self.transform == "LINEAR":
            return self.scale * (raw - prev)
        return self.scale / raw - self.scale / prev

    @property
    def position_sign(self) -> float:
        return -1.0 if self.transform == "INVERSE" else 1.0


def ff(x, default=0.0):
    try:
        v = float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default


def round_stake(x: float) -> float:
    if not math.isfinite(x) or abs(x) < 0.01 - 1e-12:
        return 0.0
    q = Decimal(str(abs(x))).quantize(STEP, rounding=ROUND_HALF_UP)
    return float(q) * (1.0 if x >= 0 else -1.0)


def load_config(path: Path) -> Dict[str, Market]:
    out = {}
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tk = r["ticker"].strip().upper()
            m = Market(tk, r.get("ig_name", "").strip(), r.get("epic", "").strip(),
                       r["transform"].strip().upper(), float(r["scale"]),
                       float(r["spread_points"]), float(r["margin_pct"]),
                       r.get("family", "").strip())
            if m.transform not in {"LINEAR", "INVERSE"} or m.scale <= 0 or m.spread < 0 or m.margin_pct <= 0:
                raise ValueError(f"Bad config row: {r}")
            out[tk] = m
    return out


def slice_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    if period == "build":
        return df[(df.date >= pd.Timestamp("2010-01-01")) & (df.date <= pd.Timestamp("2018-12-31"))].copy()
    if period == "holdout":
        return df[(df.date >= HOLD_START) & (df.date <= FREEZE)].copy()
    if period == "full":
        return df[(df.date >= pd.Timestamp("2010-01-01")) & (df.date <= FREEZE)].copy()
    raise ValueError(period)


def max_dd(values: Sequence[float]) -> float:
    a = np.asarray(values, float)
    if not len(a):
        return float("nan")
    return float(np.min(a / np.maximum.accumulate(a) - 1.0))


def stats(df: pd.DataFrame, period: str) -> dict:
    z = slice_period(df, period)
    if z.empty:
        return {"days": 0}
    r = z["return"].to_numpy(float)
    sd = np.std(r, ddof=1) if len(r) > 1 else float("nan")
    vol = sd * SQ252 if math.isfinite(sd) else float("nan")
    sh = np.mean(r) / sd * SQ252 if math.isfinite(sd) and sd > 0 else float("nan")
    years = max((z.date.iloc[-1] - z.date.iloc[0]).days / 365.2425, 1 / 252)
    e0, e1 = float(z.equity_start.iloc[0]), float(z.equity.iloc[-1])
    return {
        "days": int(len(z)),
        "annualized_mean_return": float(np.mean(r) * 252),
        "cagr": float((e1 / e0) ** (1 / years) - 1) if e0 > 0 and e1 > 0 else float("nan"),
        "annualized_volatility": float(vol),
        "sharpe": float(sh),
        "max_drawdown": max_dd(z.equity.tolist()),
        "ending_equity": e1,
        "spread_cost": float(z.spread_cost.sum()),
        "roll_cost": float(z.roll_cost.sum()),
        "turnover_abs_stake": float(z.turnover_abs_stake.sum()),
        "rounded_zero_fraction": float(z.rounded_zero_count.sum() / max(1, z.desired_nonzero_count.sum())),
        "rounded_gt25pct_fraction": float(z.rounded_gt25_count.sum() / max(1, z.desired_nonzero_count.sum())),
        "max_margin_utilization": float(z.margin_utilization.max()),
        "p95_margin_utilization": float(z.margin_utilization.quantile(.95)),
        "max_concurrent_positions": int(z.positions.max()),
    }


def simulate(ledger: pd.DataFrame, markets: Dict[str, Market], cost_mult: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    x = ledger.copy()
    x["date"] = pd.to_datetime(x["date"])
    x["ticker"] = x["ticker"].astype(str).str.upper()
    x = x.sort_values(["date", "ticker"])
    missing = sorted(set(x.ticker) - set(markets))
    if missing:
        raise ValueError("Missing config: " + ",".join(missing))

    equity = START_EQUITY
    stakes = defaultdict(float)
    leads = {}
    daily, mdaily = [], []

    for d, g in x.groupby("date", sort=True):
        start_eq = equity
        gross = {}
        for _, r in g.iterrows():
            tk = r.ticker
            m = markets[tk]
            gross[tk] = stakes[tk] * m.point_change(ff(r.raw, float("nan")), ff(r.r, 0.0))
        equity += sum(gross.values())

        cost = roll_cost = turn = margin = 0.0
        nonzero = rz = r25 = positions = 0
        for _, r in g.iterrows():
            tk = r.ticker
            m = markets[tk]
            raw = ff(r.raw, float("nan"))
            if not (math.isfinite(raw) and raw > 0):
                continue
            level = m.level(raw)
            desired = m.position_sign * ff(r.frac, 0.0) * equity / level
            target = round_stake(desired)
            prev = stakes[tk]
            lead = str(getattr(r, "lead", "") or "")
            rolled = bool(leads.get(tk)) and bool(lead) and lead != leads[tk]

            if abs(desired) > 1e-15:
                nonzero += 1
                if target == 0:
                    rz += 1
                elif abs(target - desired) / abs(desired) > .25:
                    r25 += 1

            if rolled:
                c = .5 * m.spread * (abs(prev) + abs(target)) * cost_mult
                rc = c
                tr = abs(prev) + abs(target)
            else:
                c = .5 * m.spread * abs(target - prev) * cost_mult
                rc = 0.0
                tr = abs(target - prev)
            cost += c; roll_cost += rc; turn += tr
            mdaily.append({"date": d, "ticker": tk, "family": m.family, "ig_name": m.ig_name,
                           "gross_pnl": gross.get(tk, 0.0), "spread_cost": c, "roll_cost": rc,
                           "net_pnl": gross.get(tk, 0.0) - c, "desired_stake": desired,
                           "target_stake": target, "turnover_abs_stake": tr})
            stakes[tk] = target
            if lead:
                leads[tk] = lead
            if target:
                positions += 1
                margin += abs(target * level) * m.margin_pct / 100.0

        equity -= cost
        daily.append({"date": d, "equity_start": start_eq, "gross_pnl": sum(gross.values()),
                      "spread_cost": cost, "roll_cost": roll_cost, "net_pnl": equity - start_eq,
                      "return": equity / start_eq - 1 if start_eq else 0.0, "equity": equity,
                      "turnover_abs_stake": turn, "margin": margin,
                      "margin_utilization": margin / equity if equity > 0 else float("inf"),
                      "positions": positions, "desired_nonzero_count": nonzero,
                      "rounded_zero_count": rz, "rounded_gt25_count": r25})

    ddf = pd.DataFrame(daily)
    mdf = pd.DataFrame(mdaily)
    blocks = []
    if not mdf.empty:
        for p in ("build", "holdout", "full"):
            q = slice_period(mdf, p)
            if not q.empty:
                a = q.groupby(["ticker", "family", "ig_name"], dropna=False)[
                    ["gross_pnl", "spread_cost", "roll_cost", "net_pnl", "turnover_abs_stake"]
                ].sum().reset_index()
                a.insert(0, "period", p)
                blocks.append(a)
    return ddf, pd.concat(blocks, ignore_index=True) if blocks else pd.DataFrame()


def monthly(s: pd.Series) -> pd.Series:
    return (1 + s).resample("ME").prod() - 1


def sharpe(s: pd.Series) -> float:
    a = s.dropna().to_numpy(float)
    if len(a) < 2:
        return float("nan")
    sd = np.std(a, ddof=1)
    return float(np.mean(a) / sd * SQ252) if sd > 0 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=Path("ig_translation_results"))
    ap.add_argument("--benchmark", type=Path, help="date,unrounded_main_return,ig22_return_1x,es_return")
    args = ap.parse_args()

    markets = load_config(args.config)
    ledger = pd.read_csv(args.ledger)
    ledger["ticker"] = ledger.ticker.astype(str).str.upper()
    ledger = ledger[ledger.ticker.isin(markets)].copy()  # transform failures are pre-P&L exclusions
    args.out.mkdir(parents=True, exist_ok=True)

    summaries, sims, contribs = {}, {}, {}
    for mult, label in ((1., "1x"), (2., "2x")):
        d, c = simulate(ledger, markets, mult)
        sims[label], contribs[label] = d, c
        d.to_csv(args.out / f"daily_{label}.csv", index=False)
        c.to_csv(args.out / f"market_contrib_{label}.csv", index=False)
        summaries[label] = {p: stats(d, p) for p in ("build", "holdout", "full")}

    corr, es_cmp, ig22_sh = {}, None, None
    if args.benchmark:
        b = pd.read_csv(args.benchmark)
        b.date = pd.to_datetime(b.date)
        b = b.set_index("date").sort_index()
        ex = sims["1x"].set_index("date")["return"]
        ex = ex[(ex.index >= HOLD_START) & (ex.index <= FREEZE)]
        for col in ("unrounded_main_return", "ig22_return_1x"):
            if col in b:
                by = b.loc[(b.index >= HOLD_START) & (b.index <= FREEZE), col].dropna()
                q = pd.concat([monthly(ex).rename("x"), monthly(by).rename("y")], axis=1).dropna()
                corr[col] = float(q.corr().iloc[0, 1]) if len(q) > 1 else float("nan")
        if "ig22_return_1x" in b:
            ig22_sh = sharpe(b.loc[(b.index >= HOLD_START) & (b.index <= FREEZE), "ig22_return_1x"])
        if "es_return" in b:
            es = b.loc[(b.index >= HOLD_START) & (b.index <= FREEZE), "es_return"].dropna()
            ix = ex.index.intersection(es.index)
            if len(ix) > 1:
                xr, er = ex.loc[ix].to_numpy(float), es.loc[ix].to_numpy(float)
                xv, ev = np.std(xr, ddof=1)*SQ252, np.std(er, ddof=1)*SQ252
                es_cmp = {"expanded_return_per_vol": float(np.mean(xr)*252/xv) if xv else float("nan"),
                          "es_return_per_vol": float(np.mean(er)*252/ev) if ev else float("nan")}

    h1, h2 = summaries["1x"]["holdout"], summaries["2x"]["holdout"]
    hc = contribs["1x"]
    hc = hc[hc.period == "holdout"] if not hc.empty else pd.DataFrame()
    pos = hc.loc[hc.net_pnl > 0, "net_pnl"] if not hc.empty else pd.Series(dtype=float)
    concentration = float(pos.max()/pos.sum()) if len(pos) and pos.sum() > 0 else float("nan")

    gate = {
        "1x_sharpe_ge_0_50": h1.get("sharpe", -999) >= .50,
        "2x_sharpe_ge_0_40": h2.get("sharpe", -999) >= .40,
        "1x_return_positive": h1.get("annualized_mean_return", -999) > 0,
        "2x_return_positive": h2.get("annualized_mean_return", -999) > 0,
        "1x_max_dd_ge_minus_20pct": h1.get("max_drawdown", -999) >= -.20,
        "max_margin_lt_100pct": h1.get("max_margin_utilization", 999) < 1.0,
        "single_market_positive_contribution_le_40pct": math.isfinite(concentration) and concentration <= .40,
    }
    if "unrounded_main_return" in corr:
        gate["monthly_corr_unrounded_main_ge_0_60"] = corr["unrounded_main_return"] >= .60
    if es_cmp:
        gate["return_per_vol_gt_es"] = es_cmp["expanded_return_per_vol"] > es_cmp["es_return_per_vol"]
    if ig22_sh is not None and math.isfinite(ig22_sh):
        gate["sharpe_not_gt_0_10_below_ig22"] = h1.get("sharpe", -999) >= ig22_sh - .10

    required = {"1x_sharpe_ge_0_50", "2x_sharpe_ge_0_40", "1x_return_positive", "2x_return_positive",
                "1x_max_dd_ge_minus_20pct", "max_margin_lt_100pct",
                "single_market_positive_contribution_le_40pct", "monthly_corr_unrounded_main_ge_0_60",
                "return_per_vol_gt_es", "sharpe_not_gt_0_10_below_ig22"}
    missing = sorted(required - set(gate))
    result = {"starting_equity": START_EQUITY, "market_count": len(markets), "summaries": summaries,
              "holdout_monthly_correlations": corr, "original22_holdout_sharpe": ig22_sh,
              "es_comparison": es_cmp, "holdout_positive_pnl_concentration": concentration,
              "gate": gate, "missing_gate_inputs": missing, "gate_complete": not missing,
              "pass_to_demo_paper_trading": bool(not missing and all(gate[k] for k in required))}
    (args.out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=True), encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
