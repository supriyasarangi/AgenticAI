# src/ — Application Code (Placeholder)

This folder will hold the application code for the Banner Health clinical documentation assistant.

## Intended Module Layout

When implementation begins, expect the following structure:

```
src/
├── ehr_integration/          # EHR connectors (FHIR, HL7v2)
│   ├── fhir_client.py
│   ├── hl7v2_adapter.py
│   └── __init__.py
├── phi_access/               # PHI access control and de-identification
│   ├── rbac.py
│   ├── de_identifier.py
│   └── __init__.py
├── ai_orchestration/         # AI model orchestration and RAG
│   ├── prompt_templates.py
│   ├── rag_engine.py
│   ├── guardrails.py
│   └── __init__.py
├── audit_logging/            # Immutable audit trail
│   ├── audit_store.py
│   ├── logger.py
│   └── __init__.py
├── review_ui/                # Physician review web interface
│   ├── app.py
│   ├── routes.py
│   ├── models.py
│   └── __init__.py
└── utils/                    # Shared utilities
    ├── config.py
    ├── security.py
    └── __init__.py
```

## Principles

- **Layer Responsibilities**: Each module maps to a layer in the high-level architecture (see `docs/design/high-level-design.md`).
- **No Auto-Commit**: The review UI is the gate; AI drafts are always draft status until physician approval.
- **Full Audit**: Every action in the orchestration, access, and review layers is logged.
- **Physician Override**: The physician can always reject, edit, or ignore AI suggestions.

## When to Start Coding

- [ ] Phase 1 project charter approved
- [ ] Compliance review complete
- [ ] Vendor decisions finalized (LLM, EHR integration, hosting)
- [ ] Physician advisory group feedback incorporated

See `docs/design/high-level-design.md` for rollout timeline and success metrics.
