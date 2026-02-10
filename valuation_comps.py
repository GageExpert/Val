"""Comparable company valuation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class CompInput:
    peer: str
    multiple_type: str
    multiple: float


@dataclass
class CompsResult:
    implied_value: float
    multiple_type: str
    peers: List[CompInput]
    stats: Dict[str, float]


def compute_implied_value(metric: float, multiple: float) -> float:
    return metric * multiple


def summarize_peers(peers: List[CompInput]) -> Dict[str, float]:
    values = [peer.multiple for peer in peers if peer.multiple]
    if not values:
        return {"median": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "median": float(np.median(values)),
        "mean": float(np.mean(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def comps_valuation(metric: float, peers: List[CompInput]) -> CompsResult:
    stats = summarize_peers(peers)
    implied = compute_implied_value(metric, stats["median"])
    multiple_type = peers[0].multiple_type if peers else "EV/EBITDA"
    return CompsResult(implied_value=implied, multiple_type=multiple_type, peers=peers, stats=stats)
