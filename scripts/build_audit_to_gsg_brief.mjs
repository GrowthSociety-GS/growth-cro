#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DATA_JS = path.join(ROOT, "deliverables", "growth_audit_data.js");

function arg(name, fallback = null) {
  const i = process.argv.indexOf(`--${name}`);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return fallback;
}

function loadData() {
  const src = fs.readFileSync(DATA_JS, "utf8");
  const sandbox = { window: {} };
  vm.runInNewContext(src, sandbox, { filename: DATA_JS });
  return sandbox.window.GROWTH_AUDIT_DATA;
}

function priorityRank(priority) {
  return { P0: 0, P1: 1, P2: 2, P3: 3 }[priority] ?? 9;
}

function topRecos(page, limit = 8) {
  return [...(page.recos || [])]
    .sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority) || (b.ice_score || 0) - (a.ice_score || 0))
    .slice(0, limit)
    .map((r) => ({
      priority: r.priority || "P3",
      ice_score: r.ice_score || 0,
      criterion_id: r.criterion_id || r.cluster_id || "",
      problem: r.problem_headline || (r.before || "").slice(0, 180),
      before: r.before || "",
      after: r.after || "",
      why: r.why || "",
      evidence_ids: r.evidence_ids || [],
    }));
}

function compactText(text, n = 260) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  return clean.length > n ? `${clean.slice(0, n - 1)}…` : clean;
}

function riskFlags(reco) {
  const text = `${reco.problem || ""} ${reco.before || ""} ${reco.after || ""} ${reco.why || ""}`.toLowerCase();
  const flags = [];
  if (/verbatim|testimonial|témoignage|avis client|quote|customer quote/.test(text)) {
    flags.push("requires_real_voc");
  }
  if (/g2|trustpilot|review|avis|111,368|source vérifiable|source verifiable/.test(text)) {
    flags.push("requires_external_proof_source");
  }
  if (/urgence|rareté|rarete|stock|countdown|places? restantes?/.test(text)) {
    flags.push("urgency_must_be_truthful");
  }
  return flags;
}

function safeAction(reco, n = 320) {
  const flags = riskFlags(reco);
  if (flags.includes("requires_real_voc")) {
    return "Collecter de vrais verbatims clients avant rendu. Le GSG peut réserver l'emplacement, mais ne doit pas inventer de citations.";
  }
  if (flags.includes("requires_external_proof_source") && !(reco.evidence_ids || []).length) {
    return "Ajouter une preuve vérifiable ou masquer le claim. Le GSG ne doit pas inventer de rating, source ou chiffre.";
  }
  return compactText(reco.after, n);
}

function headlineDirection(brief) {
  const name = brief.audit_summary?.client_name || "La page";
  const dominant = brief.audit_summary?.dominant_problem || "";
  if (/hero|h1|promesse|clar/i.test(dominant)) {
    return `${name}: clarifier la promesse, prouver plus vite, garder un seul CTA.`;
  }
  return `${name}: transformer l'audit en page plus claire et plus prouvée.`;
}

function localizeCtaVerb(verb) {
  const v = String(verb || "").toLowerCase();
  if (v.includes("get started") || v === "start") return "Commencer";
  if (v.includes("join")) return "Rejoindre";
  if (v.includes("choose")) return "Choisir";
  if (v.includes("translate")) return "Traduire";
  return verb || "Commencer";
}

function brandTokens(client) {
  const dna = client.v26?.brand_dna || {};
  const colors = dna.visual_tokens?.colors || {};
  const palette = colors.palette_full || [];
  return {
    primary_color: colors.primary?.hex || palette[0]?.hex || "#d7b46a",
    secondary_colors: palette.slice(1, 5).map((c) => c.hex).filter(Boolean),
    tone: dna.voice_tokens?.tone || [],
    preferred_cta_verbs: dna.voice_tokens?.preferred_cta_verbs || [],
    voice_signature_phrase: dna.voice_tokens?.voice_signature_phrase || "",
    forbidden_words: dna.voice_tokens?.forbidden_words || [],
    approved_visual_techniques: dna.asset_rules?.approved_techniques || [],
    brand_fidelity_anchors: dna.asset_rules?.brand_fidelity_anchors || [],
  };
}

