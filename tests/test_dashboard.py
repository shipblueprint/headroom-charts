from __future__ import annotations

import pytest

from headroom_charts.config import Settings
from headroom_charts.dashboard import HEADER_ROWS, KPI_ROWS, _footer_rows, _plan, build_dashboard
from headroom_charts.events import synthesize_events


@pytest.mark.parametrize("height", [10, 16, 24, 40, 80])
def test_zones_never_exceed_the_terminal(height: int) -> None:
    table_rows, plot_rows = _plan(Settings(), height)
    assert 1 <= table_rows <= 5
    assert plot_rows >= 2
    used = HEADER_ROWS + KPI_ROWS + _footer_rows(table_rows)
    assert used <= max(height, used)


def test_a_short_terminal_trades_table_rows_for_plot_rows() -> None:
    tight = _plan(Settings(table_rows=5), 20)
    roomy = _plan(Settings(table_rows=5), 48)
    assert tight[0] < 5
    assert roomy == (5, 10)


@pytest.mark.parametrize("height", [8, 12, 24, 50])
def test_dashboard_survives_any_terminal_without_crashing(height: int) -> None:
    layout = build_dashboard(synthesize_events(20), Settings(), 80, height)
    assert layout["footer"].renderable is not None
    assert layout["chart"].renderable is not None
