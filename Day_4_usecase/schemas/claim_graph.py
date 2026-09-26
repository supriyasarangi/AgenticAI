"""
Pydantic schemas for claim graphs and evidence relationships.

These schemas represent the structure of claims extracted from the RAG pipeline,
along with their evidence citations and provenance.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConfidenceTier(str, Enum):
    """Confidence tier assignments."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNVERIFIED = "Unverified"


class Source(BaseModel):
    """Information about a source document (journal, database, URL, etc.)."""

    source_id: str = Field(..., description="Unique source identifier")
    source_url: Optional[str] = Field(None, description="URL to the source")
    source_type: str = Field(
        ..., description="Type of source (e.g., 'literature', 'regulatory', 'preprint')"
    )


class Document(BaseModel):
    """A single document (paper, approval letter, etc.) from a source."""

    document_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    authors: List[str] = Field(default_factory=list, description="Document authors")
    publication_date: Optional[datetime] = Field(
        None, description="Publication/release date"
    )
    doc_type: str = Field(
        ..., description="Type of document (e.g., 'journal_article', 'approval_letter')"
    )
    source: Source = Field(..., description="Source information")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (authority tier, therapeutic area, etc.)",
    )


class Evidence(BaseModel):
    """A single piece of evidence (text chunk) from a document."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    text: str = Field(..., description="Text content of the chunk")
    span_start: int = Field(..., description="Start position in document")
    span_end: int = Field(..., description="End position in document")
    similarity_score: float = Field(
        ..., description="Relevance score (0-1) to query/claim"
    )
    document: Document = Field(..., description="Source document")


class Claim(BaseModel):
    """A single claim extracted from the synthesis phase."""

    id: str = Field(..., description="Unique claim identifier")
    text: str = Field(..., description="Claim text")
    confidence_tier: ConfidenceTier = Field(
        ..., description="Confidence level (High/Medium/Low/Unverified)"
    )
    confidence_rationale: str = Field(
        ..., description="Explanation for the confidence tier"
    )
    cited_chunk_ids: List[str] = Field(
        default_factory=list, description="IDs of chunks cited by this claim"
    )


class ClaimGraph(BaseModel):
    """
    Complete claim graph with provenance linking claims to evidence.

    This represents the output of the Citation & Verification phase,
    ready for input to the P3 Triage Agent.
    """

    query_id: str = Field(..., description="Identifier for the original query")
    claims: List[Claim] = Field(
        ..., description="List of extracted claims with confidence tiers"
    )
    evidence: List[Evidence] = Field(
        ..., description="List of evidence chunks cited by claims"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of graph creation"
    )
