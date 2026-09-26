# Phase 0 — Scaffolding: Complete

Exit criterion met: `python -m orchestration.graph` runs end-to-end with all 8 nodes executing successfully.

## Directory Structure

Created:
- `ingestion/` — data connectors (stub for Phase 1)
- `domain/` — taxonomy and routing (stub for Phase 2)
- `ui/` — frontend (stub for Phase 5)
- `data/chroma/` — persistent Chroma vector store directory
- `data/claim_graphs/` — per-answer provenance storage
- `data/raw/` — raw fetched documents

Existing:
- `agents/` — pipeline nodes
- `orchestration/` — LangGraph graph definition
- `config/` — policy/weights config files
- `schemas/` — Pydantic data models
- `eval/` — evaluation harness

## Pydantic Schemas (Pydantic v2)

Located in `orchestration/state.py`:
- **RAGState** — main pipeline state carrying query, domain selection, retrieved evidence, confidence scores, synthesized claims, verification results, and final answer
- **Chunk** — single retrieved evidence chunk with full metadata (source type, jurisdiction, authority tier, char span)
- **ConfidenceScore** — per-claim confidence with numeric score, tier, component scores, and rationale
- **ClaimGraphNode** & **ClaimGraphEdge** — graph structure for provenance
- **ClaimGraphLegacy** — legacy nodes+edges format

Located in `schemas/claim_graph.py`:
- **ClaimGraph** — complete claim graph with provenance
- **Claim**, **Evidence**, **Document**, **Source** — supporting structures

## Chroma Setup

`ingestion/vector_store.py`:
- `get_chroma_client()` — persistent client initialization from `CHROMA_PERSIST_DIR` (env var or default)
- `get_or_create_collection()` — collection management
- `init_stub_collections()` — stub collections for PubMed, ClinicalTrials, FDA, EMA, ICH
- `search_similar_chunks()` — metadata-filtered similarity search
- `upsert_chunks()` — batch insert/update

## Configuration Stubs

`config/scoring_weights.yaml`:
- Confidence scoring formula weights (retrieval_similarity, source_authority_tier, corroboration_count, recency_score, llm_consistency_check)
- Confidence tier thresholds (high/medium/low/unverified)
- Recency decay half-lives per source type
- Corroboration scoring config

`config/domains.yaml`:
- Therapeutic area taxonomy (oncology, cardiology, neurology, immunology, infectious_disease, rare_disease)
- Regulatory jurisdiction definitions (FDA, EMA, ICH, PMDA, MHRA, GLOBAL)
- MeSH keyword mappings for auto-tagging
- Default selections for testing

## LangGraph Skeleton

`orchestration/graph.py`:
- 8 stub pipeline nodes (all pass state through unchanged):
  1. QueryPlanner — decomposes query into sub-questions
  2. LiteratureRetriever — PubMed/PMC domain-filtered search
  3. ClinicalTrialsRetriever — ClinicalTrials.gov search
  4. RegulatoryRetriever — FDA/EMA/ICH/PMDA/MHRA search
  5. EvidenceRanker — dedup and clustering
  6. Synthesizer — answer synthesis with citations
  7. Verifier — groundedness checking
  8. ResponseComposer — final answer assembly
- Linear edge topology (Phase 0; retry logic added Phase 4)
- `build_graph()` — constructs StateGraph
- `create_app()` — compiles into runnable application
- `main()` — test harness with dummy state

## Entry Point

`orchestration/__init__.py`:
- Exports RAGState, Chunk, ConfidenceScore, ClaimGraph, ClaimGraphNode, ClaimGraphEdge
- Exports create_app(), build_graph(), main() for external use
- Importable and runnable via `from orchestration import create_app`

## Supporting Files

- `.env.template` — environment variables reference
- `requirements.txt` — dependencies (langgraph, chromadb, pydantic v2, anthropic, etc.)
- Package __init__.py files for: ingestion/, domain/, ui/, agents/, schemas/

## Running Phase 0

```bash
# Install dependencies
pip install -r requirements.txt

# Run end-to-end pipeline (dummy state)
python -m orchestration.graph

# Expected output:
# ✓ All 8 pipeline nodes executed successfully
```

## Phase 1 Ready

The scaffolding is complete. Next phase tasks:
- Implement real data connectors (PubMed, ClinicalTrials.gov, FDA)
- Implement real retrievers (vector store queries, domain filtering)
- Add ingestion pipeline (fetch → parse → chunk → tag → embed → upsert)
- Test with real PubMed data
