# Scoring Methodology — Liebig's Law of the Minimum

> Implementation: `src/scoring_liebig.py` · Output: `output/sp500_liebig_scores.csv`

## The problem with weighted-average ESG

Every mainstream ESG framework (MSCI, Sustainalytics, Refinitiv, Bloomberg) reduces a
company to a **weighted average** of dimension scores. This has one structural flaw
that matters for sustainability: **it lets a strong dimension mask a fatal weakness.**
A deeply green company about to go bankrupt still scores well, because a high
Environmental score offsets a catastrophic Financial-Health score in the average.

This is the opposite of how natural systems behave.

## Liebig's Law of the Minimum

In 19th-century agricultural science, Justus von Liebig observed that **a plant's
growth is constrained not by the total resources available, but by its scarcest
one** — the nutrient in shortest supply. Add more of every other nutrient and
nothing changes; the plant is still limited by the bottleneck. This became
*Liebig's Law of the Minimum*, a foundational principle of ecology.

We apply it to corporate sustainability: **a company is only as sustainable as its
weakest pillar.** No averaging, no offsetting, no weights.

```
composite_score = min( E_score, S_score, G_score, F_score )
```

This is applied at **two levels**:

### Level 1 — within each dimension (pillar score = mean of 0-100 KPIs)
Each pillar score is the **mean** of its normalised KPIs, each on a 0-100 scale
(percentile rank across the universe, inverted for lower-is-better, so higher
always = more sustainable):
```
E_score = mean( n_E_carbon_intensity, n_E_est_emissions_tco2e, n_E_decarb_investment_adequacy, n_E_emissions_to_assets, n_E_transition_readiness )
```
The mean means a pillar reflects a company's *overall* standing on that
dimension, so different raw profiles produce different pillar scores.

### Level 2 — across dimensions (the weakest pillar binds)
The composite is the **minimum** of the four pillar scores:
```
liebig_score = min( E_score, S_score, G_score, F_score )
```
The weakest dimension binds the overall score. A firm cannot trade strong
governance for weak financial health.

## Why this is the right model for sustainability

1. **It enforces the core thesis.** "Sustainable but bankrupt next year" is
   impossible under Liebig: if `F_score` collapses, the composite collapses, no
   matter how clean the emissions. A weighted average lets that firm score well;
   Liebig does not.

2. **It is ecological, not financial.** Sustainability is a *system* property, and
   systems are constrained by their bottlenecks. Treating a company like a
   balanced ecosystem — where every pillar must hold — is more faithful to what
   sustainability actually means than treating it like a diversified portfolio.

3. **No arbitrary weights.** Weighted-average ESG is endlessly criticised for its
   opaque, uncontestable weights (why 30/30/30/10 and not 25/35/30/10?). Liebig
   needs none. The method is the weight: the weakest link always sets the score.

4. **It is diagnostic.** Because the score *is* the minimum, we always know the
   **binding constraint** — which dimension (and which KPI within it) is the
   bottleneck. The output reports `binding_dimension` and `binding_kpi`, so a
   ranking is also a diagnosis: *why* a company scores where it does, not just
   *that* it does. No weighted average can do this.

## What each output column means

| Column | Meaning |
|--------|---------|
| `rank` | 1 = strongest under Liebig (highest composite) |
| `E_score`, `S_score`, `G_score`, `F_score` | Pillar scores 0–100, each the mean of its normalised KPIs (each KPI 0–100) |
| `liebig_score` | Composite 0–100 = min of the four pillar scores (the Law of the Minimum) |
| `binding_dimension` | The weakest pillar — the bottleneck that sets the composite |
| `binding_kpi` | The weakest KPI within the binding dimension — the precise bottleneck |

Higher is always better on the 0–100 scale: "lower-is-better" raw features
(emissions, debt, governance risk) are inverted before normalisation.

## Normalisation: percentile rank

Each KPI is placed on a common 0–100 scale via **percentile rank** across the
50-company universe (lower-is-better KPIs inverted first).

Why percentile rank, not min-max or z-score:
- **Monotonic** — it preserves each company's ordering on a KPI, so Liebig's
  "weakest link" still means the actually-weakest link (rigorous).
- **Distribution-free** — makes no linearity or normality assumption, so it works
  for skewed financial ratios (e.g. `F_interest_coverage` ranges 2–547) without
  distortion.
- **Outlier-robust** — no clipping needed; one extreme firm cannot compress
  everyone else onto a narrow band.
- **Comparable** — unlike min-max (which floors the worst company to exactly 0),
  percentile rank gives every firm a meaningful position. This matters under
  Liebig: min-max would make min-of-mins degenerate (a mass of ties at 0);
  percentile rank keeps scores distinguishable while keeping the weakest link
  binding.

## Missing values

Missing KPIs are excluded from a dimension's mean; they do not penalise a
company. A dimension with zero usable KPIs is NaN, and a firm with any NaN pillar
is not scored (NaN composite). In our 50-company universe every firm has enough
KPIs to score on all four pillars, so all 50 receive a Liebig score.

## How to read a result

A company with `liebig_score = 25` and `binding_dimension = Governance` is saying:
*"Across all four pillars this firm is at roughly the 25th percentile — and the
thing holding it back is governance, specifically `binding_kpi`. Improve that one
KPI and the composite rises; improving anything else, alone, does nothing."*

That last property — that only the binding constraint matters for the score — is
the whole point of Liebig, and the reason it is a more honest model of
sustainability than any weighted average.
