# Running the LLM Service for Foundry Local Integration

**Last Updated:** 2025-12-12

## Overview

When integrating with Foundry Local, the LLM service must be accessible to both your simulation (which may run in WSL) and the Foundry Local instance (which runs on Windows). To ensure compatibility, you should run the LLM service on the Windows side. This allows WSL applications to communicate with Foundry Local via the Windows network interface.

## Why Run the LLM Service on Windows?

- **Foundry Local** typically runs natively on Windows and expects to communicate with services on the Windows network stack.
- **WSL (Windows Subsystem for Linux)** applications can access Windows network services, but Windows applications cannot easily access services running inside WSL.
- Running the LLM service on Windows ensures both WSL and Foundry Local can reach it via `localhost` or the Windows IP address.

## Step-by-Step Setup

### 1. Clone the Repository (on Windows)

Open PowerShell and run:

```powershell
cd C:\Users\<your-username>
# Replace <REPO_URL> with your actual repository URL
git clone <REPO_URL> GEngine-Windows
cd GEngine-Windows
```

### 2. Create and Activate a Windows Python Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

### 3. Install Dependencies

```powershell
pip install -e .[dev]
```

### 4. (Optional) Configure LLM Provider

Set environment variables as needed (for OpenAI, Anthropic, etc.):

```powershell
$env:ECHOES_LLM_PROVIDER = "stub"          # or 'openai', 'anthropic'
$env:ECHOES_LLM_API_KEY = "your-key-here"  # if using openai/anthropic
$env:ECHOES_LLM_MODEL = "gpt-4"            # model name if needed
```

### 5. Start the LLM Service

```powershell
uv run echoes-llm-service
```

The service will start on port 8001 by default. Both WSL and Foundry Local can now access it at `http://localhost:8001`.

## Troubleshooting

- **Do not run the LLM service from inside WSL** if you need Foundry Local (on Windows) to access it.
- If you encounter issues with `uv` not being found, ensure your Python Scripts directory is in your PATH, or use `python -m uv run echoes-llm-service`.
- If you need to use a different port, set the `ECHOES_LLM_PORT` environment variable before starting the service.

## Example: Accessing the LLM Service from WSL

In your WSL terminal, you can reach the Windows-hosted LLM service using:

```bash
curl http://localhost:8001/healthz
```

This should return a JSON health status if the service is running.

## See Also
- [LLM Service API Reference](gengine/llm_service.md)
- [Foundry Local Integration Guide](narrative/foundry_local_integration.md)
