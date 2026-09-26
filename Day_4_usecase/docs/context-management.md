# Context Management for Sub-Agents

## Overview

Sub-agents working on this project operate under **deterministic context trimming**. This ensures:
- Efficient token usage across long-running work
- Clear boundaries on what agents can assume from history
- Consistent, repeatable behavior regardless of conversation length

## How It Works

### Token Budget Allocation

Total context window (e.g., 100,000 tokens) is divided:

```
Summary (Historical Context)    ~12-15%  (12,000-15,000 tokens)
Recent Messages (8-10 exchanges) ~15%     (15,000 tokens)
Instructions & Overhead          ~20%     (20,000 tokens)
Available for Work              ~50-55%   (50,000-55,000 tokens)
```

### Trimming Strategy

**When an agent receives context:**

1. **Old messages (pre-recent) are summarized**
   - Full message history > 10 exchanges ago compressed to ~12-15% of original tokens
   - Summary captures key decisions, findings, and anchors (first + last messages)
   - Stored as text summary with metadata

2. **Recent messages kept in full**
   - Last 8-10 user/assistant exchanges retained exactly as-is
   - Provides immediate context for current task
   - Agent can reference recent decisions and code without interpretation

3. **Instructions + metadata** provided
   - Agent's role and scope (from their `.md` file)
   - Available token budget breakdown
   - Constraint: "Your context is trimmed; reference docs/ for full project history"

### What Agents See

Example context injection for backend-engineer:

```
=== CONTEXT FOR BACKEND-ENGINEER ===
Context Budget: 100,000 tokens
  - Summary (history):     12,000 tokens (25 messages compressed)
  - Recent messages:       15,000 tokens (last 8 exchanges)
  - Instructions overhead:  5,000 tokens
  - Available for work:    68,000 tokens

--- CONVERSATION SUMMARY (Historical Context) ---
[25 messages compressed to ~12,000 tokens]
[User] Initial requirement: Build RAG pipeline for drug-discovery...
[Assistant] High-level approach: 8-stage pipeline with LangGraph...
... [17 intermediate messages] ...
[User] How should we handle multi-source ranking?
[Assistant] Use Evidence Ranker with pure Python dedup...

Key Decisions Made:
  • Using LangGraph instead of CrewAI for orchestration
  • Model tiering: Sonnet 5 default, Opus 5 for Verifier, Haiku 4.5 for triage
  • Confidence scoring deterministic (Python), not LLM-driven

Key Findings:
  • Verifier retry loop bounded to prevent infinite recursion
  • Citations must be schema-enforced, not prompt-only
  • Domain filtering is hard metadata pre-filter, not soft re-rank

--- RECENT CONTEXT (Last 8-10 Exchanges) ---
[1] USER: Start Phase 0 scaffolding — repo structure, schemas, LangGraph skeleton
[2] CLAUDE: I'll create orchestration/state.py with RAGState...
...
[10] USER: Now add context_manager for token efficiency
```

## Practical Implications

### For Agents

**✓ You CAN assume:**
- Recent 8-10 exchanges are visible in full
- Your agent spec in `.claude/agents/*.md` is authoritative and always available
- Documentation in `docs/` is accurate and complete
- Config files (`config/*.yaml`) define your constraints

**✗ You CANNOT assume:**
- Full conversation history beyond the recent 8-10 exchanges
- Implementation details discussed earlier in conversation (reference docs instead)
- That the project is in the phase you last heard about (check `docs/units-of-work.md` exit criteria)

**→ Best practice:**
- When uncertain, reference documentation: "See `docs/units-of-work.md` Phase 3 for scope"
- Work is deterministic: same requirements + same config → same code
- If you need project context, ask for clarification or reference the docs

### For Delegation

**When spawning an agent with a task:**

```python
Agent({
    description: "Phase 1: Build PubMed ingestion connector",
    prompt: """
You are backend-engineer. Your context is trimmed to recent exchanges.

Task: Build ingestion/pubmed_connector.py — fetch real PubMed data, chunk, embed.

Reference:
  - docs/units-of-work.md Phase 1 for exit criteria
  - docs/architecture.md §2 for ingestion topology
  - config/domains.yaml for therapeutic-area filtering
  - schemas/claim_graph.py for metadata structure

Your context is allocated:
  - 12,000 tokens: historical summary (you don't need to know everything)
  - 15,000 tokens: recent 8-10 exchanges (immediate context)
  - 68,000 tokens: available for your code work

Go.
"""
})
```

**Result:** Agent has exactly what it needs, focused on the task, efficient token usage.

## Implementation Details

See `orchestration/context_manager.py`:

- **`ContextManager` class** — core trimming logic
  - `trim_conversation()` — split history into summary + recent
  - `prepare_agent_context()` — format context for injection
  - `_create_summary()` — compress old messages

- **`ConversationSummary` dataclass** — structured summary with:
  - Compressed text, token counts, ratio
  - Key decisions and findings extracted
  - Metadata for auditing

- **`SubAgentContextBuilder`** — convenience methods:
  - `build_for_backend_engineer()`
  - `build_for_frontend_engineer()`
  - `build_for_p3_triage_agent()`

### Usage in Code

```python
from orchestration.context_manager import ContextManager, Message

# Create manager with 100k token budget
manager = ContextManager(total_context_tokens=100_000)

# Prepare history as Message objects
history = [
    Message(role="user", content="..."),
    Message(role="assistant", content="..."),
    # ... more messages
]

# Trim for an agent
trimmed = manager.trim_conversation(history)
agent_context = manager.prepare_agent_context(history, agent_name="backend-engineer")
```

## Debugging

**Check context allocation:**
```python
manager = ContextManager()
print(manager._get_allocations())
# {'total_tokens': 100000, 'summary_tokens': 12000, ...}
```

**Estimate tokens for a message:**
```python
ContextManager.estimate_tokens("Your text here")
# Returns rough token count
```

**Verify summary quality:**
```python
trimmed = manager.trim_conversation(history)
summary = trimmed["summary"]
print(f"Ratio: {summary.summary_ratio:.1%}")  # Should be ~12-15%
print(f"Key decisions: {summary.key_decisions}")
```

## Configuration

Adjust allocations by passing kwargs to `ContextManager`:

```python
# More aggressive trimming (only 10% for summary)
manager = ContextManager(
    total_context_tokens=100_000,
    summary_budget_ratio=0.10,
    recent_messages_count=8  # Keep last 8 messages instead of 10
)
```

## Future Extensions

- **Semantic summarization** — use embedding-based clustering to extract most important messages
- **Agent-specific budgets** — allocate more tokens to critical phases (Verifier), fewer to others
- **Context replay** — reconstruct full conversation for auditing (keep references, not full text)
- **Checkpointing** — use LangGraph checkpoints as context boundaries instead of message count

---

See `AGENT_DELEGATION_GUIDE.md` for how to delegate work to agents with trimmed context.
