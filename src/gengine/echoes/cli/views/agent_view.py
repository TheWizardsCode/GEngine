"""Agent roster view showing all agents with key stats and status."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _calculate_stress_level(agent_data: dict[str, Any]) -> tuple[str, str]:
    """Calculate stress level and style from agent traits.
    
    Args:
        agent_data: Agent data dictionary with traits
        
    Returns:
        Tuple of (stress_label, style)
    """
    traits = agent_data.get("traits", {})
    # Calculate stress from traits (empathy/cunning/resolve)
    # Lower resolve = higher stress
    resolve = traits.get("resolve", 0.5)
    
    if resolve >= 0.7:
        return "Calm", "green"
    elif resolve >= 0.4:
        return "Steady", "yellow"
    elif resolve >= 0.2:
        return "Strained", "orange"
    else:
        return "Stressed", "red"


def _format_expertise_pips(expertise_value: float) -> Text:
    """Format expertise as filled/unfilled pips (●○).
    
    Args:
        expertise_value: Expertise value (0.0-1.0)
        
    Returns:
        Rich Text with colored pips
    """
    filled = int(expertise_value * 5)
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


def render_agent_roster(agents_data: list[dict[str, Any]], tick: int = 0) -> Panel:
    """Render the agent roster view.
    
    Args:
        agents_data: List of agent data dictionaries with:
            - id: Agent ID
            - name: Agent name
            - role: Agent role
            - traits: Dict of trait values
            - faction_id: Optional faction affiliation
            - notes: Optional notes
        tick: Current simulation tick
        
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
    table.add_column("Agent", width=18)
    table.add_column("Role", width=14)
    table.add_column("Expertise", justify="center", width=10)
    table.add_column("Stress", width=10)
    table.add_column("Status", width=12)
    
    for agent in agents_data:
        name = agent.get("name", "Unknown")
        role = agent.get("role", "Operative")
        
        # Calculate expertise from highest trait
        traits = agent.get("traits", {})
        expertise = max(traits.values()) if traits else 0.5
        expertise_pips = _format_expertise_pips(expertise)
        
        # Get stress and status
        stress_label, stress_style = _calculate_stress_level(agent)
        status_label, status_style = _get_agent_status(agent, tick)
        
        table.add_row(
            Text(name, style="bold"),
            Text(role, style="dim"),
            expertise_pips,
            Text(stress_label, style=stress_style),
            Text(status_label, style=status_style),
        )
    
    return Panel(
        table,
        title=f"[bold]Agent Roster[/bold] ({len(agents_data)} agents)",
        border_style="cyan",
    )


def render_agent_detail(agent_data: dict[str, Any], tick: int = 0) -> Panel:
    """Render detailed view of a selected agent.
    
    Args:
        agent_data: Agent data dictionary
        tick: Current simulation tick
        
    Returns:
        Rich Panel with agent details
    """
    name = agent_data.get("name", "Unknown")
    role = agent_data.get("role", "Operative")
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
    
    if faction_id:
        table.add_row("Faction:", Text(faction_id, style="cyan"))
    
    if home_district:
        table.add_row("Home:", Text(home_district, style="yellow"))
    
    # Traits section
    if traits:
        table.add_row("", "")
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


def prepare_agent_roster_data(game_state: dict[str, Any]) -> list[dict[str, Any]]:
    """Prepare agent roster data from game state.
    
    Args:
        game_state: Full game state dictionary
        
    Returns:
        List of agent data dictionaries
    """
    agents = game_state.get("agents", {})
    
    # Convert agents dict to list and sort by name
    agent_list = []
    for agent_id, agent in agents.items():
        agent_data = {
            "id": agent_id,
            "name": agent.get("name", agent_id),
            "role": agent.get("role", "Operative"),
            "traits": agent.get("traits", {}),
            "faction_id": agent.get("faction_id"),
            "home_district": agent.get("home_district"),
            "notes": agent.get("notes"),
        }
        agent_list.append(agent_data)
    
    # Sort by name
    agent_list.sort(key=lambda a: a["name"])
    
    return agent_list
