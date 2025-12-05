#!/usr/bin/env python3
"""Balance Studio CLI - Designer feedback loop and guided workflows.

Provides an interactive interface for designers to iterate on game balance
without requiring code changes.

Examples
--------
Run interactively::

    echoes-balance-studio

Run a specific workflow::

    echoes-balance-studio sweep --strategies balanced aggressive
    echoes-balance-studio compare --config-a path/to/a --config-b path/to/b
    echoes-balance-studio test-tuning --name "boost_regen" \\
        --change economy.regen_scale=1.2
    echoes-balance-studio view-reports
    echoes-balance-studio generate-report --input build/sweeps/summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from gengine.balance_studio import (
    CompareConfigsConfig,
    ConfigOverlay,
    ExploratorySweepConfig,
    ReportViewerConfig,
    TuningTestConfig,
    get_workflow_menu,
    list_historical_reports,
    run_config_comparison,
    run_exploratory_sweep,
    run_tuning_test,
    view_historical_report,
    write_html_report,
)


def print_header() -> None:
    """Print the Balance Studio header."""
    print()
    print("=" * 60)
    print("  ECHOES BALANCE STUDIO")
    print("  Designer Feedback Loop and Tooling")
    print("=" * 60)
    print()


def print_workflow_menu() -> None:
    """Print the workflow menu."""
    workflows = get_workflow_menu()
    print("Available Workflows:")
    print("-" * 40)
    for i, w in enumerate(workflows, 1):
        print(f"  {i}. {w['name']}")
        print(f"     {w['description']}")
        print()


def interactive_mode() -> int:
    """Run the interactive workflow selection mode.

    Returns
    -------
    int
        Exit code.
    """
    print_header()
    print_workflow_menu()

    print("Enter workflow number (1-4) or 'q' to quit:")
    try:
        choice = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        return 0

    if choice in ("q", "quit", "exit"):
        return 0

    try:
        choice_num = int(choice)
    except ValueError:
        print(f"Invalid choice: {choice}")
        return 1

    if choice_num == 1:
        return interactive_sweep()
    elif choice_num == 2:
        return interactive_compare()
    elif choice_num == 3:
        return interactive_tuning()
    elif choice_num == 4:
        return interactive_view_reports()
    else:
        print(f"Invalid choice: {choice_num}")
        return 1


def interactive_sweep() -> int:
    """Interactive exploratory sweep workflow."""
    print("\n--- Run Exploratory Sweep ---\n")

    print("Enter strategies (comma-separated, or press Enter for defaults):")
    print("  Available: balanced, aggressive, diplomatic, hybrid")
    strategies_input = input("> ").strip()
    strategies = (
        [s.strip() for s in strategies_input.split(",") if s.strip()]
        if strategies_input
        else ["balanced", "aggressive", "diplomatic"]
    )

    print("\nEnter difficulty presets (comma-separated, or Enter for 'normal'):")
    print("  Available: tutorial, easy, normal, hard, brutal")
    difficulties_input = input("> ").strip()
    difficulties = (
        [d.strip() for d in difficulties_input.split(",") if d.strip()]
        if difficulties_input
        else ["normal"]
    )

    print("\nEnter random seeds (comma-separated, or Enter for defaults):")
    seeds_input = input("> ").strip()
    try:
        seeds = (
            [int(s.strip()) for s in seeds_input.split(",") if s.strip()]
            if seeds_input
            else [42, 123, 456]
        )
    except ValueError:
        print("Invalid seeds, using defaults")
        seeds = [42, 123, 456]

    print("\nEnter tick budget (or Enter for 100):")
    tick_input = input("> ").strip()
    tick_budget = int(tick_input) if tick_input else 100

    config = ExploratorySweepConfig(
        strategies=strategies,
        difficulties=difficulties,
        seeds=seeds,
        tick_budget=tick_budget,
    )

    print(f"\nRunning sweep with {len(strategies)} strategies, "
          f"{len(difficulties)} difficulties, {len(seeds)} seeds...")
    print("This may take a while...\n")

    result = run_exploratory_sweep(config, verbose=True)

    print("\n" + "=" * 40)
    if result.success:
        print(f"SUCCESS: {result.message}")
        print(f"Output: {result.output_path}")
    else:
        print(f"FAILED: {result.message}")
        for err in result.errors:
            print(f"  Error: {err}")

    return 0 if result.success else 1


def interactive_compare() -> int:
    """Interactive config comparison workflow."""
    print("\n--- Compare Two Configs ---\n")

    print("Enter path to first config directory:")
    config_a = input("> ").strip()
    if not config_a:
        print("Config path required")
        return 1

    print("\nEnter name for first config (or Enter for 'Config A'):")
    name_a = input("> ").strip() or "Config A"

    print("\nEnter path to second config directory:")
    config_b = input("> ").strip()
    if not config_b:
        print("Config path required")
        return 1

    print("\nEnter name for second config (or Enter for 'Config B'):")
    name_b = input("> ").strip() or "Config B"

    config = CompareConfigsConfig(
        config_a_path=Path(config_a),
        config_b_path=Path(config_b),
        name_a=name_a,
        name_b=name_b,
    )

    print("\nRunning comparison sweeps...")

    result = run_config_comparison(config, verbose=True)

    print("\n" + "=" * 40)
    if result.success:
        print(f"SUCCESS: {result.message}")
        print(f"Output: {result.output_path}")

        if "comparison" in result.data:
            print("\nComparison Results:")
            for strategy, comp in result.data["comparison"].items():
                delta = comp.get("delta", 0)
                direction = "↑" if delta > 0 else "↓" if delta < 0 else "="
                print(f"  {strategy}: {direction} {abs(delta):.3f} "
                      f"({comp.get('delta_percent', 0):.1f}%)")
    else:
        print(f"FAILED: {result.message}")
        for err in result.errors:
            print(f"  Error: {err}")

    return 0 if result.success else 1


def interactive_tuning() -> int:
    """Interactive tuning test workflow."""
    print("\n--- Test Tuning Change ---\n")

    print("Enter a name for this tuning experiment:")
    name = input("> ").strip()
    if not name:
        name = "tuning_test"

    print("\nEnter config changes as key=value pairs (one per line, blank to finish):")
    print("  Example: economy.regen_scale=1.2")
    print("  Example: environment.scarcity_pressure_cap=6000")

    changes: dict[str, Any] = {}
    while True:
        line = input("> ").strip()
        if not line:
            break

        if "=" not in line:
            print("  Invalid format, use key=value")
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Parse value type
        try:
            if "." in value:
                parsed_value: Any = float(value)
            else:
                parsed_value = int(value)
        except ValueError:
            if value.lower() in ("true", "false"):
                parsed_value = value.lower() == "true"
            else:
                parsed_value = value

        # Build nested dict from dotted key
        keys = key.split(".")
        current = changes
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = parsed_value
        print(f"  Added: {key} = {parsed_value}")

    if not changes:
        print("No changes specified")
        return 1

    print(f"\nTesting {len(changes)} changes...")

    config = TuningTestConfig(
        name=name,
        changes=changes,
        description=f"Interactive tuning test: {name}",
    )

    result = run_tuning_test(config, verbose=True)

    print("\n" + "=" * 40)
    if result.success:
        print(f"SUCCESS: {result.message}")
        print(f"Output: {result.output_path}")

        if "comparison" in result.data:
            print("\nTuning Impact:")
            for strategy, comp in result.data["comparison"].items():
                delta = comp.get("delta", 0)
                direction = "↑" if delta > 0 else "↓" if delta < 0 else "="
                print(f"  {strategy}: Baseline {comp.get('stability_a', 0):.3f} "
                      f"→ Tuned {comp.get('stability_b', 0):.3f} "
                      f"({direction}{abs(delta):.3f})")
    else:
        print(f"FAILED: {result.message}")
        for err in result.errors:
            print(f"  Error: {err}")

    return 0 if result.success else 1


def interactive_view_reports() -> int:
    """Interactive report viewing workflow."""
    print("\n--- View Historical Reports ---\n")

    reports = list_historical_reports()

    if not reports:
        print("No reports found in build/")
        return 0

    print("Available Reports:")
    print("-" * 60)
    for i, r in enumerate(reports[:10], 1):
        print(f"  {i}. {r['timestamp']}")
        print(f"     Sweeps: {r['completed_sweeps']}/{r['total_sweeps']}")
        print(f"     Strategies: {', '.join(r['strategies'])}")
        print()

    print("Enter report number to view (or 'q' to quit):")
    choice = input("> ").strip()

    if choice.lower() in ("q", "quit"):
        return 0

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(reports):
            report = reports[idx]
            result = view_historical_report(Path(report["path"]))

            if result.success:
                print(f"\n{result.message}")
                print(f"Path: {report['path']}")

                # Print summary
                data = result.data
                print("\nSummary:")
                print(f"  Total Sweeps: {data.get('total_sweeps', 0)}")
                print(f"  Completed: {data.get('completed_sweeps', 0)}")
                print(f"  Failed: {data.get('failed_sweeps', 0)}")

                if "strategy_stats" in data:
                    print("\nStrategy Stats:")
                    for strategy, stats in data["strategy_stats"].items():
                        avg = stats.get('avg_stability', 0)
                        print(f"  {strategy}: avg_stability={avg:.3f}")
            else:
                print(f"Failed to load report: {result.message}")
        else:
            print("Invalid report number")
    except ValueError:
        print("Invalid input")

    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    """Handle the sweep command."""
    config = ExploratorySweepConfig(
        strategies=args.strategies,
        difficulties=args.difficulties,
        seeds=args.seeds,
        tick_budget=args.ticks,
        output_dir=Path(args.output_dir),
    )

    if args.overlay:
        config.overlay = ConfigOverlay.from_yaml(Path(args.overlay))

    result = run_exploratory_sweep(config, verbose=args.verbose)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"{'SUCCESS' if result.success else 'FAILED'}: {result.message}")
        if result.output_path:
            print(f"Output: {result.output_path}")

    return 0 if result.success else 1


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle the compare command."""
    config = CompareConfigsConfig(
        config_a_path=Path(args.config_a),
        config_b_path=Path(args.config_b),
        name_a=args.name_a,
        name_b=args.name_b,
        strategies=args.strategies,
        seeds=args.seeds,
        tick_budget=args.ticks,
        output_dir=Path(args.output_dir),
    )

    result = run_config_comparison(config, verbose=args.verbose)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"{'SUCCESS' if result.success else 'FAILED'}: {result.message}")
        if result.output_path:
            print(f"Output: {result.output_path}")

    return 0 if result.success else 1


