# Qualified_Health — Low-Level Design

## Project Layout

```
Qualified_Health/
├── CLAUDE.md                        # Project primer (load this every session)
├── README.md                        # User-facing project description
├── requirements.txt                 # pip dependencies
├── run.sh                           # One-command: init DB, load sample data, start server
│
├── docs/
│   ├── HLD.md                       # High-level design (this directory)
│   └── LLD.md                       # Low-level design (you are here)
│
├── qualified_health/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app, route definitions
│   ├── config.py                    # Paths: db file, data dir, rules dir, constants
│   ├── db.py                        # SQLite connection, schema initialization
│   ├── schema.sql                   # Full DDL (executed by db.py on app start)
│   ├── models.py                    # Pydantic request/response models
│   │
│   ├── pipeline.py                  # Orchestrator: ingest() → identity_resolve() → normalize() → screen()
│   ├── ingestion.py                 # Read CSV/JSON files → raw_records table
│   ├── identity.py                  # Match raw records to canonical patients (tiered)
│   ├── tokenizer.py                 # Generate deterministic patient_token
│   ├── normalization.py             # Transform raw → typed clinical facts
│   ├── rules_engine.py              # Load YAML, evaluate criteria, generate trace
│   └── rules_dsl.py                 # Criterion evaluators (lab_threshold, medication_presence, etc.)
│
├── rules/
│   ├── statin_therapy.yaml          # Example intervention
│   ├── anticoagulation_review.yaml  # Example intervention
│   └── ...                          # One YAML per intervention
│
├── sample_data/
│   ├── generate_sample_data.py      # Standalone script to generate synthetic data
│   ├── source_a_hospital/
│   │   ├── demographics.csv         # Columns: mrn, first_name, last_name, dob, sex, icd10_code, ...
│   │   └── diagnoses.json
│   ├── source_b_clinic/
│   │   ├── patients.csv             # Columns: patient_name (full), dob, labs; NO MRN
│   │   └── labs.json                # Deliberately different schema from source_a
│   └── source_c_pharmacy/
│       └── medications.csv          # Columns: mrn_formatted, drug_name, start_date, end_date
│
├── tests/
│   ├── conftest.py                  # pytest fixtures (temp DB, sample data)
│   ├── test_tokenizer.py            # Determinism, immutability, format
│   ├── test_identity.py             # All 4 match tiers, backfill, confidence scoring
│   ├── test_normalization.py        # Raw row parsing, unit conversion, malformed handling
│   └── test_rules_engine.py         # AND/OR logic, boundary operators, lookback windows
│
└── qualified_health.db              # Generated at runtime (gitignored)
```

---

## SQLite Schema (schema.sql)

