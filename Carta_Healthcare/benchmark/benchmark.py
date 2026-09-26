#!/usr/bin/env python3
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import statistics
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from carta_healthcare.extraction import extract_record
from carta_healthcare.config import load_settings
from carta_healthcare.io_utils import load_note, list_note_files

MANUAL_BASELINE_MINUTES_PER_RECORD = 8.0


def run_benchmark(input_dir: Path, output_dir: Path, baseline_minutes: float = MANUAL_BASELINE_MINUTES_PER_RECORD) -> None:
    """Benchmark extraction performance."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        note_files = list_note_files(input_dir)
    except FileNotFoundError:
        print(f"Input directory not found: {input_dir}")
        return

    if not note_files:
        print(f"No .txt files found in {input_dir}")
        return

    print(f"Benchmarking {len(note_files)} records...")
    print(f"Manual baseline assumption: {baseline_minutes:.1f} min/record\n")

    settings = load_settings()
    timings = []
    results = []

    for i, note_file in enumerate(note_files, 1):
        print(f"  [{i}/{len(note_files)}] Processing {note_file.name}...", end=" ", flush=True)

        try:
            note_text = load_note(note_file)

            start_time = time.time()
            result = extract_record(note_text, source_file=str(note_file), settings=settings)
            elapsed_seconds = time.time() - start_time

            if result.success:
                timings.append(elapsed_seconds)
                print(f"✓ ({elapsed_seconds:.2f}s)")
            else:
                print(f"FAILED: {result.error}")

            results.append(
                {
                    "file": note_file.name,
                    "success": result.success,
                    "elapsed_seconds": elapsed_seconds,
                    "error": result.error,
                }
            )

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"file": note_file.name, "success": False, "error": str(e), "elapsed_seconds": 0})

    if not timings:
        print("No successful extractions to benchmark")
        return

    # Compute statistics
    mean_time = statistics.mean(timings)
    median_time = statistics.median(timings)
    p95_time = sorted(timings)[int(len(timings) * 0.95)] if len(timings) > 1 else mean_time
    total_time = sum(timings)

    manual_baseline_seconds = baseline_minutes * 60
    pct_faster = (1 - mean_time / manual_baseline_seconds) * 100

    summary = {
        "benchmark_timestamp": datetime.utcnow().isoformat(),
        "total_records": len(note_files),
        "successful_records": len(timings),
        "failed_records": len(note_files) - len(timings),
        "timing_statistics": {
            "mean_seconds": mean_time,
            "median_seconds": median_time,
            "p95_seconds": p95_time,
            "total_seconds": total_time,
        },
        "manual_baseline_minutes": baseline_minutes,
        "manual_baseline_seconds": manual_baseline_seconds,
        "percent_faster_than_manual": pct_faster,
        "results": results,
    }

    # Write results
    results_file = output_dir / f"benchmark_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"\n{'=' * 60}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total Records: {summary['total_records']}")
    print(f"Successful: {summary['successful_records']}")
    print(f"Failed: {summary['failed_records']}")
    print(f"\nTiming Statistics:")
    print(f"  Mean: {mean_time:.2f}s/record")
    print(f"  Median: {median_time:.2f}s/record")
    print(f"  P95: {p95_time:.2f}s/record")
    print(f"  Total: {total_time:.2f}s")
    print(f"\nManual Baseline: {baseline_minutes:.1f} min/record ({manual_baseline_seconds:.0f}s)")
    print(f"Automated Mean: {mean_time:.2f}s/record")
    print(f"\n🚀 {pct_faster:+.1f}% faster than manual baseline")
    print(f"\nDetailed results saved to: {results_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark extraction performance")
    parser.add_argument("--input-dir", default="fixtures/sample_notes", help="Input directory")
    parser.add_argument("--output-dir", default="benchmark/results", help="Output directory")
    parser.add_argument("--baseline-minutes", type=float, default=MANUAL_BASELINE_MINUTES_PER_RECORD, help="Manual baseline in minutes")
    args = parser.parse_args()

    run_benchmark(Path(args.input_dir), Path(args.output_dir), args.baseline_minutes)
