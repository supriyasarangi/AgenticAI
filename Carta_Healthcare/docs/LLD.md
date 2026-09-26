# Carta Healthcare — Low-Level Design

## Implementation-Level Details

This document provides concrete function signatures, schema definitions, API endpoints, and algorithms for implementers or future maintainers.

## Directory Structure & Responsibilities

```
Carta_Healthcare/
├── pyproject.toml              # Package metadata, dependencies
├── .env.example                # Environment variable template
├── CLAUDE.md                   # Quick reference for Claude Code sessions
├── README.md                   # User-facing introduction
├── src/carta_healthcare/
│   ├── __init__.py             # Package marker
│   ├── config.py               # Settings class, env var loading
│   ├── schema.py               # Pydantic models (5 domain + 2 wrapper)
│   ├── prompts.py              # SYSTEM_PROMPT, build_extraction_prompt()
│   ├── client.py               # Anthropic client wrapper, error types
│   ├── extraction.py           # Core pipeline: extract_record(), process_directory()
│   ├── confidence.py           # compute_confidence_flags()
│   ├── io_utils.py             # load_note(), write_record(), list_note_files()
│   ├── cli.py                  # Typer CLI app, 5 commands
│   └── api.py                  # FastAPI app, 2 endpoints
├── eval/
│   ├── gold_standard/
│   │   ├── notes/              # 10-20 synthetic .txt clinical notes
│   │   └── labels/             # Hand-authored ClinicalRecordExtraction JSON
│   ├── scoring.py              # flatten_record(), fuzzy_match(), match_lists(), accuracy functions
│   └── evaluate_accuracy.py    # Main harness: run_evaluation()
├── benchmark/
│   ├── MANUAL_BASELINE.md      # Documents MANUAL_BASELINE_MINUTES_PER_RECORD = 8.0
│   └── benchmark.py            # Main harness: run_benchmark()
├── fixtures/sample_notes/      # Larger set of synthetic notes for demoing CLI
├── tests/
│   ├── test_schema.py          # Pydantic model validation, JSON round-trip
│   ├── test_extraction.py      # extract_record() with mocked client
│   ├── test_confidence.py      # compute_confidence_flags()
│   ├── test_cli.py             # Typer CliRunner tests
│   └── test_api.py             # FastAPI TestClient tests
├── output/                     # .gitignored; default destination for `process`
└── docs/
    ├── HLD.md                  # Architecture and design rationale
    └── LLD.md                  # This file
```

## Core Modules

### 1. config.py

```python
class Settings(BaseModel):
    anthropic_api_key: str  # from ANTHROPIC_API_KEY env var (default "")
    model: str              # from CARTA_MODEL env var (default "claude-sonnet-5")
    max_retries: int        # from CARTA_MAX_RETRIES env var (default 4)
    timeout_seconds: int    # from CARTA_TIMEOUT_SECONDS env var (default 30)

def load_settings() -> Settings:
    """Load settings from environment."""
```

### 2. schema.py

All models are Pydantic v2, JSON-serializable.

#### Enums
```python
class Sex(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"
```

#### Domain Models
```python
class PatientDemographics(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=130)
    sex: Optional[Sex] = None
    mrn: Optional[str] = None

class EncounterInfo(BaseModel):
    encounter_type: Optional[str] = None
    date: Optional[str] = None
    provider: Optional[str] = None
    facility: Optional[str] = None
    chief_complaint: Optional[str] = None

class Diagnosis(BaseModel):
    description: str                    # Required
    icd10_code: Optional[str] = None
    status: Optional[str] = None

class Medication(BaseModel):
    name: str                           # Required
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None

class VitalSign(BaseModel):
    name: str                           # Required
    value: str                          # Required
    unit: Optional[str] = None

class LabResult(BaseModel):
    test_name: str                      # Required
    value: str                          # Required
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[bool] = None
```

