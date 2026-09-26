# Carta Healthcare — High-Level Design

## Executive Summary

Carta Healthcare is a demonstration application that automates extraction and structuring of clinical data from unstructured health records using the Anthropic Claude API. The system is designed to measure and demonstrate **99% accuracy** on structured field extraction and **66% faster** performance than manual data entry (against an 8 minute/record baseline assumption).

## Motivation & Claims

### Marketing Claims
- **99% Accuracy**: Targets near-perfect extraction of structured clinical fields against a hand-labeled gold-standard test set
- **66% Faster**: Completes per-record extraction in ~2.7 seconds vs. ~8 minutes manual estimate

### How We Measure (Not Assert)
- **Accuracy**: `eval/evaluate_accuracy.py` runs live Claude extractions against 10-20 hand-labeled gold-standard notes, scoring field-by-field (scalar exact/fuzzy match, lists via greedy alignment). Reports overall % and per-field breakdown.
- **Speed**: `benchmark/benchmark.py` times end-to-end pipeline (load → prompt → API call → validate → write), reports mean/median/p95 seconds/record, and computes `pct_faster` vs. a documented `MANUAL_BASELINE_MINUTES_PER_RECORD` constant.

Neither number is hardcoded or tuned — they reflect actual measurements.

## System Context

```
┌────────────────────────────────────────────────────────────┐
│                   End Users                                │
│  (Data Scientists, Healthcare Orgs, ML Researchers)        │
└────────────┬────────────────────────────────┬──────────────┘
             │                                │
      ┌──────▼──────┐                 ┌──────▼──────┐
      │ CLI          │                │ REST API     │
      │ (Typer)      │                │ (FastAPI)    │
      └──────┬──────┘                 └──────┬──────┘
             │                                │
             └────────────┬───────────────────┘
                          │
            ┌─────────────▼─────────────┐
            │  Core Pipeline            │
            │ (extraction.py)           │
            │  - Claude API call        │
            │  - Schema validation      │
            │  - Confidence flagging    │
            └─────────────┬─────────────┘
                          │
            ┌─────────────▼─────────────┐
            │ Storage                   │
            │ (JSON files on disk)      │
            └───────────────────────────┘

Alongside:
  - eval/evaluate_accuracy.py (gold-standard scoring)
  - benchmark/benchmark.py (timing harness)
```

## Data Flow

```
Clinical Note (.txt)
       │
       ▼
   Load Text
       │
       ▼
  Build Prompt
       │
       ▼
  Claude API (messages.parse)
       │
       ├──── Already Schema-Validated ────┐
       │                                   │
       ▼                                   ▼
  Compute Confidence Flags      ExtractionMetadata
       │                                   │
       └──────────────┬────────────────────┘
                      │
                      ▼
              ClinicalRecord
              (data + metadata)
                      │
                      ▼
              Write JSON to Disk
```

## Architecture Overview

### 1. Core Components

| Component | Purpose |
|-----------|---------|
| **CLI (Typer)** | User-friendly command-line interface for batch processing, single extractions, eval, benchmark |
| **REST API (FastAPI)** | Lightweight HTTP interface for integration; shares core pipeline with CLI |
| **Core Pipeline (extraction.py)** | THE shared business logic — called by both CLI and API, never duplicated |
| **Anthropic Client Wrapper (client.py)** | Single call site for Claude API, error mapping, retry handling |
| **Schema (Pydantic)** | Type-safe data contracts; `output_format=` drives server-side validation |
| **Storage (JSON files)** | Simple, inspectable, version-control friendly |

### 2. Accuracy Measurement (eval/)

- **Gold Standard**: 10-20 hand-authored synthetic notes + labels in `eval/gold_standard/`
- **Scoring** (`scoring.py`):
  - Flatten records to dotted field paths
  - Scalar fields: exact match or fuzzy match (difflib, 85% threshold)
  - List fields (diagnoses/meds/vitals/labs): greedy best-match pairing, then precision/recall/F1
- **Harness** (`evaluate_accuracy.py`): Runs live extraction against gold set, aggregates metrics, validates confidence-flag mechanism
- **Output**: JSON report + printed summary

### 3. Performance Measurement (benchmark/)

- **Manual Baseline**: 8 minutes/record (documented assumption, not hardcoded)
- **Harness** (`benchmark.py`): Times full per-record pipeline on a sample set, reports mean/median/p95, computes `pct_faster`
- **Output**: JSON report + printed summary with speedup %

### 4. Confidence Mechanism

