# Banner Health Clinical Documentation Assistant

**Reducing Physician Burnout at Scale**

An AI-assisted system for drafting clinical documentation and summarizing patient records, enabling physicians to spend less time on administrative work and more time with patients.

## Quick Links

- **[High-Level Design](docs/design/high-level-design.md)** — System architecture, requirements, tech stack, rollout phases
- **[Project Instructions](CLAUDE.md)** — Guidelines for contributors; no-PHI rule; core principles
- **[Clinical Workflow Skill](/.claude/skills/banner-health/SKILL.md)** — `/banner-health draft` and `/banner-health summarize` usage

## What This Project Does

The Banner Health assistant helps physicians draft notes and summarize charts through AI assistance, while maintaining full human oversight. Key features:

- **Note Drafting**: AI generates a draft clinical note from visit input (vitals, exam findings, history). Always labeled "DRAFT — Pending Physician Review."
- **Chart Summarization**: Quick summary of patient's problem list, meds, recent labs, and encounters for pre-visit prep.
- **Physician Review UI**: Physician edits, approves, or rejects the draft before it enters the patient record.
- **Full Audit Trail**: Every AI suggestion, edit, and approval is logged for compliance and accountability.

**Core Principle**: The physician is always in control. AI is a *draft assistant*, not an autonomous system. Nothing auto-commits to the record without physician approval.

## Project Phases

| Phase | Timeline | Goal |
|-------|----------|------|
| **Phase 0: Design** | Sept 2026 (Current) | Finalize architecture and compliance framework |
| **Phase 1: Synthetic Pilot** | Q4 2026 | MVP on test data; physician & IT feedback |
| **Phase 2: Limited Clinical Pilot** | Q1–Q2 2027 | Real (consented) data; measure time savings; fairness audit |
| **Phase 3: Scale** | Q3 2027+ | Rollout to organization; expand to other note types |

## For Contributors

1. **Read the design**: Start with `docs/design/high-level-design.md` to understand the system.
2. **Understand the constraints**: See `CLAUDE.md` for the no-real-patient-data rule and draft-status principle.
3. **Use the skill**: Try `/banner-health draft ...` or `/banner-health summarize ...` to test workflows.
4. **Review code**: When we build, code reviews will focus on safety (guardrails, audit logging, no auto-commit).

## Compliance & Safety

This project takes HIPAA compliance seriously:

- ✓ No real patient data in the repo (synthetic/sample data only)
- ✓ PHI access controlled and logged
- ✓ Draft status enforced (never auto-signed)
- ✓ Full audit trail (who did what, when)
- ✓ Physician override always available

See `docs/design/high-level-design.md` for details on security architecture, de-identification strategy, and risk mitigations.

## Next Steps

- **Compliance Review**: Legal review of HIPAA alignment
- **Vendor Evaluation**: Narrow LLM and EHR integration choices
- **Physician Advisory Group**: Gather feedback on workflows and UX priorities
- **Phase 1 Architecture**: Detailed API and database design for the MVP

## Support

- Questions about the design? See `docs/design/high-level-design.md` or ask in project channels.
- Issues with the hooks or scaffolding? Check `CLAUDE.md` or the `.claude/settings.json` and hook scripts.
- Ready to build? Create a new branch and start coding—but always check `CLAUDE.md` first for constraints.

---

*Banner Health — Reducing Physician Burnout at Scale*
