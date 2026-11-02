"""Strategy pattern + Template Method."""
from abc import ABC, abstractmethod

from .events import Bar, Order, Side


class Strategy(ABC):
    """Strategia widzi tylko zamkniety bar i zwraca zlecenia na nastepny."""

    def __init__(self) -> None:
        self.history: list[Bar] = []

    def handle(self, bar: Bar) -> list[Order]:
        """Template Method: ksiegowanie historii + hook uzytkownika."""
        self.history.append(bar)
        return self.on_bar(bar)

    @abstractmethod
    def on_bar(self, bar: Bar) -> list[Order]: ...


class SMACrossover(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50, size: float = 100.0) -> None:
        super().__init__()
        self.fast, self.slow, self.size = fast, slow, size
        self._invested = False

    def on_bar(self, bar: Bar) -> list[Order]:
        if len(self.history) < self.slow:
            return []
        closes = [b.close for b in self.history]
        fast_ma = sum(closes[-self.fast :]) / self.fast
        slow_ma = sum(closes[-self.slow :]) / self.slow

        if fast_ma > slow_ma and not self._invested:
            self._invested = True
            return [Order(bar.timestamp, bar.symbol, Side.BUY, self.size)]
        if fast_ma < slow_ma and self._invested:
            self._invested = False
            return [Order(bar.timestamp, bar.symbol, Side.SELL, self.size)]
        return []
