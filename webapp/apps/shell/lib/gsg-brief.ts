// Deterministic GSG brief builder (SP-5 webapp-v26-parity-and-beyond).
//
// Server-only module that produces the JSON contract handed to the
// `moteur_gsg` pipeline (currently FastAPI deferred V2 → JSON only).
// Mirrors the V27 reference (`deliverables/GrowthCRO-V27-CommandCenter.html`
// `buildBrief()` helper) but typed and SSR-safe.
//
// The shape is intentionally stable: any change here = a change in the
// pipeline contract. Add keys, do not rename.

import type { Client } from "@growthcro/data";

export type GsgModeId =
  | "complete"
  | "replace"
  | "extend"
  | "elevate"
  | "genesis";

export type GsgMode = {
  id: GsgModeId;
  label: string;
  short: string;
  desc: string;
};

// Single source of truth for the 5 GSG modes — used by the selector,
// the brief builder, and the end-to-end demo flow. Keep in sync with
// `BriefWizard.MODES` (legacy V2 wizard, soft deprecated).
export const GSG_MODES: Record<GsgModeId, GsgMode> = {
  complete: {
    id: "complete",
    label: "Mode 1 · Complete",
    short: "Complete",
    desc: "Reprend la page existante et applique les fixes recos doctrine. Conserve la structure source.",
  },
  replace: {
    id: "replace",
    label: "Mode 2 · Replace",
    short: "Replace",
    desc: "Remplace la LP par une refonte doctrine sur la même promesse. Pipeline sequential 4-stages.",
  },
  extend: {
    id: "extend",
    label: "Mode 3 · Extend",
    short: "Extend",
    desc: "Ajoute des sections doctrine (proof stack, mechanism, FAQ) à l'existant.",
  },
  elevate: {
    id: "elevate",
    label: "Mode 4 · Elevate",
    short: "Elevate",
    desc: "Direction artistique premium (Emil Kowalski) sans changer la copy. Visuel only.",
  },
  genesis: {
    id: "genesis",
    label: "Mode 5 · Genesis",
    short: "Genesis",
    desc: "From scratch. Crée la LP en partant de la doctrine + brand DNA, sans page source.",
  },
};

export const GSG_MODE_IDS = Object.keys(GSG_MODES) as GsgModeId[];

export function isGsgModeId(value: unknown): value is GsgModeId {
  return typeof value === "string" && value in GSG_MODES;
}

export function resolveGsgMode(raw: string | string[] | undefined): GsgModeId {
  const value = Array.isArray(raw) ? raw[0] : raw;
  return isGsgModeId(value) ? value : "complete";
}

// The deterministic brief contract. Stable JSON, hand-off ready for the
// FastAPI `/runs/gsg` endpoint (V2). All fields are derived from the
// selected client + audit + mode — no LLM call here.
export type GsgBrief = {
  version: string;
  client_slug: string;
  client_name: string;
  page_type: string;
  page_url: string | null;
  doctrine_version: string;
  mode: {
    id: GsgModeId;
    label: string;
    intent: string;
  };
  boundary: {
    llm: string;
    deterministic: string;
    reality: string;
  };
  product_name: string;
  one_line_pitch: string;
  primary_cta: string;
  brand_voice: string;
  target_audience: string;
  brand_tokens: {
    primary_color: string;
    secondary_colors: string[];
    tone: string[];
    cta_verbs: string[];
    signature: string;
    forbidden: string[];
  };
  layout: string[];
  generated_at: string;
  build_id: string;
};

// Pure helper — given a Client row + (optional) selected audit metadata
// + a mode, return the deterministic brief. The audit/recos selection
// is left to the caller (we keep this file mono-concern: brief shape).
type BuildInput = {
  client: Pick<Client, "slug" | "name" | "homepage_url" | "brand_dna_json">;
  audit?: {
    page_type?: string | null;
    page_url?: string | null;
    doctrine_version?: string | null;
  } | null;
  mode: GsgModeId;
};

// Stable fallback layout — matches the 5-step controlled renderer used
// by V27 (`hero` → `final_cta`). Mode-specific overrides come later.
const DEFAULT_LAYOUT = [
  "hero",
  "proof_stack",
  "mechanism",
  "objection_resolver",
  "final_cta",
] as const;

