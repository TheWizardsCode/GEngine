# TinyLlama ONNX Chat Interface

This document describes how to set up and use the TinyLlama-1.1B-Chat-v1.0 ONNX chat interface with NPU acceleration on Copilot+ PC with Snapdragon hardware.

## Overview

The TinyLlama chat interface provides a simple conversational AI experience running entirely locally on your device. It uses:

- **Model**: TinyLlama-1.1B-Chat-v1.0 (ONNX format)
- **Runtime**: ONNX Runtime with QNN Execution Provider
- **Hardware**: Snapdragon NPU for accelerated inference
- **Interface**: Command-line chat interface with Rich UI

## Prerequisites

### Hardware Requirements

- Copilot+ PC with Snapdragon X Elite or X Plus processor
- At least 4GB of available RAM
- 2-3GB of disk space for model files

### Software Requirements

- Python 3.12+
- uv package manager
- ONNX Runtime with QNN support
- Tokenizers library

## Installation

### 1. Install Dependencies

The required dependencies are already included in `pyproject.toml`:

```bash
cd /home/runner/work/GEngine/GEngine
uv sync
```

This will install:
- `onnxruntime>=1.16.0` - ONNX Runtime for model inference
- `numpy>=1.24.0` - Numerical computing library
- `tokenizers>=0.15.0` - Tokenizer library for text processing

### 2. Download TinyLlama Model

You need to download the TinyLlama-1.1B-Chat-v1.0 model in ONNX format. There are two options:

#### Option A: Download Pre-converted ONNX Model

1. Visit the Hugging Face model repository:
   ```
   https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0
   ```

2. Look for ONNX format files or converted models in the "Files and versions" tab

3. Download:
   - `model.onnx` (or similar ONNX model file)
   - `tokenizer.json` (tokenizer configuration)

4. Save to a directory, e.g., `~/models/tinyllama/`

#### Option B: Convert PyTorch Model to ONNX

If ONNX format is not available, you can convert the PyTorch model:

1. Install additional tools:
   ```bash
   pip install transformers torch onnx
   ```

2. Use a conversion script:
   ```python
   from transformers import AutoModelForCausalLM, AutoTokenizer
   import torch
   
   model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
   
   # Load model and tokenizer
   model = AutoModelForCausalLM.from_pretrained(model_name)
   tokenizer = AutoTokenizer.from_pretrained(model_name)
   
   # Export to ONNX
   dummy_input = torch.randint(0, 1000, (1, 10))
   torch.onnx.export(
       model,
       dummy_input,
       "tinyllama-chat-v1.0.onnx",
       opset_version=14,
       input_names=["input_ids"],
       output_names=["logits"],
       dynamic_axes={"input_ids": {0: "batch", 1: "sequence"}}
   )
   
   # Save tokenizer
   tokenizer.save_pretrained("./tokenizer/")
   ```

3. Save the model and tokenizer files to a directory

### 3. Configure Environment Variables

Set the required environment variables to point to your model files:

```bash
# Required: Path to the ONNX model file
export TINYLLAMA_MODEL_PATH="$HOME/models/tinyllama/model.onnx"

# Required: Path to the tokenizer file
export TINYLLAMA_TOKENIZER_PATH="$HOME/models/tinyllama/tokenizer.json"

# Optional: Enable NPU acceleration (default: true)
export TINYLLAMA_USE_NPU=true

# Optional: Maximum sequence length (default: 512)
export TINYLLAMA_MAX_LENGTH=512
```

You can add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make them persistent.

## Usage

### Running the Chat Interface

Once configured, launch the chat interface:

```bash
uv run echoes-tinyllama-chat
```

Or using Python directly:

```bash
uv run python -m gengine.echoes.llm.tinyllama_chat
```

### Chat Commands

The chat interface supports the following commands:

- **Regular chat**: Just type your message and press Enter
- `/help` - Show available commands
- `/info` - Display model information and execution provider
- `/clear` - Clear conversation history
- `/history` - Show conversation history
- `/quit` or `/exit` - Exit the chat interface

### Example Session

```
╭─────────────────────────────── Welcome ────────────────────────────────╮
│ TinyLlama Chat Interface                                                │
│                                                                          │
│ This is a simple chat interface using TinyLlama-1.1B-Chat-v1.0         │
│ running locally with ONNX Runtime.                                      │
│                                                                          │
│ Commands:                                                                │
│   /quit or /exit - Exit the chat                                        │
│   /help - Show this help message                                        │
│   /info - Show model information                                        │
│                                                                          │
│ Type your message and press Enter to chat.                              │
╰─────────────────────────────────────────────────────────────────────────╯

You: Hello! How are you?
TinyLlama: I'm doing well, thank you for asking! How can I help you today?

You: /info
╭─────────────────────── Model Information ───────────────────────╮
│ Model: TinyLlama-1.1B-Chat-v1.0                                  │
│ Path: /home/user/models/tinyllama/model.onnx                     │
│ Execution Provider: QNNExecutionProvider                         │
│ NPU Acceleration: True                                           │
│ Max Length: 512                                                  │
╰─────────────────────────────────────────────────────────────────╯

You: /quit
Goodbye!
```

