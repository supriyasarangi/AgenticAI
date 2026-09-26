"""
Synthesizer — generates claims with citations using Claude Sonnet 5.

Uses cached system blocks (stable evidence + instructions)
Forcing structured output with required cited_chunk_ids for each claim.
"""

import json
import logging
from typing import List, Dict, Any

from orchestration.anthropic_client import (
    call_with_task_config,
    build_cached_system_blocks,
)

logger = logging.getLogger(__name__)


def synthesizer(
    query: str,
    ranked_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Synthesize claims from ranked evidence using Sonnet 5.

    Args:
        query: User's original query
        ranked_chunks: List of chunks with chunk_id, text, similarity_score

    Returns:
        List of claims with structure: {sentence, cited_chunk_ids}
    """
    if not ranked_chunks:
        logger.warning("No ranked chunks provided to synthesizer")
        return []

    try:
        # Build evidence bundle (stable prefix for caching)
        evidence_bundle = _build_evidence_bundle(ranked_chunks)

        # Build cached system blocks
        system_prompt = f"""You are a medical research synthesis expert.
Your task is to synthesize a comprehensive answer from the provided evidence.

For each claim:
- Write a clear, factual sentence
- Cite ONLY chunks that support this claim (by chunk_id)
- Do NOT cite chunks not provided
- Each claim MUST cite at least one chunk

Return JSON with array of claims: [{{"sentence": "...", "cited_chunk_ids": ["chunk_id1", "chunk_id2"]}}]

Evidence Bundle:
{evidence_bundle}"""

        system = build_cached_system_blocks(system_prompt)

        messages = [
            {
                "role": "user",
                "content": f"Synthesize claims for this query: {query}",
            }
        ]

        response = call_with_task_config(
            "synthesizer",
            system,
            messages,
        )

        # Extract and parse response
        response_text = response.content[0].text

        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:].lstrip()
            response_text = response_text.rstrip()

        try:
            parsed = json.loads(response_text)
            claims = parsed if isinstance(parsed, list) else parsed.get("claims", [])
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse synthesizer JSON: {response_text[:100]}..."
            )
            claims = []

        # Validate citations (drop claims citing non-existent chunks)
        valid_chunk_ids = {c["chunk_id"] for c in ranked_chunks}
        validated_claims = []

        for claim in claims:
            if not isinstance(claim, dict):
                continue

            sentence = claim.get("sentence", "")
            cited_ids = claim.get("cited_chunk_ids", [])

            # Filter to only valid chunk_ids
            valid_cited_ids = [
                cid for cid in cited_ids if cid in valid_chunk_ids
            ]

            if valid_cited_ids:  # Only keep claims with valid citations
                validated_claims.append({
                    "sentence": sentence,
                    "cited_chunk_ids": valid_cited_ids,
                })
            else:
                logger.warning(
                    f"Dropping claim with invalid citations: {sentence[:50]}..."
                )

        logger.info(f"Synthesizer generated {len(validated_claims)} claims")
        return validated_claims

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return []


def _build_evidence_bundle(chunks: List[Dict[str, Any]]) -> str:
    """
    Build a serialized evidence bundle for the system prompt.

    Args:
        chunks: List of chunks with chunk_id, text, etc.

    Returns:
        Formatted evidence string
    """
    bundle_lines = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        text = chunk.get("text", "")
        similarity = chunk.get("similarity_score", 0.0)
        bundle_lines.append(
            f"[{chunk_id}] (similarity: {similarity:.3f}) {text[:200]}..."
        )

    return "\n".join(bundle_lines)
