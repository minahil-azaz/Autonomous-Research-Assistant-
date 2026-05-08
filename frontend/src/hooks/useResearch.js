/**
 * hooks/useResearch.js
 *
 * Core hook that manages:
 *  - SSE connection to the FastAPI backend
 *  - Agent step accumulation (shown in AgentThinkingPanel)
 *  - Final report state
 *  - Session memory (last 5 topics)
 *  - Error handling
 *
 * Usage:
 *   const { steps, report, isRunning, error, startResearch, reset } = useResearch();
 */

import { useState, useRef, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export function useResearch() {
  const [steps, setSteps]           = useState([]);
  const [report, setReport]         = useState("");
  const [isRunning, setIsRunning]   = useState(false);
  const [error, setError]           = useState(null);
  const [sessionMemory, setMemory]  = useState([]);

  const esRef = useRef(null);   // EventSource reference

  /**
   * Start a research session.
   * Opens an SSE connection and processes incoming events.
   */
  const startResearch = useCallback((topic, depth = "standard", style = "summary") => {
    // Clean up any previous connection
    if (esRef.current) esRef.current.close();

    setSteps([]);
    setReport("");
    setError(null);
    setIsRunning(true);

    const url = `${API_BASE}/research?topic=${encodeURIComponent(topic)}&depth=${depth}&style=${style}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        if (data.type === "step") {
          setSteps((prev) => [...prev, data.step]);
        }

        if (data.type === "done") {
          setReport(data.report);
          setIsRunning(false);
          es.close();

          // Save to session memory (keep last 5 unique topics)
          setMemory((prev) => {
            const updated = [topic, ...prev.filter((t) => t !== topic)];
            return updated.slice(0, 5);
          });
        }

        if (data.type === "error") {
          setError(data.message);
          setIsRunning(false);
          es.close();
        }
      } catch (parseError) {
        console.error("SSE parse error:", parseError);
      }
    };

    es.onerror = () => {
      setError("Connection to the research server failed. Is the backend running?");
      setIsRunning(false);
      es.close();
    };
  }, []);

  const reset = useCallback(() => {
    if (esRef.current) esRef.current.close();
    setSteps([]);
    setReport("");
    setError(null);
    setIsRunning(false);
  }, []);

  return { steps, report, isRunning, error, sessionMemory, startResearch, reset };
}
