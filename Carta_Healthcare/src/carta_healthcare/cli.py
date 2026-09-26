from pathlib import Path
import typer
import subprocess
import sys

from .config import load_settings
from .extraction import process_directory, extract_record
from .io_utils import load_note, write_record

app = typer.Typer(help="Carta Healthcare Clinical Data Extraction")


@app.command()
def process(
    input_dir: str = typer.Argument(..., help="Directory containing .txt notes"),
    output_dir: str = typer.Argument(..., help="Directory for output JSON records"),
    model: str = typer.Option(None, help="Override model (default: claude-sonnet-5)"),
    limit: int = typer.Option(None, help="Limit processing to N records"),
) -> None:
    """Process a directory of clinical notes."""
    from .config import Settings

    settings = load_settings()
    if model:
        settings.model = model

    try:
        results = process_directory(Path(input_dir), Path(output_dir), settings, limit=limit)

        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        typer.echo(f"\n✓ Processing complete: {succeeded} succeeded, {failed} failed")

        if failed > 0:
            typer.echo("\nFailed records:")
            for result in results:
                if not result.success:
                    typer.echo(f"  - {result.source_file}: {result.error}")
            sys.exit(1)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
def extract_one(
    note_file: str = typer.Argument(..., help="Path to a .txt note file"),
    output: str = typer.Option(None, help="Output JSON file (default: stdout)"),
) -> None:
    """Extract data from a single note."""
    settings = load_settings()

    try:
        note_text = load_note(Path(note_file))
        result = extract_record(note_text, source_file=note_file, settings=settings)

        if not result.success:
            typer.echo(f"Extraction failed: {result.error}", err=True)
            sys.exit(1)

        if output:
            write_record(result.record, Path(output).parent)
            typer.echo(f"✓ Record written to {output}")
        else:
            import json
            typer.echo(json.dumps(result.record.model_dump(mode="json"), indent=2, default=str))

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
def evaluate_accuracy(
    gold_dir: str = typer.Option("eval/gold_standard", help="Gold standard directory"),
    out: str = typer.Option("eval/results", help="Output directory for results"),
) -> None:
    """Run accuracy evaluation against gold standard."""
    try:
        subprocess.run(
            [sys.executable, "-m", "eval.evaluate_accuracy", "--gold-dir", gold_dir, "--out", out],
            cwd=".",
            check=True,
        )
    except subprocess.CalledProcessError:
        sys.exit(1)


@app.command()
def benchmark(
    input_dir: str = typer.Option("fixtures/sample_notes", help="Notes directory for benchmark"),
    baseline_minutes: float = typer.Option(8.0, help="Manual baseline in minutes/record"),
) -> None:
    """Run benchmark against manual baseline."""
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "benchmark.benchmark",
                "--input-dir",
                input_dir,
                "--baseline-minutes",
                str(baseline_minutes),
            ],
            cwd=".",
            check=True,
        )
    except subprocess.CalledProcessError:
        sys.exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
) -> None:
    """Start the FastAPI server."""
    try:
        import uvicorn
        from .api import app as fastapi_app

        uvicorn.run(fastapi_app, host=host, port=port)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
