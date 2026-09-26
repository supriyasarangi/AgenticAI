"""
Context Manager for Sub-Agent Memory Allocation.

Implements deterministic context trimming strategy:
- Summarize conversation history to ~12-15% of token budget
- Retain last 8-10 prompts/exchanges in full context
- Allocate remaining context window to agent-specific work

Usage:
    manager = ContextManager(total_context_tokens=100000)
    trimmed_context = manager.trim_conversation(full_history)
    recent_prompts = manager.get_recent_prompts(full_history, count=10)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Message:
    """Represents a single message in conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def token_estimate(self) -> int:
        """Rough token count (1 token ≈ 4 chars for English)."""
        return max(1, len(self.content) // 4)


@dataclass
class ConversationSummary:
    """Summarized conversation history."""
    summary_text: str
    message_count: int
    original_tokens: int
    summary_tokens: int
    summary_ratio: float  # summary_tokens / original_tokens
    key_decisions: List[str]  # Important decisions made
    key_findings: List[str]  # Important findings/conclusions
    timestamp: datetime


class ContextManager:
    """Manages context allocation and trimming for sub-agents."""

    def __init__(
        self,
        total_context_tokens: int = 100000,
        summary_budget_ratio: float = 0.15,  # 12-15% for summary
        recent_messages_count: int = 10,
    ):
        """
        Initialize context manager.

        Args:
            total_context_tokens: Total tokens available in context window
            summary_budget_ratio: Ratio of tokens to allocate for history summary (0.12-0.15)
            recent_messages_count: Number of recent messages to keep in full
        """
        self.total_context_tokens = total_context_tokens
        self.summary_budget_ratio = summary_budget_ratio
        self.recent_messages_count = recent_messages_count

        # Calculated allocations
        self.summary_budget = int(total_context_tokens * summary_budget_ratio)
        self.recent_messages_budget = total_context_tokens - self.summary_budget
        self.instructions_budget = int(self.recent_messages_budget * 0.2)  # 20% for instructions
        self.available_for_work = self.recent_messages_budget - self.instructions_budget

    def trim_conversation(
        self, history: List[Message], preserve_recent: int = None
    ) -> Dict[str, Any]:
        """
        Trim conversation history into summary + recent messages.

        Args:
            history: Full conversation history
            preserve_recent: Override recent message count (default: self.recent_messages_count)

        Returns:
            Dict with 'summary', 'recent_messages', 'allocations', 'metadata'
        """
        if preserve_recent is None:
            preserve_recent = self.recent_messages_count

        if len(history) <= preserve_recent:
            # History fits entirely in recent messages
            return {
                "summary": None,
                "recent_messages": history,
                "allocations": self._get_allocations(),
                "metadata": {
                    "original_message_count": len(history),
                    "trimmed": False,
                    "reason": "History smaller than recent_messages_count",
                },
            }

        # Split into old (to summarize) and recent (to keep)
        old_messages = history[:-preserve_recent]
        recent_messages = history[-preserve_recent:]

        summary = self._create_summary(old_messages)

        return {
            "summary": summary,
            "recent_messages": recent_messages,
            "allocations": self._get_allocations(),
            "metadata": {
                "original_message_count": len(history),
                "old_messages_summarized": len(old_messages),
                "recent_messages_retained": len(recent_messages),
                "trimmed": True,
                "summary_ratio": summary.summary_ratio if summary else 0,
            },
        }

    def get_recent_prompts(
        self, history: List[Message], count: int = 10
    ) -> List[Message]:
        """
        Extract the most recent N prompts/messages from history.

        Args:
            history: Full conversation history
            count: Number of recent messages to extract

        Returns:
            List of most recent messages (up to count)
        """
        return history[-count:] if len(history) > count else history

    def prepare_agent_context(
        self, history: List[Message], agent_name: str
    ) -> str:
        """
        Prepare context string for an agent, formatted and trimmed.

        Args:
            history: Full conversation history
            agent_name: Name of agent receiving context

        Returns:
            Formatted context string ready to include in agent prompt
        """
        trimmed = self.trim_conversation(history)
        summary = trimmed["summary"]
        recent = trimmed["recent_messages"]
        allocations = trimmed["allocations"]

        context_parts = [
            f"=== CONTEXT FOR {agent_name.upper()} ===\n",
            f"Context Budget: {allocations['total_tokens']:,} tokens",
            f"  - Summary (history):    {allocations['summary_tokens']:,} tokens",
            f"  - Recent messages:      {allocations['recent_messages_tokens']:,} tokens",
            f"  - Instructions overhead: {allocations['instructions_tokens']:,} tokens",
            f"  - Available for work:   {allocations['available_work_tokens']:,} tokens\n",
        ]

        if summary:
            context_parts.append("--- CONVERSATION SUMMARY (Historical Context) ---")
            context_parts.append(f"[{summary.message_count} messages compressed to ~{summary.summary_tokens} tokens]\n")
            context_parts.append(summary.summary_text)
            context_parts.append("\nKey Decisions Made:")
            for decision in summary.key_decisions[:5]:
                context_parts.append(f"  • {decision}")
            context_parts.append("\nKey Findings:")
            for finding in summary.key_findings[:5]:
                context_parts.append(f"  • {finding}")
            context_parts.append("\n")

        context_parts.append("--- RECENT CONTEXT (Last 8-10 Exchanges) ---\n")
        for i, msg in enumerate(recent[-10:], 1):
            role_label = "USER" if msg.role == "user" else "CLAUDE"
            context_parts.append(f"[{i}] {role_label}:")
            context_parts.append(msg.content[:500])  # Truncate long messages
            if len(msg.content) > 500:
                context_parts.append(f"... [truncated, {len(msg.content) - 500} more chars]")
            context_parts.append("")

        return "\n".join(context_parts)

    def _create_summary(self, old_messages: List[Message]) -> ConversationSummary:
        """Create a summary of old conversation messages."""
        if not old_messages:
            return None

        total_tokens = sum(msg.token_estimate for msg in old_messages)
        summary_tokens = min(self.summary_budget, total_tokens)

        # Extract user prompts as key decisions/findings
        user_messages = [msg.content for msg in old_messages if msg.role == "user"]
        assistant_messages = [msg.content for msg in old_messages if msg.role == "assistant"]

        # Simple summarization: take first + last messages as representatives
        key_decisions = user_messages[:3] if user_messages else []
        key_findings = [
            msg[:200] for msg in assistant_messages[-3:] if msg
        ]  # Last 3 assistant responses

        summary_text = self._compress_messages(old_messages, summary_tokens)

        return ConversationSummary(
            summary_text=summary_text,
            message_count=len(old_messages),
            original_tokens=total_tokens,
            summary_tokens=summary_tokens,
            summary_ratio=summary_tokens / total_tokens if total_tokens > 0 else 0,
            key_decisions=key_decisions,
            key_findings=key_findings,
            timestamp=datetime.now(),
        )

    def _compress_messages(self, messages: List[Message], max_tokens: int) -> str:
        """Compress messages into a summary within token budget."""
        if not messages:
            return ""

        parts = []
        current_tokens = 0

        # Always include first and last few messages as anchors (deduplicate by index)
        first_msgs = messages[:2]
        last_msgs = messages[-2:]
        anchor_indices = set(range(2)) | set(range(len(messages) - 2, len(messages)))
        anchor_messages = [messages[i] for i in sorted(anchor_indices) if i < len(messages)]

        for msg in anchor_messages:
            if current_tokens < max_tokens:
                role = "User" if msg.role == "user" else "Assistant"
                content_preview = msg.content[:150]
                if len(msg.content) > 150:
                    content_preview += "..."
                parts.append(f"[{role}] {content_preview}")
                current_tokens += msg.token_estimate

        # Add summary statement
        mid_count = len(messages) - len(anchor_messages)
        if mid_count > 0:
            parts.append(f"\n... [{mid_count} intermediate messages with {sum(m.token_estimate for m in messages[2:-2])} tokens] ...\n")

        return "\n".join(parts)

    def _get_allocations(self) -> Dict[str, int]:
        """Return current token allocations."""
        return {
            "total_tokens": self.total_context_tokens,
            "summary_tokens": self.summary_budget,
            "recent_messages_tokens": self.recent_messages_budget,
            "instructions_tokens": self.instructions_budget,
            "available_work_tokens": self.available_for_work,
        }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)."""
        return max(1, len(text) // 4)

    @staticmethod
    def format_for_agent(
        summary: Optional[ConversationSummary],
        recent_messages: List[Message],
        agent_instructions: str,
    ) -> str:
        """
        Format trimmed context for injection into agent prompt.

        Args:
            summary: Summarized history (or None if not needed)
            recent_messages: Recent full messages to include
            agent_instructions: Agent-specific instructions

        Returns:
            Formatted prompt injection string
        """
        parts = []

        if summary:
            parts.append("## Historical Context Summary")
            parts.append(f"(Compressed {summary.message_count} messages to {summary.summary_ratio:.1%})")
            parts.append(summary.summary_text)
            parts.append("")

        parts.append("## Recent Context (Last Exchanges)")
        for msg in recent_messages[-5:]:
            role = "**User:**" if msg.role == "user" else "**Assistant:**"
            parts.append(f"{role} {msg.content[:200]}")

        parts.append("")
        parts.append("## Your Role")
        parts.append(agent_instructions)

        return "\n".join(parts)


class SubAgentContextBuilder:
    """Helper to build context specifically for sub-agents."""

    def __init__(self, context_manager: ContextManager):
        self.manager = context_manager

    def build_for_backend_engineer(
        self, history: List[Message]
    ) -> str:
        """Build context for backend-engineer agent."""
        instructions = (
            "You own ingestion/, agents/, orchestration/, domain/, config/, schemas/, eval/. "
            "Your context includes conversation history trimmed to recent exchanges. "
            "Focus on the task at hand; assume you don't have full project history."
        )
        trimmed = self.manager.trim_conversation(history)
        return self.manager.format_for_agent(
            trimmed["summary"], trimmed["recent_messages"], instructions
        )

    def build_for_frontend_engineer(
        self, history: List[Message]
    ) -> str:
        """Build context for frontend-engineer agent."""
        instructions = (
            "You own ui/ only. Your context includes conversation history trimmed to recent exchanges. "
            "Integrate with orchestration/graph.py contract; never reach into pipeline internals."
        )
        trimmed = self.manager.trim_conversation(history)
        return self.manager.format_for_agent(
            trimmed["summary"], trimmed["recent_messages"], instructions
        )

    def build_for_p3_triage_agent(
        self, history: List[Message]
    ) -> str:
        """Build context for p3-triage-agent."""
        instructions = (
            "You own P3-triage workflow. Your context includes conversation history trimmed to recent exchanges. "
            "Use deterministic rubric; do NOT modify pipeline state; generate audit reports only."
        )
        trimmed = self.manager.trim_conversation(history)
        return self.manager.format_for_agent(
            trimmed["summary"], trimmed["recent_messages"], instructions
        )
