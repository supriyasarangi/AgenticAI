---
name: banner-health
description: AI-assisted clinical note drafting and chart summarization for physicians. Drafts clinical notes from visit input and generates chart summaries from patient context—both always labeled as draft/pending physician review. Guardrails enforce citation of facts, refuse fabrication, and flag ambiguities. For the Banner Health clinical documentation assistant.
---

# /banner-health

Draft clinical notes and summarize patient charts with AI assistance. All output is explicitly marked as **draft** — never auto-committed to the patient record. Physicians always review and approve.

## Usage

```
/banner-health draft <visit-input>
/banner-health summarize <patient-context>
/banner-health draft <visit-input> --template <note-type>
/banner-health summarize <patient-context> --format bullet
```

### Examples

```bash
# Draft a note from visit input (structured or transcript)
/banner-health draft "Chief complaint: SOB × 3 days. Vitals: HR 102, RR 22, O2 sat 94% on RA. 
Lung exam: diminished breath sounds bilateral bases. CXR: bilateral pleural effusions."

# Summarize a patient's chart for pre-visit prep
/banner-health summarize "
Patient: 68 y.o. male
PMH: HTN, DM2, CAD (s/p stent 2023)
Current meds: Lisinopril 20mg, Metoprolol 50mg, Atorvastatin 40mg, ASA 81mg
Recent labs (09/20): K 4.2, Cr 1.1, glucose 156
Recent encounter: ED visit 09/18 for chest pain, troponin negative, discharged
"

# Draft with a specific template (e.g., "discharge summary")
/banner-health draft "..." --template discharge

# Summarize in bullet format instead of paragraph
/banner-health summarize "..." --format bullet
```

## What This Skill Does

### 1. Draft Clinical Notes

**Input**: Structured visit data (demographics, chief complaint, vitals, exam findings, assessments) and/or visit transcript/scribe notes.

**Output**: A draft clinical note in SOAP (Subjective, Objective, Assessment, Plan) or your org's standard format, with:
- **DRAFT — Pending Physician Review** label (always visible, always first line)
- Source citations (e.g., "Vitals from EHR, dated 2026-09-20")
- Gaps flagged (e.g., "⚠ HPI not provided; drafting from available exam notes only")
- Never marked as final, never signed, never pre-approved

**Guardrails**:
- ✓ Every clinical fact is sourced to the provided input
- ✓ Ambiguities are flagged, not invented
- ✓ Format matches org standard (SOAP template by default; customizable)
- ✗ Never fabricate exam findings, lab values, or diagnoses not in the input
- ✗ Never mark the output as "final" or "ready to sign"

### 2. Summarize Patient Charts

**Input**: Patient context (problem list, medication list, recent labs, recent encounters).

**Output**: A one-paragraph or bullet-point summary suitable for pre-visit preparation, highlighting:
- Active problems and recent changes
- Current medications
- Key recent lab abnormalities
- Recent encounters and their outcomes
- Any urgent flags (e.g., "New positive cultures pending ID consult")

**Guardrails**:
- ✓ Summary is sourced to the provided context
- ✓ Recent abnormalities are highlighted
- ✗ Never add information not in the provided context
- ✗ Never make clinical recommendations (leave that to the physician)

## Enforcement

**Never Auto-Sign**: This skill and the system it supports will never mark a draft as final or send it to the patient record without an explicit physician approval step. The UI enforces the "draft" state until the physician signs.

**Always Physician-Reviewed**: Every AI-drafted note must be reviewed by the treating physician before it can be used clinically. Review is not optional; it is the gate.

**Cite Your Sources**: Every clinical claim in the draft must point back to the provided input or context. If a fact is not in the input, it does not appear in the draft.

**Flag Gaps**: If critical information is missing (e.g., no vital signs, no exam findings), the draft will flag these gaps rather than invent them.

## Typical Workflow

1. **Physician sees a patient** → enter visit data / transcript into the EHR intake form.
2. **Trigger `/banner-health draft`** → AI drafts a note from the intake.
3. **Physician reviews the draft** in the UI → reads, edits, approves, or rejects.
4. **Upon approval** → draft is finalized and signed (timestamp + physician ID logged).
5. **Audit log** → records all changes and approvals for compliance.

## Customization (Optional)

- `--template <type>` — use a different note template (default: SOAP). Options: `soap` (Subjective–Objective–Assessment–Plan), `hpi-based` (History of Present Illness–focused), `problem-based` (Problem-oriented).
- `--format <output>` — for summarize, choose `paragraph` (default) or `bullet`.
- `--include-flags` — add a "Clinical Flags" section highlighting abnormalities or alerts (default: on for summarize, off for draft).

## Limitations & Safety

- **Not a Diagnostic Tool**: This skill does not predict diagnoses or recommend treatments. It organizes and summarizes clinical data you provide.
- **Hallucination Risk**: While guardrails reduce it, AI can still generate unsupported claims. Physician review catches these.
- **Garbage In, Garbage Out**: If the input is sparse or inaccurate, the draft will reflect that. Detailed, accurate input yields better drafts.
- **Privacy**: Do not paste real patient names or identifiers into this skill. Use synthetic or de-identified data, or rely on the system to fetch PHI over secure channels (not chat).

## Examples of Guardrail Enforcement

### ✓ Good: Facts Sourced

```
INPUT: "Exam: lungs clear, heart regular, abd soft"
DRAFT: "Cardiac exam: regular rate and rhythm. Pulmonary exam: clear to auscultation bilaterally. Abdominal exam: soft, non-tender."
→ All facts from input; good to sign.
```

### ✗ Bad: Fabrication

```
INPUT: "Exam: lungs clear"
DRAFT: "Abdominal exam: soft, liver edge 2 cm below costal margin, no peritoneal signs."
→ ✗ Abdominal exam not in input; this will be flagged by the skill as unsourced.
```

### ✓ Good: Gaps Flagged

```
INPUT: "Chief complaint: SOB. (No HPI, vitals, or exam provided)"
DRAFT: "
DRAFT — Pending Physician Review
Chief Complaint: Shortness of breath
Subjective: Limited history provided.
⚠ GAPS FLAGGED: No HPI available. No vital signs provided. No physical exam provided.
Objective: [Awaiting complete intake]
Assessment: Unable to assess pending complete history and exam.
Plan: Physician to complete history and exam."
→ Gaps flagged, not invented; safe.
```

---

## For Developers

The guardrails in this skill are enforced by:
1. **Prompt instructions** in the AI model call (e.g., "You must cite your source for every clinical fact").
2. **Post-generation validation** that scans the output for unsourced claims (regex/heuristic checker).
3. **Physician review** as the ultimate gate—physician can always override or reject the draft.

If you enhance this skill or build the application:
- Keep guardrails front-and-center; do not weaken them for speed.
- Log every draft generation (timestamp, model, input hash, output, physician who reviewed it) for audit.
- Always, always require physician approval before draft becomes final.

---

## Related

- See `docs/design/high-level-design.md` for system architecture, compliance strategy, and rollout phases.
- See `CLAUDE.md` for project instructions and the no-PHI rule.
