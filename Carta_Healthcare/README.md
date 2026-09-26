# Carta Healthcare

**Clinical data extraction and structuring from health records using Claude AI**

Automating extraction and structuring of clinical data from health records while maintaining 99% accuracy — **66% faster** than manual data entry.

## Overview

Carta Healthcare is a demonstration application that uses the Anthropic Claude API to extract and structure clinical information from unstructured health records (e.g., discharge summaries, progress notes). The application maintains a high accuracy threshold by:

1. Using Claude's structured-output API for deterministic JSON schema validation
2. Computing independent confidence flags to surface uncertain extractions
3. Measuring performance against a transparent manual-processing baseline

## Quick Start

### Installation

```bash
# Clone or navigate to the repository
cd /home/labuser/Downloads/Carta_Healthcare

# Install in development mode
pip install -e .

# Install test dependencies (optional)
pip install -e ".[dev]"
```

### Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Process Clinical Notes

```bash
# Process a directory of .txt notes
carta process fixtures/sample_notes output/

# Extract from a single note
carta extract-one fixtures/sample_notes/note_001.txt

# Output as JSON to stdout
carta extract-one <note_file>
```

### Run Tests

```bash
pytest tests/
```

### Evaluate Accuracy

```bash
# Requires ANTHROPIC_API_KEY set
carta evaluate-accuracy --gold-dir eval/gold_standard --out eval/results
```

### Benchmark Performance

```bash
# Requires ANTHROPIC_API_KEY set
carta benchmark --input-dir fixtures/sample_notes --baseline-minutes 8.0
```

### Start the API

```bash
carta serve --host 0.0.0.0 --port 8000
```

Then extract via HTTP:

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"note_text": "Patient is a 68-year-old male..."}'

# Health check
curl http://localhost:8000/health
```

## Data Flow

1. **Input**: Plain-text clinical notes (synthetic data, no real PHI)
2. **Extraction**: Claude API call with structured-output schema enforcement
3. **Validation**: Server-side schema validation (deterministic, no hallucinations)
4. **Confidence Flags**: Locally-computed confidence indicators
5. **Output**: Structured JSON records (one file per note)

## Architecture

- **`src/carta_healthcare/`**: Core application code
  - `extraction.py`: The shared pipeline used by CLI and API
  - `schema.py`: Pydantic data models
  - `client.py`: Anthropic API wrapper
  - `cli.py`: Command-line interface (Typer)
  - `api.py`: REST API (FastAPI)

- **`eval/`**: Accuracy measurement harness
  - `gold_standard/`: Hand-labeled test data
  - `evaluate_accuracy.py`: Scoring engine
  - `scoring.py`: Field-level matching logic

- **`benchmark/`**: Performance measurement harness
  - `benchmark.py`: Timing harness
  - `MANUAL_BASELINE.md`: Documented assumption

- **`tests/`**: Unit tests (mocked, no live API calls)

- **`docs/`**: Detailed architecture (HLD, LLD)

## Key Design Decisions

1. **Structured Output API**: Uses `messages.parse(output_format=...)` for deterministic schema validation server-side — no JSON parsing errors or hallucinations.

2. **Shared Core Module**: Both CLI and API call the same `extraction.py` module — no business-logic duplication.

3. **Confidence Flags**: Two independent layers (model self-report + locally-computed heuristics) surface extraction uncertainty for human review.

4. **Honest Measurement**: Accuracy and performance claims are backed by:
   - `eval/`: Gold-standard accuracy scoring
   - `benchmark/`: Timing against a clearly-documented manual baseline

5. **Synthetic Data Only**: All fixtures and gold-standard labels use obviously fabricated data — no real patient information.

## Documentation

- **`CLAUDE.md`**: Project conventions for Claude Code sessions
- **`docs/HLD.md`**: High-level architecture and design decisions
- **`docs/LLD.md`**: Low-level implementation details and API reference

## Accuracy & Performance

- **Target Accuracy**: 99% on structured field extraction (measured against gold standard)
- **Performance**: ~66% faster than estimated manual processing (8 min/record baseline)

See `eval/results/` and `benchmark/results/` for detailed reports after running the harnesses.

## Notes

- **No real data**: This is a demo/portfolio application using synthetic clinical notes.
- **Live API calls**: Accuracy and benchmark harnesses require a valid `ANTHROPIC_API_KEY`.
- **Costs money**: The evaluation and benchmark harnesses make real Claude API calls — run judiciously.

## License

Demo application for educational purposes.
