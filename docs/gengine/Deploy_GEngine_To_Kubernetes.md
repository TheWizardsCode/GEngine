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

## Monitoring and Observability

GEngine services are instrumented with Prometheus-compatible metrics endpoints
for monitoring and alerting.

### Metrics Endpoints

Each service exposes metrics that can be scraped by Prometheus:

| Service    | Port | Metrics Endpoint | Description                        |
| ---------- | ---- | ---------------- | ---------------------------------- |
| Simulation | 8000 | `/metrics`       | Tick count, environment, profiling |
| Gateway    | 8100 | `/healthz`       | Service health and connection info |
| LLM        | 8001 | `/healthz`       | Service health status              |

### Prometheus Annotations

All deployments are annotated for automatic Prometheus discovery:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "<service-port>"
  prometheus.io/path: "/metrics"  # or "/healthz"
```

### Verifying Prometheus Scraping

To confirm Prometheus is scraping your services:

```bash
# Check simulation metrics directly
if [[ "${GENGINE_DEPLOY_ENV}" == "local" ]]; then
  MINIKUBE_IP=$(minikube ip)
  curl -s "http://${MINIKUBE_IP}:30000/metrics" | jq .
fi

# Using kubectl proxy or port-forward
kubectl port-forward -n "${GENGINE_NAMESPACE}" svc/simulation 8000:8000 &
curl -s http://localhost:8000/metrics | jq .
```

Expected output:

```json
{
  "tick": 0,
  "environment": {
    "temperature": 0.0,
    "instability": 0.0,
    "tension": 0.0
  },
  "profiling": {}
}
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

## Next Steps

- [Minikube Setup](Create_Local_Kubernetes_With_Minikube.md) -

  Provision a local Kubernetes cluster if not already done.
- [How to Play Echoes](how_to_play_echoes.md) - Learn how to interact with

  the simulation via CLI or API.

- [LLM Service Usage](llm_service_usage.md) - Configure real LLM

  providers for natural language processing.
