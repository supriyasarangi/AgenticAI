"""
Logging configuration setup.

Loads logging_config.yaml and configures Python's logging system,
guarded against repeated Streamlit reruns.
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Guard to prevent reconfiguring on each Streamlit rerun
_logging_configured = False


def setup_logging(config_path: Optional[str] = None) -> None:
    """
    Configure logging from YAML config file.

    Guards against repeated calls (e.g., in Streamlit reruns) to avoid
    reconfiguring handlers multiple times.

    Args:
        config_path: Path to logging_config.yaml. Defaults to config/logging_config.yaml
    """
    global _logging_configured

    if _logging_configured:
        logger.debug("Logging already configured, skipping setup")
        return

    if config_path is None:
        # Try multiple paths for flexibility
        possible_paths = [
            "config/logging_config.yaml",
            Path(__file__).parent.parent / "config" / "logging_config.yaml",
        ]

        config_path = None
        for path in possible_paths:
            if Path(path).exists():
                config_path = Path(path)
                break

        if config_path is None:
            # Fallback: use basicConfig if YAML not found
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            _logging_configured = True
            logger.warning(
                "logging_config.yaml not found, using basic configuration"
            )
            return

    try:
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)

        logging.config.dictConfig(config_dict)
        _logging_configured = True
        logger.info(f"Logging configured from {config_path}")

    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        _logging_configured = True
        logger.error(f"Failed to load logging config from {config_path}: {e}")
