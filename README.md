# headroom-charts

A live, single-screen terminal dashboard for
[headroom](https://github.com/shipblueprint) context-compression savings. It tails
the proxy's `savings_events.jsonl` and repaints once per second: tokens saved, cost
avoided, a bar chart of recent compressions, and the latest events.

It is a viewer only. It never writes to the events file.

> **Status:** the working reference implementation is
> [`headroom-charts.py`](headroom-charts.py) — a single script, no package yet.
> Restructuring into an installable CLI is tracked in the
> [issue backlog](https://github.com/shipblueprint/headroom-charts/issues). Behaviour
> is specified in [docs/SPEC.md](docs/SPEC.md); packaging decisions in
> [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run it today

Requires Python 3.10+ and [`rich`](https://pypi.org/project/rich/).

```bash
pip install rich
python headroom-charts.py
```

`Ctrl-C` exits and restores your terminal.

## Planned

```bash
uvx headroom-charts            # no install, isolated env
pipx install headroom-charts   # persistent global command
headroom-charts --bars 30 --interval 0.5 --demo
```

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

## License

MIT — see [LICENSE](LICENSE).
