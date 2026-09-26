"""
Persistent Chroma vector store client initialization and management.

Handles connection setup, collection creation, and metadata-filtered
similarity search for multi-source RAG retrieval.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


def get_chroma_client(persist_dir: Optional[str] = None) -> chromadb.Client:
    """
    Initialize and return a persistent Chroma client.

    Args:
        persist_dir: Directory for persistent storage. Defaults to data/chroma
                     from .env or local default.

    Returns:
        chromadb.Client configured for persistent operation.
    """
    if persist_dir is None:
        persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "data/chroma")

    # Create directory if it doesn't exist
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    # Initialize persistent client
    settings = Settings(
        is_persistent=True,
        persist_directory=persist_dir,
        anonymized_telemetry=False,
    )

    client = chromadb.Client(settings)
    logger.info(f"Initialized persistent Chroma client at {persist_dir}")

    return client


def get_or_create_collection(
    client: chromadb.Client,
    collection_name: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> chromadb.Collection:
    """
    Get or create a Chroma collection.

    Args:
        client: Chroma client instance
        collection_name: Name of the collection
        metadata: Optional metadata for the collection

    Returns:
        chromadb.Collection instance
    """
    if metadata is None:
        metadata = {}

    try:
        collection = client.get_collection(
            name=collection_name,
        )
        logger.info(f"Retrieved existing collection: {collection_name}")
    except Exception:
        collection = client.create_collection(
            name=collection_name,
            metadata=metadata,
            get_or_create=True,
        )
        logger.info(f"Created new collection: {collection_name}")

    return collection


def init_stub_collections(client: chromadb.Client) -> None:
    """
    Initialize stub collections for Phase 0 (no real data yet).

    Args:
        client: Chroma client instance
    """
    sources = [
        ("pubmed_literature", {"source": "PubMed/PMC", "source_type": "literature"}),
        ("clinical_trials", {"source": "ClinicalTrials.gov", "source_type": "clinical_trial"}),
        ("fda_regulatory", {"source": "FDA", "source_type": "regulatory", "jurisdiction": "FDA"}),
        ("ema_regulatory", {"source": "EMA", "source_type": "regulatory", "jurisdiction": "EMA"}),
        ("ich_regulatory", {"source": "ICH", "source_type": "regulatory", "jurisdiction": "ICH"}),
    ]

    for collection_name, metadata in sources:
        get_or_create_collection(client, collection_name, metadata)
        logger.info(f"Initialized stub collection: {collection_name}")


def search_similar_chunks(
    collection: chromadb.Collection,
    query_embedding: List[float],
    n_results: int = 10,
    where_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Search for similar chunks in collection with optional metadata filtering.

    Args:
        collection: Chroma collection to search
        query_embedding: Query embedding vector
        n_results: Number of results to return
        where_filter: Chroma where-filter dict for metadata filtering

    Returns:
        List of matching chunks with metadata and similarity scores.
    """
    try:
        results = collection.query(
            embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        # Reshape results into a more usable format
        chunks = []
        if results["ids"] and len(results["ids"]) > 0:
            for i, chunk_id in enumerate(results["ids"][0]):
                chunk_data = {
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                }
                chunks.append(chunk_data)

        return chunks

    except Exception as e:
        logger.error(f"Error querying collection: {e}")
        return []


def upsert_chunks(
    collection: chromadb.Collection,
    chunk_ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """
    Upsert (insert or update) chunks into collection.

    Args:
        collection: Chroma collection
        chunk_ids: List of chunk identifiers
        embeddings: List of embedding vectors
        documents: List of chunk text content
        metadatas: List of metadata dicts per chunk
    """
    try:
        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Upserted {len(chunk_ids)} chunks into collection")
    except Exception as e:
        logger.error(f"Error upserting chunks: {e}")
