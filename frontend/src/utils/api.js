/**
 * utils/api.js — Thin API client for the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * POST /api/export — Convert markdown to PDF and return a Blob.
 *
 * @param {string} markdown  Report markdown text
 * @param {string} topic     Topic (used for filename)
 * @returns {Promise<Blob>}  PDF blob
 */
export async function exportPdf(markdown, topic) {
  const resp = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ markdown, topic }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Export failed (${resp.status}): ${text}`);
  }

  return resp.blob();
}

/**
 * GET /api/memory — Retrieve past session topics from ChromaDB.
 * (Optional: call this on app load to pre-populate the memory panel.)
 *
 * @returns {Promise<string[]>}
 */
export async function fetchMemoryTopics() {
  try {
    const resp = await fetch(`${API_BASE}/memory`);
    if (!resp.ok) return [];
    const data = await resp.json();
    return data.topics || [];
  } catch {
    return [];
  }
}
