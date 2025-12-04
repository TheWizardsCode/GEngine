# Deploy GEngine to Kubernetes

## Introduction

This executable document deploys the GEngine Echoes of Emergence services to
a Kubernetes cluster. It supports both local development using Minikube and
staging environment deployments.

Summary:

- Build and load container images into the cluster.
- Deploy simulation, gateway, and LLM services using Kustomize overlays.
- Verify service health and connectivity.

## Prerequisites

Ensure you have a running Kubernetes cluster. For local development, follow
[Create_Local_Kubernetes_With_Minikube.md](Create_Local_Kubernetes_With_Minikube.md)
to provision a Minikube cluster first.

Summary:

- Kubernetes cluster is running and accessible via kubectl.
- Docker is available for building container images.
- The GEngine repository is cloned locally.

### Required CLI Tools

Confirm that kubectl and Docker are available and configured.

```bash
kubectl version --client
docker version --format '{{.Server.Version}}'
```

<!-- expected_similarity="Client Version: v.*" -->

Representative output:

```text
Client Version: v1.30.1
Kustomize Version: v5.3.0
24.0.6
```

### Verify Cluster Access

Ensure kubectl can communicate with the cluster. For Minikube, set the
context to your profile.

```bash
export GENGINE_K8S_CONTEXT="${GENGINE_K8S_CONTEXT:-minikube}"
kubectl config use-context "${GENGINE_K8S_CONTEXT}"
kubectl cluster-info
```

<!-- expected_similarity="Kubernetes control plane is running" -->

Representative output:

```text
Switched to context "minikube".
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

## Setting Up the Environment

Define environment variables that control the deployment.

```bash
export GENGINE_REPO_ROOT="${GENGINE_REPO_ROOT:-$(pwd)}"
export GENGINE_DEPLOY_ENV="${GENGINE_DEPLOY_ENV:-local}"  # local or staging
export GENGINE_IMAGE_TAG="${GENGINE_IMAGE_TAG:-latest}"
export GENGINE_NAMESPACE="${GENGINE_NAMESPACE:-gengine}"

echo "Environment variables configured."
```

<!-- expected_similarity="Environment variables configured." -->

Representative output:

```text
Environment variables configured.
```

Print the environment configuration for verification.

```bash
printf '%-25s %-50s %s\n' "Variable" "Value" "Status"
env_vars=(
  GENGINE_REPO_ROOT
  GENGINE_DEPLOY_ENV
  GENGINE_IMAGE_TAG
  GENGINE_NAMESPACE
  GENGINE_K8S_CONTEXT
)
for var in "${env_vars[@]}"; do
  value="${!var:-}"
  status="OK"
  if [[ -z "${value}" ]]; then
    status="MISSING"
  fi
  printf '%-25s %-50s %s\n' "${var}" "${value}" "${status}"
done
```

<!-- expected_similarity="GENGINE_DEPLOY_ENV.*OK" -->

Representative output:

```text
Variable                  Value                                              Status
GENGINE_REPO_ROOT         /home/user/GEngine                                 OK
GENGINE_DEPLOY_ENV        local                                              OK
GENGINE_IMAGE_TAG         latest                                             OK
GENGINE_NAMESPACE         gengine                                            OK
GENGINE_K8S_CONTEXT       minikube                                           OK
```

## Steps

### Step 1: Build the Container Image

Build the GEngine Docker image. This uses the multi-stage Dockerfile that
supports all three services via the SERVICE environment variable.

```bash
cd "${GENGINE_REPO_ROOT}"
docker build -t "gengine:${GENGINE_IMAGE_TAG}" --target runtime .
```

<!-- 
expected_similarity="Successfully built\|Successfully tagged\|exporting to image"
-->

Representative output:

```text
[+] Building 45.2s (15/15) FINISHED
 => exporting to image
 => => naming to docker.io/library/gengine:latest
```

### Step 2: Load Image into Minikube (Local Only)

For local Minikube deployments, load the image directly into Minikube's
Docker daemon so Kubernetes can access it without a registry.

```bash
if [[ "${GENGINE_DEPLOY_ENV}" == "local" ]]; then
  echo "Loading image into Minikube..."
  minikube image load "gengine:${GENGINE_IMAGE_TAG}"
  echo "Image loaded successfully."
