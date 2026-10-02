#!/usr/bin/env python3
"""Capture the frozen V3 P90 shadow trade on the live IG DFB quote stream.

No order endpoint is called. This process waits for 09:31 New York, captures
entry bid/offer, samples read-only market snapshots roughly once per minute for
MAE, captures 10:00 bid/offer, computes executable shadow P&L, and appends the
canonical forward ledger.
"""
from __future__ import annotations

import csv
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

from ig_dfb_probe import IG, fnum

HERE = Path(__file__).resolve().parent
STATE = HERE / "forward_shadow"
PENDING = STATE / "pending_signal.json"
LEDGER = STATE / "FORWARD_LEDGER.csv"
RAW_DIR = STATE / "raw"
EPIC = "IX.D.NASDAQ.CASH.IP"
NY = ZoneInfo("America/New_York")
START_EQUITY = 2000.0
MARGIN_RATE = 0.05
FIELDS = [
    "signal_date","trade_date","z","abs_z","signal_return","signal_direction","p95","fade_sign",
    "intended_stake","entry_capture_utc","entry_bid","entry_offer","entry_spread",
    "exit_capture_utc","exit_bid","exit_offer","exit_spread","entry_mid","exit_mid",
    "gross_points","gross_bp","net_points","net_bp","pnl_gbp","equity_before","equity_after",
    "margin_gbp","margin_util","mae_bp","samples","missed","reason","qc_backtest_id"
]


def round_stake(x: float) -> float:
    return max(0.01, float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))


def now_ny() -> datetime:
    return datetime.now(NY)


def target_today(hour: int, minute: int, second: int = 5) -> datetime:
    n = now_ny()
    return n.replace(hour=hour, minute=minute, second=second, microsecond=0)


def sleep_until(target: datetime) -> None:
    while True:
        wait = (target - now_ny()).total_seconds()
        if wait <= 0:
            return
        time.sleep(min(wait, 30))


def quote(ig: IG) -> dict:
    d = ig.detail(EPIC)
    snap = d.get("snapshot") or {}
    bid, offer = fnum(snap.get("bid")), fnum(snap.get("offer"))
    status = str(snap.get("marketStatus") or "")
    if bid is None or offer is None or offer <= bid:
        raise RuntimeError(f"Invalid IG quote bid={bid} offer={offer} status={status}")
    return {
        "utc": datetime.now(timezone.utc).isoformat(),
        "ny": now_ny().isoformat(),
        "bid": bid, "offer": offer, "mid": (bid + offer) / 2.0,
        "spread": offer - bid, "status": status,
    }


def read_rows() -> list[dict]:
    if not LEDGER.exists():
        return []
    with LEDGER.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def equity_before(rows: list[dict]) -> float:
    eq = START_EQUITY
    for r in rows:
        if str(r.get("missed", "")).lower() in {"true","1"}:
            continue
        v = r.get("equity_after")
        if v not in (None, ""):
            eq = float(v)
    return eq


def write_row(row: dict) -> None:
    rows = read_rows()
    # Idempotent on trade date: replace rather than duplicate.
    rows = [r for r in rows if r.get("trade_date") != row["trade_date"]]
    rows.append({k: row.get(k, "") for k in FIELDS})
    rows.sort(key=lambda r: r["trade_date"])
    with LEDGER.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)


def mark_missed(p: dict, reason: str) -> None:
    rows = read_rows(); eq = equity_before(rows)
    row = {
        "signal_date":p["signal_date"], "trade_date":p["trade_date"], "z":p["z"],
        "abs_z":p["abs_z"], "signal_return":p["signal_return"],
        "signal_direction":"UP" if p["signal_return"] > 0 else "DOWN",
        "p95":p["p95"], "fade_sign":-1 if p["signal_return"] > 0 else 1,
        "equity_before":eq, "equity_after":eq, "missed":True, "reason":reason,
        "qc_backtest_id":p.get("qc_backtest_id", ""),
    }
    write_row(row)
    PENDING.unlink(missing_ok=True)
    print(f"Recorded missed shadow event {p['trade_date']}: {reason}")


