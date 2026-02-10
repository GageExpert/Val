"""Sensitivity grid generation shared across app and Excel."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from valuation_dcf import DCFInputs, dcf_valuation, terminal_value_exit_multiple, terminal_value_perpetuity


@dataclass
class SensitivityGrid:
    x_values: List[float]
    y_values: List[float]
    grid: np.ndarray


def build_grid(min_val: float, max_val: float, size: int) -> List[float]:
    return list(np.linspace(min_val, max_val, size))


def dcf_sensitivity(
    base_inputs: DCFInputs,
    wacc_range: tuple[float, float],
    terminal_range: tuple[float, float],
    size: int,
    terminal_method: str,
    metric: str = "share_price",
) -> SensitivityGrid:
    wacc_values = build_grid(wacc_range[0], wacc_range[1], size)
    terminal_values = build_grid(terminal_range[0], terminal_range[1], size)
    grid = np.zeros((len(wacc_values), len(terminal_values)))

    for i, wacc in enumerate(wacc_values):
        for j, terminal in enumerate(terminal_values):
            if terminal_method == "exit_multiple":
                tv = terminal_value_exit_multiple(base_inputs.terminal_value, terminal)
            else:
                tv = terminal_value_perpetuity(base_inputs.terminal_value, wacc, terminal)
            inputs = DCFInputs(
                ufcf=base_inputs.ufcf,
                wacc=wacc,
                terminal_method=terminal_method,
                terminal_value=tv,
                debt=base_inputs.debt,
                cash=base_inputs.cash,
                shares=base_inputs.shares,
            )
            result = dcf_valuation(inputs)
            grid[i, j] = getattr(result, metric)
    return SensitivityGrid(x_values=wacc_values, y_values=terminal_values, grid=grid)
