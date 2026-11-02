"""Najwazniejszy test w repo: zlecenie nie moze wypelnic sie na swoim barze."""
from datetime import datetime, timedelta

from btengine.broker import SimpleBroker
from btengine.events import Bar, Order, Side


def test_fill_happens_on_next_bar_open():
    t0 = datetime(2024, 1, 2)
    signal_bar = Bar(t0, "AAA", 100, 105, 99, 104, 1_000)
    next_bar = Bar(t0 + timedelta(days=1), "AAA", 106, 110, 105, 109, 1_000)

    order = Order(signal_bar.timestamp, "AAA", Side.BUY, 10)
    fill = SimpleBroker(slippage_bps=0, commission_bps=0).execute(order, next_bar)

    assert fill.price == next_bar.open
    assert fill.price != signal_bar.close
