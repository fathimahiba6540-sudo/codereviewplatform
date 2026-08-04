# AI-Powered Multi-Agent Code Review Platform

A full-stack AI-powered code review platform that accepts uploaded `.zip` archives or GitHub repository URLs, executes a multi-agent AI analysis pipeline powered by **LangGraph** and **Google Gemini**, and provides a dashboard-style report with bug detection, security scanning, quality scoring, documentation generation, and unit test generation.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │  Flutter Web/Mobile App   │
                          └─────────────┬─────────────┘
                                        │ REST API (JWT)
                                        ▼
                          ┌───────────────────────────┐
                          │  FastAPI Backend Server   │
                          └──────┬────────────┬───────┘
                                 │            │
             ┌───────────────────┘            └────────────────────┐
             ▼                                                     ▼
┌──────────────────────────┐                             ┌───────────────────┐
│ PostgreSQL Database      │                             │ Chroma Vector DB  │
└──────────────────────────┘                             └───────────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ LangGraph Orchestrator │
                     └───────────┬────────────┘
                                 │ Prompts
                                 ▼
                     ┌────────────────────────┐
                     │ Google Gemini LLM API  │
                     └────────────────────────┘
```

---

## Directory Structure

```
codereviewplatform/
├── backend/                  # FastAPI Backend Service
│   ├── app/
│   │   ├── agents/           # Multi-agent AI review pipeline (LangGraph)
│   │   ├── core/             # Application config and settings
│   │   ├── database/         # SQLAlchemy engine and session
│   │   ├── models/           # ORM and Pydantic schemas
│   │   ├── routers/          # REST API endpoints (Auth, Projects, Reviews)
│   │   ├── services/         # Code parser, ingestion, vector store services
│   │   ├── utils/            # Helper functions
│   │   └── main.py           # FastAPI entrypoint
│   └── requirements.txt
├── frontend/                 # Flutter Application
│   ├── lib/
│   │   ├── screens/          # App UI screens (Login, Upload, Dashboard, Report)
│   │   ├── services/         # API HTTP client services
│   │   ├── widgets/          # Reusable UI widgets
│   │   └── main.dart         # Flutter entrypoint
│   ├── pubspec.yaml
│   └── analysis_options.yaml
├── docker/                   # Dockerfiles for local dev and production
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docs/                     # Technical specifications and design docs
│   ├── architecture_diagram.md
│   ├── coding_standards_and_linting.md
│   ├── data_contracts.md
│   ├── scoring_model_and_report_schema.md
│   ├── technical_stack_and_planning.md
│   └── workflow_and_branch_strategy.md
├── uploads/                  # Temporary repository upload storage
├── vector_db/                # ChromaDB persistent vector storage
├── docker-compose.yml        # Docker Compose configuration
├── .env.example              # Environment variables template
└── task.md                   # Project Roadmap & Task Breakdown
```

---

## Quick Start with Docker

### Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose installed.

### Run Service Stack

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure your `GEMINI_API_KEY` in `.env`.
3. Launch the container stack:
   ```bash
   docker-compose up --build
   ```
4. Access services:
   - **FastAPI API & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Flutter Web App**: [http://localhost:8080](http://localhost:8080)
   - **PostgreSQL DB**: `localhost:5432`

---

## Local Development Setup

### Backend (FastAPI)

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Start FastAPI server:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

### Frontend (Flutter)

1. Get pub packages:
   ```bash
   cd frontend
   flutter pub get
   ```
2. Run Flutter app:
   ```bash
   flutter run -d chrome
   ```

---

## Technical Stack & Choices

- **AI Pipeline Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
- **LLM Provider**: Google Gemini (`gemini-2.5-flash` / `gemini-2.5-pro`)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) + SQLAlchemy + Pydantic v2
- **Database**: PostgreSQL 15
- **Frontend Framework**: [Flutter](https://flutter.dev/) (Dart)

---

## License
MIT License.
