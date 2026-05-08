"""
agent/memory.py — Vector memory using ChromaDB.

Stores past research sessions as embeddings so the agent can:
- Recall related past research before starting new queries
- Skip redundant searches on related topics
- Build cumulative knowledge over time
"""

import hashlib
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions


COLLECTION_NAME = "research_sessions"
EMBED_MODEL = "all-MiniLM-L6-v2"   # local, fast, no API key needed


class MemoryStore:
    """
    Thin wrapper around ChromaDB for research session memory.

    Usage:
        mem = MemoryStore()
        mem.save("quantum computing", report_text)
        context = mem.query("quantum entanglement")  # returns related past research
    """

    def __init__(self, persist_dir: str = "./chroma_db"):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        self._col = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def save(self, topic: str, report: str) -> None:
        """
        Chunk the report and store each chunk with metadata.
        Uses topic+timestamp as a unique document ID prefix.
        """
        chunks = self._chunk(report)
        doc_id = self._make_id(topic)

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"topic": topic, "timestamp": datetime.utcnow().isoformat(), "chunk": i}
            for i in range(len(chunks))
        ]

        self._col.upsert(documents=chunks, ids=ids, metadatas=metadatas)

    def query(self, topic: str, n_results: int = 3) -> Optional[str]:
        """
        Find past research related to the given topic.
        Returns a formatted string of relevant snippets, or None.
        """
        total = self._col.count()
        if total == 0:
            return None

        results = self._col.query(
            query_texts=[topic],
            n_results=min(n_results, total),
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Only keep highly relevant hits (cosine distance < 0.45)
        relevant = [
            (doc, meta)
            for doc, meta, dist in zip(docs, metas, distances)
            if dist < 0.45
        ]

        if not relevant:
            return None

        parts = []
        for doc, meta in relevant:
            parts.append(f"[Past topic: {meta['topic']} | {meta['timestamp'][:10]}]\n{doc}")

        return "\n\n---\n\n".join(parts)

    def list_topics(self) -> list[str]:
        """Return all unique topics stored in memory."""
        if self._col.count() == 0:
            return []
        results = self._col.get(include=["metadatas"])
        seen = set()
        topics = []
        for meta in results.get("metadatas", []):
            t = meta.get("topic", "")
            if t and t not in seen:
                seen.add(t)
                topics.append(t)
        return topics

    def clear(self) -> None:
        """Wipe all stored memory."""
        self._client.delete_collection(COLLECTION_NAME)
        self._col = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embed_fn,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _chunk(text: str, size: int = 400, overlap: int = 80) -> list[str]:
        """Split text into overlapping word-level chunks."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start += size - overlap
        return chunks or [text]

    @staticmethod
    def _make_id(topic: str) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        h = hashlib.md5(topic.encode()).hexdigest()[:8]
        return f"{h}_{ts}"
