#!/usr/bin/env python
"""
Example: Running the P3 Triage Agent on sample claims.

This script demonstrates:
1. Creating a minimal RAGState with P3 claims
2. Running triage
3. Inspecting and displaying the report
"""

import json
from datetime import datetime
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.triage_report import (
    ConfidenceTier,
    TriageDecision,
    P3TriageReport,
)
from schemas.claim_graph import (
    ClaimGraph,
    Claim,
    Evidence,
    Document,
    Source,
)
from orchestration.state import RAGState
from agents.p3_triage_agent import run_p3_triage


def create_sample_rag_state() -> RAGState:
    """
    Create a minimal RAGState with sample P3 (Low/Unverified) claims for testing.
    """

    # Create sample source
    source1 = Source(
        source_id="pubmed_12345",
        source_url="https://pubmed.ncbi.nlm.nih.gov/12345",
        source_type="literature",
    )

    source2 = Source(
        source_id="fda_app_123456",
        source_url="https://www.fda.gov/drugs/application_123456",
        source_type="regulatory",
    )

    # Create sample documents
    doc1 = Document(
        document_id="doc_001",
        title="Efficacy of Drug X in Pediatric Populations",
        authors=["Smith J.", "Doe A."],
        publication_date=datetime(2023, 6, 15),
        doc_type="journal_article",
        source=source1,
        metadata={
            "source_authority_tier": 0.75,
            "source_type": "literature",
            "therapeutic_area": "pediatric_oncology",
            "journal": "Oncology Today",
        },
    )

    doc2 = Document(
        document_id="doc_002",
        title="FDA Approval Letter - Drug X",
        authors=["FDA Review Team"],
        publication_date=datetime(2024, 1, 10),
        doc_type="approval_letter",
        source=source2,
        metadata={
            "source_authority_tier": 1.0,
            "source_type": "regulatory",
            "jurisdiction": "FDA",
            "therapeutic_area": "pediatric_oncology",
        },
    )

    # Create evidence (chunks)
    evidence_list = [
        Evidence(
            chunk_id="chunk_001",
            text="In the Phase II trial, 65% of pediatric patients showed partial response.",
            span_start=100,
            span_end=180,
            similarity_score=0.82,
            document=doc1,
        ),
        Evidence(
            chunk_id="chunk_002",
            text="The safety profile was acceptable with manageable side effects.",
            span_start=200,
            span_end=270,
            similarity_score=0.75,
            document=doc1,
        ),
        Evidence(
            chunk_id="chunk_003",
            text="FDA approved Drug X for pediatric patients aged 2-18 with condition Y.",
            span_start=50,
            span_end=130,
            similarity_score=0.88,
            document=doc2,
        ),
    ]

    # Create sample claims
    claims = [
        Claim(
            id="claim_001",
            text="Efficacy was shown in Phase II trials with a 65% response rate.",
            confidence_tier=ConfidenceTier.LOW,
            confidence_rationale="Single literature source, no regulatory corroboration.",
            cited_chunk_ids=["chunk_001"],
        ),
        Claim(
            id="claim_002",
            text="The drug has manageable safety in pediatric populations.",
            confidence_tier=ConfidenceTier.LOW,
            confidence_rationale="Only literature source; safety data not independently verified.",
            cited_chunk_ids=["chunk_002"],
        ),
        Claim(
            id="claim_003",
            text="FDA approved the drug for pediatric use.",
            confidence_tier=ConfidenceTier.MEDIUM,
            confidence_rationale="Regulatory source, but narrow scope.",
            cited_chunk_ids=["chunk_003"],
        ),
    ]

    # Create claim graph
    claim_graph = ClaimGraph(
        query_id="query_001",
        claims=claims,
        evidence=evidence_list,
        created_at=datetime.utcnow(),
    )

    # Create RAGState
    rag_state = RAGState(
        query_id="query_001",
        original_query="What is the efficacy and safety of Drug X in pediatric populations?",
        therapeutic_area="pediatric_oncology",
        jurisdiction="FDA",
        claim_graph=claim_graph,
    )

    return rag_state


def display_report(report: P3TriageReport) -> None:
    """Pretty-print the triage report."""

    print("\n" + "=" * 80)
    print("P3 TRIAGE REPORT")
    print("=" * 80)

    # Metadata
    print(f"\nReport ID: {report.metadata.report_id}")
    print(f"Timestamp: {report.metadata.timestamp.isoformat()}")
    print(f"Query: {report.metadata.source_query}")
    print(f"Domain: {report.metadata.therapeutic_area} / {report.metadata.jurisdiction}")
    print(f"Total P3 Candidates: {report.metadata.total_p3_candidates}")

    # Per-claim decisions
    print("\n" + "-" * 80)
    print("CLAIM DECISIONS")
    print("-" * 80)

    for i, claim in enumerate(report.claims, 1):
        print(f"\n[{i}] {claim.claim_id}")
        print(f"    Sentence: {claim.original_sentence}")
        print(f"    Original Confidence: {claim.original_confidence.value}")
        print(f"    Decision: {claim.decision.value}")
        print(f"    Severity: {claim.severity.value}")
        if claim.recommended_confidence:
            print(f"    ⬆ Recommend: {claim.recommended_confidence.value}")
        print(f"    Rationale: {claim.rationale}")
        print(f"    Action: {claim.next_action}")
        print(f"    Sources: {claim.num_corroborating_sources} | Authority: {claim.highest_authority_tier or 'N/A'}")

    # Summary
    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)

    summary = report.summary
    print(f"\nTotal Reviewed: {summary.total_claims_reviewed}")
    print(f"\nDecision Counts:")
    for decision, count in summary.decision_counts.items():
        print(f"  {decision.value}: {count}")

    print(f"\nSeverity Distribution:")
    for severity, count in summary.severity_distribution.items():
        print(f"  {severity.value}: {count}")

    print(f"\nMetrics:")
    print(f"  Confidence Tier Matches: {summary.confidence_tier_matches}")
    print(f"  Promotion Candidates: {summary.promotion_candidates}")
    print(f"  Escalations Needed: {summary.escalation_needed}")
    print(f"  Drops Recommended: {summary.drops_recommended}")
    print(f"  Data Integrity Issues: {summary.data_integrity_issues}")

    print(f"\nQuality Gate: {'✓ PASS' if summary.pass_quality_gate else '✗ FAIL'}")
    print(f"Recommendation: {summary.overall_recommendation}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("P3 Triage Agent Example")
    print("Creating sample RAGState...")

    # Create sample state
    rag_state = create_sample_rag_state()
    print(f"✓ Created RAGState with {len(rag_state.claim_graph.claims)} claims")

    # Run triage
    print("\nRunning P3 Triage Agent...")
    try:
        report, filepath = run_p3_triage(
            rag_state=rag_state,
            query=rag_state.original_query,
            therapeutic_area=rag_state.therapeutic_area,
            jurisdiction=rag_state.jurisdiction,
            policy_path="config/triage_policy.yaml",
        )
        print(f"✓ Triage complete")
        print(f"✓ Report saved to: {filepath}")

        # Display report
        display_report(report)

        # Also print JSON for reference
        print("\nFull JSON Report:")
        print("-" * 80)
        report_dict = report.to_dict()
        # to_dict() already converts datetime to ISO strings (mode="json")
        print(json.dumps(report_dict, indent=2))

    except Exception as e:
        print(f"✗ Error during triage: {e}")
        import traceback
        traceback.print_exc()
