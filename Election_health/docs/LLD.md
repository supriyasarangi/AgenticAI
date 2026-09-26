# Elation Health - Low Level Design (LLD)

## Detailed System Specifications

### 1. Frontend Architecture

#### Component Structure
```
App/
├── pages/
│   ├── LoginPage
│   ├── DashboardPage
│   ├── PatientDetailPage
│   ├── ChartReviewPage
│   └── NoteEditorPage
│
├── components/
│   ├── auth/
│   │   ├── LoginForm
│   │   └── MFAModal
│   │
│   ├── patient/
│   │   ├── PatientCard
│   │   ├── PatientTimeline
│   │   ├── VitalsPanel
│   │   └── MedicationList
│   │
│   ├── chart/
│   │   ├── ChartSummary
│   │   ├── ChartTimeline
│   │   ├── EntrySortFilter
│   │   └── NotePreview
│   │
│   ├── documentation/
│   │   ├── NoteEditor
│   │   ├── TemplateSelector
│   │   ├── SuggestedText
│   │   └── VoiceInput
│   │
│   ├── common/
│   │   ├── Header
│   │   ├── Sidebar
│   │   ├── LoadingSpinner
│   │   └── ErrorBoundary
│
├── hooks/
│   ├── useAuth
│   ├── usePatient
│   ├── useChart
│   ├── useNote
│   └── useSummarization
│
├── services/
│   ├── apiClient.ts
│   ├── authService.ts
│   ├── patientService.ts
│   ├── chartService.ts
│   ├── noteService.ts
│   └── aiService.ts
│
├── store/
│   ├── authStore (Zustand/Redux)
│   ├── patientStore
│   ├── chartStore
│   └── uiStore
│
├── types/
│   ├── patient.ts
│   ├── chart.ts
│   ├── note.ts
│   ├── auth.ts
│   └── api.ts
│
└── utils/
    ├── formatters.ts
    ├── validators.ts
    ├── helpers.ts
    └── constants.ts
```

#### Key Pages

**LoginPage**
- Email/password input
- MFA verification
- "Remember me" option
- Session management

**DashboardPage**
- Patient list with search/filter
- Quick stats (pending notes, pending reviews)
- Recent activity feed
- Shortcuts to frequent tasks

**PatientDetailPage**
- Patient demographics sidebar
- Medical history summary
- Active problems list
- Current medications
- Allergies/contraindications
- Upcoming appointments
- Action buttons (create note, view full chart)

**ChartReviewPage**
- AI-generated summary panel (expandable)
- Full chronological timeline
- Filter by entry type (note, lab, vital, imaging)
- Expandable entry details
- Quick navigation (date picker, go to most recent)

**NoteEditorPage**
- Template selection dropdown
- Rich text editor with suggested text
- Voice-to-text input button
- Auto-save indicator
- Patient context sidebar (demographics, vitals, allergies)
- Submit/Save as draft buttons
- Undo/redo

#### State Management (Zustand)
```typescript
// authStore
{
  user: User
  isAuthenticated: boolean
  login(email, password): Promise
  logout(): void
  refresh(): Promise
}

// patientStore
{
  currentPatient: Patient | null
  patients: Patient[]
  loading: boolean
  setCurrentPatient(id): Promise
  searchPatients(query): Promise
  getPatientList(): Promise
}

// chartStore
{
  currentChart: Chart
  summary: ChartSummary | null
  entries: ChartEntry[]
  filters: ChartFilters
  setFilters(filters): void
  fetchChart(patientId): Promise
  summarizeChart(patientId): Promise
}
```

#### API Client
```typescript
class APIClient {
  baseURL: string
  token: string | null
  
  setToken(token: string): void
  get<T>(endpoint: string, params?): Promise<T>
  post<T>(endpoint: string, data): Promise<T>
  put<T>(endpoint: string, data): Promise<T>
  delete<T>(endpoint: string): Promise<T>
  
  // Interceptors
  onRequest(config): void // Add auth header
  onResponse(response): void // Handle errors
  onError(error): void // Refresh token if 401
}
```

---

### 2. Backend Architecture

#### API Endpoints

