"""Command line entry point."""

from __future__ import annotations

import argparse
import pathlib
import sys
import time

from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from headroom_charts import __version__
from headroom_charts.config import Settings
from headroom_charts.dashboard import build_dashboard
from headroom_charts.events import DEFAULT_EVENTS_PATH, Event, read_events, synthesize_events

EXIT_INTERRUPTED = 130
EXIT_UNREADABLE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="headroom-charts",
        description="Live terminal dashboard for headroom token-compression savings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--file",
        type=pathlib.Path,
        default=DEFAULT_EVENTS_PATH,
        help="savings events JSONL to read",
    )
    parser.add_argument("--bars", type=int, default=20, help="events plotted in the chart")
    parser.add_argument("--height", type=int, default=10, help="chart rows")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between repaints")
    parser.add_argument(
        "--events", dest="table_rows", type=int, default=5, help="rows in the events table"
    )
    parser.add_argument("--once", action="store_true", help="render a single frame and exit")
    parser.add_argument(
        "--demo", action="store_true", help="plot synthesised events instead of reading --file"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="pin the palette to the 8-colour system instead of the terminal's best match",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _frame(settings: Settings, console: Console) -> Layout:
    events: list[Event] = (
        synthesize_events(settings.bars)
        if settings.demo
        else read_events(settings.file, settings.bars)
    )
    size = console.size
    return build_dashboard(events, settings, size.width, size.height)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.bars < 1 or args.height < 1 or args.table_rows < 1 or args.interval <= 0:
        build_parser().error("--bars, --height, --events and --interval must be positive")

    settings = Settings(
        file=args.file,
        bars=args.bars,
        chart_height=args.height,
        interval=args.interval,
        table_rows=args.table_rows,
        demo=args.demo,
        color_system="standard" if args.no_color else None,
    )
    console = Console(color_system=settings.color_system)

    try:
        if args.once:
            console.print(_frame(settings, console))
            return 0
        with Live(
            _frame(settings, console),
            console=console,
            screen=True,
            refresh_per_second=max(1.0, 1.0 / settings.interval),
        ) as live:
            while True:
                time.sleep(settings.interval)
                live.update(_frame(settings, console))
    except KeyboardInterrupt:
        return EXIT_INTERRUPTED
    except OSError as exc:
        print(f"headroom-charts: cannot read {settings.file}: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
