"""
Streamlit Demo UI for Agentic RAG Drug-Discovery System

Phase 5 deliverable: domain-scoped query interface with cited answers,
agent-trace visibility, and evidence inspection.

Key features:
- Domain selection (therapeutic area + jurisdiction) — REQUIRED, no silent defaults
- Three tabs: Synthesized Answer | Agent Trace | Evidence Explorer
- Inline numbered citations with exact source spans
- Per-claim confidence tier badges with rationale
- Unverified claims always shown, never hidden
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Drug Discovery RAG Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# DOMAIN MODEL (from docs/domain-model.md)
# ============================================================================

THERAPEUTIC_AREAS = [
    "oncology",
    "cardiology",
    "neurology",
    "immunology",
    "infectious_disease",
    "rare_disease",
]

JURISDICTIONS = [
    "FDA",
    "EMA",
    "ICH",
    "PMDA",
    "MHRA",
    "GLOBAL",
]

CONFIDENCE_TIERS = {
    "High": "🟢",
    "Medium": "🟡",
    "Low": "🟠",
    "Unverified": "🔴",
}


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state."""
    if "therapeutic_area" not in st.session_state:
        st.session_state.therapeutic_area = None
    if "jurisdiction" not in st.session_state:
        st.session_state.jurisdiction = None
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "current_result" not in st.session_state:
        st.session_state.current_result = None
    if "agent_trace" not in st.session_state:
        st.session_state.agent_trace = []
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


init_session_state()


# ============================================================================
# SIDEBAR: DOMAIN SELECTION (R1 — REQUIRED)
# ============================================================================

def render_sidebar():
    """
    Render domain selection in sidebar.

    Per R1: Both therapeutic area and jurisdiction MUST be selected before
    query submission. No silent defaults.
    """
    st.sidebar.title("📋 Scope Configuration")
    st.sidebar.markdown("---")

    # Therapeutic Area Selector
    st.sidebar.subheader("Therapeutic Area")
    therapeutic_area = st.sidebar.selectbox(
        label="Select therapeutic area",
        options=[None] + THERAPEUTIC_AREAS,
        format_func=lambda x: "-- Select --" if x is None else x.replace("_", " ").title(),
        key="therapeutic_area_selector",
    )
    st.session_state.therapeutic_area = therapeutic_area

    # Jurisdiction Selector
    st.sidebar.subheader("Regulatory Jurisdiction")
    jurisdiction = st.sidebar.selectbox(
        label="Select jurisdiction",
        options=[None] + JURISDICTIONS,
        format_func=lambda x: "-- Select --" if x is None else x,
        key="jurisdiction_selector",
    )
    st.session_state.jurisdiction = jurisdiction

    st.sidebar.markdown("---")

    # Validation indicator
    is_valid = (
        st.session_state.therapeutic_area is not None
        and st.session_state.jurisdiction is not None
    )

    if is_valid:
        st.sidebar.success(
            f"✅ Scope: **{st.session_state.therapeutic_area.replace('_', ' ').title()}** / "
            f"**{st.session_state.jurisdiction}**"
        )
    else:
        st.sidebar.warning("⚠️ Select both therapeutic area and jurisdiction to proceed")

    return is_valid


# ============================================================================
# QUERY INPUT & SUBMISSION
# ============================================================================

def render_query_input(is_domain_valid: bool) -> Optional[str]:
    """
    Render query input form.

    Submit button is disabled if domain selection is incomplete (R1).
    """
    st.title("💊 Drug Discovery RAG Intelligence")

    # Show current scope at top
    if is_domain_valid:
        st.info(
            f"🔍 **Scoped to:** {st.session_state.therapeutic_area.replace('_', ' ').title()} / "
            f"{st.session_state.jurisdiction}"
        )

    st.markdown("---")

    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_area(
            label="Enter your question",
            placeholder="e.g., What is the FDA-approved dosage for X in oncology?",
            height=100,
            disabled=not is_domain_valid,
        )

    with col2:
        submit_button = st.button(
            "🔍 Submit Query",
            disabled=not is_domain_valid or not query.strip(),
            use_container_width=True,
        )

    if submit_button and is_domain_valid and query.strip():
        return query

    return None


