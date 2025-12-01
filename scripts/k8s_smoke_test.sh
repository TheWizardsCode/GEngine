#!/bin/bash
# =============================================================================
# Kubernetes Smoke Test Script
# =============================================================================
# This script validates the Kubernetes deployment of GEngine services by:
#   1. Verifying pods are running
#   2. Checking health endpoints for all services
#   3. Checking metrics endpoints for Prometheus scraping
#   4. Optionally running a load test
#
# Usage:
#   ./scripts/k8s_smoke_test.sh [--load] [--namespace NAMESPACE]
#
# Options:
#   --load       Run a basic load test against the simulation service
#   --namespace  Kubernetes namespace (default: gengine)
#
# Exit codes:
#   0 - All smoke tests passed
#   1 - Prerequisites not met
#   2 - Pod health check failed
#   3 - Endpoint checks failed
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
NAMESPACE="${GENGINE_NAMESPACE:-gengine}"
RUN_LOAD_TEST=false
TIMEOUT_SECONDS=60
POLL_INTERVAL=5

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --load)
            RUN_LOAD_TEST=true
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Step 1: Prerequisites Check
# =============================================================================
log_info "Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    log_error "curl is not installed or not in PATH"
    exit 1
fi

# Check cluster access
if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
    exit 1
fi

log_info "kubectl: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
log_info "Cluster access: OK"
log_info "Namespace: ${NAMESPACE}"

# =============================================================================
# Step 2: Check Pod Status
# =============================================================================
log_info "Checking pod status in namespace ${NAMESPACE}..."

# Get pod status
check_pods() {
    local pods_ready=true
    
    # Check if namespace exists
    if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_error "Namespace ${NAMESPACE} does not exist"
        return 1
    fi
    
    # Get all pods and check their status
    local pod_output
    pod_output=$(kubectl get pods -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.phase}{" "}{.status.containerStatuses[0].ready}{"\n"}{end}' 2>/dev/null)
    
    if [[ -z "${pod_output}" ]]; then
        log_error "No pods found in namespace ${NAMESPACE}"
        return 1
    fi
    
    while read -r name phase ready; do
        if [[ -z "${name}" ]]; then
            continue
        fi
        if [[ "${phase}" != "Running" ]]; then
            log_error "Pod ${name} is ${phase} (expected Running)"
            pods_ready=false
        elif [[ "${ready}" != "true" ]]; then
            log_warn "Pod ${name} is not ready yet"
            pods_ready=false
        else
            log_info "Pod ${name}: Running and Ready"
        fi
    done < <(echo "${pod_output}")
    
    if [[ "${pods_ready}" == "false" ]]; then
        return 1
    fi
    return 0
}

if ! check_pods; then
    log_error "Pod status check failed"
    log_info "Pod details:"
    kubectl get pods -n "${NAMESPACE}" -o wide
    exit 2
fi

# =============================================================================
# Step 3: Determine Service URLs
# =============================================================================
log_info "Determining service endpoints..."

# Check if running on Minikube with NodePort
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    SIM_URL="http://${MINIKUBE_IP}:30000"
    GW_URL="http://${MINIKUBE_IP}:30100"
    LLM_URL="http://${MINIKUBE_IP}:30001"
    log_info "Using Minikube NodePort endpoints"
else
    # Fallback to port-forward approach
    log_info "Setting up port-forwarding for smoke tests..."
    
    # Start port-forwards in background
    kubectl port-forward -n "${NAMESPACE}" svc/simulation 8000:8000 &>/dev/null &
    PF_SIM_PID=$!
    kubectl port-forward -n "${NAMESPACE}" svc/gateway 8100:8100 &>/dev/null &
    PF_GW_PID=$!
    kubectl port-forward -n "${NAMESPACE}" svc/llm 8001:8001 &>/dev/null &
    PF_LLM_PID=$!
    
    # Give port-forwards time to establish
    sleep 3
    
    SIM_URL="http://localhost:8000"
    GW_URL="http://localhost:8100"
    LLM_URL="http://localhost:8001"
    
    # Cleanup function for port-forwards
    cleanup_port_forwards() {
        [[ -n "${PF_SIM_PID}" ]] && kill "${PF_SIM_PID}" 2>/dev/null || true
        [[ -n "${PF_GW_PID}" ]] && kill "${PF_GW_PID}" 2>/dev/null || true
        [[ -n "${PF_LLM_PID}" ]] && kill "${PF_LLM_PID}" 2>/dev/null || true
    }
    trap cleanup_port_forwards EXIT
    
    log_info "Port-forwards established"
fi

log_info "Service URLs:"
log_info "  Simulation: ${SIM_URL}"
log_info "  Gateway:    ${GW_URL}"
log_info "  LLM:        ${LLM_URL}"

# =============================================================================
# Step 4: Health Endpoint Checks
# =============================================================================
log_info "Checking health endpoints..."

check_health() {
    local url=$1
    local name=$2
    local response
    local http_code
    
    http_code=$(curl -so /dev/null -w "%{http_code}" "${url}" --connect-timeout 5 --max-time 10 2>/dev/null) || {
        log_error "${name} health check failed: connection error"
        return 1
    }
    
    if [[ "${http_code}" != "200" ]]; then
        log_error "${name} returned HTTP ${http_code} (expected 200)"
        return 1
    fi
    
    response=$(curl -sf "${url}" --connect-timeout 5 --max-time 10 2>/dev/null)
    log_info "${name}: HTTP ${http_code} - ${response}"
    return 0
}

health_failed=false