else
  echo "Skipping Minikube image load for ${GENGINE_DEPLOY_ENV} environment."
fi
```

<!-- expected_similarity="Image loaded successfully\|Skipping Minikube" -->

Representative output:

```text
Loading image into Minikube...
Image loaded successfully.
```

### Step 3: Deploy Using Kustomize

Apply the Kustomize overlay for the target environment. The base manifests
define the core resources, and overlays customize for local or staging.

```bash
cd "${GENGINE_REPO_ROOT}"
OVERLAY_PATH="k8s/overlays/${GENGINE_DEPLOY_ENV}"

if [[ ! -d "${OVERLAY_PATH}" ]]; then
  echo "ERROR: Overlay not found at ${OVERLAY_PATH}"
  exit 1
fi

echo "Deploying GEngine to ${GENGINE_DEPLOY_ENV} environment..."
kubectl apply -k "${OVERLAY_PATH}"
```

<!-- expected_similarity="namespace/gengine created\|configured\|unchanged" -->

Representative output:

```text
Deploying GEngine to local environment...
namespace/gengine created
configmap/gengine-config created
deployment.apps/simulation created
deployment.apps/gateway created
deployment.apps/llm created
service/simulation created
service/gateway created
service/llm created
ingress.networking.k8s.io/gengine-ingress created
```

### Step 4: Wait for Deployments to be Ready

Wait for all deployments to become available before proceeding.

```bash
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment -n "${GENGINE_NAMESPACE}" --timeout=120s
```

<!-- expected_similarity="successfully rolled out" -->

Representative output:

```text
Waiting for deployments to be ready...
deployment "simulation" successfully rolled out
deployment "gateway" successfully rolled out
deployment "llm" successfully rolled out
```

### Step 5: Verify Running Pods

Check that all pods are running and healthy.

```bash
kubectl get pods -n "${GENGINE_NAMESPACE}" -o wide
```

<!-- expected_similarity="Running" -->

Representative output:

```text
NAME                          READY   STATUS    RESTARTS   AGE   IP            NODE
simulation-abc123-xyz         1/1     Running   0          45s   10.244.0.5    minikube
gateway-def456-uvw            1/1     Running   0          45s   10.244.0.6    minikube
llm-ghi789-rst                1/1     Running   0          45s   10.244.0.7    minikube
```

### Step 6: Get Service Endpoints

Retrieve the service endpoints for accessing the GEngine services.

For local Minikube deployments using NodePort:

```bash
if [[ "${GENGINE_DEPLOY_ENV}" == "local" ]]; then
  MINIKUBE_IP=$(minikube ip)
  echo "GEngine Services (Minikube NodePort):"
  echo "  Simulation: http://${MINIKUBE_IP}:30000"
  echo "  Gateway:    http://${MINIKUBE_IP}:30100"
  echo "  LLM:        http://${MINIKUBE_IP}:30001"
fi
```

<!-- expected_similarity="Simulation: http://.*:30000" -->

Representative output:

```text
GEngine Services (Minikube NodePort):
  Simulation: http://192.168.49.2:30000
  Gateway:    http://192.168.49.2:30100
  LLM:        http://192.168.49.2:30001
```

For staging or production deployments using Ingress:

```bash
if [[ "${GENGINE_DEPLOY_ENV}" != "local" ]]; then
  echo "GEngine Services (via Ingress):"
  kubectl get ingress -n "${GENGINE_NAMESPACE}"
fi
```

## Verification

### Verify Service Health

Test the health endpoints of all services to confirm they are responding.

```bash
if [[ "${GENGINE_DEPLOY_ENV}" == "local" ]]; then
  MINIKUBE_IP=$(minikube ip)
  SIM_URL="http://${MINIKUBE_IP}:30000"
  GW_URL="http://${MINIKUBE_IP}:30100"
  LLM_URL="http://${MINIKUBE_IP}:30001"
else
  # For staging, use kubectl port-forward or ingress
  echo "For staging, set up port-forwarding or use ingress URLs."
  SIM_URL="http://localhost:8000"
  GW_URL="http://localhost:8100"
  LLM_URL="http://localhost:8001"
