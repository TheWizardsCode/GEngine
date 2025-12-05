# Section 13: AI Tournament & Balance Analysis

**Last Updated:** 2025-12-04

## Overview

This guide explains how to use the AI tournament, batch sweep, and balance analysis tools introduced in Phases 9 and 11. These utilities enable designers and developers to:

- Run large batches of AI-driven games in parallel
- Compare strategy and difficulty performance
- Identify balance issues and underutilized content
- Automate regression and balance testing in CI

## Running AI Tournaments

The tournament script executes multiple games in parallel, each using a configurable AI strategy (`BALANCED`, `AGGRESSIVE`, `DIPLOMATIC`, `HYBRID`). Telemetry is captured for each game, and results are aggregated into a single JSON file for analysis.

**Example:**
```bash
uv run python scripts/run_ai_tournament.py --games 100 --output build/tournament.json
```

**Key options:**
- `--games`: Number of games to run (default: 100)
- `--output`: Path to save the aggregated results
- `--strategies`: Strategies to test (e.g., `balanced aggressive`)
- `--seeds`: Random seeds for reproducibility
- `--worlds`: World configuration bundles

## Running Batch Simulation Sweeps

The batch sweep script (Phase 11, M11.1) enables multi-dimensional parameter space exploration for comprehensive balance analysis. It generates a Cartesian product of parameter combinations and executes them in parallel, allowing you to:

- Stress-test balance across strategies, difficulties, seeds, worlds, and tick budgets
- Sample large parameter spaces efficiently
- Aggregate results for statistical analysis

### Configuration

Batch sweeps are configured via `content/config/batch_sweeps.yml`. You can override any parameter via CLI flags.

```yaml
parameters:
  strategies:
    - balanced
    - aggressive
    - diplomatic
  difficulties:
    - normal
    - hard
  seeds:
    - 42
    - 123
    - 456
  worlds:
    - default
  tick_budgets:
    - 100
    - 200

parallel:
  max_workers: null  # Auto-detect CPU count
  timeout_per_sweep: 300

output:
  dir: build/batch_sweeps
  include_telemetry: true

sampling:
  mode: full  # Options: full, random, latin_hypercube
  sample_count: 100
```

**Tip:** For very large parameter spaces, use `sampling.mode: random` and adjust `sample_count` to control the number of sweeps.

### Running Batch Sweeps

**Basic execution with default configuration:**
```bash
uv run python scripts/run_batch_sweeps.py --output-dir build/sweeps --verbose
```

**Override parameters via CLI:**
```bash
uv run python scripts/run_batch_sweeps.py \
  --strategies balanced aggressive \
  --difficulties normal hard \
  --seeds 42 123 456 \
  --ticks 100 200 \
  --output-dir build/custom_sweeps
```

**Use a custom configuration file:**
```bash
uv run python scripts/run_batch_sweeps.py --config path/to/custom_sweeps.yml
```

### Output Format

Each sweep produces a JSON file containing:
- `parameters`: Full parameter set (strategy, difficulty, seed, world, tick_budget)
- `results`: Game outcome data (final_stability, actions_taken, story_seeds_activated)
- `telemetry`: Metrics and profiling data (environment, faction_legitimacy, economy)
- `metadata`: Timestamp, git commit, runtime info

A summary file `batch_sweep_summary.json` aggregates all results, including:
- Strategy-level statistics (average/min/max stability, win rates)
- Difficulty-level statistics
- Total sweep counts and failure rates

### CLI Options

**Common CLI Flags:**

| Flag              | Description                                 |
|-------------------|---------------------------------------------|
| `--config, -c`    | Path to YAML configuration file              |
| `--strategies, -s`| Override strategies to test                  |
| `--difficulties, -d` | Override difficulty presets               |
| `--seeds`         | Override random seeds                        |
| `--worlds, -w`    | Override world bundles                       |
| `--ticks, -t`     | Override tick budgets                        |
| `--workers`       | Max parallel workers                         |
| `--output-dir, -o`| Output directory for results                 |
| `--json`          | Output summary as JSON                       |
| `--verbose, -v`   | Print progress during execution              |
| `--no-write`      | Skip writing individual sweep files          |

## Analyzing Tournament Results


After running a tournament or batch sweep, you can use two analysis scripts:

### 1. Basic Analysis

The `analyze_ai_games.py` script generates comparative reports highlighting:
- Win rate differences across strategies and difficulties
- Detection of unused story seeds
- Flagging of balance outliers and anomalies

**Example:**
```bash
uv run python scripts/analyze_ai_games.py build/tournament.json --report build/analysis.txt
```

**Key option:**
- `--report`: Path to save the analysis output

