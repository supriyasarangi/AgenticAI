# Context Management System Setup

**Status:** ✅ Complete

This document summarizes the context trimming system built to enable efficient sub-agent work while maintaining focused, repeatable behavior.

## What Was Built

### 1. Core Module: `orchestration/context_manager.py`

**Purpose:** Deterministic context trimming for sub-agents

**Components:**
- **`Message` dataclass** — Represents a single conversation message with role, content, timestamp, and metadata
- **`ConversationSummary` dataclass** — Structured summary of compressed history with token counts and key decisions/findings
- **`ContextManager` class** — Core logic:
  - `trim_conversation()` — Split history into summary (old) + recent (full)
  - `prepare_agent_context()` — Format trimmed context for agent injection
  - `get_recent_prompts()` — Extract last N messages
  - `_create_summary()` — Compress messages deterministically
  - Token allocation calculations

- **`SubAgentContextBuilder` class** — Convenience methods:
  - `build_for_backend_engineer()`
  - `build_for_frontend_engineer()`
  - `build_for_p3_triage_agent()`

### 2. State Definition: `orchestration/state.py`

**Purpose:** Shared RAGState for LangGraph pipeline

**Contents:**
- `RAGState` dataclass — Carries query, domain selection, retrieved chunks, scores, claims, final answer, citations
- `Chunk`, `ClaimGraph`, `ConfidenceScore` — Schema stubs (expanded during implementation)

### 3. Updated Agent Specs

Each agent's `.md` file now includes a **Context Management** section:

- **backend-engineer.md** — Documents trimmed context, token allocation, and implications
- **frontend-engineer.md** — Same, with UI-specific context notes
- **p3-triage-agent.md** — Same, with audit-layer context notes

### 4. Documentation: `docs/context-management.md`

**Comprehensive guide covering:**
- How trimming works (token budgets, strategy)
- What agents see (example context injection)
- Practical implications for agents (what they can/cannot assume)
- Best practices for delegation
- Implementation details and usage code
- Debugging tips and configuration options

### 5. Example & Test: `eval/context_manager_example.py`

**Runnable examples demonstrating:**
- Basic conversation trimming
- Agent context preparation
- SubAgentContextBuilder usage
- Token allocation breakdown
- Token estimation

**Status:** ✅ All examples pass

## How It Works

### Token Budget Allocation

```
Total Context: 100,000 tokens
├─ Summary (historical):    ~15,000 tokens (12-15%)
├─ Recent messages (8-10):  ~15,000 tokens (15%)
├─ Instructions overhead:   ~17,000 tokens (20%)
└─ Available for work:      ~68,000 tokens (68-70%)
```

### Trimming Strategy

1. **Older messages (pre-recent) are summarized**
   - Compressed to ~12-15% of original tokens
   - Preserves key decisions and findings
   - Includes anchors (first + last messages)

2. **Recent messages kept in full**
   - Last 8-10 exchanges retained exactly
   - Provides immediate context for current task

3. **Agents receive context injection**
   - Summary + recent messages + agent instructions
   - Clear token budget breakdown
   - Constraint: "Your context is trimmed; reference docs for full history"

### Example Context for Agent

```
=== CONTEXT FOR BACKEND-ENGINEER ===

Context Budget: 100,000 tokens
  - Summary (history):     15,000 tokens
  - Recent messages:       85,000 tokens
  - Instructions overhead: 17,000 tokens
  - Available for work:    68,000 tokens

--- CONVERSATION SUMMARY (Historical Context) ---
[25 messages compressed to ~15,000 tokens]
[User] Initial requirement: Build RAG pipeline...
[Assistant] High-level approach: 8-stage pipeline...
... [17 intermediate messages] ...

Key Decisions Made:
  • Using LangGraph for orchestration
  • Model tiering: Sonnet/Opus/Haiku
  • Confidence scoring deterministic

Key Findings:
  • Verifier retry loop bounded
  • Citations schema-enforced
  • Domain filtering is hard pre-filter

--- RECENT CONTEXT (Last 8-10 Exchanges) ---
[1] USER: Start Phase 0 scaffolding
[2] CLAUDE: I'll create orchestration/state.py...
...
[8] USER: Now add context_manager for efficiency
```

