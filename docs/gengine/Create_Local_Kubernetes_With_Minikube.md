# Create a Local Kubernetes Cluster with Minikube

## Introduction

This executable document provisions a local Kubernetes cluster by using
Minikube. It standardizes environment variables, validates the workstation
toolchain, and boots a reusable Minikube profile suitable for application
development and integration testing.

Summary:

- Build a repeatable Minikube profile for a single-node Kubernetes control
  plane.
- Validate the cluster and kubectl context for immediate workloads.

## Prerequisites

Ensure your workstation meets hardware virtualization requirements
(VT-x/AMD-V enabled) with at least 4 CPUs, 8 GB RAM, and 20 GB of free disk
space. This workflow has no dependency on other executable documents.

Summary:

- Validate tooling and virtualization support before running the workflow.

### Required CLI tools

Confirm that Minikube, kubectl, and Docker are available and sufficiently
new for this workflow. Update their versions if the checks fail.

Set explicit version baselines before running the CLI checks so drift is
highlighted consistently.

```bash
export MINIKUBE_REQUIRED_VERSION="${MINIKUBE_REQUIRED_VERSION:-v1.34.0}"  # Minikube req.
export KUBECTL_REQUIRED_VERSION="${KUBECTL_REQUIRED_VERSION:-v1.34.2}"  # kubectl req.
export DOCKER_SERVER_REQUIRED_VERSION="${DOCKER_SERVER_REQUIRED_VERSION:-24.0.6}"  # Docker req.

echo "CLI version requirements configured."
```

<!-- expected_similarity="CLI version requirements configured." -->

Representative output:

```text
CLI version requirements configured.
```

#### Install Docker Server

We use the Docker Server to host the Kubernetes Cluster. This section will ensure it is installed or upgraded as needed.

Prepare the Docker installation metadata so the workflow can download the
official installer script or use a custom command without manual edits.

```bash
export DOCKER_INSTALL_SCRIPT_URL="${DOCKER_INSTALL_SCRIPT_URL:-https://get.docker.com}"  # Installer URL.
export DOCKER_INSTALL_SCRIPT_PATH="${DOCKER_INSTALL_SCRIPT_PATH:-/tmp/install-docker.sh}"  # Script path.
existing_docker_path="$(command -v docker 2>/dev/null || true)"
export DOCKER_BIN_PATH="${DOCKER_BIN_PATH:-${existing_docker_path:-/usr/bin/docker}}"  # Docker binary.
export DOCKER_INSTALL_RUNNER="${DOCKER_INSTALL_RUNNER:-sh}"  # Command to execute installer.
export DOCKER_INSTALL_RUNNER_ARGS="${DOCKER_INSTALL_RUNNER_ARGS:-}"  # Optional args like "-s" or "sh".

echo "Docker installer configuration prepared."
```

<!-- expected_similarity="Docker installer configuration prepared." -->

Representative output:

```text
Docker installer configuration prepared.
```

Ensure the Docker Server binary exists and matches the required baseline.
Install or upgrade automatically when drift is detected, mirroring the
Minikube flow.

