"""Agent roster view showing all agents with key stats and status."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _get_field(source: Any, field: str, default: Any = None) -> Any:
    """Fetch ``field`` regardless of dict or object source."""

    if isinstance(source, dict):
        return source.get(field, default)
    return getattr(source, field, default)


def _calculate_stress_level(agent_data: dict[str, Any]) -> tuple[str, str]:
    """Calculate stress level and style from agent progression or traits.
    
    Args:
        agent_data: Agent data dictionary with progression and/or traits
        
    Returns:
        Tuple of (stress_label, style)
    """
    # First check if we have progression data with stress
    progression = agent_data.get("progression")
    if progression and "stress" in progression:
        stress = progression["stress"]
        if stress <= 0.2:
            return "Calm", "green"
        elif stress <= 0.5:
            return "Focused", "yellow"
        elif stress <= 0.75:
            return "Strained", "orange"
        else:
            return "Burned Out", "red"
    
    # Fallback to calculating from traits (resolve)
    traits = agent_data.get("traits", {})
    resolve = traits.get("resolve", 0.5)
    
    if resolve >= 0.7:
        return "Calm", "green"
    elif resolve >= 0.4:
        return "Steady", "yellow"
    elif resolve >= 0.2:
        return "Strained", "orange"
    else:
        return "Stressed", "red"


def _format_expertise_pips(expertise_value: float | int) -> Text:
    """Format expertise as filled/unfilled pips (●○).
    
    Args:
        expertise_value: Expertise value (0.0-1.0 float or 0-5 int)
        
    Returns:
        Rich Text with colored pips
    """
    # Handle both float (0.0-1.0) and int (0-5) values
    if isinstance(expertise_value, float):
        filled = int(expertise_value * 5)
    else:
        filled = min(5, max(0, int(expertise_value)))
    
    pips = "●" * filled + "○" * (5 - filled)
    
    if filled >= 4:
        color = "green"
    elif filled >= 2:
        color = "yellow"
    else:
        color = "dim"
        
    return Text(pips, style=color)


def _get_agent_specialization(agent_data: dict[str, Any]) -> str:
    """Determine agent specialization from traits.
    
    Args:
        agent_data: Agent data dictionary with traits
        
    Returns:
        Specialization label
    """
    traits = agent_data.get("traits", {})
    empathy = traits.get("empathy", 0.5)
    cunning = traits.get("cunning", 0.5)
    resolve = traits.get("resolve", 0.5)
    
    # Determine primary trait
    if empathy >= cunning and empathy >= resolve:
        return "Negotiator"
    elif cunning >= empathy and cunning >= resolve:
        return "Investigator"
    else:
        return "Operative"


def _get_agent_status(agent_data: dict[str, Any], tick: int) -> tuple[str, str]:
    """Get agent availability status.
    
    Args:
        agent_data: Agent data dictionary
        tick: Current simulation tick
        
    Returns:
        Tuple of (status_label, style)
    """
    # Check if agent is assigned (would need metadata from game state)
    # For now, assume all agents are available
    # TODO: Track agent assignments in metadata
    return "Available", "green"


def render_agent_roster(
    agents_data: list[dict[str, Any]], tick: int = 0, selected_index: int | None = None
) -> Panel:
    """Render the agent roster view.
    
    Args:
        agents_data: List of agent data dictionaries with:
            - id: Agent ID
            - name: Agent name
            - role: Agent role
            - traits: Dict of trait values
            - faction_id: Optional faction affiliation
            - notes: Optional notes
            - progression: Optional AgentProgressionState data
        tick: Current simulation tick
        selected_index: Index of currently selected agent (for keyboard navigation)
        
    Returns:
        Rich Panel with agent roster table
    """
    if not agents_data:
        return Panel(
            Text("No agents available", style="dim", justify="center"),
            title="[bold]Agent Roster[/bold]",
            border_style="cyan",
        )
    
    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Agent", width=20)
    table.add_column("Role", width=16)
    table.add_column("Expertise", justify="center", width=10)
    table.add_column("Reliability", justify="center", width=10)
    table.add_column("Stress", width=12)
    table.add_column("Missions", justify="right", width=10)
    
    for idx, agent in enumerate(agents_data):
        name = agent.get("name", "Unknown")
        
        # Get progression data if available
        progression = agent.get("progression", {})
        role = progression.get("role", agent.get("role", "Operative"))
        
        # Calculate expertise from progression or highest trait
        if progression and "expertise" in progression:
            # Get highest expertise from progression
            expertise_dict = progression.get("expertise", {})
            if expertise_dict:
                expertise = max(expertise_dict.values())
            else:
                expertise = 0
        else:
            # Fallback to calculating from traits
            traits = agent.get("traits", {})
            expertise = int(max(traits.values()) * 5) if traits else 0
        expertise_pips = _format_expertise_pips(expertise)
        
        # Get reliability from progression or calculate from traits
        if progression and "reliability" in progression:
            reliability = progression["reliability"]
        else:
            # Default to 0.5 if no progression data
            reliability = 0.5
        reliability_text = Text(f"{reliability:.1%}", style="dim")
        
        # Get stress and mission count
        stress_label, stress_style = _calculate_stress_level(agent)
        missions = progression.get("missions_completed", 0)
        missions_text = Text(str(missions), style="cyan" if missions > 0 else "dim")
        
        # Get status
        status_label, status_style = _get_agent_status(agent, tick)
        
        # Apply selection highlight
        name_style = "bold reverse" if idx == selected_index else "bold"
        
        table.add_row(
            Text(name, style=name_style),
            Text(role, style="dim"),
            expertise_pips,
            reliability_text,
            Text(stress_label, style=stress_style),
            missions_text,
        )
    
    # Add keyboard hints to title
    nav_hint = " [dim](↑↓ to navigate, Enter to select)[/dim]" if agents_data else ""
    
    return Panel(
        table,
        title=f"[bold]Agent Roster[/bold] ({len(agents_data)} agents){nav_hint}",
        border_style="cyan",
    )


def render_agent_detail(agent_data: dict[str, Any], tick: int = 0) -> Panel:
    """Render detailed view of a selected agent.
    
    Args:
        agent_data: Agent data dictionary with progression info
        tick: Current simulation tick
        
    Returns:
        Rich Panel with agent details
    """
    name = agent_data.get("name", "Unknown")
    progression = agent_data.get("progression", {})
    role = progression.get("role", agent_data.get("role", "Operative"))
    traits = agent_data.get("traits", {})
    faction_id = agent_data.get("faction_id")
    home_district = agent_data.get("home_district")
    notes = agent_data.get("notes")
    
    # Build detail table
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left", style="dim")
    table.add_column(justify="left")
    
    # Status info
    stress_label, stress_style = _calculate_stress_level(agent_data)
    status_label, status_style = _get_agent_status(agent_data, tick)
    
    table.add_row("Role:", Text(role, style="bold"))
    table.add_row("Status:", Text(status_label, style=status_style))
    table.add_row("Stress:", Text(stress_label, style=stress_style))
    
    # Add progression metrics if available
    if progression:
        if "reliability" in progression:
            reliability = progression["reliability"]
            table.add_row("Reliability:", Text(f"{reliability:.1%}", style="cyan"))
        
        if "missions_completed" in progression:
            completed = progression.get("missions_completed", 0)
            failed = progression.get("missions_failed", 0)
            total = completed + failed
            success_rate = (completed / total * 100) if total > 0 else 0
            missions_text = (
                f"{completed} completed, {failed} failed "
                f"({success_rate:.0f}% success)"
            )
            table.add_row("Missions:", Text(missions_text, style="cyan"))
    
    if faction_id:
        table.add_row("Faction:", Text(faction_id, style="cyan"))
    
    if home_district:
        table.add_row("Home:", Text(home_district, style="yellow"))
    
    # Traits/Expertise section
    table.add_row("", "")
    if progression and "expertise" in progression:
        # Show expertise from progression
        expertise_dict = progression.get("expertise", {})
        if expertise_dict:
            table.add_row("[bold]Expertise:[/bold]", "")
            for domain, pips in sorted(expertise_dict.items()):
                pips_display = _format_expertise_pips(pips)
                table.add_row(f"  {domain.capitalize()}:", pips_display)
    elif traits:
        # Fallback to showing traits
        table.add_row("[bold]Traits:[/bold]", "")
        for trait_name, trait_value in sorted(traits.items()):
            pips = _format_expertise_pips(trait_value)
            table.add_row(f"  {trait_name.capitalize()}:", pips)
    
    # Notes section
    if notes:
        table.add_row("", "")
        table.add_row("[bold]Notes:[/bold]", "")
        table.add_row("", Text(notes, style="dim"))
    
    return Panel(
        table,
        title=f"[bold]{name}[/bold]",
        border_style="cyan",
    )


def prepare_agent_roster_data(game_state: Any) -> list[dict[str, Any]]:
    """Prepare agent roster data from game state.
    
    Args:
        game_state: Full game state dictionary or object
        
    Returns:
        List of agent data dictionaries with progression info
    """
    agents = _get_field(game_state, "agents", {})
    agent_progression = _get_field(game_state, "agent_progression", {})
    
    # Convert agents dict to list and sort by name
    agent_list = []
    for agent_id, agent in agents.items():
        # Get progression data if available
        prog = _get_field(agent_progression, agent_id)
        prog_data = prog.summary() if hasattr(prog, "summary") else prog if prog else {}
        
        agent_data = {
            "id": agent_id,
            "name": _get_field(agent, "name", agent_id),
            "role": _get_field(agent, "role", "Operative"),
            "traits": _get_field(agent, "traits", {}),
            "faction_id": _get_field(agent, "faction_id"),
            "home_district": _get_field(agent, "home_district"),
            "notes": _get_field(agent, "notes"),
            "progression": prog_data,
        }
        agent_list.append(agent_data)
    
    # Sort by name
    agent_list.sort(key=lambda a: a["name"])
    
    return agent_list
