"""Context panel component showing details for selected entities."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _render_modifier_bar(name: str, value: float, delta: float = 0.0) -> Text:
    """Render a modifier with a progress bar and trend indicator.

    Args:
        name: Modifier name
        value: Current value (0.0-1.0)
        delta: Change since last update

    Returns:
        Rich Text object with formatted bar
    """
    # Create 8-char bar
    filled = int(value * 8)
    bar = "█" * filled + "░" * (8 - filled)

    # Determine color
    if value >= 0.6:
        color = "red"
    elif value >= 0.3:
        color = "yellow"
    else:
        color = "green"

    # Determine trend
    if delta > 0.01:
        trend = "↑"
    elif delta < -0.01:
        trend = "↓"
    else:
        trend = "→"

    text = Text()
    text.append(f"{name:12} ", style="dim")
    text.append(bar, style=color)
    text.append(f" {value:.2f} ", style=color)
    text.append(trend, style="bold")

    return text


def render_context_panel(
    entity_type: str | None,
    entity_data: dict[str, Any] | None,
) -> Panel:
    """Render the context panel showing entity details.

    Args:
        entity_type: Type of entity ("district", "agent", "faction", or None)
        entity_data: Entity data dictionary

    Returns:
        Rich Panel with context content
    """
    if entity_type is None or entity_data is None:
        # Show empty state
        return Panel(
            Text(
                "Select a district or entity\nto view details",
                style="dim",
                justify="center",
            ),
            title="[bold]Context[/bold]",
            border_style="white",
        )

    if entity_type == "district":
        return _render_district_context(entity_data)
    elif entity_type == "agent":
        return _render_agent_context(entity_data)
    elif entity_type == "faction":
        return _render_faction_context(entity_data)
    else:
        return Panel(
            Text(f"Unknown entity type: {entity_type}", style="red"),
            title="[bold]Context[/bold]",
            border_style="white",
        )


def _render_district_context(district: dict[str, Any]) -> Panel:
    """Render context panel for a district."""
    name = district.get("name", "Unknown")
    population = district.get("population", 0)
    modifiers = district.get("modifiers", {})
    resources = district.get("resources", {})
    active_seeds = district.get("active_seeds", [])
    faction_presence = district.get("faction_presence", "")

    table = Table(show_header=False, box=None, padding=(0, 0))
    table.add_column(justify="left", width=40)

    # Header
    table.add_row(Text(f"Population: {population:,}", style="cyan"))
    table.add_row("")  # Spacer

    # Modifiers
    table.add_row(Text("Modifiers:", style="bold"))
    for mod_name in ["unrest", "pollution", "prosperity", "security"]:
        value = modifiers.get(mod_name, 0.0)
        delta = modifiers.get(f"{mod_name}_delta", 0.0)
        table.add_row(_render_modifier_bar(mod_name.capitalize(), value, delta))

    # Resources
    if resources:
        table.add_row("")  # Spacer
        table.add_row(Text("Resources:", style="bold"))
        for resource, data in resources.items():
            current = data.get("current", 0)
            capacity = data.get("capacity", 0)
            if current < capacity * 0.5:
                style = "red"
                suffix = " (shortage!)"
            else:
                style = "green"
                suffix = ""
            table.add_row(
                Text(
                    f"  {resource.capitalize()}: {current}/{capacity}{suffix}",
                    style=style,
                )
            )

    # Active story seeds
    if active_seeds:
        table.add_row("")  # Spacer
        table.add_row(Text(f"Active Seeds: {', '.join(active_seeds)}", style="magenta"))

    # Faction presence
    if faction_presence:
        table.add_row("")  # Spacer
        table.add_row(Text(f"Faction: {faction_presence}", style="yellow"))

    return Panel(
        table,
        title=f"[bold]{name}[/bold]",
        subtitle="[dim]District[/dim]",
        border_style="cyan",
    )


def _render_agent_context(agent: dict[str, Any]) -> Panel:
    """Render context panel for an agent."""
    name = agent.get("name", "Unknown")
    role = agent.get("role", "Agent")
    status = agent.get("status", "Available")
    stress = agent.get("stress", 0.0)
    expertise = agent.get("expertise", {})

    table = Table(show_header=False, box=None, padding=(0, 0))
    table.add_column(justify="left", width=40)

    table.add_row(Text(f"Status: {status}", style="cyan"))
    stress_bar = "█" * int(stress * 8) + "░" * (8 - int(stress * 8))
    table.add_row(Text(f"Stress: {stress_bar}", style="yellow"))
    table.add_row("")  # Spacer

    # Expertise
    if expertise:
        table.add_row(Text("Expertise:", style="bold"))
        for skill, level in expertise.items():
            pips = "●" * level + "○" * (5 - level)
            table.add_row(Text(f"  {skill.capitalize()}: {pips}", style=""))

    return Panel(
        table,
        title=f"[bold]{name}[/bold]",
        subtitle=f"[dim]{role}[/dim]",
        border_style="cyan",
    )


def _render_faction_context(faction: dict[str, Any]) -> Panel:
    """Render context panel for a faction."""
    name = faction.get("name", "Unknown")
    legitimacy = faction.get("legitimacy", 0.0)
    resources = faction.get("resources", 0.0)
    territory = faction.get("territory", [])

    table = Table(show_header=False, box=None, padding=(0, 0))
    table.add_column(justify="left", width=40)

    # Legitimacy bar
    legit_bar = "█" * int(legitimacy * 8) + "░" * (8 - int(legitimacy * 8))
    table.add_row(Text(f"Legitimacy: {legit_bar} {legitimacy:.2f}", style="yellow"))

    # Resources bar
    res_bar = "█" * int(resources * 8) + "░" * (8 - int(resources * 8))
    table.add_row(Text(f"Resources:  {res_bar} {resources:.2f}", style="cyan"))

    # Territory
    if territory:
        table.add_row("")  # Spacer
        table.add_row(Text("Territory:", style="bold"))
        for t in territory[:3]:  # Show first 3
            table.add_row(Text(f"  {t}", style="dim"))

    return Panel(
        table,
        title=f"[bold]{name}[/bold]",
        subtitle="[dim]Faction[/dim]",
        border_style="cyan",
    )
