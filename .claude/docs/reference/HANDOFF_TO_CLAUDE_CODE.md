# HANDOFF — GrowthCRO vers Claude Code

**Date** : 2026-04-19 · **Contexte** : transition CoWork → Claude Code pour reprise du projet avec Claude Code natif.

Ce document est ta checklist de démarrage. Suis-la pas à pas dans ton terminal. Claude Code lira ensuite `CLAUDE.md` et démarrera correctement.

---

## 1. Rotation des clés API (à faire AVANT toute exécution)

Les clés API ont été trouvées en clair dans `WAKE_UP_NOTE_2026-04-18.md` et `WAKE_UP_NOTE_2026-04-19.md` lors du P10 (2026-04-19). Elles ont été redactées dans les fichiers, mais elles ont été visibles de plusieurs sessions LLM et doivent être considérées compromises.

- **Anthropic** : https://console.anthropic.com/settings/keys → révoque l'ancienne, génère une nouvelle, remplace dans `.env`.
- **Apify** (si encore utilisé) : https://console.apify.com/account/integrations → révoque et regénère.

---

## 2. Installer Claude Code (si pas déjà fait)

```bash
# macOS
npm install -g @anthropic-ai/claude-code
# ou
brew install claude-code
```

Vérification : `claude --version` doit afficher une version ≥ 2.0.

---

## 3. Setup du projet en local

```bash
cd "/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society"

# 1. Virtualenv Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optionnel mais recommandé pour valider les schemas
pip install jsonschema

# 2. Playwright browser (Chromium)
playwright install chromium

# 3. Deps Node (jsdom pour le verify dashboard)
npm install

# 4. Remplir .env avec les clés fraîches rotées à l'étape 1
cp .env.example .env  # si pas déjà fait
# puis édite .env et mets ton vrai ANTHROPIC_API_KEY

# 5. Charger les env vars dans ton shell (direnv recommandé, sinon manuel)
export $(grep -v '^#' .env | xargs)

# 6. Sanity check
python3 state.py
# Doit montrer : 291 captures / 104 clients / playbooks v3.2.0 locked
# Si erreur → lire le diagnostic, vérifier que l'env est OK
```

---

## 4. Git init (recommandé — Claude Code est 10× plus utile avec git)

Le `.gitignore` est déjà configuré pour exclure : data lourde, deliverables volumineux, secrets, caches. Seul le CODE + DOCTRINE + DOCS sera commité.

```bash
git init
git add .
git status   # ← VÉRIFIE avant de committer — doit être ~quelques centaines de fichiers, pas des milliers
git commit -m "P10 handoff — initial commit (v17.2.0)

- Pipeline complet V13 → V17.2.0
- Doctrine v3.2 (6 playbooks locked)
- Dashboard Observatoire v17.2.0
- 104 clients, 291 pages, 8663 recos
- Handoff Claude Code avec .claude/, SCHEMA/, RUNBOOK.md"
```

Si `git status` montre des fichiers lourds (>10 MB), STOP : vérifie le .gitignore.

---

## 5. Premier lancement Claude Code

```bash
cd "/Users/mathisfronty/Documents/Claude/Projects/Mathis - Stratégie CRO Interne - Growth Society"
claude
```

Au prompt, tape simplement :

```
Lis CLAUDE.md et exécute la séquence d'initialisation V18.
```

Claude Code va :

1. Lire `CLAUDE.md` (entrypoint forcé).
2. Lire `GROWTHCRO_MANIFEST.md` (vérité architecturale).
3. Lancer `python3 state.py`.
4. Skimmer `memory/MEMORY.md` + `WAKE_UP_NOTE_*V18_KICKOFF*.md`.
5. Te poser la question : **"Qu'est-ce qui n'a pas été compris dans la pipeline V17 ?"**

Réponds par quelques lignes décrivant les zones floues. Claude Code les convertira en plan V18.

---

## 6. Commandes slash disponibles (projet-level)

Une fois Claude Code démarré tu peux utiliser :

- `/audit-client <slug>` — audit complet d'un client (capture → scoring → recos → dashboard)
- `/score-page <slug> <pageType>` — scoring ciblé
- `/pipeline-status` — état disque enrichi (équivalent `state.py` + delta git + coûts)
- `/doctrine-diff <bloc> <old> <new>` — compare deux versions d'un playbook
- `/full-audit` — santé projet complète (doctrine + code + data + dashboard + secrets)

Ces commandes sont définies dans `.claude/commands/`. Tu peux les modifier.

---

## 7. Agents spécialisés (délégation automatique)

Claude Code peut déléguer aux subagents définis dans `.claude/agents/` :

- **capture-worker** — Playwright capture d'un client (sans LLM, rapide)
- **scorer** — Stages 2-5 du pipeline (perception + 6 piliers + overlay v3.2)
- **reco-enricher** — Stage 6 (Sonnet 4.5, recos priorisées P0-P3)
- **doctrine-keeper** — gardien de la cohérence doctrine ↔ scorer ↔ reco (Opus, pour les modifs structurantes)

Tu peux les invoquer explicitement : "Demande à l'agent scorer de faire X", ou Claude Code les choisira tout seul selon la tâche.

---

## 8. Hooks configurés

`.claude/settings.json` définit :

- **Permissions auto-accept** : lectures, grep, find, `state.py`, `verify-dashboard`, etc. → pas de confirmation à chaque commande sûre.
- **Permissions ask** : `rm`, `mv`, `git add/commit/push`, `pip install` → demande confirmation.
- **Hook PreToolUse Edit playbook** : rappel de valider le schema JSON avant de modifier `playbook/bloc_*_v3.json`.

