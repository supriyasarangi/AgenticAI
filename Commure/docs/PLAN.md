# PLAN.md - Commure MVP Implementation Roadmap

**Last Updated**: 2026-09-26  
**Status**: Scaffolding Phase

---

## Overview

This document tracks the concrete implementation steps to build Commure MVP from the architectural specs in HLD.md and LLD.md. Each phase represents a discrete, testable chunk of work. All code examples are in [LLD.md](LLD.md); this doc tracks *what's done* vs. *what remains*.

---

## Current Status Snapshot

### ✅ Already Exists
- `CLAUDE.md` — project overview and tech stack
- `docs/HLD.md` — architecture and data flow
- `docs/LLD.md` — complete technical specifications with code examples
- `docker-compose.yml` — service definitions (db, backend, frontend)
- `backend/package.json` — dependencies and scripts
- `backend/tsconfig.json` — TypeScript configuration

### ❌ Missing (To Build)
- Backend source code (`backend/src/{types.ts, db.ts, claude.ts, server.ts}`)
- Backend Docker image (`backend/Dockerfile`)
- Frontend scaffolding (`frontend/` directory)
- Frontend components and styling
- Frontend Docker image (`frontend/Dockerfile`)
- Environment configuration (`.env.example`, `.gitignore`)

---

## Phase 1: Backend Implementation

**Objective**: Create a functional Express.js + TypeScript + PostgreSQL backend that handles the 4 core API endpoints.

### Phase 1.1: Backend Source Files

Copy exact code from LLD.md §4 into these new files:

- [ ] `backend/src/types.ts` — TypeScript interfaces (Encounter type)
- [ ] `backend/src/db.ts` — PostgreSQL connection pool, table initialization, queries
- [ ] `backend/src/claude.ts` — Claude API client, SOAP note generation
- [ ] `backend/src/server.ts` — Express app, all 4 routes (POST /encounters, POST /encounters/:id/generate, GET /encounters, GET /encounters/:id)

### Phase 1.2: Backend Dockerfile

- [ ] Create `backend/Dockerfile` (from LLD.md §6.1)
  - Base: `node:20-alpine`
  - Copy package files, install, copy src, expose 5000, run `npm run dev`

### Phase 1.3: Verify Backend

- [ ] Run `npm install` in `backend/` to confirm package.json is correct
- [ ] Run `npm run typecheck` in `backend/` — should pass with no errors
- [ ] Can parse and prepare to build Docker image

**Checkpoint**: Backend code complete and type-checks.

---

## Phase 2: Frontend Implementation

**Objective**: Create a React + Vite + TailwindCSS frontend with form input and note display.

### Phase 2.1: Frontend Scaffolding

- [ ] Create `frontend/` directory
- [ ] Create `frontend/package.json` with deps: react 18, typescript, vite, tailwindcss, axios (or fetch wrapper)
- [ ] Create `frontend/tsconfig.json` (standard React + TS config)
- [ ] Create `frontend/vite.config.ts` with React plugin
- [ ] Create `frontend/index.html` entry point with `<div id="root">`
- [ ] Create `frontend/src/index.css` — Tailwind imports

### Phase 2.2: Frontend Source Files

Copy exact code from LLD.md §5 into these new files:

- [ ] `frontend/src/types.ts` — TypeScript interfaces (Encounter type, form data)
- [ ] `frontend/src/api.ts` — fetch wrapper functions (createEncounter, generateNote, listEncounters, getEncounter)
- [ ] `frontend/src/components/EncounterForm.tsx` — form component with patient fields
- [ ] `frontend/src/components/NoteDisplay.tsx` — display generated SOAP note + copy button
- [ ] `frontend/src/components/EncounterList.tsx` — tab to browse past encounters
- [ ] `frontend/src/App.tsx` — main component orchestrating tabs and flows (from LLD.md §5.4)
- [ ] `frontend/src/main.tsx` — React entry point that mounts App

### Phase 2.3: Frontend Dockerfile

- [ ] Create `frontend/Dockerfile` (from LLD.md §6.2)
  - Base: `node:20-alpine`
  - Copy package files, install, copy src, expose 3000, run `npm run dev -- --host`

### Phase 2.4: Verify Frontend

- [ ] Run `npm install` in `frontend/` — confirm no conflicts
- [ ] Run `npm run typecheck` — should pass
- [ ] Can parse and prepare to build Docker image

**Checkpoint**: Frontend code complete, type-checks, builds without errors.

---

## Phase 3: Local Deployment & Verification

**Objective**: Run the full stack locally and verify the 4-endpoint flow works end-to-end.

### Phase 3.1: Environment & Config

- [ ] Create `.env.example` in project root with template vars:
  ```
  CLAUDE_API_KEY=sk-ant-...your-key-here...
  DATABASE_URL=postgresql://commure:commure_local_dev@db:5432/commure
  NODE_ENV=development
  PORT=5000
  ```
