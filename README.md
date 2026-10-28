# headroom-charts

A live, single-screen terminal dashboard for headroom context-compression savings.
It tails the proxy's `savings_events.jsonl` and repaints once per second: tokens
saved, cost avoided, a bar chart of recent compressions, and the latest events.

This repository packages [the original script](headroom-charts.py) so it can be
installed as a command. **The rendering is the original code, unchanged** —
`headroom-charts` produces a byte-identical screen to `python headroom-charts.py`.
[tests/test_parity.py](tests/test_parity.py) enforces that against a golden frame
captured from the original script, so a future edit cannot quietly restyle it.

## Install

```bash
uvx headroom-charts             # once published to PyPI
uvx --from git+https://github.com/shipblueprint/headroom-charts headroom-charts
pipx install headroom-charts    # persistent global command
```

Needs Python 3.10+. `rich` arrives with the package; you do not install it yourself.

## Run

```bash
headroom-charts
```

Reads `~/.headroom/savings_events.jsonl`, repaints once per second, takes over the
alternate screen like `htop`. `Ctrl-C` quits and restores your terminal. There are
no options — the original script has none.

Running the script directly still works and is the same code path:

```bash
uv run python headroom-charts.py
```

## What you see

```
╭─ HEADROOM COMPRESSION DASHBOARD ─╮
╭─ Tokens Saved │ Cost Avoided │ Compressions ─╮
╭─ Live Tokens Saved Per Call ─────╯
  ██ ██    ██ ▄▄ ...                (last 20 events, 10 rows tall)
╭─ Latest Events ──────────────────╯
  Time │ Model │ Saved              (last 5)
```

## Data source

`~/.headroom/savings_events.jsonl`, one JSON object per line. The dashboard reads
`ts`, `model`, `saved` and `cost_usd`. Malformed lines are skipped; missing fields
default to `0` / `unknown`. Field reference in [docs/SPEC.md](docs/SPEC.md).

## Development

```bash
uv sync --group dev
uv run pytest              # parity tests
uv run ruff check src tests headroom-charts.py
uv build                   # sdist + wheel into dist/
```

`src/headroom_charts/app.py` is exempt from lint and format rules on purpose: it is
the original source verbatim, and autoformatting it would be a change to behaviour
by the back door. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## License

MIT — see [LICENSE](LICENSE).
