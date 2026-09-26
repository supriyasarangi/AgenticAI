"""
Document chunking — splits long documents into overlapping chunks for RAG.

Produces chunks matching orchestration.state.Chunk field names.
"""

import logging
from typing import List, Dict, Any
import uuid

logger = logging.getLogger(__name__)


def chunk_document(
    text: str,
    doc_id: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split a document into overlapping chunks.

    Args:
        text: Full document text
        doc_id: Document identifier (e.g., PMID)
        chunk_size: Target chunk size in characters (default 500)
        overlap: Overlap between chunks in characters (default 50)

    Returns:
        List of chunk dicts with chunk_id, text, char_span_start, char_span_end
    """
    chunks = []

    if not text or len(text) == 0:
        logger.warning(f"Empty text for doc_id {doc_id}")
        return chunks

    # Calculate step size (how much to advance each iteration)
    step = chunk_size - overlap

    # Generate chunks with overlapping spans
    for start_idx in range(0, len(text), step):
        end_idx = min(start_idx + chunk_size, len(text))

        chunk_text = text[start_idx:end_idx]

        # Only include non-empty chunks
        if chunk_text.strip():
            chunk_id = str(uuid.uuid4())
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "char_span_start": start_idx,
                "char_span_end": end_idx,
            })

        # Stop if we've reached the end
        if end_idx >= len(text):
            break

    logger.info(f"Split doc {doc_id} into {len(chunks)} chunks")
    return chunks
