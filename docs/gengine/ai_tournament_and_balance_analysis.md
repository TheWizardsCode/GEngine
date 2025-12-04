# Section 13: AI Tournament & Balance Analysis

**Last Updated:** 2025-12-03

## Overview
This section describes how to use the AI tournament and balance analysis tooling introduced in Phase 9. These tools help designers and developers run large batches of AI-driven games in parallel, compare strategy performance, and identify balance issues or underutilized content.

## Running AI Tournaments

The tournament script executes multiple games in parallel, each using a configurable AI strategy (BALANCED, AGGRESSIVE, DIPLOMATIC, HYBRID). Telemetry is captured for each game, and results are aggregated into a single JSON file.

**Example:**
```bash
uv run python scripts/run_ai_tournament.py --games 100 --output build/tournament.json
```
- `--games`: Number of games to run (default: 100)
- `--output`: Path to save the aggregated results
- Additional flags allow you to specify strategies, seeds, and world configs.

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

1. Run a tournament with a large number of games and varied strategies.
2. Analyze the results to identify dominant strategies, underpowered/overpowered actions, and unused content.
3. Adjust simulation parameters or authored content as needed.
4. Repeat the process to validate improvements.

## CI Integration

A nightly CI workflow automatically runs tournaments and archives results for ongoing balance review. See `.github/workflows/ai-tournament.yml` for details.

## Usage Tips
- Use different world configs and seeds to stress-test balance across scenarios.
- Review the analysis report regularly to guide design iteration.
- Archived CI artifacts provide a historical record of balance changes.

## See Also
- [How to Play Echoes](./how_to_play_echoes.md)
- [Implementation Plan](../simul/emergent_story_game_implementation_plan.md)
- [README](../../README.md)