#### Wrapper Models
```python
class ClinicalRecordExtraction(BaseModel):
    """Exactly what Claude produces. Passed to output_format=."""
    patient: PatientDemographics
    encounter: EncounterInfo
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    vitals: list[VitalSign] = Field(default_factory=list)
    labs: list[LabResult] = Field(default_factory=list)
    low_confidence_fields: list[str] = Field(
        default_factory=list,
        description="Dotted paths the model was unsure about"
    )

class ExtractionMetadata(BaseModel):
    """Computed by our code, never by the model."""
    source_file: str
    model_used: str
    extracted_at: datetime
    confidence_flags: list[str] = Field(default_factory=list)

class ClinicalRecord(BaseModel):
    """Persisted to disk."""
    data: ClinicalRecordExtraction
    extraction_metadata: ExtractionMetadata
```

### 3. prompts.py

```python
SYSTEM_PROMPT = """You are a clinical data extraction assistant...
[See source for full text]
"""

def build_extraction_prompt(note_text: str) -> str:
    """Build user message for Claude."""
    return f"Extract structured clinical data from this health record note:\n\n---\n{note_text}\n---\n\nReturn the extracted data in the specified JSON format."
```

### 4. client.py

```python
class ExtractionAPIError(Exception):
    """Non-retryable failure (4xx, refusal)."""

class ExtractionRetryableError(Exception):
    """Retry budget exhausted (429/5xx after SDK retries)."""

def get_client(settings: Settings) -> anthropic.Anthropic:
    """Create Anthropic client with configured retries/timeout."""
    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key if settings.anthropic_api_key else None,
        max_retries=settings.max_retries,
        timeout=settings.timeout_seconds,
    )

def call_claude_for_extraction(
    client: anthropic.Anthropic,
    prompt: str,
    settings: Settings
) -> ClinicalRecordExtraction:
    """Call Claude with structured output. Returns parsed object or raises exception."""
    response = client.messages.parse(
        model=settings.model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_format=ClinicalRecordExtraction,
    )
    # Raises ExtractionAPIError or ExtractionRetryableError on failure
    return response.parsed_output
```

### 5. extraction.py (THE core)

```python
class ExtractionResult(BaseModel):
    record: Optional[ClinicalRecord] = None
    success: bool
    error: Optional[str] = None
    source_file: str

def extract_record(
    note_text: str,
    *,
    source_file: str,
    settings: Optional[Settings] = None,
    client: Optional[anthropic.Anthropic] = None,
) -> ExtractionResult:
    """
    Extract structured data from a single note.
    
    Args:
        note_text: Clinical note content
        source_file: Filename for metadata (e.g., "notes/001.txt")
        settings: Config (defaults to load_settings())
        client: Anthropic client (defaults to get_client(settings)) — inject for testing
        
    Returns:
        ExtractionResult with record (on success) or error (on failure)
    """
    # 1. Validate settings, client
    # 2. Check note_text not empty
    # 3. Build prompt
    # 4. Call call_claude_for_extraction() → ClinicalRecordExtraction (already validated)
    # 5. Compute confidence flags via confidence.py
    # 6. Wrap in ExtractionMetadata + ClinicalRecord
    # 7. Return ExtractionResult(success=True, record=...)
    # On any error: return ExtractionResult(success=False, error=...)

def process_directory(
    input_dir: Path,
    output_dir: Path,
    settings: Optional[Settings] = None,
    limit: Optional[int] = None,
) -> list[ExtractionResult]:
    """
    Process all .txt files in input_dir.
    
    Args:
        input_dir: Directory containing .txt notes
        output_dir: Directory to write output JSON files
        settings: Config (defaults to load_settings())
        limit: Max records to process (None = all)
        
    Returns:
        List of ExtractionResult (one per input file)
        
    Behavior:
        - Creates output_dir if needed
        - Processes in sorted order
        - Writes JSON for each successful record
        - Never raises on a single bad record; collects results
    """
    # 1. List all *.txt files in input_dir (sorted)
    # 2. Optionally limit via `limit` parameter
    # 3. Create single client (reuse across batch)
    # 4. For each note_file:
    #    - load_note(note_file)
    #    - extract_record(note_text, ...)
    #    - If success: write_record(result.record, output_dir)
    #    - Append ExtractionResult to results
    # 5. Return results list
```

### 6. confidence.py

