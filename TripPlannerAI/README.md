# ✈️ AI Multi-Agent Trip Planner

### Less time planning. More time exploring.

Planning a trip is exciting---until you're juggling weather forecasts,
attractions, routes, hotels, and a budget across a dozen tabs.

**AI Multi-Agent Trip Planner** brings those moving pieces into one
workflow. Enter a starting point, destination, budget, and trip
duration, and a coordinated team of AI agents helps turn those details
into a travel plan.

Built with **FastAPI, React, Tailwind CSS, and LangGraph**, the project
combines external travel data with multi-agent orchestration, streaming
updates, an interactive map, and PDF itinerary export.

------------------------------------------------------------------------

## 🌍 What can it do?

Rather than asking one assistant to do everything, the planner splits
the work into focused roles:

-   **🧭 Orchestrator** --- coordinates the workflow and brings the
    results together.
-   **🌦️ Weather agent** --- gathers weather information for the trip.
-   **📍 Places agent** --- looks up attractions and points of interest.
-   **🚗 Transport agent** --- gathers route and transportation
    information.
-   **🏨 Hotel agent** --- handles accommodation-related planning.
-   **💰 Budget agent** --- helps shape the plan around the available
    budget.
-   **🗓️ Itinerary and review agents** --- organize the information into
    a coherent plan and review it.
-   **📄 PDF export** --- turns the itinerary into a portable document.

Weather, places, transport, and hotel tasks can run in parallel after
orchestration, allowing independent parts of the research to happen
together.

## ✨ What's happening behind the scenes?

### A workflow, not just a prompt

[LangGraph](https://www.langchain.com/langgraph) coordinates the
specialist agents and the flow between them. Each agent has a focused
responsibility, and the workflow combines their results.

### Updates while the plan is being built

A streaming endpoint lets the frontend receive progressive updates
instead of waiting for the entire workflow to finish.

### Real travel data

The application integrates with: -
[OpenWeatherMap](https://openweathermap.org/) for weather information -
[OpenTripMap](https://opentripmap.io/) for places and attractions -
[OpenRouteService](https://openrouteservice.org/) for routing
information

### Maps and a plan you can take with you

Leaflet powers the route map, and the application supports PDF itinerary
export.

### Built to handle imperfect conditions

External APIs can be slow or unavailable, keys can be missing, and an
LLM may not respond. The app includes timeout protection and fallback
behavior. When the LLM is unavailable, the orchestrator and itinerary
agents can use deterministic structured outputs.

### Flexible preference memory

The memory layer supports ChromaDB, with a JSON-file fallback for
storing preferences when ChromaDB is not enabled.

------------------------------------------------------------------------

## 🧰 Tech stack

  Area                Technologies
  ------------------- ---------------------------------------------------
  Frontend            React, Tailwind CSS, Vite
  Backend             Python, FastAPI
  Agent workflow      LangGraph
  Travel data         OpenWeatherMap, OpenTripMap, OpenRouteService
  Maps and export     Leaflet, PDF export
  Preference memory   ChromaDB or JSON-file fallback
  API behavior        Streaming responses, timeouts, graceful fallbacks

------------------------------------------------------------------------

## 🗂️ Project structure

``` text
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

------------------------------------------------------------------------

## 🚀 Run it locally

You'll need **Python**, **Node.js/npm**, and API keys for the travel
services you want to use. These commands use PowerShell on Windows;
adjust the virtual-environment activation command for your shell.

### 1. Start the backend

From the project directory:

``` powershell
cd trip-planner/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add the required travel API keys to `backend/.env`. If you're using the
LLM-powered path, configure `OPENAI_API_KEY` too. Check `.env.example`
for the exact variable names expected by this project.

**Never commit real API keys or secrets to Git.**

Start the API:

``` powershell
uvicorn app.main:app --reload
```

Backend: <http://127.0.0.1:8000>

### 2. Start the frontend

Open a second terminal:

``` powershell
cd trip-planner/frontend
npm install
npm run dev
```

Frontend: <http://127.0.0.1:5173>

### 3. Try a sample trip

Use this example in the UI or in a direct API request:

``` json
{
  "user_id": "test",
  "source": "Bangalore",
  "destination": "Goa",
  "budget": 30000,
  "days": 5
}
```

This represents a five-day trip from Bangalore to Goa with a budget of
30,000. Change the source, destination, budget, and duration to try
another scenario.

------------------------------------------------------------------------

## 🔌 API endpoints

  -------------------------------------------------------------------------
  Method                  Endpoint                  Purpose
  ----------------------- ------------------------- -----------------------
  `GET`                   `/health`                 Health check

  `POST`                  `/generate`               Generate a trip plan

  `POST`                  `/generate-stream`        Generate a trip plan
                                                    with streaming updates

  `GET`                   `/generated/{filename}`   Retrieve a generated
                                                    file
  -------------------------------------------------------------------------

------------------------------------------------------------------------

## ⚙️ Configuration notes

-   **Travel API keys:** Add the keys required by the external services
    to `backend/.env`.
-   **LLM fallback:** If `OPENAI_API_KEY` is missing or the LLM cannot
    be reached, the orchestrator and itinerary agents can fall back to
    deterministic structured outputs.
-   **Preference memory:** Set `USE_CHROMA=true` in `backend/.env` to
    persist preferences in ChromaDB. Otherwise, preferences are stored
    in `backend/data/preferences.json`.
-   **External service issues:** Missing keys or unavailable network
    access should trigger fallback behavior rather than making local
    development hard-crash.

------------------------------------------------------------------------

## 🧠 Why this project is interesting

The interesting part isn't just generating an itinerary. It's
coordinating specialized agents, combining information from different
travel services, handling slow or unavailable dependencies, and
presenting the result through a usable interface.

This project brings together practical full-stack engineering and AI
application patterns: **agent orchestration, parallel tasks, streaming
APIs, external integrations, preference memory, and resilient
fallbacks**.

## 🛣️ The idea

Travel planning is made up of lots of small decisions. This project
explores how a team of focused agents can take on those pieces and bring
them into one plan---so the traveler can spend less time juggling tabs
and more time looking forward to the trip.

------------------------------------------------------------------------

*Have fun exploring, experimenting, and making the planner your own.*
