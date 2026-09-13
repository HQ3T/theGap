"""Liebig sustainability scoring — the Law of the Minimum.

Novel paradigm. Standard ESG aggregates dimensions with a weighted average, which
lets one strong dimension *mask a fatal weakness* in another — a deeply green firm
about to go bankrupt still scores well. Liebig's Law of the Minimum (an ecological
principle: a system's growth is constrained by its *scarcest* resource, not its
average) inverts this: a company is only as sustainable as its weakest pillar.

    composite_score = min( E_score, S_score, G_score, F_score )

Two-level design:
  1. WITHIN each dimension, the pillar score = MEAN of its normalised KPIs.
     Each KPI is on a 0-100 scale (percentile rank across the universe, inverted
     for lower-is-better, so higher always = more sustainable). The mean means a
     pillar reflects the company's *overall* standing on that dimension —
     different raw profiles produce different pillar scores (unlike a pure min,
     which collapses many companies onto the same binding KPI value).
  2. ACROSS dimensions, the composite = MIN of the four pillar scores.
     The weakest dimension binds the overall score (the Law of the Minimum).

The output reports the binding dimension and the weakest KPI within it, so the
ranking is also a diagnosis of *why* a company scores where it does.

Normalisation: percentile rank, mapped to a true 0-100 scale (worst non-null
company = 0, best = 100). Percentile rank is monotonic (preserves ordering),
distribution-free, and outlier-robust. Every KPI in the dataset is continuous
and company-specific, so no ordinal mapping or exclusion is needed.

Missing KPIs are excluded from a dimension's mean; a dimension with zero usable
KPIs is NaN and the composite is NaN (firm not scored). In our universe all 51
firms score on all four pillars.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Direction: True = higher is better (normalise as-is); False = lower is better
# (invert before normalising). Every KPI's direction is justified by its definition.
DIRECTION = {
    # Environmental (all carbon-coupled: every metric is either emissions-based
    # or normalised by the firm's emissions burden, so dirty industrials can't
    # score well by spending heavily in a dirty business)
    "E_carbon_intensity":             False,  # lower tCO2e per US$M revenue = cleaner
    "E_est_emissions_tco2e":          False,  # lower total emissions = cleaner
    "E_decarb_investment_adequacy":   True,   # more USD invested per tonne CO2e = more decarbonisation capacity
    "E_emissions_to_assets":         False,  # lower emissions per US$M assets = cleaner asset base
    "E_transition_readiness":        True,   # more FCF per tonne CO2e = more financial capacity to transition
    # Social
    "S_worker_share":           True,   # more value to labour = better
    "S_shareholder_return":     True,   # more returned to shareholders = better
    "S_tax_contribution":       True,  # more tax paid = more public value
    "S_reinvestment_ratio":     True,   # more reinvestment = better
    # Governance (ISS risk scores: 1-10, higher = RISKIER -> lower is better)
    "G_board_risk":             False,
    "G_compensation_risk":      False,
    "G_shareholder_rights_risk": False,
    "G_audit_risk":             False,
    "G_overall_risk":           False,
    "G_earnings_stability":     True,   # higher stability = better
    "G_debt_discipline":        True,   # deleveraging (positive) = better
    # Financial Health
    "F_current_ratio":          True,   # higher liquidity = better
    "F_debt_to_assets":         False,  # lower leverage = better
    "F_interest_coverage":      True,   # higher coverage = better
    "F_retn_earnings_to_assets": True,  # more cumulative earnings = better
    "F_return_on_assets":       True,   # higher profitability = better
}

# All features in DIRECTION participate in scoring (no exclusions).
EXCLUDE_FROM_SCORING = set()

DIMS = {
    "E": [c for c in DIRECTION if c.startswith("E_") and c not in EXCLUDE_FROM_SCORING],
    "S": [c for c in DIRECTION if c.startswith("S_") and c not in EXCLUDE_FROM_SCORING],
    "G": [c for c in DIRECTION if c.startswith("G_") and c not in EXCLUDE_FROM_SCORING],
    "F": [c for c in DIRECTION if c.startswith("F_") and c not in EXCLUDE_FROM_SCORING],
}

DIM_NAMES = {"E": "Environmental", "S": "Social", "G": "Governance", "F": "Financial Health"}


def _normalise_kpi(series: pd.Series, higher_is_better: bool,
                   ordinal: bool = False) -> pd.Series:
    """Normalise a KPI to a 0-100 scale, higher = better. NaNs preserved.

    ordinal=True: linear map of discrete 0-3 to 0-100 (respects discrete meaning).
    Otherwise: percentile rank across non-null values, mapped to a true 0-100
    scale (worst non-null = 0, best = 100). lower-is-better is inverted first.
    Ties share the average rank (method='average').
    """
    s = pd.to_numeric(series, errors="coerce")
    if ordinal:
        return (s / 3.0 * 100.0).clip(0, 100)
    if s.notna().sum() < 2:
        return pd.Series(np.nan, index=s.index)
    asc = higher_is_better
    ranks = s.rank(method="average", ascending=asc, pct=True, na_option="keep")
    # Map rank (1/n .. 1.0) to a true 0-100 scale: (rank - min_rank)/(1 - min_rank)*100
    n = int(s.notna().sum())
    min_rank = 1.0 / n
    if (1.0 - min_rank) == 0:
        return pd.Series(np.where(s.notna(), 50.0, np.nan), index=s.index)
    pct = (ranks - min_rank) / (1.0 - min_rank) * 100.0
    return pct.clip(0, 100)


def score(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Liebig's Law of the Minimum. Returns a score DataFrame.

    Pillar scores (E/S/G/F) = mean of their 0-100-scaled KPIs.
    liebig_score = min of the four pillar scores (Law of the Minimum).
    binding_dimension = weakest pillar; binding_kpi = weakest KPI within it.
    """
    out = pd.DataFrame()
    out["Symbol"] = df["Symbol"]
    out["Sector"] = df["Sector"]

    norm_cols = {}
    for kpi, higher in DIRECTION.items():
        if kpi not in df.columns or kpi in EXCLUDE_FROM_SCORING:
            continue
        norm_cols[f"n_{kpi}"] = _normalise_kpi(df[kpi], higher_is_better=higher)

    # dimension pillar score = MEAN of its normalised KPIs (0-100 each)
    dim_scores = {}
    binding_kpi_in_dim = {}
    for dim, kpis in DIMS.items():
        present = [f"n_{k}" for k in kpis if f"n_{k}" in norm_cols]
        if not present:
            dim_scores[dim] = pd.Series(np.nan, index=df.index)
            binding_kpi_in_dim[dim] = pd.Series(np.nan, index=df.index)
            continue
        block = pd.concat([norm_cols[k] for k in present], axis=1)
        dim_scores[dim] = block.mean(axis=1)
        # weakest KPI within the dimension (for diagnosis)
        binding_kpi_in_dim[dim] = block.idxmin(axis=1)

    for dim in DIMS:
        out[f"{dim}_score"] = dim_scores[dim]

    # composite: Liebig across dimensions = MIN of pillar scores
    dim_block = pd.concat([dim_scores[d] for d in DIMS], axis=1)
    dim_block.columns = list(DIMS.keys())
    out["liebig_score"] = dim_block.min(axis=1)

    # Alternative 1: equal-weighted sum (mean of pillar scores, 0-100)
    out["equal_weight_score"] = dim_block.mean(axis=1)

    # Alternative 2: geometric mean of pillar scores (0-100). Rewards balance;
    # a single low pillar drags the score down more than the arithmetic mean.
    out["geo_mean_score"] = np.exp(np.log(dim_block).mean(axis=1))

    # binding dimension = weakest pillar
    out["binding_dimension"] = dim_block.idxmin(axis=1).map(DIM_NAMES)

    # binding KPI = the weakest KPI within the weakest dimension
    def _binding_kpi(row):
        comp = row["liebig_score"]
        if pd.isna(comp):
            return np.nan
        bd = None
        for d in DIMS:
            if pd.isna(row[f"{d}_score"]):
                continue
            if row[f"{d}_score"] == comp:
                bd = d
                break
        if bd is None:
            return np.nan
        return binding_kpi_in_dim[bd][row.name]

    out["binding_kpi"] = out.apply(_binding_kpi, axis=1)

    return out


if __name__ == "__main__":
    from pathlib import Path
    feat = pd.read_csv(Path(__file__).resolve().parent.parent / "output" / "sp500_esg_features.csv")
    res = score(feat)
    print(res[["Symbol", "Sector", "E_score", "S_score", "G_score", "F_score",
               "liebig_score", "equal_weight_score", "geo_mean_score",
               "binding_dimension", "binding_kpi"]]
          .sort_values("liebig_score", ascending=False).head(15).to_string(index=False))
