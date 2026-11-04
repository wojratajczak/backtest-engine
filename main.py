"""CLI: pobiera notowania ze stooq.com, uruchamia strategie, zapisuje wykres i metryki.

Przyklad:
    python main.py --symbol aapl.us --start 2015-01-01 --fast 20 --slow 50
"""
import argparse
from pathlib import Path

from btengine import Backtester, Portfolio
from btengine.broker import SimpleBroker
from btengine.data import make_feed
from btengine.metrics import max_drawdown, sharpe
from btengine.plotting import plot_equity
from btengine.strategy import BuyAndHold, MeanReversion, SMACrossover


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a backtest on daily market data.")
    parser.add_argument("--source", default="yahoo", choices=["yahoo", "stooq"])
    parser.add_argument(
        "--symbol", default="AAPL", help="yahoo: AAPL, PKN.WA | stooq: aapl.us, pkn"
    )
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--cash", type=float, default=100_000.0)
    parser.add_argument("--size", type=float, default=100.0)
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=50)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--slippage-bps", type=float, default=1.0)
    parser.add_argument("--commission-bps", type=float, default=0.5)
    parser.add_argument("--plot", default="docs/equity_curve.png")
    parser.add_argument("--cache-dir", default="data")
    return parser.parse_args(argv)


def build_strategies(args: argparse.Namespace) -> dict[str, object]:
    return {
        "Buy & hold": BuyAndHold(size=args.size),
        "SMA crossover": SMACrossover(fast=args.fast, slow=args.slow, size=args.size),
        "Mean reversion": MeanReversion(window=args.window, size=args.size),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    feed = make_feed(
        args.source,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        cache_dir=args.cache_dir,
    )
    print(f"{args.symbol} via {args.source}: {len(feed)} bars\n")

    curves: dict[str, list] = {}
    rows: list[tuple[str, float, float, float, float]] = []

    for name, strategy in build_strategies(args).items():
        broker = SimpleBroker(args.slippage_bps, args.commission_bps)
        result = Backtester(feed, strategy, Portfolio(args.cash), broker).run()
        curves[name] = result.equity_curve
        final = result.equity_curve[-1][1]
        rows.append(
            (
                name,
                final,
                final / args.cash - 1,
                sharpe(result.equity_curve),
                max_drawdown(result.equity_curve),
            )
        )

    header = f"{'strategy':<16}{'final':>14}{'return':>10}{'sharpe':>9}{'max DD':>9}"
    print(header)
    print("-" * len(header))
    for name, final, ret, sharpe_ratio, drawdown in rows:
        print(f"{name:<16}{final:>14,.0f}{ret:>9.1%}{sharpe_ratio:>9.2f}{drawdown:>9.1%}")

    window = f"{args.start} to {args.end or 'today'}"
    out = plot_equity(curves, Path(args.plot), title=f"{args.symbol} — {window}")
    print(f"\nchart saved to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
