from datetime import datetime, timedelta

from btengine.events import Bar, Side
from btengine.strategy import BuyAndHold, MeanReversion, SMACrossover


def bars(closes: list[float]) -> list[Bar]:
    start = datetime(2024, 1, 1)
    return [
        Bar(start + timedelta(days=i), "AAA", c, c, c, c, 1_000)
        for i, c in enumerate(closes)
    ]


def test_sma_crossover_buys_on_uptrend():
    strategy = SMACrossover(fast=2, slow=3, size=1)
    orders = [o for bar in bars([10, 11, 12, 13, 14]) for o in strategy.handle(bar)]
    assert any(o.side is Side.BUY for o in orders)


def test_sma_crossover_waits_for_enough_history():
    strategy = SMACrossover(fast=2, slow=5, size=1)
    orders = [o for bar in bars([10, 11, 12]) for o in strategy.handle(bar)]
    assert orders == []


def test_mean_reversion_buys_after_sharp_drop():
    strategy = MeanReversion(window=5, entry_z=-1.0, exit_z=0.0, size=1)
    series = [100, 101, 100, 99, 100, 90]
    orders = [o for bar in bars(series) for o in strategy.handle(bar)]
    assert any(o.side is Side.BUY for o in orders)


def test_mean_reversion_flat_series_produces_nothing():
    strategy = MeanReversion(window=3, size=1)
    orders = [o for bar in bars([100, 100, 100, 100]) for o in strategy.handle(bar)]
    assert orders == []


def test_buy_and_hold_buys_once_and_holds():
    strategy = BuyAndHold(size=1)
    orders = [o for bar in bars([10, 11, 12, 13]) for o in strategy.handle(bar)]
    assert len(orders) == 1
    assert orders[0].side is Side.BUY
