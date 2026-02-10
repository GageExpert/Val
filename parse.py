"""Parsing utilities for numeric SEC values and year detection."""
from __future__ import annotations

import re
from typing import Optional, Tuple

import numpy as np

YEAR_RE = re.compile(r"(20\d{2})")


def parse_numeric(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        if cleaned in {"", "-", "—"}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def detect_year(label: str) -> Optional[int]:
    match = YEAR_RE.search(label)
    if not match:
        return None
    return int(match.group(1))


def scale_value(value: float, unit: str) -> float:
    scale = 1.0
    unit = unit.lower()
    if "usd" in unit and "shares" not in unit:
        scale = 1.0
    if "thousand" in unit:
        scale = 1_000.0
    if "million" in unit:
        scale = 1_000_000.0
    if "billion" in unit:
        scale = 1_000_000_000.0
    return float(value) * scale


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return np.nan
    return numerator / denominator


def clean_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip())
