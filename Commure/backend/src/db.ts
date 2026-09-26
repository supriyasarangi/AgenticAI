import { Pool, QueryResult } from 'pg';
import { Encounter, EncounterInput, EncounterListItem } from './types';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
});

export async function query(text: string, params?: any[]): Promise<QueryResult> {
  return pool.query(text, params);
}

export async function initializeDatabase(): Promise<void> {
  try {
    await query(`
      CREATE TABLE IF NOT EXISTS encounters (
        id SERIAL PRIMARY KEY,
        patient_name VARCHAR(255) NOT NULL,
        age INTEGER NOT NULL,
        chief_complaint TEXT NOT NULL,
        vital_signs JSONB NOT NULL,
        clinical_findings TEXT NOT NULL,
        assessment TEXT NOT NULL,
        generated_note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_encounters_created_at
      ON encounters(created_at DESC);
    `);
    console.log('Database initialized successfully');
  } catch (error) {
    console.error('Database initialization error:', error);
    throw error;
  }
}

export async function createEncounter(data: EncounterInput): Promise<Encounter> {
  const result = await query(
    `INSERT INTO encounters
     (patient_name, age, chief_complaint, vital_signs, clinical_findings, assessment)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING *`,
    [
      data.patient_name,
      data.age,
      data.chief_complaint,
      JSON.stringify(data.vital_signs),
      data.clinical_findings,
      data.assessment,
    ]
  );

  return formatEncounter(result.rows[0]);
}

export async function getEncounter(id: number): Promise<Encounter | null> {
  const result = await query('SELECT * FROM encounters WHERE id = $1', [id]);

  if (result.rows.length === 0) {
    return null;
  }

  return formatEncounter(result.rows[0]);
}

export async function updateEncounterNote(
  id: number,
  generatedNote: string
): Promise<Encounter | null> {
  const result = await query(
    'UPDATE encounters SET generated_note = $1 WHERE id = $2 RETURNING *',
    [generatedNote, id]
  );

  if (result.rows.length === 0) {
    return null;
  }

  return formatEncounter(result.rows[0]);
}

export async function listEncounters(
  page: number = 1,
  limit: number = 20
): Promise<{ encounters: EncounterListItem[]; total: number }> {
  const offset = (page - 1) * limit;

  const result = await query(
    `SELECT id, patient_name, age, chief_complaint, created_at,
            (generated_note IS NOT NULL) as has_note
     FROM encounters
     ORDER BY created_at DESC
     LIMIT $1 OFFSET $2`,
    [limit, offset]
  );

  const countResult = await query('SELECT COUNT(*) FROM encounters');

  return {
    encounters: result.rows,
    total: parseInt(countResult.rows[0].count, 10),
  };
}

function formatEncounter(row: any): Encounter {
  return {
    id: row.id,
    patient_name: row.patient_name,
    age: row.age,
    chief_complaint: row.chief_complaint,
    vital_signs:
      typeof row.vital_signs === 'string'
        ? JSON.parse(row.vital_signs)
        : row.vital_signs,
    clinical_findings: row.clinical_findings,
    assessment: row.assessment,
    generated_note: row.generated_note,
    created_at: row.created_at,
  };
}

export async function closePool(): Promise<void> {
  await pool.end();
}
