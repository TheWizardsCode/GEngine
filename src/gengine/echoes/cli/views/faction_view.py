"""Faction overview view showing all factions with power dynamics."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _format_legitimacy_bar(legitimacy: float, delta: float = 0.0) -> Text:
    """Format legitimacy as a colored progress bar with trend.
    
    Args:
        legitimacy: Legitimacy value (0.0-1.0)
        delta: Change since last update
        
    Returns:
        Rich Text with formatted bar
    """
    # Create 8-char bar
    filled = int(legitimacy * 8)
    bar = "█" * filled + "░" * (8 - filled)
    
    # Color based on legitimacy level
    if legitimacy >= 0.6:
        color = "green"
    elif legitimacy >= 0.3:
        color = "yellow"
    else:
        color = "red"
    
    # Trend indicator
    if delta > 0.01:
        trend = "↑"
    elif delta < -0.01:
        trend = "↓"
    else:
        trend = "→"
    
    text = Text()
    text.append(bar, style=color)
    text.append(f" {legitimacy:.2f} ", style=color)
    text.append(trend, style="bold")
    
    return text


def _format_territory_claim(territory: list[str], districts: dict[str, Any]) -> str:
    """Format territory claims with dominance indicators.
    
    Args:
        territory: List of district IDs claimed by faction
        districts: Dict of all districts for name lookup
        
    Returns:
        Formatted territory string
    """
    if not territory:
        return "[dim]No territory[/dim]"
    
    # Limit to first 2 territories for compact display
    territory_names = []
    for district_id in territory[:2]:
        district = districts.get(district_id, {})
        name = district.get("name", district_id)
        territory_names.append(name)
    
    result = ", ".join(territory_names)
    
    if len(territory) > 2:
        result += f" (+{len(territory) - 2} more)"
    
    return result


def render_faction_overview(
    factions_data: list[dict[str, Any]],
    districts_data: dict[str, Any],
) -> Panel:
    """Render the faction overview view.
    
    Args:
        factions_data: List of faction data dictionaries with:
            - id: Faction ID
            - name: Faction name
            - ideology: Optional ideology
            - legitimacy: Legitimacy value (0.0-1.0)
            - resources: Dict of resources
            - territory: List of claimed district IDs
        districts_data: Dict of district data for territory lookup
        
    Returns:
        Rich Panel with faction overview table
    """
    if not factions_data:
        return Panel(
            Text("No factions available", style="dim", justify="center"),
            title="[bold]Faction Overview[/bold]",
            border_style="magenta",
        )
    
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Faction", width=20)
    table.add_column("Legitimacy", width=18)
    table.add_column("Territory", min_width=20)
    
    for faction in factions_data:
        name = faction.get("name", "Unknown")
        legitimacy = faction.get("legitimacy", 0.5)
        territory = faction.get("territory", [])
        
        # Get legitimacy delta from metadata if available
        delta = faction.get("legitimacy_delta", 0.0)
        legitimacy_bar = _format_legitimacy_bar(legitimacy, delta)
        
        territory_str = _format_territory_claim(territory, districts_data)
        
        table.add_row(
            Text(name, style="bold"),
            legitimacy_bar,
            Text(territory_str, style="dim"),
        )
    
    return Panel(
        table,
        title=f"[bold]Faction Overview[/bold] ({len(factions_data)} factions)",
        border_style="magenta",
    )


def render_faction_detail(
    faction_data: dict[str, Any],
    districts_data: dict[str, Any],
    all_factions: dict[str, Any],
) -> Panel:
    """Render detailed view of a selected faction.
    
    Args:
        faction_data: Faction data dictionary
        districts_data: Dict of district data for territory lookup
        all_factions: Dict of all factions for relationship context
        
    Returns:
        Rich Panel with faction details
    """
    name = faction_data.get("name", "Unknown")
    ideology = faction_data.get("ideology")
    description = faction_data.get("description")
    legitimacy = faction_data.get("legitimacy", 0.5)
    resources = faction_data.get("resources", {})
    territory = faction_data.get("territory", [])
    
    # Build detail table
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left", style="dim")
    table.add_column(justify="left")
    
    # Basic info
    if ideology:
        table.add_row("Ideology:", Text(ideology, style="cyan"))
    
    if description:
        table.add_row("", "")
        table.add_row("[bold]Description:[/bold]", "")
        table.add_row("", Text(description, style="dim"))
    
    # Legitimacy
    table.add_row("", "")
    table.add_row("[bold]Legitimacy:[/bold]", "")
    delta = faction_data.get("legitimacy_delta", 0.0)
    legitimacy_bar = _format_legitimacy_bar(legitimacy, delta)
    table.add_row("", legitimacy_bar)
    
    # Resources
    if resources:
        table.add_row("", "")
        table.add_row("[bold]Resources:[/bold]", "")
        for resource_type, amount in sorted(resources.items()):
            table.add_row(
                f"  {resource_type.capitalize()}:",
                Text(str(amount), style="yellow"),
            )
    
    # Territory
    if territory:
        table.add_row("", "")
        table.add_row("[bold]Territory:[/bold]", "")
        for district_id in territory:
            district = districts_data.get(district_id, {})
            district_name = district.get("name", district_id)
            # Determine dominance level (simplified)
            table.add_row("", Text(f"• {district_name} (claimed)", style="green"))
    
    # Recent actions (placeholder - would need action history)
    table.add_row("", "")
    table.add_row("[bold]Recent Actions:[/bold]", "")
    table.add_row("", Text("(Action history not yet implemented)", style="dim"))
    
    return Panel(
        table,
        title=f"[bold]{name}[/bold]",
        border_style="magenta",
    )


def prepare_faction_overview_data(
    game_state: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Prepare faction overview data from game state.
    
    Args:
        game_state: Full game state dictionary
        
    Returns:
        Tuple of (faction_list, districts_dict)
    """
    factions = game_state.get("factions", {})
    
    # Get districts for territory lookup
    city = game_state.get("city", {})
    districts_list = city.get("districts", [])
    districts_dict = {d.get("id"): d for d in districts_list}
    
    # Convert factions dict to list and sort by legitimacy (descending)
    faction_list = []
    for faction_id, faction in factions.items():
        faction_data = {
            "id": faction_id,
            "name": faction.get("name", faction_id),
            "ideology": faction.get("ideology"),
            "description": faction.get("description"),
            "legitimacy": faction.get("legitimacy", 0.5),
            "resources": faction.get("resources", {}),
            "territory": faction.get("territory", []),
            "legitimacy_delta": 0.0,  # Would need history tracking
        }
        faction_list.append(faction_data)
    
    # Sort by legitimacy (highest first)
    faction_list.sort(key=lambda f: f["legitimacy"], reverse=True)
    
    return faction_list, districts_dict
