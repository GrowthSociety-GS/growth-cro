# Webapp Architecture Map — V1 (2026-05-11)

**Companion to `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`.**

The YAML is the machine-readable source of truth (auto-refreshed by
`scripts/update_architecture_map.py`). This Markdown file gives a human reader
six Mermaid views that cover the whole program in ten minutes. The two are
intentionally kept in sync via the same regen script (see footer).

Conventions:
- Each Mermaid block is followed by 1-2 paragraphs explaining what the
  diagram means and where it lives in the YAML.
- Module names match the YAML keys (`growthcro/capture/scorer`,
  `moteur_gsg/core/visual_system`, …).
- Yellow-tagged nodes are upcoming work (V28 Next.js, Reality Loop with real
  credentials, V3.3 doctrine fusion). Everything else is on disk today.

---

## 1. Global view — the whole program in one diagram

```mermaid
flowchart TD
    subgraph Onboarding["Onboarding & Intake"]
        AddClient["growthcro/cli/add_client<br/>add slug + URL"]
        Discovery["growthcro/research/discovery<br/>+ skills/discover_pages_v25"]
        Intake["moteur_gsg/core/intake_wizard"]
    end

    subgraph Audit["Audit Engine (growthcro/*)"]
        Capture["capture/<br/>scorer · orchestrator · persist"]
        Perception["perception/<br/>heuristics · vision · intent"]
        Scoring["scoring/<br/>pillars · ux · specific/{listicle,product,sales,home_leadgen}"]
        Recos["recos/<br/>schema · prompts · client · orchestrator"]
    end

    subgraph GSG["GSG Engine (moteur_gsg/* V27.2-G)"]
        BriefV2["core/brief_v2 + prefiller + validator"]
        Contracts["core/{context_pack,doctrine_planner,visual_intelligence}"]
        Routes["core/creative_route_selector V27.2-F<br/>+ visual_system V27.2-G"]
        Planner["core/{planner,component_library,pattern_library,design_tokens}"]
        Copy["core/copy_writer<br/>(JSON slots only)"]
        Renderer["core/page_renderer_orchestrator<br/>+ section/hero/component renderers"]
        Modes["modes/{1,2,3,4,5}"]
        ModeOrch["moteur_gsg/orchestrator<br/>(canonical public API)"]
    end

    subgraph QA["QA / Multi-Judge"]
        Doctrine["judges/doctrine_judge V3.2.1<br/>(54 critères + 6 killers)"]
        Humanlike["judges/humanlike_judge<br/>(8 dimensions)"]
        ImplCheck["judges/implementation_check<br/>(runtime bug detection)"]
        MJOrch["moteur_multi_judge/orchestrator<br/>(70/30 weighting)"]
    end

    subgraph Webapp["Webapp Surface"]
        APIServer["growthcro/api/server<br/>FastAPI"]
        V27HTML["deliverables/GrowthCRO-V27-CommandCenter.html<br/>+ growth_audit_data.js (12MB)"]
        V28Next["Webapp V28 Next.js<br/>(Epic #6 target)"]:::pending
    end

    subgraph Loop["Reality / Experiment / Learning"]
        EvidenceLedger["skills/evidence_ledger"]
        V29Learn["skills/learning_layer_v29_audit_based<br/>(69 proposals)"]
        Experiment["skills/experiment_engine<br/>(A/B + sample size)"]
        Reality["Reality Layer<br/>(GA4/Meta/Google credentials)"]:::pending
        V30Bayes["Learning V30 Bayesian<br/>(data-driven)"]:::pending
    end

    subgraph Infra["Infrastructure & Gates"]
        Config["growthcro/config<br/>(env-var boundary)"]
        AnthropicLib["growthcro/lib/anthropic_client"]
        Lint["scripts/lint_code_hygiene"]
        Capabilities["scripts/audit_capabilities"]
        Schemas["SCHEMA/validate_all"]
        ArchMap["scripts/update_architecture_map<br/>(THIS REGEN)"]
    end

    AddClient --> Discovery --> Capture --> Perception --> Scoring --> Recos
    Recos --> EvidenceLedger
    EvidenceLedger --> V27HTML
    Capture -.brand_dna.-> Contracts
    Recos -.audit.-> BriefV2

    Intake --> BriefV2 --> Contracts --> Routes --> Planner
    Planner --> Copy --> Renderer
    Planner --> Modes
    Modes --> ModeOrch
    ModeOrch --> Renderer
    Renderer --> MJOrch
    MJOrch --> Doctrine
    MJOrch --> Humanlike
    MJOrch --> ImplCheck

    APIServer --> V27HTML
    APIServer -.target.-> V28Next
    Recos --> V29Learn
    V29Learn -.proposals.-> Reality
    Reality -.metrics.-> Experiment
    Experiment -.results.-> V30Bayes

    Config --- AnthropicLib
    Lint --- Capabilities
    Schemas --- ArchMap

    classDef pending fill:#fff7d6,stroke:#d4a017,color:#5d4309,stroke-dasharray:5 3;
```

