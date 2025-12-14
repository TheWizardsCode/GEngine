"""Tests for LLM RAG (Retrieval-Augmented Generation) components."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from gengine.echoes.llm.rag import (
    DocumentChunker,
    RAGRetriever,
    RetrievedDocument,
    StubEmbeddingClient,
    VectorStore,
    format_retrieved_context,
)

pytestmark = pytest.mark.anyio


class TestDocumentChunker:
    """Tests for DocumentChunker."""

    def test_chunk_empty_text(self) -> None:
        chunker = DocumentChunker(chunk_size=10, overlap=2)
        chunks = chunker.chunk_text("", {})
        assert chunks == []

    def test_chunk_small_text(self) -> None:
        chunker = DocumentChunker(chunk_size=10, overlap=2)
        text = "This is a small text"
        chunks = chunker.chunk_text(text, {"source": "test.md"})
        
        assert len(chunks) == 1
        assert chunks[0]["content"] == text
        assert chunks[0]["metadata"]["source"] == "test.md"
        assert chunks[0]["metadata"]["chunk_index"] == 0

    def test_chunk_with_overlap(self) -> None:
        chunker = DocumentChunker(chunk_size=5, overlap=2)
        text = "one two three four five six seven eight nine ten"
        chunks = chunker.chunk_text(text, {"source": "test.md"})
        
        # Should create multiple chunks with overlap
        assert len(chunks) > 1
        
        # Check metadata
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i
            assert chunk["metadata"]["source"] == "test.md"
            assert "start_word" in chunk["metadata"]
            assert "end_word" in chunk["metadata"]

    def test_chunk_preserves_metadata(self) -> None:
        chunker = DocumentChunker(chunk_size=10, overlap=2)
        metadata = {"source": "doc.md", "tags": ["test", "example"]}
        text = "This is test content"
        chunks = chunker.chunk_text(text, metadata)
        
        assert len(chunks) == 1
        assert chunks[0]["metadata"]["source"] == "doc.md"
        assert chunks[0]["metadata"]["tags"] == ["test", "example"]


class TestStubEmbeddingClient:
    """Tests for StubEmbeddingClient."""

    async def test_embed_single_text(self) -> None:
        client = StubEmbeddingClient(dimension=128)
        embeddings = await client.embed_texts(["test text"])
        
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 128
        # Check normalization (unit vector)
        magnitude = sum(x * x for x in embeddings[0]) ** 0.5
        assert abs(magnitude - 1.0) < 1e-6

    async def test_embed_multiple_texts(self) -> None:
        client = StubEmbeddingClient(dimension=64)
        texts = ["text one", "text two", "text three"]
        embeddings = await client.embed_texts(texts)
        
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert len(embedding) == 64

    async def test_embed_deterministic(self) -> None:
        client = StubEmbeddingClient(dimension=32)
        text = "deterministic test"
        
        embeddings1 = await client.embed_texts([text])
        embeddings2 = await client.embed_texts([text])
        
        # Same text should produce same embedding
        assert embeddings1[0] == embeddings2[0]

    async def test_embed_different_texts_different_embeddings(self) -> None:
        client = StubEmbeddingClient(dimension=32)
        embeddings = await client.embed_texts(["text one", "text two"])
        
        # Different texts should produce different embeddings
        assert embeddings[0] != embeddings[1]


class TestVectorStore:
    """Tests for VectorStore."""

    def test_create_and_count_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            assert store.count() == 0

    def test_add_and_count_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            
            contents = ["doc1", "doc2", "doc3"]
            metadatas = [{"id": i} for i in range(3)]
            embeddings = [[0.1, 0.2, 0.3] for _ in range(3)]
            
            store.add_documents(contents, metadatas, embeddings)
            assert store.count() == 3

    def test_search_returns_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            
            # Add documents with normalized embeddings
            contents = ["document one", "document two", "document three"]
            metadatas = [{"id": i} for i in range(3)]
            embeddings = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
            
            store.add_documents(contents, metadatas, embeddings)
            
            # Search with query similar to first document
            query_embedding = [0.9, 0.1, 0.0]
            results = store.search(query_embedding, top_k=2, min_score=0.0)
            
            assert len(results) <= 2
            assert all(isinstance(r, RetrievedDocument) for r in results)
            
            # First result should be most similar
            if results:
                assert results[0].content == "document one"
                assert 0.0 <= results[0].score <= 1.0

    def test_search_respects_top_k(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            
            # Add 5 documents
            contents = [f"doc {i}" for i in range(5)]
            metadatas = [{"id": i} for i in range(5)]
            embeddings = [[float(i % 3), float(i % 2), 1.0] for i in range(5)]
            
            store.add_documents(contents, metadatas, embeddings)
            
            # Search with top_k=3
            query_embedding = [1.0, 1.0, 1.0]
            results = store.search(query_embedding, top_k=3, min_score=0.0)
            
            assert len(results) <= 3

    def test_search_respects_min_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            
            # Add documents
            contents = ["doc1", "doc2"]
            metadatas = [{"id": i} for i in range(2)]
            embeddings = [[1.0, 0.0], [0.0, 1.0]]
            
            store.add_documents(contents, metadatas, embeddings)
            
            # Search with high min_score
            query_embedding = [1.0, 0.0]
            results = store.search(query_embedding, top_k=10, min_score=0.9)
            
            # Only highly similar documents should be returned
            assert all(r.score >= 0.9 for r in results)

    def test_clear_removes_all_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            
            contents = ["doc1", "doc2"]
            metadatas = [{"id": i} for i in range(2)]
            embeddings = [[0.1, 0.2] for _ in range(2)]
            
            store.add_documents(contents, metadatas, embeddings)
            assert store.count() == 2
            
            store.clear()
            assert store.count() == 0

    def test_cosine_similarity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            store = VectorStore(db_path)
            
            # Test identical vectors
            sim = store._cosine_similarity([1.0, 0.0], [1.0, 0.0])
            assert abs(sim - 1.0) < 1e-6
            
            # Test orthogonal vectors
            sim = store._cosine_similarity([1.0, 0.0], [0.0, 1.0])
            assert abs(sim - 0.0) < 1e-6
            
            # Test opposite vectors
            sim = store._cosine_similarity([1.0, 0.0], [-1.0, 0.0])
            assert sim == 0.0  # Clamped to [0, 1]


class TestRAGRetriever:
    """Tests for RAGRetriever."""

    async def test_retrieve_with_stub_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            vector_store = VectorStore(db_path)
            embedding_client = StubEmbeddingClient(dimension=128)
            
            # Add documents
            texts = [
                "The Echoes of Emergence is a simulation game",
                "Agents navigate districts and manage resources",
                "Factions compete for control and influence",
            ]
            embeddings = await embedding_client.embed_texts(texts)
            metadatas = [{"source": f"doc{i}.md"} for i in range(len(texts))]
            
            vector_store.add_documents(texts, metadatas, embeddings)
            
            # Create retriever
            retriever = RAGRetriever(vector_store, embedding_client)
            
            # Retrieve documents
            results = await retriever.retrieve("simulation game", top_k=2, min_score=0.0)
            
            assert len(results) <= 2
            assert all(isinstance(r, RetrievedDocument) for r in results)

    async def test_retrieve_returns_sorted_by_relevance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            vector_store = VectorStore(db_path)
            embedding_client = StubEmbeddingClient(dimension=128)
            
            # Add documents
            texts = ["apple", "banana", "cherry"]
            embeddings = await embedding_client.embed_texts(texts)
            metadatas = [{"id": i} for i in range(len(texts))]
            
            vector_store.add_documents(texts, metadatas, embeddings)
            
            # Create retriever
            retriever = RAGRetriever(vector_store, embedding_client)
            
            # Retrieve with exact match query
            results = await retriever.retrieve("apple", top_k=3, min_score=0.0)
            
            # Results should be sorted by score (descending)
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i].score >= results[i + 1].score


class TestFormatRetrievedContext:
    """Tests for format_retrieved_context function."""

    def test_format_empty_documents(self) -> None:
        result = format_retrieved_context([])
        assert result == ""

    def test_format_single_document(self) -> None:
        doc = RetrievedDocument(
            content="Test content",
            metadata={"source": "test.md"},
            score=0.95,
        )
        result = format_retrieved_context([doc])
        
        assert "## Retrieved Context" in result
        assert "Test content" in result
        assert "0.95" in result
        assert "test.md" in result

    def test_format_multiple_documents(self) -> None:
        docs = [
            RetrievedDocument(
                content="First document",
                metadata={"source": "doc1.md"},
                score=0.9,
            ),
            RetrievedDocument(
                content="Second document",
                metadata={"source": "doc2.md"},
                score=0.8,
            ),
        ]
        result = format_retrieved_context(docs)
        
        assert "First document" in result
        assert "Second document" in result
        assert "doc1.md" in result
        assert "doc2.md" in result

    def test_format_without_citations(self) -> None:
        doc = RetrievedDocument(
            content="Test content",
            metadata={"source": "test.md"},
            score=0.95,
        )
        result = format_retrieved_context([doc], include_citations=False)
        
        assert "Test content" in result
        assert "test.md" not in result
