// design-grammar-types.ts — pure types + helpers for the Design Grammar viewer.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
// Split out from `design-grammar-fs.ts` so client components can import the
// type+helper surface without pulling `node:fs` / `node:path` into the
// client bundle (webpack rejects that mix). Server-only disk access stays
// in `design-grammar-fs.ts` and re-exports these types for backward compat.
//
// Mirrors the pattern of `scent-types.ts` (Sprint 7) and `experiment-types.ts`
// (Sprint 8). Zero Node imports. Zero React imports.
//
// V30 Design Grammar — 7 artefacts per client, on-disk layout :
//   data/captures/<client>/design_grammar/
//     ├── tokens.css                    (CSS variables + base styles)
//     ├── tokens.json                   (structured design tokens)
//     ├── component_grammar.json        (rules per component type)
//     ├── section_grammar.json          (rules per page section)
//     ├── composition_rules.json        (do/dont composition)
//     ├── brand_forbidden_patterns.json (forbidden patterns + rationale)
//     └── quality_gates.json            (gates per pattern)
//
// V1 shape is intentionally permissive — we surface whatever the disk has
// (`unknown` json bodies) and let the UI defend each field. V2 will tighten
// the schema after Mathis validates a first artefact on screen.

/** Canonical basenames of the 7 design_grammar artefacts. */
export const DESIGN_GRAMMAR_FILES = [
  "tokens.css",
  "tokens.json",
  "component_grammar.json",
  "section_grammar.json",
  "composition_rules.json",
  "brand_forbidden_patterns.json",
  "quality_gates.json",
] as const;

export type DesignGrammarFile = (typeof DESIGN_GRAMMAR_FILES)[number];

/** Stable order used to drive the 7-artefact grid in `<DesignGrammarViewer>`. */
export const DESIGN_GRAMMAR_ORDER: readonly DesignGrammarFile[] = DESIGN_GRAMMAR_FILES;

/**
 * V1 surface : one bundle per client. Each artefact is either present with
 * its parsed contents (or raw CSS text for `tokens_css`) or null. The disk
 * may have 0..7 files for any given client — the UI must render gracefully
 * in every state (empty, partial, complete).
 */
export type DesignGrammarBundle = {
  client_slug: string;
  /** Raw CSS source (UTF-8 text), or null when tokens.css is absent on disk. */
  tokens_css: string | null;
  /** Parsed JSON contents (unknown shape — UI defends each field). */
  tokens: unknown;
  component_grammar: unknown;
  section_grammar: unknown;
  composition_rules: unknown;
  brand_forbidden_patterns: unknown;
  quality_gates: unknown;
  /** ISO mtime of the most-recent artefact (UI surfaces as "last_updated"). */
  captured_at: string | null;
  /** Count of artefacts present (0..7). Used by the empty-state copy. */
  artefact_count: number;
};

/**
 * Returns true when at least one artefact is present. Used by callers that
 * want to short-circuit the empty-state rendering without inspecting each
 * field. Pure — safe in client components.
 */
export function hasAnyArtefact(bundle: DesignGrammarBundle | null): boolean {
  if (!bundle) return false;
  return bundle.artefact_count > 0;
}

/**
 * Forbidden-patterns shape we *try* to surface in `<ForbiddenPatternsAlert>`.
 * Best-effort — the actual JSON may not match exactly. The component defends
 * each field individually before rendering.
 */
export type ForbiddenPattern = {
  id: string | null;
  label: string;
  rationale: string | null;
  severity: "low" | "medium" | "high" | null;
};

/**
 * Permissive parser : walks an `unknown` JSON value and pulls out anything
 * that *looks* like a list of forbidden patterns. Recognises three common
 * shapes :
 *   1. `{ patterns: [...] }`
 *   2. `{ forbidden: [...] }`
 *   3. The root is already an array.
 * Each entry is normalised to `ForbiddenPattern`. Unknown fields are dropped.
 * Pure — safe in client components.
 */
export function parseForbiddenPatterns(raw: unknown): ForbiddenPattern[] {
  const list = pickArray(raw);
  if (!list) return [];
  const out: ForbiddenPattern[] = [];
  for (const item of list) {
    if (typeof item === "string") {
      out.push({
        id: null,
        label: item,
        rationale: null,
        severity: null,
      });
      continue;
    }
    if (!item || typeof item !== "object") continue;
    const o = item as Record<string, unknown>;
    const label =
      asStr(o.label) ??
      asStr(o.name) ??
      asStr(o.pattern) ??
      asStr(o.id) ??
      null;
    if (!label) continue;
    out.push({
      id: asStr(o.id) ?? asStr(o.slug) ?? null,
      label,
      rationale: asStr(o.rationale) ?? asStr(o.reason) ?? asStr(o.why) ?? null,
      severity: asSeverity(o.severity),
    });
  }
  return out;
}

function pickArray(raw: unknown): unknown[] | null {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object") {
    const o = raw as Record<string, unknown>;
    if (Array.isArray(o.patterns)) return o.patterns;
    if (Array.isArray(o.forbidden)) return o.forbidden;
    if (Array.isArray(o.items)) return o.items;
    if (Array.isArray(o.rules)) return o.rules;
  }
  return null;
}

function asStr(v: unknown): string | null {
  return typeof v === "string" && v.length > 0 ? v : null;
}

function asSeverity(v: unknown): ForbiddenPattern["severity"] {
  if (v === "low" || v === "medium" || v === "high") return v;
  return null;
}
