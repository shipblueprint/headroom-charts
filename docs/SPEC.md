# headroom-charts — Behaviour Specification

Status: v1, describing shipped behaviour · Last updated: 2026-10-28

**Source of truth is the code, not this document.** [`src/headroom_charts/app.py`](../src/headroom_charts/app.py)
is the original `headroom-charts.py` verbatim; this file describes what that code
does so a packaging change can be checked against it. It is not a wish list.

## 1. Purpose

Watch a context-compression proxy's token savings while it runs, in one terminal
screen, without `tail -f` and reading raw JSON. A viewer only — it never writes the
events file.

## 2. Data contract

`~/.headroom/savings_events.jsonl` — append-only JSON Lines, one event per line,
schema version `v: 2`. A real line:

```json
{"v":2,"ts":"2026-10-27T21:06:59.766090+00:00","before":65046,"after":62184,
 "saved":2862,"cost_usd":0.008586,"model":"beam","client":"opencode",
 "source":"proxy","pid":27451,"saved_tool_schema":0}
```

| Field | Type | Used | Notes |
|---|---|---|---|
| `v` | int | no | always `2` in observed data |
| `ts` | string | **yes** | ISO-8601 with offset; sliced as `[11:16]` for `HH:MM` and `[:19]` for the table |
| `before` | int | no | prompt tokens pre-compression |
| `after` | int | no | prompt tokens post-compression |
| `saved` | int | **yes** | bar height and the token KPI |
| `cost_usd` | float | **yes** | cost KPI |
| `model` | string | **yes** | table column |
| `client`, `source`, `pid`, `saved_tool_schema` | — | no | present in the log, not displayed |

Tolerated input:

- File absent → `get_events()` returns `[]` and the chart prints `Waiting for data...`.
- Malformed line → `json.JSONDecodeError` is caught and the line skipped.
- Missing field → `.get()` default of `0`, `0.0` or `"unknown"`.
- Only the **last 100 lines** of the file are considered, then trimmed to the last
  20 for plotting.

## 3. Interface

Four zones in a `rich` `Layout`, repainted once per second on the alternate screen
(`Live(screen=True, refresh_per_second=1)`).

| Zone | Rows | Contents |
|---|---|---|
| header | 3 | `HEADROOM COMPRESSION DASHBOARD`, ivory-on-maroon, RUST border |
| kpi | 5 | `Tokens Saved (Recent)` · `Cost Avoided` · `Compressions` |
| chart | ratio 1 | `Live Tokens Saved Per Call`, HARVEST border, bars over an axis |
| footer | 8 | `Latest Events` table, last 5 as `Time │ Model │ Saved`, newest first |

Chart, exactly as implemented:

- Up to `MAX_BARS = 20` events, oldest on the left.
- `CHART_HEIGHT = 10` rows, scaled by the largest `saved` in the window (`or 1` so a
  zero window cannot divide by zero).
- Bar height is `int((val / max_val) * 10)` — truncated, so a low-but-nonzero value
  can render as no bar.
- A filled cell is `██ `, an empty cell is three spaces.
- Y-axis gutter is `{value:>6} ┤ `; baseline is `       └` + `───` per bar.
- X labels are minutes; above 15 events only every third bar is labelled.

KPI figures are window sums, not lifetime: total `saved`, total `cost_usd` and event
count over the same ≤20 events the chart plots.

Palette — 24-bit hex, from the original HTML mockup:

| Name | Hex | Used for |
|---|---|---|
| `HARVEST` | `#BB9457` | bars, KPI numerals, chart border |
| `ESPRESSO` | `#432818` | panel `style` |
| `RUST` | `#99582A` | borders, axes, table columns |
| `MAROON` | `#6F1D1B` | header background, model column |
| `IVORY` | `#EFE3D2` | text and labels |

`rich` maps these onto whatever colour system the terminal reports; verified to draw
on `TERM=dumb`, `vt100` and `xterm-256color`.

## 4. Invocation

```
headroom-charts
```

No options, matching the original script. Exits `0`, including on `Ctrl-C`, which the
loop catches and passes.

## 5. Non-goals

- **Any change to rendering, layout sizes, geometry or palette.** Packaging is a
  distribution change, not a redesign.
- Reading any file other than the one path above.
- Writing, rotating or backfilling the events log.
- Cost estimation — `cost_usd` is displayed as given.
- Network access, telemetry, config files, mouse input, panes, history zoom.

## 6. Fidelity acceptance

The gate for every future packaging change:

1. `python headroom-charts.py` and the installed `headroom-charts` command emit
   **identical bytes** for the same terminal size and the same events file.
2. Both exit `0` on `Ctrl-C`.
3. A rendered frame at 100×30 against the test fixture equals
   [`tests/golden/frame_100x30.txt`](../tests/golden/frame_100x30.txt), which was
   captured from the original script.
4. Changing any constant in §3 — a hex, `MAX_BARS`, `CHART_HEIGHT`, a zone size —
   fails that golden test rather than passing review.

Known defects in the original are preserved deliberately and tracked separately; see
docs/ARCHITECTURE.md §5.
