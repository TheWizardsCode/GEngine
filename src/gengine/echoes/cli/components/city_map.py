"""ASCII city map component showing districts with boundaries and connections."""

from __future__ import annotations

from typing import Any

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _get_focus_indicator(district_id: str, focus_data: dict[str, Any]) -> str:
    """Get the focus indicator for a district.

    Args:
        district_id: ID of the district
        focus_data: Focus state data containing district_id and adjacent list

    Returns:
        Focus indicator string ("●" for focused, "◐" for adjacent, "○" for other)
    """
    focused_id = focus_data.get("district_id")
    adjacent_ids = focus_data.get("adjacent", [])

    if district_id == focused_id:
        return "●"
    elif district_id in adjacent_ids:
        return "◐"
    else:
        return "○"


def _get_overlay_color(overlay: str | None, value: float) -> str:
    """Get color for overlay value based on overlay type.
    
    Args:
        overlay: Overlay type ("unrest", "pollution", "security",
            "prosperity", "control")
        value: Metric value (0.0-1.0)
        
    Returns:
        Color name for styling
    """
    # For positive metrics (security, prosperity), high is good (green)
    # For negative metrics (unrest, pollution), high is bad (red)
    positive_overlays = {"security", "prosperity", "control"}
    is_positive = overlay in positive_overlays if overlay else False
    
    if is_positive:
        # Inverted colors for positive metrics
        if value >= 0.6:
            return "green"
        elif value >= 0.3:
            return "yellow"
        else:
            return "red"
    else:
        # Standard colors for negative metrics
        if value >= 0.6:
            return "red"
        elif value >= 0.3:
            return "yellow"
        else:
            return "green"


def _format_district_node(
    district: dict[str, Any],
    focus_data: dict[str, Any],
    selected_id: str | None,
    overlay: str | None,
) -> Text:
    """Format a single district node for display.

    Args:
        district: District data dictionary
        focus_data: Focus state data
        selected_id: Currently selected district ID
        overlay: Overlay mode ("unrest", "pollution", "security",
            "prosperity", "control", or None)

    Returns:
        Rich Text object with formatted district node
    """
    district_id = district.get("id", "unknown")
    name = district.get("name", "Unknown")

    # Get focus indicator
    focus_marker = _get_focus_indicator(district_id, focus_data)

    # Determine overlay value and color
    modifiers = district.get("modifiers", {})
    
    # Map "control" overlay to "security" modifier
    if overlay == "control":
        value = modifiers.get("security", 0.5)
    elif overlay and overlay in modifiers:
        value = modifiers[overlay]
    else:
        # Default to aggregated stability score
        stability = district.get("stability", 0.5)
        value = stability
        overlay = None  # Use default coloring
    
    color = _get_overlay_color(overlay, value)
    overlay_str = f" {value:.2f}"

    # Build node text
    node_text = Text()

    # Highlight if selected
    if district_id == selected_id:
        node_text.append("┌─────────┐\n", style="bold cyan")
        node_text.append("│", style="bold cyan")
        node_text.append(f" {focus_marker} {name[:6]:6}", style=f"bold {color}")
        node_text.append("│\n", style="bold cyan")
        node_text.append("│", style="bold cyan")
        node_text.append(f"{overlay_str:9}", style=color)
        node_text.append("│\n", style="bold cyan")
        node_text.append("└─────────┘", style="bold cyan")
    else:
        style = "bold" if focus_marker == "●" else ""
        node_text.append("┌─────────┐\n")
        node_text.append(f"│ {focus_marker} {name[:6]:6}│\n", style=style)
        node_text.append(f"│{overlay_str:9}│\n", style=color)
        node_text.append("└─────────┘")

    return node_text


def render_city_map(
    districts: list[dict[str, Any]],
    focus_data: dict[str, Any],
    selected_id: str | None = None,
    overlay: str | None = None,
) -> Panel:
    """Render the city map showing all districts.

    Args:
        districts: List of district dictionaries
        focus_data: Focus state data
        selected_id: Currently selected district ID
        overlay: Overlay mode ("unrest", "pollution", "security",
            "prosperity", "control", or None)

    Returns:
        Rich Panel with city map content
    """
    # Create a simple grid layout for districts
    # For now, arrange in a simple table format
    # In future, could use actual coordinates if available

    table = Table.grid(padding=(0, 1))

    # Determine number of columns (3 districts per row looks good)
    num_cols = 3
    for i in range(0, len(districts), num_cols):
        row_districts = districts[i : i + num_cols]
        # Add columns for this row if needed
        if i == 0:
            for _ in range(num_cols):
                table.add_column(justify="center")

        # Format district nodes for this row
        nodes = []
        for district in row_districts:
            nodes.append(
                _format_district_node(district, focus_data, selected_id, overlay)
            )

        # Pad with empty if needed
        while len(nodes) < num_cols:
            nodes.append(Text(""))

        table.add_row(*nodes)

    # Add legend
    legend = Table.grid(padding=(0, 2))
    legend.add_column(justify="left")
    legend.add_row(
        Text("Legend: ", style="dim"),
        Text("● Focus ", style="bold"),
        Text("◐ Adjacent ", style=""),
        Text("○ Other", style="dim"),
    )

    # Add overlay legend with color scale
    if overlay:
        overlay_legend = Table.grid(padding=(0, 1))
        overlay_legend.add_column(justify="left")
        overlay_legend.add_row(
            Text(f"Overlay: {overlay.capitalize()}", style="bold"),
            Text("  Low ", style="green"),
            Text("→", style="dim"),
            Text(" Med ", style="yellow"),
            Text("→", style="dim"),
            Text(" High", style="red"),
        )
        
        content = Table.grid()
        content.add_row(table)
        content.add_row("")  # Spacer
        content.add_row(legend)
        content.add_row(overlay_legend)
    else:
        content = Table.grid()
        content.add_row(table)
        content.add_row("")  # Spacer
        content.add_row(legend)

    # Add overlay indicator if active
    overlay_text = ""
    if overlay:
        overlay_text = f" [{overlay.capitalize()}]"

    return Panel(
        Align.center(content),
        title=f"[bold]City Map{overlay_text}[/bold]",
        border_style="blue",
    )
