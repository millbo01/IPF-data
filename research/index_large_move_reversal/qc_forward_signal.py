from AlgorithmImports import *
import numpy as np
import pandas as pd
from datetime import datetime

P90 = 1.7796
P95 = 2.3646


class NdxMorningFadeForwardSignal(QCAlgorithm):
    """Signal-only QuantConnect job for the frozen V3 forward shadow.

    No orders. Emits one compact FORWARD_SIGNAL log line for the latest
    completed signal session. Signal definition is intentionally identical
    to V1/V2: QQQ previous regular close -> 15:45 NY, 252-session rolling
    z-score using prior observations only, min 60.
    """

    def initialize(self):
        self.set_start_date(2024, 1, 2)
        end_text = self.get_parameter("END_DATE")
        if end_text:
            y, m, d = [int(x) for x in end_text.split("-")]
            self.set_end_date(y, m, d)
        else:
            now = datetime.utcnow()
            self.set_end_date(now.year, now.month, now.day)
        self.set_cash(100000)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.qqq = self.add_equity("QQQ", Resolution.MINUTE).symbol
        self.prev_close = None
        self.today_signal = None
        self.rows = []
        self.day = None
        self.log("FORWARD_SIGNAL_BEGIN,V3_P90_0931_1000")

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
            self.today_signal = None

        bar = self._bar(data, self.qqq)
        if bar is None:
            return

        if self.time.hour == 15 and self.time.minute == 45:
            if self.prev_close is not None and self.prev_close > 0:
                px = float(bar.close)
                self.today_signal = {
                    "signal_date": pd.Timestamp(d),
                    "intraday_return": px / self.prev_close - 1.0,
                    "proxy_1545": px,
                    "prev_close": float(self.prev_close),
                }

        if self.time.hour == 16 and self.time.minute == 0:
            px = float(bar.close)
            if self.today_signal is not None:
                self.rows.append(dict(self.today_signal))
            self.prev_close = px

    def on_end_of_algorithm(self):
        if len(self.rows) < 60:
            self.log(f"FORWARD_SIGNAL_FAIL,rows={len(self.rows)}")
            return

        df = pd.DataFrame(self.rows).sort_values("signal_date").reset_index(drop=True)
        s = df["intraday_return"]
        mu = s.shift(1).rolling(252, min_periods=60).mean()
        sd = s.shift(1).rolling(252, min_periods=60).std()
        df["rolling_mean"] = mu
        df["rolling_sd"] = sd
        df["z"] = (s - mu) / sd
        q = df.dropna(subset=["z"]).iloc[-1]
        z = float(q["z"])
        ret = float(q["intraday_return"])
        self.log(
            "FORWARD_SIGNAL,"
            f"signalDate={pd.Timestamp(q['signal_date']).date()},"
            f"z={z:.8f},absZ={abs(z):.8f},"
            f"signalRet={ret:.10f},"
            f"p90={int(abs(z) >= P90)},p95={int(abs(z) >= P95)},"
            f"proxy1545={float(q['proxy_1545']):.6f},"
            f"prevClose={float(q['prev_close']):.6f},"
            f"rollingMean={float(q['rolling_mean']):.10f},"
            f"rollingSd={float(q['rolling_sd']):.10f},"
            f"rows={len(df)}"
        )