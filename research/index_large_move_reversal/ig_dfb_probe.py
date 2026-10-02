#!/usr/bin/env python3
"""Read-only IG DFB probe for the index morning-fade experiment.

Purpose:
- identify the live-account US Tech 100 DFB and US 500 DFB;
- record account-specific min deal size, live spread and first margin band;
- write machine-readable + human-readable results to this research branch.

Environment:
  IG_IDENTIFIER
  IG_PASSWORD
  IG_API_KEY
Optional:
  IG_ACCOUNT_ID
  IG_BASE_URL (defaults to https://api.ig.com/gateway/deal)

This script calls only session/accounts/markets read endpoints plus account
selection if needed. It never calls a dealing/order endpoint.
"""

from __future__ import annotations

import csv
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "IG_DFB_PROBE_LATEST.csv"
OUT_MD = HERE / "IG_DFB_PROBE_LATEST.md"
BASE = os.getenv("IG_BASE_URL", "https://api.ig.com/gateway/deal").rstrip("/")
PACE = 2.2

TARGETS = {
    "NDX": ["US Tech 100"],
    "SPX": ["US 500"],
}


def fnum(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def first_margin_pct(detail: Dict[str, Any]) -> Optional[float]:
    inst = detail.get("instrument") or {}
    bands = inst.get("marginDepositBands") or []
    if bands:
        def k(b):
            v = fnum(b.get("min"))
            return v if v is not None else 1e99
        b = sorted(bands, key=k)[0]
        v = fnum(b.get("margin"))
        if v is not None:
            return v
        v = fnum(b.get("marginFactor"))
        if v is not None and str(b.get("marginFactorUnit", "PERCENTAGE")).upper() == "PERCENTAGE":
            return v
    return fnum(inst.get("margin"))


class IG:
    def __init__(self, identifier: str, password: str, api_key: str, account_id: Optional[str]):
        self.s = requests.Session()
        self.api_key = api_key
        self.last = 0.0
        self.common = {
            "X-IG-API-KEY": api_key,
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": "application/json; charset=UTF-8",
        }
        self._login(identifier, password)
        self._select_spreadbet(account_id)

    def _pace(self):
        wait = PACE - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)

    def request(self, method: str, path: str, *, version: int = 1, params=None, body=None):
        self._pace()
        h = dict(self.common)
        h["Version"] = str(version)
        if hasattr(self, "cst"):
            h["CST"] = self.cst
            h["X-SECURITY-TOKEN"] = self.xst
        r = self.s.request(method, BASE + path, headers=h, params=params, json=body, timeout=30)
        self.last = time.monotonic()
        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = r.text[:500]
            raise RuntimeError(f"IG {method} {path} -> {r.status_code}: {detail}")
        return r.json() if r.text.strip() else {}

    def _login(self, identifier: str, password: str):
        h = dict(self.common)
        h["Version"] = "2"
        r = self.s.post(BASE + "/session", headers=h,
                        json={"identifier": identifier, "password": password}, timeout=30)
        self.last = time.monotonic()
        if r.status_code >= 400:
            raise RuntimeError(f"IG login failed {r.status_code}: {r.text[:500]}")
        self.cst = r.headers.get("CST")
        self.xst = r.headers.get("X-SECURITY-TOKEN")
        if not self.cst or not self.xst:
            raise RuntimeError("IG login succeeded but session tokens were missing")
        self.login = r.json()

    def _select_spreadbet(self, requested: Optional[str]):
        data = self.request("GET", "/accounts", version=1)
        accounts = data.get("accounts", [])
        if requested:
            target = next((a for a in accounts if str(a.get("accountId")) == requested), None)
            if target is None:
                raise RuntimeError("Requested IG_ACCOUNT_ID was not returned by /accounts")
        else:
            sb = [a for a in accounts if str(a.get("accountType", "")).upper() == "SPREADBET"]
            target = next((a for a in sb if str(a.get("currency", "")).upper() == "GBP"), None)
            target = target or (sb[0] if sb else None)
        if target is None:
            raise RuntimeError("No spread-bet account was returned by /accounts")
        aid = str(target.get("accountId"))
        current = str(self.login.get("currentAccountId") or self.login.get("accountId") or "")
        if aid != current:
            self.request("PUT", "/session", version=1,
                         body={"accountId": aid, "defaultAccount": False})
        self.account_type = str(target.get("accountType") or "")
        self.account_currency = str(target.get("currency") or "")

    def search(self, term: str) -> List[Dict[str, Any]]:
        return self.request("GET", "/markets", version=1,
                            params={"searchTerm": term}).get("markets", [])

    def detail(self, epic: str) -> Dict[str, Any]:
        return self.request("GET", f"/markets/{quote(epic, safe='')}", version=3)


