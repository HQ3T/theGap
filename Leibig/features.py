"""ESG feature computation — original, computed signals grouped by E / S / G.

This module ONLY computes features. No scoring, no ranking, no weights. Each
feature is named with a prefix so the dataset self-documents its dimension:
  E_*  Environmental
  S_*  Social
  G_*  Governance

Feature definitions and justifications are documented in docs/features.md.
All features are computed from free 4–5 year financial statements (yfinance):
income statement, balance sheet, cash flow, plus the info snapshot (which carries
ISS-derived governance risk scores). Multi-year history enables trend features
(CAGR, stability, slope) that a shallow single-year scrape cannot produce.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from emission_intensity import sector_intensity
from universe import SECTOR_OF
from worker_share import WORKER_SHARE_EST


# ---- helpers ---------------------------------------------------------------
def _num(x):
    try:
        f = float(x)
        if f != f or f in (float("inf"), float("-inf")):
            return None
        return f
    except Exception:
        return None


def _safe_div(a, b):
    try:
        a = float(a); b = float(b)
        if b == 0 or (a != a) or (b != b):
            return np.nan
        return a / b
    except Exception:
        return np.nan


def _cagr(series):
    """CAGR of a numeric series (oldest->newest), skipping None/<=0."""
    vals = [v for v in (series or []) if v is not None and v > 0]
    if len(vals) < 2:
        return np.nan
    n = len(vals) - 1
    first, last = vals[0], vals[-1]
    if first <= 0 or last <= 0:
        return np.nan
    return (last / first) ** (1.0 / n) - 1.0


def _last(series):
    vals = [v for v in (series or []) if v is not None]
    return vals[-1] if vals else None


def _cv(series):
    """Coefficient of variation (lower = more stable)."""
    vals = [v for v in (series or []) if v is not None]
    if len(vals) < 3:
        return np.nan
    arr = np.array(vals, dtype=float)
    m = arr.mean()
    if m == 0 or abs(m) < 1e-6:
        return np.nan
    return arr.std() / abs(m)


def _slope(series):
    """Linear slope of a series over time (robust to None/NaN)."""
    vals = [v for v in (series or [])
            if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if len(vals) < 2:
        return np.nan
    x = np.arange(len(vals))
    return float(np.polyfit(x, vals, 1)[0])


# ---- main builder ----------------------------------------------------------
def _mean_tax_share(ebit_series, ni_series):
    """Multi-year average of (EBIT - NetIncome) / EBIT, clipped to [0, 1].

    Uses only years where EBIT > 0, so a single loss year cannot inflate the
    ratio above 1 (the bug with the latest-year-only formula). Clipped to [0, 1]
    so a tax/interest burden above 100% of EBIT (e.g. distressed firm with
    negative net income despite positive EBIT) is capped, not rewarded.
    Returns np.nan if no usable year.
    """
    ebit = [v for v in (ebit_series or []) if v is not None]
    ni = [v for v in (ni_series or []) if v is not None]
    if not ebit or not ni or len(ebit) != len(ni):
        return np.nan
    shares = []
    for e, n in zip(ebit, ni):
        if e is None or n is None or e <= 0:
            continue
        s = (e - n) / e
        if s == s:  # not NaN
            shares.append(max(0.0, min(1.0, s)))
    if not shares:
        return np.nan
    return float(np.mean(shares))


def build_features(records: list[dict]) -> pd.DataFrame:
    """Compute all ESG features from the deep-collected records.

    Returns a DataFrame with columns prefixed E_ / S_ / G_ plus identifiers.
    """
    rows = []
    for r in records:
        if "_error" in r:
            continue
        sym = r["symbol"]
        rev = r.get("totalRevenue")
        emp = r.get("fullTimeEmployees")
        ni_abs = _last(r.get("net_income_series"))
        ebit = _last(r.get("ebit_series"))
        capex_abs = abs(_last(r.get("capex_series")) or 0)
        rnd_abs = _last(r.get("rnd_series"))
        # Use the authoritative GICS sector from our universe mapping, NOT the
        # yfinance-reported sector (which uses non-standard names like 'Basic
        # Materials' / 'Technology' that don't match our intensity dictionary).
        sector = SECTOR_OF.get(sym) or r.get("sector") or ""
        buybacks = abs(_last(r.get("buyback_series")) or 0)
        divs = abs(_last(r.get("dividends_paid_series")) or 0)
        fcf = _last(r.get("fcf_series")) or r.get("freeCashflow")
        cash = r.get("totalCash")
        debt = r.get("totalDebt")
        beta = r.get("beta")

        debt_series = r.get("total_debt_series") or []
        asset_series = r.get("total_assets_series") or []
        da_series = [_safe_div(d, a) for d, a in zip(debt_series, asset_series)]

        # --- Financial Health (F) inputs (latest year, real statements) ---
        dep_abs = abs(_last(r.get("depreciation_series")) or 0)  # D&A (>=0)
        ca = _last(r.get("current_assets_series"))               # current assets
        cl = _last(r.get("current_liabilities_series"))         # current liabilities
        re = _last(r.get("retained_earnings_series"))            # retained earnings
        tl = _last(r.get("total_liabilities_series"))           # total liabilities
        assets = _last(r.get("total_assets_series"))            # total assets
        interest_exp = abs(_last(r.get("interest_expense_series")) or 0)

        sci = sector_intensity(sector)["carbon_intensity"]  # tCO2e per US$1M revenue
        # Company-level estimated Scope 1 emissions (tCO2e):
        #   sector intensity (tCO2e/US$M) * company revenue (US$) / 1e6
        est_emissions_tco2e = _safe_div(sci * (rev or 0), 1e6) if rev else np.nan

        rows.append({
            "Symbol": sym,
            "Industry": r.get("industry"),
            # --- Environmental (E) ---
            # Three carbon-coupled features. The investment signal is made
            # CONDITIONAL on the firm's emissions burden: a firm earns
            # environmental credit only for spending adequate to its pollution,
            # not for spending in absolute terms (which let dirty industrials
            # like CAT score well by simply spending a lot in a dirty business).
            # Carbon intensity (tCO2e per US$M revenue) = estimated emissions /
            # revenue, the Trucost / S&P Global standard metric. Lower = cleaner.
            # Source: S&P Global 2019-20 Scope-1 sector intensity (tCO2e/US$M).
            "E_carbon_intensity": _safe_div(est_emissions_tco2e, (rev or 0) / 1e6) if rev else np.nan,
            "E_est_emissions_tco2e": est_emissions_tco2e,
            # Decarbonisation investment adequacy: total transition-relevant
            # capital (CapEx + R&D) per tonne of estimated CO2e. A firm only earns
            # E credit for investment adequate to its emissions burden. A
            # capital-intensive industrial with huge absolute CapEx but huge
            # emissions scores LOW (spending spread thin across a dirty asset
            # base); a clean-sector firm with modest spend but tiny emissions
            # scores HIGH. Higher = more decarbonisation capacity per unit of
            # pollution. Original carbon-coupled signal not in standard ESG.
            "E_decarb_investment_adequacy": _safe_div(capex_abs + (abs(rnd_abs) if rnd_abs else 0), est_emissions_tco2e) if est_emissions_tco2e else np.nan,
            # Emissions-to-assets: est. emissions per US$M of total assets.
            # Carbon efficiency of the PHYSICAL asset base — a different lens
            # from revenue intensity. A capital-intensive firm with a huge asset
            # base and high emissions scores worse than one with a lean base.
            # Lower = cleaner. Carbon-coupled, 51/51 coverage.
            "E_emissions_to_assets": _safe_div(est_emissions_tco2e, (assets or 0) / 1e6) if (est_emissions_tco2e and assets) else np.nan,
            # Transition readiness: free cash flow per tonne of CO2e. Financial
            # firepower to fund the decarbonisation transition per unit of
            # pollution. A dirty firm with weak cash flow has no capacity to
            # transition; a clean firm with strong cash flow does. Higher = better.
            # Carbon-coupled, 51/51 coverage.
            "E_transition_readiness": _safe_div(fcf, est_emissions_tco2e) if (fcf and est_emissions_tco2e) else np.nan,
            # --- Social (S) ---
            "S_worker_share": WORKER_SHARE_EST.get(sym, _safe_div((emp * 80000) if emp else None, rev)),
            "S_shareholder_return": min(_safe_div(buybacks + divs, ni_abs if ni_abs and ni_abs > 0 else None), 1.0)
            if (ni_abs and ni_abs > 0) else np.nan,
            "S_tax_contribution": _mean_tax_share(r.get("ebit_series"), r.get("net_income_series")),
            "S_reinvestment_ratio": _safe_div(capex_abs + (abs(rnd_abs) if rnd_abs else 0), rev),
            # --- Governance (G) ---
            "G_board_risk": r.get("boardRisk"),
            "G_compensation_risk": r.get("compensationRisk"),
            "G_shareholder_rights_risk": r.get("shareHolderRightsRisk"),
            "G_audit_risk": r.get("auditRisk"),
            "G_overall_risk": r.get("overallRisk"),
            "G_earnings_stability": (1.0 - _cv(r.get("net_income_series")))
            if _cv(r.get("net_income_series")) is not None
            and not (isinstance(_cv(r.get("net_income_series")), float) and np.isnan(_cv(r.get("net_income_series"))))
            else np.nan,
            "G_debt_discipline": (-_slope(da_series)) if not np.isnan(_slope(da_series)) else np.nan,
            # --- Financial Health (F) --- going-concern / survival risk.
            # Distinct from ESG: a bankrupt company sustains nothing. Each KPI
            # covers one pillar of corporate survival, computed from real
            # multi-year statements (latest year). Higher = healthier unless noted.
            # Liquidity: can it pay short-term obligations?
            "F_current_ratio": _safe_div(ca, cl) if (ca is not None and cl is not None) else np.nan,
            # Solvency / leverage: lower debt burden = more resilient.
            "F_debt_to_assets": _safe_div(debt, assets) if (debt is not None and assets) else np.nan,
            # Coverage: can operating earnings service interest? Higher = safer.
            # Null for banks (interest is their business, reported net).
            "F_interest_coverage": _safe_div(ebit, interest_exp) if interest_exp else np.nan,
            # Cumulative profitability + age: retained earnings / assets. The
            # classic resilience signal (Altman Z component): a firm with deep
            # accumulated earnings survives shocks; negative = prior losses.
            "F_retn_earnings_to_assets": _safe_div(re, assets) if (re is not None and assets) else np.nan,
            # Profitability engine: net income / assets (ROA). The core driver of
            # going concern; persistently negative ROA = distress risk.
            "F_return_on_assets": _safe_div(ni_abs, assets) if (ni_abs is not None and assets) else np.nan,
            # --- context (not scored) ---
            "marketCap": r.get("marketCap"),
            "totalRevenue": rev,
            "fullTimeEmployees": emp,
            "beta": beta,
            "fcf_margin": _safe_div(fcf, rev),
            "cash_buffer": _safe_div(cash, debt),
            "fcf_trend_cagr": _cagr([v for v in (r.get("fcf_series") or []) if v]),
            "returnOnEquity": r.get("returnOnEquity"),
        })
    return pd.DataFrame(rows)
