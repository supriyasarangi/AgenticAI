# Non-Functional Requirements

## Deployment & runtime

- **Local-first.** Runs on a single developer machine; no cloud infrastructure
  required. Vector store (Chroma) and raw data are local files under `data/`.
- **Offline-repeatable ingestion.** Once a source is fetched into `data/raw/<source>/`,
  chunking/embedding/indexing can be re-run without network access, so demos don't
  depend on live API availability at presentation time.
- **Single local user.** No authentication, no multi-tenancy, no session isolation
  between users. This is explicitly deferred — see [`requirements.md`](requirements.md)
  "Out of scope."
- **Demo-grade latency, not an SLA.** A query may take tens of seconds (multiple LLM
  calls across the pipeline, including the Opus verification step). This is acceptable
  for a research-assistant tool; it is not designed for interactive sub-second use.

## Explainability & auditability

- **Confidence scores must be inspectable, not black-box.** The scoring formula and its
  weights live in a plain YAML config (`config/scoring_weights.yaml`) and the authority
  tier table (`domain/authority_tiers.py`) — both readable and editable without touching
  agent prompts. See [`architecture.md`](architecture.md) §4.
- **Every claim graph is persisted** (`data/claim_graphs/`), so any answer given during
  a demo or review can be replayed and audited after the fact — this is a POC
  requirement precisely because it costs little now and is expensive to retrofit later.
- **No silent claim removal.** A claim that fails verification is shown as "Unverified"
  with a reason, never dropped without a trace.

## Extensibility (design now, build later)

The architecture is intentionally interface-based in a few places specifically so
production concerns can be added without a rewrite:

- `Embedder` interface (`ingestion/embedder.py`) — the local `sentence-transformers`
  model can be swapped for a hosted embedding API later.
- `ingestion/base_connector.py` — new source types (e.g. internal ELN data, patents)
  can be added as new connectors without touching the pipeline.
- Vector store access is isolated in `ingestion/vector_store.py` — Chroma could be
  swapped for a managed vector DB without changing retriever logic.
- The LangGraph pipeline in `orchestration/graph.py` is the only integration point the
  UI depends on, so a future FastAPI multi-client layer can wrap it without touching
  `ui/app.py`'s logic (it would simply call the API instead of the graph directly).

## Data handling

- All source content at POC scale is **public**: published literature, public trial
  registry entries, and public regulatory documents. No PHI/PII is expected.
- **Re-check required before scaling.** If real (non-public) trial data, internal study
  reports, or any patient-level data is ever ingested, this assumption must be
  revisited — data classification, access control, and retention policy would all need
  to be defined before that ingestion happens. This is flagged here specifically so it
  isn't quietly assumed away when the system grows beyond the POC.

## Cost

- Model tiering (Haiku for triage/tagging, Sonnet for planning/synthesis, Opus only for
  verification) plus prompt caching on the evidence bundle are the primary cost
  controls — see [`architecture.md`](architecture.md) §0. No separate cost budget is
  enforced at the POC stage, but the tiering choice should keep per-query cost
  reasonable for demo-volume usage.