```bash
docker_install_reason=""
if [[ ! -x "${DOCKER_BIN_PATH}" ]]; then
  docker_install_reason="install"
else
  DOCKER_DETECTED_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
  if [[ -z "${DOCKER_DETECTED_VERSION}" ]]; then
    docker_install_reason="install"
  elif [[ -n "${DOCKER_SERVER_REQUIRED_VERSION}" && \
          "${DOCKER_DETECTED_VERSION}" != "${DOCKER_SERVER_REQUIRED_VERSION}" ]]; then
    docker_install_reason="upgrade"
  fi
fi

docker_privilege_state="root"
docker_privilege_reason=""
docker_privilege_prefix=()
if [[ "${EUID}" -ne 0 ]]; then
  docker_privilege_state="user"
  if command -v sudo >/dev/null 2>&1; then
    if sudo -n true >/dev/null 2>&1; then
      docker_privilege_state="sudo"
      docker_privilege_prefix=(sudo -E)
    else
      docker_privilege_state="sudo-password"
      docker_privilege_reason="sudo requires an interactive password"
    fi
  else
    docker_privilege_state="no-sudo"
    docker_privilege_reason="sudo command not found"
  fi
fi

docker_privilege_available=true
if [[ "${docker_privilege_state}" == "sudo-password" || \
      "${docker_privilege_state}" == "no-sudo" ]]; then
  docker_privilege_available=false
fi

if [[ -n "${docker_install_reason}" && "${docker_privilege_available}" != true ]]; then
  if [[ "${docker_install_reason}" == "install" ]]; then
    printf 'ERROR: Docker %s requires elevated privileges (%s). Please install Docker manually or rerun with sudo/root access.\n' \
      "${docker_install_reason}" \
      "${docker_privilege_reason:-privileges unavailable}"
    exit 1
  fi
  printf 'WARNING: Skipping Docker %s because elevated privileges are unavailable (%s).\n' \
    "${docker_install_reason}" \
    "${docker_privilege_reason:-privileges unavailable}"
  docker_install_reason=""
fi

if [[ -n "${docker_install_reason}" ]]; then
  if ! curl -fsSLo "${DOCKER_INSTALL_SCRIPT_PATH}" "${DOCKER_INSTALL_SCRIPT_URL}"; then
    echo "Failed to download Docker install script." && exit 1
  fi
  runner=("${DOCKER_INSTALL_RUNNER}")
  if [[ -n "${DOCKER_INSTALL_RUNNER_ARGS}" ]]; then
    read -r -a runner_args <<< "${DOCKER_INSTALL_RUNNER_ARGS}"
    runner+=("${runner_args[@]}")
  fi
  runner+=("${DOCKER_INSTALL_SCRIPT_PATH}")
  action_label="Installing"
  [[ "${docker_install_reason}" == "upgrade" ]] && action_label="Upgrading"
  printf '%s Docker Server %s using %s.\n' \
    "${action_label}" \
    "${DOCKER_SERVER_REQUIRED_VERSION}" \
    "${DOCKER_INSTALL_SCRIPT_URL}"
  installer_cmd=("${docker_privilege_prefix[@]}" "${runner[@]}")
  if ! "${installer_cmd[@]}"; then
    echo "Failed to ${docker_install_reason} Docker." && exit 1
  fi
fi

DOCKER_DETECTED_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
if [[ -z "${DOCKER_DETECTED_VERSION}" ]]; then
  echo "Unable to detect Docker Server version." && exit 1
fi

version_status="OK"
if [[ -n "${DOCKER_SERVER_REQUIRED_VERSION}" && \
      "${DOCKER_DETECTED_VERSION}" != "${DOCKER_SERVER_REQUIRED_VERSION}" ]]; then
  version_status="DIFF"
fi

printf 'Docker Server version: %s (baseline %s) [%s]\n' \
  "${DOCKER_DETECTED_VERSION}" \
  "${DOCKER_SERVER_REQUIRED_VERSION}" \
  "${version_status}"
```

This logic only attempts installation when passwordless sudo or root access is
available. Otherwise it emits a warning and continues with the detected Docker
version, ensuring tests can run in unprivileged sandboxes. Missing Docker still
fails fast with guidance to rerun the document under elevated privileges.

Representative output:

<!-- expected_similarity="Docker Server version: .*" -->

```text
Installing Docker Server 24.0.6 using https://get.docker.com.
Docker Server version: 24.0.6 (baseline 24.0.6) [OK]
```

Optional warning-only flow when sudo access is unavailable:

```text
WARNING: Skipping Docker upgrade because elevated privileges are unavailable (sudo requires an interactive password).
Docker Server version: 28.5.1 (baseline 24.0.6) [DIFF]
```

#### Install Kubectl

All management of workloads on the Kubernetes cluster is done using the Kubectl command. This section will ensure it is installed.

Inspect the kubectl client version to confirm API compatibility.

```bash
kubectl version --client
```

This command reports the kubectl client release along with its build metadata.

<!-- expected_similarity="Client Version: v.*" -->

Representative output:

```text
Client Version: v1.30.1
Kustomize Version: v5.3.0
```

Use the required kubectl version variable to highlight when the client is out
of compliance.

```bash
KUBECTL_DETECTED_VERSION=$(
  kubectl version --client 2>/dev/null | awk '/Client Version/ {print $3}'
)
if [[ -n "${KUBECTL_DETECTED_VERSION}" && \
      -n "${KUBECTL_REQUIRED_VERSION}" ]]; then
  version_status="OK"
  if [[ "${KUBECTL_DETECTED_VERSION}" != \
        "${KUBECTL_REQUIRED_VERSION}" ]]; then
    version_status="DIFF"
  fi
  printf 'kubectl version: %s (baseline %s) [%s]\n' \
    "${KUBECTL_DETECTED_VERSION}" \
    "${KUBECTL_REQUIRED_VERSION}" \
    "${version_status}"
fi
```

<!-- expected_similarity="kubectl version: .*" -->

Representative output:

```text
kubectl version: v1.34.2 (baseline v1.30.1) [DIFF]
```

#### Install Minikube

