# Index large-move continuation / reversal anatomy v1
# QuantConnect Python: one main.py only.
#
# No external files and no orders.
#
# Signal at 15:45 New York:
#   return from previous regular-session close to 15:45
#   rolling z-score using PRIOR observations only
#
# Tests fixed build-derived absolute-z thresholds:
#   80th, 90th, 95th percentiles
#
# Windows:
#   late:      15:45 -> 16:00, same direction
#   overnight: 16:00 -> next 09:31, opposite direction
#   morning:   next 09:31 -> 10:00, opposite direction
#   total:     16:00 -> next 10:00, opposite direction
#
# Reports raw edge and break-even total transaction cost in basis points.

from AlgorithmImports import *
import numpy as np
import pandas as pd


BUILD_START = pd.Timestamp("2012-01-01")
BUILD_END = pd.Timestamp("2018-12-31")

PERIODS = [
    ("BUILD", pd.Timestamp("2012-01-01"), pd.Timestamp("2018-12-31")),
    ("2019_2021", pd.Timestamp("2019-01-01"), pd.Timestamp("2021-12-31")),
    ("2022_2024", pd.Timestamp("2022-01-01"), pd.Timestamp("2024-12-31")),
    ("2025_2026", pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31")),
]


class IndexLargeMoveAnatomy(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2012, 1, 3)
        self.set_end_date(2026, 9, 29)
        self.set_cash(100000)
        self.set_time_zone(TimeZones.NEW_YORK)

        self.spy = self.add_equity("SPY", Resolution.MINUTE).symbol
        self.qqq = self.add_equity("QQQ", Resolution.MINUTE).symbol

        self.prev_close = {"SPX": None, "NDX": None}
        self.day = None
        self.signal = {}
        self.pending = {"SPX": None, "NDX": None}
        self.rows = []

        self.set_runtime_statistic("IPF Stage", "Large-move anatomy")
        self.log("INDEX_REVERSAL_BEGIN")
        self.log("VERSION=V1_WINDOW_ANATOMY")
        self.log("Signal=prev close to 15:45 rolling-z intraday return")
        self.log("Windows=15:45-close, close-next09:31, 09:31-10:00, close-next10:00")
        self.log("Thresholds=build abs-z P80/P90/P95; no orders")

    def _reset_day(self, d):
        self.day = d
        self.signal = {}

    def on_data(self, data):
        d = self.time.date()
        if d != self.day:
            self._reset_day(d)

        if self.spy not in data.bars or self.qqq not in data.bars:
            return

        px = {
            "SPX": float(data.bars[self.spy].close),
            "NDX": float(data.bars[self.qqq].close),
        }

        if self.time.hour == 9 and self.time.minute == 31:
            for fam in ("SPX", "NDX"):
                p = self.pending[fam]
                if p is not None and self.prev_close[fam]:
                    p["next_0931_px"] = px[fam]
                    p["overnight_return"] = px[fam] / self.prev_close[fam] - 1.0

        if self.time.hour == 10 and self.time.minute == 0:
            for fam in ("SPX", "NDX"):
                p = self.pending[fam]
                if p is not None and self.prev_close[fam]:
                    p["next_1000_px"] = px[fam]
                    p["total_next_return"] = px[fam] / self.prev_close[fam] - 1.0
                    opx = p.get("next_0931_px")
                    if opx is not None and opx > 0:
                        p["morning_return"] = px[fam] / opx - 1.0
                    self.pending[fam] = None

        if self.time.hour == 15 and self.time.minute == 45:
            for fam in ("SPX", "NDX"):
                prev = self.prev_close[fam]
                if prev is None or prev <= 0:
                    continue
                intra = px[fam] / prev - 1.0
                self.signal[fam] = {
                    "date": pd.Timestamp(d),
                    "family": fam,
                    "intraday_return": intra,
                    "decision_px": px[fam],
                }

        if self.time.hour == 16 and self.time.minute == 0:
            for fam in ("SPX", "NDX"):
                s = self.signal.get(fam)
                if s is not None:
                    row = dict(s)
                    row["close_px"] = px[fam]
                    row["late_return"] = px[fam] / s["decision_px"] - 1.0
                    row["next_0931_px"] = np.nan
                    row["next_1000_px"] = np.nan
                    row["overnight_return"] = np.nan
                    row["morning_return"] = np.nan
                    row["total_next_return"] = np.nan
                    self.rows.append(row)
                    self.pending[fam] = row
                self.prev_close[fam] = px[fam]

    @staticmethod
    def _rolling_z(s):
        mu = s.shift(1).rolling(252, min_periods=60).mean()
        sd = s.shift(1).rolling(252, min_periods=60).std()
        return (s - mu) / sd

    @staticmethod
    def _stats(x):
        a = pd.Series(x).dropna().to_numpy(float)
        if len(a) == 0:
            return {"n": 0, "mean_bp": np.nan, "median_bp": np.nan, "hit": np.nan, "sum_pct": np.nan}
        return {
            "n": len(a),
            "mean_bp": float(a.mean() * 10000),
            "median_bp": float(np.median(a) * 10000),
            "hit": float(np.mean(a > 0)),
            "sum_pct": float(a.sum() * 100),
        }

    def _emit(self, fam, period, quantile, q):
        sign = np.sign(q["intraday_return"])
        trades = {
            "late": sign * q["late_return"],
            "overnight": -sign * q["overnight_return"],
            "morning": -sign * q["morning_return"],
            "total": -sign * q["total_next_return"],
        }
        stats = {k: self._stats(v) for k, v in trades.items()}
        self.log(
            f"INDEX_PATH,{fam},{period},P{int(quantile*100)},"
            f"n={stats['late']['n']},lateMeanBp={stats['late']['mean_bp']:.3f},"
            f"lateMedBp={stats['late']['median_bp']:.3f},lateHit={stats['late']['hit']:.3f},"
            f"lateBreakEvenCostBp={stats['late']['mean_bp']:.3f},"
            f"overnightMeanBp={stats['overnight']['mean_bp']:.3f},"
            f"overnightHit={stats['overnight']['hit']:.3f},"
            f"morningMeanBp={stats['morning']['mean_bp']:.3f},"
            f"morningHit={stats['morning']['hit']:.3f},"
            f"totalMeanBp={stats['total']['mean_bp']:.3f},"
            f"totalMedBp={stats['total']['median_bp']:.3f},"
            f"totalHit={stats['total']['hit']:.3f},"
            f"totalBreakEvenCostBp={stats['total']['mean_bp']:.3f},"
            f"totalSumPct={stats['total']['sum_pct']:.2f}"
        )

    def _direction_split(self, fam, q, threshold):
        e = q[q["abs_z"] >= threshold].copy()
        for label, mask in (("UP", e["intraday_return"] > 0), ("DOWN", e["intraday_return"] < 0)):
            g = e[mask].copy()
            sign = np.sign(g["intraday_return"])
            late = self._stats(sign * g["late_return"])
            total = self._stats(-sign * g["total_next_return"])
            overnight = self._stats(-sign * g["overnight_return"])
            morning = self._stats(-sign * g["morning_return"])
            self.log(
                f"INDEX_DIRECTION,{fam},HOLDOUT_P80,{label},"
                f"n={late['n']},lateMeanBp={late['mean_bp']:.3f},lateHit={late['hit']:.3f},"
                f"overnightMeanBp={overnight['mean_bp']:.3f},"
                f"morningMeanBp={morning['mean_bp']:.3f},"
                f"totalMeanBp={total['mean_bp']:.3f},totalHit={total['hit']:.3f}"
            )

    def on_end_of_algorithm(self):
        if len(self.rows) < 500:
            self.log(f"INDEX_REVERSAL_FAIL,rows={len(self.rows)}")
            return

        df = pd.DataFrame(self.rows).sort_values(["family", "date"])
        self.log(f"INDEX_REVERSAL_QA,rows={len(df)},start={df.date.min().date()},end={df.date.max().date()}")

        for fam in ("SPX", "NDX"):
            q = df[df["family"] == fam].copy().sort_values("date").reset_index(drop=True)
            q["z"] = self._rolling_z(q["intraday_return"])
            q["abs_z"] = q["z"].abs()
            q = q.dropna(subset=["z"]).copy()

            build = q[(q["date"] >= BUILD_START) & (q["date"] <= BUILD_END)].copy()
            thresholds = {quantile: float(build["abs_z"].quantile(quantile)) for quantile in (0.80, 0.90, 0.95)}

            self.log(
                f"INDEX_THRESHOLDS,{fam},P80={thresholds[0.80]:.4f},"
                f"P90={thresholds[0.90]:.4f},P95={thresholds[0.95]:.4f}"
            )

            for period, start, end in PERIODS:
                s = q[(q["date"] >= start) & (q["date"] <= end)].copy()
                for quantile, threshold in thresholds.items():
                    e = s[s["abs_z"] >= threshold].copy()
                    self._emit(fam, period, quantile, e)

            hold = q[q["date"] >= pd.Timestamp("2019-01-01")].copy()
            self._direction_split(fam, hold, thresholds[0.80])

        self.log("INDEX_REVERSAL_END")
