from __future__ import annotations

import json
from pathlib import Path

import pytest

from headroom_charts.cli import main


@pytest.fixture(autouse=True)
def _fixed_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("LINES", "30")


def test_once_is_deterministic_for_a_fixed_input(tmp_path: Path, capsys) -> None:
    log = tmp_path / "e.jsonl"
    rows = [
        {"ts": f"2026-10-28T10:0{i}:00+00:00", "model": "beam", "saved": i * 100, "cost_usd": 0.0}
        for i in range(3)
    ]
    log.write_text("".join(json.dumps(r) + "\n" for r in rows))

    main(["--once", "--file", str(log)])
    first = capsys.readouterr().out
    main(["--once", "--file", str(log)])
    assert capsys.readouterr().out == first


def test_dashboard_names_every_zone(tmp_path: Path, capsys) -> None:
    main(["--once", "--demo"])
    out = capsys.readouterr().out
    for zone in (
        "HEADROOM COMPRESSION DASHBOARD",
        "Tokens Saved",
        "Live Tokens Saved Per Call",
        "Latest Events",
    ):
        assert zone in out


def test_unreadable_log_exits_two(tmp_path: Path, capsys) -> None:
    assert main(["--once", "--file", str(tmp_path)]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_unknown_flag_exits_two() -> None:
    with pytest.raises(SystemExit) as stop:
        main(["--nope"])
    assert stop.value.code == 2


@pytest.mark.parametrize("argv", [["--bars", "0"], ["--height", "0"], ["--interval", "0"]])
def test_nonpositive_sizes_exit_two(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        main(["--once", *argv])
    assert stop.value.code == 2


def test_no_color_still_renders(capsys) -> None:
    assert main(["--once", "--demo", "--no-color"]) == 0
    assert "Live Tokens Saved Per Call" in capsys.readouterr().out


def test_version_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as stop:
        main(["--version"])
    assert stop.value.code == 0
    assert "headroom-charts 0.1.0" in capsys.readouterr().out
