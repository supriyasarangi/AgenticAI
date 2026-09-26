# Architecture

## 0. Design philosophy for this POC

- **Orchestration stays simple and inspectable.** With ~8 pipeline stages, a heavyweight
  multi-agent framework (CrewAI, AutoGen) adds abstraction cost without payoff.
  **LangGraph** is used instead: a typed state graph with conditional edges (for
  domain routing and retry-on-low-confidence loops), built-in checkpointing (useful for
  showing an R&D audience *why* an answer was produced), and it composes cleanly with
  plain Anthropic SDK calls per node. A hand-rolled state machine was considered and
  rejected only because LangGraph's graph visualization/replay is worth the small extra
  dependency for a demo audience.
- **Model tiering** keeps cost proportional to judgment required:
  - **Sonnet 5** (`claude-sonnet-5`) — default workhorse: query planning, per-source
    query rewriting, evidence-ranking rationale, synthesis.
  - **Opus 5** (`claude-opus-5`) — reserved for the Verifier/self-critique step, the one
    place where catching an unsupported or overconfident claim matters more than
    marginal cost.
  - **Haiku 4.5** (`claude-haiku-4-5`) — cheap, high-volume, low-judgment sub-tasks:
    ingestion-time metadata tagging, chunk-level relevance triage before the more
    expensive ranker, JSON-shape normalization.
  - All nodes use `thinking: {type: "adaptive"}` with `output_config.effort` tuned per
    role (`low` for Haiku triage, `medium`/`high` for Sonnet planning/synthesis,
    `high`/`xhigh` for the Opus critique step).
- **Prompt caching** is architectural, not just cost-saving: every synthesis/critique
  call re-sends the same retrieved-evidence bundle. Prompts are structured so the
  system prompt + tool definitions + the fixed evidence bundle come first with a
  `cache_control: {type: "ephemeral"}` breakpoint, and the volatile part (the specific
  claim being checked) comes last. This matters most for the Verifier, which may
  recheck multiple claims against the same evidence set in a loop.

## 1. Pipeline topology

Implemented as a LangGraph `StateGraph` over a shared `RAGState` (Pydantic) carrying:
original query, domain selection, decomposed sub-questions, retrieved chunks per source
(with metadata + similarity scores), ranked/filtered evidence, per-claim confidence
scores, synthesized answer with citation bindings, and verification results.

```
Query Planner
     │
     ├──▶ Literature Retriever ──┐
     ├──▶ Clinical Trials Retriever ──┤──▶ Evidence Ranker/Dedup ──▶ Confidence Scorer
     └──▶ Regulatory Retriever ──┘                                        │
                                                                            ▼
                                                                      Synthesizer
                                                                            │
                                                                            ▼
                                                                    Citation Binder
                                                                            │
                                                                            ▼
                                                                        Verifier ──┐
                                                                            │      │ (retry on
                                                                            ▼      │  failed claim,
                                                                  Response Composer │  bounded N)
                                                                                    │
                                                                    (loops back to Synthesizer)
```

1. **Query Planner** (`agents/query_planner.py`, Sonnet 5) — takes the raw question +
   domain selection, decomposes into 1–4 retrieval sub-queries, tags each with which
   source types are relevant (e.g. "what does the FDA label say about X" → regulatory
   only; "efficacy in trials" → clinical-trials + literature). Outputs a `RetrievalPlan`.
2. **Multi-source retrievers** (parallel fan-out):
   - `agents/retrievers/literature_retriever.py`
   - `agents/retrievers/clinical_trials_retriever.py`
   - `agents/retrievers/regulatory_retriever.py`
   Each queries the vector store with domain-filtered metadata (per
   [`domain-model.md`](domain-model.md)) plus the sub-query embedding, returning top-k
   chunks with similarity scores and full metadata.
3. **Evidence Ranker / Filter** (`agents/evidence_ranker.py`) — Haiku 4.5 does a cheap
   relevance-triage pass (drop obviously irrelevant chunks), then pure-Python
   cross-source deduplication/clustering groups chunks making the same underlying claim
   across sources, for corroboration counting.
4. **Confidence Scorer** (`agents/confidence_scorer.py`) — deterministic Python
   function, not an LLM call (see §5), applied per candidate evidence cluster.
5. **Synthesizer** (`agents/synthesizer.py`, Sonnet 5) — given ranked, scored evidence,
   produces the answer as claim-tagged sentences. Structured output (tool-call schema)
   forces every sentence to cite one or more `chunk_id`s; a sentence with no citation
   fails schema validation and triggers regeneration before it ever reaches the
   Verifier.
