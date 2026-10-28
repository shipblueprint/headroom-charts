```markdown
# headroom-charts

Live terminal dashboard for Headroom context-compression savings.

Tails `~/.headroom/savings_events.jsonl` and redraws once a second: tokens saved, cost avoided, a bar chart of recent compressions, and the latest events.

## Install

```bash
uvx --from git+https://github.com/shipblueprint/headroom-charts headroom-charts
# or, once on PyPI:
uvx headroom-charts
```

Requires Python 3.10+.

## Run

```bash
headroom-charts
```

Takes over the alternate screen (like `htop`). Ctrl-C restores your terminal.

## What you see

```
╭─ HEADROOM COMPRESSION DASHBOARD ─╮
╭─ Tokens Saved │ Cost Avoided │ Compressions ─╮
╭─ Live Tokens Saved Per Call ─────╯
  ██ ██    ██ ▄▄ ...                (last 20 events)
╭─ Latest Events ──────────────────╯
  Time │ Model │ Saved              (last 5)
```

## Data

Reads `ts`, `model`, `saved`, and `cost_usd` from each line of  
`~/.headroom/savings_events.jsonl`. Bad lines are skipped.

## License

MIT
```