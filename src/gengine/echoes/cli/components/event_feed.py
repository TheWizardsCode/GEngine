"""Event feed component displaying recent simulation events."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _get_severity_icon(severity: str) -> tuple[str, str]:
    """Get icon and color for event severity.

    Args:
        severity: Event severity ("critical", "warning", "info", "story", "economy")

    Returns:
        Tuple of (icon, color)
    """
    severity_map = {
        "critical": ("🔴", "red"),
        "warning": ("🟡", "yellow"),
        "info": ("🟢", "green"),
        "story": ("📖", "magenta"),
        "economy": ("⚡", "cyan"),
    }
    return severity_map.get(severity, ("○", "white"))


def _classify_event_severity(event: dict[str, Any]) -> str:
    """Classify event severity based on content.

    Args:
        event: Event dictionary

    Returns:
        Severity string ("critical", "warning", "info", "story", "economy")
    """
    # Check if severity is explicitly set
    if "severity" in event:
        return event["severity"]

    description = event.get("description", "").lower()
    event_type = event.get("type", "").lower()

    # Story events
    if "story" in event_type or "seed" in description:
        return "story"

    # Economy events
    if "price" in description or "market" in description or "shortage" in description:
        return "economy"

    # Critical events
    if (
        "crisis" in description
        or "critical" in description
        or "shortage" in description
        and "3" in description
    ):
        return "critical"

    # Warning events
    if (
        "warning" in description
        or "unrest" in description
        or "sabotage" in description
    ):
        return "warning"

    # Default to info
    return "info"


def render_event_feed(
    events: list[dict[str, Any]],
    max_events: int = 7,
    focus_district: str | None = None,
) -> Panel:
    """Render the event feed showing recent events.

    Args:
        events: List of event dictionaries (newest first)
        max_events: Maximum number of events to display
        focus_district: Currently focused district ID
                       (events from this district are highlighted)

    Returns:
        Rich Panel with event feed content
    """
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(justify="left", width=80)

    # Show most recent events
    displayed_events = events[:max_events]

    if not displayed_events:
        table.add_row(Text("No recent events", style="dim"))
    else:
        for event in displayed_events:
            severity = _classify_event_severity(event)
            icon, color = _get_severity_icon(severity)

            tick = event.get("tick", 0)
            location = event.get("location", "")
            description = event.get("description", "Unknown event")

            # Build event line
            event_line = Text()
            event_line.append(f"{icon} ", style=color)
            event_line.append(f"T{tick:3d} ", style="dim")

            if location:
                # Highlight if in focus district
                if location == focus_district:
                    event_line.append(f"{location}: ", style="bold cyan")
                else:
                    event_line.append(f"{location}: ", style="")

            event_line.append(description, style="")

            table.add_row(event_line)

    # Add suppressed count if available
    suppressed_count = sum(1 for e in events[max_events:])
    if suppressed_count > 0:
        footer = Text(f"  +{suppressed_count} more events archived", style="dim italic")
        table.add_row("")  # Spacer
        table.add_row(footer)

    return Panel(
        table,
        title="[bold]Event Feed[/bold]",
        border_style="yellow",
        height=8,
    )
