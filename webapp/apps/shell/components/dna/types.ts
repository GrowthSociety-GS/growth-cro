// Brand DNA — normalized view-model types for the SP-3 viewer.
//
// V29 brand_dna_extractor outputs a nested JSON (cf data/_growth_society/brand_dna.json
// and skills/site-capture/scripts/brand_dna_extractor.py). It is tolerant by design:
// some clients have only Phase 1 (visual tokens), others have Phase 2 (voice + assets).
// This module exposes a single `normalizeBrandDna()` helper that flattens whatever
// the JSON contains into a stable shape the React components can render without
// defensive plumbing.
//
// The task brief mentions a `persona { schwartz_awareness, narrative }` field; the
// real V29 schema does not yet ship that block, so we accept it optionally and
// fall back to `identity.market_position` + `audience` when persona is missing.

export type DnaColor = {
  name: string;
  hex: string;
  role: string | null; // "primary" | "secondary" | "neutral" | "semantic" | etc.
};

export type DnaTypography = {
  display: { family: string; weight: number | null } | null;
  body: { family: string; weight: number | null } | null;
  mono: { family: string; weight: number | null } | null;
  scale: string | null;
  line_height: string | null;
};

export type DnaVoice = {
  tone: string[];
  vocabulary: string[]; // preferred CTA verbs + non-forbidden vocabulary
  forbidden: string[];
  examples: string[];
  rhythm: string | null;
};

export type SchwartzLevel =
  | "unaware"
  | "problem_aware"
  | "solution_aware"
  | "product_aware"
  | "most_aware";

export type DnaPersona = {
  schwartz_awareness: SchwartzLevel | null;
  narrative: string | null;
  archetype: string | null;
  audience: string | null;
};

export type DnaIdentity = {
  brand_name: string | null;
  category: string | null;
  market_position: string | null;
  audience: string | null;
  confidence: number | null;
};

export type NormalizedBrandDna = {
  identity: DnaIdentity;
  colors: DnaColor[]; // flat list with role attached
  typography: DnaTypography;
  voice: DnaVoice;
  persona: DnaPersona;
  raw_keys: string[]; // what we found in the source JSON
  aura_tokens: Record<string, string> | null; // optional sidecar from data/_aura_*
};

const SCHWARTZ_LEVELS: SchwartzLevel[] = [
  "unaware",
  "problem_aware",
  "solution_aware",
  "product_aware",
  "most_aware",
];

function asString(v: unknown): string | null {
  if (typeof v === "string" && v.trim().length > 0) return v.trim();
  return null;
}

function asStringArray(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.filter((x): x is string => typeof x === "string" && x.length > 0);
}

function asNumber(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return null;
}

function asObject(v: unknown): Record<string, unknown> | null {
  if (v && typeof v === "object" && !Array.isArray(v)) {
    return v as Record<string, unknown>;
  }
  return null;
}