# ============================================================================
# RESULT TABS: SYNTHESIZED ANSWER | AGENT TRACE | EVIDENCE EXPLORER
# ============================================================================

def render_citation_badge(citation: Dict[str, Any]) -> str:
    """Render an inline citation reference."""
    return f"[{citation['number']}]"


def render_synthesized_answer_tab(result: Dict[str, Any]):
    """
    Tab 1: Synthesized Answer with inline citations and confidence tiers.

    Per R3: Every sentence must cite exact source chunks with resolvable identifiers.
    Per R4: Every claim shows confidence tier (High/Medium/Low/Unverified) with rationale.
    Per R6: User can inspect raw evidence independently.
    """
    st.header("📄 Synthesized Answer")

    if not result:
        st.info("Run a query to see the synthesized answer.")
        return

    # Display scope
    st.caption(
        f"Scope: {result.get('therapeutic_area', 'N/A').replace('_', ' ').title()} / "
        f"{result.get('jurisdiction', 'N/A')}"
    )

    # Main answer text with inline citations
    if "final_answer" in result and result["final_answer"]:
        st.markdown("### Answer")
        answer_text = result["final_answer"]

        # Display answer with citation markers
        st.write(answer_text)

        # Per-claim confidence display
        if "claims" in result and result["claims"]:
            st.markdown("### Claim Confidence Breakdown")

            for claim in result["claims"]:
                col1, col2, col3 = st.columns([3, 1, 2])

                with col1:
                    st.write(f"**{claim.get('sentence', 'N/A')[:100]}...**")

                with col2:
                    confidence = claim.get("confidence_tier", "Unverified")
                    badge = CONFIDENCE_TIERS.get(confidence, "❓")
                    st.write(f"{badge} {confidence}")

                with col3:
                    rationale = claim.get("confidence_rationale", "N/A")
                    st.caption(rationale[:100])

    else:
        st.warning("No answer generated for this query.")

    # Citation reference list
    st.markdown("---")
    st.markdown("### 📚 Citation References")

    if "citations" in result and result["citations"]:
        for citation in result["citations"]:
            render_citation_entry(citation)
    else:
        st.info("No citations available.")


def render_citation_entry(citation: Dict[str, Any]):
    """
    Render a single citation entry with full provenance.

    Format: [#] Source | DOI/URL | "exact span" | Confidence: Tier (rationale)
    """
    num = citation.get("number", "?")
    source = citation.get("source", "Unknown")
    doi_or_url = citation.get("doi_or_url", "N/A")
    exact_span = citation.get("exact_span", "N/A")
    confidence = citation.get("confidence", "Unverified")
    rationale = citation.get("rationale", "N/A")

    st.markdown(
        f"""
        **[{num}]** {source}
        **Source:** {doi_or_url}
        **Quote:** *"{exact_span}"*
        **Confidence:** {CONFIDENCE_TIERS.get(confidence, '❓')} {confidence}
        **Rationale:** {rationale}
        """,
        unsafe_allow_html=False,
    )
    st.markdown("---")


def render_agent_trace_tab(trace: List[Dict[str, Any]]):
    """
    Tab 2: Agent Trace showing LangGraph node execution.

    For R&D audience: understand why an answer was produced.
    Shows: node name, timing, state changes.
    """
    st.header("🔄 Agent Pipeline Trace")

    if not trace or len(trace) == 0:
        st.info("Run a query to see the agent trace.")
        return

    st.markdown(
        "This trace shows the execution flow through the LangGraph pipeline. "
        "Each node updates the state as evidence is retrieved and synthesized."
    )

    st.markdown("---")

    for i, step in enumerate(trace, 1):
        # Node header
        node_name = step.get("node", "Unknown")
        status = step.get("status", "pending")
        duration = step.get("duration_ms", 0)

        status_icon = {
            "completed": "✅",
            "running": "⏳",
            "pending": "⏺️",
            "failed": "❌",
        }.get(status, "❓")

        with st.expander(
            f"{status_icon} **Step {i}: {node_name}** ({duration}ms)",
            expanded=(status == "running"),
        ):
            # State changes
            if "state_updates" in step:
                st.subheader("State Changes")
                for key, value in step["state_updates"].items():
                    if isinstance(value, (list, dict)):
                        st.json({key: value})
                    else:
                        st.write(f"**{key}:** {value}")

            # Errors
            if "error" in step and step["error"]:
                st.error(f"Error: {step['error']}")

            # Additional metadata
            if "metadata" in step:
                st.subheader("Metadata")
                st.json(step["metadata"])


