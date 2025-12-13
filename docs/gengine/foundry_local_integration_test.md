# Foundry Local Integration Test Guide

**Last Updated:** 2025-12-12

## Overview
This guide explains how to run real integration tests between the Echoes LLM service and a local instance of Azure Foundry Local, including setup, environment variables, and troubleshooting.

## Prerequisites
- Azure Foundry Local installed and available on your machine
- A compatible chat model downloaded (see Foundry docs)
- Python 3.12+, `uv`, and all project dependencies installed

## Setting up the Environment

### 1. Start Foundry Local
Open a terminal and run:

```powershell
foundry service set --port 8002
foundry model run qwen2.5-7b-instruct-qnn-npu:2
```
- Replace `qwen2.5-7b-instruct-qnn-npu:2` with the exact model name from `foundry model list` or `curl http://localhost:8002/openai/models`.
- Wait for the model to finish loading before proceeding.

### 2. Set Environment Variables
In a new terminal, set the following (PowerShell syntax):

```powershell
$env:ECHOES_LLM_PROVIDER = "foundry_local"
$env:ECHOES_LLM_BASE_URL = "http://localhost:8002"
$env:ECHOES_LLM_MODEL = "qwen2.5-7b-instruct-qnn-npu:2"
$env:FOUNDRY_LOCAL_TESTS = "1"
```

## Running a Manual Test with curl
To verify the endpoint is working, run:

```powershell
curl -v -X POST http://localhost:8002/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{ "model": "qwen2.5-7b-instruct-qnn-npu:2", "messages": [ { "role": "user", "content": "Hello" } ] }'
```
- You should receive a JSON response with a generated message.
- If you get a 400 or 500 error, check the model name and ensure the model is loaded.

## Running the Automated Integration Tests
From the project root, run:

```powershell
uv run pytest -m windows_only tests\echoes\test_foundry_local_integration.py
```
- These tests will only run if `FOUNDRY_LOCAL_TESTS=1` is set and the model is available.
- The tests will send real requests to your Foundry Local instance and check for valid responses.

## Troubleshooting
- **400 Bad Request:** Check that the model name is exact and loaded. Use `foundry model list` and `foundry model run <model>`.
- **500 Internal Server Error:** Usually a malformed JSON payload. Double-check your curl quoting and JSON structure.
- **No response or timeout:** Ensure Foundry Local is running and listening on the correct port.
- **Test skipped:** Make sure `FOUNDRY_LOCAL_TESTS=1` is set in your environment.

## References
- [docs/gengine/windows_only_tests.md](windows_only_tests.md)
- [pytest.ini](../../pytest.ini)
- [Foundry Local REST API Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/reference/reference-rest)

