"""
agent/tools.py — Custom tools used by the research agent.

Tools:
  tavily_search   — AI-optimised web search via Tavily API
  fetch_page      — Read and clean a specific URL's content
"""

import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool


# ── Tavily search wrapper ────────────────────────────────────────────────────

def get_search_tool(max_results: int = 5) -> TavilySearchResults:
    """
    Returns a configured Tavily search tool.
    Tavily is purpose-built for AI agents — returns clean, structured results
    without ads or boilerplate, unlike raw Google scraping.

    Requires TAVILY_API_KEY in environment.
    """
    return TavilySearchResults(
        max_results=max_results,
        include_answer=True,        # Tavily's own AI summary of results
        include_raw_content=False,  # We fetch pages ourselves when needed
        include_images=False,
    )


# ── Page fetch tool ──────────────────────────────────────────────────────────

@tool
def fetch_page(url: str, max_chars: int = 4000) -> str:
    """
    Fetches a URL and returns clean readable text (strips HTML/JS/CSS).
    Used when search snippets aren't enough and the agent wants to deep-read
    a specific source page.

    Args:
        url:       Full URL to fetch.
        max_chars: Truncation limit to keep within LLM context.

    Returns:
        Cleaned page text, or an error message.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (ResearchAgent/1.0)"}
        resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        text = _clean_text(text)

        return text[:max_chars] + ("…[truncated]" if len(text) > max_chars else "")

    except httpx.TimeoutException:
        return f"[Error] Request timed out for: {url}"
    except httpx.HTTPStatusError as e:
        return f"[Error] HTTP {e.response.status_code} for: {url}"
    except Exception as e:
        return f"[Error] Could not fetch page: {e}"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Collapse whitespace and remove non-printable characters."""
    text = re.sub(r"[ \t]+", " ", text)          # collapse horizontal space
    text = re.sub(r"\n{3,}", "\n\n", text)        # max 2 blank lines
    text = re.sub(r"[^\x20-\x7E\n]", "", text)   # ASCII printable only
    return text.strip()


# ── Tool registry (used by LangGraph) ────────────────────────────────────────

AGENT_TOOLS = [get_search_tool(), fetch_page]