def render_evidence_explorer_tab(evidence: List[Dict[str, Any]], citations: List[Dict[str, Any]]):
    """
    Tab 3: Evidence Explorer showing all retrieved chunks.

    Per R6: User inspects raw retrieved evidence independent of synthesized answer.
    Shows: source, similarity score, metadata, full text.
    Can filter by source type.
    """
    st.header("🔍 Evidence Explorer")

    if not evidence or len(evidence) == 0:
        st.info("No evidence retrieved for this query.")
        return

    st.markdown(
        "This view shows **all** retrieved evidence chunks, including those not cited in the answer. "
        "Filter to explore the raw data behind the synthesis."
    )

    # Citation tracking
    cited_ids = set()
    if citations:
        cited_ids = {c.get("chunk_id", "") for c in citations if "chunk_id" in c}

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_source = st.multiselect(
            "Filter by source type",
            options=list(set(e.get("source_type", "unknown") for e in evidence)),
            default=None,
        )

    with col2:
        filter_cited = st.radio(
            "Show",
            options=["All", "Cited only", "Uncited only"],
            horizontal=True,
        )

    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Similarity (high to low)", "Similarity (low to high)", "Recency"],
        )

    st.markdown("---")

    # Filter evidence
    filtered_evidence = evidence

    if filter_source:
        filtered_evidence = [e for e in filtered_evidence if e.get("source_type") in filter_source]

    if filter_cited == "Cited only":
        filtered_evidence = [e for e in filtered_evidence if e.get("chunk_id") in cited_ids]
    elif filter_cited == "Uncited only":
        filtered_evidence = [e for e in filtered_evidence if e.get("chunk_id") not in cited_ids]

    # Sort
    if "high to low" in sort_by:
        filtered_evidence = sorted(filtered_evidence, key=lambda e: e.get("similarity_score", 0), reverse=True)
    elif "low to high" in sort_by:
        filtered_evidence = sorted(filtered_evidence, key=lambda e: e.get("similarity_score", 0))
    elif sort_by == "Recency":
        filtered_evidence = sorted(filtered_evidence, key=lambda e: e.get("publication_date", ""), reverse=True)

    st.info(f"Showing {len(filtered_evidence)} of {len(evidence)} evidence chunks")

    # Display evidence
    for chunk in filtered_evidence:
        render_evidence_chunk(chunk, cited=chunk.get("chunk_id") in cited_ids)


def render_evidence_chunk(chunk: Dict[str, Any], cited: bool = False):
    """Render a single evidence chunk."""
    chunk_id = chunk.get("chunk_id", "N/A")
    source = chunk.get("source", "Unknown")
    source_type = chunk.get("source_type", "unknown")
    similarity = chunk.get("similarity_score", 0)
    title = chunk.get("title", "N/A")
    text = chunk.get("text", "N/A")
    metadata = chunk.get("metadata", {})

    # Header with citation status
    cited_badge = "✅ **CITED**" if cited else "❌ Not cited"

    with st.expander(
        f"{cited_badge} | {source_type.upper()} | Similarity: {similarity:.2f}",
        expanded=False,
    ):
        st.markdown(f"**Source:** {source}")
        st.markdown(f"**Title:** {title}")
        st.markdown(f"**Chunk ID:** `{chunk_id}`")

        # Metadata
        if metadata:
            st.subheader("Metadata")
            for key, value in metadata.items():
                st.write(f"**{key}:** {value}")

        # Full text
        st.subheader("Text")
        st.text_area(
            "Chunk content",
            value=text,
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )

        # Direct link if available
        if chunk.get("url"):
            st.link_button("🔗 View source", chunk["url"], use_container_width=True)


