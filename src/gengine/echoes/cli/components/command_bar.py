"""Command bar component showing available actions."""

from __future__ import annotations

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def render_command_bar(active_command: str | None = None) -> Panel:
    """Render the command bar showing available actions.

    Args:
        active_command: Currently active/executing command (highlighted)

    Returns:
        Rich Panel with command bar content
    """
    commands = [
        ("▶ Next", "n"),
        ("▶▶ Run", "r"),
        ("🎯 Focus", "f"),
        ("💾 Save", "s"),
        ("❓ Why", "?"),
        ("☰ Menu", "m"),
    ]

    table = Table.grid(padding=(0, 2))

    row_texts = []
    for label, shortcut in commands:
        if active_command and shortcut in active_command.lower():
            style = "bold cyan"
        else:
            style = "white"

        text = Text()
        text.append(label, style=style)
        text.append(f" ({shortcut})", style="dim")
        row_texts.append(text)

    table.add_row(*row_texts)

    return Panel(
        Align.center(table),
        border_style="white",
        height=3,
    )
