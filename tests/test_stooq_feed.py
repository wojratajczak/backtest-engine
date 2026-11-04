"""Testy parsowania i pobierania danych ze stooq - bez ruchu sieciowego."""
from unittest.mock import Mock, patch

import pytest

from btengine.data import StooqFeed

CSV = """Date,Open,High,Low,Close,Volume
2024-01-02,100.0,105.0,99.0,104.0,1000
2024-01-03,106.0,110.0,105.0,109.0,1200
"""


def test_parse_returns_sorted_frame():
    frame = StooqFeed.parse(CSV, "aapl.us")
    assert list(frame.columns) == ["Date", "Open", "High", "Low", "Close", "Volume"]
    assert len(frame) == 2


def test_parse_rejects_plain_text_error():
    """Stooq na limit zapytan odpowiada tekstem ze statusem 200, nie bledem HTTP."""
    with pytest.raises(ValueError, match="nie zwrocil danych"):
        StooqFeed.parse("Exceeded the daily hits limit", "aapl.us")


def test_parse_rejects_empty_result():
    with pytest.raises(ValueError, match="pusty zbior"):
        StooqFeed.parse("Date,Open,High,Low,Close,Volume\n", "aapl.us")


def test_download_streams_bars_in_order():
    response = Mock(text=CSV)
    response.raise_for_status = Mock()

    with patch("btengine.data.requests.get", return_value=response) as get:
        feed = StooqFeed.download("aapl.us", start="2024-01-01", end="2024-01-31")

    get.assert_called_once()
    bars = list(feed.stream())
    assert [bar.close for bar in bars] == [104.0, 109.0]
    assert bars[0].timestamp < bars[1].timestamp
    assert feed.symbols == ["aapl.us"]


def test_missing_columns_raise():
    frame = StooqFeed.parse("Date,Open\n2024-01-02,100\n", "aapl.us")
    with pytest.raises(ValueError, match="brakujace kolumny"):
        StooqFeed("aapl.us", frame)
