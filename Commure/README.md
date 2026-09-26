# Commure - Clinical Documentation Automation

Commure is an AI-powered clinical documentation automation system that generates professional SOAP notes from patient encounter data in under 30 seconds. Built with Claude AI, React, and Node.js.

## 🎯 What is Commure?

Commure addresses a critical pain point in healthcare: clinicians spend 2-3 hours daily on documentation. This MVP demonstrates how Claude AI can automate SOAP note generation from structured patient encounter data, dramatically reducing documentation time.

**Key Features:**
- ✅ **Automated SOAP Note Generation** - Claude AI generates professional clinical notes from encounter data
- ✅ **Patient Encounter Management** - Store and retrieve patient encounters with full history
- ✅ **One-Click Export** - Copy or download generated notes to clipboard
- ✅ **Local-First Architecture** - Everything runs on your machine with Docker
- ✅ **Type-Safe** - Full TypeScript implementation with strict typing
- ✅ **Responsive UI** - Works on desktop and mobile browsers

## 🚀 Quick Start

### Prerequisites
- **Node.js** 20+
- **Docker & Docker Compose** (for containerized deployment)
- **Claude API Key** from [Anthropic](https://console.anthropic.com)
- **PostgreSQL** 15+ (local or via Docker)

### Option 1: Local Development (Recommended for First-Time Users)

```bash
# 1. Navigate to Commure directory
cd Commure

# 2. Set your Claude API key
export CLAUDE_API_KEY="sk-ant-xxxxx..."

# 3. Start PostgreSQL (macOS with Homebrew)
brew services start postgresql
createdb commure

# 4. Terminal 1 - Start Backend
cd backend
npm install
npm run dev
# Output: Server running on port 5000

# 5. Terminal 2 - Start Frontend
cd frontend
npm install
npm run dev
# Output: http://localhost:3000
```

**Done!** Open http://localhost:3000 in your browser.

### Option 2: Docker (Full Stack)

```bash
# 1. Set your Claude API key
export CLAUDE_API_KEY="sk-ant-xxxxx..."

# 2. Start all services
cd Commure
docker-compose up

# 3. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

## 📋 Usage

### Creating a New Encounter

1. Click **"New Encounter"** tab
2. Fill in patient information:
   - **Patient Name** - Full name
   - **Age** - Patient age
   - **Chief Complaint** - Primary reason for visit
   - **Vital Signs** - Heart rate, blood pressure, temperature
   - **Clinical Findings** - Examination results and observations
   - **Assessment** - Initial clinical impression
3. Click **"Create & Generate Note"**
4. Wait for Claude to generate the SOAP note (~15-30 seconds)
5. Review the note in the SOAP display area
6. Copy to clipboard or download as text file

### Viewing Encounter History

1. Click **"View History"** tab
2. Browse all past encounters in the table
3. Click **"View"** to see full encounter details
4. Generate notes for encounters that don't have them yet
5. Use pagination to navigate through records

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────┐
│    Web Browser (http://localhost:3000)  │
│    React App - Forms & SOAP Display     │
└────────────────┬────────────────────────┘
                 │ HTTP/JSON
                 ▼
┌─────────────────────────────────────────┐
│   Express Server (http://localhost:5000)│
│   - Encounter CRUD                      │
│   - Claude API Integration              │
│   - SOAP Note Generation                │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴──────────┐
    │                       │
    ▼                       ▼
┌─────────────┐      ┌──────────────────┐
│ PostgreSQL  │      │  Claude API      │
│ localhost   │      │  (Anthropic)     │
│ encounters  │      │                  │
└─────────────┘      └──────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | React 18 + TypeScript + Vite + TailwindCSS |
| **Backend** | Node.js 20 + Express.js + TypeScript |
| **Database** | PostgreSQL 15 (local or Docker) |
| **Container** | Docker + Docker Compose |
| **AI** | Claude API (Anthropic) |

## 📁 Project Structure

```
Commure/
├── frontend/                  # React web application
│   ├── src/
│   │   ├── App.tsx           # Main app component
│   │   ├── components/       # React components
│   │   ├── api.ts            # Backend API client
│   │   ├── types.ts          # TypeScript types
│   │   └── main.tsx          # React entry point
│   ├── vite.config.ts        # Vite configuration
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md             # Frontend documentation
│
├── backend/                   # Node.js/Express API
│   ├── src/
│   │   ├── server.ts         # Express server & routes
│   │   ├── db.ts             # PostgreSQL client & queries
│   │   ├── claude.ts         # Claude API wrapper
│   │   └── types.ts          # TypeScript types
│   ├── Dockerfile            # Backend container
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md             # Backend documentation
│
├── docs/                      # Architecture & design docs
│   ├── HLD.md                # High-level design
│   ├── LLD.md                # Low-level technical specs
│   └── PLAN.md               # Implementation plan
│
├── docker-compose.yml        # Full stack orchestration
├── .env                       # Environment variables (example)
├── CLAUDE.md                 # Claude Code instructions
├── QUICKSTART.md             # Quick start guide
└── README.md                 # This file
```

## 🔌 API Endpoints

### Encounters

```bash
# Create new encounter
POST /api/encounters
Content-Type: application/json
{
  "patient_name": "John Doe",
  "age": 45,
  "chief_complaint": "Chest pain",
  "vital_signs": {"hr": 72, "bp": "120/80", "temp": 98.6},
  "clinical_findings": "Regular rate and rhythm, lungs clear",
  "assessment": "Possible anxiety, rule out cardiac cause"
}

# Generate SOAP note for encounter
POST /api/encounters/:id/generate

# List all encounters (paginated)
GET /api/encounters?page=1&limit=10

# Get single encounter with details
GET /api/encounters/:id
```

See [docs/LLD.md](docs/LLD.md) for complete API specification.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the Commure directory:

```env
# Claude API (required)
CLAUDE_API_KEY=sk-ant-xxxxx...

# Backend
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://localhost/commure

# Frontend
VITE_API_URL=http://localhost:5000
```

### Database

PostgreSQL is initialized automatically with Docker Compose. For local development:

```bash
# macOS with Homebrew
brew services start postgresql
createdb commure

# Linux (Ubuntu/Debian)
sudo systemctl start postgresql
sudo -u postgres createdb commure

# Verify connection
psql -d commure -c "SELECT 1"
```

## 🧪 Testing

### Manual Testing Workflow

1. **Create Encounter**
   - Fill in all required fields
   - Click "Generate"
   - Verify note is generated within 30 seconds

2. **View History**
   - Navigate to history tab
   - Verify past encounters appear
   - Test pagination

3. **Error Handling**
   - Try submitting with missing fields
   - Disconnect backend and verify error message
   - Test API errors gracefully

See [docs/LLD.md](docs/LLD.md) for complete testing checklist.

## 📊 Performance

| Operation | Target | Typical |
|-----------|--------|---------|
| Create encounter | <1s | <500ms |
| Generate SOAP note | <30s | 15-25s |
| List encounters | <1s | <500ms |
| Copy note | instant | <100ms |

## 🐛 Troubleshooting

### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
psql -c "SELECT 1"

# macOS: Start PostgreSQL
brew services start postgresql

# Linux: Start PostgreSQL
sudo systemctl start postgresql
```

### Port Already in Use
```bash
# Backend on different port
PORT=5001 npm run dev

# Frontend on different port
npm run dev -- --port 3001
```

### Frontend Can't Connect to Backend
```bash
# Verify backend is running
curl http://localhost:5000/health

# Check backend logs for errors
# Restart backend: npm run dev
```

### Claude API Error
```bash
# Verify API key is set
echo $CLAUDE_API_KEY

# Set API key
export CLAUDE_API_KEY="sk-ant-xxxxx..."

# Restart backend
npm run dev
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

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide with detailed setup steps
- **[docs/HLD.md](docs/HLD.md)** - High-level architecture and design decisions
- **[docs/LLD.md](docs/LLD.md)** - Technical specifications and API details
- **[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)** - Frontend setup guide
- **[frontend/README.md](frontend/README.md)** - Frontend-specific documentation
- **[CLAUDE.md](CLAUDE.md)** - Claude Code project instructions

## 🎓 MVP Scope

### What's Included ✅
- Patient encounter form
- Claude AI SOAP note generation
- Encounter history with pagination
- Copy and download notes
- Local PostgreSQL database
- Docker containerization
- Full TypeScript type safety
- Responsive UI with TailwindCSS

### Not Included (Future Phases) ❌
- User authentication
- Multi-user access
- Voice recording/transcription
- EHR system integration
- Document signing
- Audit logging
- Production deployment
- HIPAA compliance

## 🚀 Next Steps

1. **Add Tests** - Unit tests and E2E test coverage
2. **User Authentication** - Multi-user support with auth
3. **Advanced Prompting** - Specialty-specific note templates
4. **Voice Input** - Speech-to-text for encounter data
5. **EHR Integration** - Connect to real electronic health records
6. **Mobile App** - React Native version for clinicians on the go

## 📝 License

This project is part of the AgenticAI initiative.

## 🤝 Support

For questions or issues:
1. Check the [docs](docs/) folder for architecture details
2. Review [CLAUDE.md](CLAUDE.md) for development guidance
3. See [QUICKSTART.md](QUICKSTART.md) for setup help
4. Review code comments for implementation details

---

**Ready to automate clinical documentation?**

```bash
docker-compose up
# Open http://localhost:3000
```

Enjoy using Commure! 🎉
