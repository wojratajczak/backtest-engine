"""Metryki wynikow."""
from datetime import datetime

import numpy as np


def returns(equity_curve: list[tuple[datetime, float]]) -> np.ndarray:
    values = np.array([e for _, e in equity_curve], dtype=float)
    return np.diff(values) / values[:-1]


def sharpe(equity_curve: list[tuple[datetime, float]], periods: int = 252) -> float:
    r = returns(equity_curve)
    if r.size == 0 or r.std() == 0:
        return 0.0
    return float(np.sqrt(periods) * r.mean() / r.std())


def max_drawdown(equity_curve: list[tuple[datetime, float]]) -> float:
    values = np.array([e for _, e in equity_curve], dtype=float)
    peak = np.maximum.accumulate(values)
    return float(((values - peak) / peak).min())
