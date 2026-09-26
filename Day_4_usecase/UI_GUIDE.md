# Phase 5 — Demo UI Guide

This document describes the Streamlit demo UI for the agentic RAG drug-discovery system.

## Quick Start

### Prerequisites

1. **Python 3.11+**
2. **Environment**: Set `ANTHROPIC_API_KEY` before running

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run the UI

```bash
streamlit run ui/app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## Features

### 1. Domain Scope Configuration (R1)

**Requirement:** Both therapeutic area and regulatory jurisdiction must be selected before any query.

- **Therapeutic Area** — Choose one from:
  - Oncology
  - Cardiology
  - Neurology
  - Immunology
  - Infectious Disease
  - Rare Disease

- **Regulatory Jurisdiction** — Choose one from:
  - FDA (US)
  - EMA (European Union)
  - ICH (International harmonization)
  - PMDA (Japan)
  - MHRA (UK)
  - GLOBAL (for literature/trials without jurisdiction-specific registration)

**No silent defaults:** Both fields must be explicitly selected. The submit button is disabled until both are set.

### 2. Query Input

Enter your natural-language question, e.g.:
- "What is the FDA-approved dosage for X in oncology?"
- "How does the safety profile compare across EMA and FDA approvals?"
- "What recent clinical trial data supports the efficacy of treatment Y?"

The query is scoped to your selected therapeutic area and jurisdiction throughout the pipeline.

### 3. Results (Three Tabs)

#### Tab 1: Synthesized Answer

The final answer with:

- **Inline numbered citations** — [1], [2], etc. linking to source chunks
- **Per-claim confidence tiers** — 🟢 High, 🟡 Medium, 🟠 Low, 🔴 Unverified
- **Confidence rationale** — E.g., "Corroborated by 3 sources including 1 FDA label; verification check passed"
- **Citation reference list** — Full provenance for each citation:
  - Source document
  - URL / DOI / registry ID (clickable)
  - Exact quoted span from source
  - Confidence tier and rationale

**Key guarantees:**
- Every claim cites specific source chunks (R3)
- Unverified claims are always shown, never hidden (R5)
- Rationale explains which inputs produced the confidence tier (R4)

#### Tab 2: Agent Trace

Real-time view of the LangGraph pipeline execution:

- **Pipeline stages** (8 nodes):
  1. Query Planner — Decomposes query into sub-questions
  2. Literature Retriever — Queries PubMed/PMC/preprints
  3. Clinical Trials Retriever — Queries ClinicalTrials.gov
  4. Regulatory Retriever — Queries FDA/EMA/ICH/PMDA/MHRA indices
  5. Evidence Ranker — Deduplicates and ranks evidence
  6. Confidence Scorer — Assigns confidence tiers
  7. Synthesizer — Generates claim-tagged answer
  8. Verifier — Checks groundedness of claims

- **Per node:**
  - Status (✅ completed, ⏳ running, ⏺️ pending, ❌ failed)
  - Execution time (ms)
  - State updates (what changed)
  - Errors (if any)

**For R&D audience:** Understand *why* an answer was produced by inspecting which sources were retrieved, how they were ranked, and how confidence was scored.

#### Tab 3: Evidence Explorer

Inspect all retrieved evidence chunks (cited + uncited):

- **Filter by source type:**
  - Literature (peer-reviewed journals, preprints)
  - Clinical trials (ClinicalTrials.gov registry entries)
  - Regulatory (FDA/EMA/ICH/PMDA/MHRA documents)

- **Show options:**
  - All chunks
  - Cited only (chunks that appear in the final answer)
  - Uncited only (retrieved but not used)

- **Sort by:**
  - Similarity score (high to low, low to high)
  - Recency (newest first)

- **Per chunk:**
  - Citation status (✅ cited or ❌ not cited)
  - Source type and similarity score
  - Full metadata (PMID, DOI, NCT ID, approval date, etc.)
  - Complete text (read-only)
  - Direct link to source (if available)

**Purpose (R6):** Verify that evidence was retrieved correctly and understand what raw data was available vs. what was actually synthesized into the answer.

---

## Architecture & Integration

### Backend Contract

The UI imports a single entry point from the backend:

```python
from orchestration.graph import run_query_pipeline