Adapte à ton goût.

---

## 9. Gains vs environnement CoWork précédent

Ce que tu gagnes immédiatement en bascule Claude Code :

| Limitation CoWork | Levée en Claude Code ? |
|---|---|
| Sandbox bash timeout 45s | Oui — Playwright batch fleet, tar 1.4 GB, reco enricher --all passent |
| `rm` bloqué sur le mount FS | Oui — cleanup disque réel possible |
| NFD unicode macOS sur "Stratégie" | Oui — path natif, zéro escape |
| Pas de git | Oui — git natif, diff doctrine, revert |
| Subagents limités | Oui — vrais subagents, parallèle, workers isolés |
| Hooks absents | Oui — pre/post tool use hooks |

---

## 10. Troubleshooting premier lancement

### Claude Code dit "I don't see CLAUDE.md"
→ Tu n'es pas dans le bon dossier. `pwd` doit afficher `.../Mathis - Stratégie CRO Interne - Growth Society`.

### Playwright refuse de démarrer
→ `playwright install chromium` oublié. Ou Rosetta sur Apple Silicon pour l'ancien Chromium.

### `ANTHROPIC_API_KEY is not set`
→ Ton `.env` n'est pas chargé. Essaie `export $(grep -v '^#' .env | xargs)` avant `claude`, ou configure direnv.

### `npm run verify-dashboard` plante sur jsdom
→ `npm install` oublié. Vérifie que `node_modules/jsdom` existe.

### `python3 state.py` échoue "ModuleNotFoundError"
→ Virtualenv pas activé. `source .venv/bin/activate`.

### Dashboard V17 rend tout blanc dans le browser
→ Ouvre `deliverables/GrowthCRO-V17-Dashboard.html` → DevTools Console → regarde la stack JS. Puis lance `node deliverables/verify_dashboard_v17_2.js` pour isoler — ce script simule le même rendu en JSDOM.

---

## 11. Structure finale du projet livrée

```
Mathis - Stratégie CRO Interne - Growth Society/
├── CLAUDE.md                    # Entrypoint Claude Code (OBLIGATOIRE read)
├── GROWTHCRO_MANIFEST.md        # Vérité architecturale (~86 KB)
├── RUNBOOK.md                   # Pipeline end-to-end (NEW P10)
├── HANDOFF_TO_CLAUDE_CODE.md    # Ce fichier
├── README.md                    # Vue d'ensemble
│
├── .env.example                 # Template env vars (NEW P10)
├── .env                         # Ta copie avec clés (gitignored)
├── .gitignore                   # Tight — data lourde hors repo (NEW P10)
│
├── .claude/                     # Config Claude Code (NEW P10)
│   ├── settings.json
│   ├── agents/                  # 4 subagents
│   └── commands/                # 5 slash commands
│
├── SCHEMA/                      # JSON Schemas + validate.py (NEW P10)
│   ├── README.md
│   ├── *.schema.json            # 7 schemas
│   ├── validate.py
│   └── validate_all.py
│
├── state.py                     # Vérité disque
├── add_client.py                # Onboarding lean
├── enrich_client.py             # Discovery URL (cas rare)
├── capture_full.py              # Capture Python fallback
├── api_server.py                # FastAPI (futur SaaS)
│
├── requirements.txt             # Python deps (mis à jour P10)
├── package.json                 # Node deps (mis à jour P10)
│
├── playbook/                    # Doctrine v3.2 (6 blocs locked)
├── skills/site-capture/scripts/ # Pipeline PROD (perception, scoring, recos)
├── scripts/                     # Scripts one-off
│
├── data/
│   ├── clients_database.json    # Base clients (tracké)
│   ├── captures/                # 3.7 GB — gitignored
│   └── golden/                  # 896 MB — gitignored
│
├── deliverables/
│   ├── GrowthCRO-V17-Dashboard.html   # Shell HTML (tracké)
│   ├── dashboard_v17_app.js           # App JS (tracké)
│   ├── verify_dashboard_v17_2.js      # Verify script (tracké)
│   ├── growthcro_data_v17.json        # Data 55 MB — gitignored
│   └── archive/                       # V16 legacy — gitignored
│
└── memory/
    ├── MEMORY.md                # Index (NEW P10)
    ├── HISTORY.md               # Journal chronologique
    ├── SPECS.md                 # Specs figées
    └── snapshots/               # 17 snapshots JSON
```

---

## 12. Prochaine étape — V18

Claude Code, à son premier prompt, te demandera "qu'est-ce qui n'a pas été compris ?". C'est le point 9 du plan P10 : tu définis V18 avec lui.

Exemples de zones potentielles (à toi de confirmer) :

- Les 7 règles overlay v3.2 donnent-elles les bons boosts de priorité ?
- Le semantic scorer Haiku est-il vraiment calibré sur tous les business types ?
- Le dashboard Observatoire affiche-t-il bien la vérité pipeline (pas d'hallucination dans les rules_firing) ?
- La doctrine v3.2 est-elle auto-cohérente (pas de critère contradictoire entre blocs) ?
- L'intent detector V13 confond-il SaaS et marketplace sur certains cas limites ?
- Le reco enricher génère-t-il des recos génériques vs haute-couture selon le pageType ?
- Les coûts API sont-ils bien proportionnels à la valeur ajoutée ?

Mais ce qui compte c'est **ta vraie liste**, pas celle-là.

---

**Tu es prêt. Bon V18.**
