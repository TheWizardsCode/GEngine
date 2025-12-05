"""Interactive HTML report viewer for balance analysis.

Generates an HTML dashboard that allows filtering, sorting, and drilling
into sweep results without requiring code changes.
"""

from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Optional matplotlib import
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class ReportViewerConfig:
    """Configuration for the report viewer.

    Attributes
    ----------
    title
        Title for the HTML report.
    include_charts
        Whether to include embedded charts.
    include_raw_data
        Whether to include raw JSON data section.
    theme
        Color theme: "light" or "dark".
    """

    title: str = "Balance Studio Report"
    include_charts: bool = True
    include_raw_data: bool = False
    theme: str = "light"


@dataclass
class FilterState:
    """Current filter state for the report viewer.

    Attributes
    ----------
    strategies
        Selected strategies to display.
    difficulties
        Selected difficulties to display.
    min_stability
        Minimum stability threshold.
    max_stability
        Maximum stability threshold.
    show_errors
        Whether to show failed sweeps.
    """

    strategies: list[str] = field(default_factory=list)
    difficulties: list[str] = field(default_factory=list)
    min_stability: float = 0.0
    max_stability: float = 1.0
    show_errors: bool = True


def generate_strategy_chart(stats: dict[str, Any]) -> str | None:
    """Generate a bar chart of average stability by strategy.

    Parameters
    ----------
    stats
        Strategy statistics from sweep results.

    Returns
    -------
    str | None
        Base64-encoded PNG image, or None if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB or not stats:
        return None

    strategies = list(stats.keys())
    avg_stabilities = [stats[s].get("avg_stability", 0) for s in strategies]

    # Generate colors dynamically based on number of strategies
    base_colors = ["#3498db", "#e74c3c", "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c"]
    colors = [base_colors[i % len(base_colors)] for i in range(len(strategies))]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(strategies, avg_stabilities, color=colors)

    ax.set_xlabel("Strategy")
    ax.set_ylabel("Average Stability")
    ax.set_title("Strategy Performance Comparison")
    ax.set_ylim(0, 1)

    for bar, val in zip(bars, avg_stabilities, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.02,
            f"{val:.2f}",
            ha="center",
            fontsize=10,
        )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_difficulty_chart(stats: dict[str, Any]) -> str | None:
    """Generate a bar chart of average stability by difficulty.

    Parameters
    ----------
    stats
        Difficulty statistics from sweep results.

    Returns
    -------
    str | None
        Base64-encoded PNG image, or None if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB or not stats:
        return None

    difficulties = list(stats.keys())
    avg_stabilities = [stats[d].get("avg_stability", 0) for d in difficulties]

    # Color gradient from easy (green) to hard (red)
    colors = plt.cm.RdYlGn(
        [1.0 - i / max(len(difficulties) - 1, 1) for i in range(len(difficulties))]
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(difficulties, avg_stabilities, color=colors)

    ax.set_xlabel("Difficulty")
    ax.set_ylabel("Average Stability")
    ax.set_title("Difficulty Level Impact")
    ax.set_ylim(0, 1)

    for bar, val in zip(bars, avg_stabilities, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.02,
            f"{val:.2f}",
            ha="center",
            fontsize=10,
        )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_stability_distribution_chart(sweeps: list[dict[str, Any]]) -> str | None:
    """Generate a histogram of stability distribution.

    Parameters
    ----------
    sweeps
        List of sweep results.

    Returns
    -------
    str | None
        Base64-encoded PNG image, or None if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB or not sweeps:
        return None

    stabilities = [
        s.get("results", {}).get("final_stability", 0)
        for s in sweeps
        if s.get("error") is None
    ]

    if not stabilities:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(stabilities, bins=20, edgecolor="white", color="#3498db", alpha=0.7)

    ax.set_xlabel("Final Stability")
    ax.set_ylabel("Count")
    ax.set_title("Stability Distribution Across All Sweeps")
    ax.axvline(0.5, color="red", linestyle="--", label="Win Threshold")
    ax.legend()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_interactive_html(
    data: dict[str, Any],
    config: ReportViewerConfig | None = None,
) -> str:
    """Generate an interactive HTML report from sweep data.

    Parameters
    ----------
    data
        Sweep results data (from batch_sweep_summary.json).
    config
        Report viewer configuration.

    Returns
    -------
    str
        Complete HTML document.
    """
    if config is None:
        config = ReportViewerConfig()

    # Generate charts
    charts: dict[str, str | None] = {}
    if config.include_charts:
        charts["strategy"] = generate_strategy_chart(data.get("strategy_stats", {}))
        charts["difficulty"] = generate_difficulty_chart(
            data.get("difficulty_stats", {})
        )
        charts["distribution"] = generate_stability_distribution_chart(
            data.get("sweeps", [])
        )

    # Extract unique values for filters
    sweeps = data.get("sweeps", [])
    strategies = sorted(
        set(s.get("parameters", {}).get("strategy", "") for s in sweeps)
    )
    difficulties = sorted(
        set(s.get("parameters", {}).get("difficulty", "") for s in sweeps)
    )

    # Build HTML
    theme_colors = _get_theme_colors(config.theme)
    metadata = data.get("metadata", {})
    strategy_stats = data.get("strategy_stats", {})
    difficulty_stats = data.get("difficulty_stats", {})

    # CSS styles (broken into lines for readability)
    font_family = (
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    )
    section_h2_style = (
        "margin-top: 0; border-bottom: 1px solid var(--border-color); "
        "padding-bottom: 10px"
    )
    details_style = (
        "display: none; padding: 10px; background: rgba(0,0,0,0.05); "
        "margin-top: 10px; border-radius: 4px"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.title}</title>
    <style>
        :root {{
            --bg-color: {theme_colors['bg']};
            --text-color: {theme_colors['text']};
            --card-bg: {theme_colors['card']};
            --border-color: {theme_colors['border']};
            --accent-color: #3498db;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: {font_family};
            background: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--border-color);
        }}
        h1 {{ margin: 0; color: var(--accent-color); }}
        .meta {{ font-size: 0.9em; opacity: 0.7; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em; font-weight: bold; color: var(--accent-color);
        }}
        .stat-label {{ font-size: 0.9em; opacity: 0.7; }}
        .section {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section h2 {{ {section_h2_style}; }}
        .filters {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .filter-group {{ display: flex; flex-direction: column; gap: 5px; }}
        .filter-group label {{ font-weight: bold; font-size: 0.9em; }}
        select, input[type="number"] {{
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{ background: var(--accent-color); color: white; cursor: pointer; }}
        th:hover {{ opacity: 0.9; }}
        tr:hover {{ background: rgba(52, 152, 219, 0.1); }}
        .status-ok {{ color: var(--success-color); }}
        .status-warn {{ color: var(--warning-color); }}
        .status-err {{ color: var(--danger-color); }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{
            max-width: 100%; height: auto; border-radius: 8px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        .expand-btn {{
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .details {{ {details_style}; }}
        .details.show {{ display: block; }}
        pre {{ overflow-x: auto; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <div>
            <h1>{config.title}</h1>
            <div class="meta">
                Generated: {metadata.get('timestamp', 'Unknown')} |
                Git: {metadata.get('git_commit', 'N/A')}
            </div>
        </div>
    </header>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{data.get('total_sweeps', 0)}</div>
            <div class="stat-label">Total Sweeps</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{data.get('completed_sweeps', 0)}</div>
            <div class="stat-label">Completed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{data.get('failed_sweeps', 0)}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{data.get('total_duration_seconds', 0):.1f}s</div>
            <div class="stat-label">Total Duration</div>
        </div>
    </div>

    <div class="section">
        <h2>Strategy Performance</h2>
        <table id="strategy-table">
            <thead>
                <tr>
                    <th onclick="sortTable('strategy-table', 0)">Strategy</th>
                    <th onclick="sortTable('strategy-table', 1)">Count</th>
                    <th onclick="sortTable('strategy-table', 2)">Completed</th>
                    <th onclick="sortTable('strategy-table', 3)">Avg Stability</th>
                    <th onclick="sortTable('strategy-table', 4)">Min</th>
                    <th onclick="sortTable('strategy-table', 5)">Max</th>
                </tr>
            </thead>
            <tbody>
                {_generate_strategy_rows(strategy_stats)}
            </tbody>
        </table>
        {_generate_chart_section(charts.get('strategy'), 'Strategy Comparison')}
    </div>

    <div class="section">
        <h2>Difficulty Analysis</h2>
        <table id="difficulty-table">
            <thead>
                <tr>
                    <th onclick="sortTable('difficulty-table', 0)">Difficulty</th>
                    <th onclick="sortTable('difficulty-table', 1)">Count</th>
                    <th onclick="sortTable('difficulty-table', 2)">Completed</th>
                    <th onclick="sortTable('difficulty-table', 3)">Avg Stability</th>
                    <th onclick="sortTable('difficulty-table', 4)">Min</th>
                    <th onclick="sortTable('difficulty-table', 5)">Max</th>
                </tr>
            </thead>
            <tbody>
                {_generate_difficulty_rows(difficulty_stats)}
            </tbody>
        </table>
        {_generate_chart_section(charts.get('difficulty'), 'Difficulty Impact')}
    </div>

    {_generate_distribution_section(charts.get('distribution'))}

    <div class="section">
        <h2>Individual Sweeps</h2>
        <div class="filters">
            <div class="filter-group">
                <label for="filter-strategy">Strategy</label>
                <select id="filter-strategy" onchange="filterTable()">
                    <option value="">All</option>
                    {_generate_options(strategies)}
                </select>
            </div>
            <div class="filter-group">
                <label for="filter-difficulty">Difficulty</label>
                <select id="filter-difficulty" onchange="filterTable()">
                    <option value="">All</option>
                    {_generate_options(difficulties)}
                </select>
            </div>
            <div class="filter-group">
                <label for="filter-min-stability">Min Stability</label>
                <input type="number" id="filter-min-stability"
                       value="0" min="0" max="1" step="0.1"
                       onchange="filterTable()">
            </div>
        </div>
        <table id="sweeps-table">
            <thead>
                <tr>
                    <th onclick="sortTable('sweeps-table', 0)">ID</th>
                    <th onclick="sortTable('sweeps-table', 1)">Strategy</th>
                    <th onclick="sortTable('sweeps-table', 2)">Difficulty</th>
                    <th onclick="sortTable('sweeps-table', 3)">Seed</th>
                    <th onclick="sortTable('sweeps-table', 4)">Stability</th>
                    <th onclick="sortTable('sweeps-table', 5)">Actions</th>
                    <th onclick="sortTable('sweeps-table', 6)">Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {_generate_sweep_rows(sweeps)}
            </tbody>
        </table>
    </div>

    {_generate_raw_data_section(data) if config.include_raw_data else ''}
</div>

<script>
function sortTable(tableId, colIndex) {{
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    const isNumeric = !isNaN(parseFloat(rows[0]?.cells[colIndex]?.textContent));

    rows.sort((a, b) => {{
        const aVal = a.cells[colIndex]?.textContent || '';
        const bVal = b.cells[colIndex]?.textContent || '';

        if (isNumeric) {{
            return parseFloat(bVal) - parseFloat(aVal);
        }}
        return aVal.localeCompare(bVal);
    }});

    rows.forEach(row => tbody.appendChild(row));
}}

function filterTable() {{
    const strategy = document.getElementById('filter-strategy').value;
    const difficulty = document.getElementById('filter-difficulty').value;
    const minStabEl = document.getElementById('filter-min-stability');
    const minStability = parseFloat(minStabEl.value) || 0;

    const rows = document.querySelectorAll('#sweeps-table tbody tr');
    rows.forEach(row => {{
        const rowStrategy = row.cells[1]?.textContent || '';
        const rowDifficulty = row.cells[2]?.textContent || '';
        const rowStability = parseFloat(row.cells[4]?.textContent) || 0;

        const show = (strategy === '' || rowStrategy === strategy) &&
                     (difficulty === '' || rowDifficulty === difficulty) &&
                     (rowStability >= minStability);

        row.style.display = show ? '' : 'none';
    }});
}}

function toggleDetails(id) {{
    const el = document.getElementById('details-' + id);
    el.classList.toggle('show');
}}
</script>
</body>
</html>"""

    return html


def _get_theme_colors(theme: str) -> dict[str, str]:
    """Get color scheme for theme."""
    if theme == "dark":
        return {
            "bg": "#1a1a2e",
            "text": "#eee",
            "card": "#16213e",
            "border": "#0f3460",
        }
    return {
        "bg": "#f5f6fa",
        "text": "#2c3e50",
        "card": "#ffffff",
        "border": "#dcdde1",
    }


def _generate_strategy_rows(stats: dict[str, Any]) -> str:
    """Generate table rows for strategy stats."""
    rows = []
    for strategy, s in stats.items():
        avg = s.get("avg_stability", 0)
        status_class = "status-ok" if avg >= 0.5 else "status-warn"
        rows.append(
            f"""<tr>
            <td>{strategy}</td>
            <td>{s.get('count', 0)}</td>
            <td>{s.get('completed', 0)}</td>
            <td class="{status_class}">{avg:.3f}</td>
            <td>{s.get('min_stability', 0):.3f}</td>
            <td>{s.get('max_stability', 0):.3f}</td>
        </tr>"""
        )
    return "\n".join(rows)


def _generate_difficulty_rows(stats: dict[str, Any]) -> str:
    """Generate table rows for difficulty stats."""
    rows = []
    for difficulty, s in stats.items():
        avg = s.get("avg_stability", 0)
        status_class = "status-ok" if avg >= 0.5 else "status-warn"
        rows.append(
            f"""<tr>
            <td>{difficulty}</td>
            <td>{s.get('count', 0)}</td>
            <td>{s.get('completed', 0)}</td>
            <td class="{status_class}">{avg:.3f}</td>
            <td>{s.get('min_stability', 0):.3f}</td>
            <td>{s.get('max_stability', 0):.3f}</td>
        </tr>"""
        )
    return "\n".join(rows)


def _generate_sweep_rows(sweeps: list[dict[str, Any]]) -> str:
    """Generate table rows for individual sweeps."""
    rows = []
    for sweep in sweeps:
        sweep_id = sweep.get("sweep_id", "?")
        params = sweep.get("parameters", {})
        results = sweep.get("results", {})
        error = sweep.get("error")

        stability = results.get("final_stability", 0)
        if error:
            status = '<span class="status-err">Error</span>'
        elif stability >= 0.5:
            status = '<span class="status-ok">Pass</span>'
        else:
            status = '<span class="status-warn">Low</span>'

        strategy = params.get('strategy', '')
        difficulty = params.get('difficulty', '')
        btn = f'<button class="expand-btn" onclick="toggleDetails({sweep_id})">'
        rows.append(
            f"""<tr data-strategy="{strategy}" data-difficulty="{difficulty}">
            <td>{sweep_id}</td>
            <td>{params.get('strategy', 'N/A')}</td>
            <td>{params.get('difficulty', 'N/A')}</td>
            <td>{params.get('seed', 'N/A')}</td>
            <td>{stability:.3f}</td>
            <td>{results.get('actions_taken', 0)}</td>
            <td>{status}</td>
            <td>
                {btn}View</button>
                <div id="details-{sweep_id}" class="details">
                    <pre>{json.dumps(sweep, indent=2)[:500]}...</pre>
                </div>
            </td>
        </tr>"""
        )
    return "\n".join(rows)


def _generate_options(values: list[str]) -> str:
    """Generate select options."""
    return "\n".join(f'<option value="{v}">{v}</option>' for v in values)


def _generate_chart_section(chart_data: str | None, title: str) -> str:
    """Generate chart section HTML."""
    if not chart_data:
        return ""
    return f"""
    <div class="chart-container">
        <img src="data:image/png;base64,{chart_data}" alt="{title}">
    </div>
    """


def _generate_distribution_section(chart_data: str | None) -> str:
    """Generate distribution chart section."""
    if not chart_data:
        return ""
    return f"""
    <div class="section">
        <h2>Stability Distribution</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,{chart_data}" alt="Stability Distribution">
        </div>
    </div>
    """


def _generate_raw_data_section(data: dict[str, Any]) -> str:
    """Generate raw data section."""
    return f"""
    <div class="section">
        <h2>Raw Data</h2>
        <pre>{json.dumps(data, indent=2)}</pre>
    </div>
    """


def write_html_report(
    data: dict[str, Any],
    output_path: Path,
    config: ReportViewerConfig | None = None,
) -> None:
    """Write an HTML report to file.

    Parameters
    ----------
    data
        Sweep results data.
    output_path
        Path to write HTML file.
    config
        Report viewer configuration.
    """
    html = generate_interactive_html(data, config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