# ============================================================================
# ORCHESTRATION INTEGRATION (Backend Contract)
# ============================================================================

def call_backend_pipeline(
    query: str,
    therapeutic_area: str,
    jurisdiction: str,
) -> Optional[Dict[str, Any]]:
    """
    Call the backend orchestration graph.

    Contract: `orchestration.graph.run_query_pipeline(query, therapeutic_area, jurisdiction)`
    Input: query, therapeutic_area, jurisdiction
    Output: Dict with final_answer, citations, claims, evidence, trace

    Integrated with Phase 0 backend scaffold.
    For demonstration during Phase 0-4, falls back to mock data if pipeline is not yet fully implemented.
    """
    try:
        from orchestration.graph import run_query_pipeline

        # Call the real pipeline
        result = run_query_pipeline(
            query=query,
            therapeutic_area=therapeutic_area,
            jurisdiction=jurisdiction,
        )

        # If pipeline returned an error, optionally supplement with mock data for demonstration
        if result.get("status") == "failed" and st.session_state.get("demo_mode", False):
            st.info("Pipeline returned stub Phase 0 output. Showing demonstration mock data.")
            mock_result = generate_mock_result(query, therapeutic_area, jurisdiction)
            # Merge: keep real data where available, supplement with mock
            return {
                **mock_result,
                "query": result.get("query", query),
                "therapeutic_area": result.get("therapeutic_area", therapeutic_area),
                "jurisdiction": result.get("jurisdiction", jurisdiction),
                "status": result.get("status", "demo"),
            }

        return result

    except (ImportError, ModuleNotFoundError, AttributeError) as e:
        st.warning(f"Backend pipeline not available: {e}. Using mock data for demonstration.")
        return generate_mock_result(query, therapeutic_area, jurisdiction)

    except ValueError as e:
        st.error(f"Input validation error: {str(e)}")
        return None

    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        return None


