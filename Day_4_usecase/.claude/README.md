# Claude Code Project Configuration

This directory contains project-specific configuration for Claude Code and agent management.

## Files

### `agents/`
**Agent specifications** — Detailed role definitions for the three project agents:
- **`backend-engineer.md`** — RAG pipeline development (ingestion, orchestration, agents, eval)
- **`frontend-engineer.md`** — Streamlit demo UI
- **`p3-triage-agent.md`** — Quality gates for low-confidence claims

Each agent's spec includes:
- Module ownership (what files they own)
- Context management expectations
- Integration contracts with other agents
- Non-negotiables and constraints

### `SKILL.md`
**Project skill** — Defines the delegation workflow for this project

**What it does:**
- Streamlines context trimming using `ContextManager`
- Delegates work to isolated sub-agents
- Manages agent spawning with proper context

**How to use:**
```
/rag-delegate backend Phase 1: Build PubMed ingestion
/rag-delegate frontend Update citation rendering
/rag-delegate triage Validate thresholds
```

See file for manual delegation examples.

### `settings.json`
**Project settings & hooks** — Configuration file with:

1. **Permissions** — Approved operations (read/write) and approval-required operations (delete, force-push, etc.)

2. **Hooks** — Automated checks when files change:
   - `on_save_orchestration_files` — Verify imports when orchestration/ changes
   - `on_save_ui_files` — Check Streamlit syntax when ui/ changes
   - `on_save_config_files` — Validate YAML when config/ changes
   - `on_agent_spawn` — Remind about context trimming
   - `on_phase_complete` — Suggest next steps

3. **Agent Profiles** — Configuration for each agent:
   - Model, context window, trimming ratio
   - Modules owned
   - Recent messages to retain

4. **Environment** — Vars for API keys, paths, etc.

5. **Testing** — Commands to run tests

6. **Documentation** — Reference to guides and specs

## Key Directories

```
.claude/
├── agents/                          # Agent specifications
│   ├── backend-engineer.md
│   ├── frontend-engineer.md
│   └── p3-triage-agent.md
├── SKILL.md                         # Project skill
├── settings.json                    # Project configuration & hooks
└── README.md                        # This file
```

## How Claude Code Uses These Files

1. **Agent specs** — When spawning `backend-engineer`, `frontend-engineer`, or `p3-triage-agent`, Claude Code loads their `.md` spec to understand their role, modules, and constraints.

2. **Settings** — When opening the project, Claude Code reads `settings.json` to:
   - Apply permission rules
   - Execute hooks on file changes
   - Load environment variables
   - Use agent profile configs for context management

3. **Skill** — When you type `/rag-delegate` or need to delegate work, the SKILL.md provides the workflow definition.

## Delegation Workflow

To delegate work to an agent:

1. **Use the skill** (future):
   ```
   /rag-delegate backend Phase 1: Build PubMed ingestion
   ```

2. **Or manually**:
   ```python
   from orchestration.context_manager import SubAgentContextBuilder, ContextManager
   
   manager = ContextManager(total_context_tokens=100_000)
   builder = SubAgentContextBuilder(manager)
   backend_context = builder.build_for_backend_engineer(history)
   
   Agent({description: "...", prompt: f"{backend_context}\n\nTask: ..."})
   ```

## Context Management

Each agent receives trimmed context:
- **15%** — Historical summary (compressed)
- **15%** — Recent 8-10 exchanges (full)
- **17%** — Instructions/overhead
- **53%** — Available for work

See `docs/context-management.md` for details.

## Agent Isolation

Each agent owns specific modules and cannot modify others' work:

| Agent | Modules | Contract |
|-------|---------|----------|
| backend-engineer | `ingestion/`, `agents/`, `orchestration/`, `domain/`, `config/`, `schemas/`, `eval/` | Outputs RAGState to orchestration/graph.py |
| frontend-engineer | `ui/` | Reads RAGState from orchestration/graph.py |
| p3-triage-agent | P3 triage workflow | Reads RAGState, outputs JSON reports |

## Development Guidelines

1. **Before modifying agent specs** — Review AGENT_DELEGATION_GUIDE.md to understand phases and ownership
2. **When delegating work** — Use SubAgentContextBuilder to trim context properly
3. **When agents report completion** — Check implementation against phase exit criteria in docs/units-of-work.md
4. **For questions about context** — See docs/context-management.md

## Quick Links

- **Delegation guide** — `AGENT_DELEGATION_GUIDE.md`
- **Context management** — `docs/context-management.md`
- **Architecture** — `docs/architecture.md`
- **Units of work** — `docs/units-of-work.md`
- **Requirements** — `docs/requirements.md`

---

**Questions?** Check the main project guides or agent specs in this directory.