fi

echo "Testing service health endpoints..."

sim_status=$(curl -s -o /dev/null -w "%{http_code}" "${SIM_URL}/healthz" 2>/dev/null || echo "failed")
gw_status=$(curl -s -o /dev/null -w "%{http_code}" "${GW_URL}/healthz" 2>/dev/null || echo "failed")
llm_status=$(curl -s -o /dev/null -w "%{http_code}" "${LLM_URL}/healthz" 2>/dev/null || echo "failed")

printf '%-15s %-40s %s\n' "Service" "URL" "Status"
printf '%-15s %-40s %s\n' "Simulation" "${SIM_URL}/healthz" "${sim_status}"
printf '%-15s %-40s %s\n' "Gateway" "${GW_URL}/healthz" "${gw_status}"
printf '%-15s %-40s %s\n' "LLM" "${LLM_URL}/healthz" "${llm_status}"

if [[ "${sim_status}" == "200" && "${gw_status}" == "200" && "${llm_status}" == "200" ]]; then
  echo ""
  echo "PASS: All services are healthy."
else
  echo ""
  echo "WARN: Some services may not be ready yet. Retry in a few seconds."
fi
```

<!-- expected_similarity="Simulation.*200\|PASS: All services are healthy" -->

Representative output:

```text
Testing service health endpoints...
Service         URL                                      Status
Simulation      http://192.168.49.2:30000/healthz       200
Gateway         http://192.168.49.2:30100/healthz       200
LLM             http://192.168.49.2:30001/healthz       200

PASS: All services are healthy.
```

### Verify Simulation API

Test the simulation service API to confirm it responds with game state.

```bash
if [[ "${GENGINE_DEPLOY_ENV}" == "local" ]]; then
  MINIKUBE_IP=$(minikube ip)
  SIM_URL="http://${MINIKUBE_IP}:30000"
else
  SIM_URL="http://localhost:8000"
fi

echo "Querying simulation state..."
curl -s "${SIM_URL}/state?detail=summary" | head -c 500
echo ""
```

<!-- expected_similarity="tick\|world\|state" -->

Representative output:

```text
Querying simulation state...
{"tick":0,"world":"default","stability":100,"factions":[...],"agents":[...]}
```

### View Logs

Check the logs of each service for any errors.

```bash
echo "=== Simulation Logs (last 10 lines) ==="
kubectl logs -n "${GENGINE_NAMESPACE}" -l app.kubernetes.io/component=simulation --tail=10

echo ""
echo "=== Gateway Logs (last 10 lines) ==="
kubectl logs -n "${GENGINE_NAMESPACE}" -l app.kubernetes.io/component=gateway --tail=10

echo ""
echo "=== LLM Logs (last 10 lines) ==="
kubectl logs -n "${GENGINE_NAMESPACE}" -l app.kubernetes.io/component=llm --tail=10
```

<!-- expected_similarity="Starting.*Service" -->

Representative output:

```text
=== Simulation Logs (last 10 lines) ===
Starting Simulation Service on port 8000...
INFO:uvicorn.error:Started server process
INFO:uvicorn.error:Waiting for application startup.
INFO:uvicorn.error:Application startup complete.
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8000

=== Gateway Logs (last 10 lines) ===
Starting Gateway Service on port 8100...
INFO:uvicorn.error:Started server process
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8100

=== LLM Logs (last 10 lines) ===
Starting LLM Service on port 8001...
INFO:uvicorn.error:Started server process
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8001
```

## Cleanup

To remove the GEngine deployment from the cluster:

```bash
echo "To delete the GEngine deployment, run:"
echo "  kubectl delete -k k8s/overlays/${GENGINE_DEPLOY_ENV}"
echo ""
echo "To delete the namespace entirely:"
echo "  kubectl delete namespace ${GENGINE_NAMESPACE}"
```

Representative output:

```text
To delete the GEngine deployment, run:
  kubectl delete -k k8s/overlays/local

To delete the namespace entirely:
  kubectl delete namespace gengine
```

## Troubleshooting

### Pods Not Starting

If pods are stuck in `Pending` or `ImagePullBackOff`:

```bash
# Check pod events
kubectl describe pod -n "${GENGINE_NAMESPACE}" -l app.kubernetes.io/part-of=gengine

