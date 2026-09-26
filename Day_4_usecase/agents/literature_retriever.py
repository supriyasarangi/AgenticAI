"""
Literature Retriever — searches PubMed Chroma collection for relevant chunks.

Embeds sub-queries, searches with metadata filtering, dedups by chunk_id.
"""

import logging
from typing import List, Dict, Any

from ingestion.embeddings import embed_texts
from ingestion.vector_store import get_chroma_client, get_or_create_collection

logger = logging.getLogger(__name__)


def retrieve_literature(
    sub_queries: List[str],
    therapeutic_area: str,
    jurisdiction: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant literature chunks from PubMed collection.

    Args:
        sub_queries: List of retrieval sub-queries (from query planner)
        therapeutic_area: Therapeutic area for metadata filtering
        jurisdiction: Jurisdiction for metadata filtering
        top_k: Number of results per sub-query

    Returns:
        List of unique chunks with similarity scores, deduplicated by chunk_id
    """
    try:
        # Get Chroma collection
        client = get_chroma_client()
        collection = get_or_create_collection(client, "pubmed_literature")

        # Embed all sub-queries
        logger.info(f"Embedding {len(sub_queries)} sub-queries")
        query_embeddings = embed_texts(sub_queries)

        # Metadata filter
        where_filter = {
            "$and": [
                {"therapeutic_area": {"$eq": therapeutic_area}},
                {"jurisdiction": {"$eq": jurisdiction}},
            ]
        }

        # Search for each sub-query and collect results
        all_chunks = {}  # Use dict to dedup by chunk_id
        for i, query_embedding in enumerate(query_embeddings):
            logger.info(
                f"Retrieving {top_k} chunks for sub-query {i+1}/{len(sub_queries)}"
            )

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            # Process results
            if results["ids"] and len(results["ids"]) > 0:
                for j, chunk_id in enumerate(results["ids"][0]):
                    # Only add if not already present (prefer lower distance from first search)
                    if chunk_id not in all_chunks:
                        distance = results["distances"][0][j]
                        similarity_score = 1.0 - distance  # Convert distance to similarity

                        chunk_data = {
                            "chunk_id": chunk_id,
                            "text": results["documents"][0][j]
                            if results["documents"]
                            else "",
                            "metadata": results["metadatas"][0][j]
                            if results["metadatas"]
                            else {},
                            "similarity_score": similarity_score,
                        }
                        all_chunks[chunk_id] = chunk_data

        # Convert dict to sorted list (by similarity score, descending)
        chunks = sorted(
            all_chunks.values(),
            key=lambda x: x["similarity_score"],
            reverse=True,
        )

        logger.info(
            f"Retrieved {len(chunks)} unique chunks from literature (after dedup)"
        )
        return chunks

    except Exception as e:
        logger.error(f"Literature retrieval failed: {e}")
        return []
