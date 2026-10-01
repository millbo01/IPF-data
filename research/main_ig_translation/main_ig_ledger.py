# QuantConnect LEAN exporter for MAIN-IG Expanded v1.
# Requires the frozen ipf_engine.py in the same QC project.
# No orders are placed. It exports the exact net MAIN target fraction by market/day.
from AlgorithmImports import *  # noqa: F401,F403

import csv
import gzip
import io
import math
from datetime import date, datetime, timedelta

from ipf_engine import Engine, prev_bday, NAN, UNIT_BREAK

START = (2010, 1, 1)
END = (2026, 9, 29)
DATA_START = datetime(2009, 1, 1)
STEP_TIME = (10, 1)
PORT_VOL_TARGET = 0.10
M_MAIN = {"T1": 1.4335, "F": 4.54643, "Dip": 3.64361}
ORIGINAL_22 = ["ES", "NQ", "YM", "ZT", "ZF", "ZN", "ZB", "6E", "6J", "6B", "6A", "6C",
               "GC", "SI", "HG", "CL", "NG", "HO", "RB", "ZC", "ZS", "ZW"]
ORIGINAL_F_EXCLUDE = {"SI", "GC", "6C", "HG", "CL"}
EQUITIES = ["ES", "NQ", "YM"]
FEE_PER_SIDE = 2.50
SLIPPAGE_TICKS = 1.0


def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else NAN
    except Exception:
        return NAN


def to_date(x):
    try:
        return x.date()
    except Exception:
        return pd.Timestamp(str(x)).date()


def csv_bytes(rows, fields):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
    return gzip.compress(s.getvalue().encode("utf-8"), compresslevel=9)


