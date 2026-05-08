"""
agent/graph.py — LangGraph agentic research loop.

Nodes:
  plan       → Break topic into sub-questions
  search     → Tavily web search per sub-question
  read       → Extract key info from search results
  reflect    → Decide: enough info? or search again?
  write      → Synthesize final Markdown report

Edges:
  plan → search → read → reflect → write   (happy path)
                          ↑_________↓       (if not enough: loop back)
"""

import json
from typing import TypedDict, Annotated, List, Optional
import operator

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from agent.memory import MemoryStore

# ── State schema ──────────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    topic: str
    style: str                              # analytical | summary | technical
    max_iterations: int
    iteration: int
    sub_questions: List[str]
    search_results: Annotated[List[dict], operator.add]
    extracted_facts: Annotated[List[str], operator.add]
    reflection: Optional[str]
    is_complete: bool
    report: str
    steps: Annotated[List[dict], operator.add]   # streamed to frontend


# ── LLM & tools ───────────────────────────────────────────────────────────────

def _llm():
    return ChatOpenAI(model="gpt-4o", temperature=0.3, streaming=True)

def _search_tool():
    return TavilySearchResults(max_results=4)


# ── Node: plan ────────────────────────────────────────────────────────────────

def plan_node(state: ResearchState) -> dict:
    llm = _llm()
    prompt = f"""Break the following research topic into 3-4 focused sub-questions.
Return ONLY a JSON array of strings. No preamble.

Topic: {state['topic']}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        questions = json.loads(response.content)
    except Exception:
        # Fallback: split by newline
        questions = [state['topic']]

    return {
        "sub_questions": questions,
        "steps": [{"type": "think", "label": "Planning", "text": f"Broke topic into {len(questions)} sub-questions"}],
    }


# ── Node: search ──────────────────────────────────────────────────────────────

def search_node(state: ResearchState) -> dict:
    tool = _search_tool()
    results = []
    steps = []

    for q in state["sub_questions"]:
        raw = tool.invoke(q)
        results.append({"query": q, "results": raw})
        steps.append({"type": "search", "label": "Searching", "text": q})

    return {"search_results": results, "steps": steps}


# ── Node: read ────────────────────────────────────────────────────────────────

def read_node(state: ResearchState) -> dict:
    llm = _llm()
    facts = []
    steps = []

    for item in state["search_results"]:
        sources = "\n\n".join(
            f"Source: {r.get('url','')}\n{r.get('content','')}"
            for r in item["results"]
        )
        prompt = f"""Extract the most important facts and insights from these sources for the query:
"{item['query']}"

Sources:
{sources}

Return a concise bullet list of key facts. Be precise."""

        response = llm.invoke([HumanMessage(content=prompt)])
        facts.append(response.content)
        steps.append({"type": "read", "label": "Extracting", "text": f"Processed results for: {item['query'][:60]}"})

    return {"extracted_facts": facts, "steps": steps}


# ── Node: reflect ─────────────────────────────────────────────────────────────

def reflect_node(state: ResearchState) -> dict:
    llm = _llm()
    all_facts = "\n\n".join(state["extracted_facts"])

    prompt = f"""You are researching: "{state['topic']}"

Facts gathered so far:
{all_facts}

Iteration {state['iteration']} of max {state['max_iterations']}.

Respond in JSON:
{{
  "is_complete": true/false,
  "missing": "what's still missing (if not complete)",
  "follow_up_questions": ["q1", "q2"]  // only if not complete
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content)
    except Exception:
        data = {"is_complete": True, "missing": "", "follow_up_questions": []}

    is_complete = data.get("is_complete", True) or state["iteration"] >= state["max_iterations"]
    follow_ups = data.get("follow_up_questions", [])

    steps = [{"type": "reflect", "label": "Reflecting", "text": data.get("missing", "Information looks sufficient.")}]

    update: dict = {
        "reflection": data.get("missing"),
        "is_complete": is_complete,
        "iteration": state["iteration"] + 1,
        "steps": steps,
    }

    if not is_complete and follow_ups:
        update["sub_questions"] = follow_ups

    return update


# ── Node: write ───────────────────────────────────────────────────────────────

def write_node(state: ResearchState) -> dict:
    llm = _llm()
    memory = MemoryStore()
    past = memory.query(state["topic"])

    past_ctx = ""
    if past:
        past_ctx = f"\n\nRelated past research (use for context):\n{past}"

    all_facts = "\n\n".join(state["extracted_facts"])

    style_instructions = {
        "analytical": "Focus on analysis, causality, and evaluation. Use structured arguments.",
        "summary":    "Write an accessible overview. Explain concepts clearly. Use examples.",
        "technical":  "Focus on technical details, specifications, and implementation. Use precise language.",
    }.get(state["style"], "Write a comprehensive, balanced report.")

    prompt = f"""Write a comprehensive research report on: "{state['topic']}"

Style: {style_instructions}{past_ctx}

Research findings:
{all_facts}

Format:
# [Title]

## Executive Summary
[2-3 sentence overview]

## [Section 1]
## [Section 2]
## [Section 3]
...

## Key Takeaways
- [bullet 1]
- [bullet 2]
- [bullet 3]

## Sources & Further Reading
[mention key sources]

Write in clean Markdown. Be thorough (600-900 words)."""

    response = llm.invoke([HumanMessage(content=prompt)])
    report = response.content

    # Save to vector memory
    memory.save(state["topic"], report)

    return {
        "report": report,
        "steps": [{"type": "write", "label": "Writing", "text": "Synthesizing final report..."}],
    }


# ── Routing ───────────────────────────────────────────────────────────────────

def should_continue(state: ResearchState) -> str:
    return "write" if state["is_complete"] else "search"


# ── Build graph ───────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(ResearchState)

    g.add_node("plan",    plan_node)
    g.add_node("search",  search_node)
    g.add_node("read",    read_node)
    g.add_node("reflect", reflect_node)
    g.add_node("write",   write_node)

    g.set_entry_point("plan")
    g.add_edge("plan",    "search")
    g.add_edge("search",  "read")
    g.add_edge("read",    "reflect")
    g.add_conditional_edges("reflect", should_continue, {"write": "write", "search": "search"})
    g.add_edge("write", END)

    return g.compile()


research_graph = build_graph()