// Color values can be hex (#abc / #aabbcc / #aabbccdd), rgb(), or hsl(). We only
// keep what is recognized as renderable, no client-side sanitizing of arbitrary CSS.
function looksLikeColor(v: string): boolean {
  if (/^#[0-9a-fA-F]{3,8}$/.test(v)) return true;
  if (/^rgba?\(\s*[\d.,\s%]+\)$/i.test(v)) return true;
  if (/^hsla?\(\s*[\d.,\s%]+\)$/i.test(v)) return true;
  return false;
}

function flattenColors(
  src: Record<string, unknown> | null
): DnaColor[] {
  if (!src) return [];
  const out: DnaColor[] = [];
  // V29 nests by role: { primary: { gold: "#d4a945", ... }, secondary: { ... }, neutrals: { ... } }
  for (const [role, group] of Object.entries(src)) {
    const groupObj = asObject(group);
    if (groupObj) {
      for (const [name, val] of Object.entries(groupObj)) {
        const s = asString(val);
        if (s && looksLikeColor(s)) {
          out.push({ name, hex: s, role });
        }
      }
      continue;
    }
    // Some captures store flat string maps: { primary: "#hex" }
    const flat = asString(group);
    if (flat && looksLikeColor(flat)) {
      out.push({ name: role, hex: flat, role: null });
    }
  }
  // Also tolerate the alternative array shape mentioned in the task brief:
  // colors: [{ name, hex, role }]
  if (Array.isArray(src)) {
    for (const item of src as unknown[]) {
      const obj = asObject(item);
      if (!obj) continue;
      const name = asString(obj.name);
      const hex = asString(obj.hex);
      if (name && hex && looksLikeColor(hex)) {
        out.push({ name, hex, role: asString(obj.role) });
      }
    }
  }
  return out;
}

function parseFontFamilyEntry(v: unknown): { family: string; weight: number | null } | null {
  const s = asString(v);
  if (s) return { family: s, weight: null };
  const obj = asObject(v);
  if (!obj) return null;
  const family = asString(obj.family) ?? asString(obj.font_family);
  if (!family) return null;
  const weight = asNumber(obj.weight);
  return { family, weight };
}

function normalizeTypography(src: Record<string, unknown> | null): DnaTypography {
  if (!src) {
    return { display: null, body: null, mono: null, scale: null, line_height: null };
  }
  // V29 keys: heading / body / mono / scale / line_height.
  // Task-brief alt: display / body. We tolerate both.
  return {
    display: parseFontFamilyEntry(src.display ?? src.heading),
    body: parseFontFamilyEntry(src.body),
    mono: parseFontFamilyEntry(src.mono),
    scale: asString(src.scale),
    line_height: asString(src.line_height),
  };
}

function normalizeVoice(src: Record<string, unknown> | null): DnaVoice {
  if (!src) {
    return { tone: [], vocabulary: [], forbidden: [], examples: [], rhythm: null };
  }
  return {
    tone: asStringArray(src.tone),
    vocabulary: [
      ...asStringArray(src.vocabulary),
      ...asStringArray(src.preferred_cta_verbs),
    ],
    forbidden: asStringArray(src.forbidden_words ?? src.forbidden),
    examples: asStringArray(src.examples),
    rhythm: asString(src.sentence_rhythm ?? src.rhythm),
  };
}

function asSchwartzLevel(v: unknown): SchwartzLevel | null {
  const s = asString(v)?.toLowerCase();
  if (!s) return null;
  return (SCHWARTZ_LEVELS as string[]).includes(s) ? (s as SchwartzLevel) : null;
}

function normalizePersona(
  src: Record<string, unknown> | null,
  identity: DnaIdentity
): DnaPersona {
  if (!src) {
    return {
      schwartz_awareness: null,
      narrative: identity.market_position,
      archetype: null,
      audience: identity.audience,
    };
  }
  return {
    schwartz_awareness: asSchwartzLevel(src.schwartz_awareness),
    narrative: asString(src.narrative) ?? identity.market_position,
    archetype: asString(src.archetype),
    audience: asString(src.audience) ?? identity.audience,
  };
}

function normalizeIdentity(src: Record<string, unknown> | null): DnaIdentity {
  if (!src) {
    return {
      brand_name: null,
      category: null,
      market_position: null,
      audience: null,
      confidence: null,
    };
  }
  return {
    brand_name: asString(src.brand_name),
    category: asString(src.category),
    market_position: asString(src.market_position),
    audience: asString(src.audience),
    confidence: asNumber(src.confidence),
  };
}

// AURA tokens sidecar: free-form { key: stringValue } map. We only keep
// stringifiable scalar entries — no nested rendering here, the goal is to surface
// extra knobs (motion timings, glass blur, etc.) as a flat token list.
function normalizeAuraTokens(src: unknown): Record<string, string> | null {
  const obj = asObject(src);
  if (!obj) return null;
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
      out[k] = String(v);
    }
  }
  return Object.keys(out).length > 0 ? out : null;
}

export function normalizeBrandDna(
  brandDna: Record<string, unknown> | null,
  auraTokens?: Record<string, unknown> | null
): NormalizedBrandDna | null {
  if (!brandDna || Object.keys(brandDna).length === 0) return null;
  const raw_keys = Object.keys(brandDna);

  const visual = asObject(brandDna.visual_tokens) ?? brandDna;
  const colorsSrc = asObject(visual.colors);
  const typoSrc = asObject(visual.typography);

  const identity = normalizeIdentity(asObject(brandDna.identity));
  const typography = normalizeTypography(typoSrc);
  const colors = flattenColors(colorsSrc);
  const voice = normalizeVoice(asObject(brandDna.voice_tokens) ?? asObject(brandDna.voice));
  const persona = normalizePersona(asObject(brandDna.persona), identity);
  const aura_tokens = normalizeAuraTokens(auraTokens);

  return { identity, colors, typography, voice, persona, raw_keys, aura_tokens };
}

// Visual color palette for the Schwartz awareness pill — maps the 5 levels to
// the existing @growthcro/ui Pill tones. Deterministic + accessible (4.5:1 on dark bg).
export const SCHWARTZ_TONES: Record<SchwartzLevel, "red" | "amber" | "gold" | "cyan" | "green"> = {
  unaware: "red",
  problem_aware: "amber",
  solution_aware: "gold",
  product_aware: "cyan",
  most_aware: "green",
};

export const SCHWARTZ_LABELS: Record<SchwartzLevel, string> = {
  unaware: "Unaware",
  problem_aware: "Problem-aware",
  solution_aware: "Solution-aware",
  product_aware: "Product-aware",
  most_aware: "Most-aware",
};