```sql
-- ===== Identity Resolution Layer =====

CREATE TABLE patients (
    patient_token       TEXT PRIMARY KEY,
    canonical_first_name TEXT,
    canonical_last_name  TEXT,
    canonical_dob        TEXT NOT NULL,          -- ISO 8601 YYYY-MM-DD
    canonical_sex        TEXT,
    canonical_mrn        TEXT,                   -- Best-known MRN (may be NULL if never provided)
    created_at           TEXT NOT NULL,          -- ISO 8601 timestamp
    identity_confidence  TEXT NOT NULL,          -- 'exact_mrn' | 'name_dob_exact' | 'name_dob_fuzzy' | 'new_patient'
    
    UNIQUE(canonical_first_name, canonical_last_name, canonical_dob)  -- Prevent exact duplicates
);

CREATE TABLE identity_crosswalk (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_token          TEXT NOT NULL REFERENCES patients(patient_token) ON DELETE CASCADE,
    source_system          TEXT NOT NULL,        -- e.g., 'source_a_hospital', 'source_b_clinic'
    source_file            TEXT NOT NULL,        -- e.g., 'demographics.csv', 'labs.json'
    record_type            TEXT NOT NULL,        -- 'demographics' | 'labs' | 'medications' | 'diagnoses'
    source_identifier_type TEXT NOT NULL,        -- 'mrn' | 'name_dob' | 'none'
    source_identifier_raw  TEXT NOT NULL,        -- Raw value as it appeared (for audit)
    match_method           TEXT NOT NULL,        -- 'exact_mrn' | 'name_dob_exact' | 'name_dob_fuzzy' | 'new_patient'
    match_confidence       REAL NOT NULL,        -- 0.0-1.0
    raw_record_id          INTEGER NOT NULL REFERENCES raw_records(id),
    matched_at             TEXT NOT NULL         -- ISO 8601 timestamp
);

-- ===== Raw Ingestion Layer (Audit Trail) =====

CREATE TABLE raw_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system   TEXT NOT NULL,               -- e.g., 'source_a_hospital'
    source_file     TEXT NOT NULL,               -- e.g., 'demographics.csv'
    record_type     TEXT NOT NULL,               -- 'demographics' | 'labs' | 'medications' | 'diagnoses'
    raw_json        TEXT NOT NULL,               -- Entire row serialized as JSON (verbatim)
    ingested_at     TEXT NOT NULL,               -- ISO 8601 timestamp
    patient_token   TEXT REFERENCES patients(patient_token)  -- Filled after identity resolution
);

CREATE INDEX idx_raw_records_patient ON raw_records(patient_token);

-- ===== Normalized Clinical Facts (Token-keyed Only) =====

CREATE TABLE labs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_token   TEXT NOT NULL REFERENCES patients(patient_token) ON DELETE CASCADE,
    test_name       TEXT NOT NULL,               -- Normalized: 'A1c', 'LDL', 'creatinine', etc.
    value           REAL NOT NULL,
    unit            TEXT,                        -- e.g., '%' for A1c, 'mg/dL' for LDL
    observed_date   TEXT NOT NULL,               -- ISO 8601 YYYY-MM-DD
    source_record_id INTEGER NOT NULL REFERENCES raw_records(id),
    normalized_at   TEXT NOT NULL                -- ISO 8601 timestamp
);

CREATE INDEX idx_labs_patient_test ON labs(patient_token, test_name);
CREATE INDEX idx_labs_observed_date ON labs(observed_date);

CREATE TABLE medications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_token   TEXT NOT NULL REFERENCES patients(patient_token) ON DELETE CASCADE,
    drug_name       TEXT NOT NULL,               -- Normalized generic name (not brand)
    drug_class      TEXT,                        -- e.g., 'statin', 'anticoagulant', 'ace_inhibitor'
    start_date      TEXT,                        -- ISO 8601 YYYY-MM-DD
    end_date        TEXT,                        -- NULL = active/ongoing
    source_record_id INTEGER NOT NULL REFERENCES raw_records(id),
    normalized_at   TEXT NOT NULL                -- ISO 8601 timestamp
);

CREATE INDEX idx_meds_patient_class ON medications(patient_token, drug_class);
CREATE INDEX idx_meds_start_date ON medications(start_date);

CREATE TABLE diagnoses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_token   TEXT NOT NULL REFERENCES patients(patient_token) ON DELETE CASCADE,
    icd10_code      TEXT NOT NULL,               -- e.g., 'E11.9' (ICD-10 code)
    description     TEXT,                        -- e.g., 'Type 2 diabetes without complications'
    diagnosed_date  TEXT,                        -- ISO 8601 YYYY-MM-DD (may be NULL if not provided)
    source_record_id INTEGER NOT NULL REFERENCES raw_records(id),
    normalized_at   TEXT NOT NULL                -- ISO 8601 timestamp
);

CREATE INDEX idx_diagnoses_patient_code ON diagnoses(patient_token, icd10_code);

-- ===== Rules & Interventions =====

CREATE TABLE interventions (
    intervention_id TEXT PRIMARY KEY,            -- Slug, e.g., 'statin_therapy'
    name            TEXT NOT NULL,               -- Human name, e.g., 'Statin Therapy Candidate'
    description     TEXT,                        -- Markdown/free text
    rule_file_path  TEXT NOT NULL,               -- e.g., 'rules/statin_therapy.yaml'
    version         TEXT NOT NULL,               -- Version string from YAML
    loaded_at       TEXT NOT NULL                -- ISO 8601 timestamp
);

-- ===== Results: Candidate Matches =====

CREATE TABLE candidate_matches (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_token    TEXT NOT NULL REFERENCES patients(patient_token) ON DELETE CASCADE,
    intervention_id  TEXT NOT NULL REFERENCES interventions(intervention_id) ON DELETE CASCADE,
    matched          INTEGER NOT NULL,           -- 1 = eligible, 0 = evaluated but not eligible
    trace_json       TEXT NOT NULL,               -- JSON array of {criterion_id, passed, evidence: [facts]}
    screened_at      TEXT NOT NULL,               -- ISO 8601 timestamp
    
    UNIQUE(patient_token, intervention_id, screened_at)
);

CREATE INDEX idx_candidates_intervention_matched ON candidate_matches(intervention_id, matched);
CREATE INDEX idx_candidates_patient ON candidate_matches(patient_token);
```

