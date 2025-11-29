# Handoff: Implement M9.1 AI Player Observer

## Context

This is a handoff to implement **Phase 9, Milestone 9.1 (AI Player Observer)** as documented in:
- `docs/simul/emergent_story_game_implementation_plan.md` (lines 344-377)
- `docs/simul/emergent_story_game_gdd.md` (lines 477-492)
- `README.md` (lines 478-486)

## Objective

Implement an AI observer that analyzes simulation state and generates structured commentary without taking actions. This enables:
- Testing narrative coherence programmatically
- Validating that simulation state is machine-readable
- Creating demo content for playtests
- Regression testing for balance changes

## Deliverables

### 1. Core Module: `src/gengine/ai_player/observer.py`

Create the AI observer module with:

```python
from typing import Optional, Dict, Any, List
from gengine.echoes.core.state import GameState
from gengine.echoes.sim.engine import SimEngine
from gengine.echoes.client import SimServiceClient

class ObserverAI:
    """
    Analyzes simulation state and generates structured commentary.
    Does not take actions - observation only.
    """
    
    def __init__(
        self, 
        engine: Optional[SimEngine] = None,
        service_url: Optional[str] = None
    ):
        """
        Connect to either local engine or remote service.
        Raises ValueError if neither or both provided.
        """
        pass
    
    def observe_tick(self, state: GameState) -> Dict[str, Any]:
        """
        Analyze a single tick and return structured observations.
        
        Returns:
            {
                "tick": int,
                "stability_trend": "rising" | "falling" | "stable",
                "concerns": List[str],  # High-priority issues
                "opportunities": List[str],  # Positive developments
                "story_seed_predictions": List[Dict],  # Seeds likely to trigger
                "faction_analysis": Dict,  # Legitimacy trends
                "narrative_coherence": float  # 0-1 score
            }
        """
        pass
    
    def generate_commentary(self, observation: Dict[str, Any]) -> str:
        """
        Convert structured observation to natural language commentary.
        """
        pass
    
    def detect_trends(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze multiple ticks to identify patterns.
        
        Returns:
            {
                "stability_trajectory": str,
                "crisis_probability": float,
                "dominant_faction": str,
                "underutilized_districts": List[str]
            }
        """
        pass
```

### 2. Execution Script: `scripts/run_ai_observer.py`

Create a CLI script:

```python
#!/usr/bin/env python3
"""
Run AI observer sessions with configurable parameters.

Usage:
    uv run python scripts/run_ai_observer.py --world default --ticks 100 --output build/observer.json
    uv run python scripts/run_ai_observer.py --service-url http://localhost:8000 --ticks 50
"""
import argparse
import json
from pathlib import Path
from gengine.ai_player.observer import ObserverAI
from gengine.echoes.sim.engine import SimEngine
from gengine.echoes.content import WorldLoader

def main():
    parser = argparse.ArgumentParser(description="Run AI observer session")
    parser.add_argument("--world", default="default", help="World to load")
    parser.add_argument("--ticks", type=int, default=100, help="Ticks to observe")
    parser.add_argument("--service-url", help="Simulation service URL (optional)")
    parser.add_argument("--output", help="JSON output path")
    parser.add_argument("--commentary", action="store_true", help="Generate natural language")
    parser.add_argument("--seed", type=int, help="Random seed for determinism")
    args = parser.parse_args()
    
    # Implementation here
    pass

if __name__ == "__main__":
    main()
```

### 3. Tests: `tests/ai_player/test_observer.py`

Create comprehensive test coverage:

```python
import pytest
from gengine.ai_player.observer import ObserverAI
from gengine.echoes.sim.engine import SimEngine
from gengine.echoes.content import WorldLoader

class TestObserverAI:
    def test_observer_connects_to_local_engine(self):
        """Observer can connect to local SimEngine."""
        pass
    
    def test_observer_requires_engine_or_service(self):
        """Observer raises ValueError if no connection provided."""
        pass
    
    def test_observe_tick_returns_structured_data(self):
        """observe_tick returns expected data structure."""
        pass
    
    def test_detect_stability_crash(self):
        """Observer detects when stability drops below threshold."""
        pass
    
    def test_predict_story_seed_activation(self):
        """Observer predicts which seeds are likely to trigger."""
        pass
    
    def test_generate_commentary_readable(self):
        """Generated commentary is valid natural language."""
        pass
    
    def test_trend_analysis_over_multiple_ticks(self):
        """Trend detection works over observation history."""
        pass
```

### 4. Documentation Updates

Update the following files:

**README.md** - Add new section after "Headless Regression Driver":

```markdown
## AI Observer

The AI observer analyzes simulation runs and generates structured commentary without taking actions:

```bash
# Basic observation session
uv run python scripts/run_ai_observer.py --world default --ticks 100 --output build/observer.json

# With natural language commentary
uv run python scripts/run_ai_observer.py --world default --ticks 100 --commentary

