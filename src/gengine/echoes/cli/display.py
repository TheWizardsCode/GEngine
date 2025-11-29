"""Enhanced ASCII display utilities using Rich formatting.

This module provides richer visualization for CLI and gateway outputs with
tables, panels, and styled text using the Rich library.
"""

from __future__ import annotations

from io import StringIO
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def render_summary_table(summary: dict[str, Any]) -> str:
    """Render world summary as a formatted table with panels."""
    console = Console(file=StringIO(), force_terminal=True, width=80)
    
    # Core stats table
    stats_table = Table(title="World Status", show_header=True, header_style="bold cyan")
    stats_table.add_column("Metric", style="cyan", width=15)
    stats_table.add_column("Value", style="yellow", width=20)
    
    for key in ("city", "tick", "districts", "factions", "agents"):
        stats_table.add_row(key.capitalize(), str(summary.get(key, "N/A")))
    
    stability = summary.get("stability")
    if isinstance(stability, (int, float)):
        stab_color = "green" if stability >= 0.7 else "yellow" if stability >= 0.4 else "red"
        stats_table.add_row("Stability", f"[{stab_color}]{stability:.3f}[/{stab_color}]")
    
    console.print(stats_table)
    console.print()
    
    # Environment impact panel
    impact = summary.get("environment_impact")
    if isinstance(impact, dict) and impact:
        _render_environment_panel(console, impact)
        console.print()
    
    # Focus state panel
    focus = summary.get("focus")
    if isinstance(focus, dict) and focus.get("district_id"):
        _render_focus_panel(console, focus)
        console.print()
    
    # Focus digest panel
    digest = summary.get("focus_digest")
    if isinstance(digest, dict) and digest.get("visible"):
        _render_digest_panel(console, digest)
        console.print()
    
    # Story seeds panel
    seeds = summary.get("story_seeds")
    if isinstance(seeds, list) and seeds:
        _render_story_seeds_panel(console, seeds)
        console.print()
    
    # Profiling panel
    profiling = summary.get("profiling")
    if isinstance(profiling, dict) and profiling:
        _render_profiling_panel(console, profiling)
    
    return console.file.getvalue()


def _render_environment_panel(console: Console, impact: dict[str, Any]) -> None:
    """Render environment impact as a styled panel."""
    lines = []
    
    pressure = impact.get("scarcity_pressure", 0.0)
    pressure_color = "red" if pressure > 2.0 else "yellow" if pressure > 1.0 else "green"
    lines.append(f"[bold]Scarcity Pressure:[/bold] [{pressure_color}]{pressure:.2f}[/{pressure_color}]")
    
    if impact.get("diffusion_applied"):
        lines.append("[dim]Diffusion: active[/dim]")
    
    avg_pollution = impact.get("average_pollution")
    if isinstance(avg_pollution, (int, float)):
        poll_color = "red" if avg_pollution > 0.7 else "yellow" if avg_pollution > 0.4 else "green"
        lines.append(f"[bold]Avg Pollution:[/bold] [{poll_color}]{avg_pollution:.3f}[/{poll_color}]")
    
    extremes = impact.get("extremes") or {}
    if isinstance(extremes, dict) and extremes:
        max_info = extremes.get("max") or {}
        min_info = extremes.get("min") or {}
        if max_info and min_info:
            lines.append(
                f"[bold]Extremes:[/bold] "
                f"max [red]{max_info.get('district')}[/red] {float(max_info.get('pollution', 0.0)):.3f}, "
                f"min [green]{min_info.get('district')}[/green] {float(min_info.get('pollution', 0.0)):.3f}"
            )
    
    biodiversity = impact.get("biodiversity") or {}
    if isinstance(biodiversity, dict) and biodiversity.get("value") is not None:
        value = biodiversity.get("value")
        if isinstance(value, (int, float)):
            bio_color = "green" if value > 0.7 else "yellow" if value > 0.5 else "red"
            delta = biodiversity.get("delta", 0.0)
            delta_text = f" ({delta:+.3f})" if abs(delta) >= 1e-4 else ""
            lines.append(f"[bold]Biodiversity:[/bold] [{bio_color}]{value:.3f}{delta_text}[/{bio_color}]")
    
    panel = Panel("\n".join(lines), title="[bold cyan]Environment Impact[/bold cyan]", border_style="cyan")
    console.print(panel)