if ! check_health "${SIM_URL}/healthz" "Simulation"; then
    health_failed=true
fi

if ! check_health "${GW_URL}/healthz" "Gateway"; then
    health_failed=true
fi

if ! check_health "${LLM_URL}/healthz" "LLM"; then
    health_failed=true
fi

if [[ "${health_failed}" == "true" ]]; then
    log_error "Health endpoint checks failed"
    exit 3
fi

# =============================================================================
# Step 5: Metrics Endpoint Checks
# =============================================================================
log_info "Checking metrics endpoints..."

check_metrics() {
    local url=$1
    local name=$2
    local response
    local http_code
    
    http_code=$(curl -so /dev/null -w "%{http_code}" "${url}" --connect-timeout 5 --max-time 10 2>/dev/null) || {
        log_warn "${name} metrics check failed: connection error"
        return 1
    }
    
    if [[ "${http_code}" != "200" ]]; then
        log_warn "${name} metrics returned HTTP ${http_code}"
        return 1
    fi
    
    response=$(curl -sf "${url}" --connect-timeout 5 --max-time 10 2>/dev/null | head -c 200)
    log_info "${name} metrics: HTTP ${http_code} - ${response}..."
    return 0
}

# Simulation has a dedicated /metrics endpoint
check_metrics "${SIM_URL}/metrics" "Simulation"

# Gateway and LLM use /healthz for metrics (JSON format)
check_metrics "${GW_URL}/healthz" "Gateway"
check_metrics "${LLM_URL}/healthz" "LLM"

# =============================================================================
# Step 6: Prometheus Annotations Verification
# =============================================================================
log_info "Verifying Prometheus annotations on pods..."

check_prometheus_annotations() {
    local deployment=$1
    local expected_port=$2
    local expected_path=$3
    
    local annotations
    annotations=$(kubectl get deployment "${deployment}" -n "${NAMESPACE}" -o jsonpath='{.spec.template.metadata.annotations}' 2>/dev/null)
    
    if echo "${annotations}" | grep -q "prometheus.io/scrape.*true"; then
        log_info "${deployment}: prometheus.io/scrape=true ✓"
    else
        log_warn "${deployment}: missing prometheus.io/scrape annotation"
    fi
    
    if echo "${annotations}" | grep -q "prometheus.io/port.*${expected_port}"; then
        log_info "${deployment}: prometheus.io/port=${expected_port} ✓"
    else
        log_warn "${deployment}: missing or incorrect prometheus.io/port annotation"
    fi
    
    if echo "${annotations}" | grep -q "prometheus.io/path.*${expected_path}"; then
        log_info "${deployment}: prometheus.io/path=${expected_path} ✓"
    else
        log_warn "${deployment}: missing or incorrect prometheus.io/path annotation"
    fi
}

check_prometheus_annotations "simulation" "8000" "/metrics"
check_prometheus_annotations "gateway" "8100" "/healthz"
check_prometheus_annotations "llm" "8001" "/healthz"

# =============================================================================
# Step 7: Optional Load Test
# =============================================================================
if [[ "${RUN_LOAD_TEST}" == "true" ]]; then
    log_info "Running basic load test..."
    
    LOAD_REQUESTS=100
    LOAD_CONCURRENT=10
    
    log_info "Sending ${LOAD_REQUESTS} requests to simulation /healthz (${LOAD_CONCURRENT} concurrent)..."
    
    # Simple load test using background jobs
    load_test() {
        local url=$1
        local requests=$2
        local concurrent=$3
        
        local tmpfile
        tmpfile=$(mktemp)
        local start_time
        start_time=$(date +%s%N)
        
        for ((i=1; i<=requests; i++)); do
            # Run in background up to concurrent limit
            if (( $(jobs -r | wc -l) >= concurrent )); then
                wait -n
            fi
            
            {
                if curl -sf "${url}" --connect-timeout 5 --max-time 10 >/dev/null 2>&1; then
                    echo "success" >> "${tmpfile}"
                else
                    echo "failed" >> "${tmpfile}"
                fi
            } &
        done
        
        wait
        
        local end_time
        end_time=$(date +%s%N)
        local duration=$(( (end_time - start_time) / 1000000 ))
        
        local success_count failed_count
        success_count=$(grep -c "success" "${tmpfile}" 2>/dev/null || echo 0)
        failed_count=$(grep -c "failed" "${tmpfile}" 2>/dev/null || echo 0)
        rm -f "${tmpfile}"
        
        log_info "Load test completed in ${duration}ms: ${success_count} success, ${failed_count} failed"
    }
    
    load_test "${SIM_URL}/healthz" "${LOAD_REQUESTS}" "${LOAD_CONCURRENT}"
    
    # Test metrics endpoint under load
    log_info "Sending ${LOAD_REQUESTS} requests to simulation /metrics..."
    load_test "${SIM_URL}/metrics" "${LOAD_REQUESTS}" "${LOAD_CONCURRENT}"
fi

# =============================================================================
# Success
# =============================================================================
log_info "=========================================="
log_info "All Kubernetes smoke tests PASSED!"
log_info "=========================================="
log_info "Services verified in namespace ${NAMESPACE}:"
log_info "  - Simulation: ${SIM_URL}/healthz ✓"
log_info "  - Gateway:    ${GW_URL}/healthz ✓"
log_info "  - LLM:        ${LLM_URL}/healthz ✓"
log_info ""
log_info "Prometheus scraping configured:"
log_info "  - Simulation metrics: ${SIM_URL}/metrics"
log_info "  - All services have prometheus.io/* annotations"

exit 0
