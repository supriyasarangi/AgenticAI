from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Sex(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class PatientDemographics(BaseModel):
    age: Optional[int] = Field(default=None, ge=0, le=130)
    sex: Optional[Sex] = None
    mrn: Optional[str] = None


class EncounterInfo(BaseModel):
    encounter_type: Optional[str] = None
    date: Optional[str] = None
    provider: Optional[str] = None
    facility: Optional[str] = None
    chief_complaint: Optional[str] = None


class Diagnosis(BaseModel):
    description: str
    icd10_code: Optional[str] = None
    status: Optional[str] = None


class Medication(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None


class VitalSign(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None


class LabResult(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[bool] = None


class ClinicalRecordExtraction(BaseModel):
    patient: PatientDemographics
    encounter: EncounterInfo
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    vitals: list[VitalSign] = Field(default_factory=list)
    labs: list[LabResult] = Field(default_factory=list)
    low_confidence_fields: list[str] = Field(
        default_factory=list,
        description="Dotted paths the model was unsure about",
    )


class ExtractionMetadata(BaseModel):
    source_file: str
    model_used: str
    extracted_at: datetime
    confidence_flags: list[str] = Field(default_factory=list)


class ClinicalRecord(BaseModel):
    data: ClinicalRecordExtraction
    extraction_metadata: ExtractionMetadata
