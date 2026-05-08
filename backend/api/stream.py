"""
api/stream.py — Server-Sent Events (SSE) endpoint.

GET /api/research?topic=...&depth=standard&style=summary

Streams agent step events as:
  data: {"type": "step", "step": {...}}
  data: {"type": "done", "report": "...markdown..."}
  data: {"type": "error", "message": "..."}

Why SSE instead of WebSockets?
  SSE is unidirectional (server → client), which is exactly what we need.
  It's simpler, HTTP-native, auto-reconnects, and works through proxies.
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from agent.graph import research_graph

router = APIRouter()

DEPTH_MAP = {"quick": 1, "standard": 2, "deep": 3}


@router.get("/research")
async def research_stream(
    topic: str = Query(..., description="Research topic"),
    depth: str = Query("standard", description="quick | standard | deep"),
    style: str = Query("summary", description="analytical | summary | technical"),
):
    """
    Streams agent steps and final report via Server-Sent Events.
    Connect from the frontend using the EventSource API.
    """
    return StreamingResponse(
        _event_generator(topic, depth, style),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",    # Disable Nginx buffering
        },
    )


async def _event_generator(
    topic: str, depth: str, style: str
) -> AsyncGenerator[str, None]:
    """Run the LangGraph agent and yield SSE events for each step."""

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    initial_state = {
        "topic": topic,
        "style": style,
        "max_iterations": DEPTH_MAP.get(depth, 2),
        "iteration": 1,
        "sub_questions": [],
        "search_results": [],
        "extracted_facts": [],
        "reflection": None,
        "is_complete": False,
        "report": "",
        "steps": [],
    }

    try:
        # LangGraph streams state updates after each node
        async for state_chunk in research_graph.astream(initial_state):
            for node_name, node_output in state_chunk.items():
                new_steps = node_output.get("steps", [])
                for step in new_steps:
                    yield _sse({"type": "step", "node": node_name, "step": step})
                    await asyncio.sleep(0)   # yield to event loop

                # If this is the write node, stream the report
                if "report" in node_output and node_output["report"]:
                    yield _sse({
                        "type": "done",
                        "report": node_output["report"],
                    })

    except Exception as e:
        yield _sse({"type": "error", "message": str(e)})
