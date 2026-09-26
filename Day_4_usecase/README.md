# Agentic RAG for Drug-Discovery Literature Review

An agentic RAG system that helps R&D teams find the right evidence across scientific
literature, clinical trials, and regulatory documents (FDA, EMA, ICH, PMDA, MHRA),
judge confidence in that evidence, and trace every claim back to its exact source.

This repository currently contains the **planning phase only** — no implementation
yet. Start with [`docs/intent.md`](docs/intent.md).

## Planning documents

- [`docs/intent.md`](docs/intent.md) — problem, goals, non-goals
- [`docs/requirements.md`](docs/requirements.md) — functional requirements & acceptance criteria
- [`docs/domain-model.md`](docs/domain-model.md) — therapeutic-area × jurisdiction taxonomy
- [`docs/architecture.md`](docs/architecture.md) — agent pipeline, ingestion, confidence scoring, citation tracing, tech stack
- [`docs/units-of-work.md`](docs/units-of-work.md) — phased build plan
- [`docs/non-functional.md`](docs/non-functional.md) — POC constraints and extensibility notes
- [`docs/evaluation.md`](docs/evaluation.md) — golden set, faithfulness, and calibration checks

## Implementation agents

Build work is split across two project-scoped subagents defined in `.claude/agents/`:
`backend-engineer` (pipeline, ingestion, scoring, eval) and `frontend-engineer`
(Streamlit demo UI). See [`docs/architecture.md`](docs/architecture.md) §8 for the
split and [`docs/units-of-work.md`](docs/units-of-work.md) for phase ownership.
