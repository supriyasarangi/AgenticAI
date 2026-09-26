"""
Reusable AI configuration loader — maps tasks to Claude models with effort levels.

Loads model_tiers.yaml and provides a single source of truth for all LLM calls.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

import yaml


@dataclass
class TaskModelConfig:
    """Configuration for a single task's model and parameters."""

    task_name: str
    model: str
    effort: str  # low, medium, high
    thinking: str  # disabled, enabled, adaptive
    max_tokens: int


@dataclass
class GlobalDefaults:
    """Global retry and timeout defaults."""

    max_retries: int
    base_delay_seconds: float
    max_delay_seconds: float
    request_timeout_seconds: float


class ModelConfigLoader:
    """Loads and caches model_tiers.yaml configuration."""

    _instance: Optional["ModelConfigLoader"] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Load config on first instantiation."""
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Load model_tiers.yaml."""
        # Try multiple paths for flexibility
        possible_paths = [
            "config/model_tiers.yaml",
            "/home/labuser/Downloads/Day_4_usecase/config/model_tiers.yaml",
            Path(__file__).parent.parent / "config" / "model_tiers.yaml",
        ]

        config_path = None
        for path in possible_paths:
            if Path(path).exists():
                config_path = Path(path)
                break

        if config_path is None:
            raise FileNotFoundError(
                f"model_tiers.yaml not found in any of: {possible_paths}"
            )

        with open(config_path) as f:
            self._config = yaml.safe_load(f)

    @property
    def config(self) -> Dict[str, Any]:
        """Get loaded configuration."""
        if self._config is None:
            self._load_config()
        return self._config


def get_task_config(task_name: str) -> TaskModelConfig:
    """
    Get model configuration for a task.

    Args:
        task_name: Name of the task (e.g., 'synthesizer', 'verifier')

    Returns:
        TaskModelConfig with model, effort, thinking, max_tokens

    Raises:
        KeyError: If task is not in model_tiers.yaml
    """
    loader = ModelConfigLoader()
    tasks = loader.config.get("tasks", {})

    if task_name not in tasks:
        raise KeyError(f"Task '{task_name}' not found in model_tiers.yaml")

    task_config = tasks[task_name]
    return TaskModelConfig(
        task_name=task_name,
        model=task_config.get("model"),
        effort=task_config.get("effort", "medium"),
        thinking=task_config.get("thinking", "disabled"),
        max_tokens=task_config.get("max_tokens", 2000),
    )


def get_global_defaults() -> GlobalDefaults:
    """
    Get global retry/timeout defaults.

    Returns:
        GlobalDefaults with max_retries, backoff params, timeouts
    """
    loader = ModelConfigLoader()
    defaults = loader.config.get("defaults", {})

    return GlobalDefaults(
        max_retries=defaults.get("max_retries", 3),
        base_delay_seconds=defaults.get("base_delay_seconds", 1.0),
        max_delay_seconds=defaults.get("max_delay_seconds", 30.0),
        request_timeout_seconds=defaults.get("request_timeout_seconds", 60.0),
    )


def load_model_tiers() -> Dict[str, Any]:
    """
    Load entire model_tiers.yaml configuration.

    Returns:
        Dict with 'tasks' and 'defaults' keys
    """
    loader = ModelConfigLoader()
    return loader.config
