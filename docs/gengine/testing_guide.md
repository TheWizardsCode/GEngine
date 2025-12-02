# GEngine Agents Testing Guide

## 1. Purpose and Scope

This document describes how to test the GEngine agents project, including:

- How to run tests locally.
- How tests are organized.
- How to add and extend tests.
- How to validate and test Kubernetes infrastructure.
- Recommendations for improving the overall testing process.

It assumes you are in the project root (the directory containing `pyproject.toml`,

`pytest.ini`, and `docker-compose.yml`).

## 2. Local Test Setup

- Install the package and test dependencies:

```bash
pip install -e .
pip install pytest
# If extras are defined:
# pip install -e ".[dev,test]"
```

- Configure any environment variables used by tests

  (for example, fake LLM keys or gateway URLs).

  Prefer dummy values in test environments so that no real external calls are made.

## 3. Running the Test Suite

### 3.1 Full test run

Run all tests from the project root:

```bash
pytest -v
```

`pytest.ini` configures test discovery, markers, and default options.

### 3.2 Targeted runs

Run a specific test directory:

```bash
# AI player tests
pytest -v tests/ai_player

# Echoes tests
pytest -v tests/echoes
```

Run a single test file:

```bash
pytest -v tests/echoes/test_service_api.py
```

Run an individual test function:

```bash
pytest -v tests/echoes/test_service_api.py::test_example_behavior
```

### 3.3 Coverage (if enabled)

If `pytest-cov` is configured, you can gather coverage:

```bash
pytest -v --cov=src/gengine --cov-report=term-missing
```

## 4. Test Layout and Conventions

### 4.1 AI Player tests (`tests/ai_player/`)

Focus: AI decision-making, strategies, and actor/observer behavior.

Typical files:

- `test_actor.py`: AI actor behavior and action selection.
- `test_observer.py`: observer/critic behavior, state evaluation.
- `test_strategies.py`: strategy components and policies.

Guidelines:

- Keep tests **pure and fast**

  (no network or filesystem where possible).
- Use descriptive test names

  (e.g. `test_chooses_defensive_action_on_low_health`).
- Mock external dependencies, especially anything that would invoke LLMs

  or external services.

### 4.2 Echoes tests (`tests/echoes/`)

Focus: Echoes game systems, LLM integration, gateway and service APIs, CLI, and content.

Indicative files:

- Systems and game logic:
  - `test_agent_system.py`
  - `test_campaign.py`
  - `test_economy_system.py`
  - `test_environment_system.py`
  - `test_faction_system.py`
  - `test_progression.py`
- LLM-related logic:
  - `test_llm_providers.py`
  - `test_llm_prompts.py`
  - `test_llm_settings.py`
  - `test_llm_intents.py`
  - `test_openai_provider.py`
  - `test_anthropic_provider.py`
  - `test_llm_app.py`
- Gateway and service:
  - `test_gateway_client.py`
  - `test_gateway_llm_client.py`
  - `test_gateway_intent_mapper.py`
  - `test_gateway_service.py`
  - `test_service_api.py`
  - `test_service_client.py`
- UX and content:
  - `test_cli_shell.py`
  - `test_content_loader.py`
  - `test_display.py`
  - `test_explanations.py`
  - `test_post_mortem.py`

Use fixtures from `tests/echoes/conftest.py` to:

- Initialize simulations and game state.
- Provide fake LLM providers / responses.
- Prepare content and configuration contexts.

Ensure tests do not call real LLM endpoints; always work with mocks/fakes.

### 4.3 Script tests (`tests/scripts/`)

Focus: scripts under `scripts/`, such as:

- `run_headless_sim.py`
- `run_difficulty_sweeps.py`
- `run_ai_observer.py`
- `eoe_dump_state.py`
- `analyze_difficulty_profiles.py`
- `plot_environment_trajectories.py`

Guidelines:

- Encapsulate script logic into functions in `scripts/` (e.g. `main()` with

  injectable parameters)

  to keep tests simple and fast.

- Use temporary directories and test configurations to avoid modifying real data.

- Mock external systems (e.g., Docker, network, filesystem heavy operations)

  where necessary.

## 5. Config-Driven and Scenario Testing

The project uses YAML and JSON configuration to describe simulations and builds:

- `content/config/simulation.yml` and `content/config/sweeps/*` define

  simulation and sweep parameters.

- `build/*.json` (e.g. difficulty and telemetry configs) define specific

  feature runs.

Testing recommendations:

- Use small, self-contained configuration snippets for tests

  (either reusing existing configs

  or adding test-only ones under `tests/resources`).
- Validate:
  - Parsing and schema of configs.
  - Behavior changes when altering key parameters.
  - That sweep definitions are correctly interpreted by scripts in

  `scripts/`.

## 6. Kubernetes and Infrastructure Testing

The repository includes Kubernetes configuration under `k8s/`:

- `k8s/base/` contains:
  - `configmap.yaml`
  - `gateway-deployment.yaml` / `gateway-service.yaml`
  - `llm-deployment.yaml` / `llm-service.yaml`
  - `simulation-deployment.yaml` / `simulation-service.yaml`
  - `ingress.yaml`
  - `namespace.yaml`
  - `kustomization.yaml`
- `k8s/overlays/local/` and `k8s/overlays/staging/` contain

  environment-specific overrides.

Testing K8s infrastructure involves both **static checks** and **runtime

smoke tests**.

### 6.1 Static validation of manifests

These tests ensure manifests are syntactically correct and compatible

with the target Kubernetes version.

Examples (run from repo root):

```bash
# Validate base manifests against the API server

# (cluster required)
kubectl apply --dry-run=server -k k8s/base

# Validate overlays
kubectl apply --dry-run=server -k k8s/overlays/local
kubectl apply --dry-run=server -k k8s/overlays/staging
```

You can also use tools like `kubeconform` or `kube-linter`:

```bash
kubectl kustomize k8s/base | kubeconform -strict -ignore-missing-schemas
kube-linter lint k8s/base
```

### 6.2 Local Kubernetes integration tests (Minikube / kind)

Follow the setup in:

- `docs/gengine/Create_Local_Kubernetes_With_Minikube.md`
- `docs/gengine/Deploy_GEngine_To_Kubernetes.md`

Typical flow:

```bash
# Start a local cluster
minikube start

# Option 1: Build image inside Minikubes Docker
eval $(minikube docker-env)
docker build -t gengine-agents:local .

# Deploy using Kustomize overlay
kubectl apply -k k8s/overlays/local
```

Once deployed:

1. Verify pods and services:

```bash
kubectl get pods -n <namespace>
kubectl get services -n <namespace>
```

1. Port-forward the gateway or simulation service:

```bash
kubectl port-forward -n <namespace> svc/gateway 8080:80
```

1. Run existing API tests against the forwarded port:

```bash
GENGINE_GATEWAY_URL=http://localhost:8080 pytest -v tests/echoes/test_service_api.py
```

Optionally, create a Kubernetes Job or pod that runs tests from within the cluster.

### 6.3 Docker Compose-based integration testing

For non-K8s integration:

```bash
docker compose up -d
```

Then run tests that depend on the gateway or simulation

(pointing them at the compose services):

```bash
GENGINE_GATEWAY_URL=http://localhost:<gateway-port> \
pytest -v tests/echoes/test_service_client.py
```

## 7. CI Pipeline Expectations

A recommended CI pipeline for this repo should:

1. Install dependencies.
2. Run linting/static analysis (if configured).
3. Run unit tests (e.g., `tests/ai_player`, `tests/echoes`).
4. Optionally run integration tests with Docker Compose or a K8s cluster.
5. Perform Kubernetes manifest validation using `kubectl` dry-run and/or `kubeconform`/`kube-linter`.
6. Publish test and coverage reports as CI artifacts.

Example commands:

```bash
pytest -v tests/ai_player tests/echoes
kubectl apply --dry-run=server -k k8s/base
```

## 8. Adding New Tests

1. Identify where your code lives under `src/gengine/...`.
2. Add or extend tests in the corresponding directory under `tests/`

   (e.g., `tests/ai_player/` for AI logic, `tests/echoes/` for Echoes systems).
3. Reuse fixtures in `conftest.py` rather than duplicating setup.
4. Keep tests deterministic and independent of external services.
5. Run targeted tests first, then the full suite:

```bash
pytest -v tests/echoes/test_new_feature.py
pytest -v
```

## 9. Recommendations and Future Improvements

### 9.1 Application tests

- Increase edge-case coverage:
  - AI strategies under extreme game states (no valid moves, max/min resources).
  - Campaign/progression at boundaries (start/end of campaign, rapid difficulty spikes).
- Harden error-path testing:
  - Invalid or missing content.
  - Misconfigured gateways or LLM providers.
  - Timeouts and 4xx/5xx scenarios in service and gateway tests.
- Standardize LLM mocking:
  - Central helpers for fake providers and canned responses.
  - Guardrails to prevent accidental real API calls during tests.

### 9.2 K8s and infra tests

- Add a dedicated K8s validation job in CI:
  - Run `kubectl apply --dry-run=server -k k8s/base` and overlays.
  - Fail fast on invalid fields or schema mismatches.
- Integrate Kubernetes linting:
  - Use `kube-linter` (or similar) to enforce readiness/liveness probes,

    resource requests/limits, and basic security best practices.
- Introduce K8s smoke tests:
  - A small `pytest` suite that:
    - Asserts Deployments are ready.
    - Sends minimal requests to the gateway and simulation services.
    - Verifies non-2xx responses are handled as expected.

### 9.3 Test ergonomics

- Introduce markers such as `unit`, `integration`, and `k8s`:

```python
import pytest

@pytest.mark.unit
def test_basic_behavior():
    ...
```

Then select tests via:

```bash
pytest -m unit
pytest -m "integration and not k8s"
pytest -m k8s
```

- Keep this testing guide updated whenever new test types, scripts,

  or infra checks are added.
