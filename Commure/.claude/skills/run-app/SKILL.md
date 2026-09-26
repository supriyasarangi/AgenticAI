# run-app

Start and verify the Commure clinical documentation MVP locally.

## Prerequisites

1. **Node.js 20+**: Required for backend and frontend
2. **PostgreSQL 15+**: Install locally (Homebrew on macOS, apt on Linux, or direct download)
3. **Claude API Key**: Export your Anthropic API key:
   ```bash
   export CLAUDE_API_KEY="sk-ant-..."
   ```
4. **Available Ports**: 3000 (frontend), 5000 (backend API), 5432 (PostgreSQL)

## Setup (First Time Only)

```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create the database
createdb commure

# Install backend dependencies
cd backend && npm install

# Install frontend dependencies
cd frontend && npm install
```

## Start the Application

**Terminal 1 - Backend:**
```bash
cd /home/labuser/Downloads/Commure/backend
export CLAUDE_API_KEY="sk-ant-..."
npm run dev
```
Should see: `Server running on port 5000`

**Terminal 2 - Frontend:**
```bash
cd /home/labuser/Downloads/Commure/frontend
npm run dev
```
Should see: `Local: http://localhost:3000`

## Verify It's Working

### Option 1: Quick API Test
```bash
curl http://localhost:5000/api/encounters
# Should return: {"encounters":[],"page":1,"limit":20,"total":0}
```

### Option 2: Browser Test
Open http://localhost:3000 in your browser:
1. Fill out the "New Encounter" form (patient name, age, chief complaint, vitals, etc.)
2. Click "Generate SOAP Note"
3. Wait <30 seconds; a professionally formatted SOAP note should appear
4. Click "View History" to see past encounters

## View Logs

Backend is already visible in Terminal 1 (where `npm run dev` runs).
Frontend is already visible in Terminal 2 (where `npm run dev` runs).

PostgreSQL logs:
```bash
tail -f /usr/local/var/log/postgres.log  # macOS
# or for Linux: journalctl -u postgresql
```

## Stop the Application

Simply press `Ctrl+C` in each terminal (backend and frontend).

PostgreSQL keeps running. To stop it:
```bash
brew services stop postgresql
```

## Connect to PostgreSQL Directly

```bash
psql commure

# View encounters:
SELECT id, patient_name, chief_complaint, created_at FROM encounters;

# Exit:
\q
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `connect ECONNREFUSED 127.0.0.1:5432` | PostgreSQL not running: `brew services start postgresql` |
| `Error: database "commure" does not exist` | Create it: `createdb commure` |
| `Port 5000 already in use` | Kill the process: `lsof -i :5000` then `kill -9 <PID>` |
| `Port 3000 already in use` | Kill the process: `lsof -i :3000` then `kill -9 <PID>` |
| Backend fails to connect to DB | Check PostgreSQL is running: `psql -c "SELECT 1"` |
| `CLAUDE_API_KEY not set` | Export it: `export CLAUDE_API_KEY="sk-ant-..."` |

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Backend crashes or exits silently | Missing `CLAUDE_API_KEY` | Export the API key: `export CLAUDE_API_KEY="sk-ant-..."`; restart `docker-compose up` |
| "Address already in use" error | Port 3000, 5000, or 5432 occupied | Stop other services using those ports, or modify `docker-compose.yml` to use different ports |
| Database connection refused | PostgreSQL not ready | Wait 10 seconds; docker-compose has a healthcheck but takes a moment |
| Frontend shows blank page | Check browser console | Look at `docker-compose logs -f frontend` for build errors |
| Claude API rate limit error | Too many requests | Wait 1 minute; Commure MVP generates one note per form submission (~20-25 tokens) |
| Frontend cannot reach backend | CORS or wrong URL | Backend must be running on 5000; frontend tries `http://localhost:5000` |

## Development Tips

**Hot reload**: Both frontend (React) and backend (ts-node) have hot reload enabled. Edit files and they auto-update without restarting the container.

**Stopping one service**: You can restart just the backend without stopping the DB:
```bash
docker-compose restart backend
```

**Entering a container shell**: Debug a running service:
```bash
docker-compose exec backend sh
docker-compose exec frontend sh
```

## API Reference (for manual testing)

See [docs/LLD.md](../../docs/LLD.md) §3 for full endpoint specs. Quick reference:

```bash
# Create an encounter
curl -X POST http://localhost:5000/api/encounters \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "John Doe",
    "age": 45,
    "chief_complaint": "Chest pain",
    "vital_signs": {"heart_rate": 72, "bp_systolic": 120, "bp_diastolic": 80, "temperature": 98.6},
    "clinical_findings": "Regular rate and rhythm, lungs clear",
    "assessment": "Possible anxiety, rule out cardiac cause"
  }'

# Generate a SOAP note for encounter ID 1
curl -X POST http://localhost:5000/api/encounters/1/generate

# Get the generated note
curl http://localhost:5000/api/encounters/1
```

## When to Use This Skill

Run this skill (`/run`) whenever you:
- Start a new development session and need to bring the app up
- Need to verify a change works in the running app
- Want to test the end-to-end flow locally before committing code
- Are about to deploy and want a final smoke test
