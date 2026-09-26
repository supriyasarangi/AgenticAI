# Commure Agent Team
## Clinical Documentation Automation - Unified Agent Definition

**Project**: Commure MVP - Automated SOAP note generation using Claude AI  
**Architecture**: Full-stack application (React frontend + Node.js backend)  
**Goal**: One application with two specialist agents working together

---

## Single Application, Two Specialists

This is **one project** that needs both backend and frontend expertise. We use two specialist agents for efficiency:

- **Backend Specialist** (see `backend-agent.md`) — Handles server, API, database, Claude integration
- **Frontend Specialist** (see `frontend-agent.md`) — Handles UI, forms, components, styling

Both work on the **same application** with a clear contract via TypeScript types.

---

## How They Work Together

### 1. Type Safety is the Contract
- Backend defines data structures in `backend/src/types.ts`
- Frontend consumes those types in `frontend/src/types.ts`
- Changes to one require coordination with the other

### 2. API Endpoints are the Interface
- Backend implements 4 REST endpoints
- Frontend calls those endpoints
- Both reference `docs/LLD.md` for the spec

### 3. Docker Composition
- Both have their own `Dockerfile`
- Single `docker-compose.yml` runs both
- They communicate via HTTP (frontend → backend API)

---

## Agent Roles

| Role | Files | Tech Stack |
|------|-------|-----------|
| **Backend** | `server.ts`, `db.ts`, `claude.ts`, `types.ts` | Node.js, Express, PostgreSQL, TypeScript |
| **Frontend** | `App.tsx`, components, `api.ts`, `types.ts` | React 18, Vite, TailwindCSS, TypeScript |

---

## Running the Full Stack

### With Docker (One Command)
```bash
export CLAUDE_API_KEY="sk-ant-..."
docker-compose up
```

- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Database: localhost:5432

### Locally (Two Terminals)
```bash
# Terminal 1
cd backend && npm run dev

# Terminal 2
cd frontend && npm run dev
```

---

## Implementation Status

✅ **Backend**: Complete  
✅ **Frontend**: Complete  
✅ **Integration**: Complete  
✅ **Deployment**: Ready (Docker Compose)  

---

## For More Details

- **Backend Role**: See `backend-agent.md`
- **Frontend Role**: See `frontend-agent.md`
- **Full Specs**: See `docs/LLD.md`
- **Project Overview**: See `CLAUDE.md`

---

**One Application. One Team. One Purpose.**
