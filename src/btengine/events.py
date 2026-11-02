"""Zdarzenia przeplywajace przez petle backtestu."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(Enum):
    BUY = 1
    SELL = -1


@dataclass(frozen=True, slots=True)
class Bar:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True, slots=True)
class Order:
    timestamp: datetime
    symbol: str
    side: Side
    quantity: float


@dataclass(frozen=True, slots=True)
class Fill:
    timestamp: datetime
    symbol: str
    side: Side
    quantity: float
    price: float
    commission: float
