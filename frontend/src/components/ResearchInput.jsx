/**
 * components/ResearchInput.jsx
 *
 * Topic input bar with depth and style selectors.
 * Submits on Enter or button click.
 */
export default function ResearchInput({
  topic, setTopic, depth, setDepth, style, setStyle,
  isRunning, onStart, onReset,
}) {
  return (
    <div className="input-area">
      <label className="input-label">Research topic</label>

      <div className="topic-row">
        <input
          className="topic-input"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onStart()}
          placeholder="e.g. The impact of AI on software engineering..."
          disabled={isRunning}
        />

        {isRunning ? (
          <button className="run-btn stop" onClick={onReset}>
            &#9632; Stop
          </button>
        ) : (
          <button className="run-btn" onClick={onStart} disabled={!topic.trim()}>
            &#9654; Research
          </button>
        )}
      </div>

      <div className="options-row">
        <span className="opt-label">Depth:</span>
        <select
          className="opt-select"
          value={depth}
          onChange={(e) => setDepth(e.target.value)}
          disabled={isRunning}
        >
          <option value="quick">Quick (1 pass)</option>
          <option value="standard">Standard (2 passes)</option>
          <option value="deep">Deep (3 passes)</option>
        </select>

        <span className="opt-label" style={{ marginLeft: 12 }}>Style:</span>
        <select
          className="opt-select"
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          disabled={isRunning}
        >
          <option value="summary">Summary</option>
          <option value="analytical">Analytical</option>
          <option value="technical">Technical</option>
        </select>
      </div>
    </div>
  );
}
