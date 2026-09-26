"""
LangGraph state graph definition for agentic RAG pipeline.

Implements 8-stage pipeline:
1. Query Planner
2. Literature Retriever
3. Clinical Trials Retriever
4. Regulatory Retriever
5. Evidence Ranker
6. Synthesizer
7. Verifier
8. Response Composer

Phase 0: stubs. Phase 1+: real LLM-backed nodes.
"""

import logging
from typing import Any

from langgraph.graph import StateGraph, START, END
from .state import RAGState
from .logging_config import setup_logging
from agents.query_planner import plan_query
from agents.literature_retriever import retrieve_literature
from agents.confidence_scorer import ConfidenceScorer
from agents.synthesizer import synthesizer as synthesize_claims
from agents.verifier import verify_claims
from agents.response_composer import compose_response

logger = logging.getLogger(__name__)


# ============================================================================
# Pipeline Node Stubs (Phase 0: pass state through unchanged)
# ============================================================================


def query_planner(state: RAGState) -> RAGState:
    """
    Query Planner (Sonnet 5).

    Decomposes the query into 1–3 retrieval sub-queries.
    """
    logger.info(f"Query Planner processing: {state.query}")
    state.status = "query_planning"

    try:
        sub_queries = plan_query(
            state.query,
            state.therapeutic_area or "oncology",
            state.jurisdiction or "GLOBAL",
        )
        state.retrieval_plan = {"sub_queries": sub_queries}
    except Exception as e:
        logger.error(f"Query planner failed: {e}")
        state.retrieval_plan = {"sub_queries": [state.query]}

    return state


def literature_retriever(state: RAGState) -> RAGState:
    """
    Literature Retriever.

    Queries PubMed/PMC vector store with domain-filtered metadata.
    """
    logger.info(f"Literature Retriever processing: {state.query}")

    try:
        sub_queries = state.retrieval_plan.get("sub_queries", [state.query])
        chunks = retrieve_literature(
            sub_queries,
            state.therapeutic_area or "oncology",
            state.jurisdiction or "GLOBAL",
            top_k=5,
        )
        state.retrieved_chunks.extend(chunks)
    except Exception as e:
        logger.error(f"Literature retrieval failed: {e}")

    return state


def clinical_trials_retriever(state: RAGState) -> RAGState:
    """
    Clinical Trials Retriever (parallel fan-out).

    Queries ClinicalTrials.gov index with domain-filtered metadata.
    Stub: passes state through.
    """
    logger.info(f"Clinical Trials Retriever processing: {state.query}")
    return state


def regulatory_retriever(state: RAGState) -> RAGState:
    """
    Regulatory Retriever (parallel fan-out).

    Queries FDA/EMA/ICH/PMDA/MHRA indices with jurisdiction filtering.
    Stub: passes state through.
    """
    logger.info(f"Regulatory Retriever processing: {state.query}")
    return state


def evidence_ranker(state: RAGState) -> RAGState:
    """
    Evidence Ranker / Filter.

    Sorts by similarity score and takes top 10.
    """
    logger.info(f"Evidence Ranker processing {len(state.retrieved_chunks)} chunks")
    state.status = "ranking"

    # Sort by similarity score (descending) and take top 10
    ranked = sorted(
        state.retrieved_chunks,
        key=lambda x: x.get("similarity_score", 0.0),
        reverse=True,
    )[:10]
    state.ranked_evidence = ranked

    logger.info(f"Ranked to {len(state.ranked_evidence)} chunks")
    return state


def synthesizer(state: RAGState) -> RAGState:
    """
    Synthesizer (Sonnet 5).

    Produces answer as claim-tagged sentences with structured output
    forcing citation of chunk_ids.
    """
    logger.info("Synthesizer processing ranked evidence")
    state.status = "synthesis"

    try:
        claims = synthesize_claims(state.query, state.ranked_evidence)
        state.synthesized_claims = claims
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        state.synthesized_claims = []

    return state


def verifier(state: RAGState) -> RAGState:
    """
    Verifier (Opus 5).

    Rereads each claim against cited chunks and checks groundedness.
    """
    logger.info("Verifier checking synthesized claims")
    state.status = "verification"

    try:
        # Build chunks_by_id dict for verifier
        chunks_by_id = {c.get("chunk_id"): c for c in state.ranked_evidence}
        verified = verify_claims(state.synthesized_claims, chunks_by_id)
        state.verification_results = {"verified_claims": verified}
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        state.verification_results = {}

    return state


def response_composer(state: RAGState) -> RAGState:
    """
    Response Composer (pure Python).

    Assembles final answer with inline citations and confidence panel.
    """
    logger.info("Response Composer assembling final answer")
    state.status = "completed"

    try:
        chunks_by_id = {c.get("chunk_id"): c for c in state.ranked_evidence}
        # Extract verified claims from verification_results dict
        verified_claims = []
        if isinstance(state.verification_results, dict):
            verified_claims = state.verification_results.get("verified_claims", [])
        elif isinstance(state.verification_results, list):
            verified_claims = state.verification_results
        # Fall back to synthesized claims if no verification happened
        if not verified_claims:
            verified_claims = state.synthesized_claims
        result = compose_response(
            state.query,
            verified_claims,
            chunks_by_id,
        )
        state.final_answer = result.get("final_answer", "")
        state.response_citations = result.get("citations", [])
    except Exception as e:
        logger.error(f"Response composition failed: {e}")
        state.final_answer = ""
        state.response_citations = []

    return state


