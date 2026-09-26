export interface VitalSigns {
  heart_rate: number;
  bp_systolic: number;
  bp_diastolic: number;
  temperature: number;
}

export interface EncounterInput {
  patient_name: string;
  age: number;
  chief_complaint: string;
  vital_signs: VitalSigns;
  clinical_findings: string;
  assessment: string;
}

export interface Encounter extends EncounterInput {
  id: number;
  generated_note: string | null;
  created_at: string;
}

export interface EncounterListItem {
  id: number;
  patient_name: string;
  age: number;
  chief_complaint: string;
  created_at: string;
  has_note: boolean;
}

export interface ListResponse {
  encounters: EncounterListItem[];
  page: number;
  limit: number;
  total: number;
}

export interface GenerateNoteResponse {
  id: number;
  generated_note: string;
  token_count: number;
  generation_time_ms: number;
}

export interface ErrorResponse {
  error: string;
}