**What this shows.** The five horizontal bands map 1:1 to the eight YAML
`pipelines:` block + the infrastructure bag. Solid arrows = wired in code
today; dashed arrows = data hand-offs through disk artefacts; dashed nodes
(`Reality Layer`, `V28 Next.js`, `Learning V30`) are next-epic work but
already have placeholder entries in the YAML. The infra band at the bottom
holds the four non-pipeline gates that every conversation must call
(`config`, `anthropic_client`, `lint`, `audit_capabilities`, `SCHEMA`,
this regen script).

**What it omits on purpose.** Internal module-to-module imports are in the
YAML `depends_on` / `imported_by` fields; surfacing them here would make the
diagram unreadable. Use the YAML for graph queries.

---

## 2. Audit pipeline — capture to reco

```mermaid
flowchart TD
    Start([client URL + slug]) --> Add["growthcro/cli/add_client<br/>data/clients_database.json"]
    Add --> Enrich["growthcro/cli/enrich_client<br/>+ research/discovery"]
    Enrich --> DiscoverArt[("data/captures/&lt;client&gt;/<br/>discovered_pages_v25.json")]
    DiscoverArt --> CaptureCli["growthcro/cli/capture_full"]
    CaptureCli --> CaptureOrch["growthcro/capture/orchestrator<br/>+ browser + cloud + dom"]
    CaptureOrch --> CaptureArt[("data/captures/&lt;client&gt;/&lt;page&gt;/<br/>{capture.json, spatial_v9.json, page.html, screenshots/}")]
    CaptureArt --> Scorer["growthcro/capture/scorer<br/>+ signals"]
    Scorer -.refines.-> CaptureArt
    CaptureArt --> PerceptionPersist["growthcro/perception/persist<br/>+ heuristics + vision + intent"]
    PerceptionPersist --> PerceptionArt[("perception_v13.json<br/>SCHEMA validated")]
    PerceptionArt --> ScoringPersist["growthcro/scoring/persist<br/>+ pillars + ux"]
    PerceptionArt --> ScoringSpecific["growthcro/scoring/specific/<br/>{listicle,product,sales,home_leadgen}"]
    ScoringPersist --> ScoreArt[("score_{hero,persuasion,ux,coherence,psycho,tech}.json<br/>+ score_page_type.json<br/>SCHEMA validated")]
    ScoringSpecific --> ScoreArt
    ScoreArt --> Evidence["skills/evidence_ledger"]
    Evidence --> EvidenceArt[("evidence_ledger.json<br/>per-criterion provenance")]
    ScoreArt --> RecosOrch["growthcro/recos/orchestrator<br/>+ schema + prompts + client"]
    EvidenceArt --> RecosOrch
    RecosOrch --> Anthropic["growthcro/lib/anthropic_client<br/>(Sonnet 4.5)"]
    Anthropic --> RecosOrch
    RecosOrch --> RecosArt[("recos_enriched.json<br/>SCHEMA validated")]
    RecosArt --> Lifecycle["skills/reco_lifecycle"]
    Lifecycle --> DashJS[("deliverables/growth_audit_data.js<br/>12 MB · 56 clients · 185 pages")]

    classDef artefact fill:#e8f4ff,stroke:#3a73b0,color:#0c2a4c;
    class DiscoverArt,CaptureArt,PerceptionArt,ScoreArt,EvidenceArt,RecosArt,DashJS artefact;
```

**What this shows.** The canonical audit pipeline as it lives on `main`
post-cleanup. Each blue node is a JSON / JS artefact persisted on disk; every
green node is a Python module from the `growthcro/` package. The orchestrator
respects Rule 4 of the code doctrine (one concern per file) — capture is split
across `browser`/`cloud`/`dom`/`orchestrator`/`scorer`/`signals`, perception
fans out into `heuristics`/`vision`/`intent`/`persist`, and scoring splits
by pillar (`pillars` + `ux`) plus page-type-specific detectors.

**Why it matters.** Every audit run produces exactly this artefact tree, and
every downstream consumer (V27 HTML dashboard, GSG context pack, V29 learning
loop) reads from these JSONs — no shadow store. SCHEMA validation gates run
at `perception_v13`, `score_pillar`, `score_page_type`, `recos_enriched`.

