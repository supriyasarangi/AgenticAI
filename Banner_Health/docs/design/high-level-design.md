# Banner Health Clinical Documentation Assistant — High-Level Design

**Project**: Banner Health — Reducing Physician Burnout at Scale  
**Date**: September 2026  
**Status**: Design Phase 0

---

## 1. Problem & Goals

### The Problem

Physicians spend an estimated 6–9 hours per week on administrative and documentation tasks, often at the end of long clinical shifts. This time—which could be spent on patient care, family, or recovery—drives burnout and reduces both physician well-being and the time available for complex patient interactions.

### The Goals

- Reduce time physicians spend on clinical documentation (note-writing, chart review) through AI-drafted notes and chart summaries
- Maintain physician autonomy and oversight: AI is a *draft assistant*, never autonomous—the physician always reviews and approves before anything enters the patient record
- Demonstrate a scalable pattern for AI-assisted healthcare workflows that prioritizes compliance, safety, and human judgment over pure automation
- Become a reference model for reducing physician burnout through thoughtful AI integration

---

## 2. Scope

### In Scope (Phase 0–1)

- **Ambient Note Drafting**: transforms visit input (structured EHR data + optional visit transcript/dictation) into a draft clinical note in the organization's standard format
- **Chart Summarization**: generates a concise brief of the patient's problem list, active medications, recent lab results, and recent encounters for pre-visit preparation
- **Physician Review UI**: a web interface where physicians can read, edit, and approve (or reject) AI drafts before they are finalized; draft status always visible
- **Audit Logging**: immutable, queryable record of every AI suggestion, physician edit, and approval—who did what, when, on which patient
- **HIPAA Compliance**: PHI encryption, RBAC, BAA-covered infrastructure, audit trail

### Out of Scope (For Future Phases)

- Autonomous charting: code submissions directly to the patient record without physician review/signature
- Clinical decision support: diagnosis prediction, treatment recommendations
- Billing and coding automation
- Real-time intraoperative assistance
- Multi-language support (Phase 2+)

---

## 3. Users & Personas

| Persona | Role | Key Need |
|---------|------|----------|
| **Dr. Chen** | Attending Physician | Wants faster note-writing without sacrificing quality or oversight; won't trust a system that auto-commits |
| **Dr. Patel** | Resident | Needs learning opportunities + time savings; concerned about over-reliance on AI |
| **Nurse Rodriguez** | Nursing Staff (secondary) | May contribute structured input (vitals, intake notes) but does not approve final clinical documentation |
| **Admin Torres** | Compliance/IT | Must ensure audit trail, PHI safeguards, and system reliability |

---

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Physician Review UI                           │
│                (Web: approve/edit/reject drafts)                │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │ (physician edits & approvals)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               Audit & Compliance Layer                           │
│        (Immutable log: who/what/when, retention policy)         │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            AI Orchestration Layer                                │
│  • RAG: retrieval-augmented generation over patient record      │
│  • Prompt templates: "draft note", "summarize chart"             │
│  • Guardrails: no fabrication, cite sources, flag ambiguities   │
│  • Hallucination checks: does output match input facts?          │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│      PHI Access & De-identification Layer                        │
│  • RBAC: physician only sees own patients (+ delegates)          │
│  • Minimum-necessary data access                                 │
│  • Optional de-identification for model calls                    │
│  • Encryption in transit/at rest                                 │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               EHR Integration Layer                              │
│  • FHIR API connectors (read-mostly; writes only post-approval)  │
│  • HL7v2 gateways (legacy systems)                               │
│  • Patient record fetch: demographics, problem list, meds, labs  │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

1. **EHR Integration** — Securely fetch patient data (demographics, active problems, medications, recent labs/encounters) from the hospital's EHR system via FHIR or HL7v2; validate data schema.

2. **PHI Access & De-identification** — Enforce role-based access control; ensure physicians only access their own patients' data; optionally strip identifiers before sending to external AI models (if not BAA-covered); handle encryption.

3. **AI Orchestration** — Use retrieval-augmented generation (RAG) to ground AI outputs in the actual patient data. Maintain separate prompt templates for note drafting vs. chart summarization. Implement guardrails (e.g., "cite your source for every clinical fact") and basic hallucination detection.

4. **Audit & Compliance** — Log every event: AI suggestion generated, physician viewed draft, physician edited field X, physician approved/rejected. Immutable logs with retention policy per HIPAA.

5. **Review UI** — Serve drafts to physicians for review. Show source citations. Support in-browser editing. Capture approval/rejection with timestamp and (optional) reason.

---

## 5. Core Capabilities

### 5.1 Clinical Note Drafting

**Input**: Structured visit data (date, chief complaint, vital signs, physical exam findings, assessment) + optional visit transcript/scribe notes.

**Process**:
1. Fetch patient's problem list, active medications, and recent encounter history from EHR.
2. Use RAG to ground the AI model on the patient's actual chart.
3. Prompt the model to draft a clinical note in the organization's standard format (e.g., SOAP: Subjective, Objective, Assessment, Plan).
4. Attach source citations (e.g., "Problem list from EHR, dated 2026-09-20").
5. Label output as **DRAFT — Pending Physician Review**; store in draft status in the EHR (not signed, not visible to other users).