# For local deployments, ensure the image is loaded
minikube image list | grep gengine
```

### Service Not Responding

If health checks fail:

```bash
# Check if pods are running
kubectl get pods -n "${GENGINE_NAMESPACE}"

# Check pod logs for errors
kubectl logs -n "${GENGINE_NAMESPACE}" -l app.kubernetes.io/component=simulation

# Test connectivity from within the cluster
kubectl run -n "${GENGINE_NAMESPACE}" --rm -it --image=curlimages/curl test-curl -- \
  curl -v http://simulation.gengine.svc.cluster.local:8000/healthz
```

### Resource Constraints

If pods are being OOMKilled or throttled:

```bash
# Check resource usage
kubectl top pods -n "${GENGINE_NAMESPACE}"

# Increase limits in the overlay's kustomization.yaml and redeploy
```

### Metrics Not Being Scraped

If Prometheus is not scraping your services:

```bash
# Verify Prometheus annotations are present on pods
kubectl get pods -n "${GENGINE_NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}: {.metadata.annotations}{"\n"}{end}'

# Check if Prometheus can reach the service
kubectl run -n "${GENGINE_NAMESPACE}" --rm -it --image=curlimages/curl test-curl -- \
  curl -v http://simulation.gengine.svc.cluster.local:8000/metrics

# If using Prometheus Operator, check ServiceMonitor status
kubectl get servicemonitors -n "${GENGINE_NAMESPACE}"
```

## Resource Sizing

GEngine services have differentiated resource allocations based on their
workload characteristics. This section explains the rationale and methodology
for tuning Kubernetes resource requests and limits.

### Service Resource Profiles

| Service | Role | CPU Profile | Memory Profile |
|---------|------|-------------|----------------|
| Simulation | Game logic, tick processing, state management | CPU-intensive (many subsystems per tick) | Higher (game state, telemetry) |
| Gateway | WebSocket routing, HTTP proxying | Low (I/O bound) | Low-moderate (connection buffers) |
| LLM | Natural language processing via external APIs | Moderate (I/O bound to LLM providers) | Higher (request/response context) |

### Default Resource Allocations

**Base Configuration** (`k8s/base/`):

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| Simulation | 300m | 750m | 384Mi | 768Mi |
| Gateway | 150m | 400m | 192Mi | 384Mi |
| LLM | 200m | 500m | 320Mi | 640Mi |

**Local Overlay** (`k8s/overlays/local/`):
Reduced resources for Minikube/local development (~50% of base).

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| Simulation | 200m | 500m | 256Mi | 512Mi |
| Gateway | 100m | 250m | 128Mi | 256Mi |
| LLM | 100m | 300m | 192Mi | 384Mi |

**Staging Overlay** (`k8s/overlays/staging/`):
Higher resources for production-like load testing (~2x base).

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| Simulation | 600m | 1500m | 768Mi | 1536Mi |
| Gateway | 300m | 800m | 384Mi | 768Mi |
| LLM | 400m | 1000m | 640Mi | 1280Mi |

### Sizing Methodology

The resource allocations were determined using:

1. **Workload Analysis**: Each service's role was analyzed:
   - Simulation processes multiple subsystems per tick (agents, factions,
     economy, environment, narrator) requiring higher CPU
   - Gateway handles WebSocket connections with minimal processing overhead
   - LLM service buffers requests to external APIs, requiring memory for context

2. **Conservative Baseline**: Base limits set to 2x typical observed usage
   to provide headroom for traffic bursts without causing throttling

3. **Request:Limit Ratio**: Approximately 1:2 ratio between requests and
   limits allows burstable workloads while ensuring QoS under load

4. **Environment Scaling**:
   - Local: ~50% of base (fits in typical 4-8GB Minikube clusters)
   - Staging: ~2x base (realistic load testing with headroom)

### Tuning Resources

To adjust resources for your environment:

1. **Monitor Current Usage**:
   ```bash
   kubectl top pods -n "${GENGINE_NAMESPACE}"
   ```

2. **Check for Throttling or OOMKills**:
   ```bash
   kubectl describe pod -n "${GENGINE_NAMESPACE}" -l app.kubernetes.io/component=simulation
   ```

3. **Update Overlay Configuration**:
   Edit the appropriate overlay's `kustomization.yaml` and redeploy:
   ```bash
   kubectl apply -k k8s/overlays/${GENGINE_DEPLOY_ENV}
   ```

4. **Validate with Smoke Tests**:
   ```bash
   ./scripts/k8s_smoke_test.sh --load
   ```

### Common Tuning Scenarios

**High Tick Rate Simulations**:
If running at higher tick rates (>10 ticks/sec), increase simulation CPU:
```yaml
- op: replace
  path: /spec/template/spec/containers/0/resources/limits/cpu
  value: "1000m"