---

## Patient Tokenization & Identity Resolution

### Normalization Functions

These are deterministic, applied before matching or hashing.

```python
def normalize_name(s: str) -> str:
    """Lowercase, strip whitespace, remove punctuation."""
    if not s:
        return ""
    return re.sub(r'[^a-z0-9]', '', s.lower().strip())

def normalize_dob(s: str) -> str:
    """Parse multiple date formats → ISO 8601 YYYY-MM-DD. Raise ValueError if unparseable."""
    # Try formats: MM/DD/YYYY, YYYY-MM-DD, DD-Mon-YYYY, etc.
    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%d-%b-%Y', '%Y%m%d']:
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {s}")

def normalize_mrn(s: str) -> str:
    """Strip leading zeros, uppercase any alpha prefix, canonicalize spacing."""
    if not s:
        return ""
    # Remove internal spaces/dashes, left-pad with zeros to e.g. 7 digits
    s = re.sub(r'[\s\-]', '', s.upper())
    return s.zfill(7)  # Adjust as needed for your MRN scheme
```

### Tiered Matching Strategy

Tried in order; first hit wins.

```python
def resolve_identity(raw_record: dict, db: Connection) -> Tuple[str, str, float]:
    """
    Match raw_record to a canonical patient.
    
    Returns:
        (patient_token, match_method, confidence)
        where match_method ∈ {'exact_mrn', 'name_dob_exact', 'name_dob_fuzzy', 'new_patient'}
    """
    # Extract and normalize identifiers from raw_record
    mrn = raw_record.get('mrn')
    first = raw_record.get('first_name')
    last = raw_record.get('last_name')
    dob = raw_record.get('dob')
    
    # Tier 1: Exact MRN match
    if mrn:
        mrn_norm = normalize_mrn(mrn)
        existing = db.execute(
            "SELECT patient_token FROM patients WHERE canonical_mrn = ?",
            (mrn_norm,)
        ).fetchone()
        if existing:
            return (existing[0], 'exact_mrn', 1.0)
    
    # Tier 2: Exact name+DOB match
    if first and last and dob:
        first_norm = normalize_name(first)
        last_norm = normalize_name(last)
        dob_norm = normalize_dob(dob)
        
        existing = db.execute(
            """SELECT patient_token FROM patients 
               WHERE canonical_first_name = ? 
               AND canonical_last_name = ? 
               AND canonical_dob = ?""",
            (first_norm, last_norm, dob_norm)
        ).fetchone()
        if existing:
            token = existing[0]
            # Backfill MRN if discovered and not already set
            if mrn and not db.execute(
                "SELECT canonical_mrn FROM patients WHERE patient_token = ?", (token,)
            ).fetchone()[0]:
                db.execute(
                    "UPDATE patients SET canonical_mrn = ? WHERE patient_token = ?",
                    (normalize_mrn(mrn), token)
                )
            return (token, 'name_dob_exact', 0.9)
    
    # Tier 3: Fuzzy name+DOB match (DOB exact, name similarity ≥ threshold)
    if first and last and dob:
        first_norm = normalize_name(first)
        last_norm = normalize_name(last)
        dob_norm = normalize_dob(dob)
        full_name = f"{first_norm} {last_norm}"
        
        candidates = db.execute(
            "SELECT patient_token, canonical_first_name, canonical_last_name FROM patients WHERE canonical_dob = ?",
            (dob_norm,)
        ).fetchall()
        
        for token, ex_first, ex_last in candidates:
            ex_full = f"{ex_first} {ex_last}".lower()
            similarity = jaro_winkler(full_name, ex_full)  # Use difflib or external lib
            if similarity >= 0.85:  # Threshold
                if mrn:
                    db.execute(
                        "UPDATE patients SET canonical_mrn = ? WHERE patient_token = ?",
                        (normalize_mrn(mrn), token)
                    )
                return (token, 'name_dob_fuzzy', similarity)
    
    # Tier 4: No match → create new patient
    token = make_patient_token(mrn if mrn else f"{first}|{last}|{dob}")
    db.execute(
        """INSERT INTO patients 
           (patient_token, canonical_first_name, canonical_last_name, canonical_dob, 
            canonical_sex, canonical_mrn, created_at, identity_confidence)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 'new_patient')""",
        (token, normalize_name(first or ''), normalize_name(last or ''), 
         normalize_dob(dob) if dob else None,
         raw_record.get('sex'), normalize_mrn(mrn) if mrn else None)
    )
    return (token, 'new_patient', 1.0)
```

