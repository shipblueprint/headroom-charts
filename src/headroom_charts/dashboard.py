"""The four-zone dashboard layout."""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.console import RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from headroom_charts.chart import render_chart
from headroom_charts.config import Settings
from headroom_charts.events import Event
from headroom_charts.theme import ESPRESSO, HARVEST, IVORY, MAROON, RUST

PANEL_CHROME = 4
MIN_CHART_WIDTH = 24
HEADER_ROWS = 3
KPI_ROWS = 5
PANEL_BORDER_ROWS = 2
AXIS_ROWS = 2
TABLE_OVERHEAD_ROWS = 3
MIN_TABLE_ROWS = 1
MIN_PLOT_ROWS = 2
MIN_ZONE_ROWS = PANEL_BORDER_ROWS + AXIS_ROWS + MIN_PLOT_ROWS


def build_dashboard(events: list[Event], settings: Settings, width: int, height: int) -> Layout:
    table_rows, plot_rows = _plan(settings, height)
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=HEADER_ROWS),
        Layout(name="kpi", size=KPI_ROWS),
        Layout(name="chart", ratio=1),
        Layout(name="footer", size=_footer_rows(table_rows)),
    )
    layout["header"].update(_header())
    layout["kpi"].update(_kpi(events))
    layout["chart"].update(_chart(events, plot_rows, width))
    layout["footer"].update(_footer(events, table_rows))
    return layout


def _plan(settings: Settings, height: int) -> tuple[int, int]:
    """Fit the four zones into `height` rows, shrinking the table before the plot."""
    table_rows = settings.table_rows
    while table_rows > MIN_TABLE_ROWS and height - _fixed_rows(table_rows) < MIN_ZONE_ROWS:
        table_rows -= 1
    zone = height - _fixed_rows(table_rows)
    plot = min(settings.chart_height, zone - PANEL_BORDER_ROWS - AXIS_ROWS)
    return table_rows, max(MIN_PLOT_ROWS, plot)


def _footer_rows(table_rows: int) -> int:
    return table_rows + TABLE_OVERHEAD_ROWS + PANEL_BORDER_ROWS


def _fixed_rows(table_rows: int) -> int:
    return HEADER_ROWS + KPI_ROWS + _footer_rows(table_rows)


def _panel(renderable: RenderableType, title: str | None = None, border: str = RUST) -> Panel:
    return Panel(
        renderable,
        title=title,
        box=box.ROUNDED,
        border_style=border,
        style=ESPRESSO,
    )


def _header() -> Panel:
    title = Text(" HEADROOM COMPRESSION DASHBOARD", style=f"bold {IVORY} on {MAROON}")
    return _panel(Align.center(title, vertical="middle"))


def _kpi(events: list[Event]) -> Panel:
    window = f"last {len(events)}"
    grid = Table.grid(expand=True)
    for _ in range(3):
        grid.add_column(justify="center")
    grid.add_row(
        f"[bold {HARVEST}]{sum(event.saved for event in events):,}[/]\n"
        f"[dim {IVORY}]Tokens Saved ({window})[/]",
        f"[bold {HARVEST}]${sum(event.cost_usd for event in events):.4f}[/]\n"
        f"[dim {IVORY}]Cost Avoided ({window})[/]",
        f"[bold {HARVEST}]{len(events)}[/]\n[dim {IVORY}]Compressions[/]",
    )
    return _panel(grid)


def _chart(events: list[Event], plot_rows: int, width: int) -> Panel:
    chart = render_chart(
        events,
        height=plot_rows,
        width=max(MIN_CHART_WIDTH, width - PANEL_CHROME),
    )
    return _panel(
        Align.center(chart, vertical="middle"),
        title=f"[bold {IVORY}]Live Tokens Saved Per Call[/]",
        border=HARVEST,
    )


def _footer(events: list[Event], table_rows: int) -> Panel:
    table = Table(expand=True, box=box.SIMPLE, style=ESPRESSO)
    table.add_column("Time", style=RUST)
    table.add_column("Model", style=MAROON)
    table.add_column("Saved", justify="right", style=HARVEST)
    for event in reversed(events[-table_rows:]):
        table.add_row(
            event.ts[:19].replace("T", " "),
            event.model,
            f"{event.saved:,}",
        )
    return _panel(table, title=f"[bold {IVORY}]Latest Events[/]")
