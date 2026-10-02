#!/usr/bin/env python3
"""Run the frozen forward-signal QuantConnect project via QC Cloud API.

This script is intended for GitHub Actions. It creates/reuses a dedicated QC
project, syncs qc_forward_signal.py into main.py, compiles it, runs a backtest
through the current New York date, reads only the compact FORWARD_SIGNAL log
line, and updates the repository forward-shadow state.

Required env:
  QC_USER_ID
  QC_API_TOKEN
Optional:
  QC_ORGANIZATION_ID
  QC_PROJECT_NAME (default: IPF NDX Forward Shadow)

No trading/live-deployment endpoint is called.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
QC_CODE = HERE / "qc_forward_signal.py"
STATE = HERE / "forward_shadow"
LATEST = STATE / "latest_signal.json"
PENDING = STATE / "pending_signal.json"
HISTORY = STATE / "signal_history.csv"
BASE = "https://www.quantconnect.com/api/v2"
PROJECT_NAME = os.getenv("QC_PROJECT_NAME", "IPF NDX Forward Shadow")
NY = ZoneInfo("America/New_York")


def auth_headers() -> Dict[str, str]:
    user_id = os.environ["QC_USER_ID"]
    token = os.environ["QC_API_TOKEN"]
    ts = str(int(time.time()))
    digest = hashlib.sha256(f"{token}:{ts}".encode()).hexdigest()
    raw = base64.b64encode(f"{user_id}:{digest}".encode()).decode("ascii")
    return {"Authorization": f"Basic {raw}", "Timestamp": ts}


def post(path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    r = requests.post(
        BASE + path,
        headers=auth_headers(),
        json=payload or {},
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"QC {path} -> {r.status_code}: {r.text[:1000]}")
    out = r.json()
    if out.get("success") is False:
        raise RuntimeError(f"QC {path} failed: {out.get('errors') or out}")
    return out


def get_or_create_project() -> int:
    out = post("/projects/read")
    matches = [p for p in out.get("projects", []) if p.get("name") == PROJECT_NAME]
    if matches:
        return int(matches[0]["projectId"])
    payload = {"name": PROJECT_NAME, "language": "Py"}
    org = os.getenv("QC_ORGANIZATION_ID")
    if org:
        payload["organizationId"] = org
    out = post("/projects/create", payload)
    return int(out["projects"][0]["projectId"])


def upsert_main(project_id: int, content: str) -> None:
    out = post("/files/read", {"projectId": project_id})
    names = {f.get("name") for f in out.get("files", [])}
    payload = {
        "projectId": project_id,
        "name": "main.py",
        "content": content,
        "codeSourceId": "IPF GitHub Forward Shadow",
    }
    if "main.py" in names:
        post("/files/update", payload)
    else:
        post("/files/create", payload)


def compile_project(project_id: int) -> str:
    out = post("/compile/create", {"projectId": project_id})
    cid = out["compileId"]
    deadline = time.time() + 300
    while time.time() < deadline:
        q = post("/compile/read", {"projectId": project_id, "compileId": cid})
        state = q.get("state")
        if state == "BuildSuccess":
            return cid
        if state == "BuildError":
            raise RuntimeError(f"QC compile error: {q}")
        time.sleep(3)
    raise TimeoutError("QC compilation did not finish within 5 minutes")


def run_backtest(project_id: int, compile_id: str, end_date: str) -> str:
    out = post("/backtests/create", {
        "projectId": project_id,
        "compileId": compile_id,
        "backtestName": f"IPF forward signal {end_date} {int(time.time())}",
        "parameters": {"END_DATE": end_date},
    })
    bid = out["backtest"]["backtestId"]
    deadline = time.time() + 900
    while time.time() < deadline:
        q = post("/backtests/read", {"projectId": project_id, "backtestId": bid})
        b = q.get("backtest") or {}
        if b.get("completed") is True or float(b.get("progress") or 0) >= 1.0:
            return bid
        if b.get("error") or b.get("stacktrace"):
            raise RuntimeError(f"QC backtest error: {b.get('error') or b.get('stacktrace')}")
        time.sleep(5)
    raise TimeoutError("QC backtest did not finish within 15 minutes")


def read_signal_line(project_id: int, backtest_id: str) -> str:
    # Query narrows the tiny log to the derived signal line only.
    out = post("/backtests/read/log", {
        "projectId": project_id,
        "backtestId": backtest_id,
        "start": 0,
        "end": 200,
        "query": "FORWARD_SIGNAL,",
    })
    lines = out.get("logs") or out.get("log") or []
    if isinstance(lines, str):
        lines = lines.splitlines()
    for line in reversed(lines):
        if "FORWARD_SIGNAL," in line:
            return line[line.index("FORWARD_SIGNAL,"):]
    raise RuntimeError(f"FORWARD_SIGNAL line not found in QC logs: {out}")


def parse_signal(line: str) -> Dict[str, Any]:
    if not line.startswith("FORWARD_SIGNAL,"):
        raise ValueError(line)
    out: Dict[str, Any] = {}
    for piece in line.split(",")[1:]:
        if "=" not in piece:
            continue
        k, v = piece.split("=", 1)
        out[k] = v
    return {
        "signal_date": out["signalDate"],
        "z": float(out["z"]),
        "abs_z": float(out["absZ"]),
        "signal_return": float(out["signalRet"]),
        "p90": bool(int(out["p90"])),
        "p95": bool(int(out["p95"])),
        "qqq_1545": float(out["proxy1545"]),
        "qqq_prev_close": float(out["prevClose"]),
        "rolling_mean": float(out["rollingMean"]),
        "rolling_sd": float(out["rollingSd"]),
        "rolling_rows": int(out["rows"]),
    }


def next_xnys_session(signal_date: str) -> str:
    cal = xcals.get_calendar("XNYS")
    d = pd.Timestamp(signal_date)
    sessions = cal.sessions_in_range(d + pd.Timedelta(days=1), d + pd.Timedelta(days=10))
    if len(sessions) == 0:
        raise RuntimeError("No next XNYS session found")
    return str(sessions[0].date())


def append_history(signal: Dict[str, Any]) -> None:
    fields = [
        "signal_date", "trade_date", "z", "abs_z", "signal_return", "p90", "p95",
        "qqq_1545", "qqq_prev_close", "rolling_mean", "rolling_sd", "rolling_rows",
        "qc_project_id", "qc_backtest_id", "recorded_utc",
    ]
    rows = []
    if HISTORY.exists():
        with HISTORY.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    rows = [r for r in rows if r.get("signal_date") != signal["signal_date"]]
    rows.append({k: signal.get(k, "") for k in fields})
    rows.sort(key=lambda r: r["signal_date"])
    with HISTORY.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def main() -> None:
    for key in ("QC_USER_ID", "QC_API_TOKEN"):
        if not os.getenv(key):
            raise SystemExit(f"Missing required environment variable {key}")
    if not QC_CODE.exists():
        raise SystemExit(f"Missing {QC_CODE}")
    STATE.mkdir(parents=True, exist_ok=True)

    now_ny = datetime.now(NY)
    end_date = now_ny.date().isoformat()
    project_id = get_or_create_project()
    upsert_main(project_id, QC_CODE.read_text(encoding="utf-8"))
    compile_id = compile_project(project_id)
    backtest_id = run_backtest(project_id, compile_id, end_date)
    signal = parse_signal(read_signal_line(project_id, backtest_id))
    signal["trade_date"] = next_xnys_session(signal["signal_date"])
    signal["qc_project_id"] = project_id
    signal["qc_backtest_id"] = backtest_id
    signal["recorded_utc"] = datetime.now(timezone.utc).isoformat()
    signal["is_current_ny_session"] = signal["signal_date"] == end_date

    LATEST.write_text(json.dumps(signal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_history(signal)

    # Only arm a trade when today's completed NY session generated a frozen P90 trigger.
    if signal["is_current_ny_session"] and signal["p90"]:
        PENDING.write_text(json.dumps(signal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"ARMED P90 shadow trade for {signal['trade_date']} z={signal['z']:.4f}")
    else:
        print(f"No new P90 trigger. latest={signal['signal_date']} z={signal['z']:.4f}")


if __name__ == "__main__":
    main()