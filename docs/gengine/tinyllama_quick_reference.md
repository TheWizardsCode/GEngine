# TinyLlama Chat Interface - Quick Reference

## What is it?

A local AI chat interface using TinyLlama-1.1B-Chat-v1.0 running on your device with NPU acceleration. No cloud, no API keys, complete privacy.

## Quick Start (3 steps)

### 1. Install
```bash
cd /home/runner/work/GEngine/GEngine
uv sync
```

### 2. Download Model
Get model files from: https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0
- `model.onnx` (ONNX model file)
- `tokenizer.json` (tokenizer file)

Save to: `~/models/tinyllama/`

### 3. Configure & Run
```bash
# Set environment
export TINYLLAMA_MODEL_PATH="$HOME/models/tinyllama/model.onnx"
export TINYLLAMA_TOKENIZER_PATH="$HOME/models/tinyllama/tokenizer.json"

# Run
uv run echoes-tinyllama-chat
```

## Chat Commands

| Command | Description |
|---------|-------------|
| (text) | Chat normally |
| `/help` | Show commands |
| `/info` | Model info |
| `/history` | View history |
| `/clear` | Clear history |
| `/quit` | Exit |

## Features

✅ **Local** - Runs on your device  
✅ **Private** - No data sent to cloud  
✅ **Fast** - NPU acceleration (50-100ms)  
✅ **Free** - No API costs  
✅ **Offline** - Works without internet  

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TINYLLAMA_MODEL_PATH` | Yes | - | Path to .onnx model |
| `TINYLLAMA_TOKENIZER_PATH` | Yes | - | Path to tokenizer.json |
| `TINYLLAMA_USE_NPU` | No | true | Enable NPU acceleration |
| `TINYLLAMA_MAX_LENGTH` | No | 512 | Max sequence length |

## Integration with GEngine

Use in LLM service:
```bash
export ECHOES_LLM_PROVIDER=tinyllama
export TINYLLAMA_MODEL_PATH=/path/to/model.onnx
export TINYLLAMA_TOKENIZER_PATH=/path/to/tokenizer.json
uv run echoes-llm-service
```

Use programmatically:
```python
from gengine.echoes.llm import create_provider, LLMSettings

settings = LLMSettings(provider="tinyllama")
provider = create_provider(settings)

result = await provider.parse_intent("inspect district", {})
narration = await provider.narrate([{"type": "event"}], {})
```

## Troubleshooting

**Model not found?**
```bash
# Check path
echo $TINYLLAMA_MODEL_PATH
ls -lh $TINYLLAMA_MODEL_PATH
```

**Slow performance?**
```bash
# Check execution provider in chat:
/info
# Should show: QNNExecutionProvider (fast)
# If CPUExecutionProvider: NPU not available
```

**Missing dependencies?**
```bash
uv pip install onnxruntime tokenizers numpy
```

## Documentation

📖 [Full Setup Guide](./tinyllama_chat_setup.md)  
📖 [README](../../README.md#tinyllama-chat-interface-phase-13-m1311)  
📖 [Implementation Plan](../simul/emergent_story_game_implementation_plan.md#13-local-llm-integration-phase-13)

## Performance

| Hardware | First Token | Per Token | 100 Tokens |
|----------|-------------|-----------|------------|
| NPU | 50-100ms | 10-20ms | 1-2s |
| CPU | 200-500ms | 50-100ms | 5-10s |

## Support

For issues or questions, see:
1. [Troubleshooting Guide](./tinyllama_chat_setup.md#troubleshooting)
2. Check environment variables are set
3. Verify model files exist
4. Test with `/info` command
