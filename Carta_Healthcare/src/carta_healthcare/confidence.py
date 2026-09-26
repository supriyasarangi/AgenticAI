from .schema import ClinicalRecordExtraction


def compute_confidence_flags(extraction: ClinicalRecordExtraction) -> list[str]:
    flags = []

    if not extraction.diagnoses:
        flags.append("no_diagnoses_found")

    if not extraction.medications:
        flags.append("no_medications_found")

    if not extraction.vitals:
        flags.append("no_vitals_found")

    if not extraction.labs:
        flags.append("no_labs_found")

    if extraction.patient.age is not None and not (0 <= extraction.patient.age <= 130):
        flags.append("implausible_age")

    if extraction.low_confidence_fields:
        flags.append("model_reported_low_confidence")

    if not extraction.encounter.encounter_type:
        flags.append("no_encounter_type")

    if not extraction.encounter.date:
        flags.append("no_encounter_date")

    return flags