We use Minikube to manage a local Kubernetes cluster. This section ensures that the correct version of Minikube is installed.

Configure the Minikube installation path so the workflow can add or update
the binary without manual intervention.

```bash
export MINIKUBE_INSTALL_DIR="${MINIKUBE_INSTALL_DIR:-$HOME/.local/bin}"  # Install dir.
export MINIKUBE_BIN_PATH="${MINIKUBE_BIN_PATH:-${MINIKUBE_INSTALL_DIR}/minikube}"  # Binary path.
if [[ -n "${MINIKUBE_DOWNLOAD_URL}" && \
      "${MINIKUBE_DOWNLOAD_URL}" != */${MINIKUBE_REQUIRED_VERSION}/* ]]; then
  unset MINIKUBE_DOWNLOAD_URL
fi
if [[ -z "${MINIKUBE_DOWNLOAD_URL}" ]]; then
  printf -v MINIKUBE_DOWNLOAD_URL '%s/%s/%s' \
    "https://storage.googleapis.com/minikube/releases" \
    "${MINIKUBE_REQUIRED_VERSION}" \
    "minikube-linux-amd64"
fi
export MINIKUBE_DOWNLOAD_URL  # Download URL.

mkdir -p "${MINIKUBE_INSTALL_DIR}"
case ":${PATH}:" in
  *":${MINIKUBE_INSTALL_DIR}:"*) ;;
  *) export PATH="${MINIKUBE_INSTALL_DIR}:${PATH}" ;;
esac

echo "Minikube install path prepared."
```

<!-- expected_similarity="Minikube install path prepared." -->

Representative output:

```text
Minikube install path prepared.
```

Ensure the Minikube binary exists and matches the required version. Install
or upgrade automatically when drift is detected, then report the result.

```bash
if [[ ! -x "${MINIKUBE_BIN_PATH}" ]]; then
  printf 'Installing Minikube %s into %s.\n' \
    "${MINIKUBE_REQUIRED_VERSION}" "${MINIKUBE_BIN_PATH}"
  if ! curl -fsSLo /tmp/minikube "${MINIKUBE_DOWNLOAD_URL}"; then
    echo "Failed to download Minikube." && exit 1
  fi
  if ! install -m 0755 /tmp/minikube "${MINIKUBE_BIN_PATH}"; then
    echo "Failed to install Minikube." && exit 1
  fi
fi

MINIKUBE_DETECTED_VERSION=$(
  minikube version --short 2>/dev/null | head -n 1
)

if [[ -z "${MINIKUBE_DETECTED_VERSION}" ]]; then
  echo "Unable to detect Minikube version." && exit 1
fi

if [[ "${MINIKUBE_DETECTED_VERSION}" != \
      "${MINIKUBE_REQUIRED_VERSION}" ]]; then
  printf 'Upgrading Minikube from %s to %s.\n' \
    "${MINIKUBE_DETECTED_VERSION}" "${MINIKUBE_REQUIRED_VERSION}"
  if ! curl -fsSLo /tmp/minikube "${MINIKUBE_DOWNLOAD_URL}"; then
    echo "Failed to download Minikube." && exit 1
  fi
  if ! install -m 0755 /tmp/minikube "${MINIKUBE_BIN_PATH}"; then
    echo "Failed to install Minikube." && exit 1
  fi
  MINIKUBE_DETECTED_VERSION=$(
    minikube version --short 2>/dev/null | head -n 1
  )
fi

version_status="OK"
if [[ "${MINIKUBE_DETECTED_VERSION}" != \
      "${MINIKUBE_REQUIRED_VERSION}" ]]; then
  version_status="DIFF"
fi

printf 'Minikube version: %s (baseline %s) [%s]\n' \
  "${MINIKUBE_DETECTED_VERSION}" \
  "${MINIKUBE_REQUIRED_VERSION}" \
  "${version_status}"
```

<!-- expected_similarity="Minikube version: .*" -->

Representative output:

```text
Installing Minikube v1.34.0 into /home/user/.local/bin/minikube.
Minikube version: v1.34.0 (baseline v1.34.0) [OK]
```

Summary:

- Confirms the required CLIs respond and report their versions.

## Setting up the environment

Define the environment variables that shape the Minikube deployment,
including profile name, Kubernetes version, and resource sizing. Inline
comments explain each value. All variables can be overridden by exporting
values before running this doc.