**Authentication**
```
POST   /auth/login                 → { token, refreshToken, user }
POST   /auth/refresh               → { token }
POST   /auth/logout                → { success }
POST   /auth/mfa/verify            → { success, token }
GET    /auth/me                    → { user }
```

**Patients**
```
GET    /patients                   → { patients[], total }
GET    /patients/:id               → { patient }
POST   /patients                   → { patient }
PUT    /patients/:id               → { patient }
DELETE /patients/:id               → { success }
GET    /patients/search?q=...      → { patients[] }
GET    /patients/:id/demographics  → { demographics }
```

**Charts**
```
GET    /charts/:patientId          → { chart }
GET    /charts/:patientId/summary  → { summary }
GET    /charts/:patientId/entries  → { entries[], total }
GET    /charts/:patientId/entries/:entryId → { entry }
POST   /charts/:patientId/entries  → { entry }
PUT    /charts/:patientId/entries/:entryId → { entry }
DELETE /charts/:patientId/entries/:entryId → { success }
```

**Notes (Documentation)**
```
GET    /notes                      → { notes[], total }
GET    /notes/:id                  → { note }
POST   /notes                      → { note }
PUT    /notes/:id                  → { note }
DELETE /notes/:id                  → { success }
GET    /notes/templates            → { templates[] }
POST   /notes/:id/submit           → { note }
GET    /notes/drafts               → { drafts[] }
```

**Summarization**
```
POST   /ai/summarize              → { summary }
POST   /ai/suggest-text           → { suggestions[] }
GET    /ai/status/:taskId         → { status, result }
```

**Templates**
```
GET    /templates                  → { templates[] }
GET    /templates/:id              → { template }
POST   /templates                  → { template }
PUT    /templates/:id              → { template }
```

#### Database Schema

**users**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  role ENUM('admin', 'clinician', 'support') NOT NULL,
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_secret VARCHAR(255),
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**patients**
```sql
CREATE TABLE patients (
  id UUID PRIMARY KEY,
  mrn VARCHAR(50) UNIQUE NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  dob DATE NOT NULL,
  gender ENUM('M', 'F', 'Other'),
  email VARCHAR(255),
  phone VARCHAR(20),
  address TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**patient_assignments**
```sql
CREATE TABLE patient_assignments (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id),
  user_id UUID REFERENCES users(id),
  role ENUM('primary_care', 'specialist', 'care_coordinator'),
  assigned_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(patient_id, user_id)
);
```

**chart_entries**
```sql
CREATE TABLE chart_entries (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id) NOT NULL,
  type ENUM('note', 'vital', 'lab', 'imaging', 'medication') NOT NULL,
  title VARCHAR(255),
  content TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_patient_date (patient_id, created_at DESC)
);
```

**notes**
```sql
CREATE TABLE notes (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id) NOT NULL,
  author_id UUID REFERENCES users(id) NOT NULL,
  template_id UUID REFERENCES templates(id),
  title VARCHAR(255),
  content TEXT,
  status ENUM('draft', 'submitted', 'signed') DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  submitted_at TIMESTAMP,
  INDEX idx_patient_status (patient_id, status)
);
```

**templates**
```sql
CREATE TABLE templates (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  content TEXT,
  structure JSONB, -- Pre-filled sections
  created_by UUID REFERENCES users(id),
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**summarization_cache**
```sql
CREATE TABLE summarization_cache (
  id UUID PRIMARY KEY,
  patient_id UUID REFERENCES patients(id),
  summary_text TEXT,
  key_points JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  UNIQUE(patient_id)
);
```

**audit_logs**
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action VARCHAR(100), -- 'view_chart', 'create_note', etc
  resource_type VARCHAR(50),
  resource_id UUID,
  timestamp TIMESTAMP DEFAULT NOW(),
  ip_address VARCHAR(45),
  INDEX idx_user_timestamp (user_id, timestamp DESC)
);
```

#### Service Layer Structure

**AuthService**
```typescript
class AuthService {
  async login(email: string, password: string): Promise<{ token, refreshToken, user }>
  async verifyMFA(userId: string, code: string): Promise<boolean>
  async refresh(refreshToken: string): Promise<string>
  async validateToken(token: string): Promise<boolean>
  async generateMFASecret(userId: string): Promise<string>
  generateTokens(userId: string): { token, refreshToken }
}
```

**PatientService**
```typescript
class PatientService {
  async getPatient(id: string): Promise<Patient>
  async listPatients(userId: string, page, limit): Promise<{ patients[], total }>
  async searchPatients(query: string): Promise<Patient[]>
  async createPatient(data: CreatePatientDTO): Promise<Patient>
  async updatePatient(id: string, data): Promise<Patient>
  async getPatientDemographics(id: string): Promise<Demographics>
  async verifyAccess(userId: string, patientId: string): Promise<boolean>
}
```

**ChartService**
```typescript
class ChartService {
  async getFullChart(patientId: string): Promise<Chart>
  async getChartEntries(patientId: string, filters, page, limit): Promise<{ entries[], total }>
  async getChartEntry(entryId: string): Promise<ChartEntry>
  async addChartEntry(patientId: string, entry: ChartEntryDTO): Promise<ChartEntry>
  async searchChart(patientId: string, query: string): Promise<ChartEntry[]>
}
```

**NoteService**
```typescript
class NoteService {
  async createNote(patientId: string, authorId: string, template?: string): Promise<Note>
  async updateNote(id: string, content: string): Promise<Note>
  async submitNote(id: string): Promise<Note>
  async getNoteTemplate(templateId: string): Promise<Template>
  async saveDraft(id: string, content: string): Promise<Note>
  async getRecentNotes(userId: string, limit: number): Promise<Note[]>
}
```

**AIService**
```typescript
class AIService {
  async summarizeChart(patientId: string, chartData: Chart): Promise<ChartSummary>
  async suggestText(context: string, currentText: string): Promise<string[]>
  async extractEntities(text: string): Promise<ClinicalEntities>
  
