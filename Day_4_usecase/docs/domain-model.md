# Domain Model

Every query is scoped along two independent axes: **therapeutic area** and
**regulatory jurisdiction**. Both are first-class metadata fields attached to every
ingested chunk at ingestion time (not inferred at query time) — see
[`architecture.md`](architecture.md) §3.

## Therapeutic area

Initial controlled vocabulary (`domain/taxonomy.py`), deliberately small and extensible:

| Value | Notes |
|---|---|
| `oncology` | |
| `cardiology` | |
| `neurology` | |
| `immunology` | |
| `infectious_disease` | |
| `rare_disease` | often cross-cuts the others; treated as its own selectable area for POC simplicity |

Auto-tagging at ingestion uses MeSH terms (for PubMed/PMC) or condition fields
(for ClinicalTrials.gov) mapped to this vocabulary via a small keyword/MeSH lookup
table. Regulatory documents without structured metadata (most guidance PDFs) are
tagged by an LLM-assisted classification pass (Haiku 4.5) at ingestion time, not at
query time — so retrieval filtering stays a cheap metadata lookup, not a per-query
LLM call.

## Regulatory jurisdiction

| Value | Authority tier (see below) | Ingestion connector(s) |
|---|---|---|
| `FDA` (United States) | 1.0 | `ingestion/fda_connector.py` |
| `EMA` (European Union) | 1.0 | `ingestion/ema_connector.py` |
| `ICH` (International harmonization guidelines) | 1.0 | `ingestion/ich_connector.py` |
| `PMDA` (Japan) | 1.0 | `ingestion/pmda_connector.py` |
| `MHRA` (United Kingdom) | 1.0 | `ingestion/mhra_connector.py` |
| `GLOBAL` (default for literature/trials with no jurisdiction-specific registration) | n/a (not regulatory tier) | — |

Literature and clinical-trial chunks are tagged `jurisdiction=GLOBAL` unless the trial
is explicitly registered under a region-specific framework (e.g. an EU CTR trial is
tagged `EMA`).

**ICH special case**: ICH guidelines are harmonization documents relevant across all
regions. When a user selects any jurisdiction other than "compare jurisdictions" mode,
ICH guidance is still included in retrieval alongside the selected jurisdiction's own
documents — encoded in `domain/routing.py` as an always-include rule, not a user toggle.

## How domain selection drives retrieval

1. UI collects `(therapeutic_area, jurisdiction)` as a required tuple per query.
2. `domain/routing.py` maps `jurisdiction` to the set of regulatory connectors/indices
   that are even eligible to be queried (e.g. `jurisdiction=PMDA` → only the PMDA index,
   plus ICH per the special case above).
3. The vector store query applies a **hard metadata pre-filter** (`where` clause) on
   `therapeutic_area` and `jurisdiction` before similarity search runs — this is a
   filter, not a soft re-rank, so out-of-scope chunks are never candidates, regardless
   of how similar their embedding is.
4. Literature and clinical-trial retrieval use `therapeutic_area` as the filter and
   generally ignore `jurisdiction` (unless jurisdiction-specific trial registries
   matter to the question), while regulatory retrieval uses both.

## Source authority tiers

Used by the Confidence Scorer (see [`architecture.md`](architecture.md) §5). A fixed,
inspectable lookup table in `domain/authority_tiers.py`:

| Source type | Tier weight |
|---|---|
| Regulatory (FDA/EMA/ICH/PMDA/MHRA) | 1.00 |
| Peer-reviewed literature | 0.75 |
| Clinical trial registry entries | 0.65 |
| Preprints | 0.40 |

This table is deliberately a plain, editable config, not a value buried in a prompt —
an R&D reviewer challenging a confidence score should be able to see exactly which
tier weight was applied and why.
