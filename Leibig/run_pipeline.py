"""Data-gathering pipeline: collect deep statement data -> compute ESG features -> CSV.

Run:  python src/run_pipeline.py [--force]
This ONLY gathers data and builds the feature dataset. No ranking, no scoring,
no visualizations, no portfolio. The feature definitions (grouped by E/S/G) live
in docs/features.md and src/features.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from universe import UNIVERSE, SECTOR_OF
from collect_deep import collect
from features import build_features
from scoring_liebig import score as liebig_score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"


def main(force=False):
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"1) Collecting deep data for {len(UNIVERSE)} companies (yfinance)...")
    records = collect(UNIVERSE, force=force)
    records = [r for r in records if "_error" not in r]
    print(f"   {len(records)} companies with usable data.")

    print("2) Computing ESG features (grouped by E / S / G)...")
    df = build_features(records)
    df.insert(1, "Sector", df["Symbol"].map(SECTOR_OF))
    df = df[~df["Sector"].isna()].reset_index(drop=True)
    print(f"   {len(df)} companies, {df.shape[1]} columns.")

    out = OUT / "sp500_esg_features.csv"
    df.to_csv(out, index=False)
    print(f"   Dataset written to {out}")

    print("3) Scoring: Liebig (min) vs equal-weighted sum vs geometric mean...")
    scores = liebig_score(df)
    scores = scores.sort_values("liebig_score", ascending=False).reset_index(drop=True)
    scores.insert(0, "rank", range(1, len(scores) + 1))
    scores_out = OUT / "sp500_liebig_scores.csv"
    scores.to_csv(scores_out, index=False)
    print(f"   Ranked scores written to {scores_out}")
    print(f"   Top 5: {list(scores.head(5)['Symbol'])}")
    print(f"   Binding dimensions: {dict(scores['binding_dimension'].value_counts())}")

    print("\nColumns by group:")
    for grp, cols in [
        ("Identifiers", [c for c in df.columns if c in ("Symbol", "Sector", "Industry")]),
        ("Environmental (E)", [c for c in df.columns if c.startswith("E_")]),
        ("Social (S)", [c for c in df.columns if c.startswith("S_")]),
        ("Governance (G)", [c for c in df.columns if c.startswith("G_")]),
        ("Financial Health (F)", [c for c in df.columns if c.startswith("F_")]),
    ]:
        print(f"  {grp} ({len(cols)}): {cols}")
    print(f"\nCoverage: {len(df)} companies.")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