### Token Generation

```python
def make_patient_token(mrn: str = None, first: str = None, last: str = None, dob: str = None) -> str:
    """
    Generate deterministic patient_token.
    
    If MRN is provided, hash it. Otherwise, hash last|first|dob (all normalized).
    """
    if mrn:
        mrn_norm = normalize_mrn(mrn)
        base = mrn_norm
    else:
        first_norm = normalize_name(first or '')
        last_norm = normalize_name(last or '')
        dob_norm = normalize_dob(dob) if dob else ''
        base = f"{last_norm}|{first_norm}|{dob_norm}"
    
    digest = hashlib.sha256(base.encode()).hexdigest()[:16]
    return f"PT-{digest}"
```

**Critical invariant**: Once assigned and stored in `patients.patient_token`, this token is **immutable**. If a later record provides a stronger identifier (e.g., discovering an MRN for a name+DOB patient), update the `canonical_*` fields on the patient row, but **never re-derive the token**. Re-deriving breaks all foreign keys.

---

## Rules Config Schema (YAML)

### Intervention Definition Format

```yaml
intervention_id: statin_therapy
name: "Statin Therapy Candidate"
version: "1.0"
description: >
  Patients with poorly controlled diabetes (A1c > 9 in the last 12 months)
  who are not currently on statin therapy are candidates for statin initiation.
  Reference: [Clinical guideline citation]

criteria:
  logic: AND                        # Top-level combination: AND | OR
  conditions:
    - id: high_a1c
      type: lab_threshold
      test_name: A1c
      operator: ">"                 # One of: >, >=, <, <=, ==
      value: 9.0
      lookback_months: 12           # Only labs observed in this window
      require_at_least: 1           # At least N qualifying observations (usually 1 or 2)
    
    - id: no_active_statin
      type: medication_absence
      drug_class: statin
      lookback_months: 12
      # If a medication row with drug_class='statin' and (end_date IS NULL OR end_date > now - 12 months)
      # exists, this condition FAILS. If no such row, condition PASSES.

    # Example of nested AND/OR:
    # - id: diabetes_or_prediabetes
    #   logic: OR
    #   conditions:
    #     - id: type2_diabetes
    #       type: diagnosis_presence
    #       icd10_code_prefix: "E11"  # ICD-10 codes starting with E11
    #       lookback_months: null      # Any time
    #
    #     - id: prediabetes
    #       type: diagnosis_presence
    #       icd10_code: "R73.9"
    #       lookback_months: null
```

### Condition Types

- **`lab_threshold`**: Compare lab value(s) to a threshold.
  - Fields: `test_name`, `operator`, `value`, `lookback_months`, `require_at_least`
  - Matches most-recent lab (or any qualifying lab, depending on `require_at_least`) within the lookback window.

- **`medication_presence`**: Patient is on a medication (or medication class).
  - Fields: `drug_class` or `drug_name`, `lookback_months`
  - Matches if any medication row with start_date within the window and end_date (NULL or after window start).

- **`medication_absence`**: Patient is NOT on a medication.
  - Fields: `drug_class` or `drug_name`, `lookback_months`
  - Matches if no medication row matching the presence criteria.

- **`diagnosis_presence`**: Patient has a diagnosis (ICD-10 code).
  - Fields: `icd10_code` (exact match) or `icd10_code_prefix` (e.g., "E11*" for all E11 codes), `lookback_months` (or null = any time)

- **`diagnosis_absence`**: Patient does NOT have a diagnosis.
  - Fields: same as above, logic inverted.

