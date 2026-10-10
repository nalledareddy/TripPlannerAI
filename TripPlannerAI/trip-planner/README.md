# AI Multi-Agent Trip Planner

Production-ready full-stack trip planner using FastAPI, React, Tailwind, LangGraph, OpenWeatherMap, OpenTripMap, OpenRouteService, file/Chroma memory, and PDF export.

## Features

- LangGraph workflow with an orchestrator plus weather, places, transport, hotel, budget, itinerary, review, and PDF agents
- Parallel execution for weather, places, transport, and hotel after orchestration
- Streaming endpoint for progressive frontend updates
- Centralized API client layer with timeout protection and graceful fallbacks
- Memory layer with ChromaDB support and automatic JSON-file fallback
- Leaflet route map and PDF export
- Safe operation even when external APIs or the LLM are unavailable

## Folder Structure

```text
trip-planner/
|- backend/
|  |- app/
|  |- requirements.txt
|  |- .env
|  `- .env.example
|- frontend/
|  |- src/
|  |- index.html
|  |- package.json
|  |- postcss.config.js
|  |- tailwind.config.js
|  `- vite.config.js
`- README.md
```

## Backend Setup

1. Open a terminal in `trip-planner/backend`
2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy `.env.example` into `.env` if you want a clean template
4. Add free API keys for:
   - OpenWeatherMap
   - OpenTripMap
   - OpenRouteService
5. Start the backend

```powershell
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`

## Frontend Setup

1. Open a second terminal in `trip-planner/frontend`
2. Install dependencies

```powershell
npm install
```

3. Start the frontend

```powershell
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`

## Test Payload

Use this payload in the UI or direct API calls:

```json
{
  "user_id": "test",
  "source": "Bangalore",
  "destination": "Goa",
  "budget": 30000,
  "days": 5
}
```

## API Endpoints

- `GET /health`
- `POST /generate`
- `POST /generate-stream`
- `GET /generated/{filename}`

## Notes

- If API keys are missing or outbound network access is unavailable, the app still works with safe fallback data so local development never hard-crashes.
- If `OPENAI_API_KEY` is missing or the LLM is unreachable, the orchestrator and itinerary agents fall back to deterministic structured outputs.
- Set `USE_CHROMA=true` in `backend/.env` to persist user preferences in ChromaDB. Otherwise the app stores them in `backend/data/preferences.json`.
