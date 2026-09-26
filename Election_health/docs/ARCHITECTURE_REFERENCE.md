# Elation Health - Architecture Reference

## System Context Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Clinician Users                                  │
│                     (Primary Care Physicians)                             │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
           ┌────────▼────────┐       ┌────────▼────────┐
           │   Web Browser   │       │   Mobile App    │
           │   (React SPA)   │       │   (Future)      │
           └────────┬────────┘       └────────┬────────┘
                    │                        │
                    └────────────┬───────────┘
                                 │ HTTPS
                    ┌────────────▼────────────┐
                    │   API Gateway / LB      │
                    │   (AWS ALB)             │
                    └────────────┬────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼──────┐   ┌────────▼────────┐   ┌──────▼───────┐
    │  Backend     │   │  Backend        │   │  Background  │
    │  Container 1 │   │  Container 2    │   │  Worker      │
    │  (Express)   │   │  (Express)      │   │  (Node)      │
    └───────┬──────┘   └────────┬────────┘   └──────┬───────┘
            │                   │                   │
            └───────────┬───────┴───────┬──────────┘
                        │               │
            ┌───────────▼──────┐    ┌───▼──────────┐
            │   PostgreSQL     │    │   Redis      │
            │   Primary DB     │    │   Cache      │
            │   (RDS)          │    │  (ElastiCache)
            └───────────┬──────┘    └───┬──────────┘
                        │               │
            ┌───────────▼──────┐    ┌───▼──────────┐
            │  PostgreSQL      │    │  Redis       │
            │  Replica 1       │    │  Replica 1   │
            └──────────────────┘    └──────────────┘
            
            ┌──────────────────────────────────────┐
            │  External Services                    │
            │  - LLM API (OpenAI/Anthropic)        │
            │  - Monitoring (DataDog/CloudWatch)   │
            │  - Email Service (SendGrid)          │
            │  - Analytics (Mixpanel)              │
            └──────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ Dashboard  │  │ Chart View │  │ Note Editor│               │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘               │
│        │                │               │                       │
│        └────────────┬───┴───┬───────────┘                       │
│                     │       │                                   │
│        ┌────────────▼───┬───▼────────────┐                     │
│        │ Global State   │  Auth Context  │                     │
│        │ (Zustand)      │  (JWT Token)   │                     │
│        └────────────┬───┴───┬────────────┘                     │
│                     │       │                                   │
│        ┌────────────▼───┬───▼────────────┐                     │
│        │  API Client    │  HTTP Client   │                     │
│        │  (axios)       │  (interceptors)│                     │
│        └────────────┬───┴───┬────────────┘                     │
└─────────────────────┼───┬───┼──────────────────────────────────┘
                      │   │   │
                      └───┼───┘ HTTPS
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Backend API Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Auth Routes  │  │ Patient      │  │ Chart Routes         │  │
│  │ /auth/*      │  │ Routes       │  │ /charts/:id/*        │  │
│  │              │  │ /patients/*  │  │                      │  │
│  └────────┬─────┘  └──────┬───────┘  └──────────┬───────────┘  │
│           │               │                     │               │
│           └───────────┬───┴─────────────────┬───┘               │
│                       │                     │                   │
│  ┌────────────────────▼──────────────┬──────▼────────────────┐ │
│  │        Middleware Layer           │                       │ │
│  │ - JWT Validation                  │  Error Handling      │ │
│  │ - RBAC Check                      │  - Global handlers   │ │
│  │ - Audit Logging                   │  - Error responses   │ │
│  │ - Rate Limiting                   │                       │ │
│  └────────────────────┬───────────┬──┴──────────────────────┘ │
│                       │           │                             │
│  ┌────────────────────▼───┐  ┌────▼──────────────────────────┐ │
│  │   Service Layer        │  │   AI/LLM Integration         │ │
│  │ - AuthService          │  │ - Chart Summarization        │ │
│  │ - PatientService       │  │ - Text Suggestions           │ │
│  │ - ChartService         │  │ - Entity Extraction          │ │
│  │ - NoteService          │  │ - LLM API Calls              │ │
│  │ - TemplateService      │  │ - Response Caching           │ │
│  └────────────────────┬───┘  └────┬──────────────────────────┘ │
│                       │           │                             │
└───────────────────────┼───────────┼─────────────────────────────┘
                        │           │
              ┌─────────▼───┬──────▼───────────┐
              │             │                  │
        ┌─────▼────┐  ┌────▼────┐   ┌────────▼────┐
        │PostgreSQL│  │ Redis   │   │  LLM API    │
        │Database  │  │ Cache   │   │  (External) │
        └──────────┘  └─────────┘   └─────────────┘
```

## Data Flow: Chart Review Scenario

```
Step 1: User clicks "View Patient"
┌──────────────────────────────────────────────┐
│ Frontend (Dashboard)                         │
│ - Dispatch action: setCurrentPatient(id)     │
│ - Show loading spinner                       │
└────────────┬─────────────────────────────────┘
             │ GET /patients/:id
             ├─ Authorization header: JWT
             ├─ Query params: include=demographics
             │
             ▼
        ┌─────────────────────────────────────┐
        │ Backend API                         │
        │ - Verify JWT                        │
        │ - Check RBAC: can user view patient?│
        │ - Log access to audit_logs          │
        └────────────┬────────────────────────┘
                     │ Query database
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ PostgreSQL                          │
        │ SELECT * FROM patients WHERE id=... │
        │ SELECT * FROM patient_assignments..│
        └────────────┬────────────────────────┘
                     │ JSON response
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Backend                             │
        │ - Construct response                │
        │ - Set cache: 1 hour TTL            │
        └────────────┬────────────────────────┘
                     │ 200 OK + JSON
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Parse response                    │
        │ - Update state (patientStore)       │
        │ - Hide loading spinner              │
        │ - Render patient details            │
        └─────────────────────────────────────┘

Step 2: User clicks "View Chart"
┌──────────────────────────────────────────────┐
│ Frontend                                     │
│ - Dispatch: fetchChart(patientId)           │
│ - Also dispatch: summarizeChart(patientId)  │
│ - Show loading                              │
└────────────┬─────────────────────────────────┘
             │                │
             │ GET /charts    │ POST /ai/summarize
             │   /:id/entries │
             │                │
             ├────────────────┼──────────────┐
             │                │              │
             ▼                ▼              ▼
        Backend        Backend          Queue Worker
        - Check cache  - Check cache    (if not cached)
        - Query DB     - Call LLM API
        - Return       - Cache result
        chart entries  - Return summary
        
             │                │              │
             └────────────────┼──────────────┘
                              │
                     ┌────────▼────────┐
                     │ Frontend        │
                     │ - Render chart  │
                     │   timeline      │
                     │ - Display       │
                     │   summary panel │
                     └─────────────────┘

Step 3: LLM Summarization Process (Detailed)
┌───────────────────────────────────────────────┐
│ POST /ai/summarize                            │
│ Body: { patientId, includeFullChart: true }   │
└────────────┬────────────────────────────────┘
             │
             ▼
        ┌─────────────────────────────────────┐
        │ AIService.summarizeChart()          │
        │ - Check Redis cache first           │
        │   If found + not expired:           │
        │   Return cached result              │
        └────────────┬────────────────────────┘
                     │ (not cached)
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Fetch full chart from DB            │
        │ - All notes (last 5 years)          │
        │ - All labs (last 2 years)           │
        │ - All vitals (last year)            │
        │ - Current medications               │
        │ - Problems list                     │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Structure chart for LLM             │
        │ - Remove duplicates                 │
        │ - Order chronologically             │
        │ - Extract key facts                 │
        │ - Anonymize where possible          │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Build LLM prompt:                   │
        │ System: "You are a clinical..."     │
        │ User: "Summarize this patient..."   │
        │       [structured chart data]       │
        │       "Provide 2-3 key takeaways"   │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Call LLM API                        │
        │ - Authorization: API key            │
        │ - Timeout: 30 seconds               │
        │ - Streaming response                │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Parse LLM response                  │
        │ - Extract summary text              │
        │ - Parse key points                  │
        │ - Validate quality (> 50 chars)     │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Store in cache (Redis)              │
        │ - Key: "summary:{patientId}"        │
        │ - TTL: 24 hours                     │
        │ - Value: JSON (summary, keyPoints)  │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Return to frontend                  │
        │ 200 OK                              │
        │ {                                   │
        │   summary: "...",                   │
        │   keyPoints: [...],                 │
        │   generatedAt: "2026-09-26...",     │
        │   cached: false                     │
        │ }                                   │
        └─────────────────────────────────────┘
```

## Data Flow: Note Creation Scenario

```
Step 1: Select Template
┌─────────────────────────────────────────────┐
│ Frontend (NoteEditor)                       │
│ - User clicks "New Note"                    │
│ - Fetch available templates                 │
└────────────┬────────────────────────────────┘
             │ GET /templates
             │ (optional: ?category=progress)
             │
             ▼
        ┌─────────────────────────────────────┐
        │ Backend                             │
        │ - Check Redis cache                 │
        │   (templates cached 7 days)         │
        │ - If not cached:                    │
        │   Query DB, cache result            │
        │ - Return template list              │
        └────────────┬────────────────────────┘
                     │ [{ id, name, category }...]
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Display template picker           │
        │ - User selects template             │
        └─────────────────────────────────────┘

Step 2: Load Template + Prefill
┌─────────────────────────────────────────────┐
│ Frontend                                    │
│ - Fetch template: GET /templates/:id        │
│ - Fetch patient context:                    │
│   - Demographics                            │
│   - Recent vitals                           │
│   - Last similar note                       │
└────────────┬────────────────────────────────┘
             │
             ├─ GET /patients/:id
             ├─ GET /charts/:id/entries?type=vital
             └─ GET /notes?patientId=...&limit=1
             
             ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Load template content             │
        │ - Prefill fields:                   │
        │   - Patient name/DOB                │
        │   - Today's date                    │
        │   - Recent vitals (BP, temp, etc)   │
        │   - History from last note          │
        │ - User begins editing               │
        └─────────────────────────────────────┘

Step 3: Auto-Save Draft
┌─────────────────────────────────────────────┐
│ Frontend                                    │
│ - On each keystroke (debounced 3 sec)       │
│ - POST /notes (or PUT /notes/:id)           │
│ - Body:                                     │
│   {                                         │
│     patientId,                              │
│     authorId,                               │
│     content: "...",                         │
│     status: "draft",                        │
│     templateId                              │
│   }                                         │
└────────────┬────────────────────────────────┘
             │
             ▼
        ┌─────────────────────────────────────┐
        │ Backend                             │
        │ - Verify JWT                        │
        │ - Verify user can edit note         │
        │ - Update/create in DB               │
        │ - Return saved note                 │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Show "Auto-saved" indicator       │
        │ - Store draft ID for resume         │
        └─────────────────────────────────────┘

Step 4: AI Text Suggestions
┌─────────────────────────────────────────────┐
│ Frontend                                    │
│ - User positions cursor in note             │
│ - Triggers suggestion (Ctrl+Space or button)│
│ - POST /ai/suggest-text                     │
│ - Body:                                     │
│   {                                         │
│     currentText: "Patient states she...",   │
│     context: { patientAge: 62, ... },       │
│     includeRecent: true                     │
│   }                                         │
└────────────┬────────────────────────────────┘
             │
             ▼
        ┌─────────────────────────────────────┐
        │ Backend AIService                   │
        │ - Build prompt with context         │
        │ - Call LLM API                      │
        │ - Extract 2-3 suggestions           │
        │ - Validate (min length, relevance)  │
        └────────────┬────────────────────────┘
                     │ Return suggestions
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Display suggestions inline        │
        │ - User clicks or presses Tab        │
        │ - Insert selected suggestion        │
        └─────────────────────────────────────┘

Step 5: Submit Note
┌─────────────────────────────────────────────┐
│ Frontend                                    │
│ - User clicks "Sign & Submit"               │
│ - Confirmation dialog                       │
└────────────┬────────────────────────────────┘
             │
             ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Perform final validation          │
        │ - POST /notes/:id/submit            │
        │ - Body:                             │
        │   {                                 │
        │     signature: "..." (or simulated) │
        │     status: "submitted"             │
        │   }                                 │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Backend                             │
        │ - Verify completeness               │
        │ - Mark as submitted                 │
        │ - Set timestamp                     │
        │ - Create audit log entry            │
        │ - Update chart_entries table        │
        │ - Trigger any downstream actions    │
        │   (notifications, billing, etc)     │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │ Frontend                            │
        │ - Show success message              │
        │ - Return to patient view            │
        │ - Note now visible in chart         │
        └─────────────────────────────────────┘
```

## State Management Architecture

```
┌─────────────────────────────────────────────────────┐
│            Redux/Zustand Stores                     │
│  (Centralized client-side state management)         │
└─────────────────────────────────────────────────────┘
         │              │              │
    ┌────▼────┐  ┌──────▼──────┐  ┌──▼──────────┐
    │ authStore│  │patientStore │  │ chartStore  │
    │          │  │             │  │             │
    │ - user   │  │ - current   │  │ - current   │
    │ - token  │  │   patient   │  │   chart     │
    │ - loading│  │ - patients[]│  │ - entries[] │
    │ - error  │  │ - loading   │  │ - summary   │
    │ - logout │  │ - search()  │  │ - filters   │
    │   action │  │ - select()  │  │ - fetch()   │
    │          │  │             │  │             │
    └────┬─────┘  └──────┬──────┘  └──┬──────────┘
         │               │            │
         └───────────────┼────────────┘
                         │
                ┌────────▼────────┐
                │   useSelector   │
                │   hooks         │
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐  ┌──────▼──────┐  ┌──▼──────┐
    │Dashboard│  │ChartReview   │  │NoteEditor
    │Component│  │Component     │  │Component
    │         │  │              │  │
    │Selects: │  │Selects:      │  │Selects:
    │- user   │  │- chart       │  │- patient
    │- isAuth │  │- entries     │  │- template
    │         │  │- summary     │  │- note
    └─────────┘  └──────────────┘  └──────────┘
```

## Error Handling Flow

```
User Action
    │
    ▼
API Call (fetch)
    │
    ├─ Network Error
    │  └─ Show: "Connection lost. Retrying..."
    │
    ├─ 401 Unauthorized
    │  └─ Refresh token
    │     ├─ Success: Retry original request
    │     └─ Fail: Redirect to login
    │
    ├─ 403 Forbidden
    │  └─ Show: "You don't have permission"
    │
    ├─ 404 Not Found
    │  └─ Show: "Patient not found"
    │
    ├─ 5xx Server Error
    │  └─ Show: "Server error. Please try again"
    │     Retry with exponential backoff
    │
    └─ 200 OK
       └─ Process response
          ├─ Success: Update state
          └─ Invalid data: Show "Invalid response"
```

---

## Deployment Topology (Production)

```
┌─────────────────────────────────────────────────────────┐
│                   AWS Region (us-east-1)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │            CloudFront (CDN)                      │  │
│  │     Static assets, caching, DDoS protection      │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                 │
│  ┌────────────────────▼──────────────────────────────┐ │
│  │        Application Load Balancer (ALB)            │ │
│  │     HTTPS termination, routing, sticky sessions   │ │
│  └────────────────────┬──────────────────────────────┘ │
│                       │                                 │
│  ┌────────────────────▼──────────────────────────────┐ │
│  │           ECS Cluster (Multi-AZ)                  │ │
│  │  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │  Container   │  │  Container   │              │ │
│  │  │  Task (api)  │  │  Task (api)  │              │ │
│  │  └──────────────┘  └──────────────┘              │ │
│  │                                                   │ │
│  │  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │  Container   │  │  Container   │              │ │
│  │  │  Task (api)  │  │  Task (async)│              │ │
│  │  └──────────────┘  └──────────────┘              │ │
│  └────────┬──────────────────┬──────────────────────┘ │
│           │                  │                         │
│  ┌────────▼──────────────────▼──────────────────────┐ │
│  │    RDS Proxy (Connection Pooling)                │ │
│  │  Manages database connections efficiently         │ │
│  └────────┬──────────────────┬──────────────────────┘ │
│           │                  │                         │
│           │         ┌────────▼──────────────────┐     │
│           │         │ RDS Aurora Primary        │     │
│           │         │ (PostgreSQL Multi-AZ)     │     │
│           │         │ - Main database           │     │
│           │         │ - Automated backups       │     │
│           └─────────┼────────────────────────────┘     │
│           │         │                                  │
│           │         └─► RDS Replica (Read-only)        │
│           │                                           │
│  ┌────────▼──────────────────────────────────────┐   │
│  │  ElastiCache Redis Cluster (Multi-AZ)         │   │
│  │  - Session store                              │   │
│  │  - Chart summary cache                        │   │
│  │  - Rate limiting counters                     │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │  S3 Bucket (Document Storage)                 │   │
│  │  - Encrypted, versioned                       │   │
│  │  - Lifecycle policies                         │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │  SQS Queue (Async Tasks)                      │   │
│  │  - Chart summarization tasks                  │   │
│  │  - Email notifications                        │   │
│  │  - Batch processing                           │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │  Secrets Manager                              │   │
│  │  - JWT secret                                 │   │
│  │  - Database passwords                         │   │
│  │  - API keys (LLM, etc)                        │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │  CloudWatch                                   │   │
│  │  - Logs, metrics, alarms                      │   │
│  │  - Performance monitoring                     │   │
│  │  - Security monitoring                        │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
└─────────────────────────────────────────────────────┘

External:
┌──────────────────────────────────────┐
│  OpenAI/Anthropic API                │
│  (LLM for summarization)             │
└──────────────────────────────────────┘
```

---

This reference document provides comprehensive details on how Elation Health's architecture works at all levels, from user interactions to infrastructure deployment.

