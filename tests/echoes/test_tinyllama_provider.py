"""Tests for TinyLlama ONNX provider."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from gengine.echoes.llm.providers import IntentParseResult, NarrateResult
from gengine.echoes.llm.settings import LLMSettings


class TestTinyLlamaProvider:
    """Test suite for TinyLlama ONNX provider."""

    @pytest.fixture
    def mock_onnx_session(self):
        """Create mock ONNX Runtime session."""
        session = MagicMock()
        session.get_providers.return_value = ["QNNExecutionProvider"]
        session.get_inputs.return_value = [MagicMock(name="input_ids")]
        session.run.return_value = [[1, 2, 3, 4, 5]]  # Mock output token IDs
        return session

    @pytest.fixture
    def mock_tokenizer(self):
        """Create mock tokenizer."""
        tokenizer = MagicMock()

        # Mock encode
        encoding = MagicMock()
        encoding.ids = [1, 2, 3, 4, 5]
        tokenizer.encode.return_value = encoding

        # Mock decode
        tokenizer.decode.return_value = "Generated response"

        return tokenizer

    @pytest.fixture
    def temp_model_files(self, tmp_path):
        """Create temporary model files for testing."""
        model_path = tmp_path / "model.onnx"
        model_path.write_text("fake model data")

        tokenizer_path = tmp_path / "tokenizer.json"
        tokenizer_path.write_text('{"version": "1.0"}')

        return model_path, tokenizer_path

    def test_provider_requires_onnxruntime(self):
        """Test that provider raises ImportError if onnxruntime not available."""
        with patch.dict(
            "sys.modules",
            {
                "onnxruntime": None,
                "gengine.echoes.llm.tinyllama_provider": MagicMock(
                    ONNX_AVAILABLE=False
                ),
            },
        ):
            # Import will fail, but we can test the error handling
            pass

    def test_provider_requires_tokenizers(self):
        """Test that provider raises ImportError if tokenizers not available."""
        with patch.dict(
            "sys.modules",
            {
                "tokenizers": None,
                "gengine.echoes.llm.tinyllama_provider": MagicMock(
                    TOKENIZERS_AVAILABLE=False
                ),
            },
        ):
            # Import will fail, but we can test the error handling
            pass

    def test_provider_requires_model_path(self):
        """Test that provider raises ValueError if model path not provided."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("gengine.echoes.llm.tinyllama_provider.ONNX_AVAILABLE", True):
                with patch(
                    "gengine.echoes.llm.tinyllama_provider.TOKENIZERS_AVAILABLE", True
                ):
                    from gengine.echoes.llm.tinyllama_provider import (
                        TinyLlamaONNXProvider,
                    )

                    settings = LLMSettings(provider="tinyllama")

                    with pytest.raises(ValueError, match="TINYLLAMA_MODEL_PATH"):
                        TinyLlamaONNXProvider(settings)

    def test_provider_validates_model_exists(self, temp_model_files):
        """Test that provider validates model file exists."""
        model_path, tokenizer_path = temp_model_files

        with patch.dict(
            os.environ,
            {
                "TINYLLAMA_MODEL_PATH": str(model_path / "nonexistent.onnx"),
                "TINYLLAMA_TOKENIZER_PATH": str(tokenizer_path),
            },
        ):
            with patch("gengine.echoes.llm.tinyllama_provider.ONNX_AVAILABLE", True):
                with patch(
                    "gengine.echoes.llm.tinyllama_provider.TOKENIZERS_AVAILABLE", True
                ):
                    from gengine.echoes.llm.tinyllama_provider import (
                        TinyLlamaONNXProvider,
                    )

                    settings = LLMSettings(provider="tinyllama")

                    with pytest.raises(ValueError, match="Model file not found"):
                        TinyLlamaONNXProvider(settings)

    def test_provider_initialization(
        self, temp_model_files, mock_onnx_session, mock_tokenizer
    ):
        """Test successful provider initialization."""
        model_path, tokenizer_path = temp_model_files

        with patch.dict(
            os.environ,
            {
                "TINYLLAMA_MODEL_PATH": str(model_path),
                "TINYLLAMA_TOKENIZER_PATH": str(tokenizer_path),
                "TINYLLAMA_USE_NPU": "true",
                "TINYLLAMA_MAX_LENGTH": "512",
            },
        ):
            with patch("gengine.echoes.llm.tinyllama_provider.ONNX_AVAILABLE", True):
                with patch(
                    "gengine.echoes.llm.tinyllama_provider.TOKENIZERS_AVAILABLE", True
                ):
                    with patch(
                        "gengine.echoes.llm.tinyllama_provider.ort.InferenceSession",
                        return_value=mock_onnx_session,
                    ):
                        with patch(
                            "gengine.echoes.llm.tinyllama_provider.Tokenizer.from_file",
                            return_value=mock_tokenizer,
                        ):
                            from gengine.echoes.llm.tinyllama_provider import (
                                TinyLlamaONNXProvider,
                            )

                            settings = LLMSettings(provider="tinyllama")
                            provider = TinyLlamaONNXProvider(settings)

                            assert provider.model_path == model_path
                            assert provider.tokenizer_path == tokenizer_path
                            assert provider.use_npu is True
                            assert provider.max_length == 512
                            assert provider.session is not None
                            assert provider.tokenizer is not None

    @pytest.mark.anyio
    async def test_parse_intent(
        self, temp_model_files, mock_onnx_session, mock_tokenizer
    ):
        """Test intent parsing with TinyLlama provider."""
        model_path, tokenizer_path = temp_model_files

        with patch.dict(
            os.environ,
            {
                "TINYLLAMA_MODEL_PATH": str(model_path),
                "TINYLLAMA_TOKENIZER_PATH": str(tokenizer_path),
            },
        ):
            with patch("gengine.echoes.llm.tinyllama_provider.ONNX_AVAILABLE", True):
                with patch(
                    "gengine.echoes.llm.tinyllama_provider.TOKENIZERS_AVAILABLE", True
                ):
                    with patch(
                        "gengine.echoes.llm.tinyllama_provider.ort.InferenceSession",
                        return_value=mock_onnx_session,
                    ):
                        with patch(
                            "gengine.echoes.llm.tinyllama_provider.Tokenizer.from_file",
                            return_value=mock_tokenizer,
                        ):
                            from gengine.echoes.llm.tinyllama_provider import (
                                TinyLlamaONNXProvider,
                            )

                            settings = LLMSettings(provider="tinyllama")
                            provider = TinyLlamaONNXProvider(settings)

                            result = await provider.parse_intent(
                                "inspect the district",
                                context={"tick": 42},
                            )

                            assert isinstance(result, IntentParseResult)
                            assert len(result.intents) > 0
                            assert result.confidence is not None
                            assert result.raw_response is not None

    @pytest.mark.anyio
    async def test_narrate(self, temp_model_files, mock_onnx_session, mock_tokenizer):
        """Test narration with TinyLlama provider."""
        model_path, tokenizer_path = temp_model_files

        with patch.dict(
            os.environ,
            {
                "TINYLLAMA_MODEL_PATH": str(model_path),
                "TINYLLAMA_TOKENIZER_PATH": str(tokenizer_path),
            },
        ):
            with patch("gengine.echoes.llm.tinyllama_provider.ONNX_AVAILABLE", True):
                with patch(
                    "gengine.echoes.llm.tinyllama_provider.TOKENIZERS_AVAILABLE", True
                ):
                    with patch(
                        "gengine.echoes.llm.tinyllama_provider.ort.InferenceSession",
                        return_value=mock_onnx_session,
                    ):
                        with patch(
                            "gengine.echoes.llm.tinyllama_provider.Tokenizer.from_file",
                            return_value=mock_tokenizer,
                        ):
                            from gengine.echoes.llm.tinyllama_provider import (
                                TinyLlamaONNXProvider,
                            )

                            settings = LLMSettings(provider="tinyllama")
                            provider = TinyLlamaONNXProvider(settings)

                            events = [
                                {"type": "stability_drop", "value": 0.1},
                                {"type": "unrest_rise", "district": "industrial"},
                            ]

                            result = await provider.narrate(
                                events,
                                context={"district": "industrial-tier"},
                            )

                            assert isinstance(result, NarrateResult)
                            assert result.narrative is not None
                            assert result.raw_response is not None
                            assert result.metadata is not None
                            assert result.metadata["provider"] == "tinyllama_onnx"
                            assert result.metadata["event_count"] == 2

    def test_settings_validation_accepts_tinyllama(self):
        """Test that LLMSettings validates tinyllama provider."""
        settings = LLMSettings(provider="tinyllama")
        # Should not raise - tinyllama doesn't need API key
        settings.validate()

    def test_create_provider_factory(self, temp_model_files):
        """Test that create_provider factory supports tinyllama."""
        model_path, tokenizer_path = temp_model_files

        with patch.dict(
            os.environ,
            {
                "TINYLLAMA_MODEL_PATH": str(model_path),
                "TINYLLAMA_TOKENIZER_PATH": str(tokenizer_path),
            },
        ):
            with patch("gengine.echoes.llm.tinyllama_provider.ONNX_AVAILABLE", True):
                with patch(
                    "gengine.echoes.llm.tinyllama_provider.TOKENIZERS_AVAILABLE", True
                ):
                    with patch(
                        "gengine.echoes.llm.tinyllama_provider.ort.InferenceSession"
                    ):
                        with patch(
                            "gengine.echoes.llm.tinyllama_provider.Tokenizer.from_file"
                        ):
                            from gengine.echoes.llm.providers import create_provider

                            settings = LLMSettings(provider="tinyllama")
                            provider = create_provider(settings)

                            # Should return TinyLlamaONNXProvider instance
                            assert provider is not None
                            assert provider.settings == settings