def cmd_test_tuning(args: argparse.Namespace) -> int:
    """Handle the test-tuning command."""
    # Parse changes from command line
    changes: dict[str, Any] = {}
    for change in args.change or []:
        if "=" not in change:
            sys.stderr.write(f"Invalid change format: {change}\n")
            continue

        key, value = change.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Parse value
        try:
            if "." in value:
                parsed: Any = float(value)
            else:
                parsed = int(value)
        except ValueError:
            if value.lower() in ("true", "false"):
                parsed = value.lower() == "true"
            else:
                parsed = value

        # Build nested dict
        keys = key.split(".")
        current = changes
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = parsed

    if not changes:
        sys.stderr.write("No valid changes specified\n")
        return 1

    config = TuningTestConfig(
        name=args.name,
        changes=changes,
        description=args.description or f"Tuning test: {args.name}",
        baseline_config=Path(args.baseline) if args.baseline else None,
        strategies=args.strategies,
        seeds=args.seeds,
        tick_budget=args.ticks,
        output_dir=Path(args.output_dir),
    )

    result = run_tuning_test(config, verbose=args.verbose)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"{'SUCCESS' if result.success else 'FAILED'}: {result.message}")
        if result.output_path:
            print(f"Output: {result.output_path}")

    return 0 if result.success else 1


