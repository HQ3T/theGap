# ESG + Financial Health Features — Definitions & Justifications (grouped by E / S / G / F)

> ETHack: Original, computed ESG and financial-health features for a focused
> ~50-company S&P 500 universe. This document defines every feature in the dataset
> and justifies why each is a relevant sustainability signal. The dataset itself is
> `output/sp500_esg_features.csv`.

## How to read the dataset

Each row is one company. Columns are prefixed so the dimension is self-documenting:
- `E_*` — Environmental
- `S_*` — Social
- `G_*` — Governance
- `F_*` — Financial Health (going-concern / survival risk)

The remaining columns (`Symbol`, `Sector`, `Industry`, `marketCap`, `totalRevenue`,
`fullTimeEmployees`, `beta`, `fcf_margin`, `cash_buffer`, `fcf_trend_cagr`,
`returnOnEquity`) are **context** — descriptive fields kept for transparency, not
scored dimensions.

All features are computed from **free 4–5 year financial statements** (yfinance:
income statement, balance sheet, cash flow) plus the info snapshot, which carries
**ISS-derived governance risk scores**. The multi-year history enables the
stability and trend features (earnings stability, debt-discipline slope) that
require multi-year statement data.

---

## Environmental (E)

The environmental dimension is deliberately **punitive toward structurally dirty
sectors**. Every feature is **carbon-coupled**: either emissions-based, or
normalised by the firm's emissions burden. A firm earns environmental credit only
for spending adequate to its *emissions burden*, not for spending in absolute
terms. This prevents a capital-intensive industrial from scoring well simply by
spending heavily in a dirty business.

Five carbon-coupled features:

| Feature | Formula | What it captures | Why it's relevant |
|--------|---------|------------------|-------------------|
| `E_carbon_intensity` | sector Scope-1 intensity [tCO₂e/US$M] | **Structural carbon-to-revenue intensity** | The Trucost / S&P Global standard carbon metric. Penalises sectors whose business model is intrinsically carbon-heavy (Utilities, Materials, Energy). Lower = cleaner |
| `E_est_emissions_tco2e` | sector intensity × revenue / 1e6 | Estimated Scope-1 emissions (tCO₂e) | The absolute emissions total. A size-based carbon penalty so a large dirty firm cannot hide behind a good intensity ratio. Lower = cleaner |
| `E_decarb_investment_adequacy` | (\|CapEx\| + \|R&D\|) / estimated emissions [tCO₂e] | **Transition investment per tonne of pollution** | **Original carbon-coupled signal, not in standard ESG.** Investment only counts relative to the firm's emissions burden. A capital-intensive industrial with huge absolute CapEx but huge emissions scores low (spending spread thin across a dirty asset base); a clean-sector firm with modest spend but tiny emissions scores high. Higher = more decarbonisation capacity per unit of pollution |
| `E_emissions_to_assets` | estimated emissions [tCO₂e] / total assets [US$M] | **Carbon efficiency of the physical asset base** | **Original signal.** A different lens from revenue intensity: measures emissions per dollar of physical assets. A capital-intensive firm with a huge dirty asset base scores worse than one with a lean, clean base. Dirty sectors rank high (Utilities 458, Materials 516, Energy 377 tCO₂e/US$M assets), clean sectors low (Health Care 4, IT 17). Lower = cleaner |
| `E_transition_readiness` | free cash flow [US$] / estimated emissions [tCO₂e] | **Financial firepower to fund the transition** | **Original signal.** A firm can only decarbonise if it has the cash to do so. This measures free cash flow per tonne of CO₂e — the financial capacity to invest in transition per unit of pollution. Clean sectors with strong cash flow top (Health Care 20,493, Communication Services 18,759 USD/tCO₂e); dirty sectors with weak or negative cash flow bottom (Utilities −10, Financials −16,462). Higher = better |

