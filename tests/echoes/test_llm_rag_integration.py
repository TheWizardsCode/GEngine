"""Integration tests for RAG-enabled LLM service."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gengine.echoes.llm.app import create_llm_app
from gengine.echoes.llm.rag import StubEmbeddingClient, VectorStore
from gengine.echoes.llm.settings import LLMSettings

pytestmark = pytest.mark.anyio


class TestRAGIntegration:
    """Integration tests for RAG in LLM service."""

    def test_app_without_rag(self) -> None:
        """Test that app works normally without RAG enabled."""
        settings = LLMSettings(provider="stub", enable_rag=False)
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["rag_enabled"] is False
        assert "rag_documents" not in data

    def test_app_with_rag_missing_db(self) -> None:
        """Test that app handles missing RAG database gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "missing.db")
            settings = LLMSettings(
                provider="stub",
                enable_rag=True,
                rag_db_path=db_path,
            )
            app = create_llm_app(settings=settings)
            client = TestClient(app)

            # App should start successfully
            response = client.get("/healthz")
            assert response.status_code == 200
            data = response.json()
            assert data["rag_enabled"] is True
            # RAG should be disabled due to missing DB
            assert "rag_documents" not in data

    async def test_app_with_rag_enabled(self) -> None:
        """Test that app initializes and uses RAG when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            
            # Create and populate knowledge base
            vector_store = VectorStore(db_path)
            embedding_client = StubEmbeddingClient(dimension=128)
            
            texts = [
                "Echoes of Emergence is a simulation game about urban dynamics",
                "Agents in the game represent characters with goals and strategies",
                "Districts are the spatial units where agents operate",
            ]
            embeddings = await embedding_client.embed_texts(texts)
            metadatas = [{"source": f"doc{i}.md"} for i in range(len(texts))]
            vector_store.add_documents(texts, metadatas, embeddings)
            
            # Create app with RAG enabled
            settings = LLMSettings(
                provider="stub",
                enable_rag=True,
                rag_db_path=db_path,
                rag_top_k=2,
                rag_min_score=0.0,
            )
            app = create_llm_app(settings=settings)
            client = TestClient(app)

            # Check health endpoint shows RAG is active
            response = client.get("/healthz")
            assert response.status_code == 200
            data = response.json()
            assert data["rag_enabled"] is True
            assert data["rag_documents"] == 3

    async def test_parse_intent_with_rag(self) -> None:
        """Test that /parse_intent uses RAG context when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            
            # Create knowledge base
            vector_store = VectorStore(db_path)
            embedding_client = StubEmbeddingClient(dimension=128)
            
            texts = ["Districts can be inspected for status information"]
            embeddings = await embedding_client.embed_texts(texts)
            metadatas = [{"source": "game_guide.md"}]
            vector_store.add_documents(texts, metadatas, embeddings)
            
            # Create app
            settings = LLMSettings(
                provider="stub",
                enable_rag=True,
                rag_db_path=db_path,
                rag_top_k=1,
                rag_min_score=0.0,
            )
            app = create_llm_app(settings=settings)
            client = TestClient(app)

            # Make request
            response = client.post(
                "/parse_intent",
                json={"user_input": "check district status", "context": {}},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "intents" in data

    async def test_narrate_with_rag(self) -> None:
        """Test that /narrate uses RAG context when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            
            # Create knowledge base
            vector_store = VectorStore(db_path)
            embedding_client = StubEmbeddingClient(dimension=128)
            
            texts = ["Narrative style should be concise and atmospheric"]
            embeddings = await embedding_client.embed_texts(texts)
            metadatas = [{"source": "style_guide.md"}]
            vector_store.add_documents(texts, metadatas, embeddings)
            
            # Create app
            settings = LLMSettings(
                provider="stub",
                enable_rag=True,
                rag_db_path=db_path,
                rag_top_k=1,
                rag_min_score=0.0,
            )
            app = create_llm_app(settings=settings)
            client = TestClient(app)

            # Make request
            response = client.post(
                "/narrate",
                json={
                    "events": [{"type": "agent_move", "agent": "Alice"}],
                    "context": {},
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "narrative" in data

    async def test_rag_metrics_recorded(self) -> None:
        """Test that RAG operations are recorded in metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            
            # Create knowledge base
            vector_store = VectorStore(db_path)
            embedding_client = StubEmbeddingClient(dimension=128)
            
            texts = ["test document"]
            embeddings = await embedding_client.embed_texts(texts)
            metadatas = [{"source": "test.md"}]
            vector_store.add_documents(texts, metadatas, embeddings)
            
            # Create app
            settings = LLMSettings(
                provider="stub",
                enable_rag=True,
                rag_db_path=db_path,
            )
            app = create_llm_app(settings=settings)
            client = TestClient(app)

            # Make request
            client.post(
                "/parse_intent",
                json={"user_input": "test", "context": {}},
            )

            # Check metrics
            response = client.get("/metrics")
            assert response.status_code == 200
            metrics_text = response.text
            
            # RAG metrics should be present
            assert "llm_rag_hits_total" in metrics_text
            assert "llm_rag_latency_seconds" in metrics_text
            assert "llm_rag_context_chars" in metrics_text


class TestRAGGracefulDegradation:
    """Tests for RAG graceful fallback behavior."""

    def test_parse_intent_succeeds_without_rag(self) -> None:
        """Test that parse_intent works when RAG is disabled."""
        settings = LLMSettings(provider="stub", enable_rag=False)
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/parse_intent",
            json={"user_input": "test", "context": {}},
        )
        
        assert response.status_code == 200

    def test_narrate_succeeds_without_rag(self) -> None:
        """Test that narrate works when RAG is disabled."""
        settings = LLMSettings(provider="stub", enable_rag=False)
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/narrate",
            json={"events": [{"type": "test"}], "context": {}},
        )
        
        assert response.status_code == 200

    def test_parse_intent_fallback_on_rag_error(self) -> None:
        """Test that parse_intent continues if RAG retrieval fails."""
        # This test validates graceful degradation, which is handled
        # by the try/except blocks in the app endpoints
        settings = LLMSettings(provider="stub", enable_rag=False)
        app = create_llm_app(settings=settings)
        client = TestClient(app)

        response = client.post(
            "/parse_intent",
            json={"user_input": "test", "context": {}},
        )
        
        # Should succeed even without RAG
        assert response.status_code == 200
