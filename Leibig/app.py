"""ETHack Sustainability Dashboard — Liebig's Law of the Minimum.

Interactive Streamlit app to explore the ESG + Financial Health sustainability
scores for 50 S&P 500 companies.

Run:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent
FEATURES_PATH = ROOT / "output" / "sp500_esg_features.csv"
SCORES_PATH = ROOT / "output" / "sp500_liebig_scores.csv"

DIM_COLORS = {
    "Environmental": "#2ecc71",
    "Social": "#3498db",
    "Governance": "#f39c12",
    "Financial Health": "#e74c3c",
}
DIM_SHORT = {
    "Environmental": "E",
    "Social": "S",
    "Governance": "G",
    "Financial Health": "F",
}


@st.cache_data
def load_data() -> pd.DataFrame:
    features = pd.read_csv(FEATURES_PATH)
    scores = pd.read_csv(SCORES_PATH)
    df = scores.merge(features, on="Symbol", suffixes=("", "_feat"))
    if "Sector_feat" in df.columns:
        df.drop(columns=["Sector_feat"], inplace=True, errors="ignore")
    if "Industry_feat" in df.columns:
        df.drop(columns=["Industry_feat"], inplace=True, errors="ignore")
    return df


df = load_data()

E_FEATURES = [
    "E_carbon_intensity", "E_est_emissions_tco2e", "E_decarb_investment_adequacy",
    "E_emissions_to_assets", "E_transition_readiness",
]
S_FEATURES = ["S_worker_share", "S_shareholder_return", "S_tax_contribution", "S_reinvestment_ratio"]
G_FEATURES = [
    "G_board_risk", "G_compensation_risk", "G_shareholder_rights_risk",
    "G_audit_risk", "G_overall_risk", "G_earnings_stability", "G_debt_discipline",
]
F_FEATURES = [
    "F_current_ratio", "F_debt_to_assets", "F_interest_coverage",
    "F_retn_earnings_to_assets", "F_return_on_assets",
]

DIM_FEATURES = {
    "Environmental": E_FEATURES, "Social": S_FEATURES,
    "Governance": G_FEATURES, "Financial Health": F_FEATURES,
}
DIM_SCORES = {
    "Environmental": "E_score", "Social": "S_score",
    "Governance": "G_score", "Financial Health": "F_score",
}

LABELS = {
    "E_carbon_intensity": "Carbon intensity",
    "E_est_emissions_tco2e": "Est. emissions",
    "E_decarb_investment_adequacy": "Decarb investment adequacy",
    "E_emissions_to_assets": "Emissions-to-assets",
    "E_transition_readiness": "Transition readiness",
    "S_worker_share": "Worker share",
    "S_shareholder_return": "Shareholder return",
    "S_tax_contribution": "Tax contribution",
    "S_reinvestment_ratio": "Reinvestment ratio",
    "G_board_risk": "Board risk",
    "G_compensation_risk": "Compensation risk",
    "G_shareholder_rights_risk": "Shareholder rights risk",
    "G_audit_risk": "Audit risk",
    "G_overall_risk": "Overall governance risk",
    "G_earnings_stability": "Earnings stability",
    "G_debt_discipline": "Debt discipline",
    "F_current_ratio": "Current ratio",
    "F_debt_to_assets": "Debt-to-assets",
    "F_interest_coverage": "Interest coverage",
    "F_retn_earnings_to_assets": "Retained earnings/assets",
    "F_return_on_assets": "Return on assets",
}

UNITS = {
    "E_carbon_intensity": "tCO₂e/US$M",
    "E_est_emissions_tco2e": "tCO₂e",
    "E_decarb_investment_adequacy": "USD/tCO₂e",
    "E_emissions_to_assets": "tCO₂e/US$M",
    "E_transition_readiness": "USD/tCO₂e",
    "S_worker_share": "ratio",
    "S_shareholder_return": "ratio",
    "S_tax_contribution": "ratio",
    "S_reinvestment_ratio": "ratio",
    "G_board_risk": "1–10",
    "G_compensation_risk": "1–10",
    "G_shareholder_rights_risk": "1–10",
    "G_audit_risk": "1–10",
    "G_overall_risk": "1–10",
    "G_earnings_stability": "index",
    "G_debt_discipline": "slope",
    "F_current_ratio": "ratio",
    "F_debt_to_assets": "ratio",
    "F_interest_coverage": "x",
    "F_retn_earnings_to_assets": "ratio",
    "F_return_on_assets": "ratio",
}

# --------------------------------------------------------------------------- #
# Page config + custom CSS
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="ETHack Sustainability", page_icon="🌱", layout="wide")

st.markdown("""
<style>
    /* Main background and font */
    .stApp { background: #0e1117; }
    .stApp, .stApp p, .stApp span, .stApp li { color: #e0e0e0; }
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 600 !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] h2 { color: #58a6ff !important; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #1c2333;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px 18px;
    }
    div[data-testid="stMetric"] label { color: #8b949e !important; font-size: 0.78rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #ffffff !important; }

    /* Dataframe / tables */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    div[data-testid="stDataFrame"] table { background: #161b22 !important; }
    div[data-testid="stDataFrame"] th { background: #21262d !important; color: #c9d1d9 !important; }
    div[data-testid="stDataFrame"] td { color: #c9d1d9 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #161b22; border-radius: 8px 8px 0 0;
        border: 1px solid #30363d; padding: 10px 22px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1f6feb, #2ecc71) !important;
        color: #ffffff !important;
    }

    /* Selectbox / multiselect */
    div[data-baseweb="select"] > div { background: #161b22; border-color: #30363d; }

    /* Cards container */
    .pill {
        display: inline-block; padding: 3px 12px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600; margin: 2px;
    }
    .divider { border-top: 1px solid #30363d; margin: 1.5rem 0; }

    /* Code blocks (markdown ```) — dark, no white background */
    .stCodeBlock, .stCodeBlock pre,
    .stMarkdown pre, code, pre code {
        background: #161b22 !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    .stMarkdown code {
        background: #161b22 !important;
        color: #79c0ff !important;
        padding: 1px 6px !important;
        border-radius: 4px !important;
        border: 1px solid #30363d !important;
    }
    pre code { color: #c9d1d9 !important; border: none !important; padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Sidebar: Liebig explanation
# --------------------------------------------------------------------------- #
LIEBIG_TEXT = """
**The origin.** In 19th-century agricultural science, Justus von Liebig observed that a plant's
growth is constrained not by the total resources available, but by its **scarcest one** — the nutrient
in shortest supply. Add more of every other nutrient and nothing changes; the plant is still limited
by the bottleneck. This became *Liebig's Law of the Minimum*, a foundational principle of ecology.

**Applied to companies.** A company is only as sustainable as its weakest pillar. No averaging, no
offsetting, no weights:

```
liebig_score = min(E_score, S_score, G_score, F_score)
```

**Why not a weighted average?** Mainstream ESG frameworks (MSCI, Sustainalytics, Refinitiv) use
weighted averages, which let a strong dimension *mask a fatal weakness* — a green company about
to go bankrupt still scores well because a high Environmental score offsets a catastrophic
Financial Health score in the average. Liebig prevents this: if Financial Health collapses, the
composite collapses, no matter how clean the emissions.

**Two levels:**
1. **Within each dimension**: the pillar score is the **mean** of its normalised KPIs (each on a
   0-100 percentile-rank scale, inverted for lower-is-better KPIs). This reflects a company's overall
   standing on that dimension.
2. **Across dimensions**: the composite is the **minimum** of the four pillar scores. The weakest
   dimension binds the overall score — the Law of the Minimum.

**No arbitrary weights.** Weighted-average ESG is criticised for its opaque, uncontestable weights
(why 30/30/30/10 and not 25/35/30/10?). Liebig needs none. The method is the weight: the weakest link
always sets the score.

**Diagnostic.** Because the score *is* the minimum, we always know the **binding constraint** —
which dimension (and which KPI within it) is the bottleneck. The ranking is also a diagnosis: *why*
a company scores where it does, not just *that* it does. No weighted average can do this.
"""

with st.sidebar:
    st.header("Data & Sources")
    st.caption("50 S&P 500 companies · 4 dimensions · 21 KPIs")
    st.markdown(
"""
**Data sources (free, reproducible):**
- **yfinance** `info` — ratios, employees, ISS governance risk scores
- **yfinance** statements (4-5 yrs) — revenue, EBIT, R&D, CapEx, FCF, debt, assets
- **S&P Global / Trucost** (2019-20 Scope 1) — sector carbon intensity

All cached per-symbol in `data/deep/` (regenerable).
""")
    st.divider()
    st.markdown("**Four dimensions:**")
    for dim, color in DIM_COLORS.items():
        st.markdown(f"<span style='color:{color}'>●</span> **{dim}**", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Header + KPI summary cards
# --------------------------------------------------------------------------- #
st.markdown("# 🌱 S&P 500 Sustainability Dashboard")
st.markdown(
    f"<span style='color:#8b949e'>Liebig's Law of the Minimum · "
    f"{len(df)} companies · 4 dimensions · 21 KPIs</span>",
    unsafe_allow_html=True,
)

n_cols = 5
c1, c2, c3, c4, c5 = st.columns(n_cols)
top = df.sort_values("liebig_score", ascending=False).iloc[0]
worst = df.sort_values("liebig_score", ascending=False).iloc[-1]
c1.metric("Companies", str(len(df)))
c2.metric("Avg. score", f"{df['liebig_score'].mean():.1f}")
c3.metric("Top", f"{top['Symbol']}", f"{top['liebig_score']:.1f}")
c4.metric("Bottom", f"{worst['Symbol']}", f"{worst['liebig_score']:.1f}")
c5.metric("Binding: Environment", str((df['binding_dimension'] == 'Environmental').sum()))

st.markdown("")

# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #
tab_method, tab_rank, tab_company, tab_vs, tab_sector, tab_scatter = st.tabs([
    "📖 The Method", "🏆 Ranking", "🔎 Company Detail", "⚔️ Method Comparison",
    "📊 Sector Comparison", "🔬 Correlations",
])

# --------------------------------------------------------------------------- #
# Tab 0: The Method (Liebig explanation, central)
# --------------------------------------------------------------------------- #
with tab_method:
    st.subheader("The Method — Liebig's Law of the Minimum")
    st.markdown(LIEBIG_TEXT)

    st.markdown("")
    st.markdown("---")

    # Visual: the two levels side by side
    st.markdown("### How it works")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown(
            """
**Level 1 — Within each dimension**

Each pillar score is the **mean** of its normalised KPIs (each 0–100):
```
E_score = mean( n_E_carbon_intensity,
                n_E_est_emissions_tco2e,
                n_E_decarb_investment_adequacy,
                n_E_emissions_to_assets,
                n_E_transition_readiness )
```
The mean reflects a company's overall standing on that dimension.
"""
        )
    with col_l2:
        st.markdown(
            """
**Level 2 — Across dimensions**

The composite is the **minimum** of the four pillar scores:
```
liebig_score = min( E_score, S_score,
                   G_score, F_score )
```
The weakest dimension binds the overall score.
"""
        )

    st.markdown("")
    st.markdown("---")

    # The barrel analogy (classic Liebig visual)
    st.markdown("### The barrel analogy")
    st.markdown(
        """
Liebig's Law is often illustrated with a wooden barrel made of staves of different
lengths. The barrel can only hold water up to its **shortest stave** — no matter
how tall the others are. Each stave is a sustainability dimension:

- If **Environmental** is the shortest, the company is bound by its carbon footprint.
- If **Financial Health** is the shortest, the company is bound by going-concern risk.
- If **Governance** is the shortest, the company is bound by board/oversight quality.
- If **Social** is the shortest, the company is bound by value distribution.

Improving any *other* stave does not raise the water level. Only fixing the
**binding** (shortest) stave does. That is why the output reports `binding_dimension`
and `binding_kpi` — the precise bottleneck for each company.
"""
    )

    # Show the binding distribution as a visual
    st.markdown("")
    st.markdown("**In our 50-company universe, here is which dimension binds most companies:**")
    binding_counts = df["binding_dimension"].value_counts().reset_index()
    binding_counts.columns = ["Dimension", "Count"]
    fig_bind_method = px.bar(
        binding_counts, x="Dimension", y="Count", color="Dimension",
        color_discrete_map=DIM_COLORS, height=300,
    )
    fig_bind_method.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", showlegend=False,
        xaxis_title="", yaxis_title="Companies",
    )
    fig_bind_method.update_yaxes(gridcolor="#30363d")
    st.plotly_chart(fig_bind_method, use_container_width=True, key="chart_bind_method")

# --------------------------------------------------------------------------- #
# Tab 1: Ranking
# --------------------------------------------------------------------------- #
with tab_rank:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        sector_filter = st.multiselect(
            "Filter by sector", options=sorted(df["Sector"].unique()), default=[],
            key="rank_sector",
        )
    with col_b:
        top_n = st.slider("Show top N", 5, 50, 50, step=1, key="rank_topn")

    display = df.copy()
    if sector_filter:
        display = display[display["Sector"].isin(sector_filter)]
    display = display.sort_values("liebig_score", ascending=False).head(top_n)

    fig = px.bar(
        display, x="liebig_score", y="Symbol", color="binding_dimension",
        orientation="h", height=max(500, len(display) * 25),
        color_discrete_map=DIM_COLORS,
        labels={"liebig_score": "Liebig score (0–100)", "binding_dimension": "Binding"},
        title="<b>Composite sustainability score</b> — coloured by binding dimension",
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(
        yaxis_title="", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", title_font_color="#ffffff",
        legend=dict(bgcolor="#161b22", font_color="#c9d1d9"),
    )
    fig.update_xaxes(gridcolor="#30363d", zerolinecolor="#30363d")
    st.plotly_chart(fig, use_container_width=True, key="chart_ranking")

    st.markdown("**Ranked table**")
    show_cols = ["rank", "Symbol", "Sector", "E_score", "S_score",
                 "G_score", "F_score", "liebig_score", "binding_dimension", "binding_kpi"]
    styled = display[show_cols].style.format({
        "E_score": "{:.1f}", "S_score": "{:.1f}", "G_score": "{:.1f}",
        "F_score": "{:.1f}", "liebig_score": "{:.1f}",
    })
    st.dataframe(styled, use_container_width=True, hide_index=True, key="df_ranking")

    st.markdown("**Binding dimension distribution**")
    binding_counts = df["binding_dimension"].value_counts().reset_index()
    binding_counts.columns = ["Dimension", "Count"]
    fig_bind = px.bar(
        binding_counts, x="Dimension", y="Count", color="Dimension",
        color_discrete_map=DIM_COLORS, height=300,
    )
    fig_bind.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", showlegend=False,
        xaxis_title="", yaxis_title="Companies",
    )
    fig_bind.update_yaxes(gridcolor="#30363d")
    st.plotly_chart(fig_bind, use_container_width=True, key="chart_bind_rank")

# --------------------------------------------------------------------------- #
# Tab 2: Company detail
# --------------------------------------------------------------------------- #
with tab_company:
    st.subheader("Company Detail")

    sorted_syms = df.sort_values("liebig_score", ascending=False)
    company = st.selectbox(
        "Select a company", options=sorted_syms["Symbol"].tolist(),
        format_func=lambda s: (
            f"{s} — {df[df.Symbol == s].Sector.values[0]} "
            f"(score {df[df.Symbol == s].liebig_score.values[0]:.1f})"
        ),
    )

    if company:
        row = df[df.Symbol == company].iloc[0]
        bd = row["binding_dimension"]
        bd_color = DIM_COLORS.get(bd, "#888")

        # Company header
        st.markdown(
            f"### {company} <span style='color:#8b949e;font-size:0.85em'>"
            f"· {row['Sector']} · {row.get('Industry', '')}</span>",
            unsafe_allow_html=True,
        )

        # KPI cards
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Rank", f"#{int(row['rank'])}")
        m2.metric("Liebig score", f"{row['liebig_score']:.1f}")
        m3.metric("Binding dimension", bd)
        m4.metric("Binding KPI", row["binding_kpi"])
        m5.metric("Market Cap",
                  f"${row.get('marketCap', 0) / 1e9:.0f}B" if pd.notna(row.get("marketCap")) else "N/A")

        st.markdown("")

        # Radar + KPI detail
        col_radar, col_kpi = st.columns([2, 3])

        with col_radar:
            pillars = ["Environmental", "Social", "Governance", "Financial Health"]
            pillar_vals = [row["E_score"], row["S_score"], row["G_score"], row["F_score"]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=pillar_vals + [pillar_vals[0]], theta=pillars + [pillars[0]],
                fill="toself", fillcolor="rgba(46,204,113,0.15)",
                line=dict(color="#2ecc71", width=2.5), name=company,
            ))
            # Add the binding dimension as a highlighted point
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0, 100], tickcolor="#30363d", gridcolor="#30363d"),
                    angularaxis=dict(gridcolor="#30363d", tickcolor="#c9d1d9"),
                    bgcolor="#0e1117",
                ),
                height=380, showlegend=False,
                paper_bgcolor="#0e1117", font_color="#e0e0e0",
                title=dict(text="<b>Pillar scores</b>", font_color="#ffffff"),
            )
            st.plotly_chart(fig_radar, use_container_width=True, key="chart_radar")

        with col_kpi:
            for dim in pillars:
                score = row[DIM_SCORES[dim]]
                is_binding = dim == bd
                prefix = "🔴" if is_binding else "▪️"
                dim_color = DIM_COLORS[dim]
                binding_note = "  *(binding)*" if is_binding else ""
                st.markdown(
                    f"**{prefix} {dim}** "
                    f"<span style='color:{dim_color}'>— score: {score:.1f}</span>{binding_note}",
                    unsafe_allow_html=True,
                )
                # Clean structured table per dimension instead of broken inline text
                feats = DIM_FEATURES[dim]
                kpi_rows = []
                for f in feats:
                    val = row[f]
                    unit = UNITS.get(f, "")
                    if pd.notna(val):
                        if abs(val) >= 1e9:
                            val_str = f"{val / 1e9:.1f}B"
                        elif abs(val) >= 1e6:
                            val_str = f"{val / 1e6:.1f}M"
                        elif abs(val) >= 1000:
                            val_str = f"{val:,.1f}"
                        else:
                            val_str = f"{val:.3g}"
                        kpi_rows.append({"KPI": LABELS[f], "Value": val_str, "Unit": unit})
                    else:
                        kpi_rows.append({"KPI": LABELS[f], "Value": "N/A", "Unit": unit})
                st.dataframe(
                    pd.DataFrame(kpi_rows),
                    use_container_width=True, hide_index=True,
                    height=min(len(kpi_rows) * 35 + 40, 250),
                    key=f"df_kpi_{dim}",
                )
                st.markdown("")

# --------------------------------------------------------------------------- #
# Tab 3: Method Comparison (Liebig vs equal-weighted sum vs geometric mean)
# --------------------------------------------------------------------------- #
with tab_vs:
    st.subheader("⚔️ Liebig vs Equal-Weighted Sum vs Geometric Mean")
    st.markdown("""
Three aggregation philosophies, all built on the **same 0-100 normalised pillar scores**
(E, S, G, F). They differ only in how the four pillars are combined into one composite:

| Method | Formula | Philosophy |
|---|---|---|
| **Liebig (min)** | `min(E, S, G, F)` | A company is only as sustainable as its **weakest pillar**. No offsetting. |
| **Equal-weighted sum** | `mean(E, S, G, F)` | All pillars count equally. A strong pillar **masks** a weak one. |
| **Geometric mean** | `(E·S·G·F)^(1/4)` | Balance is rewarded; a single low pillar **drags down** the score more than the arithmetic mean. |

The core question: should a company with a catastrophic Financial Health score but pristine
emissions rank as sustainable? **Liebig says no** — the weakest link binds. The weighted sum
says yes — the average is still decent. The geometric mean is a compromise: it penalises
imbalance but still allows some offsetting.
""")

    st.markdown("---")

    # --- Rank movement table ---
    comp = df[["Symbol", "Sector", "E_score", "S_score", "G_score", "F_score",
              "liebig_score", "equal_weight_score", "geo_mean_score"]].copy()
    comp["rank_liebig"] = comp["liebig_score"].rank(ascending=False).astype(int)
    comp["rank_equal"] = comp["equal_weight_score"].rank(ascending=False).astype(int)
    comp["rank_geo"] = comp["geo_mean_score"].rank(ascending=False).astype(int)
    comp["Δ (equal − liebig)"] = comp["rank_liebig"] - comp["rank_equal"]
    comp["Δ (geo − liebig)"] = comp["rank_liebig"] - comp["rank_geo"]

    st.markdown("### Rank comparison")
    st.caption("Positive Δ = the company ranks **higher** (better) under that method than under Liebig. "
               "Negative Δ = Liebig ranks it higher than the alternative.")
    show_comp = comp.sort_values("rank_liebig")[[
        "Symbol", "Sector", "rank_liebig", "rank_equal", "rank_geo",
        "Δ (equal − liebig)", "Δ (geo − liebig)",
    ]].copy()
    show_comp.columns = ["Symbol", "Sector", "Liebig rank", "Equal-wt rank", "Geo-mean rank",
                        "Δ (equal − liebig)", "Δ (geo − liebig)"]
    st.dataframe(show_comp, use_container_width=True, hide_index=True, key="df_vs_ranks")

    st.markdown("---")

    # --- Scatter: Liebig vs each alternative ---
    st.markdown("### Score scatter — where the methods disagree")
    st.caption("Points above the diagonal rank higher under the alternative than under Liebig. "
               "Points far from the diagonal are where the choice of method matters most.")

    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        fig_vs1 = px.scatter(
            comp, x="liebig_score", y="equal_weight_score", text="Symbol",
            color="Sector", height=450,
            labels={"liebig_score": "Liebig score", "equal_weight_score": "Equal-weighted score"},
            title="Liebig vs Equal-weighted sum",
        )
        fig_vs1.update_traces(textposition="top center", textfont_size=8)
        fig_vs1.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                          line=dict(dash="dash", color="#8b949e", width=1))
        fig_vs1.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
            legend=dict(bgcolor="#161b22", font_color="#c9d1d9"), title_font_color="#ffffff",
        )
        fig_vs1.update_xaxes(range=[0, 100], gridcolor="#30363d")
        fig_vs1.update_yaxes(range=[0, 100], gridcolor="#30363d")
        st.plotly_chart(fig_vs1, use_container_width=True, key="chart_vs_equal")
    with col_sc2:
        fig_vs2 = px.scatter(
            comp, x="liebig_score", y="geo_mean_score", text="Symbol",
            color="Sector", height=450,
            labels={"liebig_score": "Liebig score", "geo_mean_score": "Geometric-mean score"},
            title="Liebig vs Geometric mean",
        )
        fig_vs2.update_traces(textposition="top center", textfont_size=8)
        fig_vs2.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                          line=dict(dash="dash", color="#8b949e", width=1))
        fig_vs2.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
            legend=dict(bgcolor="#161b22", font_color="#c9d1d9"), title_font_color="#ffffff",
        )
        fig_vs2.update_xaxes(range=[0, 100], gridcolor="#30363d")
        fig_vs2.update_yaxes(range=[0, 100], gridcolor="#30363d")
        st.plotly_chart(fig_vs2, use_container_width=True, key="chart_vs_geo")

    st.markdown("---")

    # --- Biggest disagreements ---
    st.markdown("### Biggest disagreements")
    st.caption("Companies where the ranking changes the most between Liebig and the alternatives. "
               "These are the firms whose sustainability story depends entirely on the aggregation method.")

    biggest = comp.copy()
    biggest["max_abs_Δ"] = biggest[["Δ (equal − liebig)", "Δ (geo − liebig)"]].abs().max(axis=1)
    biggest = biggest.sort_values("max_abs_Δ", ascending=False).head(15)
    show_big = biggest[["Symbol", "Sector", "rank_liebig", "rank_equal", "rank_geo",
                        "Δ (equal − liebig)", "Δ (geo − liebig)", "liebig_score",
                        "equal_weight_score", "geo_mean_score"]].copy()
    show_big.columns = ["Symbol", "Sector", "Liebig rank", "Equal-wt rank", "Geo-mean rank",
                        "Δ (equal − liebig)", "Δ (geo − liebig)", "Liebig", "Equal-wt", "Geo-mean"]
    st.dataframe(show_big, use_container_width=True, hide_index=True, key="df_vs_biggest")

    st.markdown("---")

    # --- Score distribution ---
    st.markdown("### Score distributions")
    st.caption("Liebig compresses the range downward — the minimum can only lower the score, never raise it. "
               "The equal-weighted sum sits highest; the geometric mean sits between the two.")
    dist = comp[["Symbol", "liebig_score", "equal_weight_score", "geo_mean_score"]].melt(
        id_vars="Symbol", var_name="Method", value_name="Score"
    )
    method_labels = {
        "liebig_score": "Liebig (min)", "equal_weight_score": "Equal-weighted sum",
        "geo_mean_score": "Geometric mean",
    }
    dist["Method"] = dist["Method"].map(method_labels)
    fig_dist = px.box(
        dist, x="Method", y="Score", color="Method", height=380,
        color_discrete_map={
            "Liebig (min)": "#2ecc71", "Equal-weighted sum": "#f39c12",
            "Geometric mean": "#3498db",
        },
    )
    fig_dist.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#e0e0e0",
        showlegend=False, yaxis_title="Score (0-100)", xaxis_title="",
    )
    fig_dist.update_yaxes(range=[0, 100], gridcolor="#30363d")
    st.plotly_chart(fig_dist, use_container_width=True, key="chart_vs_dist")

