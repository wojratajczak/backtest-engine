"""Zrodla danych: abstrakcja, wspolna baza na ramce pandas, implementacje."""
import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from .events import Bar

REQUIRED_COLUMNS = ("Date", "Open", "High", "Low", "Close", "Volume")


class DataFeed(ABC):
    """Kazdy feed oddaje bary chronologicznie i tylko do biezacej chwili."""

    @abstractmethod
    def stream(self) -> Iterator[Bar]: ...

    @property
    @abstractmethod
    def symbols(self) -> list[str]: ...


class FrameFeed(DataFeed):
    """Wspolna baza dla zrodel trzymajacych notowania w ramce pandas."""

    def __init__(self, symbol: str, frame: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
        if missing:
            raise ValueError(f"brakujace kolumny w danych: {', '.join(missing)}")
        self._symbol = symbol
        self._frame = frame.sort_values("Date").reset_index(drop=True)

    @property
    def symbols(self) -> list[str]:
        return [self._symbol]

    @property
    def frame(self) -> pd.DataFrame:
        return self._frame

    def __len__(self) -> int:
        return len(self._frame)

    def stream(self) -> Iterator[Bar]:
        for row in self._frame.itertuples(index=False):
            yield Bar(
                timestamp=pd.Timestamp(row.Date).to_pydatetime(),
                symbol=self._symbol,
                open=float(row.Open),
                high=float(row.High),
                low=float(row.Low),
                close=float(row.Close),
                volume=float(row.Volume),
            )


class CSVFeed(FrameFeed):
    """Notowania z pliku CSV na dysku."""

    def __init__(self, path: Path | str, symbol: str) -> None:
        super().__init__(symbol, pd.read_csv(path, parse_dates=["Date"]))


class StooqFeed(FrameFeed):
    """Dzienne notowania pobierane po HTTP prosto ze stooq.

    Symbole: 'aapl.us', 'msft.us' dla USA, 'pkn', 'kgh' dla GPW.
    """

    BASE_URLS = ("https://stooq.com/q/d/l/", "https://stooq.pl/q/d/l/")
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/csv,text/plain,*/*",
    }

    @classmethod
    def download(
        cls,
        symbol: str,
        start: str | date | None = None,
        end: str | date | None = None,
        timeout: int = 20,
        cache_dir: Path | str | None = None,
    ) -> "StooqFeed":
        cache_path = None
        if cache_dir is not None:
            cache_path = Path(cache_dir) / f"{symbol}_{start}_{end}.csv"
            if cache_path.exists():
                return cls(symbol, pd.read_csv(cache_path, parse_dates=["Date"]))

        params = {
            "s": symbol,
            "d1": _compact(start or date(1990, 1, 1)),
            "d2": _compact(end or date.today()),
            "i": "d",
        }

        frame = None
        last_error: Exception | None = None
        for base_url in cls.BASE_URLS:
            try:
                response = requests.get(
                    base_url, params=params, headers=cls.HEADERS, timeout=timeout
                )
                response.raise_for_status()
                frame = cls.parse(response.text, symbol)
                break
            except (requests.RequestException, ValueError) as exc:
                last_error = exc

        if frame is None:
            raise RuntimeError(
                f"nie udalo sie pobrac '{symbol}' ze stooq: {last_error}"
            ) from last_error

        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(cache_path, index=False)
        return cls(symbol, frame)

    @staticmethod
    def parse(csv_text: str, symbol: str) -> pd.DataFrame:
        """Stooq na blad odpowiada zwyklym tekstem ze statusem 200, nie bledem HTTP."""
        stripped = csv_text.strip()
        header = stripped.splitlines()[0] if stripped else ""
        if not header.startswith("Date"):
            raise ValueError(f"stooq nie zwrocil danych dla '{symbol}': {stripped[:120]!r}")
        frame = pd.read_csv(StringIO(csv_text), parse_dates=["Date"])
        if frame.empty:
            raise ValueError(f"stooq zwrocil pusty zbior dla '{symbol}'")
        return frame


class YahooFeed(FrameFeed):
    """Dzienne notowania z publicznego endpointu wykresowego Yahoo Finance (JSON).

    Symbole: 'AAPL', 'MSFT' dla USA, 'PKN.WA', 'KGH.WA' dla GPW.
    """

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
    }

    @classmethod
    def download(
        cls,
        symbol: str,
        start: str | date | None = None,
        end: str | date | None = None,
        timeout: int = 20,
        cache_dir: Path | str | None = None,
    ) -> "YahooFeed":
        cache_path = None
        if cache_dir is not None:
            cache_path = Path(cache_dir) / f"yahoo_{symbol}_{start}_{end}.csv"
            if cache_path.exists():
                return cls(symbol, pd.read_csv(cache_path, parse_dates=["Date"]))

        params = {
            "period1": _epoch(start or date(1990, 1, 1)),
            "period2": _epoch(end or date.today()),
            "interval": "1d",
        }
        response = requests.get(
            cls.BASE_URL + symbol, params=params, headers=cls.HEADERS, timeout=timeout
        )
        response.raise_for_status()
        frame = cls.parse(response.text, symbol)

        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(cache_path, index=False)
        return cls(symbol, frame)

    @staticmethod
    def parse(payload: str, symbol: str) -> pd.DataFrame:
        """Yahoo sygnalizuje bledy wewnatrz JSON-a, nie statusem HTTP."""
        try:
            chart = json.loads(payload)["chart"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f"Yahoo zwrocil nieoczekiwana odpowiedz dla '{symbol}'") from exc

        if chart.get("error"):
            raise ValueError(f"Yahoo zglasza blad dla '{symbol}': {chart['error']}")

        results = chart.get("result") or []
        if not results:
            raise ValueError(f"Yahoo nie zwrocil danych dla '{symbol}'")

        result = results[0]
        quote = result["indicators"]["quote"][0]
        frame = pd.DataFrame(
            {
                "Date": pd.to_datetime(result["timestamp"], unit="s").normalize(),
                "Open": quote["open"],
                "High": quote["high"],
                "Low": quote["low"],
                "Close": quote["close"],
                "Volume": quote["volume"],
            }
        ).dropna(subset=["Open", "High", "Low", "Close"])

        if frame.empty:
            raise ValueError(f"Yahoo zwrocil pusty zbior dla '{symbol}'")
        return frame.reset_index(drop=True)


def _compact(value: str | date) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    return str(value).replace("-", "")


def _epoch(value: str | date) -> int:
    if isinstance(value, str):
        value = date.fromisoformat(value)
    moment = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return int(moment.timestamp())


def make_feed(kind: str, **kwargs) -> DataFeed:
    """Factory: dopisujesz kolejne zrodla bez dotykania reszty silnika."""
    if kind == "csv":
        return CSVFeed(**kwargs)
    if kind == "stooq":
        return StooqFeed.download(**kwargs)
    if kind == "yahoo":
        return YahooFeed.download(**kwargs)
    raise ValueError(f"nieznane zrodlo danych: {kind}")
