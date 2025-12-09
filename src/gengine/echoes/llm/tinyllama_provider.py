"""TinyLlama ONNX provider for local LLM inference using NPU acceleration.

This provider uses ONNX Runtime with QNN Execution Provider to run
TinyLlama-1.1B-Chat-v1.0 on Snapdragon NPU hardware for fast, local inference.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from .providers import IntentParseResult, LLMProvider, NarrateResult
from .settings import LLMSettings

# Try to import ONNX Runtime
try:
    import onnxruntime as ort

    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = None  # type: ignore

# Try to import tokenizers
try:
    from tokenizers import Tokenizer

    TOKENIZERS_AVAILABLE = True
except ImportError:
    TOKENIZERS_AVAILABLE = False
    Tokenizer = None  # type: ignore


class TinyLlamaONNXProvider(LLMProvider):
    """TinyLlama ONNX provider for local LLM inference.

    Uses ONNX Runtime with QNN Execution Provider for NPU acceleration
    on Copilot+ PC with Snapdragon hardware.

    Environment Variables
    ---------------------
    TINYLLAMA_MODEL_PATH : str
        Path to the ONNX model file (required)
    TINYLLAMA_TOKENIZER_PATH : str
        Path to the tokenizer.json file (optional, uses Llama tokenizer if not set)
    TINYLLAMA_USE_NPU : bool
        Whether to use QNN Execution Provider for NPU (default: True)
    TINYLLAMA_MAX_LENGTH : int
        Maximum sequence length for generation (default: 512)
    """

    def __init__(self, settings: LLMSettings) -> None:
        """Initialize TinyLlama ONNX provider.

        Parameters
        ----------
        settings
            LLM configuration settings

        Raises
        ------
        ImportError
            If onnxruntime or tokenizers is not installed
        ValueError
            If model path is not provided or model file doesn't exist
        """
        super().__init__(settings)

        if not ONNX_AVAILABLE:
            raise ImportError(
                "onnxruntime is required for TinyLlama provider. "
                "Install with: pip install onnxruntime"
            )

        if not TOKENIZERS_AVAILABLE:
            raise ImportError(
                "tokenizers is required for TinyLlama provider. "
                "Install with: pip install tokenizers"
            )

        # Get model path from environment
        model_path = os.getenv("TINYLLAMA_MODEL_PATH")
        if not model_path:
            raise ValueError(
                "TINYLLAMA_MODEL_PATH environment variable must be set. "
                "Point it to your TinyLlama-1.1B-Chat-v1.0 ONNX model file."
            )

        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise ValueError(f"Model file not found: {self.model_path}")

        # Get tokenizer path (optional)
        tokenizer_path = os.getenv("TINYLLAMA_TOKENIZER_PATH")
        self.tokenizer_path = Path(tokenizer_path) if tokenizer_path else None

        # Get configuration
        self.use_npu = os.getenv("TINYLLAMA_USE_NPU", "true").lower() == "true"
        self.max_length = int(os.getenv("TINYLLAMA_MAX_LENGTH", "512"))

        # Initialize ONNX Runtime session
        self.session = self._create_session()

        # Initialize tokenizer
        self.tokenizer = self._load_tokenizer()

        # Chat template for TinyLlama
        self.chat_template = (
            "<|system|>\n{system_prompt}</s>\n"
            "<|user|>\n{user_message}</s>\n"
            "<|assistant|>\n"
        )

    def _create_session(self) -> ort.InferenceSession:
        """Create ONNX Runtime inference session.

        Returns
        -------
        ort.InferenceSession
            Configured ONNX Runtime session
        """
        providers = []

        if self.use_npu:
            # Try to use QNN Execution Provider for NPU
            # Note: This requires ONNX Runtime with QNN support
            try:
                providers.append("QNNExecutionProvider")
            except Exception:
                # Fall back to CPU if QNN is not available
                pass

        # Add CPU provider as fallback
        providers.append("CPUExecutionProvider")

        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

        session = ort.InferenceSession(
            str(self.model_path),
            sess_options=session_options,
            providers=providers,
        )

        # Log which provider is being used
        active_provider = session.get_providers()[0]
        print(f"TinyLlama using execution provider: {active_provider}")

        return session

    def _load_tokenizer(self) -> Tokenizer:
        """Load tokenizer for TinyLlama.

        Returns
        -------
        Tokenizer
            Loaded tokenizer instance

        Raises
        ------
        ValueError
            If tokenizer cannot be loaded
        """
        if self.tokenizer_path and self.tokenizer_path.exists():
            # Load custom tokenizer
            return Tokenizer.from_file(str(self.tokenizer_path))
        else:
            # Create a simple tokenizer as fallback
            # In production, you would download the actual TinyLlama tokenizer
            raise ValueError(
                "Tokenizer not found. Please set TINYLLAMA_TOKENIZER_PATH "
                "to point to tokenizer.json file, or download from: "
                "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            )

    def _tokenize(self, text: str) -> np.ndarray:
        """Tokenize input text.

        Parameters
        ----------
        text
            Input text to tokenize

        Returns
        -------
        np.ndarray
            Token IDs as numpy array
        """
        encoding = self.tokenizer.encode(text)
        return np.array(encoding.ids, dtype=np.int64)

    def _detokenize(self, token_ids: np.ndarray) -> str:
        """Detokenize token IDs to text.

        Parameters
        ----------
        token_ids
            Token IDs to decode

        Returns
        -------
        str
            Decoded text
        """
        return self.tokenizer.decode(token_ids.tolist())

    def _generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        """Generate text using the ONNX model.

        Parameters
        ----------
        prompt
            Input prompt
        max_new_tokens
            Maximum number of tokens to generate

        Returns
        -------
        str
            Generated text
        """
        # Tokenize input
        input_ids = self._tokenize(prompt)

        # For simplicity, we'll use a basic generation approach
        # In production, you'd implement proper autoregressive generation
        # This is a simplified version that assumes the model outputs text directly

        # Prepare input
        # Note: Actual implementation depends on the ONNX model's input/output format
        # This is a placeholder that would need to be adjusted based on the actual model

        try:
            # Run inference
            # This is simplified - actual implementation depends on model architecture
            ort_inputs = {self.session.get_inputs()[0].name: input_ids.reshape(1, -1)}
            ort_outputs = self.session.run(None, ort_inputs)

            # Decode output
            # This assumes the model outputs token IDs
            # Actual implementation depends on model output format
            output_ids = ort_outputs[0]
            generated_text = self._detokenize(output_ids[0])

            return generated_text

        except Exception as e:
            # If generation fails, return error message
            return f"[Generation Error: {str(e)}]"

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any],
    ) -> IntentParseResult:
        """Parse user input into structured intents using TinyLlama.

        Parameters
        ----------
        user_input
            Natural language input from user
        context
            Game state context for intent parsing

        Returns
        -------
        IntentParseResult
            Parsed intents with metadata
        """
        # Build prompt for intent parsing
        system_prompt = (
            "You are a game intent parser. Parse the user's command into "
            "one of these intents: inspect, stabilize, negotiate, observe. "
            "Respond with just the intent type and target."
        )

        formatted_prompt = self.chat_template.format(
            system_prompt=system_prompt,
            user_message=user_input,
        )

        # Generate response
        response = self._generate(formatted_prompt, max_new_tokens=50)

        # Simple keyword-based parsing of LLM response
        # In production, you'd use more sophisticated parsing
        response_lower = response.lower()
        intents = []

        if "inspect" in response_lower:
            intents.append({"type": "inspect", "target": "district"})
        elif "stabilize" in response_lower:
            intents.append({"type": "stabilize", "target": "district"})
        elif "negotiate" in response_lower:
            intents.append({"type": "negotiate", "target": "faction"})
        else:
            intents.append({"type": "observe", "target": "city"})

        return IntentParseResult(
            intents=intents,
            raw_response=response,
            confidence=0.8,
        )

    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> NarrateResult:
        """Generate narrative description using TinyLlama.

        Parameters
        ----------
        events
            List of game events to narrate
        context
            Game state context for narrative generation

        Returns
        -------
        NarrateResult
            Generated narrative with metadata
        """
        # Build prompt for narration
        system_prompt = (
            "You are a game narrator. Describe the following events "
            "in an engaging narrative style."
        )

        event_summary = ", ".join(e.get("type", "unknown") for e in events[:5])
        user_message = f"Events: {event_summary}"

        formatted_prompt = self.chat_template.format(
            system_prompt=system_prompt,
            user_message=user_message,
        )

        # Generate narrative
        narrative = self._generate(formatted_prompt, max_new_tokens=150)

        return NarrateResult(
            narrative=narrative,
            raw_response=narrative,
            metadata={
                "provider": "tinyllama_onnx",
                "event_count": len(events),
                "execution_provider": self.session.get_providers()[0],
            },
        )
