# tests/ — Test Suite (Placeholder)

This folder will hold automated tests for the Banner Health clinical documentation assistant.

## Expected Test Categories

### 1. **Unit Tests** (src layer tests)

- PHI redaction and de-identification logic
- Prompt template rendering
- Audit log integrity
- Guardrail enforcement (no fabrication, cite sources)

```
tests/unit/
├── test_phi_redaction.py
├── test_prompts.py
├── test_guardrails.py
├── test_audit_logging.py
```

### 2. **Integration Tests** (layer-to-layer)

- EHR → PHI access → AI orchestration (happy path)
- AI orchestration → Audit logging
- Draft creation → Physician review UI interaction
- Approved draft → EHR write-back

```
tests/integration/
├── test_ehr_to_draft.py
├── test_draft_review_workflow.py
├── test_audit_trail.py
```

### 3. **Compliance Tests** (HIPAA, audit, safety)

- Audit trail completeness (all actions logged?)
- PHI redaction accuracy (no identifiers leaked?)
- Draft-status enforcement (draft never auto-signed?)
- RBAC enforcement (physician can't see other's patients?)

```
tests/compliance/
├── test_audit_completeness.py
├── test_phi_redaction.py
├── test_draft_status.py
├── test_rbac.py
```

### 4. **Functional Tests** (end-to-end, manual/automated)

- Physician can draft a note from visit input
- Physician can review and edit a draft
- Physician can approve and sign a draft
- Approved draft appears in patient record with timestamp
- UI is responsive and accessible

### 5. **AI Quality Tests** (model behavior, hallucination)

- AI draft matches provided input facts (no fabrication)
- AI draft has source citations
- AI accurately summarizes chart
- Hallucination rate < target threshold (aim: < 2%)

### 6. **Security Tests** (penetration, auth, access)

- Unauthorized user cannot access patient data
- Physician cannot sign another physician's drafts
- Session timeout enforces re-auth
- API rate-limiting prevents brute-force

## Test Data

All tests use **synthetic data** from `data/` or inline test fixtures. Never use real patient data.

Example fixture:

```python
# tests/fixtures/synthetic_patient.py
SYNTHETIC_PATIENT = {
    "id": "TEST_001",
    "name": "Test Patient",
    "age": 50,
    "problems": ["Hypertension"],
    "meds": ["Lisinopril 20mg"],
    "recent_labs": {"BP": "140/90"},
}
```

## Running Tests

_(To be defined during Phase 1 implementation)_

Likely:
```bash
pytest tests/
pytest tests/unit/                  # Unit tests only
pytest tests/compliance/            # Compliance audit
pytest tests/integration/ -s        # Integration with verbose output
```

## Continuous Integration

_(To be configured when CI/CD pipeline is set up)_

Expected:
- All tests must pass before merging to main
- Compliance tests mandatory (audit trail, PHI redaction)
- Coverage target: 80%+ for critical modules (PHI access, audit logging, guardrails)

## Success Metrics (Phase 1 Pilot)

- 100% of core workflows covered by tests
- 0 audit trail gaps (100% of actions logged)
- 0 PHI leakage in test runs
- Hallucination rate < 2% (external spot-check audit)

---

See `docs/design/high-level-design.md` for NTF requirements and success metrics for each phase.