## Troubleshooting

### Model Not Found Error

If you see:
```
ValueError: Model file not found: /path/to/model.onnx
```

**Solution**: Check that `TINYLLAMA_MODEL_PATH` points to a valid ONNX model file.

### Tokenizer Not Found Error

If you see:
```
ValueError: Tokenizer not found. Please set TINYLLAMA_TOKENIZER_PATH...
```

**Solution**: Download the `tokenizer.json` file from the TinyLlama repository and set `TINYLLAMA_TOKENIZER_PATH`.

### Import Error

If you see:
```
ImportError: onnxruntime is required for TinyLlama provider
```

**Solution**: Install dependencies:
```bash
uv pip install onnxruntime tokenizers numpy
```

### NPU Not Available

If NPU acceleration is not available, the provider will automatically fall back to CPU execution. You'll see:
```
TinyLlama using execution provider: CPUExecutionProvider
```

This is normal on systems without Snapdragon NPU support. The model will still work, just slower.

### Slow Performance

If inference is slow:

1. **Enable NPU**: Ensure `TINYLLAMA_USE_NPU=true`
2. **Check execution provider**: Run `/info` in chat to verify it's using `QNNExecutionProvider`
3. **Reduce max length**: Set `TINYLLAMA_MAX_LENGTH=256` for faster responses
4. **Install QNN-enabled ONNX Runtime**: You may need a special build of ONNX Runtime with QNN support

## Integration with GEngine

The TinyLlama provider is integrated into the existing GEngine LLM infrastructure:

### Using in LLM Service

You can configure the LLM service to use TinyLlama:

```bash
export ECHOES_LLM_PROVIDER=tinyllama
export TINYLLAMA_MODEL_PATH=/path/to/model.onnx
export TINYLLAMA_TOKENIZER_PATH=/path/to/tokenizer.json

uv run echoes-llm-service
```

The service will use TinyLlama for intent parsing and narration endpoints.

### Using Programmatically

```python
from gengine.echoes.llm import create_provider, LLMSettings

# Create settings
settings = LLMSettings(provider="tinyllama")

# Create provider
provider = create_provider(settings)

# Parse intent
result = await provider.parse_intent(
    "inspect the industrial district",
    context={"tick": 42}
)
print(result.intents)

# Generate narrative
narration = await provider.narrate(
    events=[{"type": "stability_drop", "value": 0.1}],
    context={"district": "industrial-tier"}
)
print(narration.narrative)
```

## Architecture

The TinyLlama integration follows the existing provider pattern:

```
gengine.echoes.llm/
├── providers.py              # LLMProvider abstract base class
├── settings.py               # LLMSettings configuration
├── tinyllama_provider.py     # TinyLlamaONNXProvider implementation
├── tinyllama_chat.py         # Interactive chat interface
└── ...
```

### Key Components

- **TinyLlamaONNXProvider**: Implements the `LLMProvider` interface using ONNX Runtime
- **Chat Template**: Uses TinyLlama's chat format with system/user/assistant roles
- **Tokenization**: Uses HuggingFace tokenizers library
- **Execution Providers**: Supports QNNExecutionProvider (NPU) and CPUExecutionProvider

## Performance Considerations

### Memory Usage

- Model size: ~2GB (FP32) or ~1GB (FP16/INT8 quantized)
- Runtime overhead: ~500MB
- Total: 2.5-3GB RAM recommended

### Inference Speed

With NPU acceleration (QNNExecutionProvider):
- First token: ~50-100ms
- Subsequent tokens: ~10-20ms per token
- Total for 100 tokens: ~1-2 seconds

Without NPU (CPU):
- First token: ~200-500ms
- Subsequent tokens: ~50-100ms per token
- Total for 100 tokens: ~5-10 seconds

### Optimizations

1. **Model Quantization**: Convert to INT8 for smaller size and faster inference
2. **Batch Processing**: Process multiple requests together
3. **Caching**: Cache tokenizer and model weights
4. **Early Stopping**: Use temperature and top-p sampling for faster generation

## Future Improvements

Potential enhancements for the TinyLlama integration:

1. **Proper Autoregressive Generation**: Implement full token-by-token generation
2. **Streaming Responses**: Stream tokens as they're generated
3. **Context Management**: Better handling of conversation history
4. **Fine-tuning Support**: Load custom fine-tuned models
5. **Quantization**: Support INT8/INT4 quantized models
6. **Beam Search**: Implement beam search for better quality
7. **Temperature/Top-p**: Expose sampling parameters to users

## References

- TinyLlama Model: https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0
- ONNX Runtime: https://onnxruntime.ai/
- QNN Execution Provider: https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html
- Tokenizers: https://github.com/huggingface/tokenizers

## Support

For issues or questions:

1. Check this documentation first
2. Review the Troubleshooting section
3. Check environment variables are set correctly
4. Verify model files exist and are valid ONNX format
5. Test with `/info` command to check execution provider
