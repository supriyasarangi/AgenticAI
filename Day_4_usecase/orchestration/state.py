"""
Shared state definition for RAG pipeline (LangGraph StateGraph).

All pipeline nodes read from and write to RAGState, which flows through
the graph from Query Planner → Response Composer.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Import ClaimGraph from schemas
from schemas.claim_graph import ClaimGraph as ClaimGraphStructure


class RAGState(BaseModel):
    """
    Shared state flowing through the pipeline.

    Carries: query, domain selection, retrieved evidence, confidence scores,
    synthesized claims, verification results, and final answer with citations.
    """

    # Input
    query: str = ""
    query_id: Optional[str] = None
    original_query: Optional[str] = None
    therapeutic_area: Optional[str] = None
    jurisdiction: Optional[str] = None

    # Planning
    retrieval_plan: Optional[Dict[str, Any]] = None

    # Retrieval
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)

    # Ranking & Scoring
    ranked_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_clusters: List[Dict[str, Any]] = Field(default_factory=list)

    # Synthesis
    synthesized_claims: List[Dict[str, Any]] = Field(default_factory=list)

    # Citation & Verification
    claim_graph: Optional[Union[ClaimGraphStructure, Dict[str, Any]]] = None
    verification_results: Optional[Dict[str, Any]] = None

    # Final output
    final_answer: Optional[str] = None
    response_citations: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = "pending"  # pending, processing, completed, failed
    error_log: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class Chunk(BaseModel):
    """Single retrieved evidence chunk with metadata."""

    chunk_id: str
    document_id: str
    text: str
    embedding: Optional[List[float]] = None

    # Source metadata
    source_type: str  # literature, clinical_trial, regulatory
    source_url: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    nct_id: Optional[str] = None

    # Domain metadata
    therapeutic_area: str
    jurisdiction: str  # FDA, EMA, ICH, PMDA, MHRA, GLOBAL

    # Document metadata
    title: str
    authors: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    doc_type: Optional[str] = None

    # Scoring metadata
    similarity_score: Optional[float] = None
    source_authority_tier: float = 0.5  # 1.0 (regulatory), 0.75 (literature), 0.65 (trials), 0.4 (preprints)

    # Character span in original document
    char_span_start: int
    char_span_end: int


class ConfidenceScore(BaseModel):
    """Per-claim confidence assessment with rationale."""

    claim_id: str
    score: float  # 0.0 to 1.0
    tier: str  # High, Medium, Low, Unverified

    # Component scores
    retrieval_similarity: float
    source_authority_score: float
    corroboration_count: int
    recency_score: float
    llm_consistency_check: float

    # Explanation
    rationale: str

    # Supporting evidence
    cited_chunk_ids: List[str]
    verification_status: str = "pending"  # pending, passed, failed, unverified


class ClaimGraphNode(BaseModel):
    """Single node in the claim graph (claim or evidence)."""

    node_id: str
    node_type: str  # claim, evidence, document, source
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClaimGraphEdge(BaseModel):
    """Single edge in the claim graph."""

    source_id: str
    target_id: str
    relation_type: str  # cites, supported_by, contradicts


class ClaimGraphLegacy(BaseModel):
    """
    Legacy graph-based claim structure (nodes + edges).

    Use schemas.claim_graph.ClaimGraph for new code.
    """

    graph_id: str
    query: str

    # Graph structure
    nodes: List[ClaimGraphNode]
    edges: List[ClaimGraphEdge]

    # Root claim (final answer)
    root_claim_id: str

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    therapeutic_area: str
    jurisdiction: str
