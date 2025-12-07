"""Balance Studio - Designer feedback loop and tooling.

This module provides guided workflows for designers to iterate on game
balance without requiring code changes.

Components
----------
- overlays: YAML overlay system for configuration testing
- workflows: Guided workflow implementations
- report_viewer: Interactive HTML report generation

CLI Tool
--------
The `echoes-balance-studio` CLI provides an interactive interface::

    echoes-balance-studio

Or use specific commands::

    echoes-balance-studio sweep --strategies balanced aggressive
    echoes-balance-studio compare --config-a path/to/a --config-b path/to/b
    echoes-balance-studio test-tuning --changes economy.regen_scale=1.2
    echoes-balance-studio view-reports
"""

from .overlays import (
    ConfigOverlay,
    create_tuning_overlay,
    deep_merge,
    load_overlay_directory,
    merge_overlays,
)
from .report_viewer import (
    FilterState,
    ReportViewerConfig,
    generate_interactive_html,
    write_html_report,
)
from .workflows import (
    CompareConfigsConfig,
    ExploratorySweepConfig,
    TuningTestConfig,
    WorkflowResult,
    get_workflow_menu,
    list_historical_reports,
    run_config_comparison,
    run_exploratory_sweep,
    run_tuning_test,
    view_historical_report,
)

__all__ = [
    # Overlays
    "ConfigOverlay",
    "create_tuning_overlay",
    "deep_merge",
    "load_overlay_directory",
    "merge_overlays",
    # Report Viewer
    "FilterState",
    "ReportViewerConfig",
    "generate_interactive_html",
    "write_html_report",
    # Workflows
    "CompareConfigsConfig",
    "ExploratorySweepConfig",
    "TuningTestConfig",
    "WorkflowResult",
    "get_workflow_menu",
    "list_historical_reports",
    "run_config_comparison",
    "run_exploratory_sweep",
    "run_tuning_test",
    "view_historical_report",
]
