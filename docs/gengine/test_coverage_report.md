# Test Coverage & Quality Report: Core Systems

**Date:** December 2, 2025
**Scope:** Core Simulation Systems (`src/gengine/echoes/sim`, `src/gengine/echoes/systems`)

## 1. Executive Summary

The core simulation systems (`SimEngine`, `AgentSystem`, `FactionSystem`, etc.) have high *line coverage* (85-99%), indicating that most code paths are executed during testing. However, the *quality* of these tests is primarily "smoke testing" or "happy path" verification. They ensure the system runs without crashing and produces deterministic output, but they often fail to verify the *correctness* of the underlying logic, edge cases, or complex state transitions.

Significant gaps exist in testing the AI Player, Gateway, and LLM integration layers, which have near-zero coverage.

## 2. Coverage Analysis

| Component             | Line Coverage | Assessment                                                                                       |
| :-------------------- | :------------ | :----------------------------------------------------------------------------------------------- |
| **SimEngine**         | 85%           | Good line coverage, but misses error handling and new API endpoints (Explanations, Progression). |
| **AgentSystem**       | 95%           | High coverage, but tests are superficial (determinism checks).                                   |
| **FactionSystem**     | 95%           | High coverage, tests specific behaviors but relies on brittle RNG seeding.                       |
| **EconomySystem**     | 99%           | Excellent line coverage.                                                                         |
| **EnvironmentSystem** | 96%           | Excellent line coverage.                                                                         |
| **ProgressionSystem** | 96%           | Excellent line coverage.                                                                         |
| **AI Player / LLM**   | 0-20%         | **Critical Gap**. These systems are effectively untested.                                        |

## 3. Detailed Gap Analysis

### 3.1. Simulation Engine (`SimEngine`)
*   **Missing API Tests**: The `SimEngine` exposes several methods that are not tested:
    *   `initialize_state`: Error handling for missing arguments.
    *   `director_feed`: Completely untested.
    *   `Explanations API`: `query_timeline`, `explain_metric`, etc., are not verified at the engine level.
    *   `Progression API`: `progression_summary`, `calculate_success_chance`, etc., are not verified.
*   **Error Handling**: `ValueError` checks for invalid inputs (e.g., unknown views) are missing.
*   **Integration**: The interaction between `SimEngine` and the `ProgressionSystem` is not explicitly verified (e.g., does a tick actually update progression?).

### 3.2. Agent System (`AgentSystem`)
*   **Logic Verification**: Tests verify that agents *do something* deterministically, but not *why*.
    *   **Trait Influence**: No tests verify that high `empathy` actually increases the probability of `STABILIZE_UNREST`.
    *   **Fallback Logic**: No tests for scenarios where no valid options exist.
*   **Edge Cases**: Handling of agents with missing data (no district, no faction) is not explicitly tested.

### 3.3. Faction System (`FactionSystem`)
*   **Brittle Tests**: Tests rely on specific `random.Random` seeds to force outcomes. If the internal order of checks changes, these tests will break even if the logic is correct.
*   **State Transitions**: While some state changes are checked (e.g., legitimacy change), the exact magnitude of change is often not verified against the configuration.

### 3.4. General Gaps
*   **Persistence**: `save/load` cycles are not rigorously tested to ensure 100% state fidelity.
*   **Integration**: Few tests verify the chain of cause-and-effect across systems (e.g., Agent Action -> District Modifier -> Faction Reaction -> Economy Shift).
*   **Performance**: No benchmarks or stress tests to verify the engine stays within tick limits under load.

## 4. Recommendations

### 4.1. Immediate Improvements (High Priority)
1.  **Verify Logic, Not Just Execution**:
    *   Refactor `AgentSystem` tests to mock the RNG or use statistical verification to ensure traits influence decisions as expected.
    *   Add unit tests for `AgentSystem._decide` that test specific input combinations (e.g., "High Unrest + High Empathy = High Score for Stabilize").
2.  **Expand SimEngine Coverage**:
    *   Add tests for all `SimEngine` public methods, including Explanations and Progression APIs.
    *   Test error conditions (invalid inputs, uninitialized state).
3.  **Decouple Faction Tests from RNG**:
    *   Inject a mock RNG or deterministic "Dice" object to force specific decision paths without relying on magic seeds.

### 4.2. Strategic Improvements (Medium Priority)
1.  **Integration Testing**:
    *   Create a "Scenario" test suite that runs the engine for N ticks and asserts complex state outcomes (e.g., "A faction collapse scenario").
2.  **AI/LLM Mocking**:
    *   Implement mock providers for LLM services to enable testing of `gengine.echoes.llm` and `gengine.ai_player` without making real API calls.
3.  **Property-Based Testing**:
    *   Use `hypothesis` or similar to generate random valid GameStates and ensure the engine never crashes or produces invalid states (e.g., negative resources).

### 4.3. Long-Term
1.  **Performance Regression Testing**: Add tests that fail if tick execution time exceeds a threshold.
2.  **Snapshot Fidelity**: Test that `save() -> load() -> save()` produces identical files.