def generate_mock_result(
    query: str,
    therapeutic_area: str,
    jurisdiction: str,
) -> Dict[str, Any]:
    """Generate mock result for UI development and testing."""
    return {
        "query": query,
        "therapeutic_area": therapeutic_area,
        "jurisdiction": jurisdiction,
        "final_answer": (
            f"Based on evidence retrieved for {therapeutic_area} under {jurisdiction} jurisdiction, "
            "the analysis shows [1] that clinical data supports the efficacy of the proposed treatment. "
            "Multiple regulatory sources [2] [3] confirm the safety profile. However, long-term outcomes "
            "remain unverified [4] pending additional studies."
        ),
        "claims": [
            {
                "sentence": "Clinical data supports the efficacy of the proposed treatment.",
                "confidence_tier": "High",
                "confidence_rationale": "Corroborated by 3 sources including 1 FDA label; based on peer-reviewed literature from 2023-2024; verification check passed.",
            },
            {
                "sentence": "Multiple regulatory sources confirm the safety profile.",
                "confidence_tier": "Medium",
                "confidence_rationale": "Supported by 2 regulatory sources (FDA, EMA); some jurisdictional variation noted.",
            },
            {
                "sentence": "Long-term outcomes remain unverified.",
                "confidence_tier": "Unverified",
                "confidence_rationale": "Limited follow-up data; verification check flagged insufficient evidence.",
            },
        ],
        "citations": [
            {
                "number": 1,
                "chunk_id": "chunk_001",
                "source": "PubMed Central",
                "doi_or_url": "https://pubmed.ncbi.nlm.nih.gov/12345678",
                "exact_span": "Clinical trials demonstrated sustained efficacy over 12 months",
                "confidence": "High",
                "rationale": "Peer-reviewed clinical trial data",
            },
            {
                "number": 2,
                "chunk_id": "chunk_002",
                "source": "FDA Approval Letter",
                "doi_or_url": "https://www.fda.gov/drugs/...",
                "exact_span": "The safety profile was deemed acceptable with standard monitoring",
                "confidence": "High",
                "rationale": "Regulatory approval authority",
            },
            {
                "number": 3,
                "chunk_id": "chunk_003",
                "source": "EMA CHMP Opinion",
                "doi_or_url": "https://www.ema.europa.eu/...",
                "exact_span": "Safety was consistent with known mechanism of action",
                "confidence": "High",
                "rationale": "EU regulatory authority",
            },
            {
                "number": 4,
                "chunk_id": "chunk_004",
                "source": "ClinicalTrials.gov",
                "doi_or_url": "https://clinicaltrials.gov/ct2/show/NCT00000000",
                "exact_span": "Long-term follow-up data collection is ongoing",
                "confidence": "Unverified",
                "rationale": "Incomplete data; trial still active",
            },
        ],
        "evidence": [
            {
                "chunk_id": "chunk_001",
                "source": "PubMed Central",
                "source_type": "literature",
                "similarity_score": 0.94,
                "title": "Phase III Efficacy Trial of Treatment X",
                "text": "Clinical trials demonstrated sustained efficacy over 12 months in oncology patients.",
                "metadata": {
                    "pmid": "12345678",
                    "journal": "Journal of Clinical Oncology",
                    "year": 2024,
                },
                "url": "https://pubmed.ncbi.nlm.nih.gov/12345678",
            },
            {
                "chunk_id": "chunk_002",
                "source": "FDA Approval Letter",
                "source_type": "regulatory",
                "similarity_score": 0.91,
                "title": "Application BLA #123456 Approval",
                "text": "The safety profile was deemed acceptable with standard monitoring.",
                "metadata": {
                    "application_number": "BLA #123456",
                    "approval_date": "2024-01-15",
                },
                "url": "https://www.fda.gov/drugs/drug-approvals-and-databases",
            },
            {
                "chunk_id": "chunk_003",
                "source": "EMA CHMP Opinion",
                "source_type": "regulatory",
                "similarity_score": 0.88,
                "title": "CHMP Positive Opinion for Drug X",
                "text": "Safety was consistent with known mechanism of action.",
                "metadata": {
                    "product_name": "Drug X",
                    "opinion_date": "2023-11-20",
                    "jurisdiction": "EMA",
                },
                "url": "https://www.ema.europa.eu/",
            },
            {
                "chunk_id": "chunk_004",
                "source": "ClinicalTrials.gov",
                "source_type": "clinical_trial",
                "similarity_score": 0.72,
                "title": "Long-term Follow-up of Treatment X",
                "text": "Long-term follow-up data collection is ongoing with interim results expected.",
                "metadata": {
                    "nct_id": "NCT00000000",
                    "status": "Active, not recruiting",
                    "phase": "IV",
                },
                "url": "https://clinicaltrials.gov/ct2/show/NCT00000000",
            },
            {
                "chunk_id": "chunk_005",
                "source": "Preprint Server",
                "source_type": "preprint",
                "similarity_score": 0.65,
                "title": "Preliminary Real-World Evidence for Treatment X",
                "text": "Early real-world data suggests tolerability comparable to clinical trials.",
                "metadata": {
                    "server": "medRxiv",
                    "uploaded": "2024-08-01",
                },
                "url": "https://www.medrxiv.org/",
            },
        ],
        "trace": [
            {
                "node": "Query Planner",
                "status": "completed",
                "duration_ms": 450,
                "state_updates": {
                    "retrieval_plan": {
                        "sub_queries": ["FDA approval status", "clinical efficacy", "safety data"],
                        "source_types": ["regulatory", "literature", "clinical_trial"],
                    }
                },
                "metadata": {"model": "claude-sonnet-5"},
            },
            {
                "node": "Literature Retriever",
                "status": "completed",
                "duration_ms": 800,
                "state_updates": {
                    "retrieved_chunks": {
                        "literature": 3,
                        "similarity_range": [0.88, 0.94],
                    }
                },
                "metadata": {"vector_db": "chroma", "query_count": 1},
            },
            {
                "node": "Clinical Trials Retriever",
                "status": "completed",
                "duration_ms": 620,
                "state_updates": {
                    "retrieved_chunks": {
                        "clinical_trial": 2,
                        "similarity_range": [0.71, 0.79],
                    }
                },
                "metadata": {"vector_db": "chroma", "query_count": 1},
            },
            {
                "node": "Regulatory Retriever",
                "status": "completed",
                "duration_ms": 540,
                "state_updates": {
                    "retrieved_chunks": {
                        "regulatory": 2,
                        "similarity_range": [0.84, 0.91],
                    }
                },
                "metadata": {"vector_db": "chroma", "jurisdictions": ["FDA", "EMA"]},
            },
            {
                "node": "Evidence Ranker",
                "status": "completed",
                "duration_ms": 320,
                "state_updates": {
                    "ranked_evidence": {
                        "cluster_count": 3,
                        "dedup_ratio": 0.2,
                    }
                },
                "metadata": {"model": "claude-haiku-4.5"},
            },
            {
                "node": "Confidence Scorer",
                "status": "completed",
                "duration_ms": 150,
                "state_updates": {
                    "confidence_scores": {
                        "high_confidence": 2,
                        "medium_confidence": 1,
                        "low_confidence": 0,
                    }
                },
                "metadata": {"scoring_method": "deterministic", "weights": "config/scoring_weights.yaml"},
            },
            {
                "node": "Synthesizer",
                "status": "completed",
                "duration_ms": 1200,
                "state_updates": {
                    "synthesized_claims": {
                        "claim_count": 3,
                        "avg_citation_per_claim": 1.33,
                    }
                },
                "metadata": {"model": "claude-sonnet-5", "retries": 0},
            },
            {
                "node": "Verifier",
                "status": "completed",
                "duration_ms": 890,
                "state_updates": {
                    "verification_results": {
                        "passed": 2,
                        "unverified": 1,
                    }
                },
                "metadata": {"model": "claude-opus-5", "groundedness_checks": 3},
            },
        ],
    }