The report includes:
- Win rate comparison across strategies and difficulties
- Detection of unused story seeds
- Flagging of balance outliers

### 2. Advanced Balance Analysis
#### Statistical Analysis & Visualization

#### Regression Detection

#### Report Formats

#### Testing & Quality Assurance

The `analyze_balance.py` tool is covered by 39 dedicated tests, exceeding the minimum requirement. All tests pass, and the project maintains over 92% code coverage. Linting and security checks (CodeQL) are also enforced in CI, ensuring reliability and maintainability.

The `analyze_balance.py` tool supports multiple output formats for its reports:
- **Markdown** (default): Easy to read and version control
- **HTML**: Rich, styled reports with embedded charts
- **JSON**: For programmatic analysis or integration

**Specify the format with `--format`:**
```bash
uv run python scripts/analyze_balance.py report build/batch_sweep_summary.json --format markdown --output build/balance_report.md
uv run python scripts/analyze_balance.py report build/batch_sweep_summary.json --format html --output build/balance_report.html
uv run python scripts/analyze_balance.py report build/batch_sweep_summary.json --format json --output build/balance_report.json
```
Choose the format that best fits your workflow or audience.

The `regression` subcommand in `analyze_balance.py` helps you detect significant deviations from a baseline (reference) run. This is useful for automated regression testing and ongoing balance validation.

**Example: Compare a new sweep to a baseline**
```bash
uv run python scripts/analyze_balance.py regression build/batch_sweep_summary.json --baseline build/batch_sweep_summary_baseline.json --output build/regression_report.md
```
The generated report will highlight:
- Statistically significant changes in win rates or other metrics
- Newly dominant or underperforming strategies
- Unintended balance shifts

The `analyze_balance.py` tool provides robust statistical methods to help you understand and improve game balance:

- **Confidence Intervals:** Quantifies uncertainty in win rates and other metrics.
- **T-Tests:** Compares means between groups (e.g., strategies, difficulties) to detect significant differences.
- **Trend Detection:** Identifies changes in metrics over time or across parameter sweeps.
- **Parameter Sensitivity:** Surfaces which parameters most affect outcomes.
- **Visualizations:** Generates charts for win rate distributions, metric trends, and action distributions.

**Example: Generate win rate and trend charts**
```bash
uv run python scripts/analyze_balance.py report build/batch_sweep_summary.json --format html --output build/balance_report.html
```
The HTML report will include:
- Win rate bar charts by strategy and difficulty
- Trend lines for key metrics
- Action and story seed usage distributions

You can also use the `trends` subcommand for focused trend analysis:
```bash
uv run python scripts/analyze_balance.py trends build/batch_sweep_summary.json --output build/trends.json
```

The `analyze_balance.py` script provides advanced statistical analysis and reporting for tournament and sweep results. It supports:
- Confidence intervals and t-tests
- Trend detection and parameter sensitivity
- Regression detection against baselines
- Visualizations (charts/graphs)
- Multiple report formats (Markdown, HTML, JSON)

**Subcommands:**
- `report`: Generate summary reports
- `regression`: Detect significant deviations from baseline runs
- `trends`: Analyze metric trends over time
- `stats`: Compute confidence intervals and perform t-tests

**Example:**
```bash
uv run python scripts/analyze_balance.py report build/batch_sweep_summary.json --format html --output build/balance_report.html
```

See the sections below for details on statistical analysis, regression detection, and report formats.

## Balance Iteration Workflow

### Recommended Workflow

1. **Initial Exploration:** Run batch sweeps with diverse parameter combinations to establish baseline metrics.
2. **Tournament Validation:** Run focused tournaments on specific strategy combinations.
3. **Analysis:** Use the analysis script to identify dominant strategies, underpowered/overpowered actions, and unused content.
4. **Adjustment:** Modify simulation parameters or authored content based on findings.
5. **Regression Testing:** Re-run batch sweeps to validate improvements and ensure no regressions.

## CI Integration

A nightly CI workflow automatically runs tournaments and batch sweeps, archiving results for ongoing balance review. See `.github/workflows/ai-tournament.yml` for details.

## Usage Tips

- Use different world configs and seeds to stress-test balance across scenarios.
- For large parameter spaces, start with `sampling.mode: random` and a reduced `sample_count`.
- Review the analysis report regularly to guide design iteration.
- Archived CI artifacts provide a historical record of balance changes.
- Use `--verbose` during development to monitor sweep progress.
- Use reproducible seeds for regression testing.

## See Also
- [How to Play Echoes](./how_to_play_echoes.md)
- [Implementation Plan](../simul/emergent_story_game_implementation_plan.md)
- [README](../../README.md)
 - [Testing Guide](./testing_guide.md)
 - [Content Designer Workflow](./content_designer_workflow.md)