6. **Citation Binder** (`agents/citation_binder.py`) — pure Python: resolves each
   `chunk_id` into full provenance and builds the `ClaimGraph` (see §6).
7. **Verifier** (`agents/verifier.py`, Opus 5) — rereads each claim against *only its
   bound cited chunks* (not the whole evidence pool) and checks: (a) is the claim
   actually supported by the cited text, (b) is the confidence label consistent with
   evidence tier/corroboration, (c) do retrieved-but-unused chunks contradict it. On
   failure, a conditional edge routes back to the Synthesizer with a critique note, up
   to N retries; otherwise the claim is flagged "Unverified" rather than dropped.
8. **Response Composer** (`agents/response_composer.py`) — pure Python; assembles the
   final answer with inline citation markers and a confidence/sources panel.

`orchestration/graph.py` defines the graph, edges, and the Verifier↔Synthesizer retry
loop. `orchestration/state.py` defines `RAGState`.

## 2. Domain & jurisdiction routing

See [`domain-model.md`](domain-model.md) for the full taxonomy. Implementation:
`domain/taxonomy.py` (therapeutic-area vocabulary + MeSH mapping),
`domain/routing.py` (jurisdiction → connector routing, ICH always-include rule),
`domain/authority_tiers.py` (source tier weights). Filtering is a hard metadata
pre-filter at the vector-store query level (Chroma `where` clause), not a soft re-rank.

## 3. Multi-source ingestion design

Common pattern for every connector: fetch → parse → chunk → tag metadata → embed →
upsert. All connectors implement a shared interface in `ingestion/base_connector.py`
(`fetch(query_or_id) -> List[RawDocument]`, `to_chunks(doc) -> List[Chunk]`).

| Source | Module | API / method | Metadata captured |
|---|---|---|---|
| PubMed/PMC + preprints | `ingestion/pubmed_connector.py` | NCBI E-utilities (esearch+efetch, XML); bioRxiv/medRxiv API for preprints | source_type=literature, pmid/doi, title, journal, pub_date, mesh_terms, authors, is_preprint |
| Clinical trials | `ingestion/clinicaltrials_connector.py` | ClinicalTrials.gov API v2 (JSON) | source_type=clinical_trial, nct_id, phase, status, condition(s), sponsor, jurisdiction, dates |
| FDA labels & guidances | `ingestion/fda_connector.py` | openFDA API + FDA guidance index | source_type=regulatory, jurisdiction=FDA, doc_type, application_number, approval_date |
| EMA CHMP opinions | `ingestion/ema_connector.py` | EMA public document listings (curated scrape — no clean public API) | jurisdiction=EMA, doc_type=chmp_opinion, product_name, opinion_date |
| ICH guidelines | `ingestion/ich_connector.py` | ICH website document listing (scrape) | jurisdiction=ICH, doc_type=guideline, ich_code |
| PMDA / MHRA docs | `ingestion/pmda_connector.py`, `ingestion/mhra_connector.py` | PMDA English portal / MHRA GOV.UK publications (curated seed set for POC) | jurisdiction=PMDA or MHRA, doc_type, publication_date |

Shared downstream steps:
- `ingestion/chunker.py` — recursive token chunking (~500–800 tokens, with overlap),
  assigns a stable `chunk_id` (hash of doc_id + offset), preserves exact character span
  for citation.
- `ingestion/metadata_tagger.py` — Haiku 4.5-assisted therapeutic-area classification
  when structured metadata (MeSH terms) is absent, e.g. regulatory PDFs; attaches
  `therapeutic_area`, `jurisdiction`, `doc_type`, `source_authority_tier`,
  `publication_date` to every chunk before embedding.
- `ingestion/embedder.py` — local `sentence-transformers` model (e.g.
  `bge-small-en-v1.5`), avoiding a paid embedding API and keeping ingestion
  offline-repeatable. Swappable behind an `Embedder` interface.
- `ingestion/vector_store.py` — wraps Chroma (persistent local client); stores chunk
  text + embedding + full metadata; supports metadata-filtered similarity search.
- CLI entrypoint `ingestion/run_ingestion.py --source pubmed --query "..." --therapeutic-area oncology`
  populates the index incrementally per demo scenario rather than requiring a full
  bulk crawl.

## 4. Confidence scoring

`agents/confidence_scorer.py` computes a deterministic, explainable composite per
claim/evidence cluster — computed in Python, not by LLM judgment, so it's auditable:

```
confidence = w1*retrieval_similarity
           + w2*source_authority_tier
           + w3*corroboration_count
           + w4*recency_score
           + w5*llm_consistency_check
```

- **retrieval_similarity** — normalized cosine similarity of the best-matching chunk(s).
- **source_authority_tier** — from `domain/authority_tiers.py` (see
  [`domain-model.md`](domain-model.md)).
