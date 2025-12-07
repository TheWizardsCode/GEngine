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

## Strategy Parameter Optimization

The `optimize_strategies.py` script (Phase 11, M11.4) provides automated strategy parameter tuning using optimization algorithms to find well-balanced strategy configurations. It helps reduce dominant strategy win rate deltas and improve strategic diversity.

### Optimization Algorithms

Three optimization algorithms are supported:

1. **Grid Search** (`--algorithm grid`): Exhaustive search over all parameter combinations. Best for small parameter spaces or when you need guaranteed coverage.

2. **Random Search** (`--algorithm random`): Randomly samples parameter configurations. Efficient for large parameter spaces where exhaustive search is impractical.

3. **Bayesian Optimization** (`--algorithm bayesian`): Uses Gaussian processes to intelligently explore the parameter space. Requires `scikit-optimize` package (`pip install scikit-optimize`).

### Configuration

Optimization can be configured via `content/config/optimization.yml` or CLI flags:

```yaml
parameters:
  stability_low:
    min: 0.5
    max: 0.8
    step: 0.1  # For grid search
  stability_critical:
    min: 0.3
    max: 0.5
  faction_low_legitimacy:
    min: 0.3
    max: 0.6

targets:
  - name: win_rate_delta
    weight: 1.0
    direction: minimize
  - name: diversity
    weight: 0.5
    direction: maximize

settings:
  algorithm: random
  n_samples: 50
  tick_budget: 100
  seeds: [42, 123, 456]
  strategies: [balanced, aggressive, diplomatic]
```

### Running Optimization

**Basic optimization with grid search:**
```bash
uv run python scripts/optimize_strategies.py optimize --algorithm grid
```

**Random search with more samples:**
```bash
uv run python scripts/optimize_strategies.py optimize --algorithm random --samples 100
```

**Bayesian optimization (requires scikit-optimize):**
```bash
uv run python scripts/optimize_strategies.py optimize --algorithm bayesian --samples 50
```

### Optimization Targets

The optimizer supports multiple optimization targets:

- **win_rate_delta**: Minimize the maximum win rate difference between strategies. Lower values indicate better balance.
- **diversity**: Maximize strategic diversity (different strategies succeed in different scenarios). Uses entropy-based scoring.
- **stability**: Target average stability across simulations.

Multi-objective optimization produces a Pareto frontier showing trade-offs between competing objectives.

### Pareto Frontier

The Pareto frontier represents configurations that are optimal in some dimension—no other configuration is better in all objectives simultaneously. View the frontier with:

```bash
uv run python scripts/optimize_strategies.py pareto --database build/sweep_results.db
```

This helps identify trade-offs such as:
- Balance vs. difficulty (easier games may be more balanced)
- Diversity vs. stability (more diverse outcomes may have wider stability ranges)

#### Interpreting the Pareto Frontier

The Pareto frontier is a set of parameter configurations where no single configuration is strictly better than another across all objectives. Each point on the frontier represents a trade-off:

- **If you want the most balanced game:** Look for points with the lowest `win_rate_delta`.
- **If you want the most diverse strategies:** Look for points with the highest `diversity` score.
- **If you want a compromise:** Choose a point that balances both objectives, or use the weights in your optimization config to bias toward your design goals.

**Visualizing the Pareto Frontier:**
You can plot the Pareto points (e.g., `win_rate_delta` vs. `diversity`) using your favorite plotting tool or spreadsheet. This helps you see the shape of the trade-off curve and pick a configuration that fits your needs.

**Example:**
If the Pareto frontier includes:

| win_rate_delta | diversity | stability |
|----------------|-----------|-----------|
| 0.10           | 0.95      | 0.70      |
| 0.12           | 0.98      | 0.68      |
| 0.08           | 0.90      | 0.72      |

You might choose the first row for best balance, the second for best diversity, or the third for a compromise.

**Tip:** No point on the Pareto frontier is strictly "best"—the right choice depends on your design priorities.

### Output Files

After optimization, results are saved to the output directory (default: `build/optimization/`):

- `optimization_result.json`: Full optimization data including all evaluated configurations
- `optimization_report.md`: Human-readable Markdown report with best parameters and Pareto frontier

### Integration with Result Storage

Optimization results are automatically stored in the sweep results database (`build/sweep_results.db`) for historical tracking. Query past optimization runs:

```bash
uv run python scripts/optimize_strategies.py pareto --limit 10
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--algorithm, -a` | Optimization algorithm (grid, random, bayesian) |
| `--config, -c` | Path to YAML configuration file |
| `--samples, -n` | Number of samples for random/bayesian search |
| `--ticks, -t` | Tick budget per sweep simulation |
| `--seed` | Random seed for reproducibility |
| `--output-dir, -o` | Output directory for results |
| `--database, -d` | Path to sweep results database |
| `--json` | Output as JSON instead of files |
| `--verbose, -v` | Print progress information |
| `--no-store` | Skip storing result in database |

### Example Workflow

### Troubleshooting & FAQ

- **Q: My optimization run is very slow or seems stuck.**
  - Try reducing the number of samples or using random search instead of grid search for large parameter spaces.
  - Use the `--verbose` flag to monitor progress.
- **Q: I get an error about missing or invalid parameters.**
  - Check your YAML config and CLI flags for typos or out-of-range values. All parameter names must match those in your strategy config.
- **Q: The Pareto frontier is empty or has only one point.**
  - This can happen if all configurations are dominated or if your parameter ranges are too narrow. Try expanding the search space or adjusting your targets.
- **Q: How do I add a new optimization target?**
  - Edit your config to add a new target (e.g., `stability`) and re-run the optimizer. See the config example above.

1. **Run initial optimization:**
   ```bash
   uv run python scripts/optimize_strategies.py optimize --algorithm random --samples 50 --verbose
   ```

2. **Review results:**
   ```bash
   cat build/optimization/optimization_report.md
   ```

3. **Apply best parameters:** Update `src/gengine/ai_player/strategies.py` with the discovered optimal values for `StrategyConfig`.

4. **Validate with batch sweeps:**
   ```bash
   uv run python scripts/run_batch_sweeps.py --output-dir build/validation
   ```

5. **Generate balance report:**
   ```bash
   uv run python scripts/analyze_balance.py report --database build/sweep_results.db
   ```

## Balance Iteration Workflow

### Recommended Workflow

1. **Initial Exploration:** Run batch sweeps with diverse parameter combinations to establish baseline metrics.
2. **Tournament Validation:** Run focused tournaments on specific strategy combinations.
3. **Analysis:** Use the analysis script to identify dominant strategies, underpowered/overpowered actions, and unused content.
4. **Parameter Optimization:** Use `optimize_strategies.py` to find balanced parameter configurations automatically.
5. **Adjustment:** Apply optimized parameters or modify authored content based on findings.
6. **Regression Testing:** Re-run batch sweeps to validate improvements and ensure no regressions.

## CI Integration

A nightly CI workflow automatically runs tournaments and batch sweeps, archiving results for ongoing balance review. See `.github/workflows/ai-tournament.yml` for details.

## Usage Tips

## Best Practices & Advanced Tips

- Start with a broad parameter sweep to understand the landscape, then narrow in on promising regions.
- Use multiple random seeds to avoid overfitting to a single scenario.
- Regularly review the Markdown and JSON reports to track progress and spot regressions.
- Archive your optimization results and reports for future reference and reproducibility.
- For advanced analysis, export Pareto points and plot them to visualize trade-offs.

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
