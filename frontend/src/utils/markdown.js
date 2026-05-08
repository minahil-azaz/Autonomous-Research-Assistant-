/**
 * utils/markdown.js
 *
 * Converts Markdown → safe HTML for rendering in the report viewer.
 * Covers the subset produced by the research agent:
 *   headings, bold, italic, code, lists, blockquotes, paragraphs.
 *
 * We deliberately avoid a heavy library (marked/remark) to keep the
 * bundle small. For a production app, use `marked` with DOMPurify.
 */

/**
 * Render a Markdown string to an HTML string.
 * @param {string} md  Raw Markdown
 * @returns {string}   Safe HTML
 */
export function renderMarkdown(md) {
  if (!md) return "";

  const lines = md.split("\n");
  const out = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(escapeHtml(lines[i]));
        i++;
      }
      out.push(`<pre><code class="lang-${lang}">${codeLines.join("\n")}</code></pre>`);
      i++;
      continue;
    }

    // ATX headings
    if (line.startsWith("### ")) { out.push(`<h3>${inline(line.slice(4))}</h3>`); i++; continue; }
    if (line.startsWith("## "))  { out.push(`<h2>${inline(line.slice(3))}</h2>`); i++; continue; }
    if (line.startsWith("# "))   { out.push(`<h1>${inline(line.slice(2))}</h1>`); i++; continue; }

    // Blockquote
    if (line.startsWith("> ")) {
      out.push(`<blockquote><p>${inline(line.slice(2))}</p></blockquote>`);
      i++; continue;
    }

    // Unordered list
    if (line.startsWith("- ") || line.startsWith("* ")) {
      const items = [];
      while (i < lines.length && (lines[i].startsWith("- ") || lines[i].startsWith("* "))) {
        items.push(`<li>${inline(lines[i].slice(2))}</li>`);
        i++;
      }
      out.push(`<ul>${items.join("")}</ul>`);
      continue;
    }

    // Ordered list
    if (/^\d+\. /.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(`<li>${inline(lines[i].replace(/^\d+\. /, ""))}</li>`);
        i++;
      }
      out.push(`<ol>${items.join("")}</ol>`);
      continue;
    }

    // Horizontal rule
    if (/^[-*_]{3,}$/.test(line.trim())) { out.push("<hr>"); i++; continue; }

    // Blank line
    if (line.trim() === "") { i++; continue; }

    // Paragraph
    out.push(`<p>${inline(line)}</p>`);
    i++;
  }

  return out.join("\n");
}


/** Apply inline Markdown: bold, italic, code, links */
function inline(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g,     "<em>$1</em>")
    .replace(/`([^`]+)`/g,     "<code>$1</code>")
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
