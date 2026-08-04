# Technical Stack & Planning Decisions

## 1. AI Orchestration Framework: LangGraph
- **Selected**: **LangGraph** (over CrewAI)
- **Rationale**:
  - LangGraph provides granular control over multi-agent workflows using state machines and cyclic graphs.
  - Supports explicitly defined state schemas (`TypedDict`) passed between specialized agent nodes (e.g. Code Reviewer -> Bug Finder -> Security Agent -> Summary Agent).
  - Handles branching, conditional routing, and fallback logic cleanly for long context analysis.

## 2. LLM Provider: Google Gemini
- **Selected**: **Google Gemini** (`gemini-2.5-flash` / `gemini-2.5-pro`)
- **Rationale**:
  - Large context window capability enables loading entire source code files and repository chunks without loss of context.
  - Exceptionally fast inference speed and cost-effective execution for multi-step agent reasoning.
  - Native JSON mode guarantees structured output matching system Pydantic models.

## 3. Vector Database: ChromaDB
- **Selected**: **ChromaDB**
- **Rationale**:
  - Embedded Python native vector database with zero setup overhead for local development.
  - Supports persistence on disk (`./vector_db`) and scale to client/server mode if needed.
  - Built-in integration with LangChain / Google Gemini text embedding models for semantic retrieval.

## 4. Full Architecture Summary
- **Frontend**: Flutter Web & Mobile Client (Dart, Material 3, Dark Theme).
- **Backend API**: FastAPI (Async Python 3.11, Pydantic v2, CORS, OpenAPI documentation).
- **Database**: PostgreSQL 15 (SQLAlchemy ORM + Alembic migrations).
- **Storage**: Local filesystem storage for temp repository extractions (`./uploads`).
