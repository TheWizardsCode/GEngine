#!/usr/bin/env python3
"""Analyze and compare difficulty profiles from sweep telemetry."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

DIFFICULTY_PRESETS = ["tutorial", "easy", "normal", "hard", "brutal"]


@dataclass
class DifficultyProfile:
    """Summary metrics extracted from a difficulty sweep."""

    preset: str
    stability_start: float
    stability_end: float
    stability_delta: float
    stability_trend: str
    unrest_end: float
    pollution_end: float
    anomalies: int
    suppressed_events: int
    faction_balance: float
    economic_pressure: float
    narrative_density: float
    biodiversity_end: float

    @classmethod
    def from_telemetry(cls, preset: str, data: dict[str, Any]) -> "DifficultyProfile":
        """Extract profile from telemetry JSON data."""
        env = data.get("last_environment", {})
        post_mortem = data.get("post_mortem", {})
        pm_env = post_mortem.get("environment", {})

        stability_start = pm_env.get("start", {}).get("stability", 1.0)
        stability_end = env.get("stability", 1.0)
        stability_delta = stability_end - stability_start

        if stability_delta > 0.1:
            stability_trend = "improving"
        elif stability_delta < -0.1:
            stability_trend = "declining"
        else:
            stability_trend = "stable"

        # Calculate faction balance as delta between faction legitimacies
        faction_leg = data.get("faction_legitimacy", {})
        leg_values = list(faction_leg.values())
        faction_balance = max(leg_values) - min(leg_values) if len(leg_values) >= 2 else 0.0

        # Economic pressure from price volatility
        economy = data.get("last_economy", {})
        prices = economy.get("prices", {})
        if prices:
            price_values = list(prices.values())
            economic_pressure = max(price_values) - 1.0 if price_values else 0.0
        else:
            economic_pressure = 0.0

        # Narrative density from events per tick
        ticks = data.get("ticks_executed", 1)
        events = data.get("events_emitted", 0)
        narrative_density = events / ticks if ticks > 0 else 0.0

        # Biodiversity from environment impact
        biodiversity_end = env.get("biodiversity", 0.7)

        return cls(
            preset=preset,
            stability_start=stability_start,
            stability_end=stability_end,
            stability_delta=stability_delta,
            stability_trend=stability_trend,
            unrest_end=env.get("unrest", 0.0),
            pollution_end=env.get("pollution", 0.0),
            anomalies=data.get("anomalies", 0),
            suppressed_events=data.get("suppressed_events", 0),
            faction_balance=faction_balance,
            economic_pressure=economic_pressure,
            narrative_density=narrative_density,
            biodiversity_end=biodiversity_end,
        )


def load_difficulty_profiles(
    telemetry_dir: Path,
    presets: Sequence[str] | None = None,
) -> dict[str, DifficultyProfile]:
    """Load profiles from telemetry files in the given directory."""
    selected = list(presets) if presets else DIFFICULTY_PRESETS
    profiles: dict[str, DifficultyProfile] = {}

    for preset in selected:
        telemetry_file = telemetry_dir / f"difficulty-{preset}-sweep.json"
        if not telemetry_file.exists():
            continue

        data = json.loads(telemetry_file.read_text())
        profiles[preset] = DifficultyProfile.from_telemetry(preset, data)

    return profiles


def compare_profiles(profiles: dict[str, DifficultyProfile]) -> dict[str, Any]:
    """Generate comparison analysis across difficulty profiles."""
    if not profiles:
        return {"error": "No profiles to compare"}

    comparison: dict[str, Any] = {
        "profile_count": len(profiles),
        "presets_analyzed": list(profiles.keys()),
        "metrics": {},
        "findings": [],
    }

    # Collect metrics for analysis
    stabilities = {p: prof.stability_end for p, prof in profiles.items()}
    unrests = {p: prof.unrest_end for p, prof in profiles.items()}
    pollutions = {p: prof.pollution_end for p, prof in profiles.items()}
    faction_balances = {p: prof.faction_balance for p, prof in profiles.items()}
    economic_pressures = {p: prof.economic_pressure for p, prof in profiles.items()}

    comparison["metrics"] = {
        "stability": stabilities,
        "unrest": unrests,
        "pollution": pollutions,
        "faction_balance": faction_balances,
        "economic_pressure": economic_pressures,
    }

    # Generate findings
    findings = []

    # Check if difficulty progression is reflected in stability
    preset_order = [p for p in DIFFICULTY_PRESETS if p in profiles]
    if len(preset_order) >= 2:
        stability_values = [profiles[p].stability_end for p in preset_order]
        if all(
            stability_values[i] >= stability_values[i + 1]
            for i in range(len(stability_values) - 1)
        ):
            findings.append(
                "✓ Stability correctly decreases with difficulty (harder = less stable)"
            )
        else:
            findings.append(
                "⚠ Stability does not consistently decrease with difficulty"
            )

        unrest_values = [profiles[p].unrest_end for p in preset_order]
        if all(
            unrest_values[i] <= unrest_values[i + 1]
            for i in range(len(unrest_values) - 1)
        ):
            findings.append(
                "✓ Unrest correctly increases with difficulty (harder = more unrest)"
            )
        else:
            findings.append(
                "⚠ Unrest does not consistently increase with difficulty"
            )

    # Check for extreme values
    for preset, profile in profiles.items():
        if profile.stability_end <= 0.0:
            findings.append(f"⚠ {preset}: Stability collapsed to 0 (may be too harsh)")
        if profile.anomalies > 100:
            findings.append(
                f"⚠ {preset}: High anomaly count ({profile.anomalies}) indicates system stress"
            )

    # Check differentiation between adjacent difficulties
    for i in range(len(preset_order) - 1):
        p1, p2 = preset_order[i], preset_order[i + 1]
        prof1, prof2 = profiles[p1], profiles[p2]
        stability_diff = abs(prof1.stability_end - prof2.stability_end)
        if stability_diff < 0.05:
            findings.append(
                f"⚠ {p1} vs {p2}: Stability difference is minimal ({stability_diff:.3f}), "
                "consider widening gap"
            )

    comparison["findings"] = findings
    return comparison


def print_profile_table(profiles: dict[str, DifficultyProfile]) -> None:
    """Print a formatted table of difficulty profiles."""
    print("\n" + "=" * 100)
    print("DIFFICULTY PROFILE ANALYSIS")
    print("=" * 100)
    print(
        f"{'Preset':<10} {'Stability':>10} {'Δ':>8} {'Trend':>10} "
        f"{'Unrest':>8} {'Pollution':>10} {'Faction Δ':>10} {'Econ Pres':>10}"
    )
    print("-" * 100)

    for preset in DIFFICULTY_PRESETS:
        if preset not in profiles:
            continue
        p = profiles[preset]
        print(
            f"{p.preset:<10} {p.stability_end:>10.3f} {p.stability_delta:>+8.3f} "
            f"{p.stability_trend:>10} {p.unrest_end:>8.3f} {p.pollution_end:>10.3f} "
            f"{p.faction_balance:>10.3f} {p.economic_pressure:>10.3f}"
        )

    print("=" * 100)


def print_comparison_report(comparison: dict[str, Any]) -> None:
    """Print the comparison analysis report."""
    print("\n" + "=" * 80)
    print("COMPARISON FINDINGS")
    print("=" * 80)

    for finding in comparison.get("findings", []):
        print(f"  {finding}")

    if not comparison.get("findings"):
        print("  No significant findings.")

    print("=" * 80)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for difficulty profile analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze and compare difficulty profiles from sweep telemetry."
    )
    parser.add_argument(
        "--telemetry-dir",
        "-d",
        type=Path,
        default=Path("build"),
        help="Directory containing telemetry JSON files (default: build)",
    )
    parser.add_argument(
        "--preset",
        "-p",
        action="append",
        choices=DIFFICULTY_PRESETS,
        help="Specific preset(s) to analyze (can be repeated; default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of formatted tables",
    )

    args = parser.parse_args(argv)

    profiles = load_difficulty_profiles(args.telemetry_dir, args.preset)

    if not profiles:
        print(
            f"No telemetry files found in {args.telemetry_dir}. "
            "Run run_difficulty_sweeps.py first.",
            file=__import__("sys").stderr,
        )
        return 1

    comparison = compare_profiles(profiles)

    if args.json:
        output = {
            "profiles": {p: vars(prof) for p, prof in profiles.items()},
            "comparison": comparison,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print_profile_table(profiles)
        print_comparison_report(comparison)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
