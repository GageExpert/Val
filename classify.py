"""Line item classification into driver families."""
from __future__ import annotations

from typing import Dict


DRIVER_FAMILIES = {
    "Revenue": "revenue-driven",
    "Cost of revenue": "margin-driven",
    "Gross profit": "margin-driven",
    "Operating income": "margin-driven",
    "Net income": "margin-driven",
    "Cash and equivalents": "working-capital",
    "Inventory": "working-capital",
    "Accounts receivable": "working-capital",
    "Accounts payable": "working-capital",
    "PP&E": "fixed",
    "Long-term debt": "financing",
    "Total assets": "total",
    "Total liabilities": "total",
    "Total equity": "total",
    "Net cash from ops": "cash-flow",
    "Capex": "fixed",
    "D&A": "fixed",
}


def classify_line_item(line_item: str) -> str:
    return DRIVER_FAMILIES.get(line_item, "other")


def apply_classification(df):
    df = df.copy()
    df["driver_family"] = df["line_item"].apply(classify_line_item)
    return df


def summarize_driver_families(df) -> Dict[str, int]:
    return df["driver_family"].value_counts().to_dict()
