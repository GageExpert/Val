"""Excel report generation with styling."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict

import pandas as pd


def _format_sheet(writer, sheet_name: str) -> None:
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    header_format = workbook.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1})
    for col_num, value in enumerate(worksheet.table[0] if hasattr(worksheet, "table") else []):
        worksheet.write(0, col_num, value, header_format)
    worksheet.freeze_panes(1, 1)


def generate_report(
    output_path: str,
    company_summary: Dict[str, str],
    statements: Dict[str, pd.DataFrame],
    assumptions: Dict[str, object],
    valuation_tables: Dict[str, pd.DataFrame],
    sensitivity_df: pd.DataFrame,
    diagnostics: Dict[str, object],
    source_trace: pd.DataFrame,
) -> None:
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        summary_df = pd.DataFrame(
            [
                {
                    **company_summary,
                    "timestamp": datetime.utcnow().isoformat(),
                    "model_version": "1.0",
                }
            ]
        )
        summary_df.to_excel(writer, sheet_name="Company Summary", index=False)

        for name, df in statements.items():
            df.to_excel(writer, sheet_name=name, index=False)

        assumptions_df = pd.json_normalize(assumptions)
        assumptions_df.to_excel(writer, sheet_name="Drivers & Assumptions", index=False)

        for name, df in valuation_tables.items():
            df.to_excel(writer, sheet_name=name, index=False)

        sensitivity_df.to_excel(writer, sheet_name="Sensitivity", index=False)

        diagnostics_df = pd.DataFrame([diagnostics])
        diagnostics_df.to_excel(writer, sheet_name="Diagnostics & Narrative", index=False)

        source_trace.to_excel(writer, sheet_name="Source Trace", index=False)

        for sheet in writer.sheets:
            worksheet = writer.sheets[sheet]
            worksheet.set_column(0, 30, 18)
            worksheet.freeze_panes(1, 1)
