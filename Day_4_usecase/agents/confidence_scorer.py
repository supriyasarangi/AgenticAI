"""
Confidence scoring — calculates per-claim confidence tiers using the formula.

Formula from config/scoring_weights.yaml:
confidence = w_retrieval * retrieval_similarity
           + w_source * source_authority_tier
           + w_corroboration * corroboration_count (log-scaled)
           + w_recency * recency_score
           + w_llm * llm_consistency_check
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml

from orchestration.state import ConfidenceScore

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Loaded scoring configuration."""

    weights: Dict[str, float]
    thresholds: Dict[str, float]
    recency_half_life_days: Dict[str, int]
    max_sources: int
    log_scale: bool


class ConfidenceScorer:
    """Scores claims using the multi-factor confidence formula."""

    def __init__(self, config_path: str = "config/scoring_weights.yaml"):
        """Load scoring configuration."""
        self.config_path = config_path
        self.scoring_config = self._load_config()

    def _load_config(self) -> ScoringWeights:
        """Load and parse scoring weights YAML."""
        # Try multiple paths
        possible_paths = [
            self.config_path,
            Path(__file__).parent.parent / self.config_path,
        ]

        config = None
        for path in possible_paths:
            if Path(path).exists():
                with open(path) as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded scoring config from {path}")
                break

        if config is None:
            logger.warning("Scoring config not found, using defaults")
            config = {
                "weights": {
                    "retrieval_similarity": 0.25,
                    "source_authority_tier": 0.30,
                    "corroboration_count": 0.20,
                    "recency_score": 0.10,
                    "llm_consistency_check": 0.15,
                },
                "thresholds": {
                    "high": 0.75,
                    "medium": 0.50,
                    "low": 0.25,
                },
                "recency_half_life_days": {
                    "literature": 365,
                },
                "corroboration": {
                    "max_sources": 10,
                    "log_scale": True,
                },
            }

        weights = config.get("weights", {})
        thresholds = config.get("thresholds", {})
        recency = config.get("recency_half_life_days", {})
        corroboration = config.get("corroboration", {})

        return ScoringWeights(
            weights=weights,
            thresholds=thresholds,
            recency_half_life_days=recency,
            max_sources=corroboration.get("max_sources", 10),
            log_scale=corroboration.get("log_scale", True),
        )

    def _calculate_recency_score(
        self,
        pub_date: Optional[str],
        source_type: str = "literature",
    ) -> float:
        """
        Calculate recency score with exponential decay.

        Uses half-life from config: 50% decay every N days.

        Args:
            pub_date: Publication date (YYYY or YYYY-MM-DD format, or None)
            source_type: Type of source (literature, regulatory, etc.)

        Returns:
            Recency score (0.0 to 1.0)
        """
        if not pub_date:
            return 0.5  # Neutral if no date

        try:
            # Parse date (handle both YYYY and YYYY-MM-DD formats)
            if len(pub_date) == 4:
                # Year only
                pub_datetime = datetime.strptime(pub_date, "%Y")
            else:
                # ISO format
                pub_datetime = datetime.fromisoformat(pub_date)

            days_old = (datetime.now() - pub_datetime).days
            half_life = self.scoring_config.recency_half_life_days.get(
                source_type, 365
            )

            # Exponential decay: score = 0.5 ^ (days_old / half_life)
            recency_score = 0.5 ** (days_old / half_life)
            return min(1.0, max(0.0, recency_score))

        except (ValueError, TypeError):
            return 0.5

    def _calculate_corroboration_score(self, count: int) -> float:
        """
        Calculate corroboration score with log scaling.

        Args:
            count: Number of corroborating sources

        Returns:
            Corroboration score (0.0 to 1.0)
        """
        if count <= 0:
            return 0.0

        max_sources = self.scoring_config.max_sources

        if self.scoring_config.log_scale:
            # Log scale: log(count+1) normalized to [0, 1]
            score = math.log(count + 1) / math.log(max_sources + 1)
        else:
            # Linear scale
            score = min(1.0, count / max_sources)

        return min(1.0, max(0.0, score))

    def score_claim(
        self,
        claim_id: str,
        retrieval_similarity: float,
        source_authority_tier: float,
        corroboration_count: int,
        publication_date: Optional[str],
        llm_consistency_check: float,
        source_type: str = "literature",
        cited_chunk_ids: Optional[List[str]] = None,
    ) -> ConfidenceScore:
        """
        Score a claim using the multi-factor formula.

        Args:
            claim_id: Identifier for this claim
            retrieval_similarity: Vector similarity score (0.0 to 1.0)
            source_authority_tier: Authority tier (0.0 to 1.0)
            corroboration_count: Number of supporting sources
            publication_date: Publication date (YYYY or YYYY-MM-DD)
            llm_consistency_check: LLM verification score (0.0 to 1.0)
            source_type: Type of source (literature, regulatory, etc.)
            cited_chunk_ids: List of chunk IDs supporting this claim

        Returns:
            ConfidenceScore with composite score and tier
        """
        if cited_chunk_ids is None:
            cited_chunk_ids = []

        # Calculate component scores
        recency_score = self._calculate_recency_score(publication_date, source_type)
        corroboration_score = self._calculate_corroboration_score(corroboration_count)

        # Apply weights and compute composite
        weights = self.scoring_config.weights
        composite_score = (
            weights.get("retrieval_similarity", 0.25) * retrieval_similarity
            + weights.get("source_authority_tier", 0.30) * source_authority_tier
            + weights.get("corroboration_count", 0.20) * corroboration_score
            + weights.get("recency_score", 0.10) * recency_score
            + weights.get("llm_consistency_check", 0.15) * llm_consistency_check
        )

        # Clamp to [0, 1]
        composite_score = min(1.0, max(0.0, composite_score))

        # Determine tier
        thresholds = self.scoring_config.thresholds
        if composite_score >= thresholds.get("high", 0.75):
            tier = "High"
        elif composite_score >= thresholds.get("medium", 0.50):
            tier = "Medium"
        elif composite_score >= thresholds.get("low", 0.25):
            tier = "Low"
        else:
            tier = "Unverified"

        # Build rationale
        rationale = (
            f"Composite score {composite_score:.3f} based on: "
            f"retrieval {retrieval_similarity:.3f}, authority {source_authority_tier:.3f}, "
            f"corroboration {corroboration_score:.3f}, recency {recency_score:.3f}, "
            f"llm_check {llm_consistency_check:.3f}"
        )

        return ConfidenceScore(
            claim_id=claim_id,
            score=composite_score,
            tier=tier,
            retrieval_similarity=retrieval_similarity,
            source_authority_score=source_authority_tier,
            corroboration_count=corroboration_count,
            recency_score=recency_score,
            llm_consistency_check=llm_consistency_check,
            rationale=rationale,
            cited_chunk_ids=cited_chunk_ids,
        )
