# Elation Health - Design Summary

## Quick Reference

### Project Vision
**Elation Health** - A primary-care EHR platform that reduces chart-review and documentation burden by 61% through intelligent automation, streamlined workflows, and clinician-centric design.

### Core Principle
Everything is optimized for **clinician speed** and **accuracy** without sacrificing data security or compliance.

---

## MVP Features (Phase 1)

| Feature | Purpose | Impact |
|---------|---------|--------|
| **Smart Chart Summarization** | AI generates 2-3 paragraph summary of patient history | Reduces chart review time by 50%+ |
| **Patient Dashboard** | Quick access to assigned patients with search | Reduces time finding patient records |
| **Chart Timeline View** | Chronological, filterable view of all patient data | Organized chart review |
| **Smart Note Editor** | Template-based, AI-assisted documentation | Reduces note-writing time by 40%+ |
| **Clinical Templates** | Pre-filled templates for common visit types | Standardizes documentation |
| **Quick Entry Forms** | Structured forms for vitals, medications, problems | Faster than free-text entry |

---

## Technology Stack

```
Frontend:        React 18+ / TypeScript / TailwindCSS
Backend:         Node.js / Express.js
Database:        PostgreSQL
Cache:           Redis
AI Integration:  LLM API (OpenAI/Anthropic)
Auth:            JWT + bcrypt + MFA
Testing:         Jest + React Testing Library
Deployment:      Docker / AWS ECS
```

---

## Key Workflows

### 1. Chart Review (Clinician starts patient visit)
```
1. Click on patient in dashboard (1 sec)
2. System loads:
   - Patient demographics (0.3 sec)
   - AI summary (2-3 sec)
   - Full chart timeline (0.5 sec)
3. Clinician skims summary (30 sec)
4. Drills into timeline as needed (per-click based)
5. Total time: 3-4 min (vs. 8-10 min with current EHR)
```

### 2. Note Creation (Clinician documents visit)
```
1. Click "Create Note" (0.2 sec)
2. Select template (5 sec)
3. System pre-fills with:
   - Patient history from chart
   - Recent similar notes
   - Today's vitals
4. Clinician fills gaps, uses voice-to-text (8-12 min)
5. AI suggests completion text (1-2 sec per suggestion)
6. Submit note (1 sec)
```

### 3. Search Patient
```
1. Type in search (2-3 sec)
2. Results return with relevance (0.5 sec)
3. Click on patient
```

---

## Database Schema (Simplified)

```
users (id, email, password_hash, role, mfa_enabled, ...)
patients (id, mrn, first_name, last_name, dob, gender, ...)
patient_assignments (patient_id, user_id, role)
chart_entries (id, patient_id, type, content, created_at, ...)
notes (id, patient_id, author_id, content, status, ...)
templates (id, name, category, content, structure)
summarization_cache (patient_id, summary_text, key_points, expires_at)
audit_logs (user_id, action, resource_id, timestamp)
```

---

## API Endpoints (Summary)

**Auth:** `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`

**Patients:** `GET /patients`, `GET /patients/:id`, `GET /patients/search`

**Charts:** `GET /charts/:patientId`, `GET /charts/:patientId/entries`, `GET /charts/:patientId/summary`

**Notes:** `GET /notes`, `POST /notes`, `PUT /notes/:id`, `POST /notes/:id/submit`

**Templates:** `GET /templates`, `GET /templates/:id`

**AI:** `POST /ai/summarize`, `POST /ai/suggest-text`

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Chart load time | < 500ms |
| Patient search | < 800ms |
| Note submission | < 2s |
| AI summary generation | < 5s |
| Dashboard load | < 1s |
| Page transitions | < 300ms |

---

## Security Model

```
┌─────────────────────────────────────────┐
│         HTTPS (TLS 1.3)                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│    JWT Token (in Authorization header)   │
│    - Contains: userId, role, expiry      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│     Role-Based Access Control (RBAC)    │
│     - Check user role vs endpoint       │
│     - Check resource ownership          │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Data Encryption & Audit Logging       │
│   - At-rest: AES-256                    │
│   - PII redacted in logs                │
│   - All chart access logged             │
└─────────────────────────────────────────┘
```

**MFA:** TOTP-based, required for all clinician accounts

---

## Scalability Strategy

| Layer | Scaling Approach |
|-------|------------------|
| **Frontend** | CDN + static asset caching |
| **API** | Horizontal scaling behind load balancer |
| **Database** | Connection pooling + read replicas |
| **Cache** | Redis cluster |
| **AI** | Async queue + batch processing |

**Expected Capacity:** 1,000+ concurrent clinicians at launch

---

## Development Timeline

| Phase | Timeline | Deliverables |
|-------|----------|--------------|
| 1. Planning & Design | ✓ Complete | HLD, LLD, DB schema, API spec |
| 2. Infrastructure | Week 1-2 | Docker setup, DB, Redis, basic API |
| 3. Core Backend | Week 3-4 | Auth, patient service, chart service |
| 4. Frontend Foundation | Week 5-6 | Login, dashboard, basic views |
| 5. Core Features | Week 7-8 | Chart view, note editor, templates |
| 6. AI Integration | Week 9-10 | Summarization, text suggestions |
| 7. Polish & Test | Week 11-12 | Performance tuning, security hardening |
| 8. Beta Launch | Week 13+ | Limited clinician testing, iteration |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| AI summaries inaccurate | Medium | High | Manual review, continuous testing, fallback |
| Data breach / HIPAA violation | Low | Critical | Encryption, audit logs, regular security audits |
| Clinicians don't adopt | Medium | High | Iterative user testing, feedback loops |
| Scalability issues at launch | Low | Medium | Load testing, horizontal scaling ready |
| Integration with existing EHR | Medium | High | HL7/FHIR planned for Phase 2 |

---

## Success Metrics

- **61% reduction in chart review time** (primary KPI)
- **85%+ clinician adoption** within 3 months
- **< 0.1% error rate** in AI summaries
- **99.9% system uptime**
- **< 500ms median chart load time**
- **2+ hours saved per clinician per day**

---

## Next Steps

1. ✓ Design complete (HLD + LLD)
2. → Review design with stakeholders
3. → Approve tech stack and architecture
4. → Set up development environment
5. → Begin Phase 1 implementation

---

## Document References

- **CLAUDE.md** - Project overview, goals, tech stack
- **HLD.md** - High-level architecture, components, data flows
- **LLD.md** - Detailed specifications, schemas, endpoints, services
- **This file** - Quick reference summary

---

## Questions to Resolve Before Implementation

1. **LLM Provider?** OpenAI (GPT-4) vs. Anthropic (Claude) vs. self-hosted?
2. **Cloud Platform?** AWS, GCP, or Azure?
3. **EHR Integration?** Which existing EHRs must we integrate with?
4. **Authentication?** SSO/SAML or JWT?
5. **Compliance?** HIPAA only, or GDPR/other?
6. **Backup Strategy?** Frequency, retention, recovery RPO/RTO?
7. **Clinician Roles?** Just "clinician" or more granular (physician, NP, PA, RN)?
8. **Patient Capacity?** How many patients per clinician? Total patients at launch?
9. **Data Migration?** Importing existing patient records?
10. **Feature Priority?** If time-constrained, which features are must-have vs. nice-to-have?

