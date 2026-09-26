# P3 Triage Agent

## Overview

The **P3 Triage Agent** is a quality-gate component of the agentic RAG pipeline that reviews and triages Low-confidence and Unverified claims. It applies a deterministic decision framework to assess whether claims should be:

- **Accepted** — confidence tier is appropriate to evidence
- **Escalated** — claim is grounded but needs more/better evidence
- **Dropped** — claim is contradicted or wholly ungrounded
- **Re-evaluated** — data integrity issue prevents clear judgment

Every decision is traceable to specific policy thresholds and evidence quality metrics, making triage auditable and repeatable.

## Why P3 Triage?

R&D teams using this system need to trust outputs. Low-confidence claims are inherently risky — they may indicate:

1. Legitimate gaps in evidence (acceptable, but should be escalated for more targeted retrieval)
2. Weak sourcing that doesn't meet standards for that domain (drop or accept with rationale)
3. Data integrity problems (flag for backend audit)

The P3 Triage Agent replaces subjective "maybe drop this?" decisions with explicit, policy-driven rubrics that can be reviewed by stakeholders, calibrated over time, and integrated into CI/CD or approval workflows.

## Architecture

```
RAGState (with ClaimGraph)
         │
         ▼
    P3 Triage Agent
         │
    ├─ Load Policy ─────────────────┐
    │                               │
    ├─ Extract P3 Claims ◄──────────┤
    │  (Low + Unverified)           │
    │                               │
    ├─ Per-Claim Triage ────────────┤
    │  • Resolve evidence           │
    │  • Check groundedness         │
    │  • Count sources              │
    │  • Apply rubric               │
    │  • Check promotions           │
    │                               │
    ├─ Aggregate Stats ◄───────────┘
    │
    ▼
P3TriageReport (JSON)
    │
    ├─ metadata
    ├─ claims[]
    │  ├─ claim_id
    │  ├─ decision
    │  ├─ severity
    │  ├─ rationale
    │  └─ next_action
    │
    └─ summary
       ├─ decision_counts
       ├─ severity_distribution
       └─ pass_quality_gate
```

## Usage

### Basic Usage

```python
from agents.p3_triage_agent import run_p3_triage
from orchestration.graph import RAGState

# After running the main pipeline, extract RAGState
rag_state: RAGState = ...  # from graph.invoke()

# Run triage
report, filepath = run_p3_triage(
    rag_state=rag_state,
    query="What is the safety profile of drug X in pediatric populations?",
    therapeutic_area="pediatric_oncology",
    jurisdiction="FDA",
    policy_path="config/triage_policy.yaml",  # default
)

# Report is saved to eval/triage_reports/{timestamp}_p3_triage.json
print(f"Report saved to: {filepath}")
print(f"Quality gate: {'PASS' if report.summary.pass_quality_gate else 'FAIL'}")
print(f"Recommendation: {report.summary.overall_recommendation}")
```

### Advanced: Custom Policy

```python
from agents.p3_triage_agent import P3TriageAgent

agent = P3TriageAgent(policy_path="config/triage_policy_strict.yaml")
report = agent.triage(rag_state, query, therapeutic_area, jurisdiction)

# Inspect per-claim decisions
for claim_detail in report.claims:
    if claim_detail.decision == TriageDecision.DROP:
        print(f"Drop: {claim_detail.original_sentence}")
        print(f"  Reason: {claim_detail.rationale}")
```

### Integration: Pipeline Hook

Add to `orchestration/graph.py` after response composition:

```python
from agents.p3_triage_agent import run_p3_triage

async def post_synthesis_triage(state: RAGState) -> RAGState:
    """Optional: run P3 triage on synthesized answer before returning."""
    report, _ = run_p3_triage(
        state,
        state.original_query,
        state.therapeutic_area,
        state.jurisdiction,
    )
    
    # Store report in state for UI inspection
    state.triage_report = report
    
    # Check quality gate
    if not report.summary.pass_quality_gate:
        # Optionally flag answer or trigger re-synthesis
        state.quality_gate_status = "FAILED"
    
    return state
```

