"""Generate synthetic SEC-like data for testing."""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_synthetic_statements(years: list[int]) -> pd.DataFrame:
    rows = []
    revenue = 1000
    for year in years:
        revenue *= 1.05
        rows.extend(
            [
                {"statement": "IS", "line_item": "Revenue", "year": year, "value": revenue},
                {"statement": "IS", "line_item": "Cost of revenue", "year": year, "value": revenue * 0.4},
                {"statement": "IS", "line_item": "Operating income", "year": year, "value": revenue * 0.2},
                {"statement": "IS", "line_item": "Net income", "year": year, "value": revenue * 0.15},
                {"statement": "BS", "line_item": "Total assets", "year": year, "value": revenue * 1.2},
                {"statement": "BS", "line_item": "Total liabilities", "year": year, "value": revenue * 0.6},
                {"statement": "BS", "line_item": "Total equity", "year": year, "value": revenue * 0.6},
                {"statement": "CF", "line_item": "D&A", "year": year, "value": revenue * 0.05},
                {"statement": "CF", "line_item": "Capex", "year": year, "value": revenue * 0.04},
            ]
        )
    return pd.DataFrame(rows)
