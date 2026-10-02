# O1 SPXW data-feasibility diagnostic
# Frozen spec:
# research/options_dealer_gamma/SPEC_O1_FEASIBILITY.md
#
# Run in QuantConnect Research, not as a backtest.
# This script does NOT calculate any predictive return or trading outcome.

from AlgorithmImports import *
from QuantConnect.Research import QuantBook

import numpy as np
import pandas as pd
from datetime import datetime

PROBE_DATES = [
    datetime(2025, 11, 5),
    datetime(2026, 9, 24),
]

MIN_MINUTE_ROWS = 100


def count_rows(obj):
    if obj is None:
        return 0
    try:
        return len(obj)
    except Exception:
        return 0


def time_bounds(df):
    if df is None or len(df) == 0:
        return None, None
    x = df.reset_index()
    x.columns = [str(c).lower() for c in x.columns]
    candidates = [c for c in x.columns if c in ("time", "endtime") or "time" in c]
    if not candidates:
        return None, None
    t = pd.to_datetime(x[candidates[0]], errors="coerce").dropna()
    if t.empty:
        return None, None
    return t.min(), t.max()


def probe_date(probe_dt):
    date_str = probe_dt.date().isoformat()

    qb = QuantBook()
    qb.set_time_zone(TimeZones.NEW_YORK)
    qb.set_start_date(probe_dt.year, probe_dt.month, probe_dt.day)

    underlying = qb.add_index("SPX", Resolution.MINUTE).symbol

    canonical = Symbol.create_canonical_option(
        underlying,
        "SPXW",
        Market.USA,
        "?SPXW"
    )

    chain_obj = qb.option_chain(canonical, flatten=True)
    chain = chain_obj.data_frame

    if chain is None or len(chain) == 0:
        print(f"O1_FEASIBILITY_DATE,date={date_str},FAIL,reason=EMPTY_SPXW_CHAIN")
        return False

    df = chain.copy()

    if isinstance(df.index, pd.MultiIndex):
        contract_symbols = list(df.index.get_level_values(-1))
    else:
        contract_symbols = list(df.index)

    df["_contract_symbol"] = contract_symbols
    df.columns = [str(c).lower() for c in df.columns]

    required_cols = [
        "expiry",
        "strike",
        "right",
        "openinterest",
        "delta",
        "gamma",
        "impliedvolatility",
        "volume",
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(
            f"O1_FEASIBILITY_DATE,date={date_str},FAIL,"
            f"reason=MISSING_COLUMNS,missing={';'.join(missing_cols)},"
            f"columns={';'.join(map(str, df.columns))}"
        )
        return False

    expiry_date = pd.to_datetime(df["expiry"], errors="coerce").dt.date
    zero = df.loc[expiry_date == probe_dt.date()].copy()

    if zero.empty:
        print(
            f"O1_FEASIBILITY_DATE,date={date_str},FAIL,"
            f"reason=NO_0DTE,chain_rows={len(df)}"
        )
        return False

    for c in ["strike", "openinterest", "delta", "gamma", "impliedvolatility", "volume"]:
        zero[c] = pd.to_numeric(zero[c], errors="coerce")

    oi_nonnull = int(zero["openinterest"].notna().sum())
    gamma_nonnull = int(zero["gamma"].notna().sum())
    delta_nonnull = int(zero["delta"].notna().sum())
    iv_nonnull = int(zero["impliedvolatility"].notna().sum())
    volume_nonnull = int(zero["volume"].notna().sum())

    usable = zero[
        zero["openinterest"].notna() &
        zero["gamma"].notna()
    ].copy()

    if usable.empty:
        print(
            f"O1_FEASIBILITY_DATE,date={date_str},FAIL,"
            f"reason=NO_USABLE_OI_GAMMA,"
            f"chain_rows={len(df)},zero_dte_rows={len(zero)},"
            f"oi_nonnull={oi_nonnull},gamma_nonnull={gamma_nonnull}"
        )
        return False

    usable["_vol_rank"] = usable["volume"].fillna(-1.0)
    usable["_oi_rank"] = usable["openinterest"].fillna(-1.0)
    usable = usable.sort_values(
        ["_vol_rank", "_oi_rank"],
        ascending=[False, False]
    )

    row = usable.iloc[0]
    contract_symbol = row["_contract_symbol"]

    qb.add_index_option_contract(contract_symbol, fill_forward=False)

    start = datetime(probe_dt.year, probe_dt.month, probe_dt.day, 9, 30)
    end = datetime(probe_dt.year, probe_dt.month, probe_dt.day, 16, 1)

    try:
        trade_hist = qb.history(
            TradeBar,
            contract_symbol,
            start,
            end,
            Resolution.MINUTE
        )
    except Exception as e:
        trade_hist = None
        trade_error = repr(e)
    else:
        trade_error = ""

    try:
        quote_hist = qb.history(
            QuoteBar,
            contract_symbol,
            start,
            end,
            Resolution.MINUTE
        )
    except Exception as e:
        quote_hist = None
        quote_error = repr(e)
    else:
        quote_error = ""

    trade_rows = count_rows(trade_hist)
    quote_rows = count_rows(quote_hist)
    minute_rows = max(trade_rows, quote_rows)

    tmin_trade, tmax_trade = time_bounds(trade_hist)
    tmin_quote, tmax_quote = time_bounds(quote_hist)

    pass_date = (
        len(df) > 0
        and len(zero) > 0
        and oi_nonnull > 0
        and gamma_nonnull > 0
        and minute_rows >= MIN_MINUTE_ROWS
    )

    print(
        f"O1_FEASIBILITY_DATE,"
        f"date={date_str},"
        f"status={'PASS' if pass_date else 'FAIL'},"
        f"chain_rows={len(df)},"
        f"zero_dte_rows={len(zero)},"
        f"oi_nonnull={oi_nonnull},"
        f"gamma_nonnull={gamma_nonnull},"
        f"delta_nonnull={delta_nonnull},"
        f"iv_nonnull={iv_nonnull},"
        f"volume_nonnull={volume_nonnull},"
        f"selected={contract_symbol},"
        f"selected_strike={row['strike']},"
        f"selected_right={row['right']},"
        f"selected_volume={row['volume']},"
        f"selected_oi={row['openinterest']},"
        f"selected_gamma={row['gamma']},"
        f"trade_minute_rows={trade_rows},"
        f"quote_minute_rows={quote_rows},"
        f"trade_min={tmin_trade},trade_max={tmax_trade},"
        f"quote_min={tmin_quote},quote_max={tmax_quote},"
        f"trade_error={trade_error},quote_error={quote_error}"
    )

    return pass_date


print("O1_FEASIBILITY_BEGIN")
results = []

for d in PROBE_DATES:
    try:
        ok = probe_date(d)
    except Exception as e:
        print(
            f"O1_FEASIBILITY_DATE,date={d.date().isoformat()},"
            f"FAIL,reason=UNCAUGHT_EXCEPTION,error={repr(e)}"
        )
        ok = False
    results.append(ok)

overall = all(results)

print(
    f"O1_FEASIBILITY_END,"
    f"status={'PASS' if overall else 'FAIL'},"
    f"dates_passed={sum(results)}/{len(results)},"
    f"minute_row_gate={MIN_MINUTE_ROWS}"
)

if overall:
    print(
        "O1_NEXT=DATA_GATE_PASSED;"
        "freeze_identification_proxy_control_split_and_kill_rule_before_any_outcome_test"
    )
else:
    print(
        "O1_NEXT=DATA_GATE_FAILED;"
        "do_not_change_probe_dates_or_run_outcome_test"
    )
