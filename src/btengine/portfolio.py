"""Stan portfela: pozycje, gotowka, equity curve."""
from datetime import datetime

from .events import Fill


class Portfolio:
    def __init__(self, initial_cash: float = 100_000.0) -> None:
        self.cash = initial_cash
        self.positions: dict[str, float] = {}
        self.equity_curve: list[tuple[datetime, float]] = []

    def on_fill(self, fill: Fill) -> None:
        signed_qty = fill.quantity * fill.side.value
        self.positions[fill.symbol] = self.positions.get(fill.symbol, 0.0) + signed_qty
        self.cash -= signed_qty * fill.price + fill.commission

    def mark_to_market(self, timestamp: datetime, prices: dict[str, float]) -> float:
        exposure = sum(qty * prices.get(sym, 0.0) for sym, qty in self.positions.items())
        equity = self.cash + exposure
        self.equity_curve.append((timestamp, equity))
        return equity
