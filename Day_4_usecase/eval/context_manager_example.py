"""
Example: Using ContextManager for agent context trimming.

Demonstrates:
- Creating a conversation history
- Trimming for different agents
- Estimating token efficiency
- Formatting context for injection
"""

from orchestration.context_manager import (
    ContextManager,
    Message,
    SubAgentContextBuilder,
)
from datetime import datetime


def create_sample_history():
    """Create a sample conversation history for demonstration."""
    return [
        Message(
            role="user",
            content="Build an agentic RAG system for drug-discovery literature review.",
            timestamp=datetime(2026, 9, 19, 8, 0),
        ),
        Message(
            role="assistant",
            content="I'll create a comprehensive planning structure with architecture.md, requirements.md, domain-model.md, and units-of-work.md.",
            timestamp=datetime(2026, 9, 19, 8, 5),
        ),
        Message(
            role="user",
            content="Now define three agents: backend-engineer, frontend-engineer, p3-triage-agent.",
            timestamp=datetime(2026, 9, 19, 8, 30),
        ),
        Message(
            role="assistant",
            content="Created agent specs in .claude/agents/ with clear ownership scopes and contracts...",
            timestamp=datetime(2026, 9, 19, 8, 45),
        ),
        Message(
            role="user",
            content="We need context trimming to keep token usage efficient. Compress history to 12-15%, keep last 8-10 messages.",
            timestamp=datetime(2026, 9, 19, 9, 0),
        ),
        Message(
            role="assistant",
            content="Building orchestration/context_manager.py with ContextManager class, ConversationSummary, and SubAgentContextBuilder...",
            timestamp=datetime(2026, 9, 19, 9, 15),
        ),
        Message(
            role="user",
            content="Phase 0: Create repo scaffolding. Phase 1: PubMed ingestion. Phase 2: Multi-source + domain filtering.",
            timestamp=datetime(2026, 9, 19, 9, 30),
        ),
        Message(
            role="assistant",
            content="Scaffolding complete: repo structure, Pydantic schemas, Chroma setup, LangGraph skeleton. Exit criterion: python -m orchestration.graph runs end-to-end.",
            timestamp=datetime(2026, 9, 19, 9, 45),
        ),
        Message(
            role="user",
            content="Start Phase 1: Build PubMed ingestion connector with real data.",
            timestamp=datetime(2026, 9, 19, 10, 0),
        ),
        Message(
            role="assistant",
            content="Creating ingestion/pubmed_connector.py. This connector will fetch PubMed articles, chunk them, embed with sentence-transformers, and store in Chroma.",
            timestamp=datetime(2026, 9, 19, 10, 15),
        ),
        Message(
            role="user",
            content="Now Phase 2: Add Clinical Trials and FDA connectors with domain filtering.",
            timestamp=datetime(2026, 9, 19, 10, 30),
        ),
        Message(
            role="assistant",
            content="Building clinicaltrials_connector.py and fda_connector.py. Implementing domain/routing.py to filter by therapeutic area and jurisdiction.",
            timestamp=datetime(2026, 9, 19, 10, 45),
        ),
    ]


def example_basic_trim():
    """Example 1: Basic conversation trimming."""
    print("=" * 60)
    print("Example 1: Basic Conversation Trimming")
    print("=" * 60)

    manager = ContextManager(total_context_tokens=100_000)
    history = create_sample_history()

    print(f"\nOriginal history: {len(history)} messages")
    print(f"Total token estimate: {sum(m.token_estimate for m in history):,} tokens")

    trimmed = manager.trim_conversation(history, preserve_recent=5)

    print(f"\nTrimmed result:")
    print(f"  - Messages summarized: {len(history) - 5}")
    print(f"  - Messages retained: {len(trimmed['recent_messages'])}")
    print(f"  - Trimmed: {trimmed['metadata']['trimmed']}")

    if trimmed["summary"]:
        summary = trimmed["summary"]
        print(f"\nSummary stats:")
        print(f"  - Original tokens: {summary.original_tokens:,}")
        print(f"  - Summary tokens: {summary.summary_tokens:,}")
        print(f"  - Compression ratio: {summary.summary_ratio:.1%}")
        print(f"  - Key decisions: {len(summary.key_decisions)}")
        print(f"  - Key findings: {len(summary.key_findings)}")


def example_agent_context():
    """Example 2: Prepare context for agent injection."""
    print("\n" + "=" * 60)
    print("Example 2: Agent Context Preparation")
    print("=" * 60)

    manager = ContextManager(total_context_tokens=100_000)
    history = create_sample_history()

    # Prepare context for backend-engineer
    context = manager.prepare_agent_context(history, agent_name="backend-engineer")

    print("\nFormatted context (first 1000 chars):")
    print(context[:1000])
    print("... [truncated] ...")
    print(f"\nTotal context string: {len(context)} chars (~{ContextManager.estimate_tokens(context):,} tokens)")


def example_sub_agent_builder():
    """Example 3: Using SubAgentContextBuilder convenience methods."""
    print("\n" + "=" * 60)
    print("Example 3: SubAgentContextBuilder")
    print("=" * 60)

    manager = ContextManager(total_context_tokens=100_000)
    builder = SubAgentContextBuilder(manager)
    history = create_sample_history()

    # Build context for each agent
    backend_context = builder.build_for_backend_engineer(history)
    frontend_context = builder.build_for_frontend_engineer(history)
    triage_context = builder.build_for_p3_triage_agent(history)

    print("\nContext sizes:")
    print(f"  - backend-engineer: {len(backend_context):,} chars (~{ContextManager.estimate_tokens(backend_context):,} tokens)")
    print(f"  - frontend-engineer: {len(frontend_context):,} chars (~{ContextManager.estimate_tokens(frontend_context):,} tokens)")
    print(f"  - p3-triage-agent: {len(triage_context):,} chars (~{ContextManager.estimate_tokens(triage_context):,} tokens)")

    print("\nAll three agents receive trimmed context with their specific instructions.")


def example_allocations():
    """Example 4: Token allocation breakdown."""
    print("\n" + "=" * 60)
    print("Example 4: Token Allocation Breakdown")
    print("=" * 60)

    manager = ContextManager(total_context_tokens=100_000)
    allocations = manager._get_allocations()

    print("\nToken allocations (100,000 total):")
    for key, value in allocations.items():
        pct = (value / allocations["total_tokens"]) * 100
        print(f"  - {key:30s}: {value:6,} tokens ({pct:5.1f}%)")


def example_token_estimation():
    """Example 5: Token estimation for various text sizes."""
    print("\n" + "=" * 60)
    print("Example 5: Token Estimation")
    print("=" * 60)

    test_strings = [
        ("Short message", "Hello world"),
        ("Medium paragraph", "The RAG pipeline processes queries through 8 stages, starting with a Query Planner that decomposes the question into retrieval sub-queries."),
        ("Long document", "The agentic RAG system " * 20),  # ~320 chars
    ]

    print("\nToken estimation (1 token ≈ 4 chars):")
    for label, text in test_strings:
        tokens = ContextManager.estimate_tokens(text)
        print(f"  - {label:20s}: {len(text):4d} chars → ~{tokens:4d} tokens")


if __name__ == "__main__":
    example_basic_trim()
    example_agent_context()
    example_sub_agent_builder()
    example_allocations()
    example_token_estimation()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