# --------------------------------------------------------------------------- #
# Tab 4: Sector comparison
# --------------------------------------------------------------------------- #
with tab_sector:
    st.subheader("Sector Comparison")

    sector_avg = df.groupby("Sector")[
        ["E_score", "S_score", "G_score", "F_score", "liebig_score"]
    ].mean().reset_index().sort_values("liebig_score", ascending=False)

    fig_sector = px.bar(
        sector_avg.melt(
            id_vars="Sector",
            value_vars=["E_score", "S_score", "G_score", "F_score"],
            var_name="Dimension", value_name="Score",
        ),
        x="Sector", y="Score", color="Dimension", barmode="group", height=450,
        color_discrete_map={
            "E_score": DIM_COLORS["Environmental"], "S_score": DIM_COLORS["Social"],
            "G_score": DIM_COLORS["Governance"], "F_score": DIM_COLORS["Financial Health"],
        },
        labels={"Score": "Score (0–100)", "Dimension": "Dimension"},
    )
    fig_sector.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", title_font_color="#ffffff",
        legend=dict(bgcolor="#161b22", font_color="#c9d1d9"),
        title="<b>Average scores by sector</b>",
    )
    fig_sector.update_yaxes(gridcolor="#30363d")
    st.plotly_chart(fig_sector, use_container_width=True, key="chart_sector_scores")

    st.dataframe(
        sector_avg.style.format({
            "E_score": "{:.1f}", "S_score": "{:.1f}", "G_score": "{:.1f}",
            "F_score": "{:.1f}", "liebig_score": "{:.1f}",
        }),
        use_container_width=True, hide_index=True, key="df_sector_avg",
    )

    st.markdown("---")
    st.markdown("**Carbon intensity by sector** (tCO₂e per US$M revenue, S&P Global/Trucost)")
    ci = df.groupby("Sector")["E_carbon_intensity"].first().sort_values(ascending=True)
    fig_ci = px.bar(
        ci.reset_index(), x="E_carbon_intensity", y="Sector", orientation="h",
        height=400, color="E_carbon_intensity", color_continuous_scale="Reds_r",
        labels={"E_carbon_intensity": "tCO₂e/US$M"},
    )
    fig_ci.update_yaxes(categoryorder="total ascending")
    fig_ci.update_layout(
        yaxis_title="", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", showlegend=False,
        title=dict(text="<b>Carbon intensity</b>", font_color="#ffffff"),
        coloraxis_colorbar=dict(title="tCO₂e/US$M"),
    )
    fig_ci.update_xaxes(gridcolor="#30363d")
    st.plotly_chart(fig_ci, use_container_width=True, key="chart_carbon_intensity")

