"""Petla zdarzen. Zlecenie z bara t wypelnia sie dopiero na barze t+1."""
from .broker import Broker, SimpleBroker
from .data import DataFeed
from .events import Order
from .portfolio import Portfolio
from .strategy import Strategy


class Backtester:
    def __init__(
        self,
        feed: DataFeed,
        strategy: Strategy,
        portfolio: Portfolio | None = None,
        broker: Broker | None = None,
    ) -> None:
        self.feed = feed
        self.strategy = strategy
        self.portfolio = portfolio or Portfolio()
        self.broker = broker or SimpleBroker()

    def run(self) -> Portfolio:
        pending: list[Order] = []
        for bar in self.feed.stream():
            for order in pending:
                self.portfolio.on_fill(self.broker.execute(order, bar))
            pending = self.strategy.handle(bar)
            self.portfolio.mark_to_market(bar.timestamp, {bar.symbol: bar.close})
        return self.portfolio