result = run_query_pipeline(
    query="...",
    therapeutic_area="oncology",  # required, no silent default
    jurisdiction="FDA",           # required, no silent default
)
```

**Input validation:** Both `therapeutic_area` and `jurisdiction` are required. The backend raises `ValueError` if either is None or invalid.

**Output structure (Phase 0+):**

```python
{
    "query": str,
    "therapeutic_area": str,
    "jurisdiction": str,
    "final_answer": str,
    "claims": [
        {
            "sentence": str,
            "confidence_tier": "High" | "Medium" | "Low" | "Unverified",
            "confidence_rationale": str,
            # citations: [chunk_id, ...]
        },
        ...
    ],
    "citations": [
        {
            "number": int,
            "chunk_id": str,
            "source": str,              # e.g., "PubMed Central", "FDA Approval Letter"
            "doi_or_url": str,          # resolvable identifier
            "exact_span": str,          # verbatim quote from source
            "confidence": str,
            "rationale": str,
        },
        ...
    ],
    "evidence": [
        {
            "chunk_id": str,
            "source": str,
            "source_type": "literature" | "clinical_trial" | "regulatory",
            "similarity_score": float,
            "title": str,
            "text": str,
            "metadata": {...},
            "url": str,                 # optional
        },
        ...
    ],
    "trace": [
        {
            "node": str,                # node name
            "status": "completed" | "running" | "failed",
            "duration_ms": int,
            "state_updates": {...},
            "error": str,               # if failed
            "metadata": {...},
        },
        ...
    ],
    "status": "completed" | "failed",
    "error_log": [str, ...],
}
```

### Phases

- **Phase 0 (current):** Backend scaffold; LangGraph skeleton passes state through unchanged. UI works with mock data for demonstration.
- **Phase 1–3:** Ingestion, retrieval, ranking, confidence scoring. UI receives real evidence.
- **Phase 4:** Synthesis, verification. UI renders final answer with citations.
- **Phase 5:** UI is feature-complete and demoable end-to-end.

---

## Demo Mode

During Phase 0–3, the UI can run in **demo mode**, showing realistic mock data that demonstrates:

- How domain selection drives filtering
- Citation linking and confidence badges
- Agent trace visualization
- Evidence explorer filtering

To use demo mode:

```python
# Set in session state or pass as query parameter
st.session_state.demo_mode = True
```

Once the backend's Phase 0 scaffold is available, the UI automatically uses real data from `orchestration.graph.run_query_pipeline()`.

---

## Error Handling

The UI displays errors clearly:

- **Domain selection errors:** "Select both therapeutic area and jurisdiction to proceed"
- **Input validation errors:** "Both therapeutic_area and jurisdiction are required"
- **Pipeline errors:** Displayed in a red error box with details from the backend
- **Unverified claims:** Always shown (never hidden), marked with 🔴 and reason

---

## Deployment & Scaling

### Single-user local development (current)

```bash
streamlit run ui/app.py
```

### Multi-client (Phase 6+)

A FastAPI wrapper (`api/main.py`) can be added around `orchestration/graph.py` to enable:
- Multiple concurrent users
- REST API contract
- Horizontal scaling behind a load balancer

This is out of scope for v1 but requires no changes to the UI code.

---

## Testing & Quality

### Manual testing checklist

- [ ] Domain selection enforces both fields (no submit without both)
- [ ] Scope is displayed at top of results
- [ ] Citations are numbered and clickable (linking to reference list)
- [ ] Unverified claims are shown with rationale
- [ ] Evidence explorer filters work (source type, cited/uncited, sort)
- [ ] Agent trace shows all 8 nodes
- [ ] Errors are displayed clearly, not hidden

### Example queries to test

1. **Simple efficacy:** "What is the efficacy of X in oncology according to FDA?"
2. **Multi-source:** "Compare the safety profile across FDA and EMA for treatment Y"
3. **Real-world evidence:** "What real-world data is available for drug Z?"

---

## Code Structure

```
ui/
├── app.py                   # Main Streamlit app (this file)
├── __init__.py              # Module exports
└── README.md                # This guide
```

### Key functions in `app.py`

| Function | Purpose |
|----------|---------|
| `init_session_state()` | Initialize Streamlit session state |
| `render_sidebar()` | Domain selection sidebar (R1) |
| `render_query_input()` | Query input form |
| `render_synthesized_answer_tab()` | Tab 1: Cited answer (R3, R4) |
| `render_agent_trace_tab()` | Tab 2: Pipeline visibility |
| `render_evidence_explorer_tab()` | Tab 3: Raw evidence inspection (R6) |
| `call_backend_pipeline()` | Call `orchestration.graph.run_query_pipeline()` |
| `generate_mock_result()` | Demo data for Phase 0 development |

---

## Requirements Mapping

| Requirement | How the UI satisfies it |
|-------------|------------------------|
| **R1** — Domain-scoped query | Sidebar selectors; both required; no silent defaults; scope displayed at top |
| **R3** — Claim-level citation | Inline numbered citations; reference list with exact spans; clickable URLs/DOIs |
| **R4** — Confidence judgment | Per-claim badges (High/Medium/Low/Unverified); visible rationale |
| **R6** — Evidence inspection | Evidence Explorer tab; filter by source type, citation status, sort by relevance |

---

## Next Steps (Phases 1–4)

As the backend implements each phase, the UI automatically receives more complete data:

- **Phase 1:** Real PubMed/PMC evidence
- **Phase 2:** Multi-source retrieval (trials, regulatory)
- **Phase 3:** Ranked evidence and real confidence scores
- **Phase 4:** Real synthesized answer with verified claims

No changes to `ui/app.py` are needed — it consumes the stable `orchestration/graph.run_query_pipeline()` contract.

---

## References

- `docs/requirements.md` — Functional requirements (R1–R6)
- `docs/architecture.md` — Tech stack and pipeline topology
- `docs/domain-model.md` — Therapeutic area and jurisdiction taxonomy
- `docs/units-of-work.md` — Phase 5 deliverable spec
- `.claude/agents/frontend-engineer.md` — Role specification