---

## 3. GSG pipeline — V27.2-G controlled path

```mermaid
flowchart TD
    Raw([raw user request]) --> Intake["core/intake_wizard<br/>V27.2-E"]
    Intake --> BriefBuilder["core/brief_v2<br/>+ prefiller + validator"]
    Brief[("data/_briefs_v2/<br/>&lt;timestamp&gt;_&lt;client&gt;_&lt;page&gt;.json")]
    BriefBuilder --> Brief
    Brief --> ContextPack["core/context_pack<br/>(brand_dna + audience + proof + scent)"]
    Brief --> DoctrinePack["core/doctrine_planner<br/>DoctrineCreationContract"]
    ContextPack --> VisualInt["core/visual_intelligence<br/>VisualIntelligencePack"]
    DoctrinePack --> VisualInt
    VisualInt --> RouteSelector["core/creative_route_selector<br/>V27.2-F structured"]
    RouteSelector --> AURA["AURA tokens<br/>(legacy_lab_adapters)"]
    RouteSelector --> GoldenBridge["Golden Bridge<br/>(legacy_lab_adapters)"]
    AURA --> RouteSelector
    GoldenBridge --> RouteSelector
    RouteSelector --> VisualSystem["core/visual_system<br/>V27.2-G premium layer"]
    VisualSystem --> Tokens["core/design_tokens<br/>+ design_grammar_loader"]
    Tokens --> Planner["core/planner<br/>+ component_library + pattern_library"]
    Planner --> Plan[("page plan<br/>sections + components + evidence pack")]
    Plan --> CopyWriter["core/copy_writer<br/>Sonnet → JSON copy slots only"]
    Plan --> Renderer["core/page_renderer_orchestrator<br/>+ hero/section/component renderers"]
    CopyWriter --> Renderer
    Renderer --> CSS["core/css/{base, components, responsive}"]
    CSS --> Renderer
    Renderer --> RuntimeFixes["modes/mode_1/runtime_fixes"]
    RuntimeFixes --> VisualGates["modes/mode_1/visual_gates<br/>anti-AI-slop"]
    VisualGates --> MinimalGuards["core/minimal_guards"]
    MinimalGuards --> HTML[("LP HTML<br/>deliverables/&lt;client&gt;-&lt;page&gt;-GSG-V27-2G.html")]
    HTML --> MJOpt{{"optional multi-judge<br/>(see §4)"}}

    classDef artefact fill:#e8f4ff,stroke:#3a73b0,color:#0c2a4c;
    classDef gate fill:#fef3e7,stroke:#cc7d28,color:#5a3208;
    class Brief,Plan,HTML artefact;
    class RuntimeFixes,VisualGates,MinimalGuards gate;
```

**What this shows.** The full canonical Mode 1 COMPLETE path on V27.2-G. The
LLM only writes copy as JSON slots (Sonnet text-only via `core/copy_writer`);
all visuals, structure, tokens, and CSS are deterministic. The premium visual
layer markers (`gsg-visual-system-v27.2-g`, `gsg-premium-visual-layer-v27.2-g`)
are emitted by `visual_system.py` and asserted by
`scripts/check_gsg_creative_route_selector.py` + `check_gsg_visual_renderer.py`
(see Codex handoff 2026-05-11 P1 fix).

**Mode dispatch.** Modes 2-5 share most of this pipeline; the differences live
in `mode_{2,3,4,5}*.py`:
- Mode 2 REPLACE — consumes audit V26 output for comparative refonte (the only mode that *requires* an audit).
- Mode 3 EXTEND — reuses existing `brand_dna` to add a new concept on a known site.
- Mode 4 ELEVATE — challenger DA seeded by inspiration URLs.
- Mode 5 GENESIS — brief-only, no live site.

The public entrypoint for any mode is `moteur_gsg/orchestrator.py`.

---

## 4. Multi-Judge — post-render QA layer

