# NDX/QQQ next-session morning fade — IG execution v2
# QuantConnect Python / LEAN. This is the only file required in the QC project.
# No orders are placed.
#
# Frozen signal:
#   QQQ/SPY return from previous regular-session close to 15:45 New York
#   252-session rolling z-score using PRIOR observations only (min 60)
# Fixed thresholds inherited from V1 anatomy:
#   NDX: P80=1.2681, P90=1.7796, P95=2.3646
#   SPX: P80=1.2278, P90=1.7595, P95=2.2530
#
# Trade T+1:
#   fade signal sign; primary entry 09:31 NY; sensitivity 09:32/09:35; exit 10:00.
#   Trigger remains QQQ/SPY. Execution P&L uses NDX/SPX cash-index minute data.
#
# IG economics frozen before this run:
#   Live account confirmed 2026-10-02: US Tech 100 DFB minDealSize=0.01 POINTS,
#   first-band retail margin=5%.
#   Representative full round-trip DFB spread schedule:
#     NDX 1.0 point in 14:30-21:00 London, otherwise 2.0 around the US open.
#     SPX 0.4 point in 14:30-21:00 London, otherwise 0.6 around the US open.
#   STRESS2X doubles the spread.
#
# Primary £2,000 sizing:
#   ONE_X_NOTIONAL: stake ~= running_equity / entry_index, rounded to nearest £0.01/pt.
#   This targets ~1x index notional and therefore ~5% margin before rounding.
# Diagnostic sizing:
#   LIVE_MIN_0p01: fixed £0.01/pt.
#
# Output prefixes:
#   IGFADE_QA       data coverage / index availability
#   IGFADE_SUMMARY  requested aggregate economics
#   IGFADE_YEAR     year-by-year chronology
#   IGFADE_DIR      up-day/down-day split for primary 09:31 BASE rule
#   IGFADE_TRADE    full NDX P80+ primary-rule trade ledger (P90/P95 flags included)
#
# The code deliberately does not choose a best threshold or sensitivity timestamp.

from AlgorithmImports import *
import math
import numpy as np
import pandas as pd

THRESHOLDS = {
    "SPX": {"P80": 1.2278, "P90": 1.7595, "P95": 2.2530},
    "NDX": {"P80": 1.2681, "P90": 1.7796, "P95": 2.3646},
}

