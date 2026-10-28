"""Resolved runtime settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from headroom_charts.events import DEFAULT_EVENTS_PATH

ColorSystem = Literal["standard", "256", "truecolor"]


@dataclass(frozen=True)
class Settings:
    file: Path = DEFAULT_EVENTS_PATH
    bars: int = 20
    chart_height: int = 10
    interval: float = 1.0
    table_rows: int = 5
    demo: bool = False
    color_system: ColorSystem | None = None
