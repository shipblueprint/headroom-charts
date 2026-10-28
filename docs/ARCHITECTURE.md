# headroom-charts — Architecture & Packaging

Status: draft v1 · Last updated: 2026-10-28

## 1. The packaging decision

**PyPI, not npm.** The tool is ~150 lines of Python on top of `rich`
([headroom-charts.py:5-11](https://github.com/shipblueprint/headroom-charts/blob/778c6ab/headroom-charts.py#L5)).
Re-implementing it for npm means rewriting every panel, table and bar in `ink` or
`blessed`, discarding working code, and still not giving an npm user a Python
runtime. The dependency graph is one library deep; PyPI is the native home for it.

Distribution is a spectrum, and the first two are not mutually exclusive:

| Route | Install UX | Cost | Verdict |
|---|---|---|---|
| **PyPI** + `pipx`/`uvx` | `uvx headroom-charts` | near zero | **Do this.** Isolated env, global command, no system-Python damage |
| **Standalone binary** (PyInstaller) per OS/arch | download one file from a GitHub Release | CI matrix, ~30MB artifacts, no auto-update | Do later, only if users genuinely lack Python |
| npm wrapping a Python wheel | `npm i -g` | a build shim that solves nothing | Reject |
| Homebrew tap / AUR | `brew install` | maintain a formula per release | Nice-to-have after PyPI |

A binary is *not* a substitute for the PyPI package — it is a second artifact over
the same source, so the package is built first either way.

`headroom-charts` and `headroom-tui` are unclaimed on PyPI as of 2026-10-28.
`headroom` itself is taken, so the distribution name must keep a suffix.

## 2. Target layout

```
headroom-charts/
├── pyproject.toml
├── README.md
├── LICENSE
├── docs/
│   ├── SPEC.md
│   └── ARCHITECTURE.md
├── src/
│   └── headroom_charts/
│       ├── __init__.py      # __version__ only
│       ├── __main__.py      # python -m headroom_charts
│       ├── cli.py           # argparse, exit codes, the Live loop
│       ├── config.py        # resolved settings dataclass
│       ├── events.py        # Event dataclass + bounded tail reader
│       ├── chart.py         # vertical bar renderer
│       ├── dashboard.py     # Layout: header / kpi / chart / footer
│       └── theme.py         # the five brand hex constants
└── tests/
    ├── test_events.py
    ├── test_chart.py
    └── test_dashboard_snapshot.py
```

Flat module set — no sub-packages, no plugin system. Six modules is the point where
each has one reason to change; beyond that this tool does not need abstraction.

## 3. Module boundaries

**`events.py` — the only module that touches the filesystem.**

```python
@dataclass(frozen=True)
class Event:
    ts: str; model: str; saved: int; cost_usd: float

def read_events(path: Path, limit: int) -> list[Event]: ...
```

Owns: absent-file handling, malformed-line skipping, per-field defaults, and the
bounded read. Everything above it takes `list[Event]` and is pure — which is what
makes `--once` and snapshot tests possible without mocking the disk.

**`chart.py`** takes `(events, height, width)` → `rich.text.Text`. No I/O, no theme
imports beyond `theme.py`.

**`dashboard.py`** composes panels from the pure renderers. Takes `(events, config)`
→ `Layout`.

**`cli.py`** is the impure shell: parse args, loop, sleep, catch `KeyboardInterrupt`.
The `Live` loop currently at
[headroom-charts.py:143-151](https://github.com/shipblueprint/headroom-charts/blob/778c6ab/headroom-charts.py#L143)
moves here and gains a `--once` short-circuit.

## 4. pyproject.toml

`uv_build` backend; no setuptools, no setup.py, no `__init__` version duplication.

```toml
[project]
name = "headroom-charts"
version = "0.1.0"
description = "Live terminal dashboard for headroom token-compression savings"
requires-python = ">=3.10"
dependencies = ["rich>=13.0"]

[project.scripts]
headroom-charts = "headroom_charts.cli:main"

[build-system]
requires = ["uv_build>=0.5"]
build-backend = "uv_build"
```

`[project.scripts]` is what turns the wheel into the `headroom-charts` command, and
is the single most important line in the file.

## 5. Known defects in the baseline, and where they stand

Grounded in [`headroom-charts.py` at `778c6ab`](https://github.com/shipblueprint/headroom-charts/blob/778c6ab/headroom-charts.py), not speculative. Items 1, 2, 4, 5 and 6 are fixed by the packaged CLI; 3 is mitigated.

1. **Unbounded read.** `f.readlines()[-100:]` at
   [headroom-charts.py:29](https://github.com/shipblueprint/headroom-charts/blob/778c6ab/headroom-charts.py#L29)
   loads the whole file to keep the last 100 lines, every second. Cost grows with
   file size and the constant is hardcoded independently of `MAX_BARS`.
2. **Hardcoded path and constants.** `SAVINGS_FILE`, `MAX_BARS`, `CHART_HEIGHT` at
   [headroom-charts.py:20-22](https://github.com/shipblueprint/headroom-charts/blob/778c6ab/headroom-charts.py#L20)
   make the tool unusable outside one specific setup.
3. **Truecolor-only palette.** Every brand colour is a hex value. Measured against
   `TERM=dumb`, `vt100` and `xterm-256color`, `rich` downgrades the hex colours to
   the best supported system on its own, so this is a colour-fidelity question
   rather than a crash; `--no-color` pins it to the 8-colour system.
4. **Fixed-width chart ignores terminal size.** 20 bars × 3 columns + an 8-column
   gutter is ~68 columns minimum and can silently wrap or crop below that.
5. **Small bars round to zero.** `int()` truncation at
   [headroom-charts.py:51](https://github.com/shipblueprint/headroom-charts/blob/778c6ab/headroom-charts.py#L51)
   makes a low-but-nonzero `saved` render as no bar at all.
6. **Ambiguous KPI labels.** "Cost Avoided" is a window sum but reads like a
   lifetime total.

## 6. Release flow

```
push main → CI: ruff check, mypy, pytest, uv build, twine check
tag v*    → CI: uv publish to PyPI + attach sdist/wheel to the GitHub Release
```

PyPI credentials are a trusted-publishing (OIDC) setup, not a long-lived token in
repo secrets, and must be scoped to the `headroom-charts` project only.
Binary builds, if taken on later, are a separate matrix workflow that cannot fail
the Python release.
