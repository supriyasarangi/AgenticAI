# Commure MVP - Quick Start Guide

## Getting Started with Commure Clinical Documentation

This is a complete clinical documentation automation system with a React frontend and Node.js backend.

### System Requirements

- Node.js 20+
- Docker & Docker Compose (optional, for containerized deployment)
- Claude API key from Anthropic
- PostgreSQL 15+ (local or Docker)

### Option 1: Local Development (Easiest)

#### 1. Set Up Environment

```bash
# Set your Claude API key
export CLAUDE_API_KEY="sk-ant-xxxxx..."

# Verify you're in the Commure directory
cd /home/labuser/Downloads/Commure
```

#### 2. Start PostgreSQL

**macOS with Homebrew:**
```bash
brew services start postgresql
createdb commure
```

**Linux (Ubuntu/Debian):**
```bash
sudo systemctl start postgresql
sudo -u postgres createdb commure
```

**Verify PostgreSQL is running:**
```bash
psql -d commure -c "SELECT 1"
```

#### 3. Start Backend (Terminal 1)

```bash
cd /home/labuser/Downloads/Commure/backend

npm install          # First time only
npm run dev

# Output: Server running on port 5000
```

#### 4. Start Frontend (Terminal 2)

```bash
cd /home/labuser/Downloads/Commure/frontend

npm install          # First time only
npm run dev

# Output: http://localhost:3000
```

#### 5. Open Browser

Navigate to: **http://localhost:3000**

Done! You can now:
1. Create new patient encounters
2. Generate SOAP notes with Claude AI
3. View encounter history
4. Copy/download generated notes

---

### Option 2: Docker Deployment (Full Stack)

#### 1. Prerequisites

Ensure Docker and Docker Compose are installed:

```bash
docker --version
docker-compose --version
```

#### 2. Start All Services

```bash
cd /home/labuser/Downloads/Commure

# Set Claude API key
export CLAUDE_API_KEY="sk-ant-xxxxx..."

# Start all services
docker-compose up

# Wait for "Server running on port 5000" message
```

#### 3. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **PostgreSQL**: localhost:5432 (user: commure, password: commure_local_dev)

#### 4. Stop Services

```bash
docker-compose down

# To delete all data
docker-compose down -v
```

---

## Usage

### Creating an Encounter

1. Click **"New Encounter"** tab
2. Fill in patient information:
   - Patient name
   - Age
   - Chief complaint
   - Vital signs (heart rate, blood pressure, temperature)
   - Clinical findings
   - Assessment
3. Click **"Create & Generate Note"**
4. Wait for Claude AI to generate the SOAP note (~15-30 seconds)
5. View, copy, or download the note

### Viewing History

1. Click **"View History"** tab
2. Browse past encounters in the table
3. Click **"View"** to see full encounter details
4. Generate notes for encounters that don't have them yet
5. Use pagination to navigate through records

---

## Key Features

✓ **Automated SOAP Note Generation** - Claude AI generates professional notes in seconds
✓ **Patient Encounter History** - All encounters stored in PostgreSQL
✓ **Copy to Clipboard** - One-click copy of generated notes
✓ **Download Notes** - Save notes as text files
✓ **Pagination** - Browse history with pagination controls
✓ **Form Validation** - Client-side validation with user feedback
✓ **Error Handling** - Graceful error display and recovery
✓ **Responsive Design** - Works on desktop and mobile

---

## API Documentation

See individual README files for detailed documentation:

- **Frontend**: `frontend/README.md`
- **Backend**: Check backend/package.json for scripts

### Main Endpoints

```
POST   /api/encounters              Create new encounter
POST   /api/encounters/:id/generate Generate SOAP note
GET    /api/encounters              List encounters (paginated)
GET    /api/encounters/:id          Get encounter details
```

---

## Troubleshooting

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
psql -c "SELECT 1"

# macOS: Start PostgreSQL
brew services start postgresql

