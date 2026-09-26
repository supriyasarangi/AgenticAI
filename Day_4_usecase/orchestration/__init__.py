"""
Orchestration module for agentic RAG drug-discovery system.

Manages LangGraph pipeline topology, context trimming for sub-agents,
and RAGState flow through the pipeline.
"""

from .context_manager import ContextManager, ConversationSummary
from .state import RAGState, Chunk, ClaimGraphLegacy, ClaimGraphNode, ClaimGraphEdge, ConfidenceScore

# Graph components are optional (requires langgraph)
try:
    from .graph import create_app, build_graph, main
    __all__ = [
        "ContextManager",
        "ConversationSummary",
        "RAGState",
        "Chunk",
        "ClaimGraphLegacy",
        "ClaimGraphNode",
        "ClaimGraphEdge",
        "ConfidenceScore",
        "create_app",
        "build_graph",
        "main",
    ]
except ImportError:
    __all__ = [
        "ContextManager",
        "ConversationSummary",
        "RAGState",
        "Chunk",
        "ClaimGraphLegacy",
        "ClaimGraphNode",
        "ClaimGraphEdge",
        "ConfidenceScore",
    ]