```mermaid
flowchart TD
    LP([rendered LP HTML]) --> Orch["moteur_multi_judge/orchestrator<br/>V26.AA Sprint 3"]
    Orch -->|70% weight| Doctrine["judges/doctrine_judge<br/>V3.2.1 — 54 critères + 6 killers"]
    Orch -->|30% weight| Humanlike["judges/humanlike_judge<br/>wraps skills/gsg_humanlike_audit<br/>(8 dimensions)"]
    Orch --> ImplCheck["judges/implementation_check<br/>wraps skills/fix_html_runtime<br/>(runtime bug detection)"]

    Doctrine --> DScore[("doctrine_score<br/>+ per-criterion verdicts")]
    Humanlike --> HScore[("humanlike_score<br/>+ 8-dim breakdown")]
    ImplCheck --> Bugs[("implementation_bugs<br/>(JS runtime errors, broken counters, …)")]

    DScore --> Aggregator["weighted aggregation<br/>70/30 + killer veto"]
    HScore --> Aggregator
    Bugs --> Aggregator
    Aggregator --> FinalReport[("data/_pipeline_runs/&lt;run&gt;/multi_judge.json<br/>final_score_pct + breakdown")]
    FinalReport --> Decision{{"final_score_pct ≥ 70<br/>+ killers = 0?"}}
    Decision -->|YES| Ship([Ship — Weglot V27.2-D baseline: 70.9])
    Decision -->|NO| Repair["growthcro/gsg_lp/repair_loop<br/>(legacy lab)"]
    Repair -.iterate.-> LP

    classDef artefact fill:#e8f4ff,stroke:#3a73b0,color:#0c2a4c;
    class DScore,HScore,Bugs,FinalReport artefact;
```

**What this shows.** The three-judge fan-out + 70/30 doctrine/humanlike
weighting + killer-rule veto. The Doctrine Judge consumes the SAME
`playbook/bloc_{1..6}_v3.json` files as the audit scorer — that's the
"racine partagée" insight from V26.AA. The Humanlike Judge and
Implementation Check are wrappers around legacy `skills/growth-site-generator`
scripts kept in production because they work; refactoring them into
`moteur_multi_judge/judges/*.py` is out of scope until they evolve.

**When it runs.** Multi-judge is *post-render QA*, not a blocking generation
gate. The GSG can ship without it (lite mode); enabling it adds ~5 minutes
per LP. The legacy `growthcro/gsg_lp/repair_loop.py` iterates the multi-judge
output back into the renderer; in the canonical V27.2-G path the loop is
replaced by `moteur_gsg/core/minimal_guards.py` which is deterministic and
non-iterative.

---

## 5. Webapp — V27 HTML today, V28 Next.js target

```mermaid
flowchart TD
    subgraph V27["V27 HTML (active, 56 clients)"]
        AuditPipe["audit pipeline §2<br/>(56 clients × 185 pages)"] --> CaptureTree[("data/captures/&lt;client&gt;/&lt;page&gt;/*<br/>~150 artefacts/page")]
        CaptureTree --> Builder["skills/build_growth_audit_data<br/>(consolidates the tree)"]
        Builder --> DashJS[("deliverables/growth_audit_data.js<br/>12 MB consolidated bundle")]
        DashJS --> CommandCenter[/"deliverables/GrowthCRO-V27-CommandCenter.html<br/>11 panes: Audit / Reco / GSG / …"/]
        APIv1["growthcro/api/server<br/>FastAPI"] -.programmatic.-> CommandCenter
    end

    subgraph V28["V28 Next.js (target, Epic #6)"]
        SupabaseAuth["Supabase EU<br/>auth + tables clients/audits/recos/runs"]:::pending
        APIv2["growthcro/api/server<br/>via Vercel edge functions"]:::pending
        MFAudit["audit-app microfrontend"]:::pending
        MFReco["reco-app microfrontend"]:::pending
        MFGSG["gsg-studio microfrontend"]:::pending
        MFReality["reality-monitor microfrontend"]:::pending
        MFLearn["learning-lab microfrontend"]:::pending
        VercelMF["vercel-microfrontends<br/>routing"]:::pending

        SupabaseAuth --> MFAudit
        SupabaseAuth --> MFReco
        APIv2 --> MFAudit
        APIv2 --> MFReco
        APIv2 --> MFGSG
        APIv2 --> MFReality
        APIv2 --> MFLearn
        VercelMF --> MFAudit
        VercelMF --> MFReco
        VercelMF --> MFGSG
        VercelMF --> MFReality
        VercelMF --> MFLearn
    end

    AuditPipe -.same data tree.-> APIv2

    classDef pending fill:#fff7d6,stroke:#d4a017,color:#5d4309,stroke-dasharray:5 3;
```

**What this shows.** V27 (today) is a single 12 MB `growth_audit_data.js`
bundle consumed by a static HTML Command Center — works for 56 clients but
won't scale to 100+. V28 (Epic #6 target) is a Next.js 14 monorepo with
five microfrontends, Supabase auth + tables, and the same FastAPI server
exposed as Vercel edge functions. The audit pipeline data tree is the
shared bus — both V27 HTML and V28 Next.js read from it without changes.