```

**Many Concurrent Players**:
For high connection counts, increase gateway memory:
```yaml
- op: replace
  path: /spec/template/spec/containers/0/resources/limits/memory
  value: "512Mi"
```

**LLM-Heavy Workflows**:
If using LLM service extensively, increase memory for context buffering:
```yaml
- op: replace
  path: /spec/template/spec/containers/0/resources/limits/memory
  value: "1Gi"
```

## Monitoring and Observability

GEngine services are instrumented with Prometheus-compatible metrics endpoints
for monitoring and alerting. Health checks (`/healthz`) are separate from
metrics collection (`/metrics`) to allow independent control of readiness
probes and observability scraping.

### Health Check Endpoints

Health checks are used for Kubernetes liveness and readiness probes:

| Service    | Port | Health Endpoint | Description                           |
| ---------- | ---- | --------------- | ------------------------------------- |
| Simulation | 8000 | `/healthz`      | Returns `{"status": "ok"}`            |
| Gateway    | 8100 | `/healthz`      | Returns status and upstream URLs      |
| LLM        | 8001 | `/healthz`      | Returns status, provider, and model   |

### Metrics Endpoints

Each service exposes dedicated metrics for Prometheus scraping:

| Service    | Port | Metrics Endpoint | Description                        |
| ---------- | ---- | ---------------- | ---------------------------------- |
| Simulation | 8000 | `/metrics`       | Tick count, environment, profiling |
| Gateway    | 8100 | `/metrics`       | Request counts, latencies, connections, LLM integration |
| LLM        | 8001 | `/metrics`       | Request counts, latencies, errors, provider stats, token usage |

### Example Metrics Responses

**Simulation Service** (`/metrics`):
```json
{
  "tick": 42,
  "environment": {
    "temperature": 0.5,
    "instability": 0.2,
    "tension": 0.3
  },
  "profiling": {
    "tick_ms_p50": 12.5,
    "tick_ms_p95": 25.0,
    "tick_ms_max": 45.0
  }
}
```

**Gateway Service** (`/metrics`) - Prometheus text format:
```text
# HELP gateway_requests_total Total number of requests processed
# TYPE gateway_requests_total counter
gateway_requests_total 150.0
# HELP gateway_requests_by_type_total Requests by type
# TYPE gateway_requests_by_type_total counter
gateway_requests_by_type_total{request_type="command"} 120.0
gateway_requests_by_type_total{request_type="natural_language"} 30.0
# HELP gateway_errors_total Total number of errors
# TYPE gateway_errors_total counter
gateway_errors_total 2.0
# HELP gateway_active_connections Number of active WebSocket connections
# TYPE gateway_active_connections gauge
gateway_active_connections 3.0
# HELP gateway_request_latency_seconds Request latency in seconds
# TYPE gateway_request_latency_seconds histogram
gateway_request_latency_seconds_bucket{request_type="command",le="0.1"} 80.0
gateway_request_latency_seconds_bucket{request_type="command",le="0.5"} 115.0
gateway_request_latency_seconds_bucket{request_type="command",le="+Inf"} 120.0
gateway_request_latency_seconds_count{request_type="command"} 120.0
gateway_request_latency_seconds_sum{request_type="command"} 5.46
```

**LLM Service** (`/metrics`) - Prometheus text format:
```text
# HELP llm_requests_total Total number of requests processed
# TYPE llm_requests_total counter
llm_requests_total 100.0
# HELP llm_parse_intent_requests_total Total parse_intent requests
# TYPE llm_parse_intent_requests_total counter
llm_parse_intent_requests_total 80.0
# HELP llm_narrate_requests_total Total narrate requests
# TYPE llm_narrate_requests_total counter
llm_narrate_requests_total 20.0
# HELP llm_errors_total Total number of errors
# TYPE llm_errors_total counter
llm_errors_total 1.0
# HELP llm_input_tokens_total Total input tokens used
# TYPE llm_input_tokens_total counter
llm_input_tokens_total 50000.0
# HELP llm_output_tokens_total Total output tokens used
# TYPE llm_output_tokens_total counter
llm_output_tokens_total 15000.0
# HELP llm_parse_intent_latency_seconds parse_intent request latency in seconds
# TYPE llm_parse_intent_latency_seconds histogram
llm_parse_intent_latency_seconds_bucket{le="1.0"} 75.0
llm_parse_intent_latency_seconds_bucket{le="5.0"} 80.0
llm_parse_intent_latency_seconds_bucket{le="+Inf"} 80.0
```

### Prometheus Annotations

All deployments are annotated for automatic Prometheus discovery:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "<service-port>"
  prometheus.io/path: "/metrics"
```