**Output**: A draft clinical note with physician approval pending. The note is never auto-committed; the physician must explicitly review and approve it.

### 5.2 Chart Summarization

**Input**: Patient ID.

**Process**:
1. Fetch problem list, active medication list, recent lab results (last 3 months), recent encounters (last 6 months).
2. Use RAG to condense this data into a one-paragraph or bullet-point summary suitable for pre-visit preparation.
3. Highlight any recent abnormalities or changes in medication.

**Output**: A brief (< 200 words) chart summary for the physician to review before seeing the patient.

---

## 6. Data Flow

```
┌──────────────────┐
│  EHR System      │ (read)
│  • Problems      │────┐
│  • Meds          │    │
│  • Labs          │    │
│  • Encounters    │    │
└──────────────────┘    │
                        ▼
              ┌──────────────────────┐
              │ PHI Access & RAG     │
              │ (fetch + de-id)      │
              └──────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────┐
    │  AI Orchestration                       │
    │  • Prompt: "draft a note" or            │
    │    "summarize this chart"               │
    │  • Guardrails + hallucination check     │
    └─────────────────────────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────┐
    │  Audit Log: "AI generated draft for     │
    │  patient X at [time] with [model ID]"   │
    └─────────────────────────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────┐
    │  Review UI: Display to Physician        │
    │  • Show draft + source citations        │
    │  • Allow edit / approve / reject        │
    └─────────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
       REJECT        EDIT + APPROVE  APPROVE
         │              │              │
         ▼              ▼              ▼
    Discard      Audit Log +      Audit Log +
    + Log        (optional       Write to EHR
    Reason       reasoning)      (signed)
```

**Key Principle**: Every draft is draft status until the physician explicitly approves it. Even then, the approval is logged with the physician's signature and timestamp. The physician can always override AI suggestions; override is the default state.

---

## 7. Security & Compliance

### HIPAA Requirements

- **Encryption in Transit**: TLS 1.2+ for all network traffic.
- **Encryption at Rest**: Patient data encrypted with AES-256 or equivalent; encryption keys managed by HSM or cloud provider's managed service.
- **RBAC**: Physicians access only their own patient panels (or those delegated to them). Admins cannot view clinical content, only audit logs and system health.
- **Audit Trail**: Every read, write, approve, reject, and edit is logged with user ID, timestamp, and action type. Logs are immutable and retained per org policy (typically 7 years for healthcare).
- **Minimum Necessary Access**: The AI layer only receives the specific patient data needed for the current task (e.g., problem list + recent labs for chart summary), not the entire medical record.
- **BAA-Covered Infrastructure**: If using a third-party LLM (e.g., Azure OpenAI, AWS Bedrock), it must be under a Business Associate Agreement with the covered entity. No PHI sent to non-BAA providers; de-identify first if necessary.

### De-identification Strategy

Option 1 (Recommended): Use BAA-covered model endpoint (e.g., Azure OpenAI with Enterprise Compliance), send PHI directly.

Option 2: De-identify before model call—strip names, MRNs, dates; relabel as "Patient A, age 50, Female." May reduce quality but maximizes data privacy.

Option 3: Hybrid—keep temporal relations (e.g., "2 weeks ago") but strip absolute dates; strip identifiers.

### Bias & Fairness

- Periodically audit AI outputs for demographic disparities (e.g., Do summaries for older patients vs. younger patients differ systematically?).
- Ensure physician override behavior is logged and reviewed.
- Include fairness assessment as part of Phase 1 pilot.

---

## 8. Non-Functional Requirements

| Requirement | Target | Rationale |
|---|---|---|
| **Latency** | Draft generated in < 10 seconds | Physician workflow interruption minimized |
| **Availability** | 99.5% uptime | Healthcare-critical; brief downtime tolerable, extended outage unacceptable |
| **Accuracy** | > 95% of AI-drafted notes require ≤ 3 edits by physician | Measure edit-distance to assess draft quality |
| **Hallucination Rate** | ≤ 2% unsupported clinical claims per audit sample | External reviewer spot-checks; flagged claims must cite source |
| **Audit Log Completeness** | 100% of actions logged; zero loss | Immutable append-only store |
| **Scalability** | Support up to 10,000 concurrent physicians (Phase 3) | Horizontal scaling; stateless services |

---

## 9. Technology Stack (Options — Not Commitments)

| Component | Option A (Recommended) | Option B (Alternative) |
|---|---|---|
| **LLM Hosting** | Azure OpenAI (GPT-4 under BAA) | AWS Bedrock (Anthropic Claude under BAA) |
| **EHR Integration** | HL7 FHIR R4 APIs | Epic FHIR on FIRE; Cerner FHIR |
| **RAG Engine** | LangChain + FAISS or Pinecone | LlamaIndex + custom vector DB |
| **Web UI** | React 18 + TypeScript + Tailwind | Vue.js + Bootstrap |
| **Backend** | Python FastAPI + asyncio | Node.js Express + Bull queue |
| **Database** | PostgreSQL (structured) + S3 (audit logs) | MongoDB + DynamoDB |
| **Infrastructure** | Azure App Service + Azure SQL + Key Vault | AWS ECS + RDS + Secrets Manager |

