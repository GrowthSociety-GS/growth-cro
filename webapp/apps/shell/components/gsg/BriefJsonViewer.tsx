// BriefJsonViewer — render the deterministic GSG brief as pretty JSON.
// Server Component. SP-5 (webapp-v26-parity-and-beyond). Uses the
// `.gc-mono` class shipped by SP-1 foundation (max-height + scroll +
// monospace + ink background). DIY syntax highlight via a single-pass
// state-machine tokenizer — no Prism dep.
//
// Why home-made highlight: hard constraint "pas d'install nouvelle dep"
// from the SP-5 briefing. The tokenizer walks the raw JSON string and
// emits typed spans (`key`, `str`, `num`, `lit`, `punct`). Output is
// HTML-escaped per token so user-controlled fields can't break out of
// their span.

import type { GsgBrief } from "@/lib/gsg-brief";

type Props = {
  brief: GsgBrief;
};

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// State-machine tokenizer over JSON.stringify output. We trust the
// shape (no comments, no trailing commas, valid JSON) so the parser
// stays a single forward pass over the character stream.
//
// A "key" is a string immediately followed by `:` (skipping whitespace).
// Anything else is a "str" value.
function highlightJson(raw: string): string {
  let out = "";
  const len = raw.length;
  let i = 0;
  while (i < len) {
    const ch = raw[i]!;

    // String → consume up to the closing quote (handle escaped quotes).
    if (ch === '"') {
      let j = i + 1;
      while (j < len) {
        if (raw[j] === "\\" && j + 1 < len) {
          j += 2;
          continue;
        }
        if (raw[j] === '"') break;
        j += 1;
      }
      const literal = raw.slice(i, j + 1);
      // Look ahead past whitespace for `:` → key, else value string.
      let k = j + 1;
      while (k < len && (raw[k] === " " || raw[k] === "\t")) k += 1;
      const isKey = raw[k] === ":";
      const cls = isKey ? "gc-mono__key" : "gc-mono__str";
      out += `<span class="${cls}">${escapeHtml(literal)}</span>`;
      i = j + 1;
      continue;
    }

    // Number → lookahead until we leave the digit/sign/exponent set.
    if (ch === "-" || (ch >= "0" && ch <= "9")) {
      let j = i;
      while (j < len && /[-+0-9.eE]/.test(raw[j]!)) j += 1;
      const literal = raw.slice(i, j);
      out += `<span class="gc-mono__num">${escapeHtml(literal)}</span>`;
      i = j;
      continue;
    }

    // Literals true/false/null
    if (ch === "t" || ch === "f" || ch === "n") {
      const slice4 = raw.slice(i, i + 4);
      const slice5 = raw.slice(i, i + 5);
      if (slice4 === "true" || slice4 === "null") {
        out += `<span class="gc-mono__lit">${slice4}</span>`;
        i += 4;
        continue;
      }
      if (slice5 === "false") {
        out += `<span class="gc-mono__lit">${slice5}</span>`;
        i += 5;
        continue;
      }
    }

    // Default: punctuation, whitespace, etc. — pass through escaped.
    out += escapeHtml(ch);
    i += 1;
  }
  return out;
}

export function BriefJsonViewer({ brief }: Props) {
  const raw = JSON.stringify(brief, null, 2);
  const html = highlightJson(raw);
  return (
    <pre
      id="gsg-brief-panel"
      className="gc-mono"
      // We control the entire HTML payload (escaped per token) ourselves;
      // no user-supplied HTML reaches the DOM unescaped. The tokenizer
      // calls `escapeHtml` on every literal it emits.
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