- **corroboration_count** — number of independent sources (deduplicated at the Evidence
  Ranker stage) making the same claim, log-scaled and capped.
- **recency_score** — decay function on publication/approval date; half-life
  configurable per source type.
- **llm_consistency_check** — binary/graded signal (0, 0.5, 1) from the Verifier's
  groundedness check (§1 step 7).

Weights (`w1..w5`) live in `config/scoring_weights.yaml` — tunable/inspectable without
code changes, since reviewers will ask "why is this 72% and not 90%." Output is both a
numeric score and a **template-filled rationale string** (e.g. "Corroborated by 3
sources including 1 FDA label; based on peer-reviewed literature from 2023–2024;
verification check passed") — not free-form LLM text, so the explanation is traceable
to the same inputs as the number. Scores are surfaced as a tier (High/Medium/Low/
Unverified), not a raw float.

## 5. Citation / provenance tracing

- Every chunk carries immutable lineage: `document_id → source_url/DOI/NCT/application_number
  → jurisdiction/doc_type → char_offset_start/end`.
- The Synthesizer's structured output is a list of `{sentence, cited_chunk_ids: [...]}`
  objects; empty citation lists are rejected and regenerated before reaching the
  Verifier (§1 step 5).
- `agents/citation_binder.py` builds a **claim graph**:
  `Claim (sentence) → Evidence (chunk_id, exact span, similarity score) → Document (title,
  authors/sponsor, date, doc_type) → Source (URL/DOI/registry ID, jurisdiction)`.
  Defined as a Pydantic model in `schemas/claim_graph.py`, persisted as JSON per answer
  in `data/claim_graphs/` — this is what lets the UI's evidence explorer highlight the
  exact source passage behind any claim.
- The Verifier's groundedness check operates directly on this graph, scoped to only the
  bound chunks — cheap and precise rather than a vague re-summarization.
- Final rendering always shows inline numbered citations mapped to a reference list
  with full source metadata + confidence tier. No claim renders without at least one
  resolvable citation; unverified claims are visually flagged, never silently removed.

## 6. Tech stack

- **Python 3.11+**
- **Orchestration**: LangGraph for the agent state machine; plain `anthropic` Python
  SDK for all model calls (no LangChain LLM wrapper, to keep Anthropic-specific
  features — structured outputs, prompt caching — directly accessible).
- **LLM**: Anthropic API, Sonnet 5 / Opus 5 / Haiku 4.5 per §0.
- **Vector DB**: Chroma (persistent local client) — native metadata filtering, lowest
  friction for a local POC. LanceDB is a reasonable alternative if columnar/file-based
  storage is preferred later.
- **Embeddings**: local `sentence-transformers` (e.g. `bge-small-en-v1.5`).
- **Ingestion HTTP**: `httpx`/`requests`, `biopython.Entrez` (optional, for E-utilities)
  for PubMed; `requests` + `BeautifulSoup`/`lxml` for regulatory-listing scraping.
- **Schemas**: Pydantic v2 throughout (`RAGState`, `Chunk`, `ClaimGraph`,
  `ConfidenceScore`).
- **Demo UI**: Streamlit (`ui/app.py`) — domain selectors, streamed agent-step trace
  (fits LangGraph's streaming), final answer with inline citations and confidence
  panel, evidence-explorer tab. No separate API layer for a single-user local demo; a
  FastAPI wrapper (`api/main.py`) around `orchestration/graph.py` is a clean later
  addition if multi-client use is needed, but out of scope for v1.
- **Config**: `config/scoring_weights.yaml`, `config/domains.yaml`, `.env` for
  `ANTHROPIC_API_KEY`.

## 7. Storage layout

```
data/
  raw/<source>/          # fetched raw documents per connector
  chroma/                 # persistent vector store
  claim_graphs/           # per-answer JSON, for demo replay/audit
```

## 8. Implementation ownership

Build work is split across two project-scoped subagents (see
`.claude/agents/backend-engineer.md` and `.claude/agents/frontend-engineer.md`):

- **backend-engineer** owns `ingestion/`, `agents/`, `orchestration/`, `domain/`,
  `config/`, `schemas/`, `eval/` — everything in §1–§5 above.
- **frontend-engineer** owns `ui/` — consumes `orchestration/graph.py` as its only
  contract with the backend (input: query + domain selection; output: streamed
  `RAGState` updates and the final composed answer). It never reaches into pipeline
  internals.

This split is what lets Phase 5 in [`units-of-work.md`](units-of-work.md) run UI and
eval-harness work in parallel once the graph's I/O contract is stable.
