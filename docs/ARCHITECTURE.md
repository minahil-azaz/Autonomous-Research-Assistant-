# Architecture Deep Dive

## Data Flow

```
User types topic → React (useResearch hook)
  → opens EventSource → GET /api/research?topic=...
  → FastAPI (stream.py)
  → initialises ResearchState
  → research_graph.astream(state)

LangGraph emits state patches after each node:
  plan    → { sub_questions, steps }
  search  → { search_results, steps }
  read    → { extracted_facts, steps }
  reflect → { is_complete, iteration, steps }
           conditional edge:
             is_complete=True  → write
             is_complete=False → search (loop)
  write   → { report, steps }
           saves to ChromaDB

Each state patch → FastAPI yields SSE "step" events
Final write patch → FastAPI yields SSE "done" event

React receives events:
  "step" → appends to steps array → AgentThinkingPanel rerenders
  "done" → sets report string → ReportViewer rerenders
```

## File responsibilities

| File | Responsibility |
|---|---|
| `agent/graph.py` | Defines the 5 LangGraph nodes and the conditional routing edge. This is the agent's "brain". |
| `agent/memory.py` | ChromaDB wrapper. Chunks reports into overlapping segments, stores as embeddings, queries by cosine similarity. |
| `agent/tools.py` | Tavily search tool config and a custom `fetch_page` tool for deep-reading specific URLs. |
| `api/stream.py` | Converts LangGraph's async state stream into SSE events. Handles depth-to-iterations mapping. |
| `api/export.py` | Minimal Markdown parser + WeasyPrint HTML-to-PDF pipeline. ReportLab fallback if WeasyPrint unavailable. |
| `hooks/useResearch.js` | All SSE state management. Opens/closes EventSource, accumulates steps, sets report, updates session memory. |
| `utils/markdown.js` | Hand-rolled Markdown → HTML (no external deps). Covers headings, lists, bold, italic, code, links, blockquotes. |

## Scaling considerations

- **Concurrent requests**: LangGraph runs async; FastAPI handles concurrent SSE streams without threading.
- **Memory**: ChromaDB is in-process. For multi-instance deployments, replace with Pinecone or Weaviate.
- **LLM costs**: Each research session uses ~5–15 GPT-4o calls. Cache embeddings + use `gpt-4o-mini` for the plan/reflect nodes to reduce cost.
- **Search quota**: Tavily free tier = 1000 searches/month. Cache Tavily results in Redis for repeated queries.