### Verifying Prometheus Scraping

To confirm Prometheus is scraping your services:

```bash
# Check simulation metrics directly
if [[ "${GENGINE_DEPLOY_ENV}" == "local" ]]; then
  MINIKUBE_IP=$(minikube ip)
  curl -s "http://${MINIKUBE_IP}:30000/metrics" | jq .
  curl -s "http://${MINIKUBE_IP}:30100/metrics" | jq .
  curl -s "http://${MINIKUBE_IP}:30001/metrics" | jq .
fi

# Using kubectl proxy or port-forward
kubectl port-forward -n "${GENGINE_NAMESPACE}" svc/simulation 8000:8000 &
kubectl port-forward -n "${GENGINE_NAMESPACE}" svc/gateway 8100:8100 &
kubectl port-forward -n "${GENGINE_NAMESPACE}" svc/llm 8001:8001 &
curl -s http://localhost:8000/metrics | jq .
curl -s http://localhost:8100/metrics | jq .
curl -s http://localhost:8001/metrics | jq .
```

### Prometheus Operator Integration

For clusters running Prometheus Operator, ServiceMonitor resources are available:

```bash
# Enable ServiceMonitors in kustomization.yaml
# Uncomment the servicemonitor.yaml line in k8s/base/kustomization.yaml

# Apply with ServiceMonitors
kubectl apply -k k8s/overlays/${GENGINE_DEPLOY_ENV}

# Verify ServiceMonitors are created
kubectl get servicemonitors -n "${GENGINE_NAMESPACE}"
```

### Running Smoke Tests

A dedicated smoke test script validates the Kubernetes deployment including
metrics endpoints:

```bash
# Basic smoke test
./scripts/k8s_smoke_test.sh

# With namespace override
./scripts/k8s_smoke_test.sh --namespace gengine

# Include load testing
./scripts/k8s_smoke_test.sh --load
```

The smoke test verifies:

- All pods are running and ready
- Health endpoints respond with HTTP 200
- Metrics endpoints are accessible
- Prometheus annotations are correctly configured

## Summary

This document deployed the GEngine services (simulation, gateway, LLM) to a
Kubernetes cluster using Kustomize overlays for environment-specific
configuration.

Summary:

- Container image built and loaded into the cluster.
- Services deployed using the appropriate Kustomize overlay.
- Health checks verified for all services.

## CI/CD Validation

GEngine uses a GitHub Actions workflow to validate all Kubernetes manifests
on every pull request and push to main. The workflow ensures manifests are
syntactically correct and can be applied to a cluster.

### Validation Workflow

The `.github/workflows/k8s-validation.yml` workflow performs two types of
validation:

1. **Linting with kubeconform** – Validates manifest schemas against
   Kubernetes API specifications without requiring a cluster.

2. **Dry-run validation** – Creates a temporary Kind cluster and runs
   `kubectl apply --dry-run=server -k` to validate that manifests can be
   applied successfully.

The workflow runs on:

- Pull requests modifying `k8s/**/*.yaml` or `.github/workflows/k8s-*.yml`
- Pushes to main modifying the same paths

