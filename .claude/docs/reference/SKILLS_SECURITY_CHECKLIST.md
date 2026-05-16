# SKILLS_SECURITY_CHECKLIST.md

**Audit date :** 2026-05-16
**Source dossier :** `.claude/docs/state/AUDIT_DECISION_DOSSIER_2026-05-16_POST_PACK_GPT_PLUS_ADDENDUM.md` §5.7 + §6 P0.6
**Scope :** 18 skills externes installés via `skills-lock.json` (cf. `skills-lock.json` v1, 18 entrées). Trois sont en réalité du code Python local (`runtime_heuristic_python`) — l'audit factuel couvre quand même leur **source NPM/GitHub** car le code reste téléchargé sur disque (`~/Developer/growth-cro/.agents/skills/`).
**Auditeur :** Wave 3 Agent X (issue #46), méthode `static_grep` (lecture `SKILL.md` + grep des scripts).
**Décisions finales (DROP / PIN / KEEP) :** déferrées à **revue Mathis** post-Wave 3 — ce document **propose** et le registry `growthcro/SKILLS_REGISTRY_GOVERNANCE.json` stocke la proposition factuelle ; Mathis tranche dans un commit séparé `chore(skills): drop|pin|keep N external skills [#46 follow-up]`.

---

## Template de checklist (à appliquer avant tout futur ajout d'un skill externe)

```markdown
## Skill: <id>
Source: <github URL>
Version pin: <commit SHA ou tag>
Audit date: YYYY-MM-DD
Audit method: static_grep | dynamic_test | doc_only

### Static audit (lecture SKILL.md + grep scripts)
- [ ] Shell access (`subprocess`, `os.system`, `eval`, `exec`, `child_process`, `spawn`) : Y/N + détail (file:line)
- [ ] Network access (`http`, `urllib`, `requests`, `httpx`, `fetch`, `curl`, `wget`) : Y/N + détail
- [ ] .env reads (`os.environ`, `os.getenv`, `process.env`) : Y/N + détail
- [ ] Secrets access (API keys, tokens, cert files manipulés) : Y/N + détail
- [ ] Git operations (`git commit`, `git push`, `git branch`, `git reset`, `git checkout`) : Y/N + détail
- [ ] Filesystem : `read_only` | `read_write` | `none` + scope (paths concernés)
- [ ] Dynamic code execution (`exec`, `eval`, `__import__`, `Function()`, `vm.runInContext`) : Y/N + détail
- [ ] Remote content download (`curl | bash`, `npx <pkg>`, package download URL) : Y/N + URL
- [ ] Dependencies opaques non lockées (transitive deps non pinnées) : Y/N + détail

### Decision (Mathis tranche)
- [ ] KEEP (active in code, audité safe)
- [ ] PIN (dormant mais utilité future identifiée, commit SHA pinned pour reproductibilité)
- [ ] DROP (dormant + remplaçable + pas de plan d'utilisation 6 mois)

### Justification (1-2 lignes)
<free text>

### Notes additionnelles
<free text>
```

**Critères décision** (cf. `46.md` Technical Details) :
- **KEEP** : skill activement invoqué (Python ou Skill tool), audit clean.
- **PIN** : dormant mais utilité future identifiée par Mathis (commit SHA pinned pour reproductibilité — pas de drift silencieux upstream).
- **DROP** : dormant + remplaçable par doctrine projet + pas de plan d'utilisation 6 mois.

**Anti-pattern à éviter** (cf. CLAUDE.md §Anti-patterns #12) : charger >8 skills simultanés OU skills à signaux contraires en session.

---

## Audits rétroactifs (18 skills externes)

### A — Runtime heuristic Python (3) — invoqués comme fonctions Python locales, jamais via Skill tool

Pour les 3 skills suivants, **le code Python qui les implémente vit dans `moteur_gsg/core/` et est audité comme code projet** (couvert par `python3 scripts/lint_code_hygiene.py`). La source NPM/GitHub installée sous `.agents/skills/<id>/` peut être considérée comme inerte tant qu'aucun script de ce dossier n'est invoqué par le pipeline. Audit ci-dessous = audit de la source `.agents/skills/<id>/`.

---

#### Skill: impeccable
- **Source :** `pbakaus/impeccable` (skill original, runtime Python adapté localement)
- **Version pin :** computedHash `ada9c434…3735c8` (cf. `skills-lock.json`)
- **Audit date :** 2026-05-16
- **Audit method :** static_grep
- **Path on disk :** `.agents/skills/impeccable/` (61 fichiers, ~scripts/*.mjs + .js + .json + SKILL.md)
- **Runtime usage :** invoqué via `run_impeccable_qa(html)` dans `moteur_gsg/core/impeccable_qa.py:384` — **NPM scripts NON invoqués par notre pipeline**.

Static audit (sur `.agents/skills/impeccable/scripts/`) :
- Shell access : **Y** — `execSync` / `execFileSync` from `node:child_process` dans `live-poll.mjs:11`, `live.mjs:20`, `is-generated.mjs:16`
- Network access : **Y** — `fetch('http://localhost:${port}/...')` dans `live-complete.mjs:60`, `live-status.mjs:16`, `live-poll.mjs:37`, `live-browser.js:1841,2293,2620,2626,2653,2756`. Local-only (127.0.0.1).
- .env reads : **Y** — `process.env.IMPECCABLE_CONTEXT_DIR` (`load-context.mjs:48`), `process.env.IMPECCABLE_CRITIQUE_META` (`critique-storage.mjs:200`)
- Secrets access : **N** — `token` strings sont session-tokens HTTP locaux, pas des API keys distants
- Git operations : **N** — grep `git (commit|push|reset|branch|checkout|init)` = 0 hit
- Filesystem : **read_write** — scope `.agents/skills/impeccable/scripts/.tmp/`, `~/.impeccable/`, plus le projet courant (lecture/écriture HTML output via `live-inject.mjs`)
- Dynamic code execution : **N** (les `*.exec(...)` greppés sont du regex matching `.exec(string)`, pas `eval/exec` JS)
- Remote content download : **N** — pas de `curl|wget|npx` détecté dans `scripts/`
- Dependencies opaques : **N/A** (NPM scripts non invoqués)

**Mathis decision proposed : KEEP** (la source Python locale dans `moteur_gsg/core/impeccable_qa.py` est ce qui tourne, sûre). **NPM scripts dormants** — proposition : PIN sur commit SHA pour reproductibilité, ne pas autoriser invocation Skill tool sans audit additionnel.

---

#### Skill: cro-methodology
- **Source :** `wondelai/skills` (skill original markdown-only, runtime Python adapté localement)
- **Version pin :** computedHash `2ff15137…6783af` (cf. `skills-lock.json`)
- **Audit date :** 2026-05-16
- **Audit method :** static_grep
- **Path on disk :** `.agents/skills/cro-methodology/` (1 SKILL.md + 6 reference markdown — **aucun script exécutable**)
- **Runtime usage :** invoqué via `run_cro_methodology_audit(copy_doc, brief)` dans `moteur_gsg/core/cro_methodology_audit.py:233` — module docstring dit explicitement "honest runtime version".

Static audit (sur `.agents/skills/cro-methodology/`) :
- Shell access : **N** (doc-only)
- Network access : **N**
- .env reads : **N**
- Secrets access : **N**
- Git operations : **N**
- Filesystem : **read_only** (markdown lu par Skill tool si invoqué, jamais écrit)
- Dynamic code execution : **N**
- Remote content download : **N**
- Dependencies opaques : **N**

**Mathis decision proposed : KEEP** (source markdown sûre, code Python local couvert par lint hygiene).

---

#### Skill: emil-design-eng
- **Source :** `emilkowalski/skill` (skill original markdown-only, runtime Python adapté localement)
- **Version pin :** computedHash `8bdf9e4e…ca387d` (cf. `skills-lock.json`)
- **Audit date :** 2026-05-16
- **Audit method :** static_grep
- **Path on disk :** `.agents/skills/emil-design-eng/` (1 SKILL.md uniquement — **aucun script exécutable**)
- **Runtime usage :** invoqué via `run_emil_design_eng_audit(html)` dans `moteur_gsg/core/emil_design_eng_audit.py:130`.

Static audit (sur `.agents/skills/emil-design-eng/`) :
- Shell access : **N**
- Network access : **N**
- .env reads : **N**
- Secrets access : **N**
- Git operations : **N**
- Filesystem : **read_only**
- Dynamic code execution : **N**
- Remote content download : **N**
- Dependencies opaques : **N**

**Mathis decision proposed : KEEP** (source markdown sûre, code Python local couvert par lint hygiene).

---

### B — obra/superpowers, dormants doc-only (12) — markdown sans scripts

Les 12 skills suivants sont des **séquences de prompt / convention de session** sans scripts exécutables. Risk surface = nulle côté code, mais ils consomment du context window quand chargés par la session — donc audit factuel court, et décision essentiellement "DROP" si la doctrine projet remplit déjà la même fonction.

Pattern commun pour les 12 :
- Shell : **N** | Network : **N** | .env : **N** | Secrets : **N** | Git : **N** (sauf 2 cas signalés) | Filesystem : **read_only** | Dynamic code : **N** | Remote download : **N** | Deps opaques : **N**
- Pas de scripts dans le dossier `.agents/skills/<id>/` — uniquement `SKILL.md` (+ parfois 1-2 .md de référence)

---

#### Skill: brainstorming
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `8df9b470…c9cdb0`
- **Path on disk :** `.agents/skills/brainstorming/` (SKILL.md **+ scripts/server.cjs, helper.js, start-server.sh, stop-server.sh, frame-template.html**) — **EXCEPTION** : ce skill **a** des scripts (serveur local pour brainstorm UI).

Static audit (sur `.agents/skills/brainstorming/scripts/`) :
- Shell access : **N** (sauf `start-server.sh` / `stop-server.sh` qui exécutent `node server.cjs` — boundary scripts shell)
- Network access : **Y** — `server.cjs` démarre un HTTP server `http.createServer` lié à `127.0.0.1:PORT` (port aléatoire 49152-65535)
- .env reads : **Y** — `process.env.BRAINSTORM_PORT`, `BRAINSTORM_HOST`, `BRAINSTORM_URL_HOST`, `BRAINSTORM_DIR`, `BRAINSTORM_OWNER_PID`
- Secrets access : **N**
- Git operations : **N**
- Filesystem : **read_write** — scope `/tmp/brainstorm/` (sessions dir, override-able via `BRAINSTORM_DIR`)
- Dynamic code execution : **N**
- Remote content download : **N** (server.cjs sert localement uniquement)
- Dependencies opaques : **N** (vanilla Node stdlib `http`/`fs`/`path`)

**Mathis decision proposed : DROP** (notre doctrine projet `growthcro-anti-drift` + `growthcro-prd-planner` remplit la fonction de brainstorm structurée — pas besoin d'un serveur HTTP local). Si conservé, **PIN** sur SHA + ne pas démarrer le serveur automatiquement.

---

#### Skill: dispatching-parallel-agents
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `e21044ae…c769a0a`
- **Path on disk :** `.agents/skills/dispatching-parallel-agents/` (SKILL.md uniquement)
- Audit : N partout (doc-only).
- **Runtime usage :** utilisé implicitement en session lors des Wave 1/2/3 dispatch parallèle (TaskCreate). Pas d'invocation Python.

**Mathis decision proposed : KEEP** (utilisé activement en session, sûr car doc-only, ne consomme rien hors chargement context).

---

#### Skill: executing-plans
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `b41c919c…3cc4d7`
- **Path on disk :** `.agents/skills/executing-plans/` (SKILL.md uniquement)
- Audit : N partout (doc-only).
- **Runtime usage :** session-level lors de l'exécution de plans écrits.

**Mathis decision proposed : KEEP** (paire avec `writing-plans`, utilisé en session).

---

#### Skill: finishing-a-development-branch
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `932d23af…7179d19`
- **Path on disk :** `.agents/skills/finishing-a-development-branch/` (SKILL.md uniquement)
- Audit : N partout SAUF Git = **Y** (le skill enseigne `git merge|rebase|push` au LLM, exécutés par tool Bash en session) — Filesystem = **read_write** (commits, merges).
- **Runtime usage :** session-level lors des merges fin-de-wave.

**Mathis decision proposed : KEEP** (utile pour discipline merge fin-de-wave).

---

#### Skill: receiving-code-review
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `2760c85d…07274e30`
- **Path on disk :** `.agents/skills/receiving-code-review/` (SKILL.md uniquement)
- Audit : N partout (doc-only).

**Mathis decision proposed : DROP** (pas de PR review workflow GitHub actif sur ce repo — solo dev. Si Mathis ouvre un workflow PR review, ré-installer.)

---

#### Skill: requesting-code-review
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `874f3786…d12f0e67`
- **Path on disk :** `.agents/skills/requesting-code-review/` (SKILL.md + `code-reviewer.md` reference)
- Audit : N partout (doc-only).

**Mathis decision proposed : DROP** (idem : pas de workflow PR review actif. Si activé via /security-review natif Claude Code, c'est suffisant.)

---

#### Skill: subagent-driven-development
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `b38be2f3…c343b837`
- **Path on disk :** `.agents/skills/subagent-driven-development/` (SKILL.md + 3 prompt-templates .md)
- Audit : N partout (doc-only).
- **Runtime usage :** session-level quand orchestrator session spawn subagents (TaskCreate / Wave dispatching).

**Mathis decision proposed : KEEP** (utilisé dans cette session même, paire avec `dispatching-parallel-agents`).

---

#### Skill: systematic-debugging
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `7246fdd3…fdfb86488`
- **Path on disk :** `.agents/skills/systematic-debugging/` (SKILL.md + 8 reference .md + `condition-based-waiting-example.ts` + `find-polluter.sh`)
- Static audit (sur scripts) :
  - Shell : **Y** — `find-polluter.sh` est un bash script bisection (`set -e`, `find`, `git stash`).
  - Network : **N** | .env : **N** | Secrets : **N** | Git : **Y** (bisection via `git stash`/`git status`)
  - Filesystem : **read_write** (bisection touches test files temp). Scope : projet courant.
- **Runtime usage :** session-level (LLM lit SKILL.md, peut suggérer de lancer `find-polluter.sh`).

**Mathis decision proposed : KEEP** (script `find-polluter.sh` est manuellement invoqué, audit clean, contenu pédagogique sûr).

---

#### Skill: test-driven-development
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `126f1ebf…7eecd9f`
- **Path on disk :** `.agents/skills/test-driven-development/` (SKILL.md + `testing-anti-patterns.md`)
- Audit : N partout (doc-only).

**Mathis decision proposed : KEEP** (TDD est doctrine GrowthCRO — discipline session utile).

---

#### Skill: using-git-worktrees
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `bd10bc57…78e3b0a4ff`
- **Path on disk :** `.agents/skills/using-git-worktrees/` (SKILL.md uniquement)
- Audit : N partout SAUF Git = **Y** (le skill enseigne `git worktree add|remove`) — Filesystem = **read_write**.

**Mathis decision proposed : KEEP** (utilisé pour isolation feature work pendant Wave parallel dispatch).

---

#### Skill: using-superpowers
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `de10fd3f…cce4c5bb9`
- **Path on disk :** `.agents/skills/using-superpowers/` (SKILL.md + 3 reference platform-mapping .md)
- Audit : N partout (doc-only).
- **Runtime usage :** session-onboarding skill chargé au démarrage de chaque conversation par la harness. Router vers autres superpowers skills.

**Mathis decision proposed : KEEP** (chargé automatiquement, c'est le router des autres superpowers — si on garde >=1 superpower, on garde celui-ci).

---

#### Skill: verification-before-completion
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `9b446f0c…49a4a8ba`
- **Path on disk :** `.agents/skills/verification-before-completion/` (SKILL.md uniquement)
- Audit : N partout (doc-only).

**Mathis decision proposed : KEEP** (déjà partie de CLAUDE.md §Règles immuables : "Code hygiene gate" + "Schemas guard-rails" — superpower complète).

---

#### Skill: writing-plans
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `2b986445…d2719060`
- **Path on disk :** `.agents/skills/writing-plans/` (SKILL.md + `plan-document-reviewer-prompt.md`)
- Audit : N partout (doc-only).

**Mathis decision proposed : KEEP** (paire avec `executing-plans`).

---

#### Skill: writing-skills
- **Source :** `obra/superpowers`
- **Version pin :** computedHash `c0a92e62…485937c7`
- **Path on disk :** `.agents/skills/writing-skills/` (SKILL.md + 4 reference .md + `render-graphs.js` + `graphviz-conventions.dot` + `examples/CLAUDE_MD_TESTING.md`)
- Static audit (sur scripts) :
  - Shell : **Y** — `render-graphs.js` utilise `execSync(dot, ...)` pour appeler `graphviz` (binaire système).
  - Network : **N** | .env : **N** | Secrets : **N** | Git : **N**
  - Filesystem : **read_write** (lit SKILL.md, écrit `.svg` fichiers de diagrammes graphviz).
- **Runtime usage :** utilisé Wave 1 pour créer les 3 custom skills `growthcro-anti-drift`/`growthcro-prd-planner`/`growthcro-status-memory`.

**Mathis decision proposed : KEEP** (mais script `render-graphs.js` requiert binaire `graphviz` système — optionnel, ne casse pas l'install). Script est sûr (lecture markdown, écriture SVG).

---

### C — Externals avec scripts riches (3)

#### Skill: gstack
- **Source :** `garrytan/gstack`
- **Version pin :** computedHash `d6db3f49…f472b496e`
- **Audit date :** 2026-05-16
- **Audit method :** static_grep
- **Path on disk :** `.agents/skills/gstack/` (**768 fichiers** : headless browser CLI + Chrome extension + tests + scripts TypeScript)
- **Runtime usage :** **dormant** — install reported failed 2026-05-14, 0 invocation Python détectée.

Static audit (sur `.agents/skills/gstack/`) :
- Shell access : **Y** — `child_process` partout : `execSync` dans `scripts/dev-skill.ts:11`, `scripts/host-config-export.ts:18`, `scripts/skill-check.ts:15` ; `spawnSync` dans `scripts/test-free-shards.ts:29`, `scripts/slop-diff.ts:14`. `package.json` scripts utilisent `bun build`, `bun test`, `bash browse/scripts/build-node-server.sh`, `chmod +x`.
- Network access : **Y** — dependency `@ngrok/ngrok` (tunnel HTTP/TCP), `playwright` (browser controller), `@huggingface/transformers` (ML model download). `setup-scc.sh` télécharge binaires (Homebrew + GitHub releases).
- .env reads : **Y** — `process.env.ANTHROPIC_API_KEY` lu dans `scripts/preflight-agent-sdk.ts:56` (et transmis dans `env: { ANTHROPIC_API_KEY: ... }` à un subprocess).
- Secrets access : **Y CRITIQUE** — manipule explicitement `ANTHROPIC_API_KEY` pour lancer une live query. Skill peut leak la clé si subprocess est mal isolé.
- Git operations : **Y** — `spawnSync("git", ["diff", ...])`, `spawnSync("git", ["merge-base", ...])` dans `scripts/slop-diff.ts:22,54`. Pas de write detected.
- Filesystem : **read_write** — scope projet courant (`browse/dist/`, `chmod +x`, `rm -f`) + `~/.gstack/sessions/`, `~/.gstack/.proactive-prompted` + `node_modules/`
- Dynamic code execution : **N** détecté (mais `bun` build dynamically loads TS)
- Remote content download : **Y** — `setup-scc.sh` télécharge depuis `https://github.com/boyter/scc/releases` (binaire prébuilt), `slop-diff.ts` lance `npx slop-scan` (download NPM package on-the-fly).
- Dependencies opaques : **Y** — `package.json` use `^` minor-flexible versions (`@huggingface/transformers ^4.1.0`, `@ngrok/ngrok ^1.7.0`, `playwright ^1.58.2`, `marked ^18.0.2`).

**Mathis decision proposed : DROP** (déjà recommandé dans `AUDIT_DECISION_DOSSIER §5.7` : "Réinstaller gstack sans audit sécurité" listé comme anti-pattern). Combo `shell + network + ANTHROPIC_API_KEY + remote download + unpinned deps` = **risque critique** pour un skill dormant. **Si jamais rebesoin** : ré-installer avec audit + `^` deps remplacés par exact pins + env isolation.

---

#### Skill: brainstorming
*(déjà audité section B — exception parmi les superpowers à cause de son serveur HTTP local)*

---

#### Skill: impeccable
*(déjà audité section A — runtime_heuristic_python mais NPM source a 61 fichiers avec scripts riches, audit fait là-haut)*

---

## Récap factuel et propositions de décision

| Skill | Type registry | Audit findings | Mathis decision proposed |
|---|---|---|---|
| impeccable | runtime_heuristic_python | NPM scripts: shell+network local+env+fs read_write — non invoqués par pipeline | **KEEP** (Python local) ; **PIN** NPM source |
| cro-methodology | runtime_heuristic_python | Doc-only markdown | **KEEP** |
| emil-design-eng | runtime_heuristic_python | Doc-only markdown | **KEEP** |
| brainstorming | installed_external_dormant | Serveur HTTP local 127.0.0.1 + env vars `BRAINSTORM_*` + fs `/tmp/brainstorm/` | **DROP** (remplaçable par `growthcro-prd-planner`) |
| dispatching-parallel-agents | installed_external_dormant | Doc-only | **KEEP** (utilisé en Wave dispatching) |
| executing-plans | installed_external_dormant | Doc-only | **KEEP** (paire avec writing-plans) |
| finishing-a-development-branch | installed_external_dormant | Doc-only, enseigne git merge | **KEEP** (discipline fin-de-wave) |
| gstack | installed_external_dormant | shell + network + ANTHROPIC_API_KEY + remote DL + unpinned deps | **DROP CRITIQUE** |
| receiving-code-review | installed_external_dormant | Doc-only | **DROP** (pas de PR review workflow actif) |
| requesting-code-review | installed_external_dormant | Doc-only | **DROP** (idem) |
| subagent-driven-development | installed_external_dormant | Doc-only | **KEEP** (utilisé en Wave dispatch) |
| systematic-debugging | installed_external_dormant | `find-polluter.sh` bash sûr + `git stash` | **KEEP** |
| test-driven-development | installed_external_dormant | Doc-only | **KEEP** (TDD = doctrine) |
| using-git-worktrees | installed_external_dormant | Doc-only, enseigne git worktree | **KEEP** |
| using-superpowers | installed_external_dormant | Doc-only (router) | **KEEP** (si >=1 superpower conservé) |
| verification-before-completion | installed_external_dormant | Doc-only | **KEEP** (déjà dans CLAUDE.md) |
| writing-plans | installed_external_dormant | Doc-only | **KEEP** (paire avec executing-plans) |
| writing-skills | installed_external_dormant | `render-graphs.js` execSync graphviz — sûr | **KEEP** |

**Résumé chiffré (propositions à valider par Mathis) :**
- KEEP : 13 skills (3 runtime_heuristic + 10 superpowers utiles : dispatching/executing/finishing/subagent/systematic/test-driven/using-git-worktrees/using-superpowers/verification/writing-plans/writing-skills, +impeccable Python)
- DROP : 4 skills (brainstorming, receiving-code-review, requesting-code-review, gstack)
- PIN : 1 skill (impeccable NPM source — Python local reste KEEP)

---

## Critical findings (Mathis attention)

1. **`gstack`** — combo dangereux `shell + network + lecture ANTHROPIC_API_KEY + remote download + deps non pinnées`. Recommandation : **DROP immédiat** (et purger `node_modules/` sous `.agents/skills/gstack/`). Si re-installation souhaitée plus tard, exiger : (a) exact pin sur toutes les deps, (b) sandbox subprocess, (c) audit dynamic_test (pas juste static_grep).
2. **Aucun secret exposé en clair** détecté dans les sources des 18 skills audités. Pas de fichier `.env`, pas de hardcoded API key. ✅
3. **brainstorming** — sert un HTTP server local : risque faible mais inutile vu notre stack (`growthcro-prd-planner` + `growthcro-anti-drift` couvrent l'usage).
4. **impeccable NPM source** — pas invoquée par notre pipeline, mais 61 fichiers + child_process + browser fetch = surface non négligeable si jamais on switch vers le mode Skill tool. Garder le code Python local et **PIN** la version NPM (pas de mise à jour auto).

---

## Procédure pour Mathis (post-Wave 3)

1. Reviewer ce document.
2. Pour chaque skill marqué DROP, valider et commit séparé :
   ```bash
   # Exemple si Mathis valide DROP brainstorming + receiving-code-review + requesting-code-review + gstack :
   # 1. Retirer 4 entrées de skills-lock.json
   # 2. Optionnel : rm -rf .agents/skills/brainstorming .agents/skills/receiving-code-review .agents/skills/requesting-code-review .agents/skills/gstack
   # 3. Optionnel : retirer les 4 entrées de growthcro/SKILLS_REGISTRY_GOVERNANCE.json ou les marquer "type": "archived"
   git add skills-lock.json growthcro/SKILLS_REGISTRY_GOVERNANCE.json
   git commit -m "chore(skills): drop 4 dormant external skills per audit [#46 follow-up]"
   ```
3. Pour skills marqués PIN, vérifier que `skills-lock.json` contient un commit SHA explicite (déjà le cas via `computedHash`).
4. Pour skills marqués KEEP, RAS — rester en l'état.
5. Ajouter dans `.claude/CLAUDE.md` §Anti-patterns une 13e règle : "Avant d'installer un skill externe, exécuter `SKILLS_SECURITY_CHECKLIST.md` template + remplir entrée dans `SKILLS_REGISTRY_GOVERNANCE.json` (audit + décision documentée)". Ce changement est laissé à confirmation explicite Mathis (out-of-scope agent dispatch).

---

## Méthodologie audit (pour replay)

```bash
# 1. Lister scripts par skill
SKILLS_DIR=~/Developer/growth-cro/.agents/skills
for skill in $(ls $SKILLS_DIR); do
  echo "=== $skill ==="
  find $SKILLS_DIR/$skill -type f \( -name "*.py" -o -name "*.sh" -o -name "*.js" -o -name "*.ts" -o -name "*.mjs" -o -name "*.cjs" \)
done

# 2. Grep patterns dangereux par skill
grep -rnE "subprocess|os\.system|eval\(|exec\(|urllib|requests\.|httpx|fetch\(|child_process|spawn|process\.env|os\.environ|os\.getenv|curl |wget |npx |\\bgit\\s+(commit|push|reset|branch|checkout)" $SKILLS_DIR/<skill>/

# 3. Vérifier secrets / API keys
grep -rnE "API_KEY|api_key|TOKEN|SECRET|password|credential" $SKILLS_DIR/<skill>/

# 4. Vérifier deps non pinnées
cat $SKILLS_DIR/<skill>/package.json | jq '.dependencies, .devDependencies'
```

**Audit method retenue pour les 18** : `static_grep` (suffisant pour décision DROP/PIN/KEEP). Pour passer en mode **production-grade** (ex: ré-activer gstack), exiger `dynamic_test` : sandbox VM + monitoring syscalls + audit network egress.
