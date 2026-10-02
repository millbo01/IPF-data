# Index large-move next-session morning fade — IG execution v2
# QuantConnect Python. No orders.
#
# Signal is unchanged from v1:
#   QQQ/SPY return from previous regular-session close to 15:45 NY
#   252-session rolling z-score using prior observations only (min 60)
# Fixed thresholds:
#   NDX P80=1.2681 P90=1.7796 P95=2.3646
#   SPX P80=1.2278 P90=1.7595 P95=2.2530
#
# Trade T+1: fade signal sign, enter 09:31 primary; 09:32/09:35 sensitivity;
# exit 10:00. Execution P&L uses NDX/SPX cash-index minute data.
#
# Costs:
#   NDX DFB 1 point 14:30-21:00 London, 2 points surrounding period.
#   SPX DFB 0.4 / 0.6 points on same schedule.
#   STRESS2X doubles full round-trip spread.
# Stake cases: PUBLIC_MIN £1/point; API_0p01_CONDITIONAL £0.01/point.
# Margin: 5%. Starting equity £2,000.
#
# Logs: IGFADE_QA, IGFADE_SUMMARY, IGFADE_YEAR, IGFADE_TRADE.

from AlgorithmImports import *
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
ENTRIES = [("0931",9,31),("0932",9,32),("0935",9,35)]
COSTS = [("BASE",1.0),("STRESS2X",2.0)]
STAKES = [("PUBLIC_MIN",1.0),("API_0p01_CONDITIONAL",0.01)]
START_EQUITY = 2000.0
MARGIN_RATE = 0.05

