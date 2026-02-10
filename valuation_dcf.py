"""DCF valuation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class DCFInputs:
    ufcf: List[float]
    wacc: float
    terminal_method: str
    terminal_value: float
    debt: float
    cash: float
    shares: float


@dataclass
class DCFResult:
    enterprise_value: float
    equity_value: float
    share_price: float
    pv_ufcf: float
    pv_terminal: float


def discount_factor(wacc: float, year: int) -> float:
    return 1 / ((1 + wacc) ** year)


def pv_cashflows(ufcf: List[float], wacc: float) -> float:
    return sum(cf * discount_factor(wacc, idx + 1) for idx, cf in enumerate(ufcf))


def dcf_valuation(inputs: DCFInputs) -> DCFResult:
    pv_ufcf = pv_cashflows(inputs.ufcf, inputs.wacc)
    pv_terminal = inputs.terminal_value * discount_factor(inputs.wacc, len(inputs.ufcf))
    enterprise_value = pv_ufcf + pv_terminal
    equity_value = enterprise_value - inputs.debt + inputs.cash
    share_price = equity_value / inputs.shares if inputs.shares else 0.0
    return DCFResult(
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        share_price=share_price,
        pv_ufcf=pv_ufcf,
        pv_terminal=pv_terminal,
    )


def terminal_value_exit_multiple(ebitda: float, multiple: float) -> float:
    return ebitda * multiple


def terminal_value_perpetuity(ufcf_next: float, wacc: float, growth: float) -> float:
    if wacc <= growth:
        return float("nan")
    return ufcf_next / (wacc - growth)
