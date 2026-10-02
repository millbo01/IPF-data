# QuantConnect Free-tier forward signal checker
# Frozen V3 NDX/QQQ morning-fade signal only. No orders.
#
# Output:
#   FORWARD_CHECK,NO_SIGNAL,...
# or
#   FORWARD_CHECK,P90_TRIGGER,...,P95=yes/no,...
#
# Run after the US regular close. This script checks only the most recent
# completed regular session available in the backtest data.
#
# Frozen signal:
# - QQQ return from previous regular-session close to 15:45 New York
# - z-score over prior 252 observations only, min 60
# - P90 = 1.7796 primary
# - P95 = 2.3646 secondary subset
#
# No threshold re-estimation. No trade simulation. No order placement.

from AlgorithmImports import *
import numpy as np
import pandas as pd

P90 = 1.7796
P95 = 2.3646

class NdxForwardSignalChecker(QCAlgorithm):
    def initialize(self):
        # Dynamic ~1000-day window: long enough for the frozen 252-session
        # prior-only z-score and usable throughout the prospective phase.
        today = datetime.utcnow().date()
        start = today - timedelta(days=1000)
        self.set_start_date(start.year, start.month, start.day)
        self.set_end_date(today.year, today.month, today.day)
        self.set_cash(100000)
        self.set_time_zone(TimeZones.NEW_YORK)

        self.qqq = self.add_equity("QQQ", Resolution.MINUTE).symbol

        self.prev_close = None
        self.current_signal = None
        self.rows = []
        self.day = None

        self.log("FORWARD_CHECK_BEGIN")

    def _bar(self, data):
        try:
            return data.bars[self.qqq] if self.qqq in data.bars else None
        except Exception:
            return None

    def on_data(self, data):
        d = self.time.date()
        if d != self.day:
            self.day = d
            self.current_signal = None

        b = self._bar(data)
        if b is None:
            return

        if self.time.hour == 15 and self.time.minute == 45:
            if self.prev_close is not None and self.prev_close > 0:
                px = float(b.close)
                self.current_signal = {
                    "date": pd.Timestamp(d),
                    "ret": px / self.prev_close - 1.0,
                    "px1545": px,
                }

        if self.time.hour == 16 and self.time.minute == 0:
            px = float(b.close)
            if self.current_signal is not None:
                r = dict(self.current_signal)
                r["close"] = px
                self.rows.append(r)
            self.prev_close = px

    @staticmethod
    def _rolling_z(s):
        mu = s.shift(1).rolling(252, min_periods=60).mean()
        sd = s.shift(1).rolling(252, min_periods=60).std()
        return (s - mu) / sd

    def on_end_of_algorithm(self):
        if len(self.rows) < 61:
            self.log(f"FORWARD_CHECK,ERROR,insufficient_rows={len(self.rows)}")
            return

        df = pd.DataFrame(self.rows).sort_values("date").reset_index(drop=True)
        df["z"] = self._rolling_z(df["ret"])
        df = df.dropna(subset=["z"])

        if df.empty:
            self.log("FORWARD_CHECK,ERROR,no_valid_z")
            return

        r = df.iloc[-1]
        z = float(r["z"])
        abs_z = abs(z)
        sig = "UP" if float(r["ret"]) > 0 else "DOWN"
        fade = "SELL" if sig == "UP" else "BUY"
        p95 = "yes" if abs_z >= P95 else "no"
        status = "P90_TRIGGER" if abs_z >= P90 else "NO_SIGNAL"

        self.log(
            f"FORWARD_CHECK,{status},signal_date={r['date'].date()},"
            f"ret_bp={float(r['ret'])*10000:.3f},z={z:.6f},abs_z={abs_z:.6f},"
            f"signal={sig},fade={fade},P95={p95}"
        )
        self.log("FORWARD_CHECK_END")
