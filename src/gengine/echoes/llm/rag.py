"""Retrieval-Augmented Generation (RAG) implementation for LLM service."""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """A document retrieved from the knowledge base.

    Attributes
    ----------
    content
        The document text content
    metadata
        Document metadata (source, tags, etc.)
    score
        Relevance score (0.0-1.0, higher is more relevant)
    """

    content: str
    metadata: dict[str, Any]
    score: float


class DocumentChunker:
    """Splits documents into semantic chunks with overlap."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        """Initialize chunker.

        Parameters
        ----------
        chunk_size
            Target size of each chunk in tokens (approximate)
        overlap
            Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Split text into overlapping chunks.

        Parameters
        ----------
        text
            Input text to chunk
        metadata
            Optional metadata to attach to each chunk

        Returns
        -------
        list[dict[str, Any]]
            List of chunks with content and metadata
        """
        if not text:
            return []

        # Simple token approximation: split on whitespace
        words = text.split()
        chunks = []
        
        if not words:
            return []

        # Create overlapping chunks
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = len(chunks)
            chunk_metadata["start_word"] = i
            chunk_metadata["end_word"] = i + len(chunk_words)
            
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_metadata,
            })
            
            # Move to next chunk with overlap
            i += self.chunk_size - self.overlap
            
            # Avoid tiny trailing chunks
            if i < len(words) and len(words) - i < self.overlap:
                break

        return chunks


class VectorStore:
    """Simple vector store using SQLite for persistence.

    Uses cosine similarity for relevance scoring. In production, consider
    using specialized vector databases like Chroma, FAISS, or pgvector.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize vector store.

        Parameters
        ----------
        db_path
            Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    embedding TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_metadata 
                ON documents(metadata)
            """)

    def add_documents(
        self,
        contents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """Add documents with embeddings to the store.

        Parameters
        ----------
        contents
            Document text contents
        metadatas
            Document metadata dicts
        embeddings
            Document embedding vectors
        """
        if not (len(contents) == len(metadatas) == len(embeddings)):
            raise ValueError(
                "Contents, metadatas, and embeddings must have same length"
            )

        with sqlite3.connect(self.db_path) as conn:
            for content, metadata, embedding in zip(
                contents, metadatas, embeddings, strict=False
            ):
                conn.execute(
                    "INSERT INTO documents (content, metadata, embedding) "
                    "VALUES (?, ?, ?)",
                    (content, json.dumps(metadata), json.dumps(embedding)),
                )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievedDocument]:
        """Search for documents similar to query embedding.

        Parameters
        ----------
        query_embedding
            Query embedding vector
        top_k
            Number of top results to return
        min_score
            Minimum relevance score threshold

        Returns
        -------
        list[RetrievedDocument]
            Retrieved documents with relevance scores
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT content, metadata, embedding FROM documents"
            )
            
            results = []
            for row in cursor:
                content, metadata_json, embedding_json = row
                metadata = json.loads(metadata_json)
                embedding = json.loads(embedding_json)
                
                # Compute cosine similarity
                score = self._cosine_similarity(query_embedding, embedding)
                
                if score >= min_score:
                    results.append(RetrievedDocument(
                        content=content,
                        metadata=metadata,
                        score=score,
                    ))
            
            # Sort by score descending and take top_k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors.

        Parameters
        ----------
        a
            First vector
        b
            Second vector

        Returns
        -------
        float
            Cosine similarity (0.0-1.0)
        """
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5

        if magnitude_a == 0.0 or magnitude_b == 0.0:
            return 0.0

        return max(0.0, min(1.0, dot_product / (magnitude_a * magnitude_b)))

    def clear(self) -> None:
        """Remove all documents from the store."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM documents")

    def count(self) -> int:
        """Return the number of documents in the store."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            return cursor.fetchone()[0]


class EmbeddingClient:
    """Abstract client for generating text embeddings."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Parameters
        ----------
        texts
            List of text strings to embed

        Returns
        -------
        list[list[float]]
            List of embedding vectors
        """
        raise NotImplementedError


class StubEmbeddingClient(EmbeddingClient):
    """Stub embedding client for testing and development."""

    def __init__(self, dimension: int = 128) -> None:
        """Initialize stub client.

        Parameters
        ----------
        dimension
            Embedding vector dimension
        """
        self.dimension = dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate stub embeddings based on text hash.

        Parameters
        ----------
        texts
            List of text strings to embed

        Returns
        -------
        list[list[float]]
            List of stub embedding vectors
        """
        embeddings = []
        for text in texts:
            # Generate deterministic pseudo-embedding from text hash
            text_hash = hash(text)
            embedding = [
                float((text_hash + i * 31) % 1000) / 1000.0
                for i in range(self.dimension)
            ]
            # Normalize
            magnitude = sum(x * x for x in embedding) ** 0.5
            if magnitude > 0:
                embedding = [x / magnitude for x in embedding]
            embeddings.append(embedding)
        return embeddings


class RAGRetriever:
    """Retriever that combines vector store and embedding client."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_client: EmbeddingClient,
    ) -> None:
        """Initialize retriever.

        Parameters
        ----------
        vector_store
            Vector store for document storage and search
        embedding_client
            Client for generating embeddings
        """
        self.vector_store = vector_store
        self.embedding_client = embedding_client

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievedDocument]:
        """Retrieve relevant documents for a query.

        Parameters
        ----------
        query
            Query text
        top_k
            Number of top results to return
        min_score
            Minimum relevance score threshold

        Returns
        -------
        list[RetrievedDocument]
            Retrieved documents with relevance scores
        """
        # Generate query embedding
        query_embeddings = await self.embedding_client.embed_texts([query])
        query_embedding = query_embeddings[0]

        # Search vector store
        return self.vector_store.search(query_embedding, top_k, min_score)


def format_retrieved_context(
    documents: list[RetrievedDocument],
    include_citations: bool = True,
) -> str:
    """Format retrieved documents as context string for LLM prompt.

    Parameters
    ----------
    documents
        Retrieved documents to format
    include_citations
        Whether to include source citations

    Returns
    -------
    str
        Formatted context string
    """
    if not documents:
        return ""

    context_parts = ["## Retrieved Context\n"]
    
    for i, doc in enumerate(documents, 1):
        context_parts.append(f"### Context {i} (relevance: {doc.score:.2f})")
        context_parts.append(doc.content)
        
        if include_citations and doc.metadata:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"*Source: {source}*")
        
        context_parts.append("")  # Empty line between docs

    return "\n".join(context_parts)
