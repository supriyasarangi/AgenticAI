# P3 Triage Agent — Setup and Integration Guide

## What Was Created

A complete **P3 Triage Agent** system for reviewing and triaging Low-confidence and Unverified claims from the RAG pipeline. The agent generates deterministic, auditable quality-gate reports.

### Files Created

#### 1. **Agent Definition** (`.claude/agents/`)
- **`p3-triage-agent.md`** — Agent spec for the project's Claude Code setup, defining roles, contract, and responsibilities.

#### 2. **Configuration** (`config/`)
- **`triage_policy.yaml`** — Policy thresholds and decision rubrics (tunable, no code changes needed).

#### 3. **Schemas** (`schemas/`)
- **`triage_report.py`** — Pydantic models for triage reports:
  - `P3TriageReport` — complete report
  - `ClaimTriageDetail` — per-claim decision
  - `TriageAggregateSummary` — summary statistics
  - `TriageReportSummary` — lightweight dashboard summary

#### 4. **Implementation** (`agents/`)
- **`p3_triage_agent.py`** — Main agent implementation:
  - `P3TriageAgent` class with policy loading and triage logic
  - `run_p3_triage()` convenience function
  - Deterministic decision framework (no LLM calls)

#### 5. **Documentation** (`docs/`)
- **`p3-triage.md`** — Comprehensive guide:
  - Architecture overview
  - Usage examples
  - Policy configuration
  - Decision logic details
  - Integration patterns
  - Extension points

#### 6. **Example/Test** (`eval/`)
- **`p3_triage_example.py`** — Runnable example demonstrating:
  - Creating sample RAGState
  - Running triage
  - Displaying reports

## Directory Structure

```
Day_4_usecase/
├── .claude/agents/
│   ├── backend-engineer.md
│   ├── frontend-engineer.md
│   └── p3-triage-agent.md               ← NEW
├── config/
│   └── triage_policy.yaml               ← NEW
├── schemas/
│   └── triage_report.py                 ← NEW
├── agents/
│   └── p3_triage_agent.py               ← NEW
├── docs/
│   └── p3-triage.md                     ← NEW
├── eval/
│   └── p3_triage_example.py             ← NEW
└── P3_TRIAGE_AGENT_SETUP.md             ← NEW (this file)
```

## Quick Start

### 1. Install Dependencies

Ensure your environment has:
- `pydantic` v2 (already in project)
- `pyyaml` (for config parsing)
- `python 3.11+`

```bash
pip install pyyaml pydantic
```

### 2. Run the Example

```bash
cd /home/labuser/Downloads/Day_4_usecase
python eval/p3_triage_example.py
```

Expected output:
```
P3 Triage Agent Example
Creating sample RAGState...
✓ Created RAGState with 3 claims
Running P3 Triage Agent...
✓ Triage complete
✓ Report saved to: eval/triage_reports/2026-09-19T...p3_triage.json

================================================================================
P3 TRIAGE REPORT
================================================================================
...
```

### 3. Inspect the Generated Report

```bash
# List all reports
ls eval/triage_reports/

# View latest report
cat eval/triage_reports/*.json | python -m json.tool
```

## Integration Points

### Option A: Post-Synthesis Hook (Recommended)

Add triage as an optional step after the Synthesizer produces claims:

```python
# In orchestration/graph.py

from agents.p3_triage_agent import run_p3_triage

def post_synthesis_node(state: RAGState) -> RAGState:
    """Optional: triage Low/Unverified claims before Response Composer."""
    
    if state.synthesized_claims:
        report, report_path = run_p3_triage(
            state,
            state.original_query,
            state.therapeutic_area,
            state.jurisdiction,
        )
        
        # Store report in state for UI inspection
        state.triage_report = report
        
        # Quality gate check
        if not report.summary.pass_quality_gate:
            state.quality_gate_status = "FAILED"
            # Optional: could trigger Verifier re-run or escalate to human review
    
    return state

# Add to graph
graph.add_node("post_synthesis_triage", post_synthesis_node)
graph.add_edge("response_composer", "post_synthesis_triage")
```

### Option B: Post-Pipeline Audit

Run triage offline on saved `RAGState` snapshots:

```python
import json
from pathlib import Path
from agents.p3_triage_agent import run_p3_triage
from orchestration.state import RAGState

# Load a previously saved RAGState
with open("data/claim_graphs/query_001.json") as f:
    state_dict = json.load(f)
    state = RAGState(**state_dict)

# Run triage
report, filepath = run_p3_triage(state, ...)

# Store alongside claim graph
report_copy_path = Path("data/claim_graphs") / f"{state.query_id}_triage.json"
import shutil
shutil.copy(filepath, report_copy_path)
```

### Option C: Quality Gate Workflow

Integrate triage into CI/CD or approval workflows:

```bash
#!/bin/bash
# test_quality_gate.sh

python -c "
import sys
import json
from pathlib import Path

latest_report = sorted(Path('eval/triage_reports').glob('*.json'))[-1]
with open(latest_report) as f:
    report = json.load(f)

if not report['summary']['pass_quality_gate']:
    print('FAIL: Quality gate failed')
    print(report['summary']['overall_recommendation'])
    sys.exit(1)
else:
    print('PASS: Quality gate passed')
    sys.exit(0)
"
```

## Usage Examples

### Example 1: Basic Triage

```python
from orchestration.graph import invoke_pipeline
from agents.p3_triage_agent import run_p3_triage

# Run main pipeline
rag_state = invoke_pipeline(
    query="Safety profile of Drug X?",
    therapeutic_area="oncology",
    jurisdiction="FDA",
)

# Triage the output
report, filepath = run_p3_triage(
    rag_state,
    "Safety profile of Drug X?",
    "oncology",
    "FDA",
)

print(f"Quality gate: {'PASS' if report.summary.pass_quality_gate else 'FAIL'}")
print(report.summary.overall_recommendation)
```

