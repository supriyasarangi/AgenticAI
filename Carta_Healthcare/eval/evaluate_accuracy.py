#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from carta_healthcare.extraction import extract_record
from carta_healthcare.config import load_settings
from carta_healthcare.schema import ClinicalRecordExtraction
from .scoring import flatten_record, compute_scalar_accuracy, compute_list_accuracy


def load_gold_standard(gold_dir: Path) -> list[tuple[Path, ClinicalRecordExtraction]]:
    """Load gold standard notes and their labels."""
    notes_dir = gold_dir / "notes"
    labels_dir = gold_dir / "labels"

    pairs = []
    for note_file in sorted(notes_dir.glob("*.txt")):
        label_file = labels_dir / note_file.with_suffix(".json").name
        if label_file.exists():
            with open(label_file) as f:
                label_data = json.load(f)
                extraction = ClinicalRecordExtraction(**label_data)
                pairs.append((note_file, extraction))

    return pairs


def run_evaluation(gold_dir: Path, output_dir: Path) -> None:
    """Evaluate accuracy against gold standard."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gold_pairs = load_gold_standard(gold_dir)

    if not gold_pairs:
        print("No gold standard pairs found")
        return

    print(f"Evaluating {len(gold_pairs)} records...")

    settings = load_settings()
    results = []
    scalar_scores = []
    list_scores = {"diagnoses": [], "medications": [], "vitals": [], "labs": []}

    for note_file, gold_extraction in gold_pairs:
        print(f"  Processing {note_file.name}...", end=" ", flush=True)

        try:
            with open(note_file) as f:
                note_text = f.read()

            result = extract_record(note_text, source_file=str(note_file), settings=settings)

            if not result.success:
                print(f"FAILED: {result.error}")
                results.append(
                    {"file": note_file.name, "success": False, "error": result.error}
                )
                continue

            predicted_extraction = result.record.data

            # Compute scalar accuracy
            gold_flat = flatten_record(gold_extraction)
            pred_flat = flatten_record(predicted_extraction)
            scalar_acc = compute_scalar_accuracy(gold_flat, pred_flat)
            scalar_scores.append(scalar_acc["accuracy"])

            # Compute list accuracy
            list_acc = compute_list_accuracy(gold_extraction, predicted_extraction)
            for key in list_scores:
                if list_acc[key]["gold_count"] > 0:
                    f1 = (
                        2
                        * list_acc[key]["precision"]
                        * list_acc[key]["recall"]
                        / (list_acc[key]["precision"] + list_acc[key]["recall"] + 1e-6)
                    )
                    list_scores[key].append(f1)

            confidence_flags = result.record.extraction_metadata.confidence_flags

            results.append(
                {
                    "file": note_file.name,
                    "success": True,
                    "scalar_accuracy": scalar_acc["accuracy"],
                    "list_metrics": list_acc,
                    "confidence_flags": confidence_flags,
                }
            )

            print("✓")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"file": note_file.name, "success": False, "error": str(e)})

    # Compute overall metrics
    successful = [r for r in results if r.get("success")]
    if scalar_scores:
        overall_scalar_acc = sum(scalar_scores) / len(scalar_scores)
    else:
        overall_scalar_acc = 0.0

    list_f1_scores = {}
    for key, scores in list_scores.items():
        if scores:
            list_f1_scores[key] = sum(scores) / len(scores)
        else:
            list_f1_scores[key] = 0.0

    summary = {
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "total_records": len(gold_pairs),
        "successful": len(successful),
        "failed": len(gold_pairs) - len(successful),
        "overall_scalar_accuracy": overall_scalar_acc,
        "overall_list_f1_scores": list_f1_scores,
        "results": results,
    }

    # Write results
    results_file = output_dir / f"accuracy_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"\n{'=' * 60}")
    print("ACCURACY EVALUATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total Records: {summary['total_records']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"\nScalar Field Accuracy: {summary['overall_scalar_accuracy']:.2%}")
    print(f"\nList Field F1 Scores:")
    for field, score in summary["overall_list_f1_scores"].items():
        print(f"  {field}: {score:.2%}")
    print(f"\nDetailed results saved to: {results_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate extraction accuracy")
    parser.add_argument("--gold-dir", default="eval/gold_standard", help="Gold standard directory")
    parser.add_argument("--out", default="eval/results", help="Output directory")
    args = parser.parse_args()

    run_evaluation(Path(args.gold_dir), Path(args.out))
