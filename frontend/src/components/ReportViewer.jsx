/**
 * components/ReportViewer.jsx
 *
 * Renders the final Markdown report and provides:
 *  - Copy to clipboard
 *  - Download as .md
 *  - Export to PDF (calls POST /api/export)
 */

import { useState } from "react";
import { renderMarkdown } from "../utils/markdown";
import { exportPdf } from "../utils/api";
import { countWords } from "../utils/text";

export default function ReportViewer({ report, topic, isRunning, error }) {
  const [copying, setCopying] = useState(false);
  const [exporting, setExporting] = useState(false);

  const hasReport = Boolean(report);

  const handleCopy = async () => {
    if (!report) return;
    await navigator.clipboard.writeText(report);
    setCopying(true);
    setTimeout(() => setCopying(false), 1500);
  };

  const handleDownloadMd = () => {
    if (!report) return;
    const blob = new Blob([report], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `research-${slugify(topic)}.md`;
    a.click();
  };

  const handleExportPdf = async () => {
    if (!report || exporting) return;
    setExporting(true);
    try {
      const blob = await exportPdf(report, topic);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `research-${slugify(topic)}.pdf`;
      a.click();
    } catch (e) {
      alert("PDF export failed: " + e.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="report-wrapper">
      {/* ── Report body ── */}
      <div className="report-area">
        {error && (
          <div className="error-msg">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!hasReport && !error && (
          <div className="empty-state">
            <DocIcon />
            <p>Enter a topic above and click <strong>Research</strong></p>
          </div>
        )}

        {hasReport && (
          <div
            className="report-content"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(report) }}
          />
        )}
      </div>

      {/* ── Export toolbar ── */}
      <div className="export-bar">
        <button
          className="export-btn"
          onClick={handleCopy}
          disabled={!hasReport}
        >
          {copying ? "✓ Copied!" : "⎘ Copy markdown"}
        </button>

        <button
          className="export-btn"
          onClick={handleDownloadMd}
          disabled={!hasReport}
        >
          ↓ Download .md
        </button>

        <button
          className="export-btn pdf-btn"
          onClick={handleExportPdf}
          disabled={!hasReport || exporting}
        >
          {exporting ? "Generating…" : "⬇ Export PDF"}
        </button>

        {hasReport && (
          <span className="word-count">{countWords(report)} words</span>
        )}
      </div>
    </div>
  );
}

function DocIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" opacity="0.25">
      <rect x="8" y="6" width="32" height="40" rx="4" stroke="currentColor" strokeWidth="1.5"/>
      <line x1="14" y1="18" x2="34" y2="18" stroke="currentColor" strokeWidth="1.5"/>
      <line x1="14" y1="25" x2="34" y2="25" stroke="currentColor" strokeWidth="1.5"/>
      <line x1="14" y1="32" x2="26" y2="32" stroke="currentColor" strokeWidth="1.5"/>
    </svg>
  );
}

function slugify(str = "") {
  return str.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "").slice(0, 50);
}
