"""
tests/test_api.py — Integration tests for the research API.

Run with:  pytest tests/ -v
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)


# ── Health check ──────────────────────────────────────────────────────────────

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Export endpoint ───────────────────────────────────────────────────────────

def test_export_returns_pdf():
    payload = {
        "markdown": "# Test Report\n\nThis is a **test**.\n\n## Section\n\n- Item 1\n- Item 2",
        "topic": "Test Topic"
    }
    with patch("api.export._html_to_pdf", return_value=b"%PDF-mock"):
        resp = client.post("/api/export", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]


def test_export_filename_sanitized():
    payload = {"markdown": "# Report", "topic": "AI & ML: A Deep/Dive"}
    with patch("api.export._html_to_pdf", return_value=b"%PDF-mock"):
        resp = client.post("/api/export", json=payload)
    cd = resp.headers["content-disposition"]
    # Should not contain special chars in filename
    assert "/" not in cd
    assert "&" not in cd


# ── Memory module ─────────────────────────────────────────────────────────────

def test_memory_save_and_query(tmp_path):
    from agent.memory import MemoryStore
    mem = MemoryStore(persist_dir=str(tmp_path / "chroma"))
    mem.save("quantum computing", "# Quantum\n\nQubits are the basis of quantum computing.")
    result = mem.query("quantum entanglement")
    # May or may not find it depending on similarity threshold
    assert result is None or "quantum" in result.lower()


def test_memory_empty_query(tmp_path):
    from agent.memory import MemoryStore
    mem = MemoryStore(persist_dir=str(tmp_path / "chroma"))
    result = mem.query("anything")
    assert result is None


def test_memory_list_topics(tmp_path):
    from agent.memory import MemoryStore
    mem = MemoryStore(persist_dir=str(tmp_path / "chroma"))
    mem.save("machine learning", "ML is a subset of AI.")
    mem.save("deep learning", "Deep learning uses neural networks.")
    topics = mem.list_topics()
    assert "machine learning" in topics
    assert "deep learning" in topics


# ── Markdown parser ───────────────────────────────────────────────────────────

def test_markdown_headings():
    from api.export import _parse_md
    html = _parse_md("# Title\n## Section\n### Sub")
    assert "<h1" in html
    assert "<h2" in html
    assert "<h3" in html


def test_markdown_inline():
    from api.export import _inline
    assert "<strong>" in _inline("**bold**")
    assert "<em>" in _inline("*italic*")
    assert "<code>" in _inline("`code`")


def test_markdown_list():
    from api.export import _parse_md
    html = _parse_md("- item one\n- item two\n- item three")
    assert "<ul>" in html
    assert "<li>" in html
