# Section 13: AI Tournament & Balance Analysis

**Last Updated:** 2025-12-04

## Overview
This section describes how to use the AI tournament, batch sweep, and balance analysis tooling introduced in Phases 9 and 11. These tools help designers and developers run large batches of AI-driven games in parallel, compare strategy performance, and identify balance issues or underutilized content.

## Running AI Tournaments

The tournament script executes multiple games in parallel, each using a configurable AI strategy (BALANCED, AGGRESSIVE, DIPLOMATIC, HYBRID). Telemetry is captured for each game, and results are aggregated into a single JSON file.

**Example:**
```bash
uv run python scripts/run_ai_tournament.py --games 100 --output build/tournament.json
```
- `--games`: Number of games to run (default: 100)
- `--output`: Path to save the aggregated results
- Additional flags allow you to specify strategies, seeds, and world configs.

## Running Batch Simulation Sweeps

The batch sweep script (Phase 11, M11.1) enables multi-dimensional parameter space exploration for comprehensive balance analysis. It generates a Cartesian product of parameter combinations and executes them in parallel.

### Configuration

Batch sweeps are configured via `content/config/batch_sweeps.yml`:

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

**Use custom configuration file:**
```bash
uv run python scripts/run_batch_sweeps.py --config path/to/custom_sweeps.yml
```

### Output Format

Each sweep produces a JSON file containing:
- `parameters`: Full parameter set (strategy, difficulty, seed, world, tick_budget)
- `results`: Game outcome data (final_stability, actions_taken, story_seeds_activated)
- `telemetry`: Metrics and profiling data (environment, faction_legitimacy, economy)
- `metadata`: Timestamp, git commit, runtime info

A summary file `batch_sweep_summary.json` aggregates all results with:
- Strategy-level statistics (avg/min/max stability, win rates)
- Difficulty-level statistics
- Total sweep counts and failure rates

### CLI Options

| Flag | Description |
|------|-------------|
| `--config, -c` | Path to YAML configuration file |
| `--strategies, -s` | Override strategies to test |
| `--difficulties, -d` | Override difficulty presets |
| `--seeds` | Override random seeds |
| `--worlds, -w` | Override world bundles |
| `--ticks, -t` | Override tick budgets |
| `--workers` | Max parallel workers |
| `--output-dir, -o` | Output directory for results |
| `--json` | Output summary as JSON |
| `--verbose, -v` | Print progress during execution |
| `--no-write` | Skip writing individual sweep files |

## Analyzing Tournament Results

After running a tournament, use the analysis script to generate comparative reports. This tool surfaces win rate differences, balance anomalies, and unused story seeds.

**Example:**
```bash
uv run python scripts/analyze_ai_games.py build/tournament.json --report build/analysis.txt
```
- `--report`: Path to save the analysis output

The report includes:
- Win rate comparison across strategies
- Detection of unused story seeds
- Flagging of balance outliers

## Balance Iteration Workflow

1. **Initial Exploration**: Run batch sweeps with diverse parameter combinations to establish baseline metrics.
2. **Tournament Validation**: Run focused tournaments on specific strategy combinations.
3. **Analysis**: Use the analysis script to identify dominant strategies, underpowered/overpowered actions, and unused content.
4. **Adjustment**: Modify simulation parameters or authored content based on findings.
5. **Regression Testing**: Re-run batch sweeps to validate improvements and ensure no regressions.

## CI Integration

A nightly CI workflow automatically runs tournaments and archives results for ongoing balance review. See `.github/workflows/ai-tournament.yml` for details.

## Usage Tips
- Use different world configs and seeds to stress-test balance across scenarios.
- Start with `sampling.mode: random` for large parameter spaces before running full sweeps.
- Review the analysis report regularly to guide design iteration.
- Archived CI artifacts provide a historical record of balance changes.
- Use `--verbose` during development to monitor sweep progress.

## See Also
- [How to Play Echoes](./how_to_play_echoes.md)
- [Implementation Plan](../simul/emergent_story_game_implementation_plan.md)
- [README](../../README.md)
