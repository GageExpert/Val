"""Forecasting logic for all line items with balancing rules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from classify import classify_line_item
from parse import safe_divide


@dataclass
class ForecastResult:
    forecast: pd.DataFrame
    assumptions_used: Dict[str, dict]
    diagnostics: Dict[str, object]


def _historical_pivot(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index="line_item", columns="year", values="value", aggfunc="mean")


def _latest_value(series: pd.Series) -> float:
    series = series.dropna()
    return float(series.iloc[-1]) if not series.empty else 0.0


def _ratio_to_revenue(line_values: pd.Series, revenue_series: pd.Series) -> float:
    return float(np.nanmedian(line_values / revenue_series))


def build_revenue_path(last_revenue: float, growth_rates: List[float]) -> List[float]:
    revenues = []
    current = last_revenue
    for growth in growth_rates:
        current = current * (1 + growth)
        revenues.append(current)
    return revenues


def forecast_statements(
    df: pd.DataFrame,
    forecast_years: List[int],
    assumptions: Dict[str, dict],
) -> ForecastResult:
    df = df.copy()
    df["driver_family"] = df["line_item"].apply(classify_line_item)
    hist_pivot = _historical_pivot(df)
    years = sorted(df["year"].unique())

    revenue_hist = hist_pivot.loc["Revenue"] if "Revenue" in hist_pivot.index else pd.Series(dtype=float)
    last_revenue = _latest_value(revenue_hist)
    growth_path = assumptions.get("revenue_growth", {}).get("path", [0.05] * len(forecast_years))
    revenue_fcst = build_revenue_path(last_revenue, growth_path)

    forecast_rows: List[dict] = []

    for line_item in hist_pivot.index:
        hist_values = hist_pivot.loc[line_item]
        driver = classify_line_item(line_item)
        for idx, year in enumerate(forecast_years):
            value = None
            if line_item == "Revenue":
                value = revenue_fcst[idx]
            elif driver in {"margin-driven", "revenue-driven"}:
                ratio = _ratio_to_revenue(hist_values, revenue_hist)
                value = ratio * revenue_fcst[idx]
            elif driver == "working-capital":
                ratio = _ratio_to_revenue(hist_values, revenue_hist)
                value = ratio * revenue_fcst[idx]
            elif driver == "fixed":
                trend = np.nanmedian(hist_values)
                value = trend
            elif driver == "financing":
                value = _latest_value(hist_values)
            else:
                value = _latest_value(hist_values)
            forecast_rows.append(
                {
                    "statement": df[df["line_item"] == line_item]["statement"].iloc[0],
                    "line_item": line_item,
                    "year": year,
                    "value": float(value) if value is not None else 0.0,
                    "forecast_method": driver,
                }
            )

    forecast_df = pd.DataFrame(forecast_rows)

    diagnostics = _balance_sheet_reconcile(df, forecast_df)

    return ForecastResult(
        forecast=forecast_df,
        assumptions_used={"revenue_growth": growth_path},
        diagnostics=diagnostics,
    )


def _balance_sheet_reconcile(hist_df: pd.DataFrame, forecast_df: pd.DataFrame) -> Dict[str, object]:
    diagnostics: Dict[str, object] = {"plugs": []}
    bs_forecast = forecast_df[forecast_df["statement"] == "BS"].copy()
    if bs_forecast.empty:
        return diagnostics

    for year in sorted(bs_forecast["year"].unique()):
        year_df = bs_forecast[bs_forecast["year"] == year]
        total_assets = year_df[year_df["line_item"] == "Total assets"]["value"].sum()
        total_liab = year_df[year_df["line_item"] == "Total liabilities"]["value"].sum()
        total_equity = year_df[year_df["line_item"] == "Total equity"]["value"].sum()
        gap = total_assets - (total_liab + total_equity)
        if abs(gap) > 1e-2:
            plug_item = "Cash and equivalents"
            mask = (forecast_df["year"] == year) & (forecast_df["line_item"] == plug_item)
            if mask.any():
                forecast_df.loc[mask, "value"] += gap
            else:
                forecast_df = pd.concat(
                    [
                        forecast_df,
                        pd.DataFrame(
                            [
                                {
                                    "statement": "BS",
                                    "line_item": plug_item,
                                    "year": year,
                                    "value": gap,
                                    "forecast_method": "plug",
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
            diagnostics["plugs"].append({"year": year, "amount": gap, "line_item": plug_item})
    return diagnostics


def build_ufcf(df: pd.DataFrame, tax_rate: float) -> pd.DataFrame:
    df = df.copy()
    is_df = df[df["statement"] == "IS"].pivot(index="line_item", columns="year", values="value")
    cf_df = df[df["statement"] == "CF"].pivot(index="line_item", columns="year", values="value")
    revenue = is_df.loc["Revenue"]
    ebit = is_df.loc["Operating income"] if "Operating income" in is_df.index else revenue * 0.15
    nopat = ebit * (1 - tax_rate)
    da = cf_df.loc["D&A"] if "D&A" in cf_df.index else revenue * 0.05
    capex = cf_df.loc["Capex"] if "Capex" in cf_df.index else revenue * 0.04
    nwc = np.zeros_like(revenue)
    ufcf = nopat + da - capex - nwc
    return pd.DataFrame(
        {
            "NOPAT": nopat,
            "D&A": da,
            "Capex": capex,
            "Delta NWC": nwc,
            "UFCF": ufcf,
        }
    )
