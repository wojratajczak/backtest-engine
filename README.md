# backtest-engine

Event-driven backtesting engine for daily equity strategies. Written to be read:
each component has one responsibility, and the event loop makes look-ahead bias
structurally impossible rather than merely discouraged.

![CI](https://github.com/wojratajczak/backtest-engine/actions/workflows/ci.yml/badge.svg)

## Why this exists

Most backtests quietly fill orders at the very price that generated the signal,
which inflates every result that follows. Here a signal produced on bar *t* can
only be filled at the open of bar *t+1*, and `tests/test_no_lookahead.py` fails
if that ever stops being true.

## Design

| Component | Responsibility |
|---|---|
| `DataFeed` | Yields bars chronologically. `CSVFeed` today, more via `make_feed` |
| `Strategy` | Sees a closed bar, returns orders |
| `Broker` | Turns orders into fills, applying slippage and commission |
| `Portfolio` | Positions, cash, equity curve |
| `Backtester` | The event loop connecting them |

Patterns used deliberately: **Strategy** (trading logic), **Template Method**
(`Strategy.handle` wraps `on_bar`), **Factory** (`make_feed`), **Dependency
Injection** (broker and portfolio are passed in, not constructed inside the engine).

## Install

```bash
git clone https://github.com/wojratajczak/backtest-engine.git
cd backtest-engine
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Usage

```python
from pathlib import Path

from btengine import Backtester, Portfolio
from btengine.data import CSVFeed
from btengine.metrics import max_drawdown, sharpe
from btengine.strategy import SMACrossover

feed = CSVFeed(Path("data/AAPL.csv"), symbol="AAPL")
result = Backtester(feed, SMACrossover(fast=20, slow=50), Portfolio(100_000)).run()

print(f"Sharpe: {sharpe(result.equity_curve):.2f}")
print(f"Max drawdown: {max_drawdown(result.equity_curve):.1%}")
```

## Results

*(equity curve + tabela metryk dla 2-3 strategii — do uzupelnienia)*

## Limitations

- Daily bars only: no intraday, no partial fills, no market impact beyond fixed slippage
- Single-asset portfolios in the current version
- Slippage is a flat spread in basis points, not a function of traded volume

## Roadmap

- [ ] Multi-asset portfolios and position sizing
- [ ] Walk-forward parameter selection
- [ ] Vectorised fast path for parameter sweeps
