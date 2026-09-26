"""
Pydantic schemas for P3 Triage Agent reports.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TriageDecision(str, Enum):
    """Triage decision outcomes."""
    ACCEPT = "Accept"
    ESCALATE = "Escalate"
    DROP = "Drop"
    RE_EVALUATE = "ReEvaluate"


class SeverityLevel(str, Enum):
    """Triage severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceTier(str, Enum):
    """Confidence tier assignments."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNVERIFIED = "Unverified"


class ClaimTriageDetail(BaseModel):
    """Detailed triage assessment for a single claim."""

    claim_id: str = Field(..., description="Unique identifier for this claim")
    original_sentence: str = Field(..., description="The claim text")
    original_confidence: ConfidenceTier = Field(
        ..., description="Original confidence tier from pipeline"
    )

    decision: TriageDecision = Field(..., description="Triage decision")
    recommended_confidence: Optional[ConfidenceTier] = Field(
        None, description="Recommended confidence tier if different from original"
    )
    severity: SeverityLevel = Field(..., description="Issue severity if applicable")

    rationale: str = Field(..., description="Human-readable triage justification")
    source_issues: List[str] = Field(
        default_factory=list,
        description="Specific problems identified in cited sources"
    )
    next_action: str = Field(
        ..., description="Recommended action (accept, escalate, drop, investigate)"
    )

    # Evidence details
    cited_chunk_ids: List[str] = Field(
        default_factory=list,
        description="IDs of chunks cited by this claim"
    )
    num_corroborating_sources: int = Field(
        ..., description="Number of independent sources supporting this claim"
    )
    highest_authority_tier: Optional[float] = Field(
        None, description="Authority tier of the best-sourced citation (0-1.0)"
    )

    # Metadata
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    reviewer_agent: str = Field(default="p3-triage-agent")


class TriageAggregateSummary(BaseModel):
    """Aggregate statistics from triage report."""

    total_claims_reviewed: int = Field(...)
    decision_counts: Dict[TriageDecision, int] = Field(
        ..., description="Count of each triage decision"
    )
    severity_distribution: Dict[SeverityLevel, int] = Field(
        ..., description="Count by severity level"
    )

    # Quality metrics
    confidence_tier_matches: int = Field(
        ..., description="Claims where confidence tier is correct"
    )
    promotion_candidates: int = Field(
        ..., description="Claims recommended for confidence promotion"
    )
    escalation_needed: int = Field(
        ..., description="Claims needing re-evaluation with more evidence"
    )
    drops_recommended: int = Field(
        ..., description="Claims recommended for removal"
    )
    data_integrity_issues: int = Field(
        ..., description="Claims with data quality problems"
    )

    # Overall recommendation
    overall_recommendation: str = Field(
        ..., description="Summary recommendation for pipeline quality gate"
    )
    pass_quality_gate: bool = Field(
        ..., description="Should output pass quality gate (true if no critical issues)"
    )


class TriageReportMetadata(BaseModel):
    """Report metadata and context."""

    report_id: str = Field(..., description="Unique report identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_query: str = Field(..., description="Original user query")
    therapeutic_area: str = Field(...)
    jurisdiction: str = Field(...)

    total_p3_candidates: int = Field(
        ..., description="Total Low/Unverified claims analyzed"
    )
    report_generated_by: str = Field(default="p3-triage-agent")


class P3TriageReport(BaseModel):
    """Complete P3 Triage Agent report."""

    metadata: TriageReportMetadata = Field(...)
    claims: List[ClaimTriageDetail] = Field(
        ..., description="Per-claim triage decisions"
    )
    summary: TriageAggregateSummary = Field(...)

    class Config:
        use_enum_values = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return self.model_dump(mode="json")


# Lightweight summary for dashboard/UI display
class TriageReportSummary(BaseModel):
    """Condensed triage report for UI display."""

    report_id: str
    timestamp: datetime
    therapeutic_area: str
    jurisdiction: str
    total_reviewed: int
    pass_quality_gate: bool
    critical_issues: int
    recommendation: str