# ============================================================================
# ERROR HANDLING & VALIDATION
# ============================================================================

def render_error_message(error: str):
    """Display error message in user-friendly format."""
    st.error(f"❌ Error: {error}")


# ============================================================================
# MAIN APPLICATION FLOW
# ============================================================================

def main():
    """Main application entry point."""

    # Render sidebar with domain selection
    is_domain_valid = render_sidebar()

    # Render query input
    query = render_query_input(is_domain_valid)

    # Handle query submission
    if query:
        with st.spinner("🔍 Running pipeline..."):
            result = call_backend_pipeline(
                query=query,
                therapeutic_area=st.session_state.therapeutic_area,
                jurisdiction=st.session_state.jurisdiction,
            )

            if result:
                st.session_state.current_result = result
            else:
                st.error("Failed to process query. Please try again.")

    # Display results if available
    if st.session_state.current_result:
        result = st.session_state.current_result

        # Three tabs: Answer | Trace | Evidence
        tab_answer, tab_trace, tab_evidence = st.tabs([
            "📄 Synthesized Answer",
            "🔄 Agent Trace",
            "🔍 Evidence Explorer",
        ])

        with tab_answer:
            render_synthesized_answer_tab(result)

        with tab_trace:
            render_agent_trace_tab(result.get("trace", []))

        with tab_evidence:
            render_evidence_explorer_tab(
                result.get("evidence", []),
                result.get("citations", []),
            )
    else:
        if not is_domain_valid:
            st.info("👈 Select a therapeutic area and jurisdiction in the sidebar to begin.")
        else:
            st.info("📝 Enter a query above and click **Submit Query** to analyze the evidence.")


if __name__ == "__main__":
    main()
