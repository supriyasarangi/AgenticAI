"""
Tenacity-based retry decorators for robust external API calls.

Handles retries for Anthropic API (rate limits, transients), Chroma (generic),
and network calls (Entrez/PubMed HTTP).
"""

import logging
from functools import wraps
from typing import Callable, Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)
import anthropic

from .model_config import get_global_defaults

logger = logging.getLogger(__name__)


def anthropic_retry(func: Callable) -> Callable:
    """
    Retry decorator for Anthropic API calls.

    Retries on:
    - RateLimitError (429)
    - APIConnectionError (connection issues)
    - APIStatusError with 5xx status (server errors)

    Does NOT retry on 4xx client errors (bad request, auth failure, etc.).

    Uses exponential backoff with limits from model_tiers.yaml defaults.
    """
    defaults = get_global_defaults()

    @retry(
        stop=stop_after_attempt(defaults.max_retries),
        wait=wait_exponential(
            multiplier=defaults.base_delay_seconds,
            max=defaults.max_delay_seconds,
        ),
        retry=retry_if_exception_type(
            (
                anthropic.RateLimitError,
                anthropic.APIConnectionError,
            )
        ),
        reraise=True,
    )
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except anthropic.APIStatusError as e:
            # Only retry on 5xx errors
            if e.status_code and 500 <= e.status_code < 600:
                logger.warning(
                    f"API server error {e.status_code}, will retry: {e.message}"
                )
                raise
            else:
                # 4xx errors are not retryable (auth, bad request, etc.)
                logger.error(
                    f"API client error {e.status_code}, not retrying: {e.message}"
                )
                raise

    return wrapper


def chroma_retry(func: Callable) -> Callable:
    """
    Retry decorator for Chroma vector store calls.

    Retries on any Exception with lower attempt count than API retries
    (Chroma issues are typically transient or data-integrity, not rate limits).

    Uses exponential backoff.
    """
    defaults = get_global_defaults()
    # Use half the API retries for Chroma (less aggressive)
    chroma_max_attempts = max(2, defaults.max_retries // 2)

    @retry(
        stop=stop_after_attempt(chroma_max_attempts),
        wait=wait_exponential(
            multiplier=defaults.base_delay_seconds,
            max=defaults.max_delay_seconds,
        ),
        reraise=True,
    )
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Chroma operation failed, will retry: {e}")
            raise

    return wrapper


def network_retry(func: Callable) -> Callable:
    """
    Retry decorator for external HTTP calls (Entrez, PubMed, etc.).

    Retries on connection errors and transient HTTP failures.
    NCBI Entrez requires a contact email and has rate limits (3 req/sec without key).

    Uses exponential backoff.
    """
    defaults = get_global_defaults()

    @retry(
        stop=stop_after_attempt(defaults.max_retries),
        wait=wait_exponential(
            multiplier=defaults.base_delay_seconds,
            max=defaults.max_delay_seconds,
        ),
        reraise=True,
    )
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except (
            ConnectionError,
            TimeoutError,
            OSError,
        ) as e:
            logger.warning(f"Network operation failed, will retry: {e}")
            raise

    return wrapper