def main() -> None:
    if not PENDING.exists():
        print("No pending P90 signal; nothing to capture.")
        return
    p = json.loads(PENDING.read_text(encoding="utf-8"))
    n = now_ny()
    if n.date().isoformat() != p["trade_date"]:
        print(f"Pending trade is for {p['trade_date']}; NY today is {n.date()}. No action.")
        return
    if n.hour < 9:
        print("Correct date but too early for capture window; exiting wrong-DST trigger.")
        return

    entry_target = target_today(9,31,5)
    exit_target = target_today(10,0,5)
    if n > entry_target + timedelta(seconds=90):
        mark_missed(p, f"ENTRY_CAPTURE_LATE start={n.isoformat()}")
        return
    if n < entry_target:
        sleep_until(entry_target)

    required = ["IG_IDENTIFIER","IG_PASSWORD","IG_API_KEY"]
    missing = [x for x in required if not os.getenv(x)]
    if missing:
        mark_missed(p, "MISSING_IG_SECRETS:" + ",".join(missing))
        return

    ig = IG(os.environ["IG_IDENTIFIER"], os.environ["IG_PASSWORD"],
            os.environ["IG_API_KEY"], os.getenv("IG_ACCOUNT_ID"))
    raw = {"pending":p, "samples":[]}
    try:
        entry = quote(ig); raw["samples"].append(entry)
    except Exception as e:
        mark_missed(p, "ENTRY_QUOTE_ERROR:" + repr(e)); return

    # Sample once per minute for prospective MAE while preserving ample API headroom.
    next_sample = entry_target + timedelta(minutes=1)
    while now_ny() < exit_target:
        if next_sample >= exit_target:
            break
        sleep_until(next_sample)
        try:
            raw["samples"].append(quote(ig))
        except Exception as e:
            raw.setdefault("sample_errors", []).append({"ny":now_ny().isoformat(),"error":repr(e)})
        next_sample += timedelta(minutes=1)
    sleep_until(exit_target)
    try:
        exitq = quote(ig); raw["samples"].append(exitq)
    except Exception as e:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR/f"{p['trade_date']}.json").write_text(json.dumps(raw,indent=2)+"\n")
        mark_missed(p, "EXIT_QUOTE_ERROR:" + repr(e)); return

    rows = read_rows(); eq = equity_before(rows)
    fade = -1 if float(p["signal_return"]) > 0 else 1
    entry_mid, exit_mid = entry["mid"], exitq["mid"]
    gross_points = fade * (exit_mid - entry_mid)
    gross_bp = gross_points / entry_mid * 10000.0
    if fade > 0:  # long: buy offer, sell bid
        net_points = exitq["bid"] - entry["offer"]
    else:         # short: sell bid, buy offer
        net_points = entry["bid"] - exitq["offer"]
    net_bp = net_points / entry_mid * 10000.0
    stake = round_stake(eq / entry_mid)
    pnl = stake * net_points
    margin = stake * entry_mid * MARGIN_RATE
    mids = [float(x["mid"]) for x in raw["samples"] if x.get("mid") is not None]
    path_bp = [fade * (m-entry_mid) / entry_mid * 10000.0 for m in mids]
    mae = min(path_bp) if path_bp else math.nan

    row = {
        "signal_date":p["signal_date"], "trade_date":p["trade_date"], "z":p["z"],
        "abs_z":p["abs_z"], "signal_return":p["signal_return"],
        "signal_direction":"UP" if float(p["signal_return"]) > 0 else "DOWN",
        "p95":bool(p["p95"]), "fade_sign":fade, "intended_stake":stake,
        "entry_capture_utc":entry["utc"], "entry_bid":entry["bid"], "entry_offer":entry["offer"],
        "entry_spread":entry["spread"], "exit_capture_utc":exitq["utc"],
        "exit_bid":exitq["bid"], "exit_offer":exitq["offer"], "exit_spread":exitq["spread"],
        "entry_mid":entry_mid, "exit_mid":exit_mid, "gross_points":gross_points,
        "gross_bp":gross_bp, "net_points":net_points, "net_bp":net_bp,
        "pnl_gbp":pnl, "equity_before":eq, "equity_after":eq+pnl,
        "margin_gbp":margin, "margin_util":margin/eq, "mae_bp":mae,
        "samples":len(raw["samples"]), "missed":False, "reason":"",
        "qc_backtest_id":p.get("qc_backtest_id", ""),
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw["computed"] = row
    (RAW_DIR/f"{p['trade_date']}.json").write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_row(row)
    PENDING.unlink(missing_ok=True)
    print(f"Captured shadow event {p['trade_date']}: net={net_bp:.3f}bp pnl=£{pnl:.2f} equity=£{eq+pnl:.2f}")


if __name__ == "__main__":
    main()