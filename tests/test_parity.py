"""Packaging must not change what the original script draws or how it runs."""

from __future__ import annotations

import importlib.util
import pathlib
import time

import pytest
from rich.console import Console

from headroom_charts import app, cli

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = str(ROOT / "tests" / "data" / "events.jsonl")
GOLDEN = ROOT / "tests" / "golden" / "frame_100x30.txt"


def render() -> str:
    console = Console(force_terminal=True, color_system="truecolor", width=100, height=30)
    with console.capture() as capture:
        console.print(app.generate_dashboard())
    return capture.get()


@pytest.fixture
def fixture_log(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app, "SAVINGS_FILE", FIXTURE)


def test_frame_is_byte_identical_to_the_original_script(fixture_log: None) -> None:
    assert render() == GOLDEN.read_text()


def test_palette_constants_are_unchanged() -> None:
    assert (app.HARVEST, app.ESPRESSO, app.RUST, app.MAROON, app.IVORY) == (
        "#BB9457",
        "#432818",
        "#99582A",
        "#6F1D1B",
        "#EFE3D2",
    )
    assert (app.MAX_BARS, app.CHART_HEIGHT) == (20, 10)
    assert app.SAVINGS_FILE.endswith("/.headroom/savings_events.jsonl")


def test_console_script_and_root_script_share_one_implementation() -> None:
    spec = importlib.util.spec_from_file_location("root_script", ROOT / "headroom-charts.py")
    assert spec and spec.loader
    root = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(root)
    assert cli.run is app.run
    assert root.run is app.run


def test_live_loop_keeps_the_original_settings(
    fixture_log: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple] = []

    class RecordingLive:
        def __init__(self, renderable, **kwargs):
            calls.append(("open", kwargs))

        def __enter__(self) -> RecordingLive:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def update(self, renderable: object) -> None:
            calls.append(("update",))
            if len([call for call in calls if call[0] == "update"]) >= 2:
                raise KeyboardInterrupt

    monkeypatch.setattr(app, "Live", RecordingLive)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    app.run()

    assert calls[0] == ("open", {"refresh_per_second": 1, "screen": True})
    assert [call[0] for call in calls] == ["open", "update", "update"]


def test_missing_log_renders_the_waiting_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app, "SAVINGS_FILE", "/tmp/definitely-not-here.jsonl")
    assert "Waiting for data..." in render()