## Usage

### For Delegation

When spawning an agent:

```python
Agent({
    description: "Phase 1: Build PubMed ingestion",
    prompt: """
You are backend-engineer. Your context is trimmed to recent exchanges.

Task: Build ingestion/pubmed_connector.py

Reference: docs/units-of-work.md Phase 1

Your context allocation:
  - 15,000 tokens: historical summary
  - 85,000 tokens: recent 8-10 exchanges + instructions
  - 68,000 tokens: available for your code

Go.
"""
})
```

### In Code

```python
from orchestration.context_manager import ContextManager, Message, SubAgentContextBuilder

# Create manager
manager = ContextManager(total_context_tokens=100_000)

# Prepare history
history = [
    Message(role="user", content="..."),
    Message(role="assistant", content="..."),
]

# Trim for an agent
trimmed = manager.trim_conversation(history)
context = manager.prepare_agent_context(history, agent_name="backend-engineer")

# Or use convenience builder
builder = SubAgentContextBuilder(manager)
backend_context = builder.build_for_backend_engineer(history)
```

## Key Implications

### For Agents

**✓ You CAN assume:**
- Recent 8-10 exchanges are visible in full
- Your agent spec (`.md` file) is authoritative
- Documentation in `docs/` is accurate and complete
- Config files define your constraints

**✗ You CANNOT assume:**
- Full conversation history beyond recent 8-10 exchanges
- Implementation details discussed earlier (reference docs instead)
- That the project is in a phase you last heard about

### For Delegation

- Each agent receives focused context, efficient token usage
- Work is deterministic: same requirements + same config → same code
- All agents can work in parallel without interference
- Long conversations don't bloat agent contexts — they stay trimmed

## Configuration

Adjust allocations if needed:

```python
manager = ContextManager(
    total_context_tokens=100_000,
    summary_budget_ratio=0.10,  # 10% for summary (instead of 15%)
    recent_messages_count=8     # Keep 8 messages (instead of 10)
)
```

## Testing

Run the example to verify the system works:

```bash
python -m eval.context_manager_example
```

**Output:** ✅ All 5 examples pass with token allocation and context formatting demonstrated

## Files Changed/Created

**New files:**
- `orchestration/__init__.py`
- `orchestration/context_manager.py` (330 lines)
- `orchestration/state.py` (60 lines)
- `docs/context-management.md` (comprehensive guide)
- `eval/context_manager_example.py` (runnable examples + tests)
- `CONTEXT_MANAGEMENT_SETUP.md` (this file)

**Updated files:**
- `.claude/agents/backend-engineer.md` — Added context management section
- `.claude/agents/frontend-engineer.md` — Added context management section
- `.claude/agents/p3-triage-agent.md` — Added context management section

## Next Steps

### For Immediate Use

1. **Update agent prompts** — When delegating to an agent, reference this context management system:
   ```
   "Your context is trimmed to ~15% historical summary + recent 8-10 exchanges.
    Reference docs/ for full project history. See docs/context-management.md."
   ```

2. **Pass agent context** — Use `SubAgentContextBuilder` when spawning agents to ensure they receive trimmed context

3. **Monitor token usage** — Track allocations with `manager._get_allocations()` as agents work

### For Future Enhancement

- **Semantic summarization** — Use embedding-based clustering to extract most important messages
- **Agent-specific budgets** — Allocate more tokens to critical phases (Verifier), fewer to others
- **LangGraph checkpoints** — Use checkpoints as context boundaries instead of message count
- **Auditing** — Keep context references for full conversation replay if needed

---

See `AGENT_DELEGATION_GUIDE.md` for how to delegate work to the three agents with trimmed context.

See `docs/context-management.md` for detailed implementation reference.

See `eval/context_manager_example.py` for working code examples.
