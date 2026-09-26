# data/ — Sample & Synthetic Data Only

**⚠️ CRITICAL**: This folder holds **sample and synthetic patient data only**. No real PHI (Protected Health Information) may ever be stored here.

## What Can Go Here

- ✓ Fictional patient scenarios for testing (e.g., "Patient A, 65-year-old Male, DOB 1960-01-01")
- ✓ De-identified or heavily anonymized clinical data (if approved by legal/compliance)
- ✓ Synthetic EHR exports for integration testing
- ✓ Example input/output pairs for AI model fine-tuning (on synthetic data)

## What Cannot Go Here

- ✗ Real patient names, MRNs, SSNs, or dates of birth
- ✗ Real lab values tied to real identifiers
- ✗ Real encounter records or clinical notes
- ✗ Anything that could re-identify a real patient

## Real Patient Data

Real PHI lives only in:
1. The production EHR (source of truth)
2. HIPAA-compliant secure storage (e.g., encrypted cloud DB, access-controlled)
3. Audit logs (immutable, access-controlled)

**Never** in this Git repository.

## Enforcement

The `.claude/settings.json` hooks will block writes containing SSN/MRN/DOB patterns as an additional safeguard. If a legitimate use case requires storing patient-like data, coordinate with the project lead and legal/compliance before storing it here.

## Examples

### ✓ Good: Synthetic Data

```json
{
  "patient_id": "SYNTH_001",
  "name": "Patient A",
  "age": 65,
  "gender": "Male",
  "problems": ["Hypertension", "Type 2 Diabetes"],
  "medications": ["Lisinopril 20mg", "Metformin 1000mg"],
  "recent_labs": {
    "glucose": 156,
    "K": 4.2,
    "Cr": 1.1
  }
}
```

### ✗ Bad: Real-Like Data

```json
{
  "patient_id": "MRN 12345678",
  "name": "John Smith",
  "dob": "1960-06-15",
  "ssn": "123-45-6789",
  "recent_visit": "..."
}
```

---

See `CLAUDE.md` for the no-PHI rule and how hooks enforce it.
