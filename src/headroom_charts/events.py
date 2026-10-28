"""Reading the headroom savings event log."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EVENTS_PATH = Path("~/.headroom/savings_events.jsonl").expanduser()

READ_BYTES = 256 * 1024
APPROX_LINE_BYTES = 4096


@dataclass(frozen=True)
class Event:
    ts: str
    model: str
    saved: int
    cost_usd: float

    @classmethod
    def parse(cls, raw: str) -> Event | None:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(obj, dict):
            return None
        return cls(
            ts=str(obj.get("ts", "")),
            model=str(obj.get("model", "unknown")),
            saved=_as_int(obj.get("saved")),
            cost_usd=_as_float(obj.get("cost_usd")),
        )


def _as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(value)


def _as_float(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def read_events(path: Path = DEFAULT_EVENTS_PATH, limit: int = 20) -> list[Event]:
    """Return the most recent `limit` events, oldest first.

    A missing log has not started producing yet, so it yields an empty dashboard.
    Any other read failure is raised for the caller to report.
    """
    try:
        lines = _tail_lines(path, limit)
    except FileNotFoundError:
        return []
    events = [event for event in map(Event.parse, lines) if event is not None]
    return events[-limit:] if limit > 0 else events


def _tail_lines(path: Path, count: int) -> list[str]:
    size = path.stat().st_size
    if size == 0 or count <= 0:
        return []
    window = min(size, max(READ_BYTES, count * APPROX_LINE_BYTES))
    with path.open("rb") as handle:
        handle.seek(size - window)
        data = handle.read()
    lines = data.decode("utf-8", errors="replace").splitlines()
    if window < size and lines:
        lines.pop(0)
    return lines[-count:]


def synthesize_events(count: int, seed: int = 7) -> list[Event]:
    """Deterministic demo events for `--demo` and screenshot tests."""
    models = ("beam", "stepfun-ai/step-5-preview", "claude-haiku")
    state = seed
    events: list[Event] = []
    for i in range(count):
        state = (state * 1103515245 + 12345) % (2**31)
        saved = 1200 + state % 9000
        events.append(
            Event(
                ts=f"2026-10-28T{i // 60 % 24:02d}:{i % 60:02d}:00+00:00",
                model=models[i % len(models)],
                saved=saved,
                cost_usd=round(saved * 2.6e-6, 6),
            )
        )
    return events