  private async callLLMAPI(prompt: string): Promise<string>
  private async structureChartForAI(chart: Chart): Promise<StructuredChart>
  private async validateSummary(summary: ChartSummary): Promise<boolean>
}
```

#### Middleware Pipeline
```
Request
  ↓
logger middleware
  ↓
CORS middleware
  ↓
rate-limit middleware
  ↓
auth middleware (verify JWT)
  ↓
RBAC middleware (check permissions)
  ↓
request validation middleware
  ↓
Route handler
  ↓
error handling middleware
  ↓
Response
```

#### Error Handling
```typescript
class APIError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public code: string,
    public details?: any
  ) {}
}

const errorCodes = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  DUPLICATE_RECORD: 'DUPLICATE_RECORD',
  INTERNAL_ERROR: 'INTERNAL_ERROR'
}
```

---

### 3. AI Integration

#### Summarization Flow
```
1. Fetch full chart (patient_id) from database
2. Structure chart data (remove redundancies, organize chronologically)
3. Create prompt for LLM:
   - System prompt: "You are a clinical documentation expert..."
   - Include patient context (age, conditions, medications)
   - Include chart data
   - Request: "Provide a 2-3 paragraph summary of this patient's medical history..."
4. Call LLM API (OpenAI/Anthropic)
5. Parse response
6. Extract key points via NLP
7. Cache result in Redis (24-hour TTL)
8. Return to frontend
```

#### Suggested Text Generation
```
1. User types in note editor
2. On keystroke (with debounce):
   - Collect context: current patient, recent similar notes, template
   - Send to AI service with current text
   - LLM generates 2-3 suggestions for next sentences
3. Display as inline suggestions
4. User can accept/reject with keyboard shortcut or click
```

#### LLM Prompt Templates

**Chart Summarization Prompt**
```
System: You are an expert clinical documentation specialist. Create concise, 
accurate summaries of patient medical histories.

User: Summarize this patient's key medical history in 2-3 paragraphs:
- Patient: John Doe, 62M, primary conditions: Type 2 diabetes, hypertension
- [Chart data: last 5 years of notes, labs, vitals]

Focus on:
1. Major health conditions and their progression
2. Recent significant events
3. Current treatment plan
4. Any concerns or complications

Provide ONLY the summary, no additional commentary.
```

**Text Suggestion Prompt**
```
System: You are a clinical documentation assistant helping physicians write 
clear, accurate medical notes.

