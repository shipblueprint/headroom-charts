# headroom-charts

A live, single-screen terminal dashboard for
[headroom](https://github.com/shipblueprint) context-compression savings. It tails
the proxy's `savings_events.jsonl` and repaints once per second: tokens saved, cost
avoided, a bar chart of recent compressions, and the latest events.

It is a viewer only. It never writes to the events file.

> **Status:** packaged and installable. `v0.1.0` is not on PyPI yet, so install
> from the repo for now. Remaining work is tracked in the
> [issue backlog](https://github.com/shipblueprint/headroom-charts/issues); behaviour
> is specified in [docs/SPEC.md](docs/SPEC.md) and packaging decisions in
> [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Install

```bash
uvx --from git+https://github.com/shipblueprint/headroom-charts headroom-charts
# or, once published to PyPI:
uvx headroom-charts
pipx install headroom-charts
```

Needs Python 3.10+. `rich` comes with the package — you do not install it yourself.

## Run

```bash
headroom-charts                     # tail ~/.headroom/savings_events.jsonl
headroom-charts --bars 40 --interval 0.5
headroom-charts --demo              # synthetic data, no headroom required
headroom-charts --once              # single frame, for screenshots and CI
```

`Ctrl-C` exits and restores your terminal. `--help` lists every flag.

## What you see

```
╭─ HEADROOM COMPRESSION DASHBOARD ─╮
╭─ KPI ─────────────────────────────╯
  Tokens Saved (Recent) │ Cost Avoided │ Compressions
╭─ Live Tokens Saved Per Call ──────╯
  ██ ██    ██ ▄▄ ...               (last 20 events)
╭─ Latest Events ───────────────────╯
  Time │ Model │ Saved              (last 5)
```

## Data source

`~/.headroom/savings_events.jsonl`, one JSON object per line. The dashboard reads
`ts`, `model`, `saved` and `cost_usd`; malformed or missing fields are skipped or
defaulted rather than raising. Full field reference in
[docs/SPEC.md §3](docs/SPEC.md).

## Development

```bash
uv sync --group dev
uv run pytest              # 32 tests
uv run ruff check src tests
uv run mypy src
uv build                   # sdist + wheel into dist/
```

The layout adapts to the terminal: `--events` rows are traded away before the plot
is clipped, so an 80×24 window still shows the axis and every table row.

## License

MIT — see [LICENSE](LICENSE).
