#!/usr/bin/env python3
"""Read-only authenticated IG census for MAIN-IG Expanded v1.

Inputs are environment variables only; credentials are never written to disk:
  IG_IDENTIFIER, IG_PASSWORD, IG_API_KEY
Optional:
  IG_ACCOUNT_ID      exact spread-bet account to activate
  IG_BASE_URL        defaults to https://api.ig.com/gateway/deal
  CENSUS_DATE        YYYY-MM-DD, defaults to current UTC date

The script reads EXPANDED_V1_EXPOSURES.csv beside this file and writes:
  ig_expanded_census.csv
  ig_expanded_exclusions.csv
  ig_expanded_history.csv   (only with --with-history)

No dealing/order endpoint is called.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote

import requests

HERE = Path(__file__).resolve().parent
SEED = HERE / "EXPANDED_V1_EXPOSURES.csv"
BASE = os.getenv("IG_BASE_URL", "https://api.ig.com/gateway/deal").rstrip("/")
PACE_SECONDS = 2.15  # account non-trading allowance is 30/min; keep headroom
VALID_TYPES = {"CURRENCIES", "COMMODITIES", "INDICES", "RATES"}
STOP = {
    "future", "futures", "forward", "cash", "mini", "micro", "e", "index",
    "the", "us", "usd", "cme", "cbot", "nymex", "comex", "ice", "contract",
}


def fnum(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def norm(s: Any) -> str:
    s = str(s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def tokens(s: Any) -> set[str]:
    return {x for x in norm(s).split() if len(x) > 1 and x not in STOP}


def parse_date(s: Any) -> Optional[date]:
    if not s:
        return None
    text = str(s).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%d/%m/%y", "%b-%y"):
        try:
            return datetime.strptime(text[: len(datetime.now().strftime(fmt))], fmt).date()
        except Exception:
            pass
    # IG sometimes appends timezone or uses ISO with Z.
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        return None


@dataclass
class SeedRow:
    exposure_id: str
    family: str
    qc_candidates: str
    search_terms: List[str]
    benchmark22: bool


class IG:
    def __init__(self, identifier: str, password: str, api_key: str, account_id: Optional[str]):
        self.s = requests.Session()
        self.api_key = api_key
        self.account_id = account_id
        self.last_call = 0.0
        self.common = {
            "X-IG-API-KEY": api_key,
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": "application/json; charset=UTF-8",
        }
        self._login(identifier, password)
        self._select_spreadbet_account(account_id)

    def _paced(self) -> None:
        wait = PACE_SECONDS - (time.monotonic() - self.last_call)
        if wait > 0:
            time.sleep(wait)

    def request(self, method: str, path: str, *, version: int = 1, params=None, body=None) -> Dict[str, Any]:
        self._paced()
        h = dict(self.common)
        h["Version"] = str(version)
        if hasattr(self, "cst"):
            h["CST"] = self.cst
            h["X-SECURITY-TOKEN"] = self.xst
        url = BASE + path
        r = self.s.request(method, url, headers=h, params=params, json=body, timeout=30)
        self.last_call = time.monotonic()
        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = r.text[:500]
            raise RuntimeError(f"IG {method} {path} -> {r.status_code}: {detail}")
        if not r.text.strip():
            return {}
        return r.json()

    def _login(self, identifier: str, password: str) -> None:
        # v2 gives stable CST/XST headers and is sufficient for read-only census calls.
        h = dict(self.common)
        h["Version"] = "2"
        r = self.s.post(BASE + "/session", headers=h, json={"identifier": identifier, "password": password}, timeout=30)
        self.last_call = time.monotonic()
        if r.status_code >= 400:
            raise RuntimeError(f"IG login failed {r.status_code}: {r.text[:500]}")
        self.cst = r.headers.get("CST")
        self.xst = r.headers.get("X-SECURITY-TOKEN")
        if not self.cst or not self.xst:
            raise RuntimeError("IG login succeeded but CST/X-SECURITY-TOKEN headers were missing")
        self.login = r.json()

    def _select_spreadbet_account(self, requested: Optional[str]) -> None:
        data = self.request("GET", "/accounts", version=1)
        accounts = data.get("accounts", [])
        target = None
        if requested:
            target = next((a for a in accounts if str(a.get("accountId")) == requested), None)
            if target is None:
                raise RuntimeError(f"IG_ACCOUNT_ID {requested!r} was not returned by /accounts")
        else:
            # Prefer GBP spread-bet account; otherwise any spread-bet account.
            sb = [a for a in accounts if str(a.get("accountType", "")).upper() == "SPREADBET"]
            target = next((a for a in sb if str(a.get("currency", "")).upper() == "GBP"), None) or (sb[0] if sb else None)
        if target is None:
            raise RuntimeError("No SPREADBET account was returned by /accounts")
        aid = str(target.get("accountId"))
        self.account = target
        if aid != str(self.login.get("currentAccountId") or self.login.get("accountId") or ""):
            self.request("PUT", "/session", version=1, body={"accountId": aid, "defaultAccount": False})
        self.account_id = aid

    def search(self, term: str) -> List[Dict[str, Any]]:
        return self.request("GET", "/markets", version=1, params={"searchTerm": term}).get("markets", [])

    def detail(self, epic: str) -> Dict[str, Any]:
        return self.request("GET", f"/markets/{quote(epic, safe='')}", version=3)

    def prices(self, epic: str, n: int = 65) -> Dict[str, Any]:
        # Version 2 supports the explicit /DAY/{numPoints} path and costs exactly n price points.
        return self.request("GET", f"/prices/{quote(epic, safe='')}/DAY/{int(n)}", version=2)


def load_seed() -> List[SeedRow]:
    rows: List[SeedRow] = []
    with SEED.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(
                SeedRow(
                    exposure_id=r["exposure_id"].strip(),
                    family=r["family"].strip(),
                    qc_candidates=r["qc_candidates"].strip(),
                    search_terms=[x.strip() for x in r["ig_search_terms"].split("|") if x.strip()],
                    benchmark22=r.get("benchmark22", "0").strip() == "1",
                )
            )
    return rows


def candidate_score(seed: SeedRow, term: str, m: Dict[str, Any]) -> float:
    name = m.get("instrumentName") or m.get("name") or ""
    q = tokens(term)
    n = tokens(name)
    overlap = (len(q & n) / max(1, len(q))) if q else 0.0
    exact_bonus = 0.45 if norm(term) and norm(term) in norm(name) else 0.0
    type_bonus = 0.15 if str(m.get("instrumentType", "")).upper() in VALID_TYPES else 0.0
    expiry = str(m.get("expiry") or "").upper()
    dated_bonus = 0.20 if expiry and expiry != "DFB" else -0.50
    return overlap + exact_bonus + type_bonus + dated_bonus


def first_margin_pct(detail: Dict[str, Any]) -> Optional[float]:
    inst = detail.get("instrument") or {}
    bands = inst.get("marginDepositBands") or []
    if bands:
        bands = sorted(bands, key=lambda x: fnum(x.get("min")) if fnum(x.get("min")) is not None else 1e99)
        b = bands[0]
        # IG v3 commonly exposes margin as a percentage and marginFactor with an explicit unit.
        v = fnum(b.get("margin"))
        if v is not None:
            return v
        v = fnum(b.get("marginFactor"))
        if v is not None:
            return v if str(b.get("marginFactorUnit", "PERCENTAGE")).upper() == "PERCENTAGE" else None
    v = fnum(inst.get("margin"))
    return v


def row_from_detail(seed: SeedRow, term: str, score: float, d: Dict[str, Any], census_day: date) -> Dict[str, Any]:
    inst = d.get("instrument") or {}
    snap = d.get("snapshot") or {}
    rules = d.get("dealingRules") or {}
    min_rule = rules.get("minDealSize") or {}
    bid = fnum(snap.get("bid"))
    offer = fnum(snap.get("offer"))
    expiry = inst.get("expiry")
    last_deal = parse_date((inst.get("expiryDetails") or {}).get("lastDealingDate"))
    if last_deal is None:
        last_deal = parse_date(expiry)
    days_to_expiry = (last_deal - census_day).days if last_deal else None
    special = " | ".join(str(x) for x in (inst.get("specialInfo") or []))
    sell_restricted = bool(re.search(r"sell.?only|closing.?only|cannot sell|short.+not", special, re.I))
    spread = (offer - bid) if (offer is not None and bid is not None) else None
    min_deal = fnum(min_rule.get("value"))
    mtype = str(inst.get("type") or "").upper()
    status = str(snap.get("marketStatus") or "").upper()
    margin = first_margin_pct(d)
    reasons = []
    if str(expiry or "").upper() in {"", "DFB"}:
        reasons.append("DFB_OR_NO_EXPIRY")
    if mtype not in VALID_TYPES:
        reasons.append("TYPE")
    if status in {"OFFLINE", "SUSPENDED"}:
        reasons.append("STATUS")
    if bid is None or offer is None or spread is None or spread <= 0:
        reasons.append("NO_TWO_WAY_QUOTE")
    if min_deal is None or min_deal > 0.0100000001:
        reasons.append("MIN_DEAL")
    if margin is None or margin <= 0:
        reasons.append("NO_MARGIN")
    if sell_restricted:
        reasons.append("DIRECTION_RESTRICTED")
    return {
        "exposure_id": seed.exposure_id,
        "family": seed.family,
        "qc_candidates": seed.qc_candidates,
        "benchmark22": int(seed.benchmark22),
        "search_term": term,
        "match_score": round(score, 6),
        "epic": inst.get("epic") or "",
        "ig_name": inst.get("name") or "",
        "type": mtype,
        "expiry": expiry or "",
        "last_dealing_date": last_deal.isoformat() if last_deal else "",
        "days_to_expiry": days_to_expiry if days_to_expiry is not None else "",
        "status": status,
        "bid": bid if bid is not None else "",
        "offer": offer if offer is not None else "",
        "spread_points": spread if spread is not None else "",
        "min_deal_size": min_deal if min_deal is not None else "",
        "min_deal_unit": min_rule.get("unit") or "",
        "margin_pct_first_band": margin if margin is not None else "",
        "contract_size": inst.get("contractSize") or "",
        "lot_size": inst.get("lotSize") if inst.get("lotSize") is not None else "",
        "one_pip_means": inst.get("onePipMeans") or "",
        "value_one_pip": inst.get("valueOfOnePip") or "",
        "currency": next((c.get("code") for c in (inst.get("currencies") or []) if c.get("isDefault")), ""),
        "special_info": special,
        "eligible_live": int(not reasons),
        "exclusion_reason": ";".join(reasons),
    }


def choose(seed: SeedRow, details: List[Dict[str, Any]], census_day: date) -> Tuple[Optional[Dict[str, Any]], str]:
    eligible = [x for x in details if x["eligible_live"]]
    if not eligible:
        reasons = sorted({x["exclusion_reason"] for x in details if x.get("exclusion_reason")})
        return None, "NO_ELIGIBLE_DETAIL" + ((":" + "|".join(reasons)) if reasons else "")

    # Frozen contract choice: nearest last-dealing date >=20 calendar days away.
    future = [x for x in eligible if isinstance(x.get("days_to_expiry"), int) and x["days_to_expiry"] >= 20]
    pool = future if future else eligible
    pool.sort(key=lambda x: (
        x.get("days_to_expiry") if isinstance(x.get("days_to_expiry"), int) else 10**9,
        -float(x.get("match_score") or 0),
        str(x.get("epic")),
    ))
    best = pool[0]

    # Identity ambiguity guard. If a distinct underlying-looking candidate is nearly tied, don't guess.
    tied = [x for x in pool[1:] if float(best["match_score"]) - float(x["match_score"]) <= 0.08]
    if tied:
        best_name = tokens(best.get("ig_name"))
        for x in tied:
            other = tokens(x.get("ig_name"))
            if best_name and other and len(best_name & other) / max(1, min(len(best_name), len(other))) < 0.60:
                return None, "AMBIGUOUS_IDENTITY"
    if not future:
        best["contract_buffer_flag"] = "LT20_OR_UNPARSED"
    else:
        best["contract_buffer_flag"] = "OK"
    return best, ""


def search_details(ig: IG, seed: SeedRow, census_day: date) -> Tuple[List[Dict[str, Any]], List[str]]:
    candidates: Dict[str, Tuple[float, str, Dict[str, Any]]] = {}
    errors: List[str] = []
    for term in seed.search_terms:
        try:
            markets = ig.search(term)
        except Exception as e:
            errors.append(f"SEARCH {term}: {e}")
            continue
        for m in markets:
            epic = str(m.get("epic") or "")
            if not epic:
                continue
            sc = candidate_score(seed, term, m)
            old = candidates.get(epic)
            if old is None or sc > old[0]:
                candidates[epic] = (sc, term, m)

    ranked = sorted(candidates.items(), key=lambda kv: (-kv[1][0], kv[0]))
    # Require a reasonable textual identity score before spending detail allowance.
    ranked = [x for x in ranked if x[1][0] >= 0.65][:4]
    details: List[Dict[str, Any]] = []
    for epic, (sc, term, _) in ranked:
        try:
            d = ig.detail(epic)
            details.append(row_from_detail(seed, term, sc, d, census_day))
        except Exception as e:
            errors.append(f"DETAIL {epic}: {e}")
    return details, errors


def history_rows(ig: IG, selected: Sequence[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for x in selected:
        try:
            d = ig.prices(str(x["epic"]), n=n)
        except Exception as e:
            out.append({"exposure_id": x["exposure_id"], "epic": x["epic"], "error": str(e)})
            continue
        for p in d.get("prices", []):
            op = p.get("openPrice") or {}
            cp = p.get("closePrice") or {}
            hp = p.get("highPrice") or {}
            lp = p.get("lowPrice") or {}
            def mid(z):
                b, a = fnum(z.get("bid")), fnum(z.get("ask"))
                return (b + a) / 2 if b is not None and a is not None else (b if b is not None else a)
            out.append({
                "exposure_id": x["exposure_id"],
                "epic": x["epic"],
                "snapshot_time": p.get("snapshotTimeUTC") or p.get("snapshotTime") or "",
                "open_mid": mid(op),
                "high_mid": mid(hp),
                "low_mid": mid(lp),
                "close_mid": mid(cp),
                "volume": p.get("lastTradedVolume") if p.get("lastTradedVolume") is not None else "",
                "error": "",
            })
    return out


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: List[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-history", action="store_true", help="also retrieve 65 daily prices for each admitted market")
    ap.add_argument("--history-points", type=int, default=65)
    args = ap.parse_args()

    missing = [k for k in ("IG_IDENTIFIER", "IG_PASSWORD", "IG_API_KEY") if not os.getenv(k)]
    if missing:
        print("Missing environment variables: " + ", ".join(missing), file=sys.stderr)
        return 2

    cday = date.fromisoformat(os.getenv("CENSUS_DATE", datetime.now(timezone.utc).date().isoformat()))
    ig = IG(os.environ["IG_IDENTIFIER"], os.environ["IG_PASSWORD"], os.environ["IG_API_KEY"], os.getenv("IG_ACCOUNT_ID"))
    print(f"Active account: {ig.account_id} type={ig.account.get('accountType')} currency={ig.account.get('currency')}")

    selected: List[Dict[str, Any]] = []
    exclusions: List[Dict[str, Any]] = []
    all_details: List[Dict[str, Any]] = []

    for i, seed in enumerate(load_seed(), 1):
        details, errors = search_details(ig, seed, cday)
        all_details.extend(details)
        pick, why = choose(seed, details, cday)
        if pick is not None:
            selected.append(pick)
            print(f"[{i:02d}] {seed.exposure_id:14s} -> {pick['epic']} {pick['ig_name']} spread={pick['spread_points']} min={pick['min_deal_size']} margin={pick['margin_pct_first_band']}%")
        else:
            exclusions.append({
                "exposure_id": seed.exposure_id,
                "family": seed.family,
                "qc_candidates": seed.qc_candidates,
                "benchmark22": int(seed.benchmark22),
                "reason": why or "UNMAPPED",
                "errors": " | ".join(errors),
                "detail_candidates": json.dumps(details, separators=(",", ":")),
            })
            print(f"[{i:02d}] {seed.exposure_id:14s} -> EXCLUDE {why or 'UNMAPPED'}")

    write_csv(HERE / "ig_expanded_census.csv", selected)
    write_csv(HERE / "ig_expanded_exclusions.csv", exclusions)
    write_csv(HERE / "ig_expanded_all_detail_candidates.csv", all_details)

    if args.with_history:
        hist = history_rows(ig, selected, max(20, args.history_points))
        write_csv(HERE / "ig_expanded_history.csv", hist)

    print(f"Selected {len(selected)} / {len(selected) + len(exclusions)} exposures")
    print(f"Wrote {HERE / 'ig_expanded_census.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
