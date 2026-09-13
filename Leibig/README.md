# ETHack: ESG + Financial Health Scoring for S&P 500 Companies

A data-driven framework that gathers original ESG and financial-health features for
a focused universe of ~50 S&P 500 companies, then scores them with **Liebig's Law of
the Minimum** — a rigorous alternative to weighted-average ESG scores.

## Quick start

bash
pip install -r requirements.txt
python src/run_pipeline.py        # uses cached data; add --force to refetch
streamlit run app.py              # launch the interactive dashboard


This produces two deliverables:
- `output/sp500_esg_features.csv` — the dataset (50 companies × 32 columns)
- `output/sp500_liebig_scores.csv` — the ranked Liebig scores

And an interactive dashboard (`app.py`) to explore the results.

## The scoring: Liebig's Law of the Minimum

Mainstream ESG uses a weighted average, which lets a strong dimension *mask a fatal
weakness* (a green company about to go bankrupt still scores well). We apply
**Liebig's Law of the Minimum** — an ecological principle: *a system is constrained
by its scarcest resource, not its average*. A company is only as sustainable as its
weakest pillar:


liebig_score = min( E_score, S_score, G_score, F_score )


Applied at two levels: each pillar score is the mean of its normalised KPIs
(0–100), then the weakest pillar binds the composite — with **no arbitrary
weights**. The output reports the **binding constraint** (`binding_dimension`,
`binding_kpi`), so the ranking is also a diagnosis of *why* a company scores where
it does.

See **`docs/methodology.md`** for the full rationale, the origin of Liebig's Law,
and how to read a result.

## The features (grouped by E / S / G / F)

See **`docs/features.md`** for the full definition, formula, and justification of
every feature. Summary:

| Dimension | Features | Count |
|-----------|----------|-------|
| **Environmental (E)** | Carbon intensity, Est. emissions, Decarb investment adequacy, Emissions-to-assets, Transition readiness | 5 |
| **Social (S)** | Worker share, Shareholder return, Tax contribution, Reinvestment ratio | 4 |
| **Governance (G)** | ISS board/compensation/shareholder-rights/audit/overall risk, Earnings stability, Debt discipline | 7 |
| **Financial Health (F)** | Current ratio, Debt-to-assets, Interest coverage, Retained-earnings-to-assets, Return on assets | 5 |

All E features are **carbon-coupled**: either emissions-based or normalised by the
firm's emissions burden, so a structurally dirty sector cannot escape a low
Environmental score by spending heavily.

Plus context columns (`Symbol`, `Sector`, `Industry`, `marketCap`, `totalRevenue`,
`fullTimeEmployees`, `beta`, FCF/resilience fields).

## Data sources (free, reproducible)

| Source | Provides |
|--------|----------|
| **yfinance** `info` | Ratios, employees, **ISS governance risk scores** |
| **yfinance** statements (4–5 yrs) | Revenue, EBIT, R&D, CapEx, D&A, interest, buybacks, dividends, FCF, debt, assets, retained earnings |
| **S&P Global / Trucost** (2019–20 Scope 1) | Sector carbon intensity (tCO₂e/US$M revenue) — the cited authoritative source |

All cached per-symbol in `data/deep/` (gitignored — regenerable).

## Files


src/
  run_pipeline.py       # gather data -> build features -> score (Liebig) -> CSVs
  collect_deep.py       # deep multi-year statement collector (yfinance)
  features.py           # ESG + financial-health feature computation (E_/S_/G_/F_)
  scoring_liebig.py     # Liebig's Law of the Minimum scoring
  emission_intensity.py # sector carbon-intensity reference (S&P Global/Trucost)
  universe.py           # ~50-company universe across all 11 GICS sectors
app.py                  # Streamlit interactive dashboard
docs/
  features.md           # feature definitions & justifications grouped by E/S/G/F
  methodology.md        # Liebig scoring methodology & rationale
output/
  sp500_esg_features.csv  # the dataset
  sp500_liebig_scores.csv # the ranked scores
requirements.txt


## Scalability

The framework scales to any N — change the universe in `src/universe.py` (or pass
any list of tickers) and re-run. We focused on ~50 to enable the 4–5 year trend
features (stability, slope) that require multi-year statement history.
