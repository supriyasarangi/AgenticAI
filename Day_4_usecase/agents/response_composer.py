"""
Response Composer — assembles final answer with inline citations.

Matches ui/app.py's exact response shape:
- claims[].{sentence, confidence_tier, confidence_rationale}
- citations[].{number, chunk_id, source, doi_or_url, exact_span, confidence, rationale}
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def compose_response(
    query: str,
    verified_claims: List[Dict[str, Any]],
    chunks_by_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compose final answer response with inline citations.

    Args:
        query: Original user query (for reference)
        verified_claims: List of verified claims with confidence tiers
        chunks_by_id: Dict mapping chunk_id to chunk data

    Returns:
        Dict with final_answer, claims, citations (matching ui/app.py shape)
    """
    if not verified_claims:
        logger.warning("No verified claims to compose response")
        return {
            "final_answer": "",
            "claims": [],
            "citations": [],
        }

    # Build citations dict (chunk_id -> citation) first
    citations_list = []
    citation_number = 1
    chunk_id_to_citation_number = {}

    for chunk_id in set(
        cid for claim in verified_claims for cid in claim.get("cited_chunk_ids", [])
    ):
        chunk = chunks_by_id.get(chunk_id, {})
        metadata = chunk.get("metadata", {})

        citation = {
            "number": citation_number,
            "chunk_id": chunk_id,
            "source": metadata.get("source", "Unknown"),
            "doi_or_url": (
                metadata.get("doi")
                or metadata.get("pmid", "")
                and f"https://pubmed.ncbi.nlm.nih.gov/{metadata.get('pmid')}"
                or ""
            ),
            "exact_span": chunk.get("text", "")[:200],  # First 200 chars
            "confidence": "High",  # Placeholder
            "rationale": "Evidence from literature",
        }
        citations_list.append(citation)
        chunk_id_to_citation_number[chunk_id] = citation_number
        citation_number += 1

    # Build final answer with inline citations
    final_answer_parts = []
    claims_list = []

    for claim in verified_claims:
        sentence = claim.get("sentence", "")
        cited_ids = claim.get("cited_chunk_ids", [])
        confidence_tier = claim.get("confidence_tier", "Unverified")
        confidence_rationale = claim.get("confidence_rationale", "")

        # Add sentence with inline citation markers
        if cited_ids:
            citation_markers = [
                f"[{chunk_id_to_citation_number.get(cid, '?')}]"
                for cid in cited_ids
                if cid in chunk_id_to_citation_number
            ]
            sentence_with_citations = sentence + " " + " ".join(citation_markers)
        else:
            sentence_with_citations = sentence

        final_answer_parts.append(sentence_with_citations)

        # Build claims list entry
        claims_list.append({
            "sentence": sentence,
            "confidence_tier": confidence_tier,
            "confidence_rationale": confidence_rationale,
        })

    final_answer = " ".join(final_answer_parts)

    logger.info(
        f"Composed response with {len(claims_list)} claims and {len(citations_list)} citations"
    )

    return {
        "final_answer": final_answer,
        "claims": claims_list,
        "citations": citations_list,
    }
