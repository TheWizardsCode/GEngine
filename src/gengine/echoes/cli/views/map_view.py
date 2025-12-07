"""Map view implementation for Terminal UI mode."""

from __future__ import annotations

from typing import Any

from ..components import render_city_map, render_context_panel


def prepare_map_view_data(
    state: Any,
    ui_state: Any,
) -> dict[str, Any]:
    """Prepare data for the map view from game state.

    Args:
        state: GameState object
        ui_state: UIState object

    Returns:
        Dictionary containing prepared view data
    """
    # Extract districts
    districts = []
    for district in state.city.districts.values():
        district_data = {
            "id": district.id,
            "name": district.name,
            "population": district.population,
            "stability": getattr(district, "stability", 0.5),
            "modifiers": {
                "unrest": district.unrest,
                "pollution": district.pollution,
                "prosperity": district.prosperity,
                "security": getattr(district, "security", 0.5),
                "unrest_delta": getattr(district, "unrest_delta", 0.0),
                "pollution_delta": getattr(district, "pollution_delta", 0.0),
            },
            "resources": {},  # Could be populated if available
            "active_seeds": [],  # Could be populated from metadata
            "faction_presence": "",  # Could be populated from faction data
        }
        districts.append(district_data)

    # Extract focus data
    focus_meta = state.metadata.get("focus", {})
    focus_data = {
        "district_id": focus_meta.get("district_id"),
        "adjacent": focus_meta.get("adjacent", []),
    }

    # Get selected district data if any
    selected_entity_data = None
    if ui_state.selected_entity and ui_state.selected_entity_type == "district":
        for dist in districts:
            if dist["id"] == ui_state.selected_entity:
                selected_entity_data = dist
                break

    return {
        "districts": districts,
        "focus_data": focus_data,
        "selected_id": ui_state.selected_entity,
        "overlay": ui_state.show_overlay,
        "selected_entity_type": ui_state.selected_entity_type,
        "selected_entity_data": selected_entity_data,
    }


def render_map_view(view_data: dict[str, Any]) -> tuple[Any, Any]:
    """Render the map view components.

    Args:
        view_data: Prepared view data dictionary

    Returns:
        Tuple of (main_content, context_content)
    """
    # Render city map for main area
    main_content = render_city_map(
        districts=view_data["districts"],
        focus_data=view_data["focus_data"],
        selected_id=view_data.get("selected_id"),
        overlay=view_data.get("overlay"),
    )

    # Render context panel
    context_content = render_context_panel(
        entity_type=view_data.get("selected_entity_type"),
        entity_data=view_data.get("selected_entity_data"),
    )

    return main_content, context_content