```python
def compute_confidence_flags(extraction: ClinicalRecordExtraction) -> list[str]:
    """
    Compute locally-computed confidence flags (independent of model self-report).
    
    Returns list of flag strings:
        - "no_diagnoses_found"
        - "no_medications_found"
        - "no_vitals_found"
        - "no_labs_found"
        - "implausible_age" (if age not in [0, 130])
        - "model_reported_low_confidence" (if extraction.low_confidence_fields not empty)
        - "no_encounter_type"
        - "no_encounter_date"
    """
```

### 7. io_utils.py

```python
def load_note(file_path: Path) -> str:
    """Load .txt note from file. Raises FileNotFoundError if missing."""

def write_record(record: ClinicalRecord, output_dir: Path) -> Path:
    """
    Write ClinicalRecord as JSON to output_dir.
    
    Filename: {source_file_stem}_extracted.json
    
    Returns: Path to written file
    """

def list_note_files(input_dir: Path) -> list[Path]:
    """List all .txt files in input_dir, sorted."""
```

### 8. cli.py (Typer)

Commands (run via `carta <command>` after `pip install -e .`):

```python
@app.command()
def process(
    input_dir: str,          # positional
    output_dir: str,         # positional
    model: Optional[str] = None,  # --model
    limit: Optional[int] = None,  # --limit
) -> None:
    """Process a directory of notes. Prints summary + exits non-zero on any failure."""

@app.command()
def extract_one(
    note_file: str,          # positional
    output: Optional[str] = None,  # --output
) -> None:
    """Extract from single note. Prints JSON to stdout or writes to --output."""

@app.command()
def evaluate_accuracy(
    gold_dir: str = "eval/gold_standard",  # --gold-dir
    out: str = "eval/results",             # --out
) -> None:
    """Run accuracy harness. Subprocesses eval/evaluate_accuracy.py."""

@app.command()
def benchmark(
    input_dir: str = "fixtures/sample_notes",  # --input-dir
    baseline_minutes: float = 8.0,             # --baseline-minutes
) -> None:
    """Run benchmark harness. Subprocesses benchmark/benchmark.py."""

@app.command()
def serve(
    host: str = "0.0.0.0",  # --host
    port: int = 8000,       # --port
) -> None:
    """Start FastAPI server. Runs uvicorn on specified host:port."""
```

### 9. api.py (FastAPI)

```python
app = FastAPI(title="Carta Healthcare", version="0.1.0")

class ExtractRequest(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=50000)

class ExtractResponse(BaseModel):
    record: ClinicalRecord

@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    """Extract structured data. Returns 502 on failure."""

@app.get("/health")
def health() -> dict:
    """Liveness check. Returns {"status": "ok"}."""
```

## Evaluation (eval/)

### scoring.py Functions

```python
def flatten_record(extraction: ClinicalRecordExtraction) -> dict[str, Any]:
    """
    Flatten nested record to dotted-path keys.
    
    Examples:
        patient.age → 68
        encounter.encounter_type → "discharge summary"
        diagnoses_count → 4
        medications_count → 6
    """

def fuzzy_match(gold: str, predicted: str, threshold: float = 0.85) -> bool:
    """
    Check string similarity via difflib.SequenceMatcher.
    
    Returns: ratio >= threshold
    """

def match_lists(
    gold_items: list[dict],
    predicted_items: list[dict],
    key_field: str
) -> tuple[int, int, int]:
    """
    Greedy best-match pairing for list-valued fields.
    
    Returns: (num_matched, num_gold, num_predicted)
    
    Algorithm:
        For each gold item:
            Find best fuzzy-match in predicted items (not yet matched)
            Mark both as paired
        Return count of successful pairs
    """

def compute_scalar_accuracy(gold: dict, predicted: dict) -> dict:
    """
    Score scalar fields.
    
    Returns:
        {
            "total_fields": int,
            "exact_matches": int,
            "fuzzy_matches": int,
            "accuracy": float (0.0 to 1.0)
        }
    """

def compute_list_accuracy(
    gold: ClinicalRecordExtraction,
    predicted: ClinicalRecordExtraction
) -> dict:
    """
    Score list-valued fields (diagnoses, medications, vitals, labs).
    
    Returns:
        {
            "diagnoses": {"matched": int, "gold_count": int, "predicted_count": int, "precision": float, "recall": float},
            "medications": {...},
            "vitals": {...},
            "labs": {...}
        }
    """
```

