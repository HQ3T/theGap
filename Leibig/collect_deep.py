"""Deep data collector for the focused universe.

Pulls, per company, the full statement history (4-5 yrs) needed for original
*alpha* features: R&D, buybacks, dividends, CapEx, CapEx trend, revenue trend,
free cash flow, governance risk, employees. All cached per-symbol.

Design: go deep (multi-year) on ~50 names rather than shallow on 500. The same
code scales to any N — the bottleneck is Yahoo rate limits, not the framework.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "deep"
INFO_KEYS = [
    "sector", "industry", "fullTimeEmployees", "marketCap", "totalRevenue",
    "grossMargins", "operatingMargins", "profitMargins", "ebitdaMargins",
    "returnOnEquity", "returnOnAssets", "debtToEquity", "currentRatio",
    "revenueGrowth", "earningsGrowth", "payoutRatio", "dividendYield", "beta",
    "totalCash", "totalDebt", "ebitda", "freeCashflow", "operatingCashflow",
    "boardRisk", "compensationRisk", "shareHolderRightsRisk",
    "auditRisk", "overallRisk", "governanceEpochDate",
    "recommendationKey", "targetMeanPrice", "currentPrice",
]


def _num(x):
    try:
        f = float(x)
        if f != f or f in (float("inf"), float("-inf")):
            return None
        return f
    except Exception:
        return None


def _series(df, key):
    """Return the row `key` as a list (oldest->newest) or None."""
    if df is None or df.empty or key not in df.index:
        return None
    row = df.loc[key]
    vals = [_num(v) for v in row.values]
    if all(v is None for v in vals):
        return None
    return list(reversed(vals))  # oldest first


def _pull(symbol):
    t = yf.Ticker(symbol)
    info = {}
    for _ in range(3):
        try:
            info = t.info or {}
            if info:
                break
        except Exception:
            time.sleep(1.5)
    rec = {"symbol": symbol}
    for k in INFO_KEYS:
        if k in ("sector", "industry", "recommendationKey"):
            rec[k] = info.get(k)
        else:
            rec[k] = _num(info.get(k))
    try:
        inc = t.income_stmt
    except Exception:
        inc = None
    try:
        bs = t.balance_sheet
    except Exception:
        bs = None
    try:
        cf = t.cashflow
    except Exception:
        cf = None

    rec["years"] = [str(c)[:10] for c in (inc.columns if inc is not None and not inc.empty else [])][::-1]
    # multi-year series (oldest first)
    rec["revenue_series"] = _series(inc, "Total Revenue")
    rec["net_income_series"] = _series(inc, "Net Income")
    rec["rnd_series"] = _series(inc, "Research And Development")
    rec["ebit_series"] = _series(inc, "EBIT")
    rec["interest_expense_series"] = _series(inc, "Interest Expense")
    rec["total_assets_series"] = _series(bs, "Total Assets")
    rec["total_debt_series"] = _series(bs, "Total Debt")
    rec["stockholders_equity_series"] = _series(bs, "Stockholders Equity")
    rec["capex_series"] = _series(cf, "Capital Expenditure")
    rec["depreciation_series"] = _series(cf, "Depreciation And Amortization")
    rec["buyback_series"] = _series(cf, "Repurchase Of Capital Stock")
    rec["dividends_paid_series"] = _series(cf, "Cash Dividends Paid")
    rec["fcf_series"] = _series(cf, "Free Cash Flow")
    rec["ocf_series"] = _series(cf, "Operating Cash Flow")
    # balance-sheet items for the Financial Health (F) dimension
    rec["current_assets_series"] = _series(bs, "Current Assets")
    rec["current_liabilities_series"] = _series(bs, "Current Liabilities")
    rec["retained_earnings_series"] = _series(bs, "Retained Earnings")
    rec["total_liabilities_series"] = _series(bs, "Total Liabilities Net Minority Interest")
    return rec


def collect(symbols, force=False, sleep=0.4):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    n = len(symbols)
    for i, sym in enumerate(symbols, 1):
        cf = CACHE_DIR / f"{sym}.json"
        if cf.exists() and not force:
            try:
                out.append(json.loads(cf.read_text()))
                continue
            except Exception:
                pass
        try:
            rec = _pull(sym)
            cf.write_text(json.dumps(rec))
            out.append(rec)
            print(f"  [{i}/{n}] {sym} OK")
        except Exception as e:
            rec = {"symbol": sym, "_error": str(e)}
            cf.write_text(json.dumps(rec))
            out.append(rec)
            print(f"  [{i}/{n}] {sym} ERR {e}")
        time.sleep(sleep)
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from universe import UNIVERSE
    data = collect(UNIVERSE, force="--force" in sys.argv)
    ok = sum(1 for d in data if "_error" not in d)
    print(f"Done: {ok}/{len(data)} ok")