## Policy Configuration

Policy lives in `config/triage_policy.yaml` and defines:

### Thresholds

```yaml
triage_thresholds:
  corroboration_for_escalation: 2        # min sources for promotion
  min_authority_tier_for_acceptance: 0.65 # min tier (0-1.0) to accept single-source
  recency_half_life_days: 365            # for age-based discounting
  min_chunk_relevance: 0.5               # similarity threshold
```

### Decision Framework

| Decision | Trigger | Action |
|----------|---------|--------|
| **Drop** | Explicit contradiction in cited chunks; no valid citations; claim not entailed | Remove from answer |
| **Escalate** | Grounded but single low-tier source, or all low-tier (preprint/trial only), or too old | Re-run retrieval with different queries |
| **Accept** | Grounded; meets corroboration/authority thresholds; confidence tier is appropriate | No action needed |
| **ReEvaluate** | Cited chunks missing; metadata corrupted; cannot determine authority tier | Flag for backend data audit |

### Promotion Criteria

```yaml
promotion_criteria:
  from_low_to_medium:
    - min_corroboration_sources: 2
    - include_regulatory: true
    - max_age_days: 730
  from_medium_to_high:
    - min_corroboration_sources: 3
    - include_multiple_jurisdictions: true
    - recent_publication: 365
```

## Report Format

### Full Report (JSON)

```json
{
  "metadata": {
    "report_id": "abc12345",
    "timestamp": "2026-09-19T14:32:00Z",
    "source_query": "Safety in pediatric populations",
    "therapeutic_area": "pediatric_oncology",
    "jurisdiction": "FDA",
    "total_p3_candidates": 3
  },
  "claims": [
    {
      "claim_id": "claim_001",
      "original_sentence": "Efficacy was shown in Phase II trials...",
      "original_confidence": "Low",
      "decision": "Escalate",
      "recommended_confidence": "Medium",
      "severity": "medium",
      "rationale": "Grounded in only 1 low-tier source (authority: 0.65). Needs corroboration.",
      "source_issues": [],
      "next_action": "Request backend retrieval with broader queries",
      "cited_chunk_ids": ["chunk_123", "chunk_124"],
      "num_corroborating_sources": 1,
      "highest_authority_tier": 0.65
    }
  ],
  "summary": {
    "total_claims_reviewed": 3,
    "decision_counts": {
      "Accept": 1,
      "Escalate": 1,
      "Drop": 1
    },
    "severity_distribution": {
      "low": 1,
      "medium": 1,
      "critical": 1
    },
    "promotion_candidates": 1,
    "drops_recommended": 1,
    "overall_recommendation": "REVIEW: 1 claim recommended for removal. 1 promotion candidate.",
    "pass_quality_gate": false
  }
}
```

### Dashboard Summary

For UI/dashboard display, use `TriageReportSummary`:

```json
{
  "report_id": "abc12345",
  "timestamp": "2026-09-19T14:32:00Z",
  "therapeutic_area": "pediatric_oncology",
  "jurisdiction": "FDA",
  "total_reviewed": 3,
  "pass_quality_gate": false,
  "critical_issues": 1,
  "recommendation": "REVIEW: 1 claim recommended for removal."
}
```

## Decision Logic (Detailed)

### Groundedness Check

A claim is considered **grounded** if:
- All cited chunks resolve to Evidence objects in the claim graph
- At least one chunk has similarity_score ≥ `min_chunk_relevance` (default 0.5)
- Evidence text entails (or substantially supports) the claim

If not grounded → **Drop** with severity **CRITICAL**.

### Source Corroboration

Count unique documents across all evidence chunks. Multiple chunks from the same document count as 1 source.

### Authority Tier

Highest tier across all cited chunks, from `source_authority_tier` metadata:
- Regulatory (FDA/EMA/ICH/PMDA/MHRA): 1.00
- Peer-reviewed literature: 0.75
- Clinical trial registry: 0.65
- Preprint: 0.40

