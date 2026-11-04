"""Wykresy wynikow backtestu."""
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def drawdown_series(values: np.ndarray) -> np.ndarray:
    peak = np.maximum.accumulate(values)
    return (values - peak) / peak


def plot_equity(
    curves: dict[str, list[tuple[datetime, float]]],
    path: Path | str,
    title: str = "Backtest",
) -> Path:
    """Equity curve u gory, obsuniecia pod spodem. Zwraca sciezke zapisanego pliku."""
    fig, (ax_eq, ax_dd) = plt.subplots(
        2,
        1,
        figsize=(11, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    for label, curve in curves.items():
        dates = [timestamp for timestamp, _ in curve]
        values = np.array([value for _, value in curve], dtype=float)
        ax_eq.plot(dates, values, linewidth=1.4, label=label)
        ax_dd.fill_between(dates, drawdown_series(values) * 100, 0, alpha=0.3, label=label)

    ax_eq.set_title(title)
    ax_eq.set_ylabel("Equity")
    ax_eq.legend(frameon=False)
    ax_eq.grid(alpha=0.2)

    ax_dd.set_ylabel("Drawdown %")
    ax_dd.set_xlabel("Date")
    ax_dd.grid(alpha=0.2)

    fig.tight_layout()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out
