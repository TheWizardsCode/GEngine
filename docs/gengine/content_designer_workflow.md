# Content Designer Workflow

This guide describes how to author, validate, and deploy content for Echoes of Emergence.

## Overview

Content in Echoes of Emergence is organized under the `content/` directory:

```
content/
├── config/
│   ├── simulation.yml          # Global simulation settings
│   └── sweeps/                  # Difficulty presets
│       ├── difficulty-easy/
│       ├── difficulty-normal/
│       └── ...
└── worlds/
    └── default/                 # World definitions
        ├── world.yml            # City, districts, factions, agents
        └── story_seeds.yml      # Narrative story seeds
```

## Content Types

### Worlds (`content/worlds/*/`)

Each world is a directory containing:

#### `world.yml` - World Definition

Defines the city, districts, factions, and agents:

```yaml
city:
  id: neo-echo
  name: Neo Echo
  description: A layered metropolis...
  districts:
    - id: industrial-tier
      name: Industrial Tier
      population: 120000
      coordinates:
        x: 0.0
        y: 0.0
      adjacent:
        - research-spire
      resources:
        energy:
          type: energy
          capacity: 80
          current: 60
          regen: 4.5
      modifiers:
        pollution: 0.72
        unrest: 0.35

factions:
  - id: union_of_flux
    name: Union of Flux
    ideology: Labor futurists seeking equitable automation.
    legitimacy: 0.62
    territory:
      - industrial-tier

agents:
  - id: aria-volt
    name: Aria Volt
    role: Mediator
    faction_id: union_of_flux
    home_district: industrial-tier
    traits:
      empathy: 0.82
      resolve: 0.74
    goals:
      - Secure fair energy quotas for worker districts

environment:
  stability: 0.56
  unrest: 0.33
  pollution: 0.58
  climate_risk: 0.47
  security: 0.52

metadata:
  seed: 424242
```

#### `story_seeds.yml` - Story Seeds

Defines narrative events that can trigger during gameplay:

```yaml
story_seeds:
  - id: energy-quota-crisis
    title: "Energy Quota Fallout"
    summary: "Rolling brownouts push the Industrial Tier toward a crisis."
    stakes: "Union of Flux threatens to abandon the grid."
    scope: environment  # environment, faction, or agent
    tags: [energy, labor, crisis]
    preferred_districts: [industrial-tier]
    cooldown_ticks: 40
    travel_hint:
      district_id: industrial-tier
      max_focus_distance: 3
    roles:
      agents: [aria-volt]      # Must exist in world.yml
      factions: [union_of_flux] # Must exist in world.yml
    beats:
      - "Union leaders threaten a walkout."
      - "Aria Volt drafts an emergency ration plan."
    triggers:
      - scope: environment
        district_id: industrial-tier  # Must exist in world.yml
        min_score: 0.45
        min_severity: 0.75
    resolution_templates:
      success: "Emergency rationing shares power fairly."
      failure: "Workshops go dark, strikers spread."
      partial: "Convoys buy time but tensions remain."
    followups: [hollow-supply-chain]  # Must be another seed ID
```

### Configuration (`content/config/`)

#### `simulation.yml` - Simulation Settings

Controls gameplay balance and simulation parameters:

```yaml
limits:
  engine_max_ticks: 200
  cli_run_cap: 50
  service_tick_cap: 100

lod:
  mode: balanced  # detailed, balanced, or coarse
  max_events_per_tick: 6

economy:
  regen_scale: 0.8
  demand_population_scale: 100000

environment:
  scarcity_pressure_cap: 5000
  diffusion_rate: 0.1
```

#### Sweep Configs (`content/config/sweeps/*/`)

Difficulty presets that override simulation settings:

```yaml
# content/config/sweeps/difficulty-easy/simulation.yml
economy:
  regen_scale: 1.0  # More forgiving regeneration
  demand_population_scale: 120000

environment:
  scarcity_event_threshold: 2.5  # Fewer crises
```

## Local Validation

### Using the Build Script

Validate all content before committing:

```bash
# Validate all content
python scripts/build_content.py

# Verbose output
python scripts/build_content.py --verbose

# Write manifest to file
python scripts/build_content.py --output manifest.json

# Validate custom content directory
python scripts/build_content.py --content /path/to/content
```

### Exit Codes

- `0`: All content validated successfully
- `1`: Validation errors found
- `2`: File or configuration errors

### Running Tests

```bash
# Run content loader tests
pytest tests/echoes/test_content_loader.py -v

# Run build script tests
pytest tests/scripts/test_build_content.py -v
```

## CI/CD Validation

Content is automatically validated on every pull request that modifies files in:

- `content/**/*.yml`
- `content/**/*.yaml`
- `scripts/build_content.py`
- `.github/workflows/content-*.yml`

The CI workflow:
1. Runs `scripts/build_content.py` to validate all content
2. Uploads a `content-manifest.json` artifact
3. Blocks PR merge if validation fails

See `.github/workflows/content-validation.yml` for workflow details.

## Troubleshooting

### Common Validation Errors

#### "World definition is missing 'city'"

Your `world.yml` is missing the required `city` section:

```yaml
# ❌ Invalid
factions: []

# ✅ Valid
city:
  id: my-city
  name: My City
  districts: []
factions: []
```

#### "unknown district 'X' in preferred_districts"

A story seed references a district that doesn't exist in `world.yml`:

```yaml
# In world.yml
districts:
  - id: downtown  # ← This is the valid ID

# In story_seeds.yml
preferred_districts:
  - down-town  # ❌ Typo - should be 'downtown'
```

#### "unknown agent 'X' in roles"

A story seed references an agent not defined in `world.yml`:

```yaml
# In world.yml
agents:
  - id: aria-volt  # ← Correct ID

# In story_seeds.yml
roles:
  agents:
    - aria_volt  # ❌ Wrong ID format (underscore vs hyphen)
```

#### "unknown followup 'X'"

A story seed references a followup seed that doesn't exist:

```yaml
story_seeds:
  - id: seed-a
    followups: [seed-b]  # ❌ seed-b must also be defined

  # ✅ Add the missing seed:
  - id: seed-b
    followups: []
```

#### "Schema validation error at X"

A field has an invalid type or value. Check the Pydantic models in
`src/gengine/echoes/core/models.py` for expected types.

### Debugging Tips

1. **Run with verbose mode** to see which files are being validated:
   ```bash
   python scripts/build_content.py --verbose
   ```

2. **Check YAML syntax** using an online validator or:
   ```bash
   python -c "import yaml; yaml.safe_load(open('content/worlds/default/world.yml'))"
   ```

3. **Review the test fixtures** in `tests/echoes/test_content_loader.py` for
   examples of valid content structure.

4. **Check entity IDs** - ensure IDs are consistent across files:
   - District IDs in `world.yml` must match references in `story_seeds.yml`
   - Agent IDs in `world.yml` must match `roles.agents` in seeds
   - Faction IDs in `world.yml` must match `roles.factions` in seeds

## Best Practices

1. **Use consistent ID formats** - prefer kebab-case (`my-district`) or
   snake_case (`my_district`), but be consistent within a world.

2. **Validate early and often** - run `scripts/build_content.py` before
   committing changes.

3. **Start with existing content** - copy and modify `content/worlds/default/`
   when creating new worlds.

4. **Keep followup chains valid** - if seed A references seed B, ensure B exists.

5. **Test with the simulation** - after validation, test your content:
   ```bash
   python scripts/run_headless_sim.py --world your-world --ticks 50
   ```