Validation failures will block PR merge.

### Running Validation Locally

You can run the same validation locally before pushing changes.

#### Prerequisites for Local Validation

Install the required tools:

```bash
# Install kubeconform (Linux)
KUBECONFORM_VERSION="v0.6.4"
mkdir -p ~/.local/bin
curl -sSL "https://github.com/yannh/kubeconform/releases/download/${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz" | \
  tar -xzf - -C ~/.local/bin kubeconform

# Add to PATH if not already (add to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
kubeconform -v
```

For dry-run validation, you need a running Kubernetes cluster (Minikube, Kind,
or any cluster with kubectl access).

#### Lint Manifests

Run kubeconform on individual manifests or rendered Kustomize output:

```bash
# Lint base manifests
# Note: -skip ServiceMonitor because servicemonitor.yaml exists but is
# optional (Prometheus Operator CRD, commented out in kustomization.yaml)
kubeconform \
  -summary \
  -strict \
  -ignore-missing-schemas \
  -kubernetes-version 1.29.0 \
  -skip ServiceMonitor \
  k8s/base/*.yaml

# Lint local overlay (rendered)
kubectl kustomize k8s/overlays/local | kubeconform \
  -summary \
  -strict \
  -ignore-missing-schemas \
  -kubernetes-version 1.29.0

# Lint staging overlay (rendered)
kubectl kustomize k8s/overlays/staging | kubeconform \
  -summary \
  -strict \
  -ignore-missing-schemas \
  -kubernetes-version 1.29.0
```

#### Dry-Run Validation

With a running cluster, validate manifests against the API server:

```bash
# Validate base manifests
kubectl apply --dry-run=server -k k8s/base

# Validate local overlay
kubectl apply --dry-run=server -k k8s/overlays/local

# Validate staging overlay
kubectl apply --dry-run=server -k k8s/overlays/staging
```

#### Using Kind for Local Dry-Run

If you don't have a Kubernetes cluster, use Kind to create a temporary one:

```bash
# Install kind (if not already installed)
# See: https://kind.sigs.k8s.io/docs/user/quick-start/#installation

# Create a temporary cluster
kind create cluster --name gengine-validation

# Run dry-run validation
kubectl apply --dry-run=server -k k8s/base
kubectl apply --dry-run=server -k k8s/overlays/local
kubectl apply --dry-run=server -k k8s/overlays/staging

# Delete the cluster when done
kind delete cluster --name gengine-validation
```

## CI Smoke Tests

In addition to manifest validation, GEngine includes end-to-end smoke tests
that deploy the services to a Kind cluster and verify they are functioning
correctly. These smoke tests provide deeper validation than dry-run checks
by testing actual service health, metrics endpoints, and Prometheus annotations.

### Smoke Test Workflow

The `.github/workflows/k8s-smoke-test.yml` workflow performs comprehensive
end-to-end testing:

1. **Creates a Kind cluster** – Spins up a temporary Kubernetes cluster
2. **Builds and loads Docker image** – Builds the GEngine image and loads it
   into the Kind cluster
3. **Deploys using Kustomize** – Applies the `k8s/overlays/local` overlay
4. **Waits for rollout** – Ensures all deployments are ready
5. **Runs smoke test script** – Executes `scripts/k8s_smoke_test.sh` to verify:
   - All pods are running and ready
   - Health endpoints respond with HTTP 200
   - Metrics endpoints are accessible
   - Prometheus annotations are correctly configured
6. **Captures debug logs** – On failure, collects pod logs and events for
   troubleshooting

### When CI Smoke Tests Run

The smoke test workflow runs on:

- **Pushes to main** – When any of these paths change:
  - `k8s/**/*.yaml` (Kubernetes manifests)
  - `scripts/k8s_smoke_test.sh` (smoke test script)
  - `Dockerfile` (container image)
  - `.github/workflows/k8s-smoke-test.yml` (workflow itself)
- **Nightly schedule** – Runs at 3:00 AM UTC every day
- **Manual trigger** – Can be invoked via GitHub Actions UI

**Note:** Smoke tests do NOT run on every PR to avoid heavy K8s resource
usage. For PR validation, rely on the `k8s-validation.yml` workflow which
performs schema linting and dry-run validation.