# ============================================================================
# Graph Construction
# ============================================================================


def build_graph() -> StateGraph:
    """
    Construct the LangGraph StateGraph for Phase 0.

    Returns a graph with all 8 nodes in sequence (linear for Phase 0,
    retry logic added in Phase 4).
    """
    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("query_planner", query_planner)
    graph.add_node("literature_retriever", literature_retriever)
    graph.add_node("clinical_trials_retriever", clinical_trials_retriever)
    graph.add_node("regulatory_retriever", regulatory_retriever)
    graph.add_node("evidence_ranker", evidence_ranker)
    graph.add_node("synthesizer", synthesizer)
    graph.add_node("verifier", verifier)
    graph.add_node("response_composer", response_composer)

    # Add edges (linear for Phase 0)
    graph.add_edge(START, "query_planner")
    graph.add_edge("query_planner", "literature_retriever")
    graph.add_edge("literature_retriever", "clinical_trials_retriever")
    graph.add_edge("clinical_trials_retriever", "regulatory_retriever")
    graph.add_edge("regulatory_retriever", "evidence_ranker")
    graph.add_edge("evidence_ranker", "synthesizer")
    graph.add_edge("synthesizer", "verifier")
    graph.add_edge("verifier", "response_composer")
    graph.add_edge("response_composer", END)

    return graph


def create_app():
    """
    Compile the graph into a runnable application.

    Returns a compiled LangGraph app ready for invoke() or stream().
    """
    graph = build_graph()
    app = graph.compile()
    return app


# ============================================================================
# Main entry point (for testing)
# ============================================================================


def run_query_pipeline(query: str, therapeutic_area: str, jurisdiction: str) -> dict:
    """
    Execute the RAG pipeline end-to-end.

    Frontend contract: called by ui/app.py with (query, therapeutic_area, jurisdiction).

    Args:
        query: User's natural-language question
        therapeutic_area: One of {oncology, cardiology, neurology, immunology, infectious_disease, rare_disease}
        jurisdiction: One of {FDA, EMA, ICH, PMDA, MHRA, GLOBAL}

    Returns:
        Dict with final_answer, claims, citations, evidence, trace, status

    Raises:
        ValueError: If domain selection is invalid
    """
    # Setup logging (guarded against Streamlit reruns)
    setup_logging()

    # Input validation (R1: domain selection required)
    if not therapeutic_area or not jurisdiction:
        raise ValueError(
            "Both therapeutic_area and jurisdiction are required (R1: domain-scoped query)."
        )

    # Create initial state
    initial_state = RAGState(
        query=query,
        therapeutic_area=therapeutic_area,
        jurisdiction=jurisdiction,
    )

    # Create and execute app
    app = create_app()

    try:
        # Stream events and collect final state
        final_state = None
        for event in app.stream(initial_state):
            # Extract the final state from the last event
            final_state = list(event.values())[-1] if event else final_state

        # CRITICAL BUG FIX: app.stream() yields dicts, not RAGState objects
        # Normalize to RAGState before attribute access
        if final_state is not None and isinstance(final_state, dict):
            final_state = RAGState.model_validate(final_state)

        # Convert state to response dict
        response = {
            "query": final_state.query if final_state else query,
            "therapeutic_area": therapeutic_area,
            "jurisdiction": jurisdiction,
            "final_answer": final_state.final_answer if final_state else "",
            "claims": final_state.synthesized_claims if final_state else [],
            "citations": final_state.response_citations if final_state else [],
            "evidence": final_state.retrieved_chunks if final_state else [],
            "trace": [],  # Trace will be populated in later phases
            "status": final_state.status if final_state else "failed",
            "error_log": final_state.error_log if final_state else [],
        }

        return response

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return {
            "query": query,
            "therapeutic_area": therapeutic_area,
            "jurisdiction": jurisdiction,
            "status": "failed",
            "error_log": [str(e)],
            "final_answer": None,
            "claims": [],
            "citations": [],
            "evidence": [],
            "trace": [],
        }


def main():
    """
    Test harness: run the pipeline end-to-end with dummy state.

    Exit criterion for Phase 0: all 8 nodes execute without error.
    """
    # Create app
    app = create_app()

    # Create dummy state
    initial_state = RAGState(
        query="What are the latest therapies for metastatic melanoma?",
        therapeutic_area="oncology",
        jurisdiction="FDA",
    )

    logger.info("Starting RAG pipeline with dummy state...")
    logger.info(f"Query: {initial_state.query}")
    logger.info(f"Domain: {initial_state.therapeutic_area} / {initial_state.jurisdiction}")

    # Run the pipeline
    try:
        # Stream events for visibility
        for event in app.stream(initial_state):
            for node_name, node_output in event.items():
                logger.info(f"Node: {node_name}, Status: {node_output.get('status', 'N/A')}")

        logger.info("Pipeline completed successfully!")
        print("\n✓ All 8 pipeline nodes executed successfully")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n✗ Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
