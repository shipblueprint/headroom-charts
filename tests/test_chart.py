from __future__ import annotations

from headroom_charts.chart import BAR_WIDTH, GUTTER_WIDTH, render_chart
from headroom_charts.events import Event, synthesize_events


def _event(saved: int, minute: int = 0) -> Event:
    return Event(ts=f"2026-10-28T10:{minute:02d}:00+00:00", model="beam", saved=saved, cost_usd=0.0)


def test_no_events_asks_for_data() -> None:
    assert render_chart([], height=5, width=80).plain.strip() == "Waiting for data..."


def test_plot_emits_requested_rows_plus_the_axis() -> None:
    lines = render_chart(synthesize_events(6), height=7, width=80).plain.splitlines()
    assert len(lines) == 9  # 7 plot rows + baseline + time labels


def test_bars_are_trimmed_to_fit_a_narrow_terminal() -> None:
    chart = render_chart(synthesize_events(40), height=4, width=30)
    widest = max(len(line) for line in chart.plain.splitlines())
    assert widest <= 30
    bars = chart.plain.splitlines()[0][GUTTER_WIDTH:]
    assert len(bars) // BAR_WIDTH == (30 - GUTTER_WIDTH) // BAR_WIDTH


def test_tallest_bar_reaches_the_top_row() -> None:
    chart = render_chart([_event(1000), _event(4000)], height=6, width=80)
    top = chart.plain.splitlines()[0]
    assert "██" in top[GUTTER_WIDTH:]


def test_a_small_nonzero_value_still_draws_one_row() -> None:
    chart = render_chart([_event(1), _event(10_000)], height=10, width=80)
    bottom = chart.plain.splitlines()[-3]
    assert bottom.count("██") == 2  # neither bar rounds away to nothing


def test_zero_saving_events_draw_no_bars() -> None:
    chart = render_chart([_event(0), _event(0)], height=4, width=80)
    assert "██" not in chart.plain


def test_labels_use_the_minute_of_each_event() -> None:
    chart = render_chart([_event(10, minute=42)], height=3, width=80)
    assert "42" in chart.plain.splitlines()[-1]
