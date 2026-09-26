"""
P3 Triage Agent — reviews Low confidence and Unverified claims from the RAG pipeline.

Generates deterministic triage decisions (Accept, Escalate, Drop, ReEvaluate) based
on evidence quality, source authority, corroboration, and data integrity checks.

Output: structured `P3TriageReport` with per-claim decisions and aggregate statistics.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import uuid

from pydantic import ValidationError
import yaml

from schemas.claim_graph import ClaimGraph, Claim, Evidence
from schemas.triage_report import (
    P3TriageReport,
    ClaimTriageDetail,
    TriageReportMetadata,
    TriageAggregateSummary,
    TriageDecision,
    SeverityLevel,
    ConfidenceTier,
)
from orchestration.state import RAGState


@dataclass
class TriagePolicy:
    """Loaded triage policy configuration."""

    corroboration_for_escalation: int
    min_authority_tier_for_acceptance: float
    recency_half_life_days: int
    min_chunk_relevance: float
    promotion_criteria: Dict
    decision_framework: Dict


class P3TriageAgent:
    """
    Deterministic P3 triage engine.

    Reads claims marked Low/Unverified from RAGState, applies decision rubric,
    and generates audit report with per-claim decisions.
    """

    def __init__(self, policy_path: str = "config/triage_policy.yaml"):
        """Load triage policy."""
        self.policy_path = policy_path
        self.policy = self._load_policy()
        self.report_dir = Path("eval/triage_reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def _load_policy(self) -> TriagePolicy:
        """Load and parse triage policy YAML."""
        with open(self.policy_path) as f:
            config = yaml.safe_load(f)

        thresholds = config.get("triage_thresholds", {})
        promo = config.get("promotion_criteria", {})
        framework = config.get("decision_framework", {})

        return TriagePolicy(
            corroboration_for_escalation=thresholds.get(
                "corroboration_for_escalation", 2
            ),
            min_authority_tier_for_acceptance=thresholds.get(
                "min_authority_tier_for_acceptance", 0.65
            ),
            recency_half_life_days=thresholds.get("recency_half_life_days", 365),
            min_chunk_relevance=thresholds.get("min_chunk_relevance", 0.5),
            promotion_criteria=promo,
            decision_framework=framework,
        )

    def triage(
        self,
        rag_state: RAGState,
        query: str,
        therapeutic_area: str,
        jurisdiction: str,
    ) -> P3TriageReport:
        """
        Run triage on claims in RAGState.

        Args:
            rag_state: Pipeline state containing claims and evidence
            query: Original user query
            therapeutic_area: Domain scoping
            jurisdiction: Regulatory scoping

        Returns:
            P3TriageReport with per-claim decisions
        """

        # Filter to P3 candidates (Low + Unverified confidence)
        p3_claims = self._extract_p3_claims(rag_state)

        if not p3_claims:
            # No P3 claims to triage; return passing report
            return self._empty_report(
                query, therapeutic_area, jurisdiction, rag_state
            )

        # Triage each claim
        triage_details = []
        for claim in p3_claims:
            detail = self._triage_single_claim(claim, rag_state)
            triage_details.append(detail)

        # Aggregate statistics
        summary = self._compute_summary(triage_details)

        # Build report
        metadata = TriageReportMetadata(
            report_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow(),
            source_query=query,
            therapeutic_area=therapeutic_area,
            jurisdiction=jurisdiction,
            total_p3_candidates=len(p3_claims),
        )

        report = P3TriageReport(
            metadata=metadata,
            claims=triage_details,
            summary=summary,
        )

        return report

    def _extract_p3_claims(self, rag_state: RAGState) -> List[Claim]:
        """Extract Low + Unverified claims from claim graph."""
        if not rag_state.claim_graph:
            return []

        p3_claims = [
            claim
            for claim in rag_state.claim_graph.claims
            if claim.confidence_tier.value in ["Low", "Unverified"]
        ]
        return p3_claims

    def _triage_single_claim(
        self, claim: Claim, rag_state: RAGState
    ) -> ClaimTriageDetail:
        """
        Determine triage decision for a single claim.

        Decision logic:
        1. Check if claim is grounded in cited chunks
        2. Count corroborating sources
        3. Check authority tiers
        4. Check data integrity
        5. Apply rubric
        """

        # Resolve evidence for this claim
        cited_evidence = self._resolve_evidence(claim, rag_state)

        if not cited_evidence:
            # No resolvable evidence
            return ClaimTriageDetail(
                claim_id=claim.id,
                original_sentence=claim.text,
                original_confidence=claim.confidence_tier,
                decision=TriageDecision.RE_EVALUATE,
                severity=SeverityLevel.HIGH,
                rationale="Cited chunks not found or corrupted in evidence store.",
                source_issues=["Missing evidence resolution"],
                next_action="Flag for backend data quality audit",
                cited_chunk_ids=claim.cited_chunk_ids,
                num_corroborating_sources=0,
            )

        # Check groundedness
        is_grounded = self._check_groundedness(claim, cited_evidence)
        if not is_grounded:
            return ClaimTriageDetail(
                claim_id=claim.id,
                original_sentence=claim.text,
                original_confidence=claim.confidence_tier,
                decision=TriageDecision.DROP,
                severity=SeverityLevel.CRITICAL,
                rationale="Claim is not entailed by cited evidence. Verifier correctly flagged as ungrounded.",
                source_issues=["No valid support in citations"],
                next_action="Remove from synthesized answer",
                cited_chunk_ids=claim.cited_chunk_ids,
                num_corroborating_sources=len(cited_evidence),
            )

        # Count corroborating sources
        num_sources = self._count_independent_sources(cited_evidence)
        max_authority_tier = self._max_authority_tier(cited_evidence)

        # Apply decision rubric
        decision, severity, rationale, next_action = self._apply_decision_rubric(
            claim=claim,
            num_corroborating_sources=num_sources,
            max_authority_tier=max_authority_tier,
            cited_evidence=cited_evidence,
        )

        # Check if promotion is recommended
        recommended_confidence = self._check_promotion(
            claim.confidence_tier, num_sources, max_authority_tier, cited_evidence
        )

        return ClaimTriageDetail(
            claim_id=claim.id,
            original_sentence=claim.text,
            original_confidence=claim.confidence_tier,
            decision=decision,
            recommended_confidence=recommended_confidence,
            severity=severity,
            rationale=rationale,
            next_action=next_action,
            cited_chunk_ids=claim.cited_chunk_ids,
            num_corroborating_sources=num_sources,
            highest_authority_tier=max_authority_tier,
        )

    def _resolve_evidence(
        self, claim: Claim, rag_state: RAGState
    ) -> List[Evidence]:
        """Resolve claim's cited_chunk_ids to Evidence objects."""
        if not rag_state.claim_graph or not rag_state.claim_graph.evidence:
            return []

        evidence_by_id = {e.chunk_id: e for e in rag_state.claim_graph.evidence}
        resolved = []

        for chunk_id in claim.cited_chunk_ids:
            if chunk_id in evidence_by_id:
                resolved.append(evidence_by_id[chunk_id])

        return resolved

    def _check_groundedness(self, claim: Claim, evidence: List[Evidence]) -> bool:
        """
        Simple heuristic: if evidence list is non-empty and has high enough
        similarity, assume groundedness. In production, would do LLM re-check.
        """
        if not evidence:
            return False

        # Check if any evidence has sufficient relevance
        for e in evidence:
            if (
                e.similarity_score >= self.policy.min_chunk_relevance
            ):  # reasonable match
                return True

        return False

    def _count_independent_sources(self, evidence: List[Evidence]) -> int:
        """Count unique documents across evidence list (deduplicated)."""
        document_ids = set()
        for e in evidence:
            if e.document and e.document.document_id:
                document_ids.add(e.document.document_id)

        return len(document_ids)

    def _max_authority_tier(self, evidence: List[Evidence]) -> Optional[float]:
        """Return highest authority tier from cited sources."""
        if not evidence:
            return None

        tiers = [
            e.document.metadata.get("source_authority_tier", 0.0)
            for e in evidence
            if e.document and e.document.metadata
        ]

        return max(tiers) if tiers else None

    def _apply_decision_rubric(
        self,
        claim: Claim,
        num_corroborating_sources: int,
        max_authority_tier: Optional[float],
        cited_evidence: List[Evidence],
    ) -> Tuple[TriageDecision, SeverityLevel, str, str]:
        """
        Apply decision framework from policy.

        Returns: (decision, severity, rationale, next_action)
        """

        # Case 1: Single low-tier source → Escalate
        if (
            num_corroborating_sources == 1
            and (max_authority_tier or 0.0) < 0.75
        ):
            return (
                TriageDecision.ESCALATE,
                SeverityLevel.MEDIUM,
                f"Grounded in only 1 low-tier source (authority: {max_authority_tier:.2f}). Needs corroboration.",
                "Request backend retrieval with broader queries",
            )

        # Case 2: Multiple sources but all low-tier, no regulatory → Escalate
        if num_corroborating_sources >= 2:
            has_regulatory = any(
                e.document
                and e.document.metadata
                and e.document.metadata.get("source_type") == "regulatory"
                for e in cited_evidence
            )
            if not has_regulatory and (max_authority_tier or 0.0) < 0.75:
                return (
                    TriageDecision.ESCALATE,
                    SeverityLevel.HIGH,
                    f"Supported by {num_corroborating_sources} sources but no regulatory precedent. Low-tier evidence only.",
                    "Escalate to regulatory retrieval if applicable to domain",
                )

        # Case 3: Well-grounded, meets corroboration threshold → Accept
        if num_corroborating_sources >= self.policy.corroboration_for_escalation and (
            max_authority_tier or 0.0
        ) >= self.policy.min_authority_tier_for_acceptance:
            return (
                TriageDecision.ACCEPT,
                SeverityLevel.LOW,
                f"Confidence tier appropriate: {num_corroborating_sources} corroborating sources, max authority tier {max_authority_tier:.2f}.",
                "Accept; no action needed",
            )

        # Default: Accept if grounded and meets baseline
        if (max_authority_tier or 0.0) >= self.policy.min_authority_tier_for_acceptance:
            return (
                TriageDecision.ACCEPT,
                SeverityLevel.LOW,
                f"Grounded in evidence with acceptable authority tier ({max_authority_tier:.2f}). Confidence tier is appropriate.",
                "Accept; no action needed",
            )

        # Fallback: Escalate if confidence is unclear
        return (
            TriageDecision.ESCALATE,
            SeverityLevel.MEDIUM,
            "Evidence quality unclear; recommend re-evaluation.",
            "Re-run Verifier with explicit confidence check",
        )

    def _check_promotion(
        self,
        current_tier: ConfidenceTier,
        num_sources: int,
        max_authority: Optional[float],
        evidence: List[Evidence],
    ) -> Optional[ConfidenceTier]:
        """
        Recommend confidence tier promotion if conditions are met.

        E.g., Low → Medium if corroboration and authority are strong enough.
        """

        # Low → Medium promotion
        if current_tier == ConfidenceTier.LOW:
            promo_criteria = self.policy.promotion_criteria.get(
                "from_low_to_medium", {}
            )
            min_sources = promo_criteria.get("min_corroboration_sources", 2)

            if (
                num_sources >= min_sources
                and (max_authority or 0.0) >= 0.75
            ):
                return ConfidenceTier.MEDIUM

        # Medium → High promotion
        if current_tier == ConfidenceTier.MEDIUM:
            promo_criteria = self.policy.promotion_criteria.get(
                "from_medium_to_high", {}
            )
            min_sources = promo_criteria.get("min_corroboration_sources", 3)

            if num_sources >= min_sources and (max_authority or 0.0) >= 1.0:
                return ConfidenceTier.HIGH

        return None

    def _compute_summary(
        self, triage_details: List[ClaimTriageDetail]
    ) -> TriageAggregateSummary:
        """Compute aggregate statistics from triage details."""

        decision_counts: Dict[TriageDecision, int] = defaultdict(int)
        severity_counts: Dict[SeverityLevel, int] = defaultdict(int)

        for detail in triage_details:
            decision_counts[detail.decision] += 1
            severity_counts[detail.severity] += 1

        confidence_matches = sum(
            1
            for d in triage_details
            if d.decision == TriageDecision.ACCEPT
            and d.recommended_confidence is None
        )

        promotion_candidates = sum(
            1 for d in triage_details if d.recommended_confidence is not None
        )

        escalations = sum(
            1 for d in triage_details if d.decision == TriageDecision.ESCALATE
        )

        drops = sum(
            1 for d in triage_details if d.decision == TriageDecision.DROP
        )

        investigations = sum(
            1 for d in triage_details if d.decision == TriageDecision.RE_EVALUATE
        )

        # Quality gate: fail if critical issues
        critical_count = severity_counts[SeverityLevel.CRITICAL]
        pass_gate = critical_count == 0

        # Recommendation
        if critical_count > 0:
            recommendation = f"FAIL: {critical_count} critical issue(s) found. Remove dropped claims before publishing."
        elif drops > 0:
            recommendation = f"REVIEW: {drops} claims recommended for removal. {promotion_candidates} promotion candidate(s)."
        elif escalations > 0:
            recommendation = f"ESCALATE: {escalations} claim(s) need more evidence. Consider re-retrieval before publishing."
        else:
            recommendation = "PASS: All Low/Unverified claims are appropriately tiered. Ready to publish."

        return TriageAggregateSummary(
            total_claims_reviewed=len(triage_details),
            decision_counts=dict(decision_counts),
            severity_distribution=dict(severity_counts),
            confidence_tier_matches=confidence_matches,
            promotion_candidates=promotion_candidates,
            escalation_needed=escalations,
            drops_recommended=drops,
            data_integrity_issues=investigations,
            overall_recommendation=recommendation,
            pass_quality_gate=pass_gate,
        )

    def _empty_report(
        self,
        query: str,
        therapeutic_area: str,
        jurisdiction: str,
        rag_state: RAGState,
    ) -> P3TriageReport:
        """Return a passing report when there are no P3 claims."""

        metadata = TriageReportMetadata(
            report_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow(),
            source_query=query,
            therapeutic_area=therapeutic_area,
            jurisdiction=jurisdiction,
            total_p3_candidates=0,
        )

        summary = TriageAggregateSummary(
            total_claims_reviewed=0,
            decision_counts={},
            severity_distribution={},
            confidence_tier_matches=0,
            promotion_candidates=0,
            escalation_needed=0,
            drops_recommended=0,
            data_integrity_issues=0,
            overall_recommendation="PASS: No Low/Unverified claims to triage.",
            pass_quality_gate=True,
        )

        return P3TriageReport(
            metadata=metadata,
            claims=[],
            summary=summary,
        )

    def save_report(
        self, report: P3TriageReport, pretty: bool = True
    ) -> Path:
        """
        Persist report to disk.

        Returns: path to saved report
        """

        # Use ISO format timestamp for filename
        timestamp_str = report.metadata.timestamp.isoformat()
        filename = f"{timestamp_str}_{report.metadata.report_id}_p3_triage.json"
        filepath = self.report_dir / filename

        report_dict = report.to_dict()
        # to_dict() already converts datetimes to ISO strings due to mode="json"

        with open(filepath, "w") as f:
            json.dump(report_dict, f, indent=2 if pretty else None)

        return filepath


def run_p3_triage(
    rag_state: RAGState,
    query: str,
    therapeutic_area: str,
    jurisdiction: str,
    policy_path: str = "config/triage_policy.yaml",
) -> Tuple[P3TriageReport, Path]:
    """
    Convenience function: instantiate agent, run triage, save report.

    Returns: (report, file_path)
    """

    agent = P3TriageAgent(policy_path=policy_path)
    report = agent.triage(rag_state, query, therapeutic_area, jurisdiction)
    filepath = agent.save_report(report)

    return report, filepath