### Rubric Application

```
IF groundedness_fail
  → DROP (critical)

IF num_sources == 1 AND authority < 0.75
  → ESCALATE (medium) — needs corroboration

IF num_sources >= 2 AND authority < 0.75 AND no_regulatory
  → ESCALATE (high) — needs higher-tier source

IF num_sources >= corroboration_threshold AND authority >= min_tier
  → ACCEPT (low)

IF authority >= min_tier
  → ACCEPT (low) — meets baseline

ELSE
  → ESCALATE (medium) — unclear
```

### Promotion Eligibility

After triage decision, check if tier can be promoted:

```
IF current_tier == Low AND num_sources >= 2 AND authority >= 0.75
  → recommend Medium

IF current_tier == Medium AND num_sources >= 3 AND authority >= 1.0
  → recommend High
```

## Quality Metrics

Each report includes:

- **Confidence tier matches**: Claims where original tier matches recommendation
- **Promotion candidates**: Claims eligible for tier upgrade
- **Escalations needed**: Claims needing more evidence
- **Drops recommended**: Claims to remove
- **Data integrity issues**: Claims with missing evidence
- **Pass quality gate**: Boolean (true if no critical issues)

## Integration with Pipeline

### Phase 5 (Demo UI + Eval)

The P3 Triage Agent can be added as an optional post-processing step:

1. **Strict Mode** — run triage on every synthesis; fail quality gate if critical issues
2. **Advisory Mode** — run triage; show report alongside answer but don't block
3. **Audit Mode** — run triage only on answers saved for review/replay

### Phase 6 (Stretch)

- Calibrate policy thresholds against golden set performance
- Build triage-triggered auto-retrieval (detect escalation → re-query automatically)
- Integrate with approval workflow (require sign-off on dropped claims)

## Extending the Agent

### Custom Decision Rules

Edit `config/triage_policy.yaml` decision_framework section:

```yaml
decision_framework:
  drop:
    conditions:
      - "Explicit contradiction in cited chunks"
      - "<your custom condition>"
  escalate:
    conditions:
      - "..."
```

### Custom Severity Levels

Extend `SeverityLevel` enum in `schemas/triage_report.py`:

```python
class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"  # new
```

### LLM-Assisted Triage (Future)

Replace deterministic checks with optional LLM verification:

```python
def _check_groundedness_llm(self, claim: Claim, evidence: List[Evidence]) -> bool:
    """Optional: use Verifier (Opus) to double-check groundedness."""
    # Call agents/verifier.py for independent check
    pass
```

## Monitoring and Feedback

Track triage reports over time:

```bash
# List all reports
ls eval/triage_reports/ | sort

# Compare reports across queries/domains
python -c "
import json
from pathlib import Path
for p in sorted(Path('eval/triage_reports').glob('*.json')):
    with open(p) as f:
        report = json.load(f)
    print(f\"{report['metadata']['report_id']}: \
          {report['summary']['total_claims_reviewed']} claims, \
          pass_gate={report['summary']['pass_quality_gate']}\")
"
```

### Calibration

If P3 triage reports show consistent patterns (e.g., most Low → Medium promotions), consider adjusting policy thresholds:

```yaml
# If too many escalations, relax corroboration threshold
corroboration_for_escalation: 1  # was 2

# If too many drops, raise authority threshold
min_authority_tier_for_acceptance: 0.50  # was 0.65
```

## References

- [`docs/architecture.md`](architecture.md) §4 — Confidence scoring (inputs to triage)
- [`docs/requirements.md`](requirements.md) R4–R5 — Confidence and verification requirements
- [`config/triage_policy.yaml`](../config/triage_policy.yaml) — Policy thresholds (tunable)
- [`schemas/triage_report.py`](../schemas/triage_report.py) — Output schemas
- [`agents/p3_triage_agent.py`](../agents/p3_triage_agent.py) — Implementation
