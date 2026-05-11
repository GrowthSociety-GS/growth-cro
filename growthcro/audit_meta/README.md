# growthcro/audit_meta — Meta Ads audit module (thin wrapper)

**Status**: V1 — Issue #22 webapp-stratosphere · AD-7 (Anthropic skill + thin wrapper).

## Vue d'ensemble

Module *thin wrapper* qui active le skill Anthropic
`anthropic-skills:meta-ads-auditor` comme produit parallèle accessible depuis
la webapp V28 / l'API GrowthCRO. **Aucune réinvention de l'audit Ads** :
la qualité analytique reste pilotée par le skill ; ce module se borne à :

- parser un export CSV Meta Ads Manager,
- structurer les KPIs (impressions, reach, clicks, spend, ROAS, purchases…),
- shaper la payload Notion-template (sections **A–H**) attendue par l'agence
  Growth Society,
- déléguer les sections narratives (audiences, creatives, conversions, recos,
  next steps) au skill via des slots `<<SKILL_FILLED>>`.

Combo Claude Code (`SKILLS_INTEGRATION_BLUEPRINT.md`, combo `agency_products`):

```
claude-api + anthropic-skills:meta-ads-auditor [+ anthropic-skills:gads-auditor selon route]
```

Limite session = **3 skills max**, activation **contextual** sur routes
`/audit-gads` ou `/audit-meta`.

## Structure (8-axes — `CODE_DOCTRINE.md`)

| Fichier | Axis | Concern |
|---|---|---|
| `__init__.py` | — | Re-exports publics |
| `orchestrator.py` | #4 | Pipeline parse → KPIs → sections → slots skill |
| `notion_export.py` | #8 | Pure dict→Markdown / dict→Notion-API payload |
| `cli.py` | #5 | `python -m growthcro.audit_meta.cli` |

Aucune lecture env (`os.environ` / `os.getenv`).

## Inputs

| Input | Statut | Notes |
|---|---|---|
| CSV export Meta Ads Manager | **MVP** | Export "Campaigns" niveau campagne |
| Meta Marketing API (OAuth) | **post-MVP** | Hors-scope #22 |

### Colonnes CSV reconnues (EN ↔ FR)

| Canonique | EN | FR |
|---|---|---|
| `campaign` | Campaign name | Nom de la campagne |
| `objective` | Objective | Objectif |
| `impressions` | Impressions | Impressions |
| `reach` | Reach | Couverture |
| `clicks` | Clicks (all) / Link clicks | Clics |
| `ctr_pct` | CTR (all) / CTR (link) | CTR |
| `cpm` | CPM | CPM |
| `cpc` | CPC (all) | CPC |
| `spend` | Amount spent | Dépenses |
| `purchases` | Purchases / Website purchases | Achats |
| `purchase_value` | Purchases conversion value | Valeur de conversion |
| `leads` | Leads / Form leads | Leads |
| `frequency` | Frequency | Fréquence |
| `roas` | Purchase ROAS | ROAS achats |

## Outputs

Tous les artefacts atterrissent sous `data/audits/meta/<client>/<period>/`:

| Fichier | Concerné |
|---|---|
| `bundle.json` | Structure complète (KPIs + sections + métadonnées) |
| `notion.md` | Template A–H prêt à coller dans Notion |
| `notion_payload.json` | Payload `pages.create` Notion-API |

### Sections (Growth Society template)

| Lettre | Titre | Mode |
|---|---|---|
| A | Overview compte Meta (FB + IG) | déterministe (CSV) |
| B | Campagnes (ASC, Advantage+, leads) | déterministe (CSV) |
| C | Audiences (broad / LAL / custom / retargeting) | `<<SKILL_FILLED>>` |
| D | Creatives (copy + visuels + video assets) | `<<SKILL_FILLED>>` |
| E | Conversions (Pixel + CAPI + offline events) | `<<SKILL_FILLED>>` |
| F | Recommandations priorisées | `<<SKILL_FILLED>>` |
| G | Next steps actionables | `<<SKILL_FILLED>>` |
| H | Annexes (CSV refs + screenshots) | déterministe |

## Usage

### CLI

```bash
python -m growthcro.audit_meta.cli \
  --client growth-society-acme \
  --csv data/audits/meta/_fixtures/acme.csv \
  --period 2026-04 \
  --business-category ecommerce \
  --notes "Compte e-com FR, ASC scaling Q2"
```

Options : `--no-write` (preview only), `--json` (stdout bundle), `--out-dir`
(override default).

### Python

```python
from growthcro.audit_meta import AuditInputs, run_audit, render_notion_markdown

bundle = run_audit(AuditInputs(client_slug="acme", csv_path="acme.csv"))
markdown = render_notion_markdown(bundle.as_dict())
```

### FastAPI

`POST /audit/meta` (cf. `growthcro/api/server.py`) — accepte `client_slug` +
soit `csv_path` soit `csv_text`, retourne le bundle JSON et les chemins
d'artefacts persistés.

## Procédure validation Mathis (post-merge)

1. Récupérer un export CSV réel d'un compte client Growth Society
   (Ads Manager → Campaigns → Export Table → CSV, 30 derniers jours).
2. Lancer :
   ```bash
   python -m growthcro.audit_meta.cli --client <real-slug> --csv <real.csv>
   ```
3. Ouvrir `data/audits/meta/<slug>/<period>/notion.md` et vérifier :
   - sections A, B, H renseignées avec KPIs corrects vs Ads Manager UI,
   - sections C–G contiennent les slots `<<SKILL_FILLED>>` clairement identifiés.
4. Lancer le skill interactif (Claude Code) :
   ```
   /anthropic-skills:meta-ads-auditor avec bundle data/audits/meta/<slug>/<period>/bundle.json
   ```
5. Mathis remplace les slots `<<SKILL_FILLED>>` par les outputs du skill et
   valide la qualité globale.

## Follow-ups (out-of-scope #22)

- Intégration directe Meta Marketing API (OAuth).
- Génération PDF export (post-MVP).
- Stockage chiffré at-rest des artefacts si on persiste sur Supabase
  (sinon ephemeral dans `data/audits/`, gitignored).
- Branding + pricing final avec direction Growth Society.

## Liens

- Task spec : `.claude/epics/webapp-stratosphere/22.md`
- PRD FR-7 : `.claude/prds/webapp-stratosphere.md`
- Blueprint skills : `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md`
- Architecture map : `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`
- Code doctrine : `.claude/docs/doctrine/CODE_DOCTRINE.md`
