# Agent Delegation Guide

Three specialized agents own this project. Each has complete autonomy within their scope and does not need context from the others' work.

## Agent Overview

### 1. **backend-engineer** 
**Scope:** `ingestion/`, `agents/`, `orchestration/`, `domain/`, `config/`, `schemas/`, `eval/`

**Owns:** The entire RAG pipeline for drug-discovery intelligence
- Query Planner (multi-source sub-question decomposition)
- Multi-source retrievers (PubMed, Clinical Trials, FDA/regulatory)
- Evidence Ranker & deduplication
- Confidence Scorer (deterministic Python, reads `config/scoring_weights.yaml`)
- Synthesizer (LLM-driven claim generation with structured citations)
- Citation Binder (builds ClaimGraph with full provenance)
- Verifier (Opus 5 groundedness recheck, triggers Synthesizer retry loop)
- Response Composer (assembles final answer with citations)

**Contract:** Only integration point with frontend is `orchestration/graph.py`'s public entrypoint. Do NOT assume how the UI renders output.

**Current work phases:**
- **Phase 0:** Scaffolding — repo structure, Pydantic schemas, Chroma setup, LangGraph skeleton
- **Phase 1:** Single-source retrieval — PubMed connector + literature retriever
- **Phase 2:** Multi-source + domain filtering — Clinical Trials + FDA connectors, taxonomy routing
- **Phase 3:** Ranking + confidence scoring — Evidence ranker, confidence formula with weights
- **Phase 4:** Synthesis + citation + verification — Full pipeline end-to-end
- **Phase 5 (parallel):** Eval harness — golden set, retrieval/faithfulness/calibration metrics
- **Phase 6 (stretch):** Additional regulatory connectors (EMA, ICH, PMDA, MHRA), jurisdiction comparison

---

### 2. **frontend-engineer**
**Scope:** `ui/` only

**Owns:** The Streamlit demo application
- Therapeutic area + jurisdiction selectors (both required before query submission)
- Streamed agent-trace view (LangGraph state updates for R&D audience transparency)
- Final answer rendering with inline numbered citations
- Citation links (clickable → exact source span, URL/DOI/registry ID)
- Confidence tier display + human-readable rationale per claim
- "Unverified" claim handling (never hidden)
- Evidence explorer tab (all retrieved chunks, sources, similarity scores, metadata)

**Contract:** Read only from `orchestration/graph.py` output (`RAGState` structure). If backend needs a new field for UI rendering, ask backend-engineer to update schemas — do NOT reach into pipeline internals.

**Current work phases:**
- **Phase 5:** Build demo UI (runs parallel with Phase 4 backend work)
  - Domain selectors
  - Streamed trace view
  - Cited-answer rendering
  - Evidence explorer

---

### 3. **p3-triage-agent**
**Scope:** P3-triage quality-gate workflow (deterministic, read-only audit layer)

**Owns:** Triaging low-confidence and unverified claims from pipeline output
- Ingests P3 candidates from `RAGState` (claims marked "Low" or "Unverified")
- Re-assesses each claim against its cited evidence using deterministic rubric (table in agent spec)
- Generates structured triage reports: JSON with per-claim decisions + aggregate statistics
- Outputs to `eval/triage_reports/{timestamp}_p3_triage_report.json`

**Framework:** NOT LLM-driven. Uses explicit rubric:
- Drop (explicitly contradicted by cited chunks)
- Escalate (grounded but insufficient sources)
- Accept (Low/Medium/High tier correct)
- ReEvaluate (data integrity issues)

**Contract:** Does NOT modify `RAGState` or pipeline confidence scores. Reports are recommendations only, not automatic mutations.

**Current work:** Implementation already complete (Phase 5 eval layer). Ready to consume backend output once pipeline produces P3 candidates.

---

## How to Delegate Work

### Scenario 1: All three agents work on their phases in parallel

**From main session, send three Agent calls simultaneously:**