**Carbon intensity source & unit.** The sector intensities are the **Trucost /
S&P Global standard metric**: tonnes of CO₂e per US$1 million of revenue
(tCO₂e/US$mn), specifically the **2019–2020 average Scope 1 (direct) emissions
intensity by GICS sector** published by S&P Global. This is the exact unit confirmed
in the S&P Global Sustainable1 *Trucost Environmental Data Methodology* and the
*Trucost FAQ* ("carbon intensity ... in the units: tCO₂e/US$ mn Revenues").
Per-sector values for all 11 GICS sectors: Utilities 2,634; Materials 918; Energy
571; Industrials 194; Consumer Staples 90; Consumer Discretionary 33; Real Estate
31; Information Technology 24; Financials 19; Communication Services 9; Health
Care 7 (tCO₂e/US$M). Each company is assigned the intensity of its GICS sector
(from `src/universe.py`'s `SECTOR_OF` mapping, which uses standard GICS names, not
the non-standard names yfinance reports) and multiplied by its own real revenue
(yfinance) to produce `E_est_emissions_tco2e`.

**Limitation (transparency).** Because the carbon metric rests on sector-level
Scope-1 intensity (the most defensible free, citeable source), all companies
within a sector share the same `E_carbon_intensity`. No reliable free source
covers all 50 companies with audited per-company emissions: yfinance's
sustainability endpoint is dead; Climate TRACE exposes asset-level data requiring
complex owner-to-company aggregation; HuggingFace GHG datasets cover fewer than
20 of the 50 companies and are LLM-derived; EPA GHGRP is US-only. The sector-level
metric is the honest, reproducible choice, and `E_decarb_investment_adequacy`,
`E_emissions_to_assets`, and `E_transition_readiness` provide company-specific
environmental differentiation within a sector (because each firm's CapEx + R&D,
assets, cash flow, and revenue are real and unique).

**Design note:** The E dimension has five features, all carbon-coupled: three
penalise emissions (revenue intensity, absolute total, asset-base intensity),
two credit capacity relative to emissions (investment adequacy, transition
readiness). No feature rewards spending or financial strength in absolute terms.
A structurally dirty sector cannot escape a low Environmental score by spending
heavily.

---

## Social (S)

The social dimension measures **who captures the value the company creates** — not how
much value it creates. A company that extracts all value as buybacks is less socially
sustainable than one that pays wages, taxes, and reinvests.

| Feature | Formula | What it captures | Why it's relevant |
|--------|---------|------------------|-------------------|
| `S_worker_share` | (median compensation × headcount) / revenue | Share of revenue flowing to labour | A company that captures almost all revenue as profit, with little going to its workforce, is socially extractive. Uses real per-company median employee compensation × headcount (externally sourced); for 3 companies where median compensation was unavailable, a $80k base salary fallback was used. Higher = more value reaches workers |
| `S_shareholder_return` | min((\|buybacks\| + \|dividends\|) / net income, 1) | Capital returned to shareholders (capped at 100%) | Measures how much profit is distributed to shareholders. Capped at 1: returning more than 100% of net income is extraction (draining the company), not sustainability, so it is not rewarded beyond the cap. Read alongside `S_reinvestment_ratio` |
| `S_tax_contribution` | mean over 4–5 yrs of (EBIT − net income) / EBIT, clipped to [0,1] | Share of operating profit paid in tax + interest | **Novel signal**: companies that pay their taxes fund public goods (infrastructure, education, health). Conventional ESG ignores tax contribution entirely. Uses a multi-year average so a single loss year cannot inflate the ratio; clipped to [0,1] so a distressed firm is not rewarded. Higher = more value reaches the public |
| `S_reinvestment_ratio` | (\|CapEx + R&D\|) / revenue | Value ploughed back into the business | Balances the shareholder-return feature: a sustainable company reinvests in its future rather than extracting all value now |