**Migration strategy.** V27 stays live during the entire V28 build (Epic #6
strategy AD-6). The migration is microfrontend-by-microfrontend, never a
big-bang flip. The legacy `build_growth_audit_data.py` god file is in
`KNOWN_DEBT` (803 LOC) and will be split as part of Epic #5.

---

## 6. Reality / Experiment / Learning loop

```mermaid
flowchart TD
    AuditFleet["56 audits sur disque<br/>data/captures/*"] --> V29Learn["skills/learning_layer_v29_audit_based"]
    V29Learn --> Proposals[("data/learning/audit_based_proposals/<br/>69 proposals V29")]
    Proposals --> Review{{"Mathis review<br/>accept / reject / defer"}}
    Review -->|accept| V33[("playbook/bloc_*_v3-3.json<br/>doctrine V3.3 CRE fusion")]:::pending
    Review -->|reject| Discard([discard])
    Review -->|defer| ProposalsQueue([backlog])

    subgraph Reality["Reality Layer (pending credentials)"]
        GA4["GA4 API"]:::pending
        Meta["Meta Ads API"]:::pending
        Google["Google Ads API"]:::pending
        Shopify["Shopify API"]:::pending
        Clarity["Microsoft Clarity"]:::pending
    end

    GA4 --> RealityCollector["Reality collector<br/>(orchestrator V26.AI dry-run OK)"]:::pending
    Meta --> RealityCollector
    Google --> RealityCollector
    Shopify --> RealityCollector
    Clarity --> RealityCollector
    RealityCollector --> RealityData[("data/reality/&lt;client&gt;/*.json<br/>real-world metrics")]:::pending

    Recos["growthcro/recos/orchestrator<br/>recos_enriched"] --> Experiment["skills/experiment_engine<br/>A/B specs + sample size + guardrails"]
    Experiment --> ABSpec[("A/B test specs<br/>(5 target on 3 pilot clients)")]:::pending
    ABSpec --> RealityCollector
    RealityData --> V30Bayes["Learning V30 Bayesian update<br/>(data-driven, not audit-based)"]:::pending
    V30Bayes --> DataProposals[("data-driven doctrine proposals<br/>(target: ≥10 by Q4)")]:::pending
    DataProposals --> Review
    V33 --> AuditEngine["audit engine consumes new doctrine<br/>(56 clients stay on V3.2.1 until next audit)"]

    classDef pending fill:#fff7d6,stroke:#d4a017,color:#5d4309,stroke-dasharray:5 3;
```

**What this shows.** The full closed loop from audit → action → measurement
→ learning → doctrine update → next audit. V29 (audit-based learning) is
ACTIVE today and has generated 69 proposals; V30 (data-driven Bayesian) is
PENDING because the Reality Layer needs credentials on 3 pilot clients
(Epic #8, FR-8). The 69 V29 proposals queue feeds Epic #3 (doctrine V3.3
CRE fusion) — that's the "K mutualisé" remark in the epic doc.

**Status today.** Out of the 7-stage loop, stages 1-3 (audit fleet, V29
extraction, 69 proposals) are wired and producing artefacts. Stages 4-7
(Reality collect, Experiment Engine A/B, V30 Bayesian, doctrine V3.4)
require Mathis to collect credentials on 3 pilot clients + 5 measured A/Bs;
the orchestrator skeleton runs in dry-run mode without raising.

---

## Cross-references

- Machine-readable YAML: `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`
- Auto-regen script: `scripts/update_architecture_map.py`
- Code doctrine: `.claude/docs/doctrine/CODE_DOCTRINE.md`
- Architecture snapshot post-cleanup: `.claude/docs/state/ARCHITECTURE_SNAPSHOT_POST_CLEANUP_2026-05-11.md`
- Codex GSG handoff (V27.2-G alignment): `.claude/docs/state/CODEX_TO_CLAUDE_GSG_ALIGNMENT_HANDOFF_2026-05-11.md`
- Epic technique: `.claude/epics/webapp-stratosphere/epic.md`
- PRD master: `.claude/prds/webapp-stratosphere.md` (FR-1 / US-1)

---

**Last regen**: see `meta.generated_at` in the YAML.

**To regenerate** (after merging an epic that adds / moves / deletes modules):

```bash
python3 scripts/update_architecture_map.py
```

The script is idempotent and preserves human-curated `purpose` / `inputs` /
`outputs` / `doctrine_refs` / `status` / `lifecycle_phase` fields. Only
`path`, `depends_on`, `imported_by`, and the `meta.generated_at` /
`meta.source_commit` are refreshed on every run.