// Build IDs are deterministic when the input is stable: we hash the
// (client, mode, audit) triple via a simple `djb2` so the same browser
// reload yields the same brief — no random UUIDs that would break
// snapshot diffs and SSR hydration.
function djb2(input: string): string {
  let hash = 5381;
  for (let i = 0; i < input.length; i += 1) {
    hash = ((hash << 5) + hash + input.charCodeAt(i)) | 0;
  }
  return Math.abs(hash).toString(36).padStart(8, "0").slice(0, 8);
}

// Read a string field nested in `client.brand_dna_json` without
// erroring out when the column is null (3 seed clients have no DNA).
function readDna(
  dna: Record<string, unknown> | null,
  path: string[]
): unknown {
  let cur: unknown = dna;
  for (const seg of path) {
    if (!cur || typeof cur !== "object") return null;
    cur = (cur as Record<string, unknown>)[seg];
  }
  return cur;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((v): v is string => typeof v === "string");
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

export function buildDeterministicBrief(input: BuildInput): GsgBrief {
  const { client, audit, mode } = input;
  const dna = client.brand_dna_json ?? null;

  const palette = readDna(dna, ["visual_tokens", "colors", "palette_full"]);
  const paletteArr = Array.isArray(palette) ? palette : [];
  const primaryColor =
    asString(readDna(dna, ["visual_tokens", "colors", "primary", "hex"])) ||
    asString((paletteArr[0] as { hex?: string } | undefined)?.hex) ||
    "#d7b46a";
  const secondaryColors = paletteArr
    .slice(1, 5)
    .map((entry) => (entry as { hex?: string }).hex)
    .filter((hex): hex is string => Boolean(hex));

  const tone = asStringArray(readDna(dna, ["voice_tokens", "tone"]));
  const ctaVerbs = asStringArray(
    readDna(dna, ["voice_tokens", "preferred_cta_verbs"])
  );
  const signature = asString(
    readDna(dna, ["voice_tokens", "voice_signature_phrase"])
  );
  const forbidden = asStringArray(
    readDna(dna, ["voice_tokens", "forbidden_words"])
  );

  const modeMeta = GSG_MODES[mode];
  const pageType = audit?.page_type ?? "homepage";
  const pageUrl = audit?.page_url ?? client.homepage_url ?? null;
  const doctrineVersion = audit?.doctrine_version ?? "v3.2.1";

  const productName = client.name;
  const oneLinePitch =
    signature ||
    `Clarifier la promesse de ${productName} et prouver plus vite.`;
  const primaryCta = ctaVerbs[0]
    ? `${ctaVerbs[0]} maintenant`
    : "Commencer maintenant";
  const brandVoice = tone.length > 0 ? tone.join(", ") : "neutral";
  const targetAudience = "Visiteurs ciblés audience paid";

  const buildIdSource = `${client.slug}|${pageType}|${mode}|${doctrineVersion}`;
  const buildId = djb2(buildIdSource);

  return {
    version: "v27.0.0-browser-brief",
    client_slug: client.slug,
    client_name: client.name,
    page_type: pageType,
    page_url: pageUrl,
    doctrine_version: doctrineVersion,
    mode: {
      id: mode,
      label: modeMeta.label,
      intent: modeMeta.desc,
    },
    boundary: {
      llm: "copy variants only",
      deterministic: "layout, evidence, CTA, brand tokens",
      reality: "not required",
    },
    product_name: productName,
    one_line_pitch: oneLinePitch,
    primary_cta: primaryCta,
    brand_voice: brandVoice,
    target_audience: targetAudience,
    brand_tokens: {
      primary_color: primaryColor,
      secondary_colors: secondaryColors,
      tone,
      cta_verbs: ctaVerbs,
      signature,
      forbidden,
    },
    layout: [...DEFAULT_LAYOUT],
    // ISO date is the only "live" field — kept at second precision so the
    // brief stays diff-friendly within a single SSR pass.
    generated_at: new Date().toISOString().slice(0, 19) + "Z",
    build_id: buildId,
  };
}