- **`demographic_filter`**: Simple attribute on the patient.
  - Fields: `attribute` (e.g., "age_years"), `operator`, `value`
  - Age is derived from `canonical_dob` and today's date.

### Evaluation Engine

```python
def screen_patient(patient_token: str, rule: InterventionRule, db: Connection) -> ScreeningResult:
    """
    Evaluate a rule against one patient.
    
    Returns:
        ScreeningResult(
            patient_token=...,
            intervention_id=...,
            matched=bool,
            trace=[
                ConditionResult(criterion_id='...', passed=bool, evidence=[...]),
                ...
            ]
        )
    """
    trace = evaluate_criteria_tree(rule.criteria, patient_token, db)
    matched = combine_results(rule.criteria.logic, trace)
    
    return ScreeningResult(
        patient_token=patient_token,
        intervention_id=rule.intervention_id,
        matched=matched,
        trace=trace
    )

def evaluate_lab_threshold(patient_token: str, condition: dict, db: Connection) -> ConditionResult:
    """Example DSL evaluator for lab_threshold."""
    test_name = condition['test_name']
    operator = condition['operator']
    value = condition['value']
    lookback_months = condition.get('lookback_months')
    
    cutoff_date = None
    if lookback_months:
        cutoff_date = (datetime.now() - timedelta(days=30 * lookback_months)).strftime('%Y-%m-%d')
    
    query = "SELECT id, value, observed_date FROM labs WHERE patient_token = ? AND test_name = ?"
    if cutoff_date:
        query += f" AND observed_date >= ?"
    
    params = [patient_token, test_name]
    if cutoff_date:
        params.append(cutoff_date)
    
    labs = db.execute(query, params).fetchall()
    
    evidence = []
    passed = False
    
    for lab_id, lab_value, obs_date in labs:
        if apply_operator(lab_value, operator, value):
            evidence.append({'lab_id': lab_id, 'value': lab_value, 'date': obs_date})
            passed = True
            break  # Usually stop at first match, unless require_at_least > 1
    
    return ConditionResult(
        criterion_id=condition['id'],
        passed=passed,
        evidence=evidence
    )
```

---

## FastAPI Endpoints

| Method | Path | Purpose | Request Body | Response |
|---|---|---|---|---|
| **POST** | `/ingest` | Run ingestion pipeline over source directory | `{"source_dir": "sample_data"}` (optional, defaults to config) | `{"raw_records_ingested": N, "patients_resolved": N, "new_patients": N, "duration_seconds": X}` |
| **POST** | `/screen` | Load rules and evaluate all patients | `{"intervention_id": "statin_therapy"}` (optional; omit = run all) | `{"interventions_run": [...], "total_candidates": N, "duration_seconds": X}` |
| **GET** | `/interventions` | List loaded intervention definitions | — | `[{"intervention_id": "...", "name": "...", "version": "...", "description": "..."}]` |
| **GET** | `/candidates/{intervention_id}` | List patients who matched an intervention | Query: `matched=true` (default), `limit=50`, `offset=0` | `[{"patient_token": "...", "matched": 1, "screened_at": "...", "trace_json": "..."}]` |
| **GET** | `/patients/{patient_token}` | Full normalized view of one patient | — | `{"patient_token": "...", "demographics": {...}, "labs": [...], "medications": [...], "diagnoses": [...]}` |
| **GET** | `/patients/{patient_token}/candidacy` | All intervention results for one patient with trace | — | `[{"intervention_id": "...", "matched": 1, "trace": [...]}]` |
| **GET** | `/patients/{patient_token}/crosswalk` | Identity resolution audit trail for one patient | — | `[{"source_system": "...", "match_method": "...", "confidence": 0.95, "source_identifier_raw": "...", "matched_at": "..."}]` |
| **GET** | `/health` | Liveness check | — | `{"status": "ok"}` |

---

## Synthetic Data Generation

**Script**: `sample_data/generate_sample_data.py` (runs standalone, generates CSV/JSON files only).

### Approach

1. Generate ~200 synthetic patients with consistent "ground truth" identity (name, DOB, sex, MRN).
2. Emit each patient's records **inconsistently** across 3 fake source systems to simulate fragmentation:
   - **`source_a_hospital`** (demographics.csv, diagnoses.json): has MRN, full demographics, ICD-10 diagnoses.
   - **`source_b_clinic`** (patients.csv, labs.json): has labs only, no MRN, name in a single `patient_name` field, DOB in a different date format. ~10% of records have name typos/nicknames to exercise fuzzy matching.
   - **`source_c_pharmacy`** (medications.csv): has MRN (differently formatted — zero-padded or dashed) and medications.

