# Low-Level Design (LLD) - MVP
## Commure: Clinical Documentation Automation

**Version**: 1.0 MVP  
**Last Updated**: 2026-09-26  
**Status**: Ready for Implementation

---

## 1. Executive Summary

This document provides technical specifications for the MVP implementation:
- Single database table schema
- 4 API endpoints with examples
- Component architecture
- Claude API integration details
- Local deployment configuration

---

## 2. Database Schema

### Single Table: `encounters`

```sql
CREATE TABLE encounters (
  id SERIAL PRIMARY KEY,
  patient_name VARCHAR(255) NOT NULL,
  age INTEGER NOT NULL,
  chief_complaint TEXT NOT NULL,
  vital_signs JSONB,
  clinical_findings TEXT,
  assessment TEXT,
  generated_note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries
CREATE INDEX idx_encounters_created_at ON encounters(created_at DESC);
```

**Field Definitions:**
- `id`: Auto-incrementing primary key
- `patient_name`: Free text patient identifier
- `age`: Patient age in years
- `chief_complaint`: Primary reason for visit
- `vital_signs`: JSON object `{heart_rate, bp_systolic, bp_diastolic, temperature}`
- `clinical_findings`: Physical exam and findings (textarea)
- `assessment`: Clinical assessment (textarea)
- `generated_note`: Full SOAP note output from Claude
- `created_at`: Timestamp of record creation

**Example Record:**
```json
{
  "id": 1,
  "patient_name": "John Doe",
  "age": 45,
  "chief_complaint": "Chest pain",
  "vital_signs": {
    "heart_rate": 72,
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "temperature": 98.6
  },
  "clinical_findings": "Regular rate and rhythm, lungs clear bilaterally",
  "assessment": "Possible anxiety, rule out cardiac cause",
  "generated_note": "SOAP NOTE: ...",
  "created_at": "2026-09-26T14:30:00Z"
}
```

---

## 3. API Endpoints

### 3.1 POST /api/encounters

**Create a new encounter**

```
POST /api/encounters
Content-Type: application/json

Request:
{
  "patient_name": "John Doe",
  "age": 45,
  "chief_complaint": "Chest pain",
  "vital_signs": {
    "heart_rate": 72,
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "temperature": 98.6
  },
  "clinical_findings": "Regular rate and rhythm, lungs clear bilaterally",
  "assessment": "Possible anxiety, rule out cardiac cause"
}

Response (201 Created):
{
  "id": 1,
  "patient_name": "John Doe",
  "age": 45,
  "chief_complaint": "Chest pain",
  "vital_signs": {...},
  "clinical_findings": "...",
  "assessment": "...",
  "generated_note": null,
  "created_at": "2026-09-26T14:30:00Z"
}
```

---

### 3.2 POST /api/encounters/:id/generate

**Generate SOAP note for an encounter**

```
POST /api/encounters/1/generate
Content-Type: application/json

Request: {} (empty body)

Response (200 OK):
{
  "id": 1,
  "generated_note": "SUBJECTIVE:\nPatient is a 45-year-old presenting with chest pain...\n\nOBJECTIVE:\nVital Signs:\n- Heart Rate: 72 bpm\n- BP: 120/80 mmHg\n- Temperature: 98.6°F\n\nPhysical Exam:\n- Cardiac: Regular rate and rhythm\n- Lungs: Clear bilaterally\n\nASSESSMENT:\nChest pain, likely anxiety. Rule out cardiac etiology.\n\nPLAN:\n1. EKG if not already done\n2. Consider cardiac workup if symptoms persist\n3. Reassurance and anxiety management",
  "token_count": 245,
  "generation_time_ms": 12400
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Claude API error: rate limited",
  "status": 400
}
```

---

### 3.3 GET /api/encounters

**List all encounters (paginated)**

