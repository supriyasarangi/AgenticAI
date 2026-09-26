# Commure Frontend

React 18 + TypeScript + Vite + TailwindCSS frontend for the Commure clinical documentation automation system.

## Quick Start

### Prerequisites
- Node.js 20+
- Backend running on http://localhost:5000 (or set VITE_API_URL environment variable)

### Development

```bash
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── EncounterForm.tsx      # Form to create new encounters
│   │   ├── NoteDisplay.tsx        # Display and copy generated SOAP notes
│   │   └── EncounterList.tsx      # View and manage encounter history
│   ├── App.tsx                    # Main app component with tab navigation
│   ├── api.ts                     # API client functions
│   ├── types.ts                   # TypeScript interfaces
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles with Tailwind
├── index.html                     # HTML entry point
├── package.json                   # Dependencies
├── tsconfig.json                  # TypeScript configuration
├── vite.config.ts                 # Vite build configuration
├── tailwind.config.js             # Tailwind CSS configuration
└── postcss.config.js              # PostCSS configuration
```

## Features

- **New Encounter**: Form to input patient data (demographics, vitals, findings, assessment)
- **Auto-Generate SOAP Notes**: Integrated with Claude AI for instant note generation
- **View History**: Browse past encounters with pagination
- **Copy to Clipboard**: Quick copy of generated notes
- **Download Notes**: Save SOAP notes as text files
- **Responsive Design**: Works on desktop and mobile devices

## Environment Variables

```bash
# Optional - default is http://localhost:5000
VITE_API_URL=http://your-backend-url:5000
```

## API Integration

The frontend communicates with the backend API:

- `POST /api/encounters` - Create new encounter
- `POST /api/encounters/:id/generate` - Generate SOAP note
- `GET /api/encounters` - List encounters (paginated)
- `GET /api/encounters/:id` - Get single encounter details

See backend documentation for full API spec.

## Testing

Manual testing checklist:

1. Fill out encounter form and submit
2. Verify SOAP note generates and displays
3. Test copy to clipboard
4. Test download functionality
5. View encounter history
6. Navigate through pagination
7. View and regenerate notes from history
8. Test error handling (missing fields, API errors)

## Performance Targets

- Form submission to note display: <35 seconds (mostly Claude API time)
- Page load: <1 second
- API response: <100ms

## Common Commands

```bash
# Development server with HMR
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Lint code (if configured)
npm run lint
```

## Troubleshooting

**Port 3000 already in use:**
```bash
npm run dev -- --port 3001
```

**API connection issues:**
- Ensure backend is running on port 5000
- Check VITE_API_URL environment variable
- Verify CORS is enabled on backend

**Build errors:**
```bash
rm -rf node_modules
npm install
npm run build
```