User: I'm writing a progress note for a patient with hypertension. Here's my 
current note: "Patient reports feeling well. Blood pressure today is..."

Suggest 3 possible next sentences to continue this note naturally and clinically 
accurately.

Return ONLY the 3 suggestions as a numbered list.
```

---

### 4. Performance Optimizations

#### Frontend
- Code splitting by route
- Lazy loading of heavy components
- Image optimization (WebP, responsive sizes)
- Minification and tree-shaking
- Service worker for offline access to cached charts
- Virtual scrolling for long patient lists

#### Backend
- Database connection pooling (pg-pool)
- Query optimization (indexes, joins)
- Pagination (default 20 items per page)
- Redis caching for:
  - Chart summaries (24hr TTL)
  - Patient demographics (1hr TTL)
  - Template list (7 days TTL)
- Response compression (gzip)
- CDN for static assets

#### AI Processing
- Async task queue for summarization (not blocking request)
- Batch processing for multiple summaries
- Caching of summaries to avoid re-processing
- Rate limiting on LLM API calls

---

### 5. Security Implementation

#### Authentication Flow
```
1. User submits email + password
2. Server validates credentials against bcrypt hash
3. If valid, check if MFA enabled
4. If MFA enabled:
   - Generate and send OTP (TOTP)
   - User verifies
5. Issue JWT token + refresh token
6. Token includes: { userId, role, iat, exp }
7. Refresh token stored in httpOnly cookie
```

#### Authorization
```
Every endpoint checks:
1. Token validity (expiration, signature)
2. User role permissions
3. Resource ownership (can user access this patient?)
4. Audit log the access
```

#### Data Protection
- All patient data encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- Sensitive fields in database encrypted
- Regular backups with encryption
- PII redacted in logs
- No sensitive data in error messages

---

### 6. Testing Strategy

#### Unit Tests
- Service layer logic (70%+ coverage)
- Component logic and state management
- Utility functions and formatters
- API client and interceptors

#### Integration Tests
- API endpoint flows
- Service interactions
- Database operations
- Auth flows

#### E2E Tests
- Login flow
- Chart review workflow
- Note creation and submission
- Patient search

#### Performance Tests
- Chart load time benchmarks
- Database query performance
- API response time profiling
- Frontend rendering metrics

---

### 7. Deployment Configuration

#### Docker Compose (Development)
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["3001:3001"]
    environment: [DATABASE_URL, REDIS_URL, LLM_API_KEY]
    depends_on: [postgres, redis]
  
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment: [REACT_APP_API_URL]
  
  postgres:
    image: postgres:15
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]
  
  redis:
    image: redis:7
    ports: ["6379:6379"]
```

#### Environment Variables
```
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/elation_health
REDIS_URL=redis://localhost:6379
JWT_SECRET=<long-random-key>
JWT_EXPIRY=1h
LLM_API_KEY=<anthropic-or-openai-key>
LLM_MODEL=gpt-4-turbo or claude-3-opus
NODE_ENV=development

# Frontend
REACT_APP_API_URL=http://localhost:3001
REACT_APP_ENV=development
```

---

### 8. Monitoring & Observability

#### Logging
- Structured JSON logging (Winston/Bunyan)
- Log levels: error, warn, info, debug
- Log aggregation (ELK stack or Cloud Logging)
- Request tracing with correlation IDs

#### Metrics
- API response times (p50, p95, p99)
- Error rates by endpoint
- Database query times
- Cache hit rates
- AI API usage and latency
- User login attempts
- Chart access frequency

#### Alerts
- Error rate > 1%
- Response time > 2 sec (p95)
- Database connection pool exhausted
- Redis connection lost
- LLM API errors
- Disk space > 80%

---

### 9. Rollout Plan

**Week 1-2:** Infrastructure setup, database, basic APIs
**Week 3-4:** Authentication, frontend scaffolding
**Week 5-6:** Patient dashboard, chart view
**Week 7-8:** Note editor, templates
**Week 9-10:** AI integration, testing
**Week 11-12:** Performance tuning, security hardening
**Week 13+:** Beta testing with clinicians, iterations

