# Token Optimizer - Web Setup Guide

Modern web-based UI for the Token Optimizer platform.

## Architecture

- **Backend**: Flask (Python) - handles AI processing, token tracking, caching
- **Frontend**: React + TypeScript + Tailwind CSS - beautiful, responsive UI
- **Communication**: REST API + WebSocket for real-time updates

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Backend Setup (Flask)

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
# .env
AI_CLIPBOARD_OPTIMIZER_AI_PROVIDER=claude
AI_CLIPBOARD_OPTIMIZER_CLAUDE_API_KEY=your-key-here
```

3. Start Flask server:
```bash
python -m aiclipboardoptimizer.web.server
```

Server runs on `http://localhost:5000`

## Frontend Setup (React)

1. Install dependencies:
```bash
cd web
npm install
```

2. Start development server:
```bash
npm run dev
```

App runs on `http://localhost:5173`

## Features

### Dashboard
- Real-time token usage tracking
- Cost breakdown by provider/model/operation
- AI-powered cost reduction recommendations
- Visual statistics and trends

### Process
- Beautiful text processing interface
- Multiple AI operations (clean, summarize, translate, etc.)
- Copy/download results
- Real-time processing feedback

### Settings
- Select AI provider (Claude, OpenAI, Gemini, Ollama)
- Quality level selection (Budget/Balanced/Premium)
- Enable/disable caching and tracking
- Save preferences

### Onboarding
- Interactive tour for first-time users
- Explains tokens, providers, optimization strategies
- Quick tips and best practices

## API Endpoints

- `GET /health` - Health check
- `GET /api/operations` - List available operations
- `POST /api/process` - Process text
- `GET /api/stats` - Get usage statistics
- `GET /api/settings` - Get settings
- `POST /api/settings` - Update settings
- `GET /api/cache-stats` - Get cache statistics

## Development

Hot reload enabled for both backend (Flask debug) and frontend (Vite).

Make changes and see them instantly in the browser.

## Production Build

Frontend:
```bash
cd web
npm run build
npm run preview
```

Backend: Deploy with gunicorn or similar WSGI server.

## Next Steps

- [ ] Connect to actual AI provider APIs
- [ ] Add WebSocket for real-time updates
- [ ] Deploy to production (Vercel + Flask)
- [ ] Add authentication
- [ ] Mobile app version
