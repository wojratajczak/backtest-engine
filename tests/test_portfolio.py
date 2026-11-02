from datetime import datetime

from btengine.events import Fill, Side
from btengine.portfolio import Portfolio


def test_buy_reduces_cash_and_adds_position():
    p = Portfolio(initial_cash=10_000)
    p.on_fill(Fill(datetime(2024, 1, 2), "AAA", Side.BUY, 10, 100.0, 1.0))
    assert p.positions["AAA"] == 10
    assert p.cash == 10_000 - 10 * 100.0 - 1.0


def test_mark_to_market_tracks_equity():
    p = Portfolio(initial_cash=1_000)
    p.on_fill(Fill(datetime(2024, 1, 2), "AAA", Side.BUY, 5, 100.0, 0.0))
    equity = p.mark_to_market(datetime(2024, 1, 3), {"AAA": 110.0})
    assert equity == 1_000 - 500 + 550
    assert len(p.equity_curve) == 1