```python
Agent({
  description: "Build backend pipeline Phase 0: scaffolding",
  prompt: """You are the backend-engineer for this RAG drug-discovery system.
  
  Your task: Complete Phase 0 scaffolding.
  See docs/units-of-work.md Phase 0 for full spec.
  
  Exit criterion: python -m orchestration.graph runs end-to-end against dummy state.
  """
})

Agent({
  description: "Build frontend UI for demo",
  prompt: """You are the frontend-engineer for this RAG drug-discovery system.
  
  Your task: Build the Streamlit demo UI (Phase 5).
  See docs/requirements.md R1, R3, R4, R6 and frontend-engineer.md for spec.
  
  Build domain selectors, streamed trace view, cited-answer rendering, evidence explorer.
  """
})

Agent({
  description: "Review P3 triage implementation",
  prompt: """You are the p3-triage-agent.
  
  Your task: Verify the P3 triage implementation is complete and correct.
  See p3-triage-agent.md and P3_TRIAGE_AGENT_SETUP.md.
  
  Run the example: python eval/p3_triage_example.py and confirm output structure.
  """
})
```

All three run independently in parallel. Results come back to main session.

### Scenario 2: Sequential phases (backend first, then frontend)

**Phase 0–4: Backend builds full pipeline**

```python
Agent({
  description: "Build RAG pipeline Phases 0–4",
  prompt: """Complete Phases 0 through 4 of the backend pipeline.
  See docs/units-of-work.md.
  
  Phase 0: Scaffolding (exit: dummy run works)
  Phase 1: PubMed ingestion + literature retrieval
  Phase 2: Multi-source + domain filtering
  Phase 3: Ranking + confidence scoring
  Phase 4: Synthesis + citation + verification
  
  Exit criterion: Full pipeline produces cited, confidence-scored, verified answer end-to-end.
  """
})
```

**Phase 5: Frontend builds UI (once backend Phase 0–4 done)**

```python
Agent({
  description: "Build Streamlit demo UI",
  prompt: """The backend has completed Phases 0–4.
  
  Now build the UI to call orchestration/graph.py and render results.
  See docs/requirements.md R1, R3, R4, R6.
  
  Build: domain selectors, streamed trace, cited answers, evidence explorer.
  """
})
```

### Scenario 3: Delegate a specific bug or change

**Example: Frontend needs confidence-tier rationale field**

```python
Agent({
  description: "Add confidence rationale to backend output",
  prompt: """You are backend-engineer.
  
  The UI needs to display confidence rationale per claim (why High/Medium/Low/Unverified).
  
  Task: Add a rationale field to the claim structure in schemas/claim_graph.py 
  and ensure the Confidence Scorer populates it with a human-readable explanation.
  
  Coordinate with orchestration/graph.py public contract to document the new field.
  """
})
```

---

## Key Isolation Points

Each agent's `.md` file defines **ownership** and **contract**. No context needed from others:

- **backend-engineer** reads requirements from `docs/` and config files; outputs RAGState to orchestration/graph.py
- **frontend-engineer** reads RAGState from orchestration/graph.py; renders it; never reaches into agents/ internals
- **p3-triage-agent** reads RAGState output; produces JSON reports; does NOT modify pipeline state

**Result:** Each can work independently. Work is isolated by module ownership, not by context passing.

---

## Work Checklist (Current State)

- [ ] **backend-engineer Phase 0:** Repo scaffolding, schemas, LangGraph skeleton
- [ ] **backend-engineer Phase 1:** PubMed ingestion + retrieval
- [ ] **backend-engineer Phase 2:** Multi-source + domain filtering
- [ ] **backend-engineer Phase 3:** Ranking + scoring
- [ ] **backend-engineer Phase 4:** Synthesis + citation + verification
- [ ] **frontend-engineer Phase 5:** Streamlit UI (can start after Phase 0 backend)
- [ ] **backend-engineer Phase 5:** Eval harness (parallel with UI)
- [ ] **p3-triage-agent:** Review/validate existing implementation
- [ ] **backend-engineer Phase 6 (stretch):** Additional regulatory connectors

---

## Next Steps

1. Review this guide with your agents.
2. Send them their respective task prompts using the Agent tool.
3. Results will arrive as background tasks — check with `/workflows` or `ListAgents`.
4. Each agent stays within their `.md` file scope — no overlap needed.

