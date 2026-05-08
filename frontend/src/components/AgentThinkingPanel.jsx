/**
 * components/AgentThinkingPanel.jsx
 *
 * Displays live agent steps streamed from the backend via SSE.
 * Each step has a type (search | think | read | reflect | write | done)
 * which determines its color and icon.
 *
 * The #1 interview talking point:
 *  "I streamed intermediate agent states to the frontend via SSE so users
 *   can see the reasoning in real time — not just wait for a final answer."
 */

import { useEffect, useRef } from "react";

const STEP_CONFIG = {
  search:  { icon: "⊕", label: "Search",  cls: "step-search"  },
  think:   { icon: "◆", label: "Planning", cls: "step-think"   },
  read:    { icon: "■", label: "Reading",  cls: "step-read"    },
  reflect: { icon: "↻", label: "Reflect",  cls: "step-reflect" },
  write:   { icon: "✎", label: "Writing",  cls: "step-write"   },
  done:    { icon: "✓", label: "Done",     cls: "step-done"    },
};

function StepItem({ step }) {
  const cfg = STEP_CONFIG[step.type] || STEP_CONFIG.think;
  return (
    <div className={`step-item ${cfg.cls}`}>
      <div className="step-top">
        <span className="step-icon">{cfg.icon}</span>
        <span className="step-label">{step.label || cfg.label}</span>
      </div>
      <div className="step-text">{step.text}</div>
    </div>
  );
}

export default function AgentThinkingPanel({ steps, isRunning }) {
  const bottomRef = useRef(null);

  // Auto-scroll to latest step
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps]);

  return (
    <div className="thinking-panel">
      <div className="panel-header">
        <span className="panel-title">Agent Steps</span>
        {isRunning && <div className="spinner" />}
      </div>

      <div className="steps-list">
        {steps.length === 0 ? (
          <div className="empty-steps">Steps appear live here</div>
        ) : (
          steps.map((step, i) => <StepItem key={i} step={step} />)
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