- [ ] Create `.gitignore` (node_modules, dist, .env, .env.local, *.log, .DS_Store)

### Phase 3.2: Local Setup

- [ ] Install PostgreSQL locally (Homebrew: `brew install postgresql`)
- [ ] Start PostgreSQL: `brew services start postgresql`
- [ ] Create database: `createdb commure`
- [ ] Install backend dependencies: `cd backend && npm install`
- [ ] Install frontend dependencies: `cd frontend && npm install`

### Phase 3.3: Local Run (Three Terminals)

**Terminal 1 - Backend:**
- [ ] Export `CLAUDE_API_KEY`: `export CLAUDE_API_KEY="sk-ant-..."`
- [ ] Run `cd backend && npm run dev`
- [ ] Verify: `Server running on port 5000` appears

**Terminal 2 - Frontend:**
- [ ] Run `cd frontend && npm run dev`
- [ ] Verify: `Local: http://localhost:3000` appears

**Terminal 3 - Testing:**
- [ ] PostgreSQL is running (verify with `psql -c "SELECT 1"`)

### Phase 3.4: Test API Endpoints

- [ ] `GET /api/encounters` on port 5000 returns empty list `{encounters: [], page: 1, total: 0}`
- [ ] `POST /api/encounters` with valid data returns created encounter with id
- [ ] `POST /api/encounters/:id/generate` calls Claude, returns generated SOAP note in <30s
- [ ] `GET /api/encounters/:id` returns full encounter including generated note

### Phase 3.4: Test UI Flow

- [ ] Open browser to `http://localhost:3000`
- [ ] "New Encounter" tab loads form without errors
- [ ] Fill out form (patient name, age, chief complaint, vitals, findings, assessment)
- [ ] Click "Generate SOAP Note"
- [ ] Generated note appears on page in <35s total
- [ ] Can copy note to clipboard
- [ ] Can switch to "View History" tab
- [ ] See list of past encounters
- [ ] Click on encounter → view full details + generated note

### Phase 3.5: Cleanup

- [ ] Press `Ctrl+C` in both backend and frontend terminals to stop them
- [ ] Run `brew services stop postgresql` to stop PostgreSQL
- [ ] Data persists in PostgreSQL (can restart without loss)

**Checkpoint**: Full stack deployed locally, all 4 endpoints working, UI responsive.

---

## Phase 4: Project Configuration (Skills & Hooks)

**Objective**: Set up Claude Code project-level scaffolding to make future work safer and faster.

### Phase 4.1: Create Project Skill: `run-app`

- [ ] Create `.claude/skills/run-app/SKILL.md` with:
  - Clear prerequisite: export `CLAUDE_API_KEY` before starting
  - **How to start**: `docker-compose up` (ports 3000, 5000, 5432)
  - **How to verify**: hit `GET /api/encounters`, load frontend
  - **How to view logs**: `docker-compose logs -f backend` / `frontend`
  - **How to stop**: `docker-compose down` (warn: `-v` deletes data)
  - **Common issues**: missing API key, port conflicts, database connection failures

### Phase 4.2: Create Project Settings with Hooks

- [ ] Use `update-config` skill to add `.claude/settings.json` with:
  - **Type-check on file save**: `PostToolUse` on Edit/Write matching `backend/src/**/*.ts` and `frontend/src/**/*.tsx?` → runs `npm run typecheck` in the matching workspace, blocks if errors
  - **Secret-leak guard**: `PreToolUse` on Bash matching `git add` / `git commit` → greps staged content for `.env` files or `sk-ant-` pattern, blocks if found

### Phase 4.3: Verify Configuration

- [ ] Confirm `.claude/skills/run-app/SKILL.md` exists and is readable
- [ ] Confirm `.claude/settings.json` has valid JSON and both hooks are defined
- [ ] Test (manual): create dummy file `backend/src/test.ts` with a type error, attempt edit → hook should report error
- [ ] Test (manual): attempt `git add .env.example` or similar → hook should check and warn

**Checkpoint**: Project-level configuration complete, safety guardrails in place.

---

## Success Criteria

✅ **Backend**: All 4 endpoints working, <100ms response, <30s note generation  
✅ **Frontend**: Form fills and submits, note displays in <35s, history browsable  
✅ **Deployment**: Single `docker-compose up` starts full stack, all services healthy  
✅ **Safety**: Type-checking and secret guards configured and functional  

---

## Next Steps After MVP

- [ ] User acceptance testing with real clinicians
- [ ] Phase 2: Multi-user, authentication, document types
- [ ] Phase 3: EHR integration, voice input, templates
- [ ] Phase 4: Production deployment, monitoring, compliance

---

## References

- See [LLD.md](LLD.md) for all code to copy
- See [HLD.md](HLD.md) for architecture context
- See [CLAUDE.md](../CLAUDE.md) for project overview and quick-start
