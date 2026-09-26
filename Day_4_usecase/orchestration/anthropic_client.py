"""
Single choke point for all Claude API calls in the pipeline.

Handles client initialization, cached system blocks, and task-specific model selection.
"""

import os
import logging
from typing import Any, Dict, List, Optional

import anthropic

from .model_config import get_task_config, get_global_defaults
from .retry import anthropic_retry

logger = logging.getLogger(__name__)


def get_client() -> anthropic.Anthropic:
    """
    Initialize and return the Anthropic client.

    Reads ANTHROPIC_API_KEY from environment.

    Returns:
        anthropic.Anthropic client instance

    Raises:
        RuntimeError: If ANTHROPIC_API_KEY is not set
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Please configure your .env file."
        )

    return anthropic.Anthropic(api_key=api_key)


def build_cached_system_blocks(
    stable_prefix: str,
    tool_defs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Build system block list with ephemeral cache on the final stable block.

    The stable prefix (system prompt + evidence bundle) is the same for all
    requests in a batch, so it's cached for cost/latency savings.

    Args:
        stable_prefix: The stable system prompt + serialized evidence (long text)
        tool_defs: Optional list of tool definitions (not cached)

    Returns:
        List of system blocks ready for messages.create(), with cache_control
        on the last block of the stable prefix.
    """
    blocks = [
        {
            "type": "text",
            "text": stable_prefix,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    # Tool definitions (if any) are not cached, come after stable prefix
    if tool_defs:
        for tool_def in tool_defs:
            blocks.append({
                "type": "text",
                "text": f"Tool: {tool_def.get('name', 'unknown')}",
            })

    return blocks


@anthropic_retry
def call_with_task_config(
    task_name: str,
    system: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
    **kwargs
) -> anthropic.Message:
    """
    Call Claude with task-specific model and effort configuration.

    Looks up task_name in model_tiers.yaml, builds thinking/output_config
    conditionally, and makes the API call with automatic retries.

    Args:
        task_name: Task name from model_tiers.yaml (e.g., 'synthesizer')
        system: System blocks (from build_cached_system_blocks)
        messages: Message list for the request
        **kwargs: Additional args passed to messages.create()

    Returns:
        anthropic.Message response

    Raises:
        KeyError: If task_name not in model_tiers.yaml
        RuntimeError: If ANTHROPIC_API_KEY not set
        anthropic.APIError: If API call fails after retries
    """
    # Get task config
    config = get_task_config(task_name)
    client = get_client()

    # Base kwargs
    call_kwargs = {
        "model": config.model,
        "max_tokens": config.max_tokens,
        "system": system,
        "messages": messages,
    }

    # Add thinking only if not disabled and model supports it
    # (Opus and Sonnet support thinking; Haiku does not)
    if config.thinking != "disabled":
        if config.model in ["claude-opus-5", "claude-sonnet-5"]:
            call_kwargs["thinking"] = {
                "type": config.thinking,  # "adaptive" or "enabled"
            }

    # Add temperature/top_k for different effort levels
    if config.effort == "low":
        call_kwargs["temperature"] = 0.5
    elif config.effort == "medium":
        call_kwargs["temperature"] = 1.0
    elif config.effort == "high":
        call_kwargs["temperature"] = 1.0

    # Merge any additional kwargs
    call_kwargs.update(kwargs)

    logger.info(
        f"Calling {config.model} for task '{task_name}' (effort={config.effort}, "
        f"thinking={config.thinking})"
    )

    return client.messages.create(**call_kwargs)