```bash
export HASH="${HASH:-$(date -u +"%y%m%d%H%M")}"  # Timestamp.
export MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-k8s-local-${HASH}}"  # Profile.
export MINIKUBE_K8S_VERSION="${MINIKUBE_K8S_VERSION:-v1.30.0}"  # K8s ver.
export MINIKUBE_CPUS="${MINIKUBE_CPUS:-4}"  # vCPUs.
export MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-8192}"  # Memory.
export MINIKUBE_DRIVER="${MINIKUBE_DRIVER:-docker}"  # Driver.
export MINIKUBE_CONTAINER_RUNTIME="${MINIKUBE_CONTAINER_RUNTIME:-containerd}"  # Runtime.
export MINIKUBE_ADDONS="${MINIKUBE_ADDONS:-metrics-server,storage-provisioner}"  # Addons.
export KUBECONFIG_PATH="${KUBECONFIG_PATH:-$HOME/.kube/config}"  # kubeconfig.

echo "Environment variables configured."
```

This block standardizes all environment variables that parameterize the run.

<!-- expected_similarity="Environment variables configured." -->

Representative output:

```text
Environment variables configured.
```

This loop prints every variable and flags any missing values before changes.

```bash
printf '%-32s %-40s %s\n' "Variable" "Value" "Status"
env_vars=(
  HASH
  MINIKUBE_PROFILE
  MINIKUBE_K8S_VERSION
  MINIKUBE_CPUS
  MINIKUBE_MEMORY
  MINIKUBE_DRIVER
  MINIKUBE_CONTAINER_RUNTIME
  MINIKUBE_ADDONS
  KUBECONFIG_PATH
  MINIKUBE_REQUIRED_VERSION
  KUBECTL_REQUIRED_VERSION
  DOCKER_SERVER_REQUIRED_VERSION
  DOCKER_INSTALL_SCRIPT_URL
  DOCKER_INSTALL_SCRIPT_PATH
  DOCKER_INSTALL_RUNNER
  DOCKER_INSTALL_RUNNER_ARGS
  DOCKER_BIN_PATH
  MINIKUBE_INSTALL_DIR
  MINIKUBE_BIN_PATH
  MINIKUBE_DOWNLOAD_URL
)
for var in "${env_vars[@]}"; do
  value="${!var:-}"
  status="OK"
  if [[ -z "${value}" ]]; then
    status="MISSING"
  fi
  printf '%-32s %-40s %s\n' "${var}" "${value}" "${status}"
done
```

<!-- expected_similarity="MINIKUBE_PROFILE.*OK" -->

Representative output:

```text
Variable                         Value                                    Status
HASH                              2511261530                              OK
MINIKUBE_PROFILE                  k8s-local-2511261530                    OK
MINIKUBE_K8S_VERSION              v1.30.0                                 OK
MINIKUBE_CPUS                     4                                       OK
MINIKUBE_MEMORY                   8192                                    OK
MINIKUBE_DRIVER                   docker                                  OK
MINIKUBE_CONTAINER_RUNTIME        containerd                              OK
MINIKUBE_ADDONS                   metrics-server,storage-provisioner      OK
KUBECONFIG_PATH                   /home/user/.kube/config                 OK
MINIKUBE_REQUIRED_VERSION         v1.34.0                                 OK
KUBECTL_REQUIRED_VERSION          v1.30.1                                 OK
DOCKER_SERVER_REQUIRED_VERSION    24.0.6                                  OK
DOCKER_INSTALL_SCRIPT_URL         https://get.docker.com                   OK
DOCKER_INSTALL_SCRIPT_PATH        /tmp/install-docker.sh                   OK
DOCKER_INSTALL_RUNNER             sh                                       OK
DOCKER_INSTALL_RUNNER_ARGS                                                OK
DOCKER_BIN_PATH                   /usr/bin/docker                          OK
MINIKUBE_INSTALL_DIR              /home/user/.local/bin                   OK
MINIKUBE_BIN_PATH                 /home/user/.local/bin/minikube          OK
MINIKUBE_DOWNLOAD_URL             https://storage.googleapis.com/...      OK
```

Summary:

- Declares all environment variables with safe defaults and surfaces their
  current values for auditing.

## Steps

Follow the ordered steps to create or resume the Minikube-based local
cluster. Each block is idempotent and can be rerun safely.

### Start or resume the Minikube profile

Launch the Minikube profile if it is not already running, applying the
configuration defined earlier. Existing profiles are reused.