# Against running service
uv run python scripts/run_ai_observer.py --service-url http://localhost:8000 --ticks 50
```

The observer generates:
- Stability trend analysis
- Story seed trigger predictions
- Faction legitimacy tracking
- Narrative coherence scoring

Output includes structured JSON plus optional natural language commentary.
```

**gamedev-agent-thoughts.txt** - Log implementation progress:

```
[TIMESTAMP] HEAD [HASH] (feature/m9-1-ai-observer): Created branch for M9.1 AI Observer implementation.
[TIMESTAMP] Implemented ObserverAI core module with local/service connectivity and structured observation output.
[TIMESTAMP] Added run_ai_observer.py script with CLI args and JSON/commentary output modes.
[TIMESTAMP] Created comprehensive test suite covering observation, trend detection, and error cases.
[TIMESTAMP] Ran `uv run --group dev pytest tests/ai_player/ -v` -> N passed, coverage X%.
[TIMESTAMP] Captured observer telemetry via `uv run python scripts/run_ai_observer.py --world default --ticks 200 --seed 42 --output build/feature-m9-1-observer.json`.
[TIMESTAMP] Updated README with observer usage examples and output format documentation.
```

## Acceptance Criteria

- ✅ Observer connects to both local `SimEngine` and remote service via `SimServiceClient`
- ✅ `observe_tick()` returns structured analysis including stability trends, concerns, opportunities
- ✅ `detect_trends()` identifies patterns across multiple ticks
- ✅ `generate_commentary()` produces readable natural language summaries
- ✅ Integration test asserts observer detects scripted stability crash
- ✅ Test coverage ≥90% for `ai_player/observer.py`
- ✅ `scripts/run_ai_observer.py` executes successfully with both modes
- ✅ README includes observer invocation examples
- ✅ Telemetry captured in `build/feature-m9-1-observer.json`

## Implementation Notes

### Key Design Decisions

1. **No Privileged Access**: Observer uses only public APIs (`SimEngine.query_view()` or `SimServiceClient.state()`)

2. **Dual Connectivity**: Support both local and service modes like CLI does:
   ```python
   # Local mode
   observer = ObserverAI(engine=engine)
   
   # Service mode
   observer = ObserverAI(service_url="http://localhost:8000")
   ```

3. **Structured Output First**: Return dictionaries/dataclasses, not just text. Commentary is optional post-processing.

4. **Deterministic Analysis**: Given same state, produce same observations (no random scoring).

5. **Trend Window**: Keep rolling window of last N observations for pattern detection (suggest N=10).

### Suggested Analysis Heuristics

**Stability Trend**:
- Compare current stability to average of last 5 ticks
- "rising" if >5% improvement
- "falling" if >5% decline
- "stable" otherwise

**Story Seed Prediction**:
- Check if any seed's trigger conditions are within 20% of threshold
- Return list of seeds + confidence score

**Narrative Coherence**:
- Score based on: are story seeds triggering? Are agent actions diverse? Is environment changing?
- Formula suggestion: `(seed_matches + unique_agent_actions + env_deltas) / expected_baseline`

**Concerns Detection**:
- Stability < 0.3: "City stability critically low"
- Unrest > 0.8: "Widespread unrest across districts"
- Pollution > 0.9: "Environmental collapse imminent"
- Faction legitimacy delta < -0.1: "Faction losing popular support"

## Testing Strategy

1. **Unit Tests**: Each method in isolation with mocked state
2. **Integration Test**: Full 100-tick observation run
3. **Regression Test**: Compare output to golden snapshot
4. **Service Mode Test**: Spin up FastAPI service, connect observer

## Example Usage After Implementation

```bash
# Run observer for 200 ticks
uv run python scripts/run_ai_observer.py \
  --world default \
  --ticks 200 \
  --seed 42 \
  --output build/observer-baseline.json \
  --commentary

# Output excerpt:
# Tick 50: Stability falling (0.67 → 0.61). Industrial Tier pollution approaching critical.
# Story seed "Energy Quota Crisis" predicted (confidence: 0.78).
# Union of Flux legitimacy trending upward (+0.15 over 10 ticks).
```

## Dependencies

All required dependencies already in `pyproject.toml`:
- `pydantic` for data models
- Existing `gengine.echoes.sim` and `gengine.echoes.client` modules
- No new external packages needed

## Workflow Compliance

This handoff follows the documented development workflow:

1. ✅ Branch: Create `feature/m9-1-ai-observer` from main
2. ✅ Docs: Implementation plan already updated (Phase 9)
3. ✅ Tests: Test suite specified above
4. ✅ Telemetry: Capture observer output as `build/feature-m9-1-observer.json`
5. ✅ Coverage: Target ≥90% for new module
6. ✅ Logging: Update `gamedev-agent-thoughts.txt` throughout

## Questions for PM (if any)

None - requirements are clear from Phase 9 documentation. Proceed with implementation.

## Related Issues/PRs

This is the first AI player milestone. Future milestones (M9.2-M9.4) will build on this foundation.

---

**Ready to implement?** Create branch `feature/m9-1-ai-observer` and begin with `src/gengine/ai_player/observer.py`.
