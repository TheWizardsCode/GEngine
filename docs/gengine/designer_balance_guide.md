# Designer Balance Guide

A practical guide for game designers to diagnose balance issues and iterate on game parameters in Echoes of Emergence using the balance studio tooling.

## Overview

The balance studio provides designer-friendly workflows for:

- Running exploratory parameter sweeps
- Comparing configuration variants
- Testing tuning changes with overlays
- Viewing historical balance reports

This guide covers common balance iteration tasks and provides step-by-step workflows.

## Quick Start

### Installation

The balance studio is included with the GEngine development environment:

```bash
# Install dependencies
uv sync --group dev

# Verify installation
uv run echoes-balance-studio --help
```

### Available Commands

| Command | Purpose |
|---------|---------|
| `sweep` | Run exploratory balance sweeps |
| `compare` | Compare two configurations |
| `test-tuning` | Test overlay changes |
| `history` | View past sweep runs |
| `view` | Inspect a specific run |
| `report` | Generate HTML reports |
| `overlays` | List available overlays |

## Diagnosing Dominant Strategies

When one strategy consistently outperforms others, it indicates a balance issue that needs investigation.

### Symptoms

- Win rate differences >10% between strategies
- Players gravitating to a single approach
- AI tournaments showing lopsided results

### Diagnostic Workflow

1. **Run a multi-strategy sweep:**

   ```bash
   uv run echoes-balance-studio sweep \
       --strategies balanced aggressive diplomatic \
       --seeds 42 123 456 789 \
       --ticks 100
   ```

2. **Check the results:**

   ```
   Strategy Results:
     balanced: avg_stability=0.721
     aggressive: avg_stability=0.534
     diplomatic: avg_stability=0.698
   ```

3. **Identify the dominant strategy:** If one strategy has >10% higher win rate, it may need adjustment.

4. **Generate a detailed report:**

   ```bash
   uv run echoes-balance-studio report \
       --output build/balance_report.html
   ```

5. **Review the HTML report** for:
   - Win rate comparisons
   - Action usage frequencies
   - Story seed activation rates

### Common Fixes

| Issue | Typical Cause | Suggested Fix |
|-------|--------------|---------------|
| Aggressive too strong | Low stability penalty for aggression | Increase `environment.scarcity_unrest_weight` |
| Diplomatic too weak | Negotiation rewards too low | Adjust `progression.experience_per_negotiation` |
| Balanced dominates | Other strategies have skewed risk/reward | Review action costs and outcomes |

## Iterating on Action Costs

Action costs determine how expensive each player choice is, affecting strategy viability.

### Understanding Action Economy

Actions in Echoes consume resources and have effects:

- **Direct costs**: Resources spent to take the action
- **Opportunity costs**: What else could be done instead
- **Side effects**: Stability, faction legitimacy, pollution impacts

### Testing Cost Changes

1. **Create an overlay to adjust costs:**

   ```yaml
   # content/config/overlays/action_cost_test.yml
   _meta:
     name: "Action Cost Test"
     hypothesis: "Reducing inspection costs encourages exploration"
   
   progression:
     experience_per_inspection: 8.0  # Increased from 5.0
   ```

2. **Test the change:**

   ```bash
   uv run echoes-balance-studio test-tuning \
       --overlay content/config/overlays/action_cost_test.yml \
       --strategy balanced \
       --ticks 50
   ```

3. **Evaluate the results:**

   ```
   Results:
     Baseline stability: 0.712
     With overlay: 0.745
     Delta: +0.033
     Impact: ✅ positive
   ```

4. **If positive**, run a full comparison sweep to validate across strategies.

### Case Study: Balancing Faction Interactions

**Problem**: Players rarely use faction negotiation because the payoff is unclear.

**Hypothesis**: Increasing negotiation experience rewards will encourage diplomatic play.

**Process**:

```bash
# Create test overlay
cat > content/config/overlays/negotiation_boost.yml << 'EOF'
_meta:
  name: "Negotiation Boost"
  hypothesis: "Higher negotiation XP encourages diplomatic strategies"

progression:
  experience_per_negotiation: 25.0  # Up from 15.0
  diplomacy_multiplier: 1.3
EOF

# Test the change
uv run echoes-balance-studio test-tuning \
    --overlay content/config/overlays/negotiation_boost.yml \
    --strategy diplomatic \
    --ticks 100

# Compare strategies with the new settings
uv run echoes-balance-studio sweep \
    --strategies balanced aggressive diplomatic \
    --overlay content/config/overlays/negotiation_boost.yml \
    --ticks 100 \
    --seeds 42 123 456
```

## Testing Narrative Pacing Changes

The narrative director controls story seed activation and pacing.

### Key Pacing Parameters

| Parameter | Effect |
|-----------|--------|
| `director.max_active_seeds` | How many story arcs can run simultaneously |
| `director.global_quiet_ticks` | Minimum ticks between new seed activations |
| `director.seed_active_ticks` | How long a seed stays in "active" state |
| `director.seed_resolve_ticks` | How long resolution takes |

### Testing Pacing Adjustments

1. **Create a pacing overlay:**

   ```yaml
   # content/config/overlays/slower_pacing.yml
   _meta:
     name: "Slower Narrative Pacing"
     hypothesis: "More breathing room between story beats reduces overwhelm"
   
   director:
     max_active_seeds: 1
     global_quiet_ticks: 8  # Up from 4
     seed_quiet_ticks: 10   # Up from 6
   ```

2. **Run a longer sweep to observe pacing effects:**

   ```bash
   uv run echoes-balance-studio sweep \
       --overlay content/config/overlays/slower_pacing.yml \
       --ticks 200 \
       --seeds 42
   ```

3. **Check story seed activation counts** in the output telemetry.

### Balancing Story Density

Too many story seeds firing leads to chaos; too few leads to boredom.

**Indicators of over-pacing:**
- Multiple story seeds active simultaneously
- Players unable to respond before new events
- Stability crashes from overlapping crises

**Indicators of under-pacing:**
- Long stretches with no narrative events
- Players waiting with nothing to do
- Low engagement between crises

## Example Workflows

### Workflow 1: New Feature Balance Check

When adding a new game feature, validate it doesn't break existing balance:

```bash
# 1. Establish baseline
uv run echoes-balance-studio sweep \
    --strategies balanced aggressive diplomatic \
    --ticks 100 \
    --output-dir build/baseline

# 2. Apply your feature changes to an overlay

# 3. Test with overlay
uv run echoes-balance-studio sweep \
    --strategies balanced aggressive diplomatic \
    --overlay content/config/overlays/new_feature.yml \
    --ticks 100 \
    --output-dir build/with_feature

# 4. Compare results manually or generate reports
uv run echoes-balance-studio report \
    --output build/feature_comparison.html
```

### Workflow 2: Difficulty Tuning

Adjusting difficulty presets for different player skill levels:

```bash
# Compare easy vs hard difficulty configs
uv run echoes-balance-studio compare \
    --config-a content/config/sweeps/difficulty-easy/simulation.yml \
    --config-b content/config/sweeps/difficulty-hard/simulation.yml \
    --strategies balanced \
    --ticks 100
```

### Workflow 3: Regression Testing

After making changes, verify you haven't broken balance:

```bash
# Run sweep and ingest to database
uv run python scripts/run_batch_sweeps.py \
    --strategies balanced aggressive \
    --output-dir build/regression_test

uv run python scripts/aggregate_sweep_results.py \
    ingest build/regression_test

# Check historical trends
uv run echoes-balance-studio history --days 7

# Generate comparison report
uv run echoes-balance-studio report \
    --days 7 \
    --output build/regression_report.html
```

## Case Study: Balancing the Industrial Tier

This example walks through a complete balance iteration for a specific faction.

### Problem Statement

