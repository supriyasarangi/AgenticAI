"""
Embeddings generation — lazy-loaded sentence-transformers model.

Uses all-MiniLM-L6-v2 (384-dim, small/fast POC model).
"""

import logging
from typing import List, Optional

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model instance (lazy-loaded)
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Get or load the embedding model (lazy singleton).

    Args:
        model_name: HuggingFace model identifier (default all-MiniLM-L6-v2)

    Returns:
        Loaded SentenceTransformer instance
    """
    global _embedding_model

    if _embedding_model is None:
        logger.info(f"Loading embedding model: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded (dim={_embedding_model.get_sentence_embedding_dimension()})")

    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of text strings.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (384-dim)
    """
    if not texts:
        return []

    model = get_embedding_model()
    logger.info(f"Embedding {len(texts)} texts")
    embeddings = model.encode(texts, convert_to_tensor=False)

    # Convert numpy arrays to lists
    return [embedding.tolist() for embedding in embeddings]


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string.

    Args:
        text: Text string to embed

    Returns:
        Single embedding vector (384-dim)
    """
    embeddings = embed_texts([text])
    return embeddings[0] if embeddings else []
