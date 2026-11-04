"""Testy parsowania odpowiedzi Yahoo Finance - bez ruchu sieciowego."""
import json
from unittest.mock import Mock, patch

import pytest

from btengine.data import YahooFeed

PAYLOAD = json.dumps(
    {
        "chart": {
            "error": None,
            "result": [
                {
                    "meta": {"symbol": "AAPL", "currency": "USD"},
                    "timestamp": [1704153600, 1704240000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0, 106.0],
                                "high": [105.0, 110.0],
                                "low": [99.0, 105.0],
                                "close": [104.0, 109.0],
                                "volume": [1000, 1200],
                            }
                        ]
                    },
                }
            ],
        }
    }
)


def test_parse_builds_ohlcv_frame():
    frame = YahooFeed.parse(PAYLOAD, "AAPL")
    assert list(frame.columns) == ["Date", "Open", "High", "Low", "Close", "Volume"]
    assert len(frame) == 2


def test_parse_drops_rows_with_missing_prices():
    payload = json.loads(PAYLOAD)
    payload["chart"]["result"][0]["indicators"]["quote"][0]["close"] = [104.0, None]
    frame = YahooFeed.parse(json.dumps(payload), "AAPL")
    assert len(frame) == 1


def test_parse_rejects_api_error():
    payload = json.dumps({"chart": {"error": {"code": "Not Found"}, "result": None}})
    with pytest.raises(ValueError, match="zglasza blad"):
        YahooFeed.parse(payload, "NOPE")


def test_parse_rejects_non_json():
    with pytest.raises(ValueError, match="nieoczekiwana odpowiedz"):
        YahooFeed.parse("<html>Access denied</html>", "AAPL")


def test_download_streams_bars_in_order():
    response = Mock(text=PAYLOAD)
    response.raise_for_status = Mock()

    with patch("btengine.data.requests.get", return_value=response) as get:
        feed = YahooFeed.download("AAPL", start="2024-01-01", end="2024-01-31")

    get.assert_called_once()
    bars = list(feed.stream())
    assert [bar.close for bar in bars] == [104.0, 109.0]
    assert bars[0].timestamp < bars[1].timestamp
