# Qualified_Health

**Tagline**: Identifying patients for life-saving treatments.

A simple prototype that screens large patient populations against fragmented medical records to surface candidates for evidence-based clinical interventions. Built on FastAPI + SQLite + pandas.

## Quick Start

```bash
pip install -r requirements.txt
./run.sh
# Loads sample data, runs screening pipeline, starts API on http://localhost:8000
# Access UI at http://localhost:8000/docs (FastAPI Swagger)
```

## Stack

- **Backend**: Python 3.9+, FastAPI, SQLite, pandas
- **Screening logic**: Rule-based, config-driven (YAML) — no ML, human-auditable
- **Data**: Fragmented synthetic source files (CSV/JSON) with inconsistent schemas, simulating real EHR integration challenges

## Architecture Primer

**Read these in order for context:**
1. [docs/HLD.md](docs/HLD.md) — Pipeline diagram, problem breakdown, design rationale
2. [docs/LLD.md](docs/LLD.md) — SQLite schema, API endpoints, tokenization algorithm, testing approach

**Key invariants** (every future edit must respect these):
- **Patient token immutability**: Once assigned, `patient_token` never changes — it's the canonical FK throughout the system. Raw identifiers are resolved once at ingestion; never re-derive the token.
- **PHI boundary**: Raw name/DOB/MRN live only in `patients` and `raw_records` tables. Rules engine, normalized fact tables, and API responses use `patient_token` only.
- **Rules are config, not code**: New interventions go in `rules/*.yaml`, not Python. New criterion *types* require a Python change in `rules_dsl.py`, but are rare.

## Project Layout

```
qualified_health/
  ├── main.py              # FastAPI app & routes
  ├── pipeline.py          # Orchestrates: ingest → identity → normalize → screen
  ├── identity.py          # Tiered record linkage (exact MRN → fuzzy name+DOB)
  ├── tokenizer.py         # Deterministic patient_token generation (SHA-256 hash)
  ├── schema.sql           # SQLite DDL
  ├── db.py                # DB connection & helpers
  └── ...                  # ingestion.py, normalization.py, rules_engine.py, etc.
rules/                      # Intervention definitions (YAML)
sample_data/
  ├── generate_sample_data.py
  └── source_{a,b,c}/      # Fake EHR source systems, inconsistent schemas
tests/
  ├── test_tokenizer.py, test_identity.py, test_rules_engine.py, etc.
```

## Running & Testing

```bash
# Run ingestion + screening (fills SQLite, outputs candidates)
curl -X POST http://localhost:8000/ingest
curl -X POST http://localhost:8000/screen

# Query results
curl http://localhost:8000/interventions
curl http://localhost:8000/candidates/statin_therapy

# Run tests
pytest
```

## Docs Reference

- **HLD**: Why identity resolution is split from tokenization, why rules are config-driven, how fragmented records are handled
- **LLD**: Full SQLite schema, tokenization algorithm, rules YAML shape, API endpoint specs, synthetic data generation, test cases
