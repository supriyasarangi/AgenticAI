# Project Skill: Agentic RAG Context Management

**Trigger:** `/rag-delegate` or when delegating work to backend-engineer, frontend-engineer, or p3-triage-agent

**Purpose:** Streamline delegation of work to isolated sub-agents with deterministic context trimming

## What This Skill Does

Prepares trimmed conversation context and delegates tasks to the three project agents:
- **backend-engineer** — RAG pipeline (ingestion, orchestration, agents)
- **frontend-engineer** — Streamlit demo UI
- **p3-triage-agent** — Quality gates for low-confidence claims

## How to Use

### Option 1: Slash Command (Future)
```
/rag-delegate backend Phase 1: Build PubMed ingestion
/rag-delegate frontend Update citation rendering for accuracy
/rag-delegate triage Validate decision thresholds for escalation
```

### Option 2: Manual Delegation (Current)
```python
from orchestration.context_manager import ContextManager, SubAgentContextBuilder

manager = ContextManager(total_context_tokens=100_000)
builder = SubAgentContextBuilder(manager)

# Get trimmed context for each agent
backend_context = builder.build_for_backend_engineer(history)
frontend_context = builder.build_for_frontend_engineer(history)
triage_context = builder.build_for_p3_triage_agent(history)

# Spawn agents
Agent({description: "...", prompt: f"{backend_context}\n\nTask: ..."})
```

## Key Features

- **Deterministic context trimming** (12-15% summary + 15% recent + 68% work)
- **Agent isolation** (each owns specific modules, no overlap)
- **Parallel execution** (all three can work simultaneously)
- **Token efficiency** (no context bloat from long conversations)

## Reference

- `AGENT_DELEGATION_GUIDE.md` — Complete delegation guide with examples
- `CONTEXT_MANAGEMENT_SETUP.md` — Implementation details
- `docs/context-management.md` — Comprehensive context management reference
- `.claude/agents/backend-engineer.md` — Backend agent spec
- `.claude/agents/frontend-engineer.md` — Frontend agent spec
- `.claude/agents/p3-triage-agent.md` — P3 triage agent spec

## Agent Specs

All three agents have updated `.md` files with:
- Module ownership (what files they own)
- Context management expectations (trimmed context)
- Contract with other agents (how they integrate)
- Non-negotiables (what they must/must not do)

## Phases of Work

- **Phase 0:** ✅ Complete (backend scaffolding)
- **Phase 1:** PubMed ingestion + retrieval
- **Phase 2:** Multi-source + domain filtering
- **Phase 3:** Ranking + confidence scoring
- **Phase 4:** Synthesis + citation + verification
- **Phase 5:** Demo UI + eval harness (✅ UI complete, harness pending)
- **Phase 6:** Stretch goals (additional regulatory connectors)

## Context Management

Each agent receives:
- **Historical summary** (~15% budget) — compressed conversation history
- **Recent exchanges** (~15% budget) — last 8-10 full messages
- **Instructions** (~17% budget) — role spec, constraints
- **Work budget** (~53% available) — for actual task execution

See `docs/context-management.md` for full details.

## Quick Start

To delegate Phase 1 work (PubMed ingestion):

```python
Agent({
    description: "Build PubMed ingestion connector",
    prompt: """You are backend-engineer.

Your context is trimmed to recent exchanges. Reference docs/ for full history.

Task: Phase 1 — Build ingestion/pubmed_connector.py
- Fetch real PubMed data
- Implement chunking
- Embed with sentence-transformers
- Upsert to Chroma

Reference:
  - docs/units-of-work.md Phase 1
  - docs/architecture.md §2
  - orchestration/state.py (Chunk schema)

Go."""
})
```

---

**See AGENT_DELEGATION_GUIDE.md for more examples and complete workflow.**