class IpfMainIgLedger(QCAlgorithm):
    def initialize(self):
        self.set_start_date(*START)
        self.set_end_date(*END)
        self.set_cash(1_000_000)
        self.set_time_zone(TimeZones.NEW_YORK)

        # One QC parameter is the only universe input required after the live IG census.
        # Example: ES,NQ,YM,...,RTY,PL
        raw = (self.get_parameter("tickers") or "").strip()
        self.tickers = [x.strip().upper() for x in raw.split(",") if x.strip()] or list(ORIGINAL_22)
        self.tickers = list(dict.fromkeys(self.tickers))
        self.log("MAIN-IG ledger universe (%d): %s" % (len(self.tickers), ",".join(self.tickers)))

        specs, hol = {}, {}
        self.canon = {}
        for tk in self.tickers:
            fut = self.add_future(tk, Resolution.DAILY)
            fut.set_filter(0, 0)
            self.canon[tk] = fut.symbol
            try:
                sp = fut.symbol_properties
                mult = float(sp.contract_multiplier)
                tick = float(sp.minimum_price_variation)
                if not (mult > 0 and tick >= 0):
                    raise ValueError("bad symbol properties")
            except Exception:
                # Costs do not enter the exported target fractions; this fallback only keeps
                # the research benchmark series calculable if QC metadata is incomplete.
                mult, tick = 1.0, 0.0
            specs[tk] = (FEE_PER_SIDE + SLIPPAGE_TICKS * mult * tick, mult)
            try:
                hol[tk] = set(to_date(h) for h in fut.exchange.hours.holidays)
            except Exception:
                hol[tk] = set()

        f_excl = [tk for tk in self.tickers if tk in ORIGINAL_F_EXCLUDE]
        self.eng = Engine(self.tickers, specs, hol, f_excl, EQUITIES)
        self.snap = {}
        self._attach_snapshot_hooks()
        self.schedule.on(self.date_rules.every_day(), self.time_rules.at(*STEP_TIME), self.step)

    def _attach_snapshot_hooks(self):
        # Capture FeatState.last at the exact point the unchanged Engine calls books().
        # This is observational only; the original return values and state transitions are untouched.
        for tk, fs in self.eng.fs.items():
            original = fs.books

            def wrapped(ow, _orig=original, _fs=fs, _tk=tk):
                ans = _orig(ow)
                L = _fs.last
                if L is not None:
                    self.snap.setdefault(L["date"], {})[_tk] = {
                        "w": dict(L["w"]),
                        "live_raw": float(L["live_raw"]),
                        "lead": L["lead"],
                        "raw": float(L["raw"]),
                        "r": float(L["r"]) if L["r"] == L["r"] else 0.0,
                    }
                return ans

            fs.books = wrapped

    def fetch(self, tk):
        cs = self.eng.chain[tk]
        if cs.max_stamp is None:
            start = DATA_START
        else:
            start = datetime(cs.max_stamp.year, cs.max_stamp.month, cs.max_stamp.day) - timedelta(days=1)
        for fu in self.history[FutureUniverse](self.canon[tk], start, self.time):
            stamp = to_date(fu.end_time)
            d = prev_bday(stamp)
            for c in fu:
                s = c.symbol
                key = str(s)
                e = cs.exp.get(key)
                if e is None and key not in cs.exp:
                    try:
                        e = to_date(s.id.date)
                    except Exception:
                        e = None
                cs.add_row(d, key, (fnum(c.open), fnum(c.high), fnum(c.low), fnum(c.close),
                                    fnum(c.open_interest), fnum(c.volume)), e, stamp)

    def step(self):
        if self.time.weekday() >= 5:
            return
        chains = self.eng.chain
        for tk in self.tickers:
            cs = chains[tk]
            try:
                self.fetch(tk)
                if cs.med is None:
                    cs.set_median_from_raw()
                fb = cs.final_bound()
                if fb is not None:
                    cs.consume(fb)
            except Exception as ex:
                self.log("fetch %s failed: %s" % (tk, str(ex)[:180]))
        stamps = {tk: cs.max_stamp for tk, cs in chains.items() if cs.max_stamp is not None}
        if not stamps:
            return
        med = sorted(stamps.values())[len(stamps) // 2]
        fresh = [tk for tk, s in stamps.items() if s >= med - timedelta(days=10)]
        if not fresh:
            return
        G = min(chains[tk].final_bound() for tk in fresh)
        self.eng.process_ready(G)

    def _finalize_engine(self):
        for cs in self.eng.chain.values():
            cs.flush()
        self.eng.process_ready()

    def _target_rows(self):
        mk = {k: v * PORT_VOL_TARGET / 0.10 for k, v in M_MAIN.items()}
        state = {}
        rows = []
        for d in sorted(self.snap):
            changed = self.snap[d]
            state.update(changed)
            nlive = {}
            for k in mk:
                nlive[k] = sum(1 for t in self.eng.univ[k]
                               if t in state and state[t]["live_raw"] > 0)
            for tk in self.tickers:
                if tk not in state:
                    continue
                L = state[tk]
                frac = 0.0
                for k, m in mk.items():
                    if tk in self.eng.univ[k] and nlive[k] > 0:
                        frac += m * float(L["w"][self.eng.src[k]]) / nlive[k]
                # Same-contract return only exists when this market actually updated on d.
                upd = changed.get(tk)
                rows.append({
                    "date": d.isoformat(),
                    "ticker": tk,
                    "frac": "%.14g" % frac,
                    "raw": "%.14g" % float(L["raw"]),
                    "r": "%.14g" % (float(upd["r"]) if upd is not None else 0.0),
                    "lead": str(L["lead"]),
                    "t1_w": "%.14g" % float(L["w"].get("T1", 0.0)),
                    "f_w": "%.14g" % float(L["w"].get("F", 0.0)),
                    "dip_w": "%.14g" % float(L["w"].get("Dip", 0.0)),
                    "nlive_t1": nlive.get("T1", 0),
                    "nlive_f": nlive.get("F", 0),
                    "nlive_dip": nlive.get("Dip", 0),
                    "updated": 1 if upd is not None else 0,
                })
        return rows

    def _benchmark_rows(self):
        s = self.eng.book_series(date(*START))
        dates = sorted(set(self.eng.bench) | set().union(*(set(s[k][0]) for k in M_MAIN)))
        rows = []
        for d in dates:
            main = sum(M_MAIN[k] * s[k][0].get(d, 0.0) for k in M_MAIN)
            rows.append({
                "date": d.isoformat(),
                "unrounded_main_return": "%.14g" % main,
                "es_return": "%.14g" % float(self.eng.bench.get(d, 0.0) or 0.0),
            })
        return rows

    def on_end_of_algorithm(self):
        self._finalize_engine()
        ledger = self._target_rows()
        bench = self._benchmark_rows()
        universe_tag = "original22" if self.tickers == ORIGINAL_22 else "expanded"
        k1 = f"{self.project_id}/main_ig_{universe_tag}_ledger.csv.gz"
        k2 = f"{self.project_id}/main_ig_{universe_tag}_benchmark.csv.gz"
        ok1 = self.object_store.save_bytes(k1, csv_bytes(ledger, [
            "date", "ticker", "frac", "raw", "r", "lead", "t1_w", "f_w", "dip_w",
            "nlive_t1", "nlive_f", "nlive_dip", "updated"]))
        ok2 = self.object_store.save_bytes(k2, csv_bytes(bench, ["date", "unrounded_main_return", "es_return"]))
        self.log("MAIN-IG EXPORT: %d ledger rows, %d benchmark rows" % (len(ledger), len(bench)))
        self.log("Object Store: %s saved=%s" % (k1, ok1))
        self.log("Object Store: %s saved=%s" % (k2, ok2))
        self.log("No orders were placed.")
