# QuantConnect LEAN source-data census for MAIN-IG Expanded v1.
# No strategy signals and no orders. It checks only the frozen minimum source-data rule.
from AlgorithmImports import *  # noqa: F401,F403

import csv
import gzip
import io
import math
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd

# Ordered fallback candidates copied from EXPANDED_V1_EXPOSURES.csv.  No performance data.
CANDIDATE_ROOTS = [
    "ES","NQ","YM","ZT","ZF","ZN","ZB","6E","E7","M6E","6J","J7","MJY","M6J",
    "6B","M6B","6A","M6A","6C","M6C","MCD","GC","MGC","SI","SIL","HG","CL","MCL",
    "NG","HH","HP","HO","RB","ZC","ZS","ZW","6S","MSF","M6S","6N","6M","6L","6Z",
    "CNH","MNH","ACD","AJY","ANE","CJY","EAD","ECD","ESK","MIR","BZ","EH","AC0",
    "B0","A1R","A7Q","AD0","TN","UB","GE","F1U","LBR","LBS","KE","ZO","ZM","ZL",
    "BCF","BWF","EI","NKD","NIY","RS1","RTY","M2K","EMD","TPY","IBV","GF","HE","LE",
    "PA","PAM","PL","HRC","SB","YO"
]
CANDIDATE_ROOTS = list(dict.fromkeys(CANDIDATE_ROOTS))
START = (2024, 1, 1)
END = (2026, 9, 29)
DATA_START = datetime(2023, 9, 1)


def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def csv_gz(rows, fields):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=fields)
    w.writeheader(); w.writerows(rows)
    return gzip.compress(s.getvalue().encode("utf-8"), compresslevel=9)


class IpfSourceCensus(QCAlgorithm):
    def initialize(self):
        self.set_start_date(*START)
        self.set_end_date(*END)
        self.set_cash(100000)
        self.canon = {}
        self.add_errors = {}
        for tk in CANDIDATE_ROOTS:
            try:
                f = self.add_future(tk, Resolution.DAILY)
                f.set_filter(0, 0)
                self.canon[tk] = f.symbol
            except Exception as ex:
                self.add_errors[tk] = str(ex)[:250]
        self.stats = {tk: {"dates": set(), "price_dates": set(), "volume_dates": set(), "oi_dates": set(),
                           "rows": 0, "first": None, "last": None} for tk in CANDIDATE_ROOTS}
        self.schedule.on(self.date_rules.month_start(), self.time_rules.at(12, 0), self.scan)

    def scan(self):
        end = self.time
        start = max(DATA_START, end - timedelta(days=45))
        for tk, sym in self.canon.items():
            st = self.stats[tk]
            try:
                for fu in self.history[FutureUniverse](sym, start, end):
                    d = fu.end_time.date()
                    any_price = any_vol = any_oi = False
                    n = 0
                    for c in fu:
                        n += 1
                        close = fnum(c.close)
                        vol = fnum(c.volume)
                        oi = fnum(c.open_interest)
                        any_price = any_price or (close is not None and close > 0)
                        any_vol = any_vol or (vol is not None and vol > 0)
                        any_oi = any_oi or (oi is not None and oi > 0)
                    if n:
                        st["rows"] += n
                        st["dates"].add(d)
                        if any_price: st["price_dates"].add(d)
                        if any_vol: st["volume_dates"].add(d)
                        if any_oi: st["oi_dates"].add(d)
                        st["first"] = d if st["first"] is None or d < st["first"] else st["first"]
                        st["last"] = d if st["last"] is None or d > st["last"] else st["last"]
            except Exception as ex:
                self.add_errors.setdefault(tk, str(ex)[:250])

    def on_end_of_algorithm(self):
        # One final window catches the freeze-month dates.
        self.scan()
        rows = []
        for tk in CANDIDATE_ROOTS:
            s = self.stats[tk]
            np_, nv, no = len(s["price_dates"]), len(s["volume_dates"]), len(s["oi_dates"])
            ok = tk in self.canon and np_ >= 252 and nv >= 252 and no >= 252
            reasons = []
            if tk not in self.canon: reasons.append("ADD_FUTURE_FAILED")
            if np_ < 252: reasons.append("PRICE_LT252")
            if nv < 252: reasons.append("VOLUME_LT252")
            if no < 252: reasons.append("OI_LT252")
            rows.append({
                "ticker": tk,
                "source_data_ok": int(ok),
                "price_days": np_,
                "volume_days": nv,
                "oi_days": no,
                "universe_days": len(s["dates"]),
                "contract_rows": s["rows"],
                "first_date": s["first"].isoformat() if s["first"] else "",
                "last_date": s["last"].isoformat() if s["last"] else "",
                "reason": ";".join(reasons),
                "error": self.add_errors.get(tk, ""),
            })
        key = f"{self.project_id}/main_ig_source_census.csv.gz"
        ok = self.object_store.save_bytes(key, csv_gz(rows, ["ticker","source_data_ok","price_days",
            "volume_days","oi_days","universe_days","contract_rows","first_date","last_date","reason","error"]))
        self.log("SOURCE CENSUS: %d roots, %d pass" % (len(rows), sum(r["source_data_ok"] for r in rows)))
        self.log("Object Store: %s saved=%s" % (key, ok))
        self.log("No signals calculated; no orders placed.")