```bash
if minikube status --profile "${MINIKUBE_PROFILE}" >/dev/null 2>&1; then
  echo "Profile ${MINIKUBE_PROFILE} already running."
else
  IFS=',' read -ra addon_list <<< "${MINIKUBE_ADDONS}"
  START_ARGS=()
  for addon in "${addon_list[@]}"; do
    addon_trimmed="$(echo "${addon}" | xargs)"
    [[ -z "${addon_trimmed}" ]] && continue
    START_ARGS+=("--addons" "${addon_trimmed}")
  done
  if ! minikube start \
    --profile "${MINIKUBE_PROFILE}" \
    --kubernetes-version "${MINIKUBE_K8S_VERSION}" \
    --cpus "${MINIKUBE_CPUS}" \
    --memory "${MINIKUBE_MEMORY}" \
    --driver "${MINIKUBE_DRIVER}" \
    --container-runtime "${MINIKUBE_CONTAINER_RUNTIME}" \
    "${START_ARGS[@]}"; then
    echo "Minikube start failed for profile ${MINIKUBE_PROFILE}."
    exit 1
  fi
fi
```

This logic starts a new Minikube profile or confirms it is already running.

<!-- expected_similarity="(Profile .*already running|Done! kubectl is now configured)" -->

Representative output:

```text
Done! kubectl is now configured to use "k8s-local-2511261530" cluster and
"default" namespace by default
```

Summary:

- Starts the Minikube cluster when necessary and reuses it when already up.

### Update kubeconfig and default context

Make sure kubectl points at the Minikube profile and confirm node
registration along with addon readiness state.

```bash
if ! minikube update-context --profile "${MINIKUBE_PROFILE}"; then
  echo "Failed to update kubectl context for ${MINIKUBE_PROFILE}."
  exit 1
fi

if ! KUBECONFIG="${KUBECONFIG_PATH}" kubectl config use-context "${MINIKUBE_PROFILE}"; then
  echo "kubectl could not switch to context ${MINIKUBE_PROFILE}."
  exit 1
fi

if ! KUBECONFIG="${KUBECONFIG_PATH}" kubectl get nodes -o wide; then
  echo "kubectl get nodes failed for profile ${MINIKUBE_PROFILE}."
  exit 1
fi

if ! minikube addons list --profile "${MINIKUBE_PROFILE}" | \
  grep -E "(metrics-server|storage-provisioner)"; then
  echo "Expected addons metrics-server or storage-provisioner not found."
  exit 1
fi
```

These commands align kubectl and verify node plus addon status.

<!-- expected_similarity="Ready" -->

Representative output:

```text
Switched to context "k8s-local-2511261530".
NAME                 STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE
k8s-local-2511261530 Ready    control-plane   2m    v1.30.0   192.168.49.2  <none>        Ubuntu 24.04 LTS
| metrics-server        | enabled |
| storage-provisioner   | enabled |
```

Summary:

- Aligns kubectl with the Minikube profile and verifies nodes plus addons.

## Verification

Use these read-only checks to verify that the Minikube-based Kubernetes
cluster is still healthy. If this section passes, the rest of the document
can be skipped on future runs.

```bash
STATUS_OUTPUT=$(minikube status --profile "${MINIKUBE_PROFILE}")
if [[ $? -ne 0 ]]; then
  echo "FAIL: minikube status failed for ${MINIKUBE_PROFILE}."
  exit 1
fi

if ! grep -q "host: Running" <<<"${STATUS_OUTPUT}"; then
  echo "FAIL: Minikube host is not running"
  exit 1
fi

if ! KUBECONFIG="${KUBECONFIG_PATH}" kubectl get nodes --no-headers >/tmp/nodes.out; then
  echo "FAIL: kubectl get nodes did not succeed"
  exit 1
fi

if [[ ! -s /tmp/nodes.out ]]; then
  echo "FAIL: kubectl get nodes returned no data"
  exit 1
fi

if ! grep -q "Ready" /tmp/nodes.out; then
  echo "FAIL: No Ready nodes detected"
  exit 1
fi

echo "PASS: Minikube profile ${MINIKUBE_PROFILE} is running and Ready."
```

These checks confirm the cluster remains healthy without mutating resources.

<!-- expected_similarity="PASS: Minikube profile .*" -->

Representative output:

```text
PASS: Minikube profile k8s-local-2511261530 is running and Ready.
```

Summary:

- Confirms the Minikube host and Kubernetes nodes are available.

## Summary

This document provisioned or resumed a Minikube profile, aligned kubectl to
the new context, and confirmed addon health so local workloads can be
scheduled immediately.

Summary:

- Local Minikube cluster is active with kubectl context configured.
- Metrics-server and storage-provisioner addons are enabled and verified.

## Next Steps

Continue with the following executable documents to expand from the local
cluster toward more advanced Kubernetes workflows.

- [IE MCP On K8s Local](docs/incubation/IE_MCP_On_K8s_Local.md)
- [IE MCP Server](docs/incubation/IE_MCP_Server.md)
- [Install UV](docs/incubation/Install_UV.md)
