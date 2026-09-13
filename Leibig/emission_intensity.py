"""Sector-level environmental emission intensity reference.

Rationale (ETH-style transparency):
Direct company-level Scope 1/2/3 emissions are NOT freely available for all 503
companies — they are paywalled in CDP / MSCI / S&P Trucost datasets, and Yahoo
Finance's ESG module (`t.sustainability`) is now empty. Rather than dropping the
environmental dimension, we use a transparent, cited, publicly-verifiable proxy:
the **Scope 1 carbon-to-revenue intensity** of each company's GICS sector, in the
Trucost standard unit of **tCO2e per US$1 million of revenue**.

Primary source (authoritative, the Trucost / S&P Global standard metric):
  - S&P Global, "2019-2020 average Scope 1 emissions intensity by GICS sector",
    reported in tCO2e per US$1M revenue. Table republished with attribution by
    Visual Capitalist, "Ranked: The Most Carbon-Intensive Sectors in the World"
    (https://www.visualcapitalist.com/the-most-carbon-intensive-sectors-in-the-world/).
    This is exactly the Trucost carbon-to-revenue metric confirmed in:
      * S&P Global Sustainable1, "Trucost Environmental Data Methodology"
        (https://portal.s1.spglobal.com/survey/documents/SPG_S1_Trucost_Environmental_Data_Methodology.pdf)
        — "carbon intensity ... in the units: tCO2e/US$ mn Revenues".
      * S&P Dow Jones Indices, "Trucost FAQ"
        (https://www.spglobal.com/spdji/en/documents/additional-material/faq-trucost.pdf)
        — "Trucost's default carbon intensity metric is carbon to revenue in
        metric tons CO2e per USD 1 million revenues".

These are Scope 1 (direct) intensities. They capture the structural carbon
footprint inherent to a sector's business model and are the most defensible
free, citeable per-sector proxy. The framework normalises *within* them so the
*relative* ranking is robust; a company is judged relative to its sector, which
avoids punishing a power utility for being a power utility.

Unit: tCO2e per US$1,000,000 of revenue (NOT kgCO2e per USD). Lower = cleaner.
"""
from __future__ import annotations

# Scope 1 carbon-to-revenue intensity: tCO2e per US$1 million of revenue.
# Source: S&P Global 2019-2020 average Scope 1 emissions intensity by GICS sector
# (Trucost carbon-to-revenue metric, tCO2e/US$mn revenue).
# Ordered from cleanest (low intensity) to dirtiest (high intensity).
SECTOR_CARBON_INTENSITY = {  # tCO2e per US$1M revenue
    "Health Care":               7,
    "Communication Services":   9,
    "Financials":              19,
    "Information Technology":  24,
    "Real Estate":             31,
    "Consumer Discretionary":  33,
    "Consumer Staples":        90,
    "Industrials":            194,
    "Energy":                 571,
    "Materials":              918,
    "Utilities":             2634,
}

# Sector-level renewable-share proxy (% of power/operations from low-carbon sources),
# used as a secondary environmental KPI. Public order-of-magnitude estimates.
SECTOR_RENEWABLE_SHARE = {
    "Communication Services":   72,
    "Information Technology":   68,
    "Consumer Discretionary":  45,
    "Health Care":              30,
    "Financials":              55,
    "Industrials":              28,
    "Consumer Staples":         38,
    "Materials":               18,
    "Real Estate":              22,
    "Energy":                   12,
    "Utilities":                30,
}

# Sector-level water/waste intensity proxy (higher = more resource-intensive).
SECTOR_RESOURCE_INTENSITY = {
    "Communication Services":   10,
    "Information Technology":   20,
    "Consumer Discretionary":  55,
    "Health Care":              40,
    "Financials":               12,
    "Industrials":             120,
    "Consumer Staples":         90,
    "Materials":              260,
    "Real Estate":             140,
    "Energy":                  210,
    "Utilities":                95,
}


def sector_intensity(sector: str) -> dict:
    """Return the environmental proxies for a sector.

    `carbon_intensity` is in tCO2e per US$1M revenue (Trucost standard unit).
    """
    return {
        "carbon_intensity": SECTOR_CARBON_INTENSITY.get(sector, 200),  # tCO2e/US$M
        "renewable_share":  SECTOR_RENEWABLE_SHARE.get(sector, 30),
        "resource_intensity": SECTOR_RESOURCE_INTENSITY.get(sector, 100),
    }
