# AgriNegotiator 🌾🤖

AgriNegotiator is a state-of-the-art, AI-powered multi-agent agricultural negotiation platform. It enables farmers and buyers to negotiate naturally using conversational AI agents, while seamlessly integrating real-world constraints like live APMC mandi prices, weather conditions, spoilage risks, and supply chain fallbacks (warehouse, transport, processing, and compost).

---

## 🌟 Key Features

- **Multi-Agent Orchestration (LangGraph):** Employs distinct LangChain agents for Farmers, Buyers, Warehouses, Transporters, Processors, and Compost plants.
- **RAG-Driven Market Intelligence:** Agents consult ChromaDB vector stores containing real-time government Minimum Support Prices (MSP), daily mandi arrivals, and official crop cultivation guidelines to prevent LLM hallucination.
- **Explainable AI (XAI) & Reflection:** Every negotiation outcome is analyzed by a Reflection Agent and logged into a continuous-learning PostgreSQL memory store to improve future strategies.
- **Live Websocket Streams:** Built on Redis Pub/Sub to push real-time negotiation messages directly to the frontend.
- **Premium User Interface:** A modern, TypeScript-based React frontend utilizing Tailwind CSS with mesh gradients, glassmorphism, and Framer Motion micro-animations.

---

## 🛠️ Technology Stack

### Frontend
- **React 18** (Vite + TypeScript)
- **Tailwind CSS** (Custom dark mesh gradient branding)
- **Axios** (API Client)
- **Native WebSockets** (Real-time updates)

### Backend
- **FastAPI** (Python 3.11, Dependency Injection pattern)
- **LangGraph & LangChain** (AI Agent State Machine)
- **ChromaDB** (Vector Database for RAG)
- **Ollama** (Local Qwen3/Llama3.1) with **Gemini API** Fallback support

### Data Layer
- **PostgreSQL** (Primary Relational Database via SQLAlchemy + asyncpg)
- **Redis** (WebSocket Pub/Sub & Caching)

### DevOps
- **Docker** & **Docker Compose**
- **GitHub Actions** (CI/CD Pipeline)

---

## 📁 Project Structure

```
├── backend/
│   ├── agents/          # LangGraph Nodes & Orchestrator
│   ├── controllers/     # API Route Handlers
│   ├── dataset/         # CSVs & Knowledge Base (Mandi Prices, Schemes)
│   ├── db/              # SQLAlchemy Models & Schema
│   ├── repositories/    # Database DI Repositories
│   └── services/        # RAG Service, External APIs (OpenMeteo, Agmarknet)
├── frontend/            # React + TypeScript Web Application
├── scripts/             # Data Seeders & E2E CI/CD Integration Tests
└── .github/workflows/   # Automated CI Pipeline Configurations
```

---

## 🚀 Local Setup & Development

### 1. Environment Variables
Create a `.env` file in the root directory:
```env
# Database Connections
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agrinegotiator
REDIS_URL=redis://localhost:6379/0

# AI Configuration
LLM_PROVIDER=ollama
GEMINI_API_KEY=your_gemini_key_here
EMBEDDING_MODEL=all-MiniLM-L6-v2

# APIs
DATA_GOV_IN_API_KEY=your_agmarknet_key_here
```

### 2. Docker Quickstart
The easiest way to boot the entire stack (PostgreSQL, Redis, ChromaDB, FastAPI Backend, and React Frontend) is via Docker Compose:

```bash
docker compose up --build
```
- **Frontend Dashboard:** `http://localhost:8080`
- **Backend API Docs (Swagger):** `http://localhost:8000/docs`

### 3. Seeding the Database & Vector Store
Once the containers are running, you must seed the historical negotiations, fake users, and live market intelligence into PostgreSQL and ChromaDB:
```bash
docker compose exec backend python scripts/seed_database.py
```

---

## 🧪 CI/CD & Testing
AgriNegotiator utilizes **GitHub Actions** for continuous integration. On every push to `main`, the platform spins up the backend and executes the rigorous end-to-end simulation test located in `scripts/full_e2e_test.py`. This verifies all 7 agents, LangGraph nodes, database dependencies, and AI mathematical bounding rules.
