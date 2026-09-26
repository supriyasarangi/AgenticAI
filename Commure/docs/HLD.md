# High-Level Design (HLD)
## Commure MVP: Clinical Documentation Automation

**Version**: 1.0 MVP  
**Last Updated**: 2026-09-26  
**Status**: Ready for Implementation

---

## 1. Executive Summary

Commure MVP is a simple, single-user local application that demonstrates automated clinical documentation generation from patient encounter data using Claude AI. The system:

- Accepts patient encounter information via a web form
- Generates professional SOAP notes using Claude API in <30 seconds
- Displays and stores generated notes locally
- Runs entirely on localhost with Docker Compose

---

## 2. System Architecture

### 2.1 Simple Architecture Diagram

```
┌─────────────────────────────────────────┐
│         Web Browser (Port 3000)         │
│  React App - Encounter Form & Display   │
└────────────────┬────────────────────────┘
                 │ HTTP
                 ▼
┌─────────────────────────────────────────┐
│   Express Server (Port 5000)            │
│  ├─ POST /api/encounters                │
│  ├─ POST /api/encounters/:id/generate   │
│  ├─ GET /api/encounters                 │
│  └─ GET /api/encounters/:id             │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴──────────┐
    │                       │
    ▼                       ▼
┌─────────────┐      ┌──────────────────┐
│ PostgreSQL  │      │  Claude API      │
│ (Port 5432) │      │  (Cloud)         │
│ encounters  │      │                  │
│   table     │      │  Generate Notes  │
└─────────────┘      └──────────────────┘
```

### 2.2 Core Components

#### **Frontend (React + TypeScript)**
- Single page application running at localhost:3000
- **EncounterForm**: Input form for patient data (name, age, vitals, findings, assessment)
- **NoteDisplay**: Displays generated SOAP note with copy button
- **EncounterList**: Browse past encounters

#### **Backend (Express.js + TypeScript)**
- API server running at localhost:5000
- 4 endpoints handling CRUD operations and note generation
- Connects to PostgreSQL and Claude API

#### **Database (PostgreSQL)**
- Single `encounters` table
- Stores: patient info, encounter data, generated note, timestamps

#### **AI Layer (Claude API)**
- Calls Claude API to generate SOAP notes
- Prompt-based generation with encounter data
- No caching or complex prompt engineering for MVP

---

## 3. MVP Data Flow

### Typical User Journey

```
1. Clinician opens http://localhost:3000
   ↓
2. Fills form:
   - Patient: John Doe, 45 years old
   - Chief Complaint: Chest pain
   - Vitals: HR 72, BP 120/80, Temp 98.6
   - Findings: Regular rate and rhythm, lungs clear
   - Assessment: Possible anxiety, rule out cardiac cause
   ↓
3. Click "Generate SOAP Note"
   ↓
4. Backend:
   - Creates encounter in database
   - Formats data as prompt
   - Sends to Claude API
   - Returns generated note
   ↓
5. Frontend displays note (< 30 seconds total)
   ↓
6. Clinician reviews, can copy note to clipboard
   ↓
7. Can view past encounters anytime
```

### Data Entities (MVP - Single Table)

```sql
encounters {
  id: UUID,
  patient_name: string,
  age: number,
  chief_complaint: string,
  vital_signs: {heart_rate, bp, temperature},
  clinical_findings: text,
  assessment: text,
  generated_note: text,
  created_at: timestamp
}
```

---

## 4. API Overview

See [LLD.md](LLD.md) for full details.

```
POST /api/encounters
  Create new encounter from form data
  
POST /api/encounters/:id/generate
  Generate SOAP note for encounter using Claude
  
GET /api/encounters
  List all encounters (paginated)
  
GET /api/encounters/:id
  Get single encounter with generated note
```

---

## 5. Non-Functional Requirements

### Performance
- **Document Generation**: <30 seconds
- **API Response**: <100ms (except generate)
- **Form to Display**: <35 seconds end-to-end

### Reliability
- Application should not crash on invalid input
- Claude API failures should return graceful error message

### Local Deployment
- Single `docker-compose up` command starts all services
- Automatic database initialization
- No external dependencies except Claude API key

### Development
- Hot reload for React and backend
- Easy to modify prompts and schemas
- Clear separation of frontend/backend/database

---

## 6. Technology Stack (Final)

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| Backend | Express.js + TypeScript + Node.js 20 |
| Database | PostgreSQL 15 (Alpine) |
| Container | Docker + Docker Compose |
| AI | Claude API (Anthropic) |

---

## 7. Deployment (MVP)

**Local Development:**
```bash
export CLAUDE_API_KEY="sk-ant-..."
docker-compose up
# Opens http://localhost:3000
```

**Services:**
- PostgreSQL: localhost:5432
- Backend API: localhost:5000
- Frontend: localhost:3000

All data stored locally in PostgreSQL container.

---

## 8. MVP Limitations (Not Supported)

- ❌ User authentication
- ❌ Multi-user access
- ❌ Voice recording/transcription
- ❌ EHR integration
- ❌ Document signing
- ❌ Audit logging
- ❌ Production deployment
- ❌ HIPAA compliance (development use only)

---

## 9. Future Enhancements (Phase 2+)

- Add user authentication
- Support multiple document types (progress note, discharge summary)
- Voice-to-text input
- EHR connectors
- Advanced prompt engineering by specialty
- Document templates
- Analytics dashboard

---

## 10. Success Criteria (MVP)

✅ Can run `docker-compose up` and have app running  
✅ Can fill form and generate SOAP note in <30 seconds  
✅ Generated notes are clinically reasonable  
✅ Can view past encounters  
✅ Code is simple and readable  
✅ Ready to test with real clinicians
