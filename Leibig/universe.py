"""Selected S&P 500 universe: ~50 companies spanning all 11 GICS sectors.

Rationale for the selection:
  * All 11 GICS sectors represented.
  * Mix of mega-cap leaders, transition stories, and sector exemplars so the
    sustainability-alpha methodology is exercised across structurally different
    business models.
  * Well-known, liquid names with complete statement history (for trend features).

This is the focused universe for the deep, original-feature approach. The boss
asked for scalability, not 500 companies — so we go deep on ~50 and design the
framework so the same code scales to any N.
"""
import pandas as pd

UNIVERSE = [
    # Information Technology
    "AAPL", "MSFT", "NVDA", "AVGO",
    # Communication Services
    "GOOGL", "META", "VZ", "TMUS",
    # Consumer Discretionary
    "AMZN", "TSLA", "HD", "NKE",
    # Consumer Staples
    "PG", "KO", "PEP", "WMT",
    # Health Care
    "JNJ", "UNH", "PFE", "LLY",
    # Financials
    "JPM", "BAC", "GS", "BLK",
    # Industrials
    "CAT", "GE", "HON", "UPS",
    # Energy
    "XOM", "CVX", "COP", "SLB",
    # Materials
    "LIN", "FCX", "NEM", "SHW",
    # Utilities
    "NEE", "DUK", "SO", "AEP",
    # Real Estate
    "AMT", "PLD", "SPG", "EQIX",
    # a few more for breadth
    "MRK", "INTC", "CRM", "ABT", "LOW", "COST",
]

SECTOR_OF = {  # canonical GICS sector per ticker (from Wikipedia list)
    "AAPL": "Information Technology", "MSFT": "Information Technology",
    "NVDA": "Information Technology", "AVGO": "Information Technology",
    "GOOGL": "Communication Services", "META": "Communication Services",
    "VZ": "Communication Services", "TMUS": "Communication Services",
    "AMZN": "Consumer Discretionary", "TSLA": "Consumer Discretionary",
    "HD": "Consumer Discretionary", "NKE": "Consumer Discretionary",
    "PG": "Consumer Staples", "KO": "Consumer Staples",
    "PEP": "Consumer Staples", "WMT": "Consumer Staples",
    "JNJ": "Health Care", "UNH": "Health Care",
    "PFE": "Health Care", "LLY": "Health Care",
    "JPM": "Financials", "BAC": "Financials",
    "GS": "Financials", "BLK": "Financials",
    "CAT": "Industrials", "GE": "Industrials",
    "HON": "Industrials", "UPS": "Industrials",
    "XOM": "Energy", "CVX": "Energy",
    "COP": "Energy", "SLB": "Energy",
    "LIN": "Materials", "FCX": "Materials",
    "NEM": "Materials", "SHW": "Materials",
    "NEE": "Utilities", "DUK": "Utilities",
    "SO": "Utilities", "AEP": "Utilities",
    "AMT": "Real Estate", "PLD": "Real Estate",
    "SPG": "Real Estate", "EQIX": "Real Estate",
    "MRK": "Health Care", "INTC": "Information Technology",
    "CRM": "Information Technology", "ABT": "Health Care",
    "LOW": "Consumer Discretionary",
    "COST": "Consumer Staples",
}


def universe_df() -> pd.DataFrame:
    return pd.DataFrame(
        [{"Symbol": s, "Sector": SECTOR_OF[s]} for s in UNIVERSE])


if __name__ == "__main__":
    df = universe_df()
    print(f"{len(df)} companies across {df['Sector'].nunique()} sectors")
    print(df["Sector"].value_counts().to_string())