### Example 2: Custom Policy

Create `config/triage_policy_strict.yaml`:

```yaml
triage_thresholds:
  corroboration_for_escalation: 3  # require 3 sources, not 2
  min_authority_tier_for_acceptance: 0.85  # strict
```

Then:

```python
from agents.p3_triage_agent import P3TriageAgent

agent = P3TriageAgent(policy_path="config/triage_policy_strict.yaml")
report = agent.triage(rag_state, query, area, jurisdiction)
```

### Example 3: Inspect Decisions

```python
from schemas.triage_report import TriageDecision

for claim in report.claims:
    if claim.decision == TriageDecision.DROP:
        print(f"❌ Drop: {claim.original_sentence}")
        print(f"   {claim.rationale}\n")
    elif claim.decision == TriageDecision.ESCALATE:
        print(f"⬆ Escalate: {claim.original_sentence}")
        print(f"   {claim.next_action}\n")
```

## Policy Tuning

The triage policy is designed to be tuned without code changes. Edit `config/triage_policy.yaml`:

### Scenario 1: Too Many Drops

**Symptom**: Reports show many "Drop" decisions, but claims seem reasonable.

**Fix**: Raise `min_chunk_relevance` threshold:

```yaml
triage_thresholds:
  min_chunk_relevance: 0.6  # was 0.5
```

### Scenario 2: Too Many Escalations

**Symptom**: Reports escalate most Low claims for more evidence.

**Fix**: Lower `corroboration_for_escalation`:

```yaml
triage_thresholds:
  corroboration_for_escalation: 1  # was 2
```

### Scenario 3: Stringent Review (Production)

**Scenario**: Want strict quality for regulatory submissions.

**Fix**: Use `config/triage_policy_strict.yaml`:

```yaml
triage_thresholds:
  corroboration_for_escalation: 3
  min_authority_tier_for_acceptance: 0.90
  min_chunk_relevance: 0.75

promotion_criteria:
  from_low_to_medium:
    - min_corroboration_sources: 3
    - include_regulatory: true
    - include_multiple_jurisdictions: true
```

## Output Interpretation

### Quality Gate Status

```
pass_quality_gate: true
→ No critical issues; answer is ready to publish.

pass_quality_gate: false
→ Critical issues found; human review or re-synthesis needed.
```

### Overall Recommendation

| Recommendation | Meaning | Action |
|---|---|---|
| `PASS: All claims appropriate` | No issues | Publish answer |
| `REVIEW: N claims for removal` | Some claims are weak | Remove flagged claims or get more evidence |
| `ESCALATE: N claims need evidence` | Evidence is thin | Re-run retrieval with different queries |
| `FAIL: N critical issues` | Claims are contradicted/invalid | Re-synthesize or investigate |

### Decision Breakdown

```json
"decision_counts": {
  "Accept": 5,      # ✓ Tier is correct
  "Escalate": 2,    # ⬆ Needs more evidence
  "Drop": 1,        # ✗ Remove this claim
  "ReEvaluate": 0   # ? Data quality issue
}
```

## Monitoring and Dashboards

### Simple Dashboard Script

```python
import json
from pathlib import Path
from collections import defaultdict

reports_dir = Path("eval/triage_reports")
stats = defaultdict(lambda: {"pass": 0, "fail": 0})

for report_file in sorted(reports_dir.glob("*.json")):
    with open(report_file) as f:
        report = json.load(f)
    
    area = report["metadata"]["therapeutic_area"]
    status = "pass" if report["summary"]["pass_quality_gate"] else "fail"
    stats[area][status] += 1

print("Triage Quality by Domain:")
for area, counts in sorted(stats.items()):
    total = counts["pass"] + counts["fail"]
    pass_rate = 100 * counts["pass"] / total if total > 0 else 0
    print(f"  {area}: {pass_rate:.0f}% pass ({counts['pass']}/{total})")
```

## Troubleshooting

### ImportError: No module named 'yaml'

```bash
pip install pyyaml
```

### FileNotFoundError: config/triage_policy.yaml

Ensure `triage_policy.yaml` exists. If missing, copy default:

```bash
cp config/triage_policy.yaml config/triage_policy.backup.yaml
```

### Report not saved

Check that `eval/triage_reports/` directory exists and is writable:

```bash
mkdir -p eval/triage_reports
ls -la eval/triage_reports/
```

### All claims marked "ReEvaluate"

Evidence is not resolving. Check:
1. `ClaimGraph.evidence` list is populated
2. `cited_chunk_ids` match evidence `chunk_id` values
3. Chunk metadata is not corrupted

## References

- **Agent spec**: `.claude/agents/p3-triage-agent.md`
- **Policy config**: `config/triage_policy.yaml`
- **Full documentation**: `docs/p3-triage.md`
- **Example code**: `eval/p3_triage_example.py`
- **Main implementation**: `agents/p3_triage_agent.py`
- **Report schemas**: `schemas/triage_report.py`

## Next Steps

1. **Run the example** — `python eval/p3_triage_example.py`
2. **Read the policy** — review `config/triage_policy.yaml`
3. **Review documentation** — read `docs/p3-triage.md` for detailed logic
4. **Integrate into pipeline** — add triage hook to `orchestration/graph.py`
5. **Tune policy** — adjust thresholds based on initial runs
6. **Build dashboard** — aggregate reports for monitoring

---

Created: 2026-09-19
P3 Triage Agent v1.0
