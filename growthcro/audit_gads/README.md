# growthcro/audit_gads — Google Ads audit module (thin wrapper)

**Status**: V1 — Issue #22 webapp-stratosphere · AD-7 (Anthropic skill + thin wrapper).

## Vue d'ensemble

Module *thin wrapper* qui active le skill Anthropic `anthropic-skills:gads-auditor`
comme produit parallèle accessible depuis la webapp V28 / l'API GrowthCRO. **Aucune
réinvention de l'audit Ads** : la qualité analytique reste pilotée par le skill ;
ce module se borne à :

- parser un export CSV Google Ads Editor / Reports,
- structurer les KPIs (impressions, clics, coût, conversions, ROAS, CPA…),
- shaper la payload Notion-template (sections **A–H**) attendue par l'agence
  Growth Society,
- déléguer les sections narratives (recos, next steps) au skill via des slots
  `<<SKILL_FILLED>>` qui sont remplacés à l'invocation interactive.

Combo Claude Code activé (`SKILLS_INTEGRATION_BLUEPRINT.md`, combo
`agency_products`) :

```
claude-api + anthropic-skills:gads-auditor [+ anthropic-skills:meta-ads-auditor selon route]
```

Limite session = **3 skills max**, activation **contextual** sur routes
`/audit-gads` ou `/audit-meta`.

## Structure (8-axes — `CODE_DOCTRINE.md`)

| Fichier | Axis | Concern |
|---|---|---|
| `__init__.py` | — | Re-exports publics |
| `orchestrator.py` | #4 | Pipeline parse → KPIs → sections → slots skill |
| `notion_export_gads.py` | #8 | Pure dict→Markdown / dict→Notion-API payload (Google Ads) |
| `cli.py` | #5 | `python -m growthcro.audit_gads.cli` |

Aucune lecture env (`os.environ` / `os.getenv`) — tout passe par
`growthcro.config` si besoin (zéro env requis aujourd'hui : tout est CSV-driven).

## Inputs

| Input | Statut | Notes |
|---|---|---|
| CSV export Google Ads Editor | **MVP** | Format Reports standard, colonnes EN ou FR |
| CSV téléchargé depuis Reports UI | **MVP** | Idem |
| API Google Ads (OAuth) | **post-MVP** | Hors-scope #22 — follow-up ticket à créer |

### Colonnes CSV reconnues (anglais ↔ français)

| Canonique | EN | FR |
|---|---|---|
| `campaign` | Campaign | Campagne |
| `campaign_type` | Campaign type | Type de campagne |
| `impressions` | Impressions | Impressions / Impr. |
| `clicks` | Clicks | Clics |
| `cost` | Cost | Coût / Spend |
| `conversions` | Conversions | Conversions / Conv. |
| `conv_value` | Conv. value | Valeur de conversion |
| `ctr` | CTR | Taux de clics |
| `avg_cpc` | Avg. CPC | CPC moy. |
| `cpa` | Cost / conv. | Coût / conv. |
| `roas` | ROAS | Conv. value / cost |

## Outputs

Tous les artefacts atterrissent sous
`data/audits/gads/<client>/<period>/` :

| Fichier | Concerné |
|---|---|
| `bundle.json` | Structure complète (KPIs + sections + métadonnées) |
| `notion.md` | Template A–H prêt à coller dans Notion |
| `notion_payload.json` | Payload `pages.create` Notion-API |

### Sections (Growth Society template)

| Lettre | Titre | Mode |
|---|---|---|
| A | Overview compte / KPIs globaux | déterministe (CSV) |
| B | Campagnes (Search + Shopping + PMax + Demand Gen) | déterministe (CSV) |
| C | Keywords / Audiences | `<<SKILL_FILLED>>` |
| D | Creatives (ads + assets) | `<<SKILL_FILLED>>` |
| E | Conversions (tracking, attribution, valeur) | `<<SKILL_FILLED>>` |
| F | Recommandations priorisées | `<<SKILL_FILLED>>` |
| G | Next steps actionables (timeline) | `<<SKILL_FILLED>>` |
| H | Annexes (CSV refs + screenshots) | déterministe |

## Usage

### CLI

```bash
python -m growthcro.audit_gads.cli \
  --client growth-society-acme \
  --csv data/audits/gads/_fixtures/acme.csv \
  --period 2026-04 \
  --business-category ecommerce \
  --notes "Compte e-com FR, BFCM Q4 prep"
```

Options : `--no-write` (preview only), `--json` (stdout bundle), `--out-dir`
(override default).

### Python

```python
from growthcro.audit_gads import AuditInputs, run_audit, render_notion_markdown

bundle = run_audit(AuditInputs(client_slug="acme", csv_path="acme.csv"))
markdown = render_notion_markdown(bundle.as_dict())
```

### FastAPI

`POST /audit/gads` (cf. `growthcro/api/server.py`) — accepte `client_slug` +
soit `csv_path` soit `csv_text`, retourne le bundle JSON et les chemins
d'artefacts persistés.

## Procédure validation Mathis (post-merge)

1. Récupérer un export CSV réel d'un compte client Growth Society
   (Reports → Campaign performance, 30 derniers jours).
2. Lancer :
   ```bash
   python -m growthcro.audit_gads.cli --client <real-slug> --csv <real.csv>
   ```
3. Ouvrir `data/audits/gads/<slug>/<period>/notion.md` et vérifier :
   - sections A, B, H renseignées avec KPIs corrects vs Reports UI,
   - sections C–G contiennent les slots `<<SKILL_FILLED>>` clairement identifiés.
4. Lancer le skill interactif (Claude Code) :
   ```
   /anthropic-skills:gads-auditor avec bundle data/audits/gads/<slug>/<period>/bundle.json
   ```
5. Mathis remplace les slots `<<SKILL_FILLED>>` par les outputs du skill et
   valide la qualité globale.

## Follow-ups (out-of-scope #22)

- Intégration directe API Google Ads (OAuth) — éviter export CSV manuel.
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