**Principle**: Use managed services (cloud provider's LLM endpoints, DBs, encryption) to offload compliance burden. Avoid self-hosted LLM inference—BAA complexity and operational overhead.

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Hallucinated Clinical Content** | Physician relies on false AI suggestion; patient harm | Mandatory physician review (always); source citation for every claim; external spot-check audit; fallback to manual drafting |
| **Over-Automation / Automation Bias** | Physician trusts AI too much, under-reviews edits | Draft-only status (not auto-signed); UI friction on auto-approve; mandatory read/review before approval; training on risks |
| **PHI Leakage** | Confidentiality breach; regulatory fine; loss of trust | Access controls + role-based redaction; encryption at rest/transit; PreToolUse hook to block accidental PHI commits during development |
| **Regulatory Non-Compliance** | Audit failure; loss of license; liability | Immutable audit trail; BAA-covered infrastructure; HIPAA compliance checklist in design and code review; legal review before pilot |
| **Model Bias** | AI outputs systematically disadvantage certain demographics | Regular bias audit (fairness metrics by age/gender/race); override logging to detect systematic under-trust; Phase 2 fairness study |
| **Physician Rejection / Non-Adoption** | System sits unused; no benefit realized | Early physician involvement in UX design; address friction points (speed, accuracy); pilot with enthusiastic early adopters; measure satisfaction |

---

## 11. Rollout Phases

### Phase 0: Design (Current)
- Finalize architecture and technical design (this doc).
- Set compliance requirements and audit framework.
- Initial vendor/architecture decisions.

### Phase 1: Synthetic Data Pilot (Q4 2026)
- Build MVP: note drafting + chart summarization on synthetic patient data.
- Physician and IT staff test in sandbox; gather UX feedback.
- Security audit and HIPAA readiness review.
- Success metric: 5+ physicians can draft and review a note in < 3 minutes.

### Phase 2: Limited Clinical Pilot (Q1–Q2 2027)
- Deploy to single department (e.g., Internal Medicine) with real (but carefully consented) patient data.
- Measure time savings, edit patterns, physician satisfaction.
- Fairness audit (demographic disparities?).
- Success metric: Avg. documentation time reduced by ≥ 15%; physician satisfaction ≥ 4/5.

### Phase 3: Scale (Q3 2027+)
- Rollout to additional departments.
- Expand to other note types (discharge summaries, procedure notes).
- Integrate with EHR alerts (e.g., "auto-summarize new lab result" on order entry).
- Target: 80% of physicians actively using the system; organization-wide documentation time reduced by 20%+.

---

## 12. Success Metrics

| Metric | Baseline | Target (Phase 1 / 2 / 3) |
|---|---|---|
| **Physician Documentation Time (min/patient encounter)** | 12–15 | 10 / 8 / 5 |
| **Physician Satisfaction (1–5 scale)** | N/A | 3.5 / 4.0 / 4.5 |
| **AI Draft Quality (avg. edits per note)** | N/A | ≤ 3 / ≤ 2 / ≤ 1 |
| **System Uptime (%)** | N/A | 99.0 / 99.5 / 99.9 |
| **User Adoption Rate (% of eligible physicians)** | N/A | 30 / 60 / 80 |
| **Audit Trail Completeness (% events logged)** | N/A | 100 / 100 / 100 |
| **Hallucination Rate (% of audited drafts)** | N/A | ≤ 2 / ≤ 1 / ≤ 0.5 |

---

## 13. Glossary

- **HIPAA**: Health Insurance Portability and Accountability Act; US federal privacy/security law.
- **BAA**: Business Associate Agreement; contract required when a covered entity (hospital) shares PHI with a third party (e.g., cloud vendor).
- **PHI**: Protected Health Information; any data that can identify a patient (name, MRN, date of birth, etc.).
- **RBAC**: Role-Based Access Control; system that grants permissions based on user role.
- **RAG**: Retrieval-Augmented Generation; technique where an LLM is given specific context (e.g., patient chart) before generating output, reducing hallucination.
- **FHIR**: Fast Healthcare Interoperability Resources; modern standard for health data exchange.
- **HL7v2**: Legacy healthcare data standard.
- **Draft Status**: Note is visible only to the creating physician and admins; not signed, not visible to other clinicians, not actionable for clinical workflows.
- **Audit Log**: Immutable record of system actions; stored separately from modifiable clinical data.

---

## Next Steps

1. **Legal & Compliance Review**: Confirm design aligns with HIPAA, state regulations, and organizational policy.
2. **Vendor Evaluation**: Narrow technology stack choices (LLM, FHIR integration, hosting).
3. **Physician Advisory Group**: Gather feedback on workflows, UX priorities, risk concerns.
4. **Project Charter**: Define roles, timeline, budget for Phase 1 pilot.
5. **Architecture Deep Dives**: For each layer, define APIs, error handling, failure modes.
