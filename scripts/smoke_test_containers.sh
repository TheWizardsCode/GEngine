#!/bin/bash
# =============================================================================
# Container Smoke Test Script
# =============================================================================
# This script validates the Docker/Compose setup for the Echoes of Emergence
# microservices by:
#   1. Building the Docker image
#   2. Starting all services via docker compose
#   3. Polling /healthz endpoints for simulation, gateway, and LLM services
#   4. Shutting down the stack on completion
#
# Usage:
#   ./scripts/smoke_test_containers.sh
#
# Exit codes:
#   0 - All smoke tests passed
#   1 - Docker/Compose not available or build failed
#   2 - Services failed to become healthy
#   3 - Health endpoint checks failed
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT_SECONDS=120
POLL_INTERVAL=5
SIMULATION_URL="http://localhost:8000/healthz"
GATEWAY_URL="http://localhost:8100/healthz"
LLM_URL="http://localhost:8001/healthz"

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

cleanup() {
    log_info "Cleaning up: stopping containers..."
    docker compose down --volumes --remove-orphans 2>/dev/null || true
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# =============================================================================
# Step 1: Prerequisites Check
# =============================================================================
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    log_error "Docker Compose V2 is not available"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    log_error "curl is not installed or not in PATH"
    exit 1
fi

log_info "Docker: $(docker --version)"
log_info "Docker Compose: $(docker compose version)"
log_info "curl: $(curl --version | head -n 1)"

# =============================================================================
# Step 2: Build Docker Image
# =============================================================================
log_info "Building Docker image..."

if ! docker compose build --quiet; then
    log_error "Docker image build failed"
    exit 1
fi

log_info "Docker image built successfully"

# =============================================================================
# Step 3: Start Services
# =============================================================================
log_info "Starting services via docker compose..."

if ! docker compose up -d; then
    log_error "Failed to start services"
    exit 1
fi

log_info "Services started, waiting for health checks..."

# =============================================================================
# Step 4: Wait for Services to Become Healthy
# =============================================================================
wait_for_health() {
    local url=$1
    local name=$2
    local elapsed=0
    
    while [ $elapsed -lt $TIMEOUT_SECONDS ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_info "$name is healthy"
            return 0
        fi
        sleep $POLL_INTERVAL
        elapsed=$((elapsed + POLL_INTERVAL))
        log_info "Waiting for $name... (${elapsed}s / ${TIMEOUT_SECONDS}s)"
    done
    
    log_error "$name did not become healthy within ${TIMEOUT_SECONDS}s"
    return 1
}

# Wait for all services sequentially (gateway depends on simulation being healthy first)
all_healthy=true

log_info "Polling health endpoints..."

# Wait for simulation first (gateway depends on it)
if ! wait_for_health "$SIMULATION_URL" "Simulation"; then
    all_healthy=false
fi

# Wait for LLM service
if ! wait_for_health "$LLM_URL" "LLM"; then
    all_healthy=false
fi

# Wait for gateway last (depends on simulation)
if ! wait_for_health "$GATEWAY_URL" "Gateway"; then
    all_healthy=false
fi

if [ "$all_healthy" = false ]; then
    log_error "One or more services failed health checks"
    log_info "Container logs:"
    docker compose logs --tail=50
    exit 2
fi

# =============================================================================
# Step 5: Verify Health Endpoint Responses
# =============================================================================
log_info "Verifying health endpoint responses..."

verify_health() {
    local url=$1
    local name=$2
    
    local response
    local http_code
    
    response=$(curl -sf "$url" 2>/dev/null) || {
        log_error "$name health check failed: no response"
        return 1
    }
    
    http_code=$(curl -so /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$http_code" != "200" ]; then
        log_error "$name returned HTTP $http_code (expected 200)"
        return 1
    fi
    
    # Check for expected JSON structure (status field)
    if ! echo "$response" | grep -q "status"; then
        log_warn "$name response doesn't contain 'status' field: $response"
    fi
    
    log_info "$name: HTTP $http_code - $response"
    return 0
}

verification_failed=false

if ! verify_health "$SIMULATION_URL" "Simulation"; then
    verification_failed=true
fi

if ! verify_health "$GATEWAY_URL" "Gateway"; then
    verification_failed=true
fi

if ! verify_health "$LLM_URL" "LLM"; then
    verification_failed=true
fi

if [ "$verification_failed" = true ]; then
    log_error "Health endpoint verification failed"
    exit 3
fi

# =============================================================================
# Success
# =============================================================================
log_info "=========================================="
log_info "All container smoke tests PASSED!"
log_info "=========================================="
log_info "Services verified:"
log_info "  - Simulation: $SIMULATION_URL"
log_info "  - Gateway:    $GATEWAY_URL"
log_info "  - LLM:        $LLM_URL"

exit 0
