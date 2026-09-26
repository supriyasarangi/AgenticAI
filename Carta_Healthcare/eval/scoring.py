import difflib
from typing import Any
from .schema import ClinicalRecordExtraction


def flatten_record(extraction: ClinicalRecordExtraction) -> dict[str, Any]:
    """Flatten a record to dotted-path keys."""
    flattened = {}

    # Demographics
    if extraction.patient.age is not None:
        flattened["patient.age"] = extraction.patient.age
    if extraction.patient.sex is not None:
        flattened["patient.sex"] = extraction.patient.sex.value if hasattr(extraction.patient.sex, 'value') else str(extraction.patient.sex)
    if extraction.patient.mrn is not None:
        flattened["patient.mrn"] = extraction.patient.mrn

    # Encounter
    if extraction.encounter.encounter_type is not None:
        flattened["encounter.encounter_type"] = extraction.encounter.encounter_type
    if extraction.encounter.date is not None:
        flattened["encounter.date"] = extraction.encounter.date
    if extraction.encounter.provider is not None:
        flattened["encounter.provider"] = extraction.encounter.provider
    if extraction.encounter.facility is not None:
        flattened["encounter.facility"] = extraction.encounter.facility
    if extraction.encounter.chief_complaint is not None:
        flattened["encounter.chief_complaint"] = extraction.encounter.chief_complaint

    # Lists
    flattened["diagnoses_count"] = len(extraction.diagnoses)
    flattened["medications_count"] = len(extraction.medications)
    flattened["vitals_count"] = len(extraction.vitals)
    flattened["labs_count"] = len(extraction.labs)

    return flattened


def fuzzy_match(gold: str, predicted: str, threshold: float = 0.85) -> bool:
    """Check if two strings are similar enough."""
    ratio = difflib.SequenceMatcher(None, gold.lower(), predicted.lower()).ratio()
    return ratio >= threshold


def match_lists(
    gold_items: list[dict], predicted_items: list[dict], key_field: str
) -> tuple[int, int, int]:
    """Greedy matching for list-valued fields. Returns (matched, gold_count, predicted_count)."""
    matched = 0
    used_predicted = set()

    for gold_item in gold_items:
        gold_key = gold_item.get(key_field, "").lower()
        for i, pred_item in enumerate(predicted_items):
            if i in used_predicted:
                continue
            pred_key = pred_item.get(key_field, "").lower()
            if fuzzy_match(gold_key, pred_key):
                matched += 1
                used_predicted.add(i)
                break

    return matched, len(gold_items), len(predicted_items)


def compute_scalar_accuracy(gold: dict, predicted: dict) -> dict[str, Any]:
    """Compute accuracy for scalar fields."""
    total = 0
    exact_matches = 0
    fuzzy_matches = 0

    # String fields use fuzzy matching; numeric use exact
    string_fields = [
        "patient.sex",
        "encounter.encounter_type",
        "encounter.provider",
        "encounter.facility",
        "encounter.chief_complaint",
    ]

    for field in set(list(gold.keys()) + list(predicted.keys())):
        if field.endswith("_count"):
            continue

        total += 1
        gold_val = gold.get(field)
        pred_val = predicted.get(field)

        if gold_val is None and pred_val is None:
            exact_matches += 1
        elif gold_val is None or pred_val is None:
            pass
        elif field in string_fields and isinstance(gold_val, str) and isinstance(pred_val, str):
            if fuzzy_match(gold_val, pred_val):
                fuzzy_matches += 1
        elif gold_val == pred_val:
            exact_matches += 1

    return {
        "total_fields": total,
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
        "accuracy": (exact_matches + fuzzy_matches) / total if total > 0 else 0.0,
    }


def compute_list_accuracy(
    gold: ClinicalRecordExtraction, predicted: ClinicalRecordExtraction
) -> dict[str, Any]:
    """Compute precision/recall for list-valued fields."""
    results = {}

    # Diagnoses
    diag_matched, diag_gold, diag_pred = match_lists(
        [d.model_dump() for d in gold.diagnoses],
        [d.model_dump() for d in predicted.diagnoses],
        "description",
    )
    results["diagnoses"] = {
        "matched": diag_matched,
        "gold_count": diag_gold,
        "predicted_count": diag_pred,
        "precision": diag_matched / diag_pred if diag_pred > 0 else 0.0,
        "recall": diag_matched / diag_gold if diag_gold > 0 else 0.0,
    }

    # Medications
    med_matched, med_gold, med_pred = match_lists(
        [m.model_dump() for m in gold.medications],
        [m.model_dump() for m in predicted.medications],
        "name",
    )
    results["medications"] = {
        "matched": med_matched,
        "gold_count": med_gold,
        "predicted_count": med_pred,
        "precision": med_matched / med_pred if med_pred > 0 else 0.0,
        "recall": med_matched / med_gold if med_gold > 0 else 0.0,
    }

    # Vitals
    vitals_matched, vitals_gold, vitals_pred = match_lists(
        [v.model_dump() for v in gold.vitals],
        [v.model_dump() for v in predicted.vitals],
        "name",
    )
    results["vitals"] = {
        "matched": vitals_matched,
        "gold_count": vitals_gold,
        "predicted_count": vitals_pred,
        "precision": vitals_matched / vitals_pred if vitals_pred > 0 else 0.0,
        "recall": vitals_matched / vitals_gold if vitals_gold > 0 else 0.0,
    }

    # Labs
    labs_matched, labs_gold, labs_pred = match_lists(
        [l.model_dump() for l in gold.labs],
        [l.model_dump() for l in predicted.labs],
        "test_name",
    )
    results["labs"] = {
        "matched": labs_matched,
        "gold_count": labs_gold,
        "predicted_count": labs_pred,
        "precision": labs_matched / labs_pred if labs_pred > 0 else 0.0,
        "recall": labs_matched / labs_gold if labs_gold > 0 else 0.0,
    }

    return results
