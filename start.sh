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

# Run the Terminal UI demo
echo "Starting Echoes of Emergence Terminal UI..."
# python scripts/demo_terminal_ui.py "$@"
uv run echoes-shell "$@"