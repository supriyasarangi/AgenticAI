# Units of Work

Phased build plan. Each phase names its exit criterion and which subagent owns it
(`.claude/agents/backend-engineer.md` / `.claude/agents/frontend-engineer.md`).
Module names refer to [`architecture.md`](architecture.md).

## Phase 0 — Scaffolding
**Owner:** backend-engineer

- Repo structure (`ingestion/`, `agents/`, `orchestration/`, `domain/`, `config/`,
  `schemas/`, `eval/`, `ui/`, `data/`).
- Pydantic schemas (`schemas/`): `RAGState`, `Chunk`, `ClaimGraph`, `ConfidenceScore`.
- Chroma persistent client setup (`ingestion/vector_store.py`).
- `.env`/settings loader; `config/scoring_weights.yaml` and `config/domains.yaml`
  stubs.
- Empty LangGraph skeleton (`orchestration/graph.py`, `orchestration/state.py`) with
  stub nodes that pass state through unchanged.

**Exit criterion:** `python -m orchestration.graph` runs end-to-end against dummy
state with no errors.

## Phase 1 — Single-source ingestion + retrieval
**Owner:** backend-engineer

- `ingestion/pubmed_connector.py`, `ingestion/chunker.py`, `ingestion/embedder.py`
  built fully against real PubMed data.
- `agents/retrievers/literature_retriever.py` implemented for real.
- No domain filtering yet (pass-through).

**Exit criterion:** asking a question returns real PubMed chunks with similarity
scores.

## Phase 2 — Multi-source + domain filtering
**Owner:** backend-engineer

- `ingestion/clinicaltrials_connector.py` and `ingestion/fda_connector.py` (FDA first —
  openFDA has the cleanest API of the regulatory sources).
- `domain/taxonomy.py`, `domain/routing.py`, and metadata-filtered retrieval wired
  across all three source types.

**Exit criterion:** a domain-scoped query (therapeutic area + jurisdiction) returns
correctly filtered results across literature, trials, and FDA regulatory sources.

## Phase 3 — Ranking + confidence scoring
**Owner:** backend-engineer

- `agents/evidence_ranker.py` (Haiku triage + Python dedup/clustering).
- `agents/confidence_scorer.py` with the weighted formula, reading
  `config/scoring_weights.yaml`.

**Exit criterion:** retrieved evidence comes back ranked with a numeric + rationale
confidence score per cluster (no synthesis yet).

## Phase 4 — Synthesis + citation binding + verification
**Owner:** backend-engineer

- `agents/synthesizer.py` with structured claim/citation output schema and
  retry-on-schema-violation.
- `agents/citation_binder.py` building the claim graph (`schemas/claim_graph.py`).
- `agents/verifier.py` with the groundedness recheck and the Verifier↔Synthesizer
  retry loop.

**Exit criterion:** the full pipeline produces a cited, confidence-scored,
self-verified answer end-to-end.

## Phase 5 — Demo UI + eval harness
**Owners:** frontend-engineer (UI) / backend-engineer (eval harness) — **run in
parallel**, since the UI only needs the stable `orchestration/graph.py` contract from
Phase 0–4, not a finished pipeline.

- frontend-engineer: `ui/app.py` (Streamlit) — domain selectors, streamed agent-trace
  view, cited-answer rendering, confidence panel, evidence explorer.
- backend-engineer: `eval/golden_set.jsonl`, `eval/retrieval_eval.py`,
  `eval/faithfulness_eval.py`, `eval/calibration_eval.py`, `eval/run_eval.py`. See
  [`evaluation.md`](evaluation.md).

**Exit criterion:** a demoable end-to-end POC with a measurable quality report.

## Phase 6 — Stretch
**Owner:** backend-engineer

- Remaining regulatory connectors: `ingestion/ema_connector.py`,
  `ingestion/ich_connector.py`, `ingestion/pmda_connector.py`,
  `ingestion/mhra_connector.py` (curated seed document sets given limited public
  APIs).
- Cross-jurisdiction comparison mode (relaxing the hard jurisdiction filter to a
  side-by-side view).
- Richer confidence-calibration analysis.

**Exit criterion:** all five regulatory jurisdictions have at least a seed corpus, and
a user can explicitly compare evidence across jurisdictions for one question.