function buildBrief(data, clientId, pageType) {
  const client = data.clients.find((c) => c.id === clientId);
  if (!client) throw new Error(`Unknown client: ${clientId}`);
  const page = (client.pages || []).find((p) => p.page_type === pageType);
  if (!page) throw new Error(`Unknown page for ${clientId}: ${pageType}`);

  const recos = topRecos(page, 10);
  const tokens = brandTokens(client);
  const primaryReco = recos[0] || {};
  const pageScore = Math.round(page.score_pct || 0);
  const p0 = page.priority_distribution?.P0 || 0;
  const ctaVerb = localizeCtaVerb(tokens.preferred_cta_verbs?.[0]);

  const brief = {
    version: "v27.0.0-audit-to-gsg-brief",
    generated_at: new Date().toISOString(),
    source: {
      data_file: "deliverables/growth_audit_data.js",
      client: client.id,
      page_type: page.page_type,
      page_url: page.url,
      score_pct: page.score_pct,
      priority_distribution: page.priority_distribution,
      screenshot_desktop: page.screenshots?.desktop_full || page.screenshots?.desktop_fold || "",
      screenshot_mobile: page.screenshots?.mobile_full || page.screenshots?.mobile_fold || "",
    },
    product_boundary: {
      audit_engine: "read_only",
      recommendations_engine: "read_only",
      gsg: "brief_consumer",
      reality_layer: "not_required_for_static_mvp",
      llm_scope: "copy variants only; no layout, no scoring, no full HTML rewrite",
      deterministic_scope: "page structure, section order, evidence selection, brand tokens, CTA contract",
    },
    brand_tokens: tokens,
    audit_summary: {
      client_name: client.name,
      business_type: client.business_type,
      panel_role: client.panel?.role || "runtime_panel",
      score_pct: pageScore,
      p0_count: p0,
      dominant_problem: compactText(primaryReco.problem || primaryReco.before, 220),
      top_recos: recos.map((r) => ({
        priority: r.priority,
        ice_score: Math.round(r.ice_score || 0),
        criterion_id: r.criterion_id,
        problem: compactText(r.problem || r.before, 220),
        action: safeAction(r, 320),
        rationale: compactText(r.why, 260),
        risk_flags: riskFlags(r),
        evidence_ids: r.evidence_ids,
      })),
    },
    deterministic_layout_plan: [
      {
        id: "hero",
        intent: "clarify promise, one primary CTA, visible proof, product-in-action visual",
        must_use: ["single H1", "one primary CTA", "one proof strip", "desktop and mobile screenshot awareness"],
        source_recos: recos.slice(0, 2).map((r) => r.criterion_id).filter(Boolean),
      },
      {
        id: "proof_stack",
        intent: "move trust signals above doubt, not decorative logo soup",
        must_use: ["specific numbers only if sourced", "named proof types", "no fake five-star badges"],
        source_recos: recos.filter((r) => /proof|social|trust|preuve|confiance/i.test(`${r.problem} ${r.after}`)).slice(0, 3).map((r) => r.criterion_id),
      },
      {
        id: "mechanism",
        intent: "explain why the offer works before feature grid",
        must_use: ["unique mechanism", "short scannable steps", "no generic feature cards"],
        source_recos: recos.filter((r) => /mechanism|mécanisme|how|comment|coh_09/i.test(`${r.criterion_id} ${r.problem} ${r.after}`)).slice(0, 3).map((r) => r.criterion_id),
      },
      {
        id: "objection_resolver",
        intent: "answer friction surfaced by audit before final CTA",
        must_use: ["pricing/integration/time/risk objections", "concrete reassurance", "supporting evidence"],
        source_recos: recos.filter((r) => /objection|friction|risk|risque|pricing|integration|validation/i.test(`${r.problem} ${r.after}`)).slice(0, 3).map((r) => r.criterion_id),
      },
      {
        id: "final_cta",
        intent: "repeat one action, no competing CTA cluster",
        must_use: ["same CTA contract as hero", "short reassurance", "no artificial urgency"],
        source_recos: recos.slice(0, 4).map((r) => r.criterion_id).filter(Boolean),
      },
    ],
    copy_contract: {
      target_language: "FR",
      h1_direction: "",
      primary_cta_label: `${ctaVerb} maintenant`,
      claims_policy: "Only use numbers already present in audit/reco/brand data. Otherwise phrase as qualitative.",
      forbidden: ["generic SaaS hero", "fake reviews", "countdown urgency", "full HTML polish by LLM"],
    },
    renderer_contract: {
      output: "controlled HTML sections",
      allowed_inputs: ["this brief", "brand_tokens", "selected screenshot paths", "manual offer overrides"],
      blocked_inputs: ["raw mega-prompt", "unbounded design grammar dump", "Reality metrics until configured"],
      post_run_judges: ["deterministic CTA/language/proof gates", "multi-judge optional post-run only"],
    },
  };
  brief.copy_contract.h1_direction = headlineDirection(brief);
  return brief;
}

