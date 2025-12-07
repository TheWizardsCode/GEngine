"""Global status bar component showing city health at a glance."""

from __future__ import annotations

from typing import Any

from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _format_stability_bar(stability: float) -> Text:
    """Format stability as a colored progress bar.

    Args:
        stability: Stability value (0.0-1.0)

    Returns:
        Rich Text object with styled progress bar
    """
    # Determine color based on thresholds
    if stability >= 0.7:
        color = "green"
    elif stability >= 0.4:
        color = "yellow"
    else:
        color = "red"

    # Create 10-char bar
    filled = int(stability * 10)
    bar = "█" * filled + "░" * (10 - filled)

    return Text(f"{bar} {stability:.0%}", style=color)


def render_status_bar(state_data: dict[str, Any]) -> Panel:
    """Render the global status bar showing city health.

    Args:
        state_data: Dictionary containing:
            - city: City name
            - tick: Current tick number
            - stability: Stability value (0.0-1.0)
            - alerts: List of alert dictionaries
            - events_count: Number of recent events

    Returns:
        Rich Panel with status bar content
    """
    city_name = state_data.get("city", "Unknown City")
    tick = state_data.get("tick", 0)
    stability = state_data.get("stability", 1.0)
    alerts = state_data.get("alerts", [])
    events_count = state_data.get("events_count", 0)

    # Count critical alerts
    critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
    alert_count = len(critical_alerts)

    # Build status table
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left", width=20)
    table.add_column(justify="center", width=12)
    table.add_column(justify="center", width=20)
    table.add_column(justify="center", width=10)
    table.add_column(justify="center", width=10)

    # Add row with all elements
    stability_bar = _format_stability_bar(stability)

    alert_style = "red bold" if alert_count > 0 else "dim"
    alert_text = Text(f"⚠ {alert_count}", style=alert_style)

    events_style = "cyan" if events_count > 0 else "dim"
    events_text = Text(f"🔔 {events_count}", style=events_style)

    table.add_row(
        Text(f"🏙 {city_name}", style="bold cyan"),
        Text(f"Tick {tick}", style="yellow"),
        stability_bar,
        alert_text,
        events_text,
    )

    return Panel(
        Align.center(table),
        title="[bold]Global Status[/bold]",
        border_style="cyan",
        height=3,
    )


class StatusBar:
    """Rich renderable class for the status bar component."""

    def __init__(self, state_data: dict[str, Any]):
        self.state_data = state_data

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield render_status_bar(self.state_data)
