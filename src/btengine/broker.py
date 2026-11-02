"""Egzekucja zlecen: poslizg i prowizja."""
from abc import ABC, abstractmethod

from .events import Bar, Fill, Order


class Broker(ABC):
    @abstractmethod
    def execute(self, order: Order, bar: Bar) -> Fill: ...


class SimpleBroker(Broker):
    """Wypelnia po otwarciu NASTEPNEGO bara - to blokuje look-ahead bias."""

    def __init__(self, slippage_bps: float = 1.0, commission_bps: float = 0.5) -> None:
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps

    def execute(self, order: Order, bar: Bar) -> Fill:
        slip = bar.open * (self.slippage_bps / 10_000) * order.side.value
        price = bar.open + slip
        commission = abs(order.quantity * price) * (self.commission_bps / 10_000)
        return Fill(
            timestamp=bar.timestamp,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            commission=commission,
        )
