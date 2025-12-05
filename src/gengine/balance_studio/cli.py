"""CLI entry point for Balance Studio.

This module provides the main() function that is registered as the
`echoes-balance-studio` command in pyproject.toml.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Import and re-export main from the script module
# We need to load it dynamically to avoid circular imports


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the echoes-balance-studio command.

    This function imports and runs the main CLI from the scripts module.

    Parameters
    ----------
    argv
        Command-line arguments (defaults to sys.argv[1:]).

    Returns
    -------
    int
        Exit code.
    """
    # Import the main function from the script
    from importlib import util

    script_dir = Path(__file__).resolve().parents[3] / "scripts"
    script_path = script_dir / "echoes_balance_studio.py"

    spec = util.spec_from_file_location("echoes_balance_studio", script_path)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"Failed to load Balance Studio script: {script_path}\n")
        return 1

    module = util.module_from_spec(spec)
    sys.modules.setdefault("echoes_balance_studio", module)
    spec.loader.exec_module(module)

    return module.main(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