3. Inject realistic noise:
   - Some missing fields (e.g., ~5% of patients missing DOB in source_b).
   - A few duplicate rows within a source.
   - A handful of patients appearing in only 1–2 of the 3 sources (incomplete records).
   - A few rows with unparseable dates (to test error handling).

4. Hand-craft clinical facts so:
   - ~15% of patients unambiguously satisfy each intervention criteria (e.g., A1c > 9 AND no statin).
   - ~15% unambiguously fail (e.g., A1c > 9 BUT has statin).
   - Remainder (~70%) randomized.

### Usage

```bash
python sample_data/generate_sample_data.py [--num_patients 200] [--output_dir sample_data]
```

Generates:
- `sample_data/source_a_hospital/demographics.csv`
- `sample_data/source_a_hospital/diagnoses.json`
- `sample_data/source_b_clinic/patients.csv`
- `sample_data/source_b_clinic/labs.json`
- `sample_data/source_c_pharmacy/medications.csv`

---

## Testing

**Test framework**: `pytest`

### Test Modules

- **`test_tokenizer.py`**:
  - Token determinism: same identity → same token.
  - Format check: `PT-` prefix + 16 hex chars.
  - Immutability invariant: token never changes post-creation.

- **`test_identity.py`**:
  - Tier 1 (exact MRN): MRN match → existing patient token.
  - Tier 2 (exact name+DOB): name+DOB exact → existing patient token.
  - Tier 3 (fuzzy): name similarity ≥ threshold + exact DOB → match with lower confidence.
  - Tier 4 (new): no match → new patient token created.
  - Backfill: discovering MRN for name+DOB patient updates canonical_mrn but not token.
  - Confidence scoring: verify confidence values for each tier.

- **`test_normalization.py`**:
  - Date parsing: multiple formats → ISO 8601.
  - Name normalization: capitalization, punctuation, spaces.
  - MRN normalization: zero-padding, alpha casing.
  - Malformed handling: unparseable dates, missing units → graceful skip or error.

- **`test_rules_engine.py`**:
  - Lab threshold: value > threshold matches, < threshold doesn't.
  - Lookback window: labs inside window counted, outside window excluded.
  - Medication presence/absence: active medications match, ended/absent don't.
  - AND logic: all conditions must pass.
  - OR logic: at least one condition must pass.
  - Nested combinations: AND inside OR, etc.
  - Trace generation: evidence list populated correctly.

### Running Tests

```bash
pytest tests/
pytest tests/test_identity.py -v               # Verbose
pytest tests/test_rules_engine.py::test_lab_threshold -v
```

### Fixtures (conftest.py)

- `temp_db`: Creates temporary SQLite database with full schema for each test.
- `sample_patients`: Pre-populated `patients` table with 5–10 deterministic test patients.
- `sample_facts`: Pre-populated `labs`, `medications`, `diagnoses` tables with known facts.

---

## Key Files to Implement First

1. **`schema.sql`**: Full DDL for all tables (copy the section above). Highest priority — other modules depend on it.
2. **`tokenizer.py`**: `make_patient_token()` function — simple hash, highly testable.
3. **`identity.py`**: Tiered matching logic — complex, thoroughly tested.
4. **`rules_engine.py`** + **`rules_dsl.py`**: Config-driven rules, evaluator functions.
5. **`main.py`**: FastAPI app with the 8 endpoints.
6. **Sample data generation** + **ingestion.py** / **normalization.py**.

---

## Token Optimization Notes

**"Optimize for proper token usage"** interpreted as:

1. **Architectural**: Patient tokens reduce PHI surface (raw identifiers isolated to `patients` table, never flow downstream).
2. **Documentation**: `CLAUDE.md` is kept lean (< 100 lines, loaded every session) so future edits have minimal context overhead. Full design lives in `HLD.md` and `LLD.md`, linked rather than duplicated.
3. **Code**: Modules are small and testable in isolation (tokenizer is 20 lines, identity resolution is ~100 lines, etc.), reducing the cognitive load per session and enabling fast verification.
