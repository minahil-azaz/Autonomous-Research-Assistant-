# Autonomous Research Assistant

> **Agentic AI system** that autonomously searches the web, reflects on gaps, iterates, and synthesises a structured report — with every reasoning step streamed live to the UI.

---

## Table of Contents

1. [What it does](#what-it-does)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Environment Variables](#environment-variables)
7. [API Reference](#api-reference)
8. [How the Agent Loop Works](#how-the-agent-loop-works)
9. [Key Design Decisions](#key-design-decisions)
10. [Running Tests](#running-tests)
11. [Deployment](#deployment)
12. [Interview Talking Points](#interview-talking-points)

---

## What it does

The assistant takes a research topic and autonomously:

1. **Plans** — breaks the topic into 3–4 focused sub-questions
2. **Searches** — queries the web via Tavily for each sub-question
3. **Reads** — extracts key facts from search results using GPT-4o
4. **Reflects** — decides whether the gathered information is sufficient
5. **Iterates** — if not enough, generates follow-up questions and searches again (up to N passes)
6. **Writes** — synthesises everything into a structured Markdown report
7. **Exports** — allows the user to download the report as `.md` or `.pdf`

Every step is streamed live to the frontend via **Server-Sent Events (SSE)**, so users watch the agent "think" in real time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (React)                       │
│                                                             │
│   ResearchInput ─────────────────────────────────────────   │
│   AgentThinkingPanel ← SSE stream (step events)            │
│   ReportViewer       ← SSE stream (done event)             │
│   MemoryPanel        ← session memory                      │
└────────────────────────────┬────────────────────────────────┘
                             │  HTTP / SSE
┌────────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend (Python)                   │
│                                                             │
│   GET  /api/research  → SSE stream                         │
│   POST /api/export    → PDF bytes                          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              LangGraph Agent Loop                    │  │
│   │                                                     │  │
│   │  [plan] → [search] → [read] → [reflect] → [write]  │  │
│   │                          ↑___________↓              │  │
│   │                    (if not complete)                │  │
│   └──────────┬────────────────────────────┬────────────┘  │
│              │                            │                │
│        Tavily API                    ChromaDB              │
│       (web search)               (vector memory)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| **Agent Brain** | LangGraph | Stateful graph with conditional edges — models the research loop cleanly |
| **LLM** | OpenAI GPT-4o | Reasoning, synthesis, reflection |
| **Web Search** | Tavily API | Built for AI agents — structured, clean results; no scraping |
| **Vector Memory** | ChromaDB + Sentence Transformers | Local vector DB; no managed infra required |
| **Backend** | FastAPI + Uvicorn | Async, fast, streaming-friendly |
| **SSE Streaming** | FastAPI `StreamingResponse` | Simple, HTTP-native, auto-reconnects |
| **Frontend** | React + Vite | Lightweight; no heavy framework overhead |
| **PDF Export** | WeasyPrint (+ ReportLab fallback) | HTML-to-PDF with CSS styling |

---

## Project Structure

```
research-agent/
│
├── backend/
│   ├── main.py                 ← FastAPI app + CORS + router mounting
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py            ← LangGraph nodes & edges (the agent loop)
│   │   ├── memory.py           ← ChromaDB read/write
│   │   └── tools.py            ← Tavily search + page fetcher
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── stream.py           ← GET /api/research → SSE
│   │   └── export.py           ← POST /api/export → PDF
│   │
│   └── tests/
│       └── test_api.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   │
│   └── src/
│       ├── main.jsx            ← React entry point
│       ├── App.jsx             ← Root component + layout
│       ├── index.css           ← Full stylesheet (light + dark mode)
│       │
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── ResearchInput.jsx        ← Topic input + controls
│       │   ├── AgentThinkingPanel.jsx   ← Live step feed
│       │   ├── ReportViewer.jsx         ← Rendered report + export buttons
│       │   └── MemoryPanel.jsx          ← Past topics sidebar
│       │
│       ├── hooks/
│       │   └── useResearch.js           ← SSE connection + state management
│       │
│       └── utils/
│           ├── markdown.js              ← MD → HTML renderer
│           ├── api.js                   ← API client (export, memory)
│           └── text.js                  ← countWords, slugify, truncate
│
├── docs/
│   └── ARCHITECTURE.md
│
└── README.md                   ← This file
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [OpenAI API key](https://platform.openai.com)
- [Tavily API key](https://tavily.com) (free tier available)

---

### 1 — Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# → Edit .env and add your OPENAI_API_KEY and TAVILY_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs for the interactive API docs.

---

### 2 — Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional — Vite proxy handles this in dev)
cp .env.example .env

# Start the dev server
npm run dev
```

Visit http://localhost:3000

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | GPT-4o for reasoning and synthesis |
| `TAVILY_API_KEY` | ✅ | Web search |
| `CHROMA_DB_DIR` | ❌ | ChromaDB persist directory (default: `./chroma_db`) |
| `APP_ENV` | ❌ | `development` or `production` |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ❌ | Backend URL (default: `http://localhost:8000/api`) |

---

## API Reference

### `GET /api/research`

Stream agent steps and the final report via Server-Sent Events.

**Query params:**

| Param | Type | Default | Values |
|---|---|---|---|
| `topic` | string | — | Any research topic |
| `depth` | string | `standard` | `quick` \| `standard` \| `deep` |
| `style` | string | `summary` | `summary` \| `analytical` \| `technical` |

**SSE event format:**

```json
// Step event (emitted for each agent action)
{ "type": "step", "node": "search", "step": { "type": "search", "label": "Searching", "text": "..." } }

// Done event (final report)
{ "type": "done", "report": "# Title\n\n..." }

// Error event
{ "type": "error", "message": "..." }
```

**Connect from JavaScript:**

```js
const es = new EventSource(`/api/research?topic=quantum+computing&depth=standard`);
es.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === "step")  renderStep(data.step);
  if (data.type === "done")  renderReport(data.report);
  if (data.type === "error") showError(data.message);
};
```

---

### `POST /api/export`

Convert a Markdown report to a downloadable PDF.

**Request body:**

```json
{
  "markdown": "# Report\n\nContent...",
  "topic": "Quantum Computing"
}
```

**Response:** `application/pdf` binary with `Content-Disposition: attachment`.

---

### `GET /health`

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## How the Agent Loop Works

The agent is implemented as a **LangGraph StateGraph** — a directed graph where each node is a Python function that reads from and writes to a shared `ResearchState` dict.

```
plan → search → read → reflect ──(complete?)──→ write → END
                          ↑                         |
                          └──── (not complete) ─────┘
                              generates follow-ups
```

### State schema

```python
class ResearchState(TypedDict):
    topic: str
    style: str                  # report style
    max_iterations: int         # depth control
    iteration: int              # current pass
    sub_questions: List[str]    # questions to search
    search_results: List[dict]  # raw Tavily results
    extracted_facts: List[str]  # LLM-summarised facts
    reflection: Optional[str]   # what's missing
    is_complete: bool           # routing decision
    report: str                 # final markdown
    steps: List[dict]           # streamed to frontend
```

### The `reflect` node (the agentic decision)

The `reflect` node is where the agent decides whether to stop or search again:

```python
def reflect_node(state):
    # Ask GPT-4o: "Is this enough to write a complete report?"
    # Returns JSON: { is_complete, missing, follow_up_questions }
    # If not complete AND iterations remain → update sub_questions and loop back
```

This is the **ReAct pattern** (Reason + Act) — the core of modern agent design.

### Memory (ChromaDB)

Before writing, the `write` node checks ChromaDB for related past research:

```python
past = memory.query(state["topic"])  # cosine similarity search
# If related sessions found → include as context in the synthesis prompt
```

After writing, the report is chunked and stored for future sessions.

---

## Key Design Decisions

### Why SSE instead of WebSockets?

SSE is unidirectional (server → client), which is exactly what this use case needs. It's HTTP-native, simpler to implement, auto-reconnects, and works through load balancers and proxies without special configuration.

### Why LangGraph instead of raw LangChain?

LangGraph makes the loop explicit as a graph with named nodes and conditional edges. This makes it easy to:
- Add new nodes (e.g., a `fact_check` node) without refactoring
- Visualise the agent's structure
- Control iteration with typed state

### Why Tavily instead of Google/SerpAPI?

Tavily is purpose-built for AI agents — it returns clean, de-duplicated, structured results without ads, navigation menus, or boilerplate. It also provides its own AI summary of results (`include_answer=True`).

### Why ChromaDB for memory?

ChromaDB runs in-process with no external service required. The `PersistentClient` stores embeddings to disk, so memory survives server restarts. For production, swap in Pinecone or Weaviate.

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Tests cover:
- Health endpoint
- PDF export endpoint (mocked)
- Filename sanitisation
- Memory: save, query, empty, list
- Markdown parser: headings, inline formatting, lists

---

## Deployment

### Backend (production)

```bash
# Install without dev deps
pip install -r requirements.txt

# Run with Gunicorn + Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Update `CORS` origins in `main.py` to your frontend domain.

### Frontend (production)

```bash
cd frontend
npm run build        # outputs to dist/
# Deploy dist/ to Vercel, Netlify, or any static host
```

Set `VITE_API_URL` to your backend's production URL.

### Docker (optional)

```bash
# Backend
docker build -t research-agent-backend ./backend
docker run -p 8000:8000 --env-file backend/.env research-agent-backend

# Frontend
docker build -t research-agent-frontend ./frontend
docker run -p 3000:80 research-agent-frontend
```

---

## Interview Talking Points

> *"I built an autonomous research agent using LangGraph where the agent decides how many search iterations it needs via a self-reflection node. I streamed intermediate reasoning steps to the frontend in real time using Server-Sent Events — so users don't just wait; they watch the agent think. I also added cross-session vector memory with ChromaDB so the agent recalls related past research, which significantly reduces redundant API calls on similar topics."*

That answer covers: **LLMs, agents (ReAct pattern), streaming (SSE), vector databases, API design, and UX thinking** — the full stack of what interviewers want in 2026.

---

## Author

**Minahil Azaz** — [github.com/minahil-azaz](https://github.com/minahil-azaz) · [linkedin.com/in/minahil-azaz-397756241](https://linkedin.com/in/minahil-azaz-397756241)
# Autonomous-Research-Assistant-