Two independent layers surface extraction uncertainty:
1. **Model Self-Report**: `low_confidence_fields` list in extraction (weak signal alone)
2. **Local Heuristics** (`confidence.py`): rules like `no_diagnoses_found`, `implausible_age`, `no_encounter_date` (rules don't know what the model knows, so divergence is meaningful)

Both flagged together in `ExtractionMetadata.confidence_flags` for downstream triage.

## Non-Functional Requirements

### Security & Privacy
- **No Real PHI**: All fixtures and gold-standard data are synthetic — no actual patient information
- **API Key Handling**: Only via `ANTHROPIC_API_KEY` env var, never hardcoded, never logged
- **Input Validation**: Length limits, empty-string rejection

### Performance
- **Latency**: One synchronous Claude API call per record; no queueing or batching (by design, keeps it simple)
- **Throughput**: Depends on Claude API latency + network

### Reliability
- **Graceful Failure**: One bad record doesn't crash batch; collects results and reports success/failure counts
- **Determinism**: `messages.parse(output_format=...)` guarantees schema-valid output or raises exception — no JSON parsing errors

### Simplicity
- **No Database**: JSON files on disk
- **No Authentication**: CLI/API open, no tokens
- **No Message Queue**: Synchronous per-record processing
- **Minimal Dependencies**: Anthropic SDK, Pydantic, Typer, FastAPI, Uvicorn

## Explicit Non-Goals

- **Real-time streaming**: Single sync API call per record
- **High-volume multi-tenant SaaS**: Demo app, synthetic data
- **Advanced search/analytics**: JSON files are read-only by external tools
- **Offline/local LLM**: Uses Claude API explicitly for reproducibility and accuracy

## Key Architectural Decisions

### 1. Structured Output API (`messages.parse(output_format=...)`)
**Decision**: Use server-side schema enforcement instead of asking Claude for JSON and parsing manually.

**Rationale**: 
- Deterministic output structure
- Server validates before returning
- No hallucinated extra fields or type mismatches
- No retry-on-parse-error complexity

**Trade-off**: Requires exact Pydantic schema match on client; less flexible if schema needs frequent tweaks.

### 2. Shared Core Module (`extraction.py`)
**Decision**: Both CLI and API import and call the same `extract_record()` and `process_directory()` functions.

**Rationale**:
- Zero business-logic duplication
- Bug fixes/enhancements automatically available to both interfaces
- Easier to test (one code path, not two)

**Trade-off**: CLI and API must share function signatures and error handling.

### 3. Two-Layer Confidence Flagging
**Decision**: Model self-report + locally-computed heuristics, both persisted.

**Rationale**:
- Model confidence alone is weak signal (can be wrong without knowing)
- Heuristics are independent, so agreement/disagreement is informative
- Downstream consumers (e.g., QA review) can triage based on flags

**Trade-off**: Adds complexity; requires maintaining two flag sets in sync.

### 4. JSON Files, Not Database
**Decision**: Each extracted record written as standalone JSON file to disk.

**Rationale**:
- Zero schema-migration complexity
- Files are diff-able, version-control friendly
- Trivial to inspect/debug individual records
- Suitable for demo/batch processing

**Trade-off**: No structured query support; scaling to millions of records would need a DB layer.

### 5. Documented, Not Hardcoded, Performance Baseline
**Decision**: `MANUAL_BASELINE_MINUTES_PER_RECORD` is a documented assumption in `benchmark/MANUAL_BASELINE.md`, not a magic constant.

**Rationale**:
- Forces honesty about the "66% faster" claim
- Readers can audit/dispute the baseline assumption
- Measured speedup is testable, not tuned

**Trade-off**: Requires maintaining a separate markdown file; slightly more work to change baseline.

## Data Schema

### ClinicalRecordExtraction (what Claude produces)
```
{
  patient: {
    age: int | null,
    sex: "male" | "female" | "other" | "unknown" | null,
    mrn: str | null  (synthetic identifier only)
  },
  encounter: {
    encounter_type: str | null,
    date: str | null,
    provider: str | null,
    facility: str | null,
    chief_complaint: str | null
  },
  diagnoses: [
    {
      description: str,        (required)
      icd10_code: str | null,
      status: str | null
    }
  ],
  medications: [
    {
      name: str,               (required)
      dosage: str | null,
      frequency: str | null,
      route: str | null
    }
  ],
  vitals: [
    {
      name: str,               (required)
      value: str,
      unit: str | null
    }
  ],
  labs: [
    {
      test_name: str,          (required)
      value: str,
      unit: str | null,
      reference_range: str | null,
      abnormal_flag: bool | null
    }
  ],
  low_confidence_fields: [str]  (model self-report)
}
```

### ClinicalRecord (what gets persisted)
```
{
  data: ClinicalRecordExtraction,
  extraction_metadata: {
    source_file: str,
    model_used: str,
    extracted_at: datetime,
    confidence_flags: [str]   (locally computed)
  }
}
```

## Error Handling

| Error Type | Handling |
|-----------|----------|
| Empty note text | Return failure result, don't call API |
| API key missing | Fail at startup (env var resolution) |
| Rate limit (429) | SDK retries; if exhausted, return failure result |
| Server error (5xx) | SDK retries; if exhausted, return failure result |
| Client error (4xx) | Return failure result (non-retryable) |
| Refusal (stop_reason="refusal") | Return failure result |
| Malformed response | Caught by `output_format=` validation; if somehow invalid, wrapped as failure result |
| File I/O error | Return failure result for that record, continue batch |

## Limitations & Caveats

1. **Small Gold Standard**: 10-20 notes is enough for a demo; production accuracy claims would need 100+ diverse examples.
2. **Synthetic Data**: No exposure to real messy clinical notes; actual accuracy may differ.
3. **LLM Latency Variance**: Claude API response times vary; benchmark timing is illustrative, not deterministic.
4. **Manual Baseline Assumption**: 8 min/record is an illustrative estimate, not a peer-reviewed time-motion study.
5. **No Real PHI**: Deliberately limited scope — no actual patient information anywhere.

## Future Extensions

- Streaming responses for large notes
- Batch API endpoint for multiple notes
- Database backend for structured queries
- Fine-tuned smaller model for cost/latency optimization
- Web UI for manual review of confidence-flagged records
- Integration with EHR systems
