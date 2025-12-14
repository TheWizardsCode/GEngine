#!/usr/bin/env python3
"""Build knowledge base for LLM RAG from project documentation.

This script ingests documents from configured sources (docs/, content/, README),
chunks them into semantic units, generates embeddings, and stores them in a
local vector database for retrieval-augmented generation.

Usage:
    uv run scripts/build_llm_knowledge_base.py [--provider PROVIDER] [--clean]
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gengine.echoes.llm.rag import (
    DocumentChunker,
    StubEmbeddingClient,
    VectorStore,
)
from gengine.echoes.llm.settings import LLMSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_INPUT_GLOBS = [
    "docs/gengine/**/*.md",
    "content/worlds/**/*.yml",
    "content/worlds/**/*.yaml",
    "README.md",
]


def load_document(path: Path) -> tuple[str, dict[str, Any]]:
    """Load a single document and extract metadata.

    Parameters
    ----------
    path
        Path to document file

    Returns
    -------
    tuple[str, dict[str, Any]]
        Document content and metadata
    """
    try:
        content = path.read_text(encoding="utf-8")
        metadata = {
            "source": str(path),
            "filename": path.name,
            "extension": path.suffix,
            "size": len(content),
        }
        return content, metadata
    except Exception as e:
        logger.warning(f"Failed to load {path}: {e}")
        return "", {}


def discover_documents(input_globs: list[str], base_path: Path) -> list[Path]:
    """Discover documents matching input globs.

    Parameters
    ----------
    input_globs
        List of glob patterns relative to base_path
    base_path
        Base directory for glob patterns

    Returns
    -------
    list[Path]
        List of discovered document paths
    """
    discovered = set()
    for pattern in input_globs:
        full_pattern = str(base_path / pattern)
        for path_str in glob.glob(full_pattern, recursive=True):
            path = Path(path_str)
            if path.is_file():
                discovered.add(path)
    
    return sorted(discovered)


async def build_knowledge_base(
    input_globs: list[str],
    output_path: str,
    provider: str,
    chunk_size: int,
    overlap: int,
    clean: bool,
) -> None:
    """Build knowledge base from input documents.

    Parameters
    ----------
    input_globs
        List of glob patterns for input documents
    output_path
        Path to output database file
    provider
        Provider to use for embeddings (stub, openai, foundry_local)
    chunk_size
        Target chunk size in tokens
    overlap
        Overlap between chunks in tokens
    clean
        Whether to clean existing database before building
    """
    # Discover documents
    base_path = Path(__file__).parent.parent
    logger.info(f"Discovering documents in {base_path}")
    documents = discover_documents(input_globs, base_path)
    logger.info(f"Found {len(documents)} documents")

    if not documents:
        logger.warning("No documents found. Exiting.")
        return

    # Initialize components
    chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)
    vector_store = VectorStore(output_path)

    # Clean if requested
    if clean:
        logger.info("Cleaning existing database")
        vector_store.clear()

    # Initialize embedding client based on provider
    if provider == "stub":
        logger.info("Using stub embedding client")
        embedding_client = StubEmbeddingClient(dimension=128)
    elif provider == "openai":
        logger.info("Using OpenAI embedding client")
        try:
            from gengine.echoes.llm.rag import OpenAIEmbeddingClient
            settings = LLMSettings.from_env()
            if not settings.api_key:
                raise ValueError("ECHOES_LLM_API_KEY required for OpenAI provider")
            embedding_client = OpenAIEmbeddingClient(
                api_key=settings.api_key,
                model="text-embedding-3-small",
            )
        except ImportError:
            logger.error("OpenAI provider requires openai package")
            sys.exit(1)
    elif provider == "foundry_local":
        logger.info("Using Foundry Local embedding client")
        try:
            from gengine.echoes.llm.rag import FoundryLocalEmbeddingClient
            settings = LLMSettings.from_env()
            if not settings.base_url:
                raise ValueError(
                    "ECHOES_LLM_BASE_URL required for Foundry Local provider"
                )
            embedding_client = FoundryLocalEmbeddingClient(
                base_url=settings.base_url,
            )
        except ImportError:
            logger.error("Foundry Local provider not yet implemented, using stub")
            embedding_client = StubEmbeddingClient(dimension=128)
    else:
        logger.error(f"Unknown provider: {provider}")
        sys.exit(1)

    # Process documents
    all_chunks = []
    all_contents = []
    all_metadatas = []
    
    for doc_path in documents:
        logger.info(f"Processing {doc_path}")
        content, metadata = load_document(doc_path)
        
        if not content:
            continue
        
        # Chunk document
        chunks = chunker.chunk_text(content, metadata)
        logger.info(f"  Created {len(chunks)} chunks")
        
        all_chunks.extend(chunks)
        all_contents.extend([c["content"] for c in chunks])
        all_metadatas.extend([c["metadata"] for c in chunks])

    logger.info(f"Total chunks: {len(all_chunks)}")

    # Generate embeddings in batches
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(all_contents), batch_size):
        batch_contents = all_contents[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_contents) + batch_size - 1) // batch_size
        logger.info(f"Generating embeddings for batch {batch_num}/{total_batches}")
        batch_embeddings = await embedding_client.embed_texts(batch_contents)
        all_embeddings.extend(batch_embeddings)

    # Store in vector store
    logger.info(f"Storing {len(all_contents)} chunks in {output_path}")
    vector_store.add_documents(all_contents, all_metadatas, all_embeddings)

    # Summary
    total_docs = vector_store.count()
    logger.info("✓ Knowledge base built successfully")
    logger.info(f"  Total documents in store: {total_docs}")
    logger.info(f"  Database: {output_path}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build LLM knowledge base from project documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build with default settings (stub provider)
  uv run scripts/build_llm_knowledge_base.py

  # Clean and rebuild with OpenAI embeddings
  uv run scripts/build_llm_knowledge_base.py --provider openai --clean

  # Custom input sources
  uv run scripts/build_llm_knowledge_base.py --input-glob "docs/**/*.md" \\
      --input-glob "README.md"

  # Adjust chunk size
  uv run scripts/build_llm_knowledge_base.py --chunk-size 300 --overlap 30
        """,
    )
    
    parser.add_argument(
        "--input-glob",
        action="append",
        help="Glob pattern for input documents (can be specified multiple times)",
    )
    parser.add_argument(
        "--output",
        default="build/knowledge_base/index.db",
        help="Output database path (default: build/knowledge_base/index.db)",
    )
    parser.add_argument(
        "--provider",
        choices=["stub", "openai", "foundry_local"],
        default="stub",
        help="Embedding provider (default: stub)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Target chunk size in tokens (default: 500)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Overlap between chunks in tokens (default: 50)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean existing database before building",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_globs = args.input_glob or DEFAULT_INPUT_GLOBS

    asyncio.run(
        build_knowledge_base(
            input_globs=input_globs,
            output_path=args.output,
            provider=args.provider,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            clean=args.clean,
        )
    )


if __name__ == "__main__":
    main()
