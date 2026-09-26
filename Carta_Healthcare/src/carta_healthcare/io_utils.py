import json
from pathlib import Path
from .schema import ClinicalRecord


def load_note(file_path: Path) -> str:
    """Load a text note from file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Note file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_record(record: ClinicalRecord, output_dir: Path) -> Path:
    """Write a structured clinical record to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename based on source
    source_name = Path(record.extraction_metadata.source_file).stem
    output_file = output_dir / f"{source_name}_extracted.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(record.model_dump(mode="json"), f, indent=2, default=str)

    return output_file


def list_note_files(input_dir: Path) -> list[Path]:
    """List all .txt files in a directory."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    return sorted(input_dir.glob("*.txt"))
