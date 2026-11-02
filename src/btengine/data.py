"""Zrodla danych: abstrakcja + implementacje (Factory)."""
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from .events import Bar


class DataFeed(ABC):
    """Kazdy feed oddaje bary chronologicznie i tylko do biezacej chwili."""

    @abstractmethod
    def stream(self) -> Iterator[Bar]: ...

    @property
    @abstractmethod
    def symbols(self) -> list[str]: ...


class CSVFeed(DataFeed):
    def __init__(self, path: Path, symbol: str) -> None:
        self._symbol = symbol
        self._df = pd.read_csv(path, parse_dates=["Date"]).sort_values("Date")

    @property
    def symbols(self) -> list[str]:
        return [self._symbol]

    def stream(self) -> Iterator[Bar]:
        for row in self._df.itertuples(index=False):
            yield Bar(
                timestamp=row.Date,
                symbol=self._symbol,
                open=float(row.Open),
                high=float(row.High),
                low=float(row.Low),
                close=float(row.Close),
                volume=float(row.Volume),
            )


def make_feed(kind: str, **kwargs) -> DataFeed:
    """Factory: dopisujesz kolejne zrodla bez dotykania reszty silnika."""
    registry: dict[str, type[DataFeed]] = {"csv": CSVFeed}
    try:
        return registry[kind](**kwargs)
    except KeyError:
        raise ValueError(f"nieznane zrodlo danych: {kind}") from None