# Linux: Start PostgreSQL
sudo systemctl start postgresql
```

### "Port 5000 already in use"

```bash
# Find and kill process on port 5000
lsof -i :5000
kill -9 <PID>

# Or use different port
PORT=5001 npm run dev
```

### "Port 3000 already in use"

```bash
# Find and kill process on port 3000
lsof -i :3000
kill -9 <PID>

# Or use different port
npm run dev -- --port 3001
```

### Frontend Can't Connect to Backend

```bash
# Verify backend is running
curl http://localhost:5000/health

# Check CORS is enabled (it should be by default)
# If issues persist, check vite.config.ts proxy settings
```

### "CLAUDE_API_KEY not set"

```bash
# Set your Claude API key
export CLAUDE_API_KEY="sk-ant-xxxxx..."

# Verify it's set
echo $CLAUDE_API_KEY
```

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up

# View logs
docker-compose logs frontend
docker-compose logs backend
docker-compose logs db
```

---

## Performance Targets

| Operation | Target | Typical |
|-----------|--------|---------|
| Create encounter | <1s | <500ms |
| Generate SOAP note | <30s | 15-25s |
| View history | <1s | <500ms |
| Copy note | instant | <100ms |

---

## File Structure

```
Commure/
├── frontend/                  React 18 + TypeScript + Vite
│   ├── src/                   Source code
│   ├── package.json           Dependencies
│   └── README.md              Frontend documentation
│
├── backend/                   Node.js + Express + PostgreSQL
│   ├── src/                   Source code
│   ├── package.json           Dependencies
│   └── Dockerfile             Container configuration
│
├── docs/                      Architecture documentation
│   ├── HLD.md                 High-level design
│   ├── LLD.md                 Low-level design
│   └── PLAN.md                Implementation plan
│
├── docker-compose.yml         Full stack orchestration
├── CLAUDE.md                  Project instructions
├── QUICKSTART.md              This file
└── FRONTEND_INTEGRATION.md    Frontend setup guide
```

---

## Development Workflow

### Making Changes

1. Frontend changes auto-reload with Vite HMR
2. Backend changes require manual restart (`npm run dev`)
3. Database schema changes require manual migration

### Testing

For MVP, manual testing is sufficient:

1. Create a test encounter
2. Generate a note
3. View history
4. Test error cases (missing fields, API errors)

See `docs/LLD.md` for manual testing checklist.

---

## Deployment

### To Production

1. Build frontend: `npm run build` in frontend/
2. Build backend: `npm run build` in backend/
3. Use Docker images for deployment
4. Set environment variables (CLAUDE_API_KEY, DATABASE_URL)
5. Configure reverse proxy (nginx, CloudFlare, etc.)

### Environment Variables

**Backend:**
- `CLAUDE_API_KEY` - Your Anthropic API key (required)
- `DATABASE_URL` - PostgreSQL connection string
- `NODE_ENV` - Set to "production"
- `PORT` - Server port (default: 5000)

**Frontend:**
- `VITE_API_URL` - Backend URL (default: http://localhost:5000)

---

## Next Steps

1. **Add Tests** - Unit and E2E tests
2. **User Auth** - Authentication system (future phase)
3. **EHR Integration** - Connect to real EHR systems (future phase)
4. **Mobile App** - React Native version (future phase)
5. **Analytics** - Track usage and performance

---

## Support & Documentation

- **Frontend Details**: See `frontend/README.md`
- **Architecture**: See `docs/HLD.md` and `docs/LLD.md`
- **API Spec**: See `docs/LLD.md` Section 3
- **Integration**: See `FRONTEND_INTEGRATION.md`

---

## MVP Scope Included

✓ Patient encounter form
✓ Claude AI SOAP note generation
✓ Encounter history with pagination
✓ Copy and download notes
✓ Local PostgreSQL database
✓ Docker containerization
✓ Full TypeScript type safety
✓ Responsive UI with TailwindCSS

---

**Commure MVP is ready to use! Enjoy automating clinical documentation.**

For questions or issues, check the documentation files or review the code comments.