function markdown(brief) {
  const lines = [];
  lines.push(`# Audit to GSG Brief — ${brief.audit_summary.client_name} / ${brief.source.page_type}`);
  lines.push("");
  lines.push(`Score: ${brief.audit_summary.score_pct}/100 · P0: ${brief.audit_summary.p0_count}`);
  lines.push(`URL: ${brief.source.page_url}`);
  lines.push("");
  lines.push("## Dominant Problem");
  lines.push(brief.audit_summary.dominant_problem || "No dominant problem.");
  lines.push("");
  lines.push("## Top Recos");
  brief.audit_summary.top_recos.slice(0, 6).forEach((r, i) => {
    lines.push(`${i + 1}. [${r.priority} · ICE ${r.ice_score}] ${r.problem}`);
    lines.push(`   Action: ${r.action}`);
  });
  lines.push("");
  lines.push("## Deterministic Layout");
  brief.deterministic_layout_plan.forEach((s) => {
    lines.push(`- ${s.id}: ${s.intent}`);
  });
  lines.push("");
  lines.push("## LLM Boundary");
  lines.push(brief.product_boundary.llm_scope);
  return `${lines.join("\n")}\n`;
}

function previewHtml(brief) {
  const color = brief.brand_tokens.primary_color || "#d7b46a";
  const secondary = brief.brand_tokens.secondary_colors?.[0] || "#0f766e";
  const recos = brief.audit_summary.top_recos.slice(0, 4);
  const proof = brief.audit_summary.top_recos.find((r) => /proof|preuve|trust|confiance|logo/i.test(`${r.problem} ${r.action}`));
  return `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>${brief.audit_summary.client_name} — GSG V27 Preview</title>
<style>
:root{--ink:#111318;--muted:#5c6472;--line:#dfe3ea;--bg:#f7f4ee;--surface:#fff;--brand:${color};--secondary:${secondary}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.5}a{color:inherit}
.shell{max-width:1180px;margin:0 auto;padding:28px}.nav{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:16px}.brand{font-weight:800;letter-spacing:.02em}.nav a{font-size:14px;color:var(--muted);text-decoration:none;margin-left:18px}.hero{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:44px;align-items:center;min-height:560px}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.14em;color:var(--secondary);font-weight:800}.h1{font-size:clamp(40px,6vw,76px);line-height:.95;letter-spacing:0;margin:18px 0 22px;font-weight:900;max-width:760px}.sub{font-size:19px;color:var(--muted);max-width:650px}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.btn{border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:6px;padding:14px 20px;font-weight:750;text-decoration:none}.btn.secondary{background:transparent;color:var(--ink)}.proof{display:flex;gap:18px;flex-wrap:wrap;margin-top:26px;font-size:13px;color:var(--muted)}.proof strong{color:var(--ink)}.visual{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:16px;box-shadow:0 18px 60px rgba(23,28,38,.12)}.visual img{display:block;width:100%;height:420px;object-fit:cover;object-position:top;border-radius:6px;border:1px solid var(--line)}.section{border-top:1px solid var(--line);padding:54px 0}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.item{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:18px}.item b{display:block;margin-bottom:8px}.item p{margin:0;color:var(--muted);font-size:14px}.final{background:var(--ink);color:#fff;border-radius:8px;padding:32px;display:flex;justify-content:space-between;gap:18px;align-items:center}.final p{margin:0;color:#c9ced8}@media(max-width:860px){.hero{grid-template-columns:1fr;min-height:auto;padding:42px 0}.visual img{height:320px}.grid{grid-template-columns:1fr}.final{display:block}.final .actions{margin-top:18px}}
</style>
</head>
<body>
<main class="shell">
<nav class="nav"><div class="brand">${brief.audit_summary.client_name}</div><div><a href="#proof">Preuves</a><a href="#mechanism">Mecanisme</a><a href="#cta">Action</a></div></nav>
<section class="hero">
<div>
<div class="eyebrow">Preview GSG V27 · structure deterministe</div>
<h1 class="h1">${brief.copy_contract.h1_direction || brief.audit_summary.dominant_problem}</h1>
<p class="sub">${brief.audit_summary.dominant_problem}</p>
<div class="actions"><a class="btn" href="#">${brief.copy_contract.primary_cta_label}</a><a class="btn secondary" href="#proof">Voir les preuves</a></div>
<div class="proof"><span><strong>Score audit</strong> ${brief.audit_summary.score_pct}/100</span><span><strong>P0</strong> ${brief.audit_summary.p0_count}</span><span><strong>Source</strong> GrowthCRO evidence-led</span></div>
</div>
<div class="visual">${brief.source.screenshot_desktop ? `<img src="${path.relative(path.join(ROOT, "deliverables", "gsg_demo"), path.join(ROOT, brief.source.screenshot_desktop.replace(/^\.\.\//, ""))).replaceAll(path.sep, "/")}" alt="Capture ${brief.audit_summary.client_name}"/>` : ""}</div>
</section>
<section class="section" id="proof"><div class="eyebrow">Trust stack</div><h2>La preuve remonte avant le doute.</h2><div class="grid">${recos.slice(0,3).map((r) => `<div class="item"><b>${r.criterion_id || r.priority}</b><p>${r.action || r.problem}</p></div>`).join("")}</div></section>
<section class="section" id="mechanism"><div class="eyebrow">Mechanism</div><h2>Le systeme explique pourquoi ca marche.</h2><div class="grid">${brief.deterministic_layout_plan.slice(1,4).map((s) => `<div class="item"><b>${s.id}</b><p>${s.intent}</p></div>`).join("")}</div></section>
<section class="section" id="cta"><div class="final"><div><h2>Une action principale, aucune dilution.</h2><p>${proof?.action || "Les preuves restent sourcees par l'audit, puis le LLM ne propose que des variantes de copy."}</p></div><div class="actions"><a class="btn" style="background:var(--brand);border-color:var(--brand);color:#111" href="#">${brief.copy_contract.primary_cta_label}</a></div></div></section>
</main>
</body>
</html>`;
}

const data = loadData();
const client = arg("client", "weglot");
const page = arg("page", "home");
const outDir = path.resolve(ROOT, arg("out-dir", "deliverables/gsg_demo"));
fs.mkdirSync(outDir, { recursive: true });

const brief = buildBrief(data, client, page);
const base = `${client}-${page}-gsg-v27`;
const jsonPath = path.join(outDir, `${base}.json`);
const mdPath = path.join(outDir, `${base}.md`);
const htmlPath = path.join(outDir, `${base}-preview.html`);

fs.writeFileSync(jsonPath, `${JSON.stringify(brief, null, 2)}\n`);
fs.writeFileSync(mdPath, markdown(brief));
fs.writeFileSync(htmlPath, previewHtml(brief));

console.log(`Brief: ${path.relative(ROOT, jsonPath)}`);
console.log(`Markdown: ${path.relative(ROOT, mdPath)}`);
console.log(`Preview: ${path.relative(ROOT, htmlPath)}`);