**Design note:** `S_shareholder_return` and `S_reinvestment_ratio` are deliberately
paired — they only make sense together. A company returning 100% of profit via
buybacks with zero reinvestment is extracting; one returning some while reinvesting
heavily is balancing present and future stakeholders.

---

## Governance (G)

The governance dimension combines **independent third-party risk scores** (ISS) with
**track-record signals** computed over 4–5 years. Standard governance ESG is a static
board snapshot; this dimension asks whether governance has produced *resilient
outcomes over time*.

| Feature | Source | What it captures | Why it's relevant |
|--------|--------|------------------|-------------------|
| `G_board_risk` | ISS (1–10, higher = riskier) | Board independence, composition, oversight quality | Independent third-party assessment of board quality — not self-reported |
| `G_compensation_risk` | ISS (1–10) | Pay-for-performance alignment, excess compensation | Captures whether executive pay is aligned with performance |
| `G_shareholder_rights_risk` | ISS (1–10) | Voting rights, anti-takeover devices | Measures protection of shareholder rights vs. entrenchment |
| `G_audit_risk` | ISS (1–10) | Accounting quality, restatement risk | Financial-reporting integrity |
| `G_overall_risk` | ISS (1–10) | Composite ISS governance view | A single blended governance-risk read |
| `G_earnings_stability` | 1 − CV(net income, 4–5 yrs) | Consistency of earnings through cycles | **Novel**: consistent earnings over 4–5 years signal robust *operational* governance — the board's stewardship actually produces stable results, not just good optics. Higher = more stable |
| `G_debt_discipline` | −slope(debt/assets over 4–5 yrs) | Deleveraging vs. releveraging trend | **Novel**: a company steadily reducing debt/assets is demonstrating prudent stewardship; rising leverage signals fragility. Positive value = deleveraging (good) |

**Design note:** The five ISS risk features are static snapshots from an independent
provider. The two computed features (`G_earnings_stability`, `G_debt_discipline`)
add the *time dimension* — they ask whether governance has *worked* over a cycle, not
just whether the boardroom looks good today.

---

## Financial Health (F)

A dimension distinct from ESG on purpose: **a bankrupt company sustains nothing.**
No matter how clean its emissions, a firm that cannot service its obligations next
year delivers zero sustainability. The F dimension therefore measures
**going-concern / survival risk** — the precondition for any sustainability claim to
be meaningful. Every KPI covers one pillar of corporate survival (liquidity,
solvency, coverage, cumulative profitability, operating profitability), all
computed from the same real 4–5 year statements.

Higher = healthier for every F feature **except** `F_debt_to_assets`, where lower
= healthier (less leverage).

| Feature | Formula | Pillar | What it captures |
|--------|---------|--------|------------------|
| `F_current_ratio` | current assets / current liabilities | Liquidity | Can the firm pay its short-term obligations? <1 signals potential short-term cash strain |
| `F_debt_to_assets` | total debt / total assets | Solvency / leverage | How leveraged is the balance sheet? Lower = more resilient to shocks (lower = healthier) |
| `F_interest_coverage` | EBIT / \|interest expense\| | Coverage | Can operating earnings service debt interest? Higher = safer; persistently <1.5 is a distress signal. Null for banks, where interest is the core business reported net |
| `F_retn_earnings_to_assets` | retained earnings / total assets | Cumulative profitability + age | The classic resilience signal (an Altman Z component): a firm with deep accumulated earnings absorbs shocks; negative = prior losses eroded the cushion |
| `F_return_on_assets` | net income / total assets | Operating profitability | The core engine of going concern; persistently negative ROA is a primary distress indicator |

**Design note.** This is intentionally a **separate dimension**, not folded into E/S/G,
because financial health is a *precondition* rather than a sustainability attribute:
it gates whether a company will exist to deliver on any ESG commitment. The five
KPIs mirror the pillars used in classic distress-prediction models (liquidity,
solvency, coverage, cumulative profitability, asset productivity), but are kept as
individual transparent ratios rather than collapsed into a single opaque score.
Note `F_interest_coverage` is null for banks (JPM, BAC, GS) and any firm reporting
no standalone interest expense — this is structural, not missing data.