def row_from_detail(family: str, search_term: str, detail: Dict[str, Any]) -> Dict[str, Any]:
    inst = detail.get("instrument") or {}
    snap = detail.get("snapshot") or {}
    rules = detail.get("dealingRules") or {}
    min_deal = rules.get("minDealSize") or {}
    bid, offer = fnum(snap.get("bid")), fnum(snap.get("offer"))
    spread = (offer - bid) if bid is not None and offer is not None else None
    currencies = inst.get("currencies") or []
    ccy = next((x.get("code") for x in currencies if x.get("isDefault")), None)
    return {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "family": family,
        "search_term": search_term,
        "epic": inst.get("epic") or "",
        "name": inst.get("name") or "",
        "type": inst.get("type") or "",
        "expiry": inst.get("expiry") or "",
        "market_status": snap.get("marketStatus") or "",
        "bid": bid if bid is not None else "",
        "offer": offer if offer is not None else "",
        "spread_points": spread if spread is not None else "",
        "min_deal_size": fnum(min_deal.get("value")) if fnum(min_deal.get("value")) is not None else "",
        "min_deal_unit": min_deal.get("unit") or "",
        "margin_pct_first_band": first_margin_pct(detail) if first_margin_pct(detail) is not None else "",
        "currency": ccy or "",
        "contract_size": inst.get("contractSize") or "",
        "lot_size": inst.get("lotSize") if inst.get("lotSize") is not None else "",
        "one_pip_means": inst.get("onePipMeans") or "",
        "value_of_one_pip": inst.get("valueOfOnePip") or "",
        "controlled_risk_allowed": rules.get("controlledRiskAllowed"),
        "streaming_prices_available": inst.get("streamingPricesAvailable"),
    }


def score(row: Dict[str, Any]) -> tuple:
    expiry = str(row.get("expiry") or "").upper()
    status = str(row.get("market_status") or "").upper()
    name = str(row.get("name") or "").lower()
    fam = row.get("family")
    wanted = "us tech 100" if fam == "NDX" else "us 500"
    return (
        1 if expiry == "DFB" else 0,
        1 if wanted in name else 0,
        1 if status == "TRADEABLE" else 0,
        -len(name),
    )


def main():
    required = ["IG_IDENTIFIER", "IG_PASSWORD", "IG_API_KEY"]
    missing = [x for x in required if not os.getenv(x)]
    if missing:
        raise SystemExit("Missing environment variables: " + ", ".join(missing))

    ig = IG(os.environ["IG_IDENTIFIER"], os.environ["IG_PASSWORD"],
            os.environ["IG_API_KEY"], os.getenv("IG_ACCOUNT_ID"))

    rows: List[Dict[str, Any]] = []
    seen = set()
    for family, terms in TARGETS.items():
        for term in terms:
            markets = ig.search(term)
            # Prefer DFB search results, but keep a few nearby results if IG labels are unusual.
            ranked = sorted(markets, key=lambda m: (
                0 if str(m.get("expiry") or "").upper() == "DFB" else 1,
                0 if str(m.get("instrumentType") or "").upper() == "INDICES" else 1,
                str(m.get("instrumentName") or m.get("name") or ""),
            ))
            for m in ranked[:8]:
                epic = str(m.get("epic") or "")
                if not epic or epic in seen:
                    continue
                seen.add(epic)
                d = ig.detail(epic)
                row = row_from_detail(family, term, d)
                # Keep only index candidates. Include non-DFB nearby rows for auditability.
                if str(row.get("type") or "").upper() == "INDICES":
                    rows.append(row)

    if not rows:
        raise RuntimeError("No index market details were returned")

    fields = list(rows[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    best = {}
    for fam in TARGETS:
        cand = [r for r in rows if r["family"] == fam]
        cand.sort(key=score, reverse=True)
        best[fam] = cand[0] if cand else None

    lines = [
        "# IG DFB live-account probe",
        "",
        f"Checked UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Read-only market/account metadata probe. No dealing/order endpoint was called.",
        "",
        f"Account type: {ig.account_type}",
        f"Account currency: {ig.account_currency}",
        "",
        "## Selected candidates",
        "",
        "| Family | Name | EPIC | Expiry | Status | Bid | Offer | Spread pts | Min deal | Unit | First margin % |",
        "|---|---|---|---|---|---:|---:|---:|---:|---|---:|",
    ]
    for fam in ("NDX", "SPX"):
        r = best.get(fam)
        if not r:
            lines.append(f"| {fam} | NOT FOUND | | | | | | | | | |")
            continue
        lines.append(
            f"| {fam} | {r['name']} | {r['epic']} | {r['expiry']} | {r['market_status']} | "
            f"{r['bid']} | {r['offer']} | {r['spread_points']} | {r['min_deal_size']} | "
            f"{r['min_deal_unit']} | {r['margin_pct_first_band']} |"
        )

    lines += [
        "",
        "## Gate interpretation",
        "",
        "- The NDX row must be the US Tech 100 DFB (expiry DFB) to settle the implementation question.",
        "- If min deal is 0.01 POINTS on that DFB, use the small-stake scenario as executable.",
        "- If min deal is 1 POINTS (or larger), the public-minimum scenario remains the executable case.",
        "- The full CSV retains nearby index candidates for auditability.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(OUT_MD.read_text(encoding="utf-8"))
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