```
GET /api/encounters?page=1&limit=20

Response (200 OK):
{
  "encounters": [
    {
      "id": 1,
      "patient_name": "John Doe",
      "age": 45,
      "chief_complaint": "Chest pain",
      "created_at": "2026-09-26T14:30:00Z",
      "has_note": true
    },
    {
      "id": 2,
      "patient_name": "Jane Smith",
      "age": 32,
      "chief_complaint": "Headache",
      "created_at": "2026-09-26T13:15:00Z",
      "has_note": false
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 42
}
```

---

### 3.4 GET /api/encounters/:id

**Get single encounter with full details**

```
GET /api/encounters/1

Response (200 OK):
{
  "id": 1,
  "patient_name": "John Doe",
  "age": 45,
  "chief_complaint": "Chest pain",
  "vital_signs": {
    "heart_rate": 72,
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "temperature": 98.6
  },
  "clinical_findings": "Regular rate and rhythm, lungs clear bilaterally",
  "assessment": "Possible anxiety, rule out cardiac cause",
  "generated_note": "SUBJECTIVE:\nPatient is a 45-year-old...",
  "created_at": "2026-09-26T14:30:00Z"
}
```

---

## 4. Backend Implementation Details

### 4.1 Technology Stack

- **Runtime**: Node.js 20 with TypeScript
- **Framework**: Express.js
- **Database**: PostgreSQL 15 (Alpine Docker image)
- **HTTP Client**: Node.js built-in `fetch` or axios
- **Environment**: Docker container

### 4.2 Project Structure

```
backend/
├── src/
│   ├── server.ts           # Main Express app + routes
│   ├── db.ts               # PostgreSQL connection & queries
│   ├── claude.ts           # Claude API integration
│   ├── types.ts            # TypeScript interfaces
│   └── middleware.ts       # Error handling, logging
├── Dockerfile
├── package.json
└── tsconfig.json
```

### 4.3 Environment Variables

```bash
# .env file
DATABASE_URL=postgresql://commure:commure_local_dev@db:5432/commure
CLAUDE_API_KEY=sk-ant-xxx...
NODE_ENV=development
PORT=5000
```

### 4.4 Database Connection Pool

```typescript
// src/db.ts
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
});

export async function query(text: string, params?: any[]) {
  return pool.query(text, params);
}

export async function initializeDatabase() {
  await query(`
    CREATE TABLE IF NOT EXISTS encounters (
      id SERIAL PRIMARY KEY,
      patient_name VARCHAR(255) NOT NULL,
      age INTEGER NOT NULL,
      chief_complaint TEXT NOT NULL,
      vital_signs JSONB,
      clinical_findings TEXT,
      assessment TEXT,
      generated_note TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
}
```

### 4.5 Claude API Integration

```typescript
// src/claude.ts
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.CLAUDE_API_KEY,
});

export async function generateSOAPNote(encounterData: any): Promise<string> {
  const prompt = `Generate a professional SOAP note from this patient encounter:

Patient: ${encounterData.patient_name}, Age ${encounterData.age}
Chief Complaint: ${encounterData.chief_complaint}

Vital Signs:
- Heart Rate: ${encounterData.vital_signs.heart_rate} bpm
- BP: ${encounterData.vital_signs.bp_systolic}/${encounterData.vital_signs.bp_diastolic} mmHg
- Temperature: ${encounterData.vital_signs.temperature}°F

Clinical Findings:
${encounterData.clinical_findings}

Assessment:
${encounterData.assessment}

Generate a professional SOAP note with clear sections for Subjective, Objective, Assessment, and Plan.`;

  const message = await client.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1024,
    messages: [
      {
        role: 'user',
        content: prompt,
      },
    ],
  });

  const textContent = message.content.find((block) => block.type === 'text');
  return textContent?.text || 'Error generating note';
}
```

### 4.6 Express Routes

```typescript
// src/server.ts
import express, { Request, Response } from 'express';
import * as db from './db';
import * as claude from './claude';

const app = express();
app.use(express.json());

