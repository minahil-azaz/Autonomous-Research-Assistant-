/**
 * components/MemoryPanel.jsx
 *
 * Shows past research topics from the current session.
 * Clicking a topic pre-fills the input — simulating persistent memory.
 *
 * In the full system, this would also show results from ChromaDB
 * (cross-session vector memory), displayed after querying GET /api/memory.
 */

export default function MemoryPanel({ topics, onSelect }) {
  if (!topics || topics.length === 0) return null;

  return (
    <div className="memory-panel">
      <div className="memory-label">Session memory</div>
      <div className="memory-list">
        {topics.map((t, i) => (
          <button
            key={i}
            className="memory-item"
            onClick={() => onSelect(t)}
            title={t}
          >
            <span className="memory-dot" />
            <span className="memory-text">
              {t.length > 36 ? t.slice(0, 36) + "…" : t}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
