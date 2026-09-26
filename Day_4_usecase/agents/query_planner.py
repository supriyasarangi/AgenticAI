"""
Query Planner — decomposes user queries into sub-queries using Claude.

Uses Sonnet 5 with structured output to decompose into 1-3 sub-queries.
"""

import json
import logging
from typing import List, Dict, Any

from orchestration.anthropic_client import call_with_task_config

logger = logging.getLogger(__name__)


def plan_query(
    query: str,
    therapeutic_area: str,
    jurisdiction: str,
) -> List[str]:
    """
    Decompose a query into sub-queries using Claude Sonnet 5.

    Args:
        query: User's natural-language question
        therapeutic_area: Therapeutic area for context
        jurisdiction: Jurisdiction for context

    Returns:
        List of 1-3 sub-queries for retrieval
    """
    system = [
        {
            "type": "text",
            "text": f"""You are a medical research query decomposition expert.
Your task is to decompose the user's query into 1-3 focused sub-queries for literature retrieval.

Context:
- Therapeutic Area: {therapeutic_area}
- Jurisdiction: {jurisdiction}

Guidelines:
- Each sub-query should be specific and retrievable from PubMed/literature
- Avoid redundancy between sub-queries
- Return JSON with a "sub_queries" array of strings""",
        }
    ]

    messages = [
        {
            "role": "user",
            "content": f"Decompose this query: {query}",
        }
    ]

    try:
        response = call_with_task_config(
            "query_planner",
            system,
            messages,
        )

        # Extract text from response
        response_text = response.content[0].text

        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:].lstrip()
            response_text = response_text.rstrip()

        # Try to parse JSON
        try:
            parsed = json.loads(response_text)
            sub_queries = parsed.get("sub_queries", [query])
        except json.JSONDecodeError:
            # Fallback: if JSON parsing fails, just use original query
            logger.warning(
                f"Failed to parse query planner JSON: {response_text[:100]}..."
            )
            sub_queries = [query]

        logger.info(f"Query planner decomposed into {len(sub_queries)} sub-queries")
        return sub_queries

    except Exception as e:
        logger.error(f"Query planner failed: {e}")
        # Degrade gracefully: return original query
        return [query]