### evaluate_accuracy.py Main Function

```python
def run_evaluation(gold_dir: Path, output_dir: Path) -> None:
    """
    Main harness.
    
    1. Load gold_dir/notes/*.txt + gold_dir/labels/*.json pairs
    2. For each pair:
       - Read note text
       - Call extract_record() (live API)
       - Score against gold using scoring.py functions
       - Accumulate metrics
    3. Aggregate overall accuracy %
    4. Write results to output_dir/accuracy_report_TIMESTAMP.json
    5. Print summary table to stdout
    
    Note: Makes real API calls. Costs money.
    """
```

## Benchmark (benchmark/)

### benchmark.py Main Function

```python
MANUAL_BASELINE_MINUTES_PER_RECORD = 8.0

def run_benchmark(
    input_dir: Path,
    output_dir: Path,
    baseline_minutes: float = MANUAL_BASELINE_MINUTES_PER_RECORD
) -> None:
    """
    Main harness.
    
    1. List all *.txt files in input_dir
    2. For each file:
       - Time load_note() → extract_record() → write_record()
       - Accumulate elapsed_seconds
    3. Compute statistics:
       - mean, median, p95 seconds/record
       - total seconds
       - pct_faster = (1 - mean_seconds / (baseline_minutes * 60)) * 100
    4. Write results to output_dir/benchmark_report_TIMESTAMP.json
    5. Print summary table to stdout
    
    Note: Makes real API calls. Costs money.
    """
```

## Testing Strategy

### tests/test_schema.py
- Pydantic model instantiation
- Field validation (required vs optional)
- JSON serialization round-trip

### tests/test_extraction.py
- `extract_record()` with mocked Anthropic client
  - Happy path: client returns valid extraction
  - Client raises RateLimitError → failure result
  - Client raises APIStatusError (4xx) → failure result
  - Client raises APIStatusError (5xx, already retried) → failure result
  - Refusal (stop_reason="refusal") → failure result
- Empty note text → failure result
- Confidence flags computed correctly

### tests/test_confidence.py
- Each flag condition independently
- Multiple flags together

### tests/test_cli.py
- Typer CliRunner for each command
- Mock extraction.py to avoid real API calls
- Happy path + error cases

### tests/test_api.py
- FastAPI TestClient for each endpoint
- Mock extraction.py
- POST /extract with valid input → 200 + record
- POST /extract with invalid input → 422
- POST /extract with extraction failure → 502
- GET /health → 200 + {"status": "ok"}

## Error Codes & Exit Codes

### CLI Exit Codes
- **0**: All records processed successfully
- **1**: One or more records failed

### API Status Codes
- **200**: Successful extraction
- **422**: Invalid request (e.g., empty note_text)
- **502**: Extraction failed (API error, refusal, etc.)

## Dependencies

```
anthropic>=0.35.0
pydantic>=2.0
typer[all]>=0.9.0
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pytest>=7.0  (dev only)
pytest-cov>=4.0  (dev only)
black>=23.0  (dev only)
ruff>=0.1.0  (dev only)
mypy>=1.0  (dev only)
```

## Testing Coverage Matrix

| Component | Unit Tests | Live API Tests | Notes |
|-----------|-----------|----------------|-------|
| schema.py | ✓ | - | Type validation, JSON round-trip |
| config.py | ✓ | - | Env var loading |
| prompts.py | ✓ | - | Prompt building |
| client.py | ✓ | - | Mocked Anthropic client |
| extraction.py | ✓ | - | Mocked client |
| confidence.py | ✓ | - | Flag logic |
| io_utils.py | ✓ | - | File I/O |
| cli.py | ✓ | - | Mocked extraction |
| api.py | ✓ | - | Mocked extraction |
| eval/scoring.py | ✓ | - | Scoring algorithms |
| eval/evaluate_accuracy.py | - | ✓* | Requires real API key |
| benchmark/benchmark.py | - | ✓* | Requires real API key |

*: Not part of `pytest tests/` — run manually.
