"""Vertical bar chart drawn as text."""

from __future__ import annotations

from rich.text import Text

from headroom_charts.events import Event
from headroom_charts.theme import HARVEST, IVORY, RUST

BAR_WIDTH = 3
GUTTER_WIDTH = 9
LABEL_DENSITY = 15


def render_chart(events: list[Event], *, height: int, width: int) -> Text:
    """Plot `saved` per event, oldest first, scaled so the tallest bar fills `height`.

    Events are trimmed from the left to fit `width`, so a narrow terminal shows
    fewer bars instead of wrapping the plot.
    """
    if not events or height <= 0:
        return Text("Waiting for data...", style=IVORY)

    fits = max(1, (width - GUTTER_WIDTH) // BAR_WIDTH)
    shown = events[-fits:]
    peak = max(event.saved for event in shown) or 1

    chart = Text()
    for row in range(height, 0, -1):
        chart.append(f"{round((row / height) * peak):>{GUTTER_WIDTH - 3}} ┤ ", style=RUST)
        for event in shown:
            if _bar_height(event.saved, peak, height) >= row:
                chart.append("██", style=HARVEST)
            else:
                chart.append("  ")
            chart.append(" ")
        chart.append("\n")

    chart.append(" " * (GUTTER_WIDTH - 1) + "└" + "───" * len(shown), style=RUST)
    chart.append("\n" + " " * GUTTER_WIDTH, style=RUST)
    _append_time_labels(chart, shown)
    return chart


def _bar_height(saved: int, peak: int, height: int) -> int:
    if saved <= 0:
        return 0
    return max(1, round((saved / peak) * height))


def _append_time_labels(chart: Text, shown: list[Event]) -> None:
    thin = len(shown) > LABEL_DENSITY
    for index, event in enumerate(shown):
        minute = event.ts[14:16]
        if not minute.isdigit() or (thin and index % 3):
            minute = ""
        chart.append(f"{minute:>{BAR_WIDTH}}", style=IVORY)
