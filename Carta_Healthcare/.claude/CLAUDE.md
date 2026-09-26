# Carta Healthcare

**Clinical data extraction and structuring from health records — 66% faster clinical data processing**

## Project Summary

A demonstration CLI + REST API application that uses Claude AI to extract structured clinical data from unstructured health records (e.g., discharge summaries) with 99% accuracy target. Synthetic test data only.

## Install & Run

```bash
# Install in development mode
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY

# Run tests (no API calls — all mocked)
pytest tests/

# Process notes (requires API key)
carta process fixtures/sample_notes output/

# Single extraction
carta extract-one <note_file>

# Start API server
carta serve

# Measure accuracy (requires API key, costs money)
carta evaluate-accuracy --gold-dir eval/gold_standard

# Benchmark performance (requires API key, costs money)
carta benchmark --input-dir fixtures/sample_notes
```

## Where Things Live

| Capability | File(s) |
|-----------|---------|
| Core extraction pipeline | `src/carta_healthcare/extraction.py` |
| Data schema | `src/carta_healthcare/schema.py` |
| Anthropic client | `src/carta_healthcare/client.py` |
| CLI | `src/carta_healthcare/cli.py` |
| REST API | `src/carta_healthcare/api.py` |
| Configuration | `src/carta_healthcare/config.py` |
| Confidence flags | `src/carta_healthcare/confidence.py` |
| IO utilities | `src/carta_healthcare/io_utils.py` |
| Prompts | `src/carta_healthcare/prompts.py` |
| Unit tests | `tests/` |
| Gold-standard accuracy data | `eval/gold_standard/` |
| Accuracy harness | `eval/evaluate_accuracy.py` |
| Accuracy scoring logic | `eval/scoring.py` |
| Performance benchmark harness | `benchmark/benchmark.py` |
| Manual baseline assumption | `benchmark/MANUAL_BASELINE.md` |
| HLD (architecture) | `docs/HLD.md` |
| LLD (implementation) | `docs/LLD.md` |

## Explicit Don'ts

1. **Do not hardcode API keys** — only read from `ANTHROPIC_API_KEY` env var.
2. **Do not duplicate extraction logic** between `cli.py` and `api.py` — both call `extraction.py`.
3. **Do not add a database or queue** without discussion — current design uses JSON files on disk.
4. **Do not use real PHI** in fixtures or gold-standard labels — only synthetic data.

## Key Modules

### `extraction.py` (THE shared core)
- `extract_record(note_text, *, source_file, settings, client=None)` → `ExtractionResult`
- `process_directory(input_dir, output_dir, settings, limit)` → list[ExtractionResult]

### `schema.py`
- `ClinicalRecordExtraction` — what Claude produces
- `ClinicalRecord` — extraction + metadata (what gets persisted)

### `client.py`
- `get_client(settings)` → Anthropic client
- `call_claude_for_extraction(client, prompt, settings)` → ClinicalRecordExtraction (parsed)

### `confidence.py`
- `compute_confidence_flags(extraction)` → list[str]

### `cli.py`
Commands: `process`, `extract-one`, `evaluate-accuracy`, `benchmark`, `serve`

### `api.py`
Endpoints: `POST /extract`, `GET /health`

## Testing

- Unit tests are **fast, free, deterministic** — mocks the Anthropic client completely
- Accuracy and benchmark harnesses are **separate**, **on-demand**, **cost real API calls**
- Never wire eval/benchmark into pytest or CI default runs

## Configuration

Set via environment variables (or `.env` file):
- `ANTHROPIC_API_KEY` — required, never hardcoded
- `CARTA_MODEL` — default `claude-sonnet-5`
- `CARTA_MAX_RETRIES` — default `4`
- `CARTA_TIMEOUT_SECONDS` — default `30`

## Gold Standard (eval/)

Hand-authored test set: `eval/gold_standard/notes/*.txt` + `eval/gold_standard/labels/*.json`.

Run `carta evaluate-accuracy` to score extraction against these labels using fuzzy matching (difflib, 85% threshold) for string fields and greedy list-matching for diagnoses/medications/vitals/labs.

## Benchmark (benchmark/)

Assumes `MANUAL_BASELINE_MINUTES_PER_RECORD = 8.0` (documented in `MANUAL_BASELINE.md`).

Measures end-to-end automated time (load → prompt → API → validate → write) and reports `pct_faster` vs. baseline.

## Documentation Structure

- **CLAUDE.md** (this file) — quick reference for sessions
- **docs/HLD.md** — architecture, motivation, non-functional requirements
- **docs/LLD.md** — schema, function signatures, CLI/API reference, scoring algorithm
