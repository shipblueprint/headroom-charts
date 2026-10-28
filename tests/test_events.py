from __future__ import annotations

import json
from pathlib import Path

from headroom_charts.events import read_events, synthesize_events


def _write(path: Path, events: list[dict]) -> Path:
    path.write_text("".join(json.dumps(e) + "\n" for e in events))
    return path


def test_missing_file_renders_empty(tmp_path: Path) -> None:
    assert read_events(tmp_path / "nope.jsonl") == []


def test_empty_file_renders_empty(tmp_path: Path) -> None:
    assert read_events(_write(tmp_path / "e.jsonl", [])) == []


def test_malformed_and_partial_lines_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "e.jsonl"
    good = {"ts": "2026-10-28T10:00:00+00:00", "model": "beam", "saved": 10, "cost_usd": 0.1}
    path.write_text(
        json.dumps(good)
        + "\n"
        + "{not json at all}\n"
        + "[1, 2, 3]\n"
        + '{"ts": "2026-10-28T10:01'  # truncated final append
    )
    events = read_events(path)
    assert [e.saved for e in events] == [10]


def test_absent_fields_fall_back_to_defaults(tmp_path: Path) -> None:
    events = read_events(_write(tmp_path / "e.jsonl", [{}]))
    assert events[0].model == "unknown"
    assert events[0].saved == 0
    assert events[0].cost_usd == 0.0


def test_returns_the_newest_limit_events_oldest_first(tmp_path: Path) -> None:
    rows = [{"saved": i, "ts": f"2026-10-28T00:00:{i:02d}+00:00"} for i in range(50)]
    events = read_events(_write(tmp_path / "e.jsonl", rows), limit=5)
    assert [e.saved for e in events] == [45, 46, 47, 48, 49]


def test_large_log_returns_only_the_window(tmp_path: Path) -> None:
    rows = [{"saved": i, "ts": f"2026-10-28T00:00:{i % 60:02d}+00:00"} for i in range(20_000)]
    events = read_events(_write(tmp_path / "e.jsonl", rows), limit=3)
    assert [e.saved for e in events] == [19997, 19998, 19999]


def test_synthesized_events_are_deterministic() -> None:
    assert synthesize_events(10) == synthesize_events(10)
    assert len(synthesize_events(10)) == 10