---

## Context fields (descriptive, not a scored dimension)

These columns are kept in the dataset for transparency and downstream use, but are
not part of the E/S/G feature grouping:

| Field | Source | Notes |
|-------|--------|-------|
| `Symbol`, `Sector`, `Industry` | Wikipedia / yfinance | Identifiers |
| `marketCap`, `totalRevenue`, `fullTimeEmployees` | yfinance info | Size context |
| `beta` | yfinance info | Systematic volatility |
| `fcf_margin`, `cash_buffer`, `fcf_trend_cagr`, `returnOnEquity` | yfinance statements | Financial-resilience context |

---

## Coverage

50 companies across all 11 GICS sectors. Per-feature coverage (non-null counts):

| Group | Feature | Non-null / 50 |
|-------|---------|:------------:|
| E | `E_carbon_intensity` | 50 |
| E | `E_est_emissions_tco2e` | 50 |
| E | `E_decarb_investment_adequacy` | 50 |
| E | `E_emissions_to_assets` | 50 |
| E | `E_transition_readiness` | 50 |
| S | `S_worker_share` | 50 |
| S | `S_reinvestment_ratio` | 50 |
| S | `S_shareholder_return` | 49 |
| S | `S_tax_contribution` | 47 |
| G | `G_board_risk` | 50 |
| G | `G_compensation_risk` | 50 |
| G | `G_shareholder_rights_risk` | 50 |
| G | `G_audit_risk` | 50 |
| G | `G_overall_risk` | 50 |
| G | `G_earnings_stability` | 50 |
| G | `G_debt_discipline` | 50 |
| F | `F_current_ratio` | 47 |
| F | `F_debt_to_assets` | 50 |
| F | `F_interest_coverage` | 45 |
| F | `F_retn_earnings_to_assets` | 50 |
| F | `F_return_on_assets` | 50 |

17 of the 21 E/S/G/F features are complete for all 50 companies. The gaps are
all explained by business-model differences (banks do not report a standalone
interest expense or a meaningful current-asset/liability split; the EBIT→net-
income tax bridge is not meaningful for financial firms) rather than missing
scrapes. **No values are imputed** — every cell is the raw computed figure, so a
null honestly means "this feature is not defined for this business model." All
five Environmental features are complete for every company.

### Companies with a gap (and why)

These nulls are all intentional — they arise where a feature is genuinely not
defined for a company's business model, not from missing scrapes:

| Company | Sector | Null feature(s) | Reason |
|---------|--------|------------------|--------|
| JPM (JPMorgan Chase) | Financials | `S_tax_contribution`, `F_current_ratio`, `F_interest_coverage` | The EBIT→net-income tax bridge and a standalone interest expense are not meaningful for financial firms (interest is their core business, reported net); current assets/liabilities are not the relevant liquidity frame for a bank |
| BAC (Bank of America) | Financials | `S_tax_contribution`, `F_current_ratio`, `F_interest_coverage` | Same as JPM |
| GS (Goldman Sachs) | Financials | `S_tax_contribution`, `F_current_ratio`, `F_interest_coverage` | Same as JPM/BAC |
| INTC (Intel) | Information Technology | `S_shareholder_return` | The buybacks+dividends to net-income ratio cannot be reliably derived from the reported income-statement lines |
| NKE (Nike) | Consumer Discretionary | `F_interest_coverage` | No standalone interest expense reported |
| CRM (Salesforce) | Information Technology | `F_interest_coverage` | No standalone interest expense reported |

These gaps reflect genuine structural limits of the underlying statements, not
missing scrapes. Reporting them transparently — rather than filling them with
imputed values — keeps the dataset auditable and defensible.
