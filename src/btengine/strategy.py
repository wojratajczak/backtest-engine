"""Strategy pattern + Template Method."""
from abc import ABC, abstractmethod

import numpy as np

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

    def reset(self) -> None:
        self.history = []


class SMACrossover(Strategy):
    """Kupuje, gdy srednia szybka przecina wolna od dolu; sprzedaje przy przecieciu w dol."""

    def __init__(self, fast: int = 20, slow: int = 50, size: float = 100.0) -> None:
        super().__init__()
        self.fast, self.slow, self.size = fast, slow, size
        self._invested = False

    def reset(self) -> None:
        super().reset()
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


class MeanReversion(Strategy):
    """Kupuje, gdy cena odchyla sie w dol od sredniej kroczacej o zadana liczbe odchylen."""

    def __init__(
        self,
        window: int = 20,
        entry_z: float = -1.5,
        exit_z: float = 0.0,
        size: float = 100.0,
    ) -> None:
        super().__init__()
        self.window = window
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.size = size
        self._invested = False

    def reset(self) -> None:
        super().reset()
        self._invested = False

    def zscore(self) -> float | None:
        if len(self.history) < self.window:
            return None
        closes = np.array([b.close for b in self.history[-self.window :]], dtype=float)
        sd = closes.std(ddof=1)
        if sd == 0:
            return None
        return float((closes[-1] - closes.mean()) / sd)

    def on_bar(self, bar: Bar) -> list[Order]:
        z = self.zscore()
        if z is None:
            return []
        if z <= self.entry_z and not self._invested:
            self._invested = True
            return [Order(bar.timestamp, bar.symbol, Side.BUY, self.size)]
        if z >= self.exit_z and self._invested:
            self._invested = False
            return [Order(bar.timestamp, bar.symbol, Side.SELL, self.size)]
        return []


class BuyAndHold(Strategy):
    """Kupuje na pierwszym barze i trzyma do konca. Punkt odniesienia dla reszty."""

    def __init__(self, size: float = 100.0) -> None:
        super().__init__()
        self.size = size
        self._invested = False

    def reset(self) -> None:
        super().reset()
        self._invested = False

    def on_bar(self, bar: Bar) -> list[Order]:
        if self._invested:
            return []
        self._invested = True
        return [Order(bar.timestamp, bar.symbol, Side.BUY, self.size)]
