# headroom-charts — Product Specification

Status: draft v1 · Owner: shipblueprint · Last updated: 2026-10-28

## 1. Problem

A context-compression proxy writes token-savings events to a JSONL file while it
runs. Today the only way to watch them is `tail -f` and read raw JSON. There is
no way to answer, at a glance and without leaving the terminal:

- How many tokens has compression saved me recently?
- What did that avoid in dollars?
- Is the saving rate per call trending up or down?
- Which model produced the last few events?

`headroom-charts` is a single-screen live dashboard over that file. It is a
*viewer only*.

## 2. Audience

Developers running the headroom compression proxy on their own machine. They
have a terminal, care about token spend, and want the dashboard to start with one
command.

## 3. Data contract

Source of truth: `~/.headroom/savings_events.jsonl`

Append-only JSON Lines, one event per line, schema version `v: 2`. A real line:

```json
{"v":2,"ts":"2026-10-27T21:06:59.766090+00:00","before":65046,"after":62184,
 "saved":2862,"cost_usd":0.008586,"model":"beam","client":"opencode",
 "source":"proxy","pid":27451,"saved_tool_schema":0}
```

| Field | Type | Consumed by the dashboard | Notes |
|---|---|---|---|
| `v` | int | no | schema version; currently always `2` |
| `ts` | string | **yes** | ISO-8601 with offset; `HH:MM` slice assumes `YYYY-MM-DDTHH:MM:SS` |
| `before` | int | no | prompt tokens pre-compression |
| `after` | int | no | prompt tokens post-compression |
| `saved` | int | **yes** | bar height + token KPI |
| `cost_usd` | float | **yes** | cost KPI |
| `model` | string | **yes** | events-table column |
| `client` | string | no | e.g. `opencode`; candidate for a future column |
| `source` | string | no | e.g. `proxy` |
| `pid` | int | no | writer process |
| `saved_tool_schema` | int | no | tokens saved on tool schemas specifically |

Robustness rules the viewer must honour:

- The file may not exist yet. Empty dashboard, not a crash.
- Lines may be malformed or half-written (a reader can catch a partial append).
  Skip them silently and continue.
- Any field may be absent. Fall back to a permissive default (`0`, `"unknown"`).

## 4. Interface

Fixed 4-zone vertical layout, drawn to the alternate screen (`screen=True`) so the
user's scrollback is untouched, and repainted once per second.

```
╭─ HEADROOM COMPRESSION DASHBOARD ─╮   header   3 rows
╭─ KPI row ────────────────────────╮   kpi      5 rows
  Tokens Saved (Recent) | Cost Avoided | Compressions
╭─ Live Tokens Saved Per Call ─────╮   chart    fills remaining height
  vertical bars, y-axis gutter, x-axis time labels
╭─ Latest Events ──────────────────╯   footer   8 rows
  Time | Model | Saved      (last 5, newest first)
```

### 4.1 Chart

- One vertical bar per event in the display window, oldest on the left.
- Default window: last **20** events (`MAX_BARS`).
- Default plot height: **10** rows (`CHART_HEIGHT`), scaled to the largest `saved`
  in the window, so the tallest bar always fills the panel.
- Y-axis gutter prints the value at each row; x-axis prints minute labels, thinning
  to every third bar above 15 events.

### 4.2 Semantics of the numbers — explicit

The dashboard renders a *window*, not a lifetime total, and the two must not be
confused:

- "Tokens Saved (Recent)" = sum of `saved` across the display window only.
- "Cost Avoided" = sum of `cost_usd` across the same window. It currently carries
  no "recent" qualifier in its label; **v1 must make the window explicit on every
  figure.**
- "Compressions" = event count in the window.

### 4.3 Palette

Brand colours are the 24-bit hex values from the original HTML mockup. They render
as `Text`/`Panel` styles on `rich`, which requires truecolor.

| Name | Hex | Role |
|---|---|---|
| `HARVEST` | `#BB9457` | bars, KPI numerals, chart border |
| `ESPRESSO` | `#432818` | panel background |
| `RUST` | `#99582A` | borders, axes, table columns |
| `MAROON` | `#6F1D1B` | header background, model column |
| `IVORY` | `#EFE3D2` | text and labels |

## 5. CLI surface (target state)

The reference implementation hardcodes everything. The packaged tool takes:

```
headroom-charts [OPTIONS]

  --file PATH       events JSONL to read   [default ~/.headroom/savings_events.jsonl]
  --bars N          events in the chart window   [default 20]
  --height N        chart rows   [default 10]
  --interval SECS   repaint period   [default 1.0]
  --events N        rows in the footer table   [default 5]
  --once            render one frame and exit (no live loop; for CI/screenshots)
  --demo            synthesise events instead of reading a file
  --no-color        fall back to ANSI 16-colour when truecolor is unavailable
  --version / --help
```

Exit codes: `0` clean (including `--once`), `130` on `Ctrl-C`, `2` for a bad flag
or unreadable file.

## 6. Non-goals

- Not writing, rotating, or backfilling the events file.
- Not a proxy, not a cost estimator — it displays `cost_usd` as given.
- No network access, no telemetry, no config file in v1.
- No mouse interaction, no panes, no historical zoom.
- Not a web dashboard; the HTML it was mocked from is out of scope.

## 7. Acceptance criteria

1. `uvx headroom-charts` runs on a machine with no project venv and no `rich`
   installed.
2. Pointed at an absent or empty file it renders the full layout and
   `Waiting for data...` rather than raising.
3. Pointed at a file with a truncated final line it skips that line and keeps
   painting.
4. Appending a line is reflected within one repaint interval.
5. Growing the file to 100k lines does not grow resident memory — the read is
   bounded, not a full-file `readlines()`.
6. `Ctrl-C` exits with the terminal restored to the primary screen, cursor and
   colours intact.
7. Works at 80×24 (chart degrades, nothing crashes) and at 200×50.
8. `--once` output is deterministic for a fixed input file, so it is snapshot-
   testable.
9. `--no-color` produces a readable dashboard on a terminal without truecolor.