// POST /api/encounters - Create encounter
app.post('/api/encounters', async (req: Request, res: Response) => {
  try {
    const { patient_name, age, chief_complaint, vital_signs, clinical_findings, assessment } =
      req.body;

    const result = await db.query(
      `INSERT INTO encounters 
       (patient_name, age, chief_complaint, vital_signs, clinical_findings, assessment) 
       VALUES ($1, $2, $3, $4, $5, $6) 
       RETURNING *`,
      [patient_name, age, chief_complaint, JSON.stringify(vital_signs), clinical_findings, assessment]
    );

    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

// POST /api/encounters/:id/generate - Generate SOAP note
app.post('/api/encounters/:id/generate', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    // Get encounter
    const encounterResult = await db.query('SELECT * FROM encounters WHERE id = $1', [id]);
    if (encounterResult.rows.length === 0) {
      return res.status(404).json({ error: 'Encounter not found' });
    }

    const encounter = encounterResult.rows[0];

    // Generate note with Claude
    const generatedNote = await claude.generateSOAPNote(encounter);
    const tokenCount = Math.ceil(generatedNote.length / 4); // Rough estimate

    // Update encounter
    const updateResult = await db.query(
      'UPDATE encounters SET generated_note = $1 WHERE id = $2 RETURNING *',
      [generatedNote, id]
    );

    res.json({
      id: updateResult.rows[0].id,
      generated_note: generatedNote,
      token_count: tokenCount,
      generation_time_ms: 'varies',
    });
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

// GET /api/encounters - List encounters
app.get('/api/encounters', async (req: Request, res: Response) => {
  try {
    const page = parseInt((req.query.page as string) || '1');
    const limit = parseInt((req.query.limit as string) || '20');
    const offset = (page - 1) * limit;

    const result = await db.query(
      `SELECT id, patient_name, age, chief_complaint, created_at, 
              (generated_note IS NOT NULL) as has_note 
       FROM encounters 
       ORDER BY created_at DESC 
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    const countResult = await db.query('SELECT COUNT(*) FROM encounters');

    res.json({
      encounters: result.rows,
      page,
      limit,
      total: parseInt(countResult.rows[0].count),
    });
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

// GET /api/encounters/:id - Get single encounter
app.get('/api/encounters/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const result = await db.query('SELECT * FROM encounters WHERE id = $1', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Encounter not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: (error as Error).message });
  }
});

app.listen(process.env.PORT || 5000, () => {
  console.log(`Server running on port ${process.env.PORT || 5000}`);
  db.initializeDatabase();
});
```

---

## 5. Frontend Implementation Details

### 5.1 Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **HTTP Client**: Fetch API or axios
- **State**: React hooks (useState, useEffect)

### 5.2 Project Structure

```
frontend/
├── src/
│   ├── App.tsx                      # Main component
│   ├── components/
│   │   ├── EncounterForm.tsx        # Form to create encounter
│   │   ├── NoteDisplay.tsx          # Display generated note
│   │   └── EncounterList.tsx        # List past encounters
│   ├── api.ts                       # API client functions
│   ├── types.ts                     # TypeScript interfaces
│   └── index.css                    # Global styles
├── Dockerfile
├── package.json
└── vite.config.ts
```

### 5.3 API Client

```typescript
// src/api.ts
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function createEncounter(data: any) {
  const response = await fetch(`${API_URL}/api/encounters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

export async function generateNote(id: number) {
  const response = await fetch(`${API_URL}/api/encounters/${id}/generate`, {
    method: 'POST',
  });
  return response.json();
}

export async function listEncounters(page = 1, limit = 20) {
  const response = await fetch(`${API_URL}/api/encounters?page=${page}&limit=${limit}`);
  return response.json();
}

export async function getEncounter(id: number) {
  const response = await fetch(`${API_URL}/api/encounters/${id}`);
  return response.json();
}
```

### 5.4 Main App Component

```typescript
// src/App.tsx
import { useState, useEffect } from 'react';
import EncounterForm from './components/EncounterForm';
import NoteDisplay from './components/NoteDisplay';
import EncounterList from './components/EncounterList';

export default function App() {
  const [activeTab, setActiveTab] = useState<'form' | 'list'>('form');
  const [encounter, setEncounter] = useState(null);
  const [generatedNote, setGeneratedNote] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFormSubmit = async (formData: any) => {
    setLoading(true);
    try {
      // Create encounter
      const newEncounter = await createEncounter(formData);
      setEncounter(newEncounter);

      // Generate note
      const result = await generateNote(newEncounter.id);
      setGeneratedNote(result.generated_note);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">Commure - Clinical Documentation</h1>
      </header>

      <div className="max-w-4xl mx-auto p-4">
        <div className="flex gap-4 mb-4">
          <button
            onClick={() => setActiveTab('form')}
            className={`px-4 py-2 rounded ${activeTab === 'form' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            New Encounter
          </button>
          <button
            onClick={() => setActiveTab('list')}
            className={`px-4 py-2 rounded ${activeTab === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            View History
          </button>
        </div>

        {activeTab === 'form' ? (
          <>
            <EncounterForm onSubmit={handleFormSubmit} loading={loading} />
            {generatedNote && <NoteDisplay note={generatedNote} />}
          </>
        ) : (
          <EncounterList />
        )}
      </div>
    </div>
  );
}
```

---

## 6. Docker Configuration

### 6.1 Backend Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY backend/package*.json ./

RUN npm ci

COPY backend/src ./src
COPY backend/tsconfig.json .

EXPOSE 5000

CMD ["npm", "run", "dev"]
```

### 6.2 Frontend Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/vite.config.ts .
COPY frontend/tsconfig.json .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
```

---

## 7. Local Deployment

### Setup

```bash
# 1. Clone/cd to project
cd commure

# 2. Set Claude API key
export CLAUDE_API_KEY="sk-ant-..."

# 3. Start all services
docker-compose up

# First run: database initializes automatically
# Services available:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
# - PostgreSQL: localhost:5432
```

### Database Access

```bash
# Connect to PostgreSQL directly
psql -h localhost -U commure -d commure

# View encounters
SELECT id, patient_name, chief_complaint, created_at FROM encounters;
```

### Stopping

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (delete data)
docker-compose down -v
```

---

## 8. Error Handling

### Backend Error Responses

```typescript
// 400 Bad Request - Invalid input
{ "error": "Missing required field: patient_name" }

// 404 Not Found
{ "error": "Encounter not found" }

// 500 Server Error (Claude API failure)
{ "error": "Claude API error: service unavailable" }
```

### Frontend Error Display

Display errors in a toast/alert:
```
"Failed to generate note. Please check your Claude API key and try again."
```

---

## 9. Performance Targets

| Metric | Target |
|--------|--------|
| Form submission to encounter created | <1 second |
| Claude API call + note generation | 15-25 seconds |
| Display generated note to user | <1 second |
| List encounters page load | <500ms |
| Get single encounter | <200ms |

---

## 10. Testing Strategy (MVP)

### Manual Testing

1. **Create Encounter**: Fill form → Create encounter
2. **Generate Note**: Click generate → Wait for Claude → View note
3. **View History**: Navigate to history tab → See past encounters
4. **Error Cases**: Submit with missing fields → See error message

### No automated tests for MVP (manual testing sufficient)

---

## 11. Implementation Checklist

- [ ] Database schema created
- [ ] Backend API endpoints implemented
- [ ] Claude API integration working
- [ ] Frontend form component
- [ ] Frontend note display component
- [ ] Frontend history component
- [ ] Docker Compose configuration
- [ ] Dockerfile for backend
- [ ] Dockerfile for frontend
- [ ] Environment variables configured
- [ ] Local deployment tested
- [ ] Manual testing complete
