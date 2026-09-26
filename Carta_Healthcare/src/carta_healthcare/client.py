import anthropic
from .config import Settings
from .schema import ClinicalRecordExtraction
from .prompts import SYSTEM_PROMPT


class ExtractionAPIError(Exception):
    """Non-retryable failure calling Claude (4xx, refusal, etc.)."""


class ExtractionRetryableError(Exception):
    """Failure that the SDK already retried and exhausted (429/5xx/connection)."""


def get_client(settings: Settings) -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key if settings.anthropic_api_key else None,
        max_retries=settings.max_retries,
        timeout=settings.timeout_seconds,
    )


def call_claude_for_extraction(
    client: anthropic.Anthropic, prompt: str, settings: Settings
) -> ClinicalRecordExtraction:
    try:
        response = client.messages.parse(
            model=settings.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            output_format=ClinicalRecordExtraction,
        )
    except anthropic.RateLimitError as e:
        raise ExtractionRetryableError(f"rate limited: {e}") from e
    except anthropic.APIConnectionError as e:
        raise ExtractionRetryableError(f"connection error: {e}") from e
    except anthropic.APIStatusError as e:
        if e.status_code >= 500:
            raise ExtractionRetryableError(f"server error {e.status_code}: {e.message}") from e
        raise ExtractionAPIError(f"API error {e.status_code}: {e.message}") from e
    except anthropic.APIError as e:
        raise ExtractionAPIError(f"API error: {e}") from e

    if hasattr(response, "stop_reason") and response.stop_reason == "refusal":
        raise ExtractionAPIError("model declined to process this note")

    return response.parsed_output