### Manually Triggering Smoke Tests

To manually trigger the smoke test workflow:

1. Go to the repository's **Actions** tab on GitHub
2. Select **K8s Smoke Test** from the workflow list
3. Click **Run workflow**
4. Optionally configure:
   - **Run load test**: Enable the `--load` flag to run basic load testing
   - **Debug on failure**: Capture extra debug logs if the test fails
5. Click **Run workflow** to start

### Running Smoke Tests Locally

You can run the same smoke tests locally to validate changes before pushing.

#### Prerequisites for Local Smoke Tests

Ensure you have:

- **Docker** – For building container images
- **kubectl** – For interacting with Kubernetes
- **Kind** – For creating local Kubernetes clusters
- **curl** – For health check requests

Install Kind if not already installed:

```bash
# Install kind (Linux)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify installation
kind version
```

#### Local Smoke Test Procedure

Run these commands to replicate the CI smoke test locally:

```bash
# Set environment variables
export GENGINE_IMAGE_TAG="latest"
export GENGINE_NAMESPACE="gengine"

# Create a Kind cluster
kind create cluster --name gengine-smoke-test --wait 120s

# Build the Docker image
docker build -t "gengine:${GENGINE_IMAGE_TAG}" --target runtime .

# Load the image into Kind
kind load docker-image "gengine:${GENGINE_IMAGE_TAG}" --name gengine-smoke-test

# Deploy GEngine (update image tag first if needed)
kubectl apply -k k8s/overlays/local

# Wait for deployments to be ready
kubectl rollout status deployment -n "${GENGINE_NAMESPACE}" --timeout=180s

# Run the smoke test script
./scripts/k8s_smoke_test.sh --namespace "${GENGINE_NAMESPACE}"

# Optional: Run with load test
./scripts/k8s_smoke_test.sh --namespace "${GENGINE_NAMESPACE}" --load

# Cleanup when done
kubectl delete -k k8s/overlays/local
kind delete cluster --name gengine-smoke-test
```

#### Quick Local Smoke Test with Minikube

If you already have a Minikube cluster running (see
[Create_Local_Kubernetes_With_Minikube.md](Create_Local_Kubernetes_With_Minikube.md)):

```bash
# Ensure Minikube is running
minikube status

# Build and load the image
docker build -t "gengine:latest" --target runtime .
minikube image load "gengine:latest"

# Deploy and test
kubectl apply -k k8s/overlays/local
kubectl rollout status deployment -n gengine --timeout=120s
./scripts/k8s_smoke_test.sh
```

### Smoke Test Script Options

The `scripts/k8s_smoke_test.sh` script accepts these options:

| Option        | Description                                      | Default   |
| ------------- | ------------------------------------------------ | --------- |
| `--namespace` | Kubernetes namespace to test                     | `gengine` |
| `--load`      | Run basic load test against health/metrics endpoints | disabled  |

Exit codes:

| Code | Meaning                    |
| ---- | -------------------------- |
| 0    | All smoke tests passed     |
| 1    | Prerequisites not met      |
| 2    | Pod health check failed    |
| 3    | Endpoint checks failed     |

### Troubleshooting Smoke Test Failures

If the smoke test fails in CI:

1. **Check the workflow logs** – The "Capture debug logs on failure" step
   includes pod descriptions, logs, and cluster events

2. **Common issues:**
   - **Pods not starting**: Check for image pull errors or resource constraints
   - **Health checks failing**: Verify services are binding to correct ports
   - **Timeout errors**: Increase rollout timeout or check for slow startup

3. **Reproduce locally** – Use the local smoke test procedure above to
   debug the issue in an interactive environment

4. **Check recent changes** – Review commits that modified K8s manifests,
   Dockerfile, or service code

## Next Steps

- [Minikube Setup](Create_Local_Kubernetes_With_Minikube.md) -

  Provision a local Kubernetes cluster if not already done.
- [How to Play Echoes](how_to_play_echoes.md) - Learn how to interact with

  the simulation via CLI or API.

- [LLM Service Usage](llm_service_usage.md) - Configure real LLM

  providers for natural language processing.
