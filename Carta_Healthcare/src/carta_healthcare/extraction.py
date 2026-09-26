from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import anthropic

from .config import Settings, load_settings
from .schema import ClinicalRecord, ClinicalRecordExtraction, ExtractionMetadata
from .client import get_client, call_claude_for_extraction, ExtractionAPIError, ExtractionRetryableError
from .prompts import build_extraction_prompt
from .confidence import compute_confidence_flags
from .io_utils import load_note, write_record


class ExtractionResult(BaseModel):
    record: ClinicalRecord | None = None
    success: bool
    error: str | None = None
    source_file: str


def extract_record(
    note_text: str,
    *,
    source_file: str,
    settings: Settings | None = None,
    client: anthropic.Anthropic | None = None,
) -> ExtractionResult:
    """Extract structured data from a clinical note."""
    if settings is None:
        settings = load_settings()

    if client is None:
        client = get_client(settings)

    if not note_text or not note_text.strip():
        return ExtractionResult(
            success=False, error="Note text is empty", source_file=source_file
        )

    prompt = build_extraction_prompt(note_text)

    try:
        extraction = call_claude_for_extraction(client, prompt, settings)
    except (ExtractionAPIError, ExtractionRetryableError) as e:
        return ExtractionResult(success=False, error=str(e), source_file=source_file)

    metadata = ExtractionMetadata(
        source_file=source_file,
        model_used=settings.model,
        extracted_at=datetime.utcnow(),
        confidence_flags=compute_confidence_flags(extraction),
    )

    return ExtractionResult(
        record=ClinicalRecord(data=extraction, extraction_metadata=metadata),
        success=True,
        source_file=source_file,
    )


def process_directory(
    input_dir: Path,
    output_dir: Path,
    settings: Settings | None = None,
    limit: int | None = None,
) -> list[ExtractionResult]:
    """Process all notes in a directory."""
    if settings is None:
        settings = load_settings()

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    note_files = sorted(input_dir.glob("*.txt"))

    if limit:
        note_files = note_files[:limit]

    results = []
    client = get_client(settings)

    for note_file in note_files:
        try:
            note_text = load_note(note_file)
        except Exception as e:
            results.append(
                ExtractionResult(
                    success=False, error=f"Failed to load note: {e}", source_file=str(note_file)
                )
            )
            continue

        result = extract_record(note_text, source_file=str(note_file), settings=settings, client=client)

        if result.success and result.record:
            try:
                write_record(result.record, output_dir)
            except Exception as e:
                results.append(
                    ExtractionResult(
                        success=False,
                        error=f"Failed to write record: {e}",
                        source_file=str(note_file),
                    )
                )
                continue

        results.append(result)

    return results