class IndexMorningFadeIG(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2012,1,3)
        self.set_end_date(2026,9,29)
        self.set_cash(100000)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.spy = self.add_equity("SPY", Resolution.MINUTE).symbol
        self.qqq = self.add_equity("QQQ", Resolution.MINUTE).symbol
        self.spx = self.add_index("SPX", Resolution.MINUTE).symbol
        self.ndx = self.add_index("NDX", Resolution.MINUTE).symbol
        self.proxy = {"SPX":self.spy,"NDX":self.qqq}
        self.execsym = {"SPX":self.spx,"NDX":self.ndx}
        self.prev_close = {"SPX":None,"NDX":None}
        self.pending = {"SPX":None,"NDX":None}
        self.signal = {}
        self.day = None
        self.rows = []
        self.log("IGFADE_BEGIN")
        self.log("VERSION=V2_IG_EXECUTION_FIXED_THRESHOLDS")

    @staticmethod
    def _bar(data,s):
        try: return data.bars[s] if s in data.bars else None
        except: return None

    def on_data(self,data):
        d = self.time.date()
        if d != self.day:
            self.day = d
            self.signal = {}
        pbar = {f:self._bar(data,s) for f,s in self.proxy.items()}
        ebar = {f:self._bar(data,s) for f,s in self.execsym.items()}

        for key,hh,mm in ENTRIES:
            if self.time.hour == hh and self.time.minute == mm:
                for fam in ("SPX","NDX"):
                    p,b = self.pending[fam],ebar[fam]
                    if p is None or b is None: continue
                    px=float(b.close)
                    p["trade_date"]=pd.Timestamp(d)
                    p["exec_"+key]=px
                    p["min_"+key]=px
                    p["max_"+key]=px

        for fam in ("SPX","NDX"):
            p,b = self.pending[fam],ebar[fam]
            if p is None or b is None: continue
            for key,hh,mm in ENTRIES:
                ep=p.get("exec_"+key)
                if ep is None or not np.isfinite(ep): continue
                after=(self.time.hour>hh) or (self.time.hour==hh and self.time.minute>mm)
                before=(self.time.hour<10) or (self.time.hour==10 and self.time.minute<=0)
                if after and before:
                    p["min_"+key]=min(float(p["min_"+key]),float(b.low))
                    p["max_"+key]=max(float(p["max_"+key]),float(b.high))

        if self.time.hour==10 and self.time.minute==0:
            for fam in ("SPX","NDX"):
                p,b=self.pending[fam],ebar[fam]
                if p is None or b is None: continue
                p["exec_1000"]=float(b.close)
                p["complete"]=True
                self.pending[fam]=None

        if self.time.hour==15 and self.time.minute==45:
            for fam in ("SPX","NDX"):
                b,prev=pbar[fam],self.prev_close[fam]
                if b is None or prev is None or prev<=0: continue
                px=float(b.close)
                self.signal[fam]={"signal_date":pd.Timestamp(d),"family":fam,
                                  "intraday_return":px/prev-1.0,"proxy_1545":px}

        if self.time.hour==16 and self.time.minute==0:
            for fam in ("SPX","NDX"):
                b=pbar[fam]
                if b is None: continue
                px=float(b.close)
                s=self.signal.get(fam)
                if s is not None:
                    r=dict(s); r["proxy_close"]=px; r["trade_date"]=pd.NaT; r["complete"]=False
                    for key,_,_ in ENTRIES:
                        r["exec_"+key]=np.nan; r["min_"+key]=np.nan; r["max_"+key]=np.nan
                    r["exec_1000"]=np.nan
                    self.rows.append(r); self.pending[fam]=r
                self.prev_close[fam]=px

    @staticmethod
    def _rolling_z(s):
        mu=s.shift(1).rolling(252,min_periods=60).mean()
        sd=s.shift(1).rolling(252,min_periods=60).std()
        return (s-mu)/sd

    @staticmethod
    def _spread(fam,trade_date,key):
        hhmm={"0931":"09:31","0932":"09:32","0935":"09:35"}[key]
        ts=pd.Timestamp(str(pd.Timestamp(trade_date).date())+" "+hhmm,tz="America/New_York")
        lon=ts.tz_convert("Europe/London")
        m=lon.hour*60+lon.minute
        core=(14*60+30)<=m<21*60
        if fam=="NDX": return 1.0 if core else 2.0
        return 0.4 if core else 0.6

    @staticmethod
    def _mdd(eq):
        a=np.asarray(eq,float); peak=np.maximum.accumulate(a)
        return float(np.min(a/peak-1.0))

    def _enrich(self,fam,q):
        q=q.sort_values("signal_date").reset_index(drop=True).copy()
        q["z"]=self._rolling_z(q["intraday_return"]); q["abs_z"]=q["z"].abs()
        q["fade_sign"]=-np.sign(q["intraday_return"])
        q=q.dropna(subset=["z","trade_date","exec_1000"]).copy()
        for key,_,_ in ENTRIES:
            q=q.dropna(subset=["exec_"+key]).copy()
            q["gross_ret_"+key]=q["fade_sign"]*(q["exec_1000"]/q["exec_"+key]-1.0)
            q["gross_bp_"+key]=q["gross_ret_"+key]*10000
            q["gross_pts_"+key]=q["fade_sign"]*(q["exec_1000"]-q["exec_"+key])
            q["spread_"+key]=[self._spread(fam,d,key) for d in q["trade_date"]]
            adverse=np.where(q["fade_sign"]>0,q["min_"+key],q["max_"+key])
            q["mae_pts_"+key]=q["fade_sign"]*(adverse-q["exec_"+key])
            q["mae_bp_"+key]=q["mae_pts_"+key]/q["exec_"+key]*10000
        return q

    def _summary(self,fam,period,g,tname,key,cname,cmult,sname,stake):
        if len(g)==0: return
        gbp=g["gross_bp_"+key].to_numpy(float)
        gpt=g["gross_pts_"+key].to_numpy(float)
        entry=g["exec_"+key].to_numpy(float)
        sp=g["spread_"+key].to_numpy(float)*cmult
        nbp=gbp-sp/entry*10000
        npt=gpt-sp
        mae=g["mae_bp_"+key].to_numpy(float)
        eq=START_EQUITY; curve=[eq]; margins=[]
        for ep,p in zip(entry,npt):
            margins.append(stake*ep*MARGIN_RATE/eq if eq>0 else np.inf)
            eq+=stake*p; curve.append(eq)
        years=max(1,len(set(pd.Timestamp(x).year for x in g["trade_date"])))
        self.log(
          f"IGFADE_SUMMARY,{fam},{period},{tname},{key},{cname},{sname},"
          f"n={len(g)},tradesPerYear={len(g)/years:.3f},"
          f"grossMeanBp={np.mean(gbp):.3f},grossMedianBp={np.median(gbp):.3f},grossHit={np.mean(gbp>0):.3f},"
          f"netMeanBp={np.mean(nbp):.3f},netMedianBp={np.median(nbp):.3f},netHit={np.mean(nbp>0):.3f},"
          f"grossMeanPts={np.mean(gpt):.3f},netMeanPts={np.mean(npt):.3f},"
          f"breakEvenBp={np.mean(gbp):.3f},breakEvenPts={np.mean(gpt):.3f},"
          f"meanMAEBp={np.mean(mae):.3f},worstMAEBp={np.min(mae):.3f},"
          f"pnlGBP={stake*np.sum(npt):.2f},endEquity={eq:.2f},maxDD={self._mdd(curve):.4f},"
          f"marginP95={np.percentile(margins,95):.4f},marginMax={np.max(margins):.4f}"
        )

    def _years(self,fam,q):
        for tname,thr in THRESHOLDS[fam].items():
            e=q[q["abs_z"]>=thr]
            for key,_,_ in ENTRIES:
                for cname,cmult in COSTS:
                    for year,y in e.groupby(e["trade_date"].dt.year):
                        gbp=y["gross_bp_"+key].to_numpy(float)
                        gpt=y["gross_pts_"+key].to_numpy(float)
                        entry=y["exec_"+key].to_numpy(float)
                        sp=y["spread_"+key].to_numpy(float)*cmult
                        nbp=gbp-sp/entry*10000; npt=gpt-sp
                        self.log(
                          f"IGFADE_YEAR,{fam},{tname},{key},{cname},{year},"
                          f"n={len(y)},grossMeanBp={np.mean(gbp):.3f},grossMedianBp={np.median(gbp):.3f},"
                          f"grossHit={np.mean(gbp>0):.3f},netMeanBp={np.mean(nbp):.3f},"
                          f"netMedianBp={np.median(nbp):.3f},netHit={np.mean(nbp>0):.3f},"
                          f"pnlGBP_publicMin={np.sum(npt):.2f}"
                        )

    def _ledger(self,fam,q):
        e=q[q["abs_z"]>=THRESHOLDS[fam]["P80"]]
        for _,r in e.iterrows():
            flags="|".join(n for n,t in THRESHOLDS[fam].items() if float(r["abs_z"])>=t)
            p=["IGFADE_TRADE",fam,str(pd.Timestamp(r["signal_date"]).date()),
               str(pd.Timestamp(r["trade_date"]).date()),f"z={float(r['z']):.6f}",
               f"absZ={float(r['abs_z']):.6f}",f"signalRet={float(r['intraday_return']):.8f}",
               f"fadeSign={int(r['fade_sign'])}",f"flags={flags}",f"exit1000={float(r['exec_1000']):.4f}"]
            for key,_,_ in ENTRIES:
                ep=float(r["exec_"+key]); sp=float(r["spread_"+key]); gb=float(r["gross_bp_"+key])
                p += [f"entry{key}={ep:.4f}",f"spread{key}={sp:.2f}",f"grossBp{key}={gb:.3f}",
                      f"netBp{key}={gb-sp/ep*10000:.3f}",f"grossPts{key}={float(r['gross_pts_'+key]):.3f}",
                      f"maeBp{key}={float(r['mae_bp_'+key]):.3f}"]
            self.log(",".join(p))

    def on_end_of_algorithm(self):
        if len(self.rows)<500:
            self.log(f"IGFADE_FAIL,rows={len(self.rows)}"); return
        df=pd.DataFrame(self.rows)
        self.log(f"IGFADE_QA,rows={len(df)},complete={int(df.complete.sum())},"
                 f"start={df.signal_date.min().date()},end={df.signal_date.max().date()}")
        for fam in ("NDX","SPX"):
            q=self._enrich(fam,df[df.family==fam].copy())
            self._ledger(fam,q)
            for period,start,end in PERIODS:
                p=q[(q.signal_date>=start)&(q.signal_date<=end)]
                for tname,thr in THRESHOLDS[fam].items():
                    e=p[p.abs_z>=thr]
                    for key,_,_ in ENTRIES:
                        for cname,cmult in COSTS:
                            for sname,stake in STAKES:
                                self._summary(fam,period,e,tname,key,cname,cmult,sname,stake)
            self._years(fam,q)
        self.log("IGFADE_END")