def _render_focus_panel(console: Console, focus: dict[str, Any]) -> None:
    """Render focus state as a styled panel."""
    lines = []
    
    district_id = focus.get("district_id", "")
    lines.append(f"[bold yellow]Center:[/bold yellow] {district_id}")
    
    neighbors = focus.get("neighbors") or []
    if neighbors:
        lines.append(f"[bold]Neighbors:[/bold] {', '.join(neighbors)}")
    
    coords = focus.get("coordinates")
    if coords:
        coord_str = f"({coords.get('x', 0):.1f}, {coords.get('y', 0):.1f}"
        if coords.get('z') is not None:
            coord_str += f", {coords.get('z', 0):.1f}"
        coord_str += ")"
        lines.append(f"[bold]Coords:[/bold] {coord_str}")
    
    adjacent = focus.get("adjacent") or []
    if adjacent:
        lines.append(f"[dim]Adjacent:[/dim] {', '.join(adjacent)}")
    
    weights = focus.get("spatial_weights") or []
    if weights:
        weight_strs = [
            f"{entry['district_id']}:[cyan]{entry.get('score', 0.0):.2f}[/cyan]"
            for entry in weights[:3]
        ]
        lines.append(f"[bold]Spatial Weights:[/bold] {', '.join(weight_strs)}")
    
    panel = Panel("\n".join(lines), title="[bold magenta]Focus State[/bold magenta]", border_style="magenta")
    console.print(panel)


def _render_digest_panel(console: Console, digest: dict[str, Any]) -> None:
    """Render focus digest as a styled panel."""
    lines = []
    
    visible = digest.get("visible", [])
    for i, event in enumerate(visible[:3], 1):
        lines.append(f"{i}. {event}")
    
    suppressed = digest.get("suppressed_count", 0)
    if suppressed:
        lines.append(f"\n[dim italic]({suppressed} archived events)[/dim italic]")
    
    ranked = digest.get("ranked_archive") or []
    if ranked and len(ranked) > 0:
        lines.append(f"\n[bold]Top Ranked:[/bold]")
        for entry in ranked[:2]:
            score = entry.get("score", 0.0)
            message = entry.get("message", "")
            lines.append(f"  • [{score:.2f}] {message}")
    
    panel = Panel("\n".join(lines), title="[bold green]Focus Digest[/bold green]", border_style="green")
    console.print(panel)


def _render_story_seeds_panel(console: Console, seeds: list[dict[str, Any]]) -> None:
    """Render active story seeds as a styled table."""
    table = Table(title="Active Story Seeds", show_header=True, header_style="bold yellow")
    table.add_column("Seed", style="yellow", width=25)
    table.add_column("Title", style="white", width=30)
    table.add_column("Status", style="cyan", width=15)
    
    for seed in seeds[:5]:
        seed_id = seed.get("seed_id", "unknown")
        title = seed.get("title", "Untitled")
        cooldown = seed.get("cooldown_remaining", 0)
        status = f"cooling ({cooldown})" if cooldown > 0 else "active"
        status_color = "yellow" if cooldown > 0 else "green"
        
        table.add_row(
            seed_id,
            title,
            f"[{status_color}]{status}[/{status_color}]"
        )
    
    console.print(table)


def _render_profiling_panel(console: Console, profiling: dict[str, Any]) -> None:
    """Render profiling metrics as a styled table."""
    table = Table(title="Performance Metrics", show_header=True, header_style="bold blue")
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="yellow", width=15)
    
    for key in ("tick_ms_p50", "tick_ms_p95", "tick_ms_max"):
        value = profiling.get(key)
        if value is not None:
            table.add_row(key, f"{value:.2f}ms")
    
    slowest = profiling.get("slowest_subsystems") or []
    if slowest:
        table.add_row("", "")  # Spacer
        table.add_row("[bold]Slowest Subsystems[/bold]", "")
        for entry in slowest[:3]:
            name = entry.get("name", "")
            ms = entry.get("ms", 0.0)
            table.add_row(f"  {name}", f"{ms:.2f}ms")
    
    anomalies = profiling.get("anomaly_count", 0)
    if anomalies > 0:
        table.add_row("", "")  # Spacer
        anom_color = "red" if anomalies > 100 else "yellow"
        table.add_row("[bold]Anomalies[/bold]", f"[{anom_color}]{anomalies}[/{anom_color}]")
    
    console.print(table)


