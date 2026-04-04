# FarmGenAI

FarmGenAI is an AI-assisted agricultural negotiation platform where farmer and buyer agents negotiate price and quantity, with fallback paths for storage, processing, and compost workflows.

This repository includes:

- FastAPI backend APIs and WebSocket negotiation stream
- Multi-agent negotiation logic and simulation engine
- Static frontend dashboard, listing form, auth pages, and simulation UI
- SQLite persistence layer

## Features

- Live negotiation updates over WebSocket
- Marketplace buyer screening and best-offer selection
- Negotiation history and logs
- Simulation scenarios (`direct-sale`, `storage`, `processing`, `all`)
- Basic auth endpoints and UI integration
- Warehouse storage and transport assignment endpoints

## Tech Stack

- Python 3.10+
- FastAPI + Uvicorn
- SQLite
- Vanilla HTML/CSS/JS frontend

## Project Layout

- `backend/`: API routes, controllers, services, websocket hub
- `agents/`: buyer/farmer/warehouse/transporter/processor/compost agents
- `negotiation_engine/`: negotiation manager and support logic
- `simulation/`: scenario runner and metrics
- `frontend/`: static web UI
- `database/`: DB wrapper and schema references
- `tests/`: unit and integration-style test modules

## Local Development

1. Create and activate a virtual environment.
2. Install dependencies.
3. Start backend API.
4. Serve frontend static files.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal:

```powershell
python -m http.server 5500 --directory frontend
```

Then open:

- Frontend: `http://localhost:5500/index.html`
- Backend API docs: `http://localhost:8000/docs`

## Docker Setup

This repo includes Dockerfiles and Docker Compose for backend + frontend.

### Run

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Stop

```powershell
docker compose down
```

Data is persisted in `./data/agrinegotiator.db` through a bind mount.

## Environment Variables

Optional variables:

- `DB_PATH` (default: `agrinegotiator.db`)
- `ENABLE_LLM` (`true`/`false`)
- `FEATHERLESS_API_KEY`
- `FEATHERLESS_BASE_URL`

Create a `.env` file in repository root if needed.

## Useful API Endpoints

- `POST /start-negotiation`
- `GET /negotiation-status/{negotiation_id}`
- `GET /api/negotiations`
- `GET /agents`
- `POST /run-simulation`
- `GET /api/warehouse/`
- `POST /api/warehouse/assign-storage`
- `POST /api/warehouse/assign-transport`
- `GET /api/warehouse/fleet`

## Run Tests

```powershell
python -m unittest discover -s tests -v
```

## Notes

- Frontend API base is currently hardcoded to `http://localhost:8000` in `frontend/js/api.js`.
- If you run frontend on another host/port, update that file accordingly.
