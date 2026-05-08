// src/App.jsx — Root component
import { useState } from "react";
import ResearchInput from "./components/ResearchInput";
import AgentThinkingPanel from "./components/AgentThinkingPanel";
import ReportViewer from "./components/ReportViewer";
import MemoryPanel from "./components/MemoryPanel";
import Header from "./components/Header";
import { useResearch } from "./hooks/useResearch";

export default function App() {
  const [topic, setTopic] = useState("");
  const [depth, setDepth] = useState("standard");
  const [style, setStyle] = useState("summary");

  const {
    steps,
    report,
    isRunning,
    error,
    sessionMemory,
    startResearch,
    reset,
  } = useResearch();

  const handleStart = () => {
    if (!topic.trim() || isRunning) return;
    startResearch(topic, depth, style);
  };

  return (
    <div className="app">
      <Header />

      <div className="layout">
        {/* ── Left: Input + Report ── */}
        <div className="main-panel">
          <ResearchInput
            topic={topic}
            setTopic={setTopic}
            depth={depth}
            setDepth={setDepth}
            style={style}
            setStyle={setStyle}
            isRunning={isRunning}
            onStart={handleStart}
            onReset={reset}
          />

          <ReportViewer
            report={report}
            topic={topic}
            isRunning={isRunning}
            error={error}
          />
        </div>

        {/* ── Right: Steps + Memory ── */}
        <div className="side-panel">
          <AgentThinkingPanel steps={steps} isRunning={isRunning} />
          <MemoryPanel
            topics={sessionMemory}
            onSelect={(t) => setTopic(t)}
          />
        </div>
      </div>
    </div>
  );
}
