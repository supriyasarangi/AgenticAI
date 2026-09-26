"""
Domain taxonomy — loads therapeutic areas and jurisdictions from YAML.

Minimal implementation per single-source scope: just enough for display.
No real multi-source routing logic.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

logger = logging.getLogger(__name__)

# Cache loaded domains
_domains_cache: Optional[Dict[str, Any]] = None


def load_domains(config_path: str = "config/domains.yaml") -> Dict[str, Any]:
    """
    Load domain taxonomy from YAML.

    Args:
        config_path: Path to domains.yaml

    Returns:
        Dict with 'therapeutic_areas', 'jurisdictions', 'defaults'
    """
    global _domains_cache

    if _domains_cache is not None:
        return _domains_cache

    # Try multiple paths
    possible_paths = [
        config_path,
        Path(__file__).parent.parent / config_path,
    ]

    loaded_config = None
    for path in possible_paths:
        if Path(path).exists():
            with open(path) as f:
                loaded_config = yaml.safe_load(f)
            _domains_cache = loaded_config
            logger.info(f"Loaded domains from {path}")
            break

    if loaded_config is None:
        logger.warning(f"Domains config not found, using empty dict")
        _domains_cache = {
            "therapeutic_areas": {},
            "jurisdictions": {},
            "defaults": {},
        }

    return _domains_cache


def get_therapeutic_area_display(area_key: str) -> str:
    """
    Get display name for a therapeutic area.

    Args:
        area_key: Key like 'oncology'

    Returns:
        Display name or area_key if not found
    """
    domains = load_domains()
    areas = domains.get("therapeutic_areas", {})

    if area_key in areas:
        return areas[area_key].get("display_name", area_key)

    return area_key


def get_jurisdiction_display(jurisdiction_key: str) -> str:
    """
    Get display name for a jurisdiction.

    Args:
        jurisdiction_key: Key like 'FDA', 'GLOBAL'

    Returns:
        Display name or jurisdiction_key if not found
    """
    domains = load_domains()
    jurisdictions = domains.get("jurisdictions", {})

    if jurisdiction_key in jurisdictions:
        return jurisdictions[jurisdiction_key].get("display_name", jurisdiction_key)

    return jurisdiction_key


def get_jurisdiction_tier(jurisdiction_key: str) -> Optional[float]:
    """
    Get authority tier for a jurisdiction (1.0 = regulatory, None = literature/global).

    Args:
        jurisdiction_key: Key like 'FDA', 'GLOBAL'

    Returns:
        Tier (float) or None
    """
    domains = load_domains()
    jurisdictions = domains.get("jurisdictions", {})

    if jurisdiction_key in jurisdictions:
        return jurisdictions[jurisdiction_key].get("tier")

    return None