def cmd_view_reports(args: argparse.Namespace) -> int:
    """Handle the view-reports command."""
    reports = list_historical_reports(
        reports_dir=Path(args.reports_dir),
        limit=args.limit,
    )

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        if not reports:
            print("No reports found")
            return 0

        print("\nAvailable Reports:")
        print("-" * 70)
        for r in reports:
            print(f"  {r['timestamp']} | "
                  f"{r['completed_sweeps']}/{r['total_sweeps']} sweeps | "
                  f"{', '.join(r['strategies'])}")
            print(f"    Path: {r['path']}")

    return 0


def cmd_generate_report(args: argparse.Namespace) -> int:
    """Handle the generate-report command."""
    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"Input file not found: {input_path}\n")
        return 1

    try:
        with open(input_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Failed to parse input: {e}\n")
        return 1

    config = ReportViewerConfig(
        title=args.title,
        include_charts=not args.no_charts,
        include_raw_data=args.include_raw,
        theme=args.theme,
    )

    output_path = Path(args.output)
    write_html_report(data, output_path, config)

    print(f"Report generated: {output_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for Balance Studio."""
    parser = argparse.ArgumentParser(
        description="Balance Studio - Designer feedback loop and guided workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run interactively
  echoes-balance-studio

  # Run exploratory sweep
  echoes-balance-studio sweep --strategies balanced aggressive

  # Compare two configurations
  echoes-balance-studio compare \\
      --config-a content/config \\
      --config-b content/config/sweeps/difficulty-hard

  # Test a tuning change
  echoes-balance-studio test-tuning \\
      --name boost_regen \\
      --change economy.regen_scale=1.2 \\
      --change environment.scarcity_pressure_cap=6000

  # View historical reports
  echoes-balance-studio view-reports

  # Generate HTML report from sweep results
  echoes-balance-studio generate-report \\
      --input build/batch_sweeps/batch_sweep_summary.json \\
      --output build/balance_report.html
""",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Sweep command
    sweep_parser = subparsers.add_parser(
        "sweep", help="Run an exploratory sweep"
    )
    sweep_parser.add_argument(
        "--strategies", "-s", nargs="+",
        default=["balanced", "aggressive", "diplomatic"],
        help="Strategies to test",
    )
    sweep_parser.add_argument(
        "--difficulties", "-d", nargs="+",
        default=["normal"],
        help="Difficulty presets to test",
    )
    sweep_parser.add_argument(
        "--seeds", nargs="+", type=int,
        default=[42, 123, 456],
        help="Random seeds",
    )
    sweep_parser.add_argument(
        "--ticks", "-t", type=int, default=100,
        help="Tick budget per sweep",
    )
    sweep_parser.add_argument(
        "--output-dir", "-o", default="build/studio_sweeps",
        help="Output directory",
    )
    sweep_parser.add_argument(
        "--overlay", help="Path to config overlay YAML",
    )
    sweep_parser.add_argument(
        "--json", action="store_true", help="Output as JSON",
    )
    sweep_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output",
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare two configurations"
    )
    compare_parser.add_argument(
        "--config-a", "-a", required=True,
        help="Path to first config directory",
    )
    compare_parser.add_argument(
        "--config-b", "-b", required=True,
        help="Path to second config directory",
    )
    compare_parser.add_argument(
        "--name-a", default="Config A",
        help="Display name for first config",
    )
    compare_parser.add_argument(
        "--name-b", default="Config B",
        help="Display name for second config",
    )
    compare_parser.add_argument(
        "--strategies", "-s", nargs="+", default=["balanced"],
        help="Strategies to test",
    )
    compare_parser.add_argument(
        "--seeds", nargs="+", type=int, default=[42],
        help="Random seeds",
    )
    compare_parser.add_argument(
        "--ticks", "-t", type=int, default=100,
        help="Tick budget per sweep",
    )
    compare_parser.add_argument(
        "--output-dir", "-o", default="build/studio_compare",
        help="Output directory",
    )
    compare_parser.add_argument(
        "--json", action="store_true", help="Output as JSON",
    )
    compare_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output",
    )

    # Test-tuning command
    tuning_parser = subparsers.add_parser(
        "test-tuning", help="Test a tuning change"
    )
    tuning_parser.add_argument(
        "--name", "-n", required=True,
        help="Name for this tuning experiment",
    )
    tuning_parser.add_argument(
        "--change", "-c", action="append",
        help="Config change as key=value (can be repeated)",
    )
    tuning_parser.add_argument(
        "--description", help="Description of the changes",
    )
    tuning_parser.add_argument(
        "--baseline", help="Path to baseline config directory",
    )
    tuning_parser.add_argument(
        "--strategies", "-s", nargs="+", default=["balanced"],
        help="Strategies to test",
    )
    tuning_parser.add_argument(
        "--seeds", nargs="+", type=int, default=[42, 123],
        help="Random seeds",
    )
    tuning_parser.add_argument(
        "--ticks", "-t", type=int, default=100,
        help="Tick budget per sweep",
    )
    tuning_parser.add_argument(
        "--output-dir", "-o", default="build/studio_tuning",
        help="Output directory",
    )
    tuning_parser.add_argument(
        "--json", action="store_true", help="Output as JSON",
    )
    tuning_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output",
    )

    # View-reports command
    reports_parser = subparsers.add_parser(
        "view-reports", help="View historical reports"
    )
    reports_parser.add_argument(
        "--reports-dir", default="build",
        help="Directory to search for reports",
    )
    reports_parser.add_argument(
        "--limit", "-l", type=int, default=20,
        help="Maximum reports to list",
    )
    reports_parser.add_argument(
        "--json", action="store_true", help="Output as JSON",
    )

    # Generate-report command
    generate_parser = subparsers.add_parser(
        "generate-report", help="Generate HTML report from sweep results"
    )
    generate_parser.add_argument(
        "--input", "-i", required=True,
        help="Path to sweep summary JSON",
    )
    generate_parser.add_argument(
        "--output", "-o", required=True,
        help="Output HTML file path",
    )
    generate_parser.add_argument(
        "--title", default="Balance Studio Report",
        help="Report title",
    )
    generate_parser.add_argument(
        "--theme", choices=["light", "dark"], default="light",
        help="Color theme",
    )
    generate_parser.add_argument(
        "--no-charts", action="store_true",
        help="Disable chart generation",
    )
    generate_parser.add_argument(
        "--include-raw", action="store_true",
        help="Include raw JSON data section",
    )

    args = parser.parse_args(argv)

    # If no command, run interactive mode
    if args.command is None:
        return interactive_mode()

    # Dispatch to command handler
    handlers = {
        "sweep": cmd_sweep,
        "compare": cmd_compare,
        "test-tuning": cmd_test_tuning,
        "view-reports": cmd_view_reports,
        "generate-report": cmd_generate_report,
    }

    return handlers[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
