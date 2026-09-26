# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Commure - Clinical Documentation Automation

A system that automates clinical documentation generation directly from patient encounters using Claude AI.

### Core Value Proposition
- **Problem**: Clinicians spend hours daily on documentation
- **Solution**: AI-powered automated SOAP note generation from encounter data
- **MVP Goal**: Working local application for clinicians to test document generation

## MVP Scope (This Phase)

**In Scope:**
- ✅ Simple web form to enter patient encounter data
- ✅ Claude AI generates SOAP notes in <30 seconds
- ✅ Display and edit generated notes
- ✅ Store encounters in local PostgreSQL database
- ✅ View history of past encounters
- ✅ Copy notes to clipboard
- ✅ Local Docker deployment

**Out of Scope (Future Phases):**
- ❌ User authentication / multi-user
- ❌ EHR integration
- ❌ Voice recording / transcription
- ❌ Complex RBAC or audit logging
- ❌ Multiple document types (MVP: SOAP notes only)
- ❌ Advanced validation rules or templates
- ❌ Production compliance/HIPAA (development use only)

## Tech Stack

**Backend:**
- Node.js + Express.js + TypeScript
- PostgreSQL (local Docker)
- Claude API for AI generation

**Frontend:**
- React + TypeScript + Vite
- TailwindCSS for styling
- Simple, no complex state management

**Deployment:**
- Docker + Docker Compose (local only)
- Single docker-compose.yml starts everything

## Quick Start

```bash
# 1. Start PostgreSQL locally (macOS with Homebrew)
brew services start postgresql

# 2. Create database
createdb commure

# 3. Set your Claude API key
export CLAUDE_API_KEY="sk-ant-..."

# 4. Terminal 1: Backend
cd backend
npm install
npm run dev

# 5. Terminal 2: Frontend
cd frontend
npm install
npm run dev

# 6. Open browser
http://localhost:3000
```

## Development Setup

### Prerequisites
- Node.js 20+
- PostgreSQL 15+ (local installation)
- Claude API key (export as CLAUDE_API_KEY)

### Common Commands

```bash
# Start PostgreSQL (macOS)
brew services start postgresql
# Stop: brew services stop postgresql

# Check if PostgreSQL is running
psql -c "SELECT 1"

# Backend development
cd backend && npm run dev

# Frontend development
cd frontend && npm run dev

# Access database directly
psql -d commure
```

## Project Structure

```
commure/
├── backend/
│   ├── src/
│   │   ├── server.ts          # Express server, routes
│   │   ├── db.ts              # PostgreSQL connection & queries
│   │   ├── claude.ts          # Claude API wrapper
│   │   └── types.ts           # TypeScript types
│   ├── Dockerfile
│   └── package.json
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Main app component
│   │   ├── components/
│   │   │   ├── EncounterForm.tsx
│   │   │   └── NoteDisplay.tsx
│   │   ├── api.ts             # API client
│   │   └── types.ts           # TypeScript types
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── CLAUDE.md (this file)
├── HLD.md (architecture overview)
└── LLD.md (detailed technical specs)
```

## Key Architecture Decisions

- **Single table, single entity**: Encounters with embedded data (JSONB for vitals, etc.)
- **Synchronous API**: Generate notes on-demand, return immediately
- **Local first**: All data stored locally, no cloud services required for MVP
- **No auth**: Local development only, single user
- **Simple UI**: Focus on functionality, not design

## API Overview

See [LLD.md](docs/LLD.md) for detailed specs. Quick reference:

```
POST   /api/encounters           - Create encounter
POST   /api/encounters/:id/generate - Generate SOAP note
GET    /api/encounters           - List encounters
GET    /api/encounters/:id       - Get encounter + note
```

## Performance Targets (MVP)

- Document generation: <30 seconds
- API response: <100ms
- Form submission to note display: <35 seconds

## References

- [HLD.md](docs/HLD.md) - MVP architecture overview
- [LLD.md](docs/LLD.md) - Technical specifications and API details
