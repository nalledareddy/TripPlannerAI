
# AI Multi-Agent Trip Planner

A trip planning application that uses multiple AI agents to prepare an itinerary based on the source, destination, budget, and number of days.

The application has a FastAPI backend and a React frontend. LangGraph coordinates the agents. The system uses external APIs for weather, places, and routes, and supports streaming responses, route maps, PDF export, and preference storage.

## Features

- LangGraph workflow with an orchestrator and separate agents for weather, places, transport, hotels, budget, itinerary, review, and PDF generation
- Parallel execution of weather, places, transport, and hotel tasks
- Streaming endpoint for progressive updates in the frontend
- OpenWeatherMap, OpenTripMap, and OpenRouteService integrations
- Leaflet route map and PDF itinerary export
- Timeout handling and fallback responses when external APIs or the LLM are unavailable
- Preference storage using ChromaDB or a JSON file

## Tech Stack

Frontend: React, Tailwind CSS, Vite

Backend: Python, FastAPI

Agent workflow: LangGraph

External APIs: OpenWeatherMap, OpenTripMap, OpenRouteService

Maps: Leaflet

Memory: ChromaDB with JSON file fallback

## Project Structure

```text
trip-planner/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
└── README.md
```

## Setup

### Backend

Open a terminal and move into the backend directory.

```powershell
cd trip-planner/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add the required API keys to `backend/.env`. Check `.env.example` for the exact environment variable names. Configure `OPENAI_API_KEY` if using the LLM-powered workflow.

Start the backend:

```powershell
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

### Frontend

Open a second terminal and move into the frontend directory.

```powershell
cd trip-planner/frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:5173`.

## Example Request

Use this payload in the frontend or when calling the API directly.

```json
{
  "user_id": "test",
  "source": "Bangalore",
  "destination": "Goa",
  "budget": 30000,
  "days": 5
}
```

This requests a five day trip from Bangalore to Goa with a budget of 30000.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/generate` | Generate a trip plan |
| POST | `/generate-stream` | Generate a trip plan with streaming updates |
| GET | `/generated/{filename}` | Retrieve a generated file |

## Configuration

Set `USE_CHROMA=true` in `backend/.env` to store preferences in ChromaDB. Otherwise, preferences are stored in `backend/data/preferences.json`.

If API keys are missing or external services are unavailable, the application can use fallback data. If `OPENAI_API_KEY` is missing or the LLM cannot be reached, the orchestrator and itinerary agents can return deterministic structured outputs.

Do not commit API keys or other secrets to the repository.
