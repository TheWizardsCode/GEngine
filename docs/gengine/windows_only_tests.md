# Running Windows-Only Tests

**Last Updated:** 2025-12-12

## Overview
Some tests in this project are marked as `windows_only` because they require Windows-specific APIs or behaviors. By default, these tests are skipped to avoid failures on other platforms.

## How to Run Windows-Only Tests

To run only the Windows-specific tests, use the following command from the project root in PowerShell:

```powershell
uv run pytest -m windows_only
```

Or, to include them alongside other markers:

```powershell
uv run pytest -m "windows_only or unit"
```

## How It Works
- The `windows_only` marker is defined in `pytest.ini`.
- The default pytest options (`addopts`) exclude these tests unless you explicitly include them with `-m windows_only`.
- This prevents accidental failures on non-Windows platforms or CI environments.

## Marking a Test as Windows-Only
Add the following to your test or test class:

```python
import pytest
pytestmark = pytest.mark.windows_only
```

Or decorate individual test functions:

```python
@pytest.mark.windows_only
def test_windows_behavior():
    ...
```

## See Also
- [pytest.ini](../../pytest.ini) for marker definitions and options
- [pytest documentation on markers](https://docs.pytest.org/en/stable/example/markers.html)

