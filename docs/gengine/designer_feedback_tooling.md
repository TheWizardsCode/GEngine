# Designer Feedback Loop and Tooling

**Last Updated:** 2025-12-06

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Workflows](#workflows)
    - [Run Exploratory Sweep](#1-run-exploratory-sweep)
    - [Compare Two Configs](#2-compare-two-configs)
    - [Test Tuning Change](#3-test-tuning-change)
    - [View Historical Reports](#4-view-historical-reports)
4. [YAML Overlay System](#yaml-overlay-system)
5. [Interactive HTML Reports](#interactive-html-reports)
6. [Diagnose Dominant Strategies](#how-to-diagnose-dominant-strategies)
7. [Iterating on Action Costs](#iterating-on-action-costs)
8. [Testing Narrative Pacing Changes](#testing-narrative-pacing-changes)
9. [Case Study: Balancing the Industrial Tier Faction](#case-study-balancing-the-industrial-tier-faction)
10. [Tips and Best Practices](#tips-and-best-practices)
11. [Command Reference](#command-reference)
12. [See Also](#see-also)
# Designer Feedback Loop and Tooling

This guide explains how to use the Balance Studio tools for iterating on game
balance without requiring code changes. These tools are designed for designers
who want to experiment with tuning, diagnose balance issues, and validate
changes through data-driven analysis.

## Overview

The Balance Studio provides:

- **Interactive CLI** (`echoes-balance-studio`) with guided workflows
- **YAML overlay system** for testing config changes without modifying base files
- **HTML dashboard** for exploring sweep results visually
- **Workflow presets** for common balance iteration tasks

## Quick Start

```bash
# Run the interactive Balance Studio
echoes-balance-studio

# Or use specific commands
echoes-balance-studio sweep --strategies balanced aggressive
echoes-balance-studio compare --config-a content/config --config-b content/config/sweeps/difficulty-hard
echoes-balance-studio test-tuning --name boost_regen --change economy.regen_scale=1.2
echoes-balance-studio view-reports
echoes-balance-studio generate-report --input build/sweeps/summary.json --output build/report.html
```

## Workflows

### 1. Run Exploratory Sweep

Executes batch simulations across multiple strategies and configurations to
explore the balance space.

```bash
# Interactive mode
echoes-balance-studio

# Direct command
echoes-balance-studio sweep \
    --strategies balanced aggressive diplomatic \
    --difficulties normal hard \
    --seeds 42 123 456 \
    --ticks 100
```

**When to use:**
- Initial exploration of a new feature or mechanic
- Validating balance after significant changes
- Gathering baseline data for comparison

**Output:**
- Individual sweep JSON files in `build/studio_sweeps/`
- Summary report with strategy and difficulty breakdowns
- Stability distributions and action counts

### 2. Compare Two Configs

Runs side-by-side sweeps with different configurations and produces a
comparison report.

```bash
echoes-balance-studio compare \
    --config-a content/config \
    --config-b content/config/sweeps/difficulty-hard \
    --name-a "Normal" \
    --name-b "Hard" \
    --strategies balanced
```

**When to use:**
- Validating difficulty presets
- A/B testing configuration changes
- Comparing before/after tuning adjustments

**Output:**
- Stability deltas between configurations
- Per-strategy performance comparison
- Percentage change metrics

### 3. Test Tuning Change

Creates a temporary configuration overlay with specific changes and compares
results against the baseline.

```bash
echoes-balance-studio test-tuning \
    --name "boost_regen" \
    --change economy.regen_scale=1.2 \
    --change environment.scarcity_pressure_cap=6000 \
    --strategies balanced aggressive
```

**When to use:**
- Quick iteration on specific parameters
- Testing hypotheses about balance issues
- Validating fixes for identified problems

**Output:**
- Baseline vs. tuned comparison
- Saved overlay file for future reference
- Detailed stability metrics

### 4. View Historical Reports

Browse and inspect previously generated sweep reports.

```bash
# List available reports
echoes-balance-studio view-reports

# Output as JSON for processing
echoes-balance-studio view-reports --json
```

**When to use:**
- Reviewing past experiments
- Tracking balance changes over time
- Finding regression baselines

---

## YAML Overlay System

Overlays allow you to test configuration changes without modifying base files.
This is similar to the existing difficulty presets but designed for quick
experimentation.

### Creating an Overlay

Create a YAML file with your changes:

```yaml
# my_overlay.yml
name: aggressive_economy
description: Test higher resource regeneration and lower scarcity pressure

overrides:
  economy:
    regen_scale: 1.2
    demand_population_scale: 80000
  environment:
    scarcity_pressure_cap: 4000
    scarcity_unrest_weight: 0.00003

metadata:
  author: designer_name
  ticket: GAME-1234
```

### Using an Overlay

```bash
# Apply overlay during sweep
echoes-balance-studio sweep --overlay my_overlay.yml

# Or use the test-tuning workflow for quick changes
echoes-balance-studio test-tuning \
    --name quick_test \
    --change economy.regen_scale=1.2
```

### Overlay Directory

Place overlays in `content/config/overlays/` to make them available for the
Balance Studio to discover:

```
content/
  config/
    overlays/
      aggressive_economy.yml
      conservative_pacing.yml
      stress_test.yml
```

---

## Interactive HTML Reports

Generate rich HTML dashboards from sweep results:

```bash
echoes-balance-studio generate-report \
    --input build/batch_sweeps/batch_sweep_summary.json \
    --output build/balance_report.html \
    --title "Weekly Balance Review"
```

### Features

- **Strategy Performance Table**: Sortable comparison of all strategies
- **Difficulty Analysis**: See how each difficulty level affects stability
- **Stability Distribution**: Histogram of outcomes across all sweeps
- **Individual Sweep Browser**: Filter and drill into specific runs
- **Embedded Charts**: Visual representations of key metrics

### Themes

```bash
# Light theme (default)
echoes-balance-studio generate-report --theme light ...

# Dark theme
echoes-balance-studio generate-report --theme dark ...
```

---

## How to Diagnose Dominant Strategies

When one strategy consistently outperforms others, it may indicate a balance
issue. Here's how to diagnose and address dominant strategies:

### Step 1: Run a Broad Sweep

```bash
echoes-balance-studio sweep \
    --strategies balanced aggressive diplomatic hybrid \
    --seeds 42 123 456 789 1000 \
    --ticks 200
```

### Step 2: Generate and Review the Report

```bash
echoes-balance-studio generate-report \
    --input build/studio_sweeps/sweep_*/batch_sweep_summary.json \
    --output build/dominant_strategy_analysis.html
```

Look for:
- **Win rate gaps > 10%** between strategies
- **Consistently high/low stability** for specific strategies
- **Action distribution skews** (some actions never used)

### Step 3: Identify Root Causes

Common causes of dominant strategies:

1. **Overpowered actions**: Check action_counts in sweep data
2. **Resource imbalance**: Review economy.regen_scale and demand weights
3. **Threshold issues**: Stability thresholds may favor certain playstyles
4. **Faction mechanics**: Some factions may synergize too well with a strategy

### Step 4: Test Fixes

```bash
# Example: If aggressive strategy is dominant due to high resource gains
echoes-balance-studio test-tuning \
    --name nerf_aggressive \
    --change economy.regen_scale=0.7 \
    --strategies balanced aggressive
```

### Step 5: Validate

Re-run the broad sweep with your changes and confirm the gap has narrowed.

---

## Iterating on Action Costs

Action costs affect how often AI strategies choose specific actions. Here's
how to tune them:

### Step 1: Identify Underused Actions

Run a sweep and check action frequency distribution:

```bash
echoes-balance-studio sweep --strategies balanced aggressive diplomatic
echoes-balance-studio generate-report \
    --input build/studio_sweeps/*/batch_sweep_summary.json \
    --output build/action_analysis.html
```

Actions with < 5% usage may be too expensive or ineffective.

### Step 2: Test Cost Adjustments

```bash
# Reduce cost of underused action
echoes-balance-studio test-tuning \
    --name buff_negotiate \
    --change actions.negotiate.base_cost=0.5 \
    --change actions.negotiate.cooldown=2
```

### Step 3: Monitor Side Effects

Check that buffing one action doesn't make others obsolete. Compare action
distributions before and after.

### Best Practices

- Make small, incremental changes (10-20% adjustments)
- Test across multiple strategies
- Use multiple seeds for statistical validity
- Document changes with descriptive overlay names

---

## Testing Narrative Pacing Changes

Narrative pacing affects story seed activation, director events, and the
overall flow of the game.

### Key Pacing Parameters

| Parameter | Location | Effect |
|-----------|----------|--------|
| `max_active_seeds` | director | How many story seeds can be active at once |
| `global_quiet_ticks` | director | Minimum ticks between major events |
| `seed_active_ticks` | director | How long a seed stays active |
| `seed_resolve_ticks` | director | Time to resolve after active phase |
| `seed_quiet_ticks` | director | Cooldown before seed can reactivate |

### Step 1: Baseline Measurement

Run a sweep with current settings:

```bash
echoes-balance-studio sweep \
    --ticks 300 \
    --seeds 42 123
```

Check story seed activation rates in the output.

### Step 2: Test Pacing Adjustment

```bash
# Example: Increase drama density
echoes-balance-studio test-tuning \
    --name fast_pacing \
    --change director.max_active_seeds=3 \
    --change director.global_quiet_ticks=2 \
    --ticks 300
```

### Step 3: Review Story Seed Behavior

Look for:
- **Activation rate**: Are seeds firing at the expected frequency?
- **Overlap issues**: Are too many seeds active simultaneously?
- **Dead zones**: Are there long stretches without narrative events?

### Step 4: Iterate

Adjust parameters based on observations:
- Increase `global_quiet_ticks` if events feel overwhelming
- Decrease `seed_quiet_ticks` if the game feels slow
- Adjust `story_seed_limit` to control how many seeds surface per tick

---

## Case Study: Balancing the Industrial Tier Faction

This case study demonstrates a complete balance iteration workflow.

### Problem Statement

Playtest feedback indicates the Industrial Tier faction feels underpowered
compared to other factions. Players report:
- Lower legitimacy gains
- Fewer opportunities for impactful actions
- Pollution penalties seem too harsh

### Step 1: Gather Data

```bash
# Run comprehensive sweep focusing on faction behavior
echoes-balance-studio sweep \
    --strategies balanced diplomatic \
    --seeds 42 123 456 789 1000 1001 1002 1003 \
    --ticks 200 \
    --output-dir build/industrial_tier_analysis
```

### Step 2: Analyze Baseline

```bash
echoes-balance-studio generate-report \
    --input build/industrial_tier_analysis/batch_sweep_summary.json \
    --output build/industrial_tier_baseline.html
```

Review faction legitimacy trends in the sweep data.

### Step 3: Hypothesis Testing

**Hypothesis 1: Pollution penalties are too harsh**

```bash
echoes-balance-studio test-tuning \
    --name reduce_pollution_penalty \
    --change environment.faction_sabotage_pollution_spike=0.015 \
    --change environment.scarcity_pollution_weight=0.00002 \
    --strategies balanced \
    --seeds 42 123 456
```

**Hypothesis 2: Investment returns are too low**

```bash
echoes-balance-studio test-tuning \
    --name boost_investment \
    --change economy.faction_investment_return=1.5 \
    --change environment.faction_invest_pollution_relief=0.03 \
    --strategies balanced \
    --seeds 42 123 456
```

### Step 4: Compare Results

```bash
# Generate comparison between baseline and each hypothesis
echoes-balance-studio compare \
    --config-a content/config \
    --config-b build/industrial_tier_analysis/tuning_reduce_pollution_penalty_*/modified_config \
    --name-a "Baseline" \
    --name-b "Reduced Pollution"
```

### Step 5: Implement and Validate

Based on the data, create a formal overlay for the winning hypothesis:

```yaml
# content/config/overlays/industrial_tier_balance.yml
name: industrial_tier_balance_v1
description: Rebalance Industrial Tier faction after Dec 2024 analysis

overrides:
  environment:
    faction_sabotage_pollution_spike: 0.018
    scarcity_pollution_weight: 0.000025
    faction_invest_pollution_relief: 0.025

metadata:
  ticket: GAME-4567
  analysis_date: 2024-12-01
  baseline_report: build/industrial_tier_baseline.html
```

Run a final validation sweep with the new overlay applied.

---

## Tips and Best Practices

### Statistical Validity

- Use at least 5 different seeds for meaningful comparisons
- Run 100+ ticks to capture mid-to-late game dynamics
- Repeat experiments if results are marginal

### Documenting Changes

- Always include descriptive names for overlays
- Reference ticket numbers in metadata
- Save baseline reports before making changes

### Iterative Approach

1. Make one change at a time when possible
2. Measure impact before adding more changes
3. Keep changes small (10-20% parameter adjustments)
4. Validate that fixes don't create new problems

### Sharing Results

- Use `--json` flag for data that needs processing
- Generate HTML reports for stakeholder reviews
- Archive summary JSONs for regression testing

---

## Command Reference

| Command | Description |
|---------|-------------|
| `echoes-balance-studio` | Interactive workflow selection |
| `echoes-balance-studio sweep` | Run exploratory sweeps |
| `echoes-balance-studio compare` | Compare two configurations |
| `echoes-balance-studio test-tuning` | Test a tuning change |
| `echoes-balance-studio view-reports` | Browse historical reports |
| `echoes-balance-studio generate-report` | Generate HTML dashboard |

### Common Flags

| Flag | Description |
|------|-------------|
| `--strategies` | AI strategies to test |
| `--difficulties` | Difficulty presets |
| `--seeds` | Random seeds for reproducibility |
| `--ticks` | Tick budget per sweep |
| `--output-dir` | Output directory |
| `--json` | Output as JSON |
| `--verbose` | Verbose progress output |

---

## See Also

- [AI Tournament & Balance Analysis](./ai_tournament_and_balance_analysis.md)
- [How to Play Echoes](./how_to_play_echoes.md)
- [Content Designer Workflow](./content_designer_workflow.md)
- [Implementation Plan](../simul/emergent_story_game_implementation_plan.md)