PERIODS = [
    ("BUILD", pd.Timestamp("2012-01-01"), pd.Timestamp("2018-12-31")),
    ("2019_2021", pd.Timestamp("2019-01-01"), pd.Timestamp("2021-12-31")),
    ("2022_2024", pd.Timestamp("2022-01-01"), pd.Timestamp("2024-12-31")),
    ("2025_2026", pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31")),
    ("HOLDOUT", pd.Timestamp("2019-01-01"), pd.Timestamp("2026-12-31")),
    ("ALL", pd.Timestamp("2012-01-01"), pd.Timestamp("2026-12-31")),
]

ENTRIES = [("0931", 9, 31), ("0932", 9, 32), ("0935", 9, 35)]
COSTS = [("BASE", 1.0), ("STRESS2X", 2.0)]
SIZING = ("ONE_X_NOTIONAL", "LIVE_MIN_0p01")
START_EQUITY = 2000.0
MARGIN_RATE = 0.05
STAKE_STEP = 0.01
MIN_STAKE = 0.01


class IndexMorningFadeIG(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2012, 1, 3)
        self.set_end_date(2026, 9, 29)
        self.set_cash(100000)
        self.set_time_zone(TimeZones.NEW_YORK)

        self.spy = self.add_equity("SPY", Resolution.MINUTE).symbol
        self.qqq = self.add_equity("QQQ", Resolution.MINUTE).symbol
        self.spx = self.add_index("SPX", Resolution.MINUTE).symbol
        self.ndx = self.add_index("NDX", Resolution.MINUTE).symbol

        self.proxy = {"SPX": self.spy, "NDX": self.qqq}
        self.execsym = {"SPX": self.spx, "NDX": self.ndx}
        self.prev_close = {"SPX": None, "NDX": None}
        self.pending = {"SPX": None, "NDX": None}
        self.signal = {}
        self.day = None
        self.rows = []
        self.exec_bar_count = {"SPX": 0, "NDX": 0}
        self._setup_export_chart()

        self.log("IGFADE_BEGIN")
        self.log("VERSION=V2_IG_EXECUTION_AMEND2_CHART_EXPORT")
        self.log("PRIMARY=NDX,P80/P90/P95_UNCHANGED,ENTRY=09:31,EXIT=10:00")
        self.log("SENSITIVITY=09:32|09:35;NO_TIMESTAMP_SELECTION")

    def _setup_export_chart(self):
        # Transport the event-level results through QC charts so Download Results
        # carries the data even when the account log quota is exhausted.
        # Free-tier quota is 10 custom series; this uses exactly 10.
        chart = Chart("IGFADE_EXPORT")
        names = [
            "NDX_Z",
            "NDX_SIGRET_BP",
            "NDX_ENTRY0931",
            "NDX_GROSS0931_BP",
            "NDX_MAE0931_BP",
            "NDX_GROSS0932_BP",
            "NDX_GROSS0935_BP",
            "SPX_Z",
            "SPX_ENTRY0931",
            "SPX_GROSS0931_BP",
        ]
        self.export_series = {}
        for idx, name in enumerate(names):
            series = Series(name, SeriesType.LINE, idx, "")
            chart.add_series(series)
            self.export_series[name] = series
        self.add_chart(chart)

    def _export_chart_data(self, ndx, spx):
        # X-axis is the trade date. The signal date is the immediately preceding
        # regular US equity session and can therefore be reconstructed exactly.
        ne = ndx[ndx["abs_z"] >= THRESHOLDS["NDX"]["P80"]].sort_values("trade_date")
        for _, r in ne.iterrows():
            t = pd.Timestamp(r["trade_date"]).to_pydatetime()
            self.export_series["NDX_Z"].add_point(t, float(r["z"]))
            self.export_series["NDX_SIGRET_BP"].add_point(t, float(r["intraday_return"]) * 10000.0)
            self.export_series["NDX_ENTRY0931"].add_point(t, float(r["exec_0931"]))
            self.export_series["NDX_GROSS0931_BP"].add_point(t, float(r["gross_bp_0931"]))
            self.export_series["NDX_MAE0931_BP"].add_point(t, float(r["mae_bp_0931"]))
            self.export_series["NDX_GROSS0932_BP"].add_point(t, float(r["gross_bp_0932"]))
            self.export_series["NDX_GROSS0935_BP"].add_point(t, float(r["gross_bp_0935"]))

        se = spx[spx["abs_z"] >= THRESHOLDS["SPX"]["P80"]].sort_values("trade_date")
        for _, r in se.iterrows():
            t = pd.Timestamp(r["trade_date"]).to_pydatetime()
            self.export_series["SPX_Z"].add_point(t, float(r["z"]))
            self.export_series["SPX_ENTRY0931"].add_point(t, float(r["exec_0931"]))
            self.export_series["SPX_GROSS0931_BP"].add_point(t, float(r["gross_bp_0931"]))

        self.set_runtime_statistic("IGFADE Export", f"NDX={len(ne)} SPX={len(se)}")
        self.set_runtime_statistic("IGFADE Output", "Download Results JSON")

    @staticmethod
    def _bar(data, symbol):
        try:
            return data.bars[symbol] if symbol in data.bars else None
        except Exception:
            return None

    def on_data(self, data):
        d = self.time.date()
        if d != self.day:
            self.day = d
            self.signal = {}

        pbar = {f: self._bar(data, s) for f, s in self.proxy.items()}
        ebar = {f: self._bar(data, s) for f, s in self.execsym.items()}
        for fam in ("SPX", "NDX"):
            if ebar[fam] is not None:
                self.exec_bar_count[fam] += 1

        # Capture the three pre-specified candidate entry prices.
        for key, hh, mm in ENTRIES:
            if self.time.hour == hh and self.time.minute == mm:
                for fam in ("SPX", "NDX"):
                    p, b = self.pending[fam], ebar[fam]
                    if p is None or b is None:
                        continue
                    px = float(b.close)
                    p["trade_date"] = pd.Timestamp(d)
                    p["exec_" + key] = px
                    p["min_" + key] = px
                    p["max_" + key] = px

        # Track adverse excursion from each entry through the 10:00 bar.
        for fam in ("SPX", "NDX"):
            p, b = self.pending[fam], ebar[fam]
            if p is None or b is None:
                continue
            for key, hh, mm in ENTRIES:
                ep = p.get("exec_" + key)
                if ep is None or not np.isfinite(ep):
                    continue
                after = (self.time.hour > hh) or (self.time.hour == hh and self.time.minute > mm)
                before = (self.time.hour < 10) or (self.time.hour == 10 and self.time.minute <= 0)
                if after and before:
                    p["min_" + key] = min(float(p["min_" + key]), float(b.low))
                    p["max_" + key] = max(float(p["max_" + key]), float(b.high))

        # Exit observation.
        if self.time.hour == 10 and self.time.minute == 0:
            for fam in ("SPX", "NDX"):
                p, b = self.pending[fam], ebar[fam]
                if p is None or b is None:
                    continue
                p["exec_1000"] = float(b.close)
                p["complete"] = True
                self.pending[fam] = None

        # Signal observation at 15:45 using the proxy, exactly as in V1.
        if self.time.hour == 15 and self.time.minute == 45:
            for fam in ("SPX", "NDX"):
                b, prev = pbar[fam], self.prev_close[fam]
                if b is None or prev is None or prev <= 0:
                    continue
                px = float(b.close)
                self.signal[fam] = {
                    "signal_date": pd.Timestamp(d),
                    "family": fam,
                    "intraday_return": px / prev - 1.0,
                    "proxy_1545": px,
                }

        # Store the regular-session close and arm the next-session trade observation.
        if self.time.hour == 16 and self.time.minute == 0:
            for fam in ("SPX", "NDX"):
                b = pbar[fam]
                if b is None:
                    continue
                px = float(b.close)
                s = self.signal.get(fam)
                if s is not None:
                    r = dict(s)
                    r["proxy_close"] = px
                    r["trade_date"] = pd.NaT
                    r["complete"] = False
                    for key, _, _ in ENTRIES:
                        r["exec_" + key] = np.nan
                        r["min_" + key] = np.nan
                        r["max_" + key] = np.nan
                    r["exec_1000"] = np.nan
                    self.rows.append(r)
                    self.pending[fam] = r
                self.prev_close[fam] = px

    @staticmethod
    def _rolling_z(s):
        mu = s.shift(1).rolling(252, min_periods=60).mean()
        sd = s.shift(1).rolling(252, min_periods=60).std()
        return (s - mu) / sd

    @staticmethod
    def _spread(fam, trade_date, key):
        """Representative CURRENT IG DFB spread schedule, applied historically.

        London-clock conversion is deliberate because the UK and US switch DST on
        different dates. During mismatch weeks, 09:31 New York can be 13:31 London.
        """
        hhmm = {"0931": "09:31", "0932": "09:32", "0935": "09:35"}[key]
        ts = pd.Timestamp(str(pd.Timestamp(trade_date).date()) + " " + hhmm,
                          tz="America/New_York")
        lon = ts.tz_convert("Europe/London")
        minute = lon.hour * 60 + lon.minute
        core = (14 * 60 + 30) <= minute < 21 * 60
        if fam == "NDX":
            return 1.0 if core else 2.0
        return 0.4 if core else 0.6

    @staticmethod
    def _round_stake(x):
        # Positive stake magnitude only; conventional half-up to the live £0.01 step.
        if not np.isfinite(x) or x <= 0:
            return 0.0
        q = math.floor(x / STAKE_STEP + 0.5) * STAKE_STEP
        return max(MIN_STAKE, q)

    @staticmethod
    def _mdd(equity_curve):
        a = np.asarray(equity_curve, float)
        if len(a) == 0:
            return np.nan
        peak = np.maximum.accumulate(a)
        return float(np.min(a / peak - 1.0))

    def _enrich(self, fam, q):
        q = q.sort_values("signal_date").reset_index(drop=True).copy()
        q["z"] = self._rolling_z(q["intraday_return"])
        q["abs_z"] = q["z"].abs()
        q["fade_sign"] = -np.sign(q["intraday_return"])
        q = q.dropna(subset=["z", "trade_date", "exec_1000"]).copy()

        # Require all three entries so sensitivity comparisons use the identical event set.
        q = q.dropna(subset=["exec_0931", "exec_0932", "exec_0935"]).copy()

        for key, _, _ in ENTRIES:
            q["gross_ret_" + key] = q["fade_sign"] * (q["exec_1000"] / q["exec_" + key] - 1.0)
            q["gross_bp_" + key] = q["gross_ret_" + key] * 10000.0
            q["gross_pts_" + key] = q["fade_sign"] * (q["exec_1000"] - q["exec_" + key])
            q["spread_" + key] = [self._spread(fam, d, key) for d in q["trade_date"]]
            adverse = np.where(q["fade_sign"] > 0, q["min_" + key], q["max_" + key])
            q["mae_pts_" + key] = q["fade_sign"] * (adverse - q["exec_" + key])
            q["mae_bp_" + key] = q["mae_pts_" + key] / q["exec_" + key] * 10000.0
        return q

    def _equity_path(self, g, key, cost_mult, sizing_mode):
        equity = START_EQUITY
        curve = [equity]
        margins = []
        records = []

        for _, r in g.sort_values("trade_date").iterrows():
            entry = float(r["exec_" + key])
            spread = float(r["spread_" + key]) * cost_mult
            gross_pts = float(r["gross_pts_" + key])
            net_pts = gross_pts - spread

            if sizing_mode == "LIVE_MIN_0p01":
                stake = MIN_STAKE
            elif sizing_mode == "ONE_X_NOTIONAL":
                stake = self._round_stake(equity / entry) if equity > 0 else 0.0
            else:
                raise ValueError("unknown sizing mode")

            equity_before = equity
            margin = stake * entry * MARGIN_RATE
            margin_util = margin / equity_before if equity_before > 0 else np.inf
            gross_gbp = stake * gross_pts
            net_gbp = stake * net_pts
            equity = equity_before + net_gbp
            margins.append(margin_util)
            curve.append(equity)
            records.append({
                "signal_date": r["signal_date"],
                "trade_date": r["trade_date"],
                "stake": stake,
                "equity_before": equity_before,
                "equity_after": equity,
                "margin": margin,
                "margin_util": margin_util,
                "gross_gbp": gross_gbp,
                "net_gbp": net_gbp,
                "net_pts": net_pts,
            })

        return {
            "end_equity": equity,
            "curve": curve,
            "margins": np.asarray(margins, float),
            "records": records,
        }

    def _summary(self, fam, period, g, tname, key, cname, cost_mult, sizing_mode):
        if len(g) == 0:
            return
        gbp = g["gross_bp_" + key].to_numpy(float)
        gpt = g["gross_pts_" + key].to_numpy(float)
        entry = g["exec_" + key].to_numpy(float)
        spread = g["spread_" + key].to_numpy(float) * cost_mult
        nbp = gbp - spread / entry * 10000.0
        npt = gpt - spread
        mae = g["mae_bp_" + key].to_numpy(float)
        path = self._equity_path(g, key, cost_mult, sizing_mode)
        margins = path["margins"]

        first = pd.Timestamp(g["trade_date"].min())
        last = pd.Timestamp(g["trade_date"].max())
        span_years = max(1.0, (last - first).days / 365.25)

        self.log(
            f"IGFADE_SUMMARY,{fam},{period},{tname},{key},{cname},{sizing_mode},"
            f"n={len(g)},tradesPerYear={len(g)/span_years:.3f},"
            f"grossMeanBp={np.mean(gbp):.3f},grossMedianBp={np.median(gbp):.3f},grossHit={np.mean(gbp>0):.3f},"
            f"netMeanBp={np.mean(nbp):.3f},netMedianBp={np.median(nbp):.3f},netHit={np.mean(nbp>0):.3f},"
            f"grossMeanPts={np.mean(gpt):.3f},netMeanPts={np.mean(npt):.3f},"
            f"breakEvenBp={np.mean(gbp):.3f},breakEvenPts={np.mean(gpt):.3f},"
            f"meanMAEBp={np.mean(mae):.3f},worstMAEBp={np.min(mae):.3f},"
            f"pnlGBP={path['end_equity']-START_EQUITY:.2f},endEquity={path['end_equity']:.2f},"
            f"maxDD={self._mdd(path['curve']):.4f},"
            f"marginP95={np.percentile(margins,95):.4f},marginMax={np.max(margins):.4f}"
        )

    def _years(self, fam, q):
        # Year chronology is primary 09:31 only. Both cost cases are reported.
        key = "0931"
        for tname, threshold in THRESHOLDS[fam].items():
            e = q[q["abs_z"] >= threshold]
            for cname, cost_mult in COSTS:
                for year, y in e.groupby(e["trade_date"].dt.year):
                    gbp = y["gross_bp_" + key].to_numpy(float)
                    entry = y["exec_" + key].to_numpy(float)
                    spread = y["spread_" + key].to_numpy(float) * cost_mult
                    nbp = gbp - spread / entry * 10000.0
                    p1 = self._equity_path(y, key, cost_mult, "ONE_X_NOTIONAL")
                    pm = self._equity_path(y, key, cost_mult, "LIVE_MIN_0p01")
                    self.log(
                        f"IGFADE_YEAR,{fam},{tname},{key},{cname},{year},"
                        f"n={len(y)},grossMeanBp={np.mean(gbp):.3f},grossMedianBp={np.median(gbp):.3f},"
                        f"grossHit={np.mean(gbp>0):.3f},netMeanBp={np.mean(nbp):.3f},"
                        f"netMedianBp={np.median(nbp):.3f},netHit={np.mean(nbp>0):.3f},"
                        f"pnlGBP_1x={p1['end_equity']-START_EQUITY:.2f},"
                        f"pnlGBP_min={pm['end_equity']-START_EQUITY:.2f}"
                    )

    def _direction_split(self, fam, q):
        # Primary entry / base cost only. This is descriptive, not a filter.
        key = "0931"
        for tname, threshold in THRESHOLDS[fam].items():
            e = q[q["abs_z"] >= threshold].copy()
            for label, mask in (("AFTER_UP", e["intraday_return"] > 0),
                                ("AFTER_DOWN", e["intraday_return"] < 0)):
                g = e[mask]
                if len(g) == 0:
                    continue
                gbp = g["gross_bp_" + key].to_numpy(float)
                entry = g["exec_" + key].to_numpy(float)
                spread = g["spread_" + key].to_numpy(float)
                nbp = gbp - spread / entry * 10000.0
                self.log(
                    f"IGFADE_DIR,{fam},{tname},{label},n={len(g)},"
                    f"grossMeanBp={np.mean(gbp):.3f},grossHit={np.mean(gbp>0):.3f},"
                    f"netMeanBp={np.mean(nbp):.3f},netHit={np.mean(nbp>0):.3f}"
                )

    def _ledger(self, fam, q):
        # Full ledger is emitted for the primary NDX strategy only to keep QC logs tractable.
        # P80 contains P90/P95 events too, and flags preserve nested threshold membership.
        if fam != "NDX":
            return
        key = "0931"
        e = q[q["abs_z"] >= THRESHOLDS[fam]["P80"]].sort_values("trade_date")

        # P80 1x-notional path provides executable stake/equity fields in the ledger.
        path = self._equity_path(e, key, 1.0, "ONE_X_NOTIONAL")
        rec_by_date = {str(pd.Timestamp(x["trade_date"]).date()): x for x in path["records"]}

        for _, r in e.iterrows():
            td = str(pd.Timestamp(r["trade_date"]).date())
            er = rec_by_date[td]
            flags = "|".join(n for n, t in THRESHOLDS[fam].items() if float(r["abs_z"]) >= t)
            entry = float(r["exec_0931"])
            spread = float(r["spread_0931"])
            gross_bp = float(r["gross_bp_0931"])
            net_bp = gross_bp - spread / entry * 10000.0
            self.log(
                "IGFADE_TRADE,NDX,"
                f"signalDate={pd.Timestamp(r['signal_date']).date()},tradeDate={td},"
                f"z={float(r['z']):.6f},absZ={float(r['abs_z']):.6f},"
                f"signalRet={float(r['intraday_return']):.8f},fadeSign={int(r['fade_sign'])},flags={flags},"
                f"entry0931={entry:.4f},exit1000={float(r['exec_1000']):.4f},spread={spread:.2f},"
                f"grossBp={gross_bp:.3f},netBp={net_bp:.3f},grossPts={float(r['gross_pts_0931']):.3f},"
                f"maeBp={float(r['mae_bp_0931']):.3f},stake1x={er['stake']:.2f},"
                f"marginUtil={er['margin_util']:.4f},grossGBP={er['gross_gbp']:.2f},"
                f"netGBP={er['net_gbp']:.2f},equityBefore={er['equity_before']:.2f},"
                f"equityAfter={er['equity_after']:.2f},"
                f"entry0932={float(r['exec_0932']):.4f},grossBp0932={float(r['gross_bp_0932']):.3f},"
                f"entry0935={float(r['exec_0935']):.4f},grossBp0935={float(r['gross_bp_0935']):.3f}"
            )

    def on_end_of_algorithm(self):
        if len(self.rows) < 500:
            self.set_runtime_statistic("IGFADE Status", f"FAIL rows={len(self.rows)}")
            return

        df = pd.DataFrame(self.rows)
        ndx = self._enrich("NDX", df[df.family == "NDX"].copy())
        spx = self._enrich("SPX", df[df.family == "SPX"].copy())

        if len(ndx) == 0 or len(spx) == 0:
            self.set_runtime_statistic("IGFADE Status", f"FAIL NDX={len(ndx)} SPX={len(spx)}")
            return

        self._export_chart_data(ndx, spx)
        self.set_runtime_statistic(
            "IGFADE QA",
            f"rows={len(df)} NDX={len(ndx)} SPX={len(spx)}"
        )
        self.set_runtime_statistic(
            "IGFADE Bars",
            f"NDX={self.exec_bar_count['NDX']} SPX={self.exec_bar_count['SPX']}"
        )
        # One compact log line only. Runtime statistics + Download Results are the
        # authoritative output path for this run.
        self.log(
            f"IGFADE_EXPORT_READY,rows={len(df)},NDX={len(ndx)},SPX={len(spx)},"
            f"chart=IGFADE_EXPORT"
        )