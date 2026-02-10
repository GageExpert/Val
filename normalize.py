"""Normalize SEC facts into canonical statement long format."""
from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

STATEMENT_TAGS = {
    "IS": {
        "Revenues": "Revenue",
        "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
        "CostOfRevenue": "Cost of revenue",
        "GrossProfit": "Gross profit",
        "OperatingIncomeLoss": "Operating income",
        "NetIncomeLoss": "Net income",
    },
    "BS": {
        "Assets": "Total assets",
        "Liabilities": "Total liabilities",
        "StockholdersEquity": "Total equity",
        "CashAndCashEquivalentsAtCarryingValue": "Cash and equivalents",
        "InventoryNet": "Inventory",
        "AccountsReceivableNetCurrent": "Accounts receivable",
        "AccountsPayableCurrent": "Accounts payable",
        "PropertyPlantAndEquipmentNet": "PP&E",
        "LongTermDebtNoncurrent": "Long-term debt",
    },
    "CF": {
        "NetCashProvidedByUsedInOperatingActivities": "Net cash from ops",
        "PaymentsToAcquirePropertyPlantAndEquipment": "Capex",
        "DepreciationDepletionAndAmortization": "D&A",
    },
}


def map_facts_to_statements(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    for statement, tag_map in STATEMENT_TAGS.items():
        for tag, label in tag_map.items():
            subset = df[df["tag"] == tag]
            if subset.empty:
                continue
            for _, row in subset.iterrows():
                rows.append(
                    {
                        "statement": statement,
                        "line_item": label,
                        "year": int(row["fy"]) if pd.notna(row["fy"]) else None,
                        "value": row["value"],
                        "source_tag": tag,
                        "source_taxonomy": row["taxonomy"],
                    }
                )
    return pd.DataFrame(rows)


def canonicalize_long_format(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    return df


def ensure_statement_coverage(df: pd.DataFrame) -> Dict[str, List[str]]:
    missing: Dict[str, List[str]] = {}
    for statement in {"IS", "BS", "CF"}:
        if df[df["statement"] == statement].empty:
            missing[statement] = ["No mapped tags"]
    return missing