# --------------------------------------------------------------------------- #
# Tab 4: Correlations
# --------------------------------------------------------------------------- #
with tab_scatter:
    st.subheader("Correlations Between Dimensions")

    score_cols = list(DIM_SCORES.values())
    col_x, col_y = st.columns(2)
    with col_x:
        x_axis = st.selectbox("X axis", score_cols, index=0, key="scatter_x")
    with col_y:
        y_axis = st.selectbox("Y axis", score_cols, index=3, key="scatter_y")

    fig_scatter = px.scatter(
        df, x=x_axis, y=y_axis, color="Sector", text="Symbol",
        hover_data=["liebig_score", "binding_dimension"], height=550,
        labels={x_axis: x_axis.replace("_score", " score"),
                y_axis: y_axis.replace("_score", " score")},
        title=f"<b>{x_axis.replace('_score', '')} vs {y_axis.replace('_score', '')}</b>",
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=9)
    fig_scatter.add_hline(y=50, line_dash="dash", line_color="#30363d")
    fig_scatter.add_vline(x=50, line_dash="dash", line_color="#30363d")
    fig_scatter.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", title_font_color="#ffffff",
        legend=dict(bgcolor="#161b22", font_color="#c9d1d9"),
    )
    fig_scatter.update_xaxes(gridcolor="#30363d", zerolinecolor="#30363d")
    fig_scatter.update_yaxes(gridcolor="#30363d", zerolinecolor="#30363d")
    st.plotly_chart(fig_scatter, use_container_width=True, key="chart_scatter")

    st.markdown(
        "Companies in the **bottom-left** are weak on both dimensions; "
        "**top-right** are strong on both."
    )

    st.markdown("---")
    st.markdown("**KPI correlation matrix**")
    all_feats = E_FEATURES + S_FEATURES + G_FEATURES + F_FEATURES
    corr = df[all_feats].corr()
    fig_corr = px.imshow(
        corr, x=all_feats, y=all_feats, color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1, height=650, labels=dict(color="corr"),
    )
    fig_corr.update_layout(
        xaxis_tickangle=-45, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", coloraxis_colorbar=dict(title="Correlation"),
    )
    st.plotly_chart(fig_corr, use_container_width=True, key="chart_corr")