def render_director_table(feed: dict[str, Any], history: list[dict[str, Any]] | None, analysis: dict[str, Any] | None) -> str:
    """Render director feed and analysis as formatted tables."""
    console = Console(file=StringIO(), force_terminal=True, width=80)
    
    # Current feed panel
    if feed:
        lines = []
        lines.append(f"[bold]Tick:[/bold] {feed.get('tick', 0)}")
        
        focus_center = feed.get('focus_center')
        if focus_center:
            lines.append(f"[bold]Focus:[/bold] {focus_center}")
        
        suppressed = feed.get('suppressed_count', 0)
        if suppressed:
            lines.append(f"[dim]Suppressed: {suppressed}[/dim]")
        
        panel = Panel("\n".join(lines), title="[bold cyan]Current Director Feed[/bold cyan]", border_style="cyan")
        console.print(panel)
        console.print()
    
    # Director events table
    if analysis:
        events = analysis.get("director_events") or []
        if events:
            table = Table(title="Director Events", show_header=True, header_style="bold yellow")
            table.add_column("Seed", style="yellow", width=20)
            table.add_column("Title", style="white", width=25)
            table.add_column("District", style="cyan", width=20)
            table.add_column("Tick", style="dim", width=8)
            
            for event in events[:5]:
                table.add_row(
                    event.get("seed_id", ""),
                    event.get("title", ""),
                    event.get("district_id", ""),
                    str(event.get("tick", 0))
                )
            
            console.print(table)
            console.print()
    
    # History table
    if history:
        table = Table(title="Focus History", show_header=True, header_style="bold magenta")
        table.add_column("Tick", style="dim", width=8)
        table.add_column("Center", style="cyan", width=20)
        table.add_column("Suppressed", style="yellow", width=12)
        table.add_column("Top Events", style="white", width=30)
        
        for entry in history[-5:]:
            tick = entry.get("tick", 0)
            center = entry.get("focus_center", "")
            suppressed = entry.get("suppressed_count", 0)
            
            top_ranked = entry.get("top_ranked") or []
            top_msg = top_ranked[0].get("message", "") if top_ranked else ""
            if len(top_msg) > 27:
                top_msg = top_msg[:27] + "..."
            
            table.add_row(
                str(tick),
                center,
                str(suppressed),
                top_msg
            )
        
        console.print(table)
    
    return console.file.getvalue()


def render_map_overlay(summary: dict[str, Any]) -> str:
    """Render enhanced map with district overlays in a styled format."""
    console = Console(file=StringIO(), force_terminal=True, width=100)
    
    console.print(Panel("[bold cyan]City Map Overview[/bold cyan]", border_style="cyan"))
    console.print()
    
    # District status table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("District", style="cyan", width=25)
    table.add_column("Population", style="yellow", width=12)
    table.add_column("Pollution", style="white", width=12)
    table.add_column("Unrest", style="white", width=12)
    table.add_column("Status", style="green", width=15)
    
    # Note: This is a placeholder - real implementation would extract district data
    # from the full state snapshot
    table.add_row(
        "Industrial Tier",
        "120,000",
        "[red]0.85[/red]",
        "[yellow]0.45[/yellow]",
        "[green]Stable[/green]"
    )
    table.add_row(
        "Research Spire",
        "45,000",
        "[green]0.25[/green]",
        "[green]0.15[/green]",
        "[green]Stable[/green]"
    )
    table.add_row(
        "Perimeter Hollow",
        "200,000",
        "[yellow]0.55[/yellow]",
        "[red]0.75[/red]",
        "[yellow]Tense[/yellow]"
    )
    
    console.print(table)
    console.print()
    
    # Geometry overlay info
    focus = summary.get("focus")
    if isinstance(focus, dict) and focus.get("district_id"):
        coords = focus.get("coordinates")
        if coords:
            console.print(f"[bold]Focus Center:[/bold] {focus.get('district_id')} at ({coords.get('x', 0):.1f}, {coords.get('y', 0):.1f})")
            
            adjacent = focus.get("adjacent") or []
            if adjacent:
                console.print(f"[dim]Adjacent districts: {', '.join(adjacent)}[/dim]")
    
    return console.file.getvalue()