The Industrial Tier faction (Union of Flux) is underperforming:
- Lower win rates when playing industrial-focused strategies
- Faction legitimacy rarely exceeds 0.5
- Story seeds related to industry trigger less frequently

### Investigation

1. **Run targeted sweep:**

   ```bash
   uv run echoes-balance-studio sweep \
       --strategies balanced aggressive \
       --ticks 150 \
       --seeds 42 123 456 789 1234
   ```

2. **Review telemetry for faction legitimacy** in the output JSON.

3. **Identify issues:**
   - Industrial production values too low
   - Pollution costs outweigh benefits
   - Faction investment actions have weak effects

### Creating a Fix

```yaml
# content/config/overlays/industrial_balance.yml
_meta:
  name: "Industrial Tier Balance"
  hypothesis: "Boosting industrial benefits and reducing pollution penalties"

economy:
  base_resource_weights:
    materials: 3.0  # Up from 2.5
    energy: 4.5     # Up from 4.0

environment:
  faction_invest_pollution_relief: 0.03  # Up from 0.02
  scarcity_pollution_weight: 0.00002     # Down from 0.00003
```

### Testing the Fix

```bash
# Quick validation
uv run echoes-balance-studio test-tuning \
    --overlay content/config/overlays/industrial_balance.yml \
    --strategy balanced \
    --ticks 100

# Full sweep comparison
uv run echoes-balance-studio sweep \
    --overlay content/config/overlays/industrial_balance.yml \
    --strategies balanced aggressive diplomatic \
    --ticks 150 \
    --seeds 42 123 456
```

### Validating the Fix

After the overlay shows positive results:

1. Merge overlay values into the base config
2. Run full regression sweep
3. Update difficulty presets if needed
4. Document the change in commit message

## Best Practices

### Overlay Organization

```
content/config/overlays/
├── economy/
│   ├── resource_boost.yml
│   └── price_stability.yml
├── environment/
│   ├── pollution_reduction.yml
│   └── biodiversity_focus.yml
├── narrative/
│   ├── faster_pacing.yml
│   └── more_story_seeds.yml
└── experimental/
    └── wild_ideas.yml
```

### Testing Checklist

Before merging a balance change:

- [ ] Tested with at least 3 random seeds
- [ ] Compared against baseline configuration
- [ ] Checked all strategies (balanced, aggressive, diplomatic)
- [ ] Verified no dramatic win rate shifts
- [ ] Documented hypothesis and results
- [ ] Run against multiple difficulty levels if applicable

### Interpreting Results

| Metric | Good Range | Warning Signs |
|--------|------------|---------------|
| Avg Stability | 0.5 - 0.8 | Below 0.4 (too hard) or above 0.9 (too easy) |
| Win Rate Delta | < 10% | > 15% indicates dominant strategy |
| Actions/Game | 5-20 | Very low suggests boring; very high suggests chaos |
| Story Seed Activations | 2-5 per 100 ticks | None (broken pacing) or >10 (overwhelming) |

## Troubleshooting

### "No sweep runs found"

The database may be empty or in the wrong location:

```bash
# Check database exists
ls -la build/sweep_results.db

# Ingest results if needed
uv run python scripts/aggregate_sweep_results.py \
    ingest build/batch_sweeps
```

### Sweep takes too long

Reduce the parameter space:

```bash
# Fewer seeds and lower tick budget for quick tests
uv run echoes-balance-studio sweep \
    --strategies balanced \
    --seeds 42 \
    --ticks 30
```

### Overlay not applying

Verify the overlay file:

```bash
# Check syntax
python -c "import yaml; yaml.safe_load(open('path/to/overlay.yml'))"

# List available overlays
uv run echoes-balance-studio overlays
```

## See Also

- [AI Tournament & Balance Analysis](./ai_tournament_and_balance_analysis.md) - Detailed tournament tooling
- [How to Play Echoes](./how_to_play_echoes.md) - Gameplay mechanics reference
- [Implementation Plan](../simul/emergent_story_game_implementation_plan.md) - Technical details
