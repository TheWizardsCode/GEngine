"""Focus management view for narrative budget allocation."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def render_focus_management(
    focus_state: dict[str, Any],
    districts_data: list[dict[str, Any]],
) -> Panel:
    """Render the focus management view showing budget allocation.
    
    Args:
        focus_state: Focus state dictionary with:
            - district_id: Current focus district ID (or None)
            - adjacent: List of adjacent district IDs
            - allocation: Budget allocation stats
        districts_data: List of all districts
        
    Returns:
        Rich Panel with focus management interface
    """
    focused_id = focus_state.get("district_id")
    adjacent_ids = focus_state.get("adjacent", [])
    allocation = focus_state.get("allocation", {})
    
    # Build districts lookup
    districts_dict = {d.get("id"): d for d in districts_data}
    
    # Create table
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left", style="dim")
    table.add_column(justify="left")
    
    # Current focus
    if focused_id:
        district = districts_dict.get(focused_id, {})
        district_name = district.get("name", focused_id)
        table.add_row(
            "[bold]Current Focus:[/bold]",
            Text(district_name, style="cyan bold"),
        )
    else:
        table.add_row("[bold]Current Focus:[/bold]", Text("None (Global)", style="dim"))
    
    table.add_row("", "")
    
    # Budget allocation
    table.add_row("[bold]Budget Allocation:[/bold]", "")
    
    ring_events = allocation.get("ring_events", 0)
    global_events = allocation.get("global_events", 0)
    total_events = ring_events + global_events
    archived = allocation.get("archived", 0)
    
    if total_events > 0:
        ring_pct = (ring_events / total_events) * 100
        global_pct = (global_events / total_events) * 100
        
        table.add_row(
            "  Ring events:",
            Text(f"{ring_events}/{total_events} ({ring_pct:.0f}%)", style="green"),
        )
        table.add_row(
            "  Global events:",
            Text(f"{global_events}/{total_events} ({global_pct:.0f}%)", style="yellow"),
        )
    else:
        table.add_row("  Ring events:", Text("0/0 (0%)", style="dim"))
        table.add_row("  Global events:", Text("0/0 (0%)", style="dim"))
    
    table.add_row("  Archived:", Text(str(archived), style="dim"))
    
    # Adjacent districts in focus ring
    if adjacent_ids:
        table.add_row("", "")
        table.add_row("[bold]Focus Ring:[/bold]", "")
        
        for district_id in adjacent_ids[:5]:  # Show first 5
            district = districts_dict.get(district_id, {})
            district_name = district.get("name", district_id)
            table.add_row("", Text(f"• {district_name}", style="cyan"))
        
        if len(adjacent_ids) > 5:
            table.add_row("", Text(f"  (+{len(adjacent_ids) - 5} more)", style="dim"))
    
    # Instructions
    table.add_row("", "")
    table.add_row("[dim]Press 'f' to change focus[/dim]", "")
    
    return Panel(
        table,
        title="[bold]Focus Management[/bold]",
        border_style="blue",
    )


def render_focus_selection(
    districts_data: list[dict[str, Any]],
    current_focus: str | None,
) -> Panel:
    """Render district selection interface for focus change.
    
    Args:
        districts_data: List of all districts with:
            - id: District ID
            - name: District name
            - modifiers: District modifiers
        current_focus: Currently focused district ID
        
    Returns:
        Rich Panel with district selection table
    """
    table = Table(show_header=True, header_style="bold blue", expand=True)
    table.add_column("#", width=4, justify="right")
    table.add_column("District", width=20)
    table.add_column("Status", width=15)
    table.add_column("Distance", width=10)
    
    for idx, district in enumerate(districts_data, 1):
        district_id = district.get("id", "unknown")
        district_name = district.get("name", "Unknown")
        modifiers = district.get("modifiers", {})
        
        # Calculate district health score (simplified)
        unrest = modifiers.get("unrest", 0.5)
        pollution = modifiers.get("pollution", 0.5)
        health_score = 1.0 - ((unrest + pollution) / 2.0)
        
        if health_score >= 0.6:
            status = Text("Stable", style="green")
        elif health_score >= 0.3:
            status = Text("Stressed", style="yellow")
        else:
            status = Text("Crisis", style="red")
        
        # Distance indicator (relative to current focus)
        if district_id == current_focus:
            distance = Text("Current", style="cyan bold")
        else:
            # Would calculate actual distance from focus graph
            distance = Text("-", style="dim")
        
        table.add_row(
            str(idx),
            Text(district_name, style="bold" if district_id == current_focus else ""),
            status,
            distance,
        )
    
    return Panel(
        table,
        title="[bold]Select Focus District[/bold]",
        subtitle="[dim]Enter district number or 'c' to cancel[/dim]",
        border_style="blue",
    )


def prepare_focus_data(game_state: dict[str, Any]) -> dict[str, Any]:
    """Prepare focus management data from game state.
    
    Args:
        game_state: Full game state dictionary
        
    Returns:
        Focus state dictionary
    """
    metadata = game_state.get("metadata", {})
    focus_state = metadata.get("focus_state", {})
    
    # Extract allocation from last digest
    last_digest = metadata.get("last_event_digest", {})
    allocation = last_digest.get("allocation", {})
    
    return {
        "district_id": focus_state.get("district_id"),
        "adjacent": focus_state.get("adjacent", []),
        "allocation": {
            "ring_events": allocation.get("ring_events", 0),
            "global_events": allocation.get("global_events", 0),
            "archived": allocation.get("archived", 0),
        },
    }
