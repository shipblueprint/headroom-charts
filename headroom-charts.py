import json
import os
import time
from collections import deque
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

# --- Brand Colors from your HTML ---
HARVEST = "#BB9457"
ESPRESSO = "#432818"
RUST = "#99582A"
MAROON = "#6F1D1B"
IVORY = "#EFE3D2"

SAVINGS_FILE = os.path.expanduser("~/.headroom/savings_events.jsonl")
MAX_BARS = 20 # How many recent events to show in the chart
CHART_HEIGHT = 10 # Height of the vertical bars

def get_events():
    events = []
    if os.path.exists(SAVINGS_FILE):
        with open(SAVINGS_FILE, "r") as f:
            # Get the last 100 events just in case
            for line in f.readlines()[-100:]:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events[-MAX_BARS:] # Return only the recent ones for the chart

def make_vertical_chart(events):
    if not events:
        return Text("Waiting for data...", style=IVORY)

    max_val = max(e.get("saved", 0) for e in events) or 1
    chart = Text()

    # Draw top-down
    for r in range(CHART_HEIGHT, 0, -1):
        # Y-Axis label
        y_val = int((r / CHART_HEIGHT) * max_val)
        chart.append(f"{y_val:>6} ┤ ", style=RUST)
        
        for e in events:
            val = e.get("saved", 0)
            bar_h = int((val / max_val) * CHART_HEIGHT)
            
            if bar_h >= r:
                # Filled part of the bar
                chart.append("██ ", style=HARVEST)
            else:
                # Empty space
                chart.append("   ", style=ESPRESSO)
        chart.append("\n")

    # X-Axis baseline
    chart.append("       └" + "───" * len(events) + "\n", style=RUST)
    
    # X-Axis labels (Time)
    chart.append("        ", style=RUST)
    for i, e in enumerate(events):
        ts = e.get("ts", "")[11:16] # Extract HH:MM
        # If we have many bars, show fewer labels to prevent overlap
        if len(events) > 15:
            if i % 3 == 0:
                chart.append(f"{ts[3:]:>3}", style=IVORY) # Just :MM
            else:
                chart.append("   ")
        else:
            chart.append(f"{ts[-2:]:>3}", style=IVORY) # Just MM

    return chart

def generate_dashboard():
    events = get_events()
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="kpi", size=5),
        Layout(name="chart", ratio=1),
        Layout(name="footer", size=8)
    )

    total_saved = sum(e.get("saved", 0) for e in events)
    total_cost = sum(e.get("cost_usd", 0.0) for e in events)
    
    # --- 1. Header ---
    header_text = Text(" HEADROOM COMPRESSION DASHBOARD", style=f"bold {IVORY} on {MAROON}")
    layout["header"].update(Panel(Align.center(header_text, vertical="middle"), box=box.ROUNDED, border_style=RUST, style=ESPRESSO))

    # --- 2. KPI Row ---
    kpi_table = Table.grid(expand=True)
    kpi_table.add_column(justify="center")
    kpi_table.add_column(justify="center")
    kpi_table.add_column(justify="center")
    
    kpi_table.add_row(
        f"[bold {HARVEST}]{total_saved:,}[/]\n[dim {IVORY}]Tokens Saved (Recent)[/]",
        f"[bold {HARVEST}]${total_cost:.4f}[/]\n[dim {IVORY}]Cost Avoided[/]",
        f"[bold {HARVEST}]{len(events)}[/]\n[dim {IVORY}]Compressions[/]"
    )
    layout["kpi"].update(Panel(kpi_table, box=box.ROUNDED, border_style=RUST, style=ESPRESSO))

    # --- 3. Vertical Chart ---
    chart_panel = Panel(
        Align.center(make_vertical_chart(events), vertical="middle"),
        title=f"[bold {IVORY}]Live Tokens Saved Per Call[/]",
        box=box.ROUNDED,
        border_style=HARVEST,
        style=ESPRESSO
    )
    layout["chart"].update(chart_panel)

    # --- 4. Footer Table ---
    table = Table(expand=True, box=box.SIMPLE, style=ESPRESSO)
    table.add_column("Time", style=RUST)
    table.add_column("Model", style=MAROON)
    table.add_column("Saved", justify="right", style=HARVEST)
    
    # Show last 5 events in table
    for e in reversed(events[-5:]):
        ts = e.get("ts", "")[:19].replace("T", " ")
        model = e.get("model", "unknown")
        saved = e.get("saved", 0)
        table.add_row(ts, model, f"{saved:,}")

    layout["footer"].update(Panel(
        table, 
        title=f"[bold {IVORY}]Latest Events[/]", 
        box=box.ROUNDED, 
        border_style=RUST, 
        style=ESPRESSO
    ))

    return layout

if __name__ == "__main__":
    # screen=True makes it take over the terminal like htop/Sleev
    with Live(generate_dashboard(), refresh_per_second=1, screen=True) as live:
        try:
            while True:
                time.sleep(1)
                live.update(generate_dashboard())
        except KeyboardInterrupt:
            pass