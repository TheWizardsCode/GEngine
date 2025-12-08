#!/bin/bash
set -e

# Ensure environment is set up
if [ ! -d ".venv" ]; then
    echo "Setting up environment..."
    uv venv
    source .venv/bin/activate
    uv pip install -e .[dev]
else
    source .venv/bin/activate
fi

# Parse for --ui flag
run_ui_demo=false
args=()
for arg in "$@"; do
    if [[ "$arg" == "--ui" ]]; then
        run_ui_demo=true
    else
        args+=("$arg")
    fi
done

if [ "$run_ui_demo" = true ]; then
    echo "Starting Echoes of Emergence Terminal UI..."
    uv run echoes-shell --ui "${args[@]}"
else
    echo "Starting Echoes of Emergence CLI shell..."
    uv run echoes-shell "${args[@]}"
fi