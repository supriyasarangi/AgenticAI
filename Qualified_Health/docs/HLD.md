# Qualified_Health — High-Level Design

## Problem Statement

Healthcare organizations often collect patient data across multiple systems (hospital EHR, clinic labs, pharmacy records, etc.), each with its own patient identifiers and schemas. This **fragmentation** makes it difficult to:
1. Identify the same patient across sources (Bob Smith in the hospital system vs. Robert Smith in the lab system — same person?)
2. Apply evidence-based clinical rules that depend on a unified view (e.g., "is this patient on a statin AND has an A1c > 9?")

**Qualified_Health** solves this for a *single deployment* by ingesting fragmented records, resolving identity across sources, normalizing clinical facts, and evaluating rule-based intervention eligibility criteria transparently.

**Scope**: Prototype/demo on synthetic data, no real PHI, single machine, no distributed infra. The goal is to demonstrate the problem-solving approach (identity resolution → normalized view → rule evaluation) and produce an auditable, patient-by-patient trace of why candidates match or don't.

## Architecture

```
[Source Files]
   (demographics.csv, labs.json, medications.csv, diagnoses.json
    from 3+ different systems with inconsistent schemas/identifiers)
         ↓
   ┌─────────────────────────────────────────┐
   │        1. INGESTION LAYER               │
   │  (Parse CSV/JSON → raw_records table)   │
   │  Preserves raw data verbatim for audit  │
   └─────────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────────┐
   │    2. IDENTITY RESOLUTION LAYER         │
   │  (Link fragmented records to patients)  │
   │  Tiered: exact MRN → name+DOB → fuzzy   │
   │  Produces: patients table + crosswalk   │
   └─────────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────────┐
   │    3. TOKENIZATION LAYER                │
   │  (Assign deterministic patient_token)   │
   │  From here on: raw identifiers hidden   │
   │  All downstream tables use token only   │
   └─────────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────────┐
   │    4. NORMALIZATION LAYER               │
   │  (Raw → typed clinical facts)           │
   │  Produces: labs, medications, diagnoses │
   │  Facts keyed by patient_token, not MRN  │
   └─────────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────────┐
   │    5. RULES ENGINE LAYER                │
   │  (Evaluate YAML criteria per patient)   │
   │  Checks: lab thresholds, meds, diagnoses│
   │  Produces: candidate_matches with trace │
   └─────────────────────────────────────────┘
         ↓
   ┌─────────────────────────────────────────┐
   │    6. API LAYER                         │
   │  (FastAPI: browse results, audit trail) │
   │  Endpoints: /ingest, /screen, /candidates/
   └─────────────────────────────────────────┘
```

## Core Design Principles

### 1. Identity Resolution as a Separate Concern

**Why**: Records from different systems refer to "patients" using different identifiers. Some systems have a unique MRN, others only have name+DOB, some have neither. We need a *matching strategy* that handles all three cases.

**How**:
- **Tier 1 (Exact MRN)**: If the record has an MRN and an existing patient has that same MRN, they're the same person (confidence: exact).
- **Tier 2 (Name+DOB)**: If no MRN or unseen MRN, normalize name+DOB and match exactly (confidence: high).
- **Tier 3 (Fuzzy name+DOB)**: If still no match, use string similarity on name (Jaro-Winkler) with exact DOB requirement (confidence: lower, but documented).
- **Tier 4 (New)**: If no match at any tier, create a new patient record.

Every decision is logged in `identity_crosswalk` for auditability — a clinician can see exactly why records were or weren't linked.

### 2. Tokenization: Immutable Patient Identity

**Why**: 
- Once we've decided two source records belong to the same patient, we need a stable, opaque identifier that doesn't change.
- This identifier should be deterministic (so future ingestions can re-link to the same patient without a lookup table).
- Raw identifiers (name, DOB, MRN) should not flow downstream into the rules engine or API responses — this is a privacy/audit boundary.

**How**:
```
patient_token = "PT-" + sha256(
    canonical_mrn 
    or normalize_name(last) + "|" + normalize_name(first) + "|" + normalize_dob(dob)
)[:16]
```

- Deterministic: the same identity attributes always produce the same token.
- One-way: token → cannot recover raw identifiers without the `patients` table (which stays on the secure boundary).
- **Immutable**: Once assigned to a patient, the token never changes — even if a later ingestion discovers a better identifier (e.g., a previously-unknown MRN). The `canonical_*` fields on the patient row are updated, the token stays the same.

This immutability is crucial: every foreign key in every other table (`labs`, `medications`, `candidate_matches`) points to this token. Changing it would break all linkages.

### 3. Normalized Fact Tables with No Raw Identifiers

**Why**: The rules engine needs clean, typed clinical facts (lab values with units, medication names, diagnosis codes). Mixing this with raw identifier confusion is error-prone and unmaintainable.

**How**:
- Raw CSV/JSON rows → parsed into typed tables (`labs`, `medications`, `diagnoses`, `patients` demographics).
- Every row is keyed by `patient_token` (never by name/DOB/MRN).
- Unit normalization (e.g., "A1c" regardless of whether the source said "A1C" or "HbA1c"), date parsing (handle multiple formats), medication name normalization (generic name, not brand names).

Result: rules engine reads clean, consistent data. No identity confusion in the business logic.

### 4. Rules as Config, Not Code

**Why**:
- A clinician or analyst should be able to define an intervention eligibility rule without touching Python.
- Rules should be human-readable and auditable (so a reviewer can see exactly what "candidate for statin therapy" means).
- Adding a new intervention should not require a code deployment or QA cycle.

**How**:
- Each intervention is a YAML file (e.g., `rules/statin_therapy.yaml`).
- YAML specifies criteria in a simple DSL: `lab_threshold`, `medication_presence`, `diagnosis_presence`, etc.
- Rule evaluation produces a **trace** — a list of which criteria passed/failed and which specific facts (lab date, medication date, diagnosis code) satisfied or failed each criterion.
- This trace is the auditability: a clinician can click on a patient and see "matched because A1c=9.4 on 2026-03-01 (source: hospital labs) passes 'A1c > 9', and no statin medication found in the last 12 months (source: pharmacy records), so criteria pass."

Adding a new *kind* of criterion (rare) requires one new function in `rules_dsl.py`, not a redesign.

### 5. Full Audit Trail

**Why**: In healthcare, you need to trust the system. If a patient is flagged as a candidate, a clinician or auditor should be able to trace exactly:
- Which source records contributed to that patient's view
- How those records were linked together
- Which facts satisfied which criteria

**How**:
- `raw_records` table preserves every ingested row verbatim (not mutated, never deleted).
- `identity_crosswalk` shows which raw records map to which patients and *why* (match method, confidence, evidence).
- `candidate_matches` includes a `trace_json` field: the per-criterion evaluation results (which facts were examined, did they pass/fail).
- API endpoints expose this trace: `/patients/{token}/crosswalk`, `/patients/{token}/candidacy`.

### 6. Deterministic Pipeline, Single Process

**Why**: 
- Simplicity. No message queues, no distributed transactions, no eventual consistency headaches.
- For prototype data volumes (hundreds to low thousands of patients), the entire pipeline runs in seconds.

**How**:
- `pipeline.py` orchestrates: ingest → identity → normalize → screen → store results.
- Can be invoked via CLI script or FastAPI endpoints (`POST /ingest`, `POST /screen`).
- Separating ingestion from screening allows re-running rules after tweaking a YAML file without re-ingesting data.

---

## Non-Goals (What We Explicitly Don't Do)

- **Real PHI**: Sample data is synthetic, never real patient names/DOB/MRN.
- **Auth/ACL**: No user authentication, no role-based access control — all endpoints public.
- **Machine learning**: Rules are hand-authored and human-readable, not learned from data.
- **Distributed/scalable infra**: Single process, single SQLite file, single machine. No Kafka, Kubernetes, data lakes.
- **Real EHR integration**: We ingest flat files (CSV/JSON), not FHIR APIs or HL7 feeds. Real deployments would add those layers atop the core identity/rules logic.
- **Advanced matching**: No name phonetic matching, no birth-order clustering, no ML-based record linkage confidence scoring — we keep to simple, explainable tiers.

---

## Why This Matters

The traditional problem with "screening large patient populations against fragmented records" is that you spend 80% of your time **proving you've found the right patient** (identity resolution) and only 20% applying the actual clinical logic. By splitting these concerns clearly:
- Identity resolution is **testable and auditable** (show me why these two records are the same person).
- Rules are **transparent** (a clinician can read the YAML and the trace and understand why a patient matched).
- PHI is **bounded** (raw identifiers stay on the secure boundary, tokens are opaque).

A hospital or clinic can then:
1. Validate the matching logic on a small pilot (inspect a few matched/non-matched patients, verify the audit trail).
2. Tune thresholds in YAML (e.g., lower A1c cutoff, extend lookback window) without a deployment cycle.
3. Integrate with their EHR's identity master (swap out the fuzzy-match tier, add a real MRN lookup service).
4. Scale horizontally (replace the single-process pipeline with a Spark job or cloud dataflow) without changing the rules or the API.

This prototype is the "validate the model" step. The architecture is real-world-ready; we just keep the data and infra simple.
