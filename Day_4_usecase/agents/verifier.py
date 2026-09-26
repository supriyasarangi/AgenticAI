"""
Verifier — checks groundedness of claims against cited chunks using Opus 5.

Re-reads each claim against only its cited chunks (scoped cached system block).
Feeds verification result into confidence scorer.
"""

import json
import logging
from typing import List, Dict, Any

from orchestration.anthropic_client import (
    call_with_task_config,
    build_cached_system_blocks,
)
from agents.confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)


def verify_claims(
    claims: List[Dict[str, Any]],
    chunks_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Verify each claim for groundedness using Opus 5.

    For each claim:
    - Scopes system block to only its cited chunks
    - Calls Opus 5 for groundedness check
    - Runs confidence scorer
    - Attaches confidence tier and rationale

    Args:
        claims: List of claims with sentence, cited_chunk_ids
        chunks_by_id: Dict mapping chunk_id to chunk data

    Returns:
        List of verified claims with confidence tiers
    """
    if not claims:
        return []

    verified_claims = []
    scorer = ConfidenceScorer()

    for i, claim in enumerate(claims):
        sentence = claim.get("sentence", "")
        cited_ids = claim.get("cited_chunk_ids", [])

        if not sentence or not cited_ids:
            logger.warning(f"Skipping invalid claim: {claim}")
            continue

        # Build scoped evidence for this claim only
        cited_chunks = [chunks_by_id.get(cid, {}) for cid in cited_ids]
        evidence_text = _build_scoped_evidence(cited_chunks)

        try:
            # Build cached system block scoped to this claim's evidence
            system_prompt = f"""You are a medical evidence verification expert.
Your task is to assess whether the claim is well-grounded in the provided evidence.

Evidence (ONLY chunks supporting this claim):
{evidence_text}

Provide JSON: {{"grounded": true/false, "llm_consistency_score": 0.0-1.0, "explanation": "..."}}

Only rate 'true' if the claim is well-supported by the evidence."""

            system = build_cached_system_blocks(system_prompt)

            messages = [
                {
                    "role": "user",
                    "content": f"Verify this claim: {sentence}",
                }
            ]

            response = call_with_task_config(
                "verifier",
                system,
                messages,
            )

            # Parse verification result
            response_text = response.content[0].text

            # Strip markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].lstrip()
                response_text = response_text.rstrip()

            try:
                verification = json.loads(response_text)
                grounded = verification.get("grounded", False)
                llm_score = verification.get("llm_consistency_score", 0.5)
                explanation = verification.get("explanation", "")
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse verifier JSON: {response_text[:100]}..."
                )
                grounded = False
                llm_score = 0.5
                explanation = "Verification parsing failed"

            # Run confidence scorer
            # Get first cited chunk for metadata
            first_chunk = chunks_by_id.get(cited_ids[0], {})
            source_authority = first_chunk.get("metadata", {}).get(
                "source_authority_tier", 0.75
            )
            pub_date = first_chunk.get("metadata", {}).get("pub_date", None)

            confidence_score = scorer.score_claim(
                claim_id=f"claim_{i}",
                retrieval_similarity=first_chunk.get("similarity_score", 0.7),
                source_authority_tier=source_authority,
                corroboration_count=len(cited_ids),  # Use num cited chunks as proxy
                publication_date=pub_date,
                llm_consistency_check=llm_score,
                cited_chunk_ids=cited_ids,
            )

            verified_claims.append({
                "sentence": sentence,
                "cited_chunk_ids": cited_ids,
                "grounded": grounded,
                "llm_consistency_check": llm_score,
                "confidence_tier": confidence_score.tier,
                "confidence_rationale": confidence_score.rationale,
                "verification_explanation": explanation,
            })

        except Exception as e:
            logger.error(f"Verification failed for claim '{sentence[:50]}...': {e}")
            # Still include claim but mark as unverified
            verified_claims.append({
                "sentence": sentence,
                "cited_chunk_ids": cited_ids,
                "grounded": False,
                "llm_consistency_check": 0.0,
                "confidence_tier": "Unverified",
                "confidence_rationale": f"Verification failed: {str(e)}",
            })

    logger.info(f"Verified {len(verified_claims)} claims")
    return verified_claims


def _build_scoped_evidence(chunks: List[Dict[str, Any]]) -> str:
    """
    Build evidence text scoped to specific chunks for claim verification.

    Args:
        chunks: List of chunks supporting a single claim

    Returns:
        Formatted evidence string
    """
    evidence_lines = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        text = chunk.get("text", "")
        evidence_lines.append(f"[{chunk_id}] {text}")

    return "\n\n".join(evidence_lines)
