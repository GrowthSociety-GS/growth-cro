# PRD-E — Push to Stratospheric

**Sprint 19 / Epic** : gsg-push-to-stratospheric-2026-05
**Estimated** : 3h

## E1. Pull-quote provenance tagging

`page_renderer_orchestrator.py` :
```
<aside class="pull-quote" data-pull-quote-of-reason="04">
  <span class="pull-quote-mark">"</span>
  <p>+400% trafic organique (cas client Polaar, 12 mois)</p>
  <cite class="pull-quote-cite">— Raison 04, cas client Polaar</cite>
</aside>
```

Doctrine judge prompt at `moteur_multi_judge/judges/doctrine_judge.py` :
add 1 line to instruction set : *"Ignore content inside
`<aside class='pull-quote'>` — these are editorial callouts amplifying
the previous reason, not independent claims."*

## E2. Reason-level proof citation chips

For each reason where the `side_note` matches a `brief.sourced_numbers`
context, emit a chip list :

```
<ul class="reason-sources" aria-label="Sources">
  <li><a href="https://g2.com/products/weglot" rel="nofollow noopener">G2 ↗</a></li>
  <li><a href="https://weglot.com/case-studies/polaar" rel="nofollow noopener">Case study Polaar ↗</a></li>
</ul>
```

Sources come from :
- `brief.sourced_numbers[*].source_url` (when present) — Sprint 19
  adds this optional field to `SourcedNumber` dataclass
- Hardcoded canonical URLs for known publishers (G2, Trustpilot,
  WordPress Plugin Directory) inferred from the `source` string

## E3. Multi-page generation foundation

New module `moteur_gsg/core/bundle_generator.py` (~150 LOC) :

```python
def generate_lp_bundle(
    *,
    client: str,
    pages: list[str],   # ["home", "pricing", "lp_listicle"]
    shared_brief: dict, # objective, audience, angle minimal
    save_dir: str,
    multi_judge: bool = False,
) -> dict[str, Any]:
    """Generate N pages for a client in a single run, shared brand context."""
```

Loops `generate_lp()` per page, shares :
- Same `client` (same brand_dna, same captures)
- Same `objective`, `audience`, `angle` (cloned from `shared_brief`)
- `page_type` varies per iteration
- Outputs : `save_dir/<client>/<YYYY-MM-DD>/<page_type>.html` + a
  consolidated `bundle_summary.json` with all composite scores

Smoke-test on Weglot with `pages=["lp_listicle"]` only first (reuses
the existing weglot brief). Then later test with 3 pages.

## E4. SourcedNumber.source_url

`brief_v2.py` SourcedNumber dataclass : add `source_url: Optional[str] = None`.
`to_legacy_brief()` propagates. When a reason's side_note matches a
sourced number by string overlap, the renderer picks up the URL.

## Files to modify

- `moteur_gsg/core/page_renderer_orchestrator.py` — pull-quote + reason
  chips rendering
- `moteur_gsg/core/brief_v2.py` — SourcedNumber.source_url field
- `moteur_gsg/core/css/components.py` — `.pull-quote-cite`,
  `.reason-sources`, `.reason-sources li a` rules
- `moteur_multi_judge/judges/doctrine_judge.py` — system prompt
  addition : skip `<aside class='pull-quote'>`
- `moteur_gsg/core/bundle_generator.py` (NEW)
- `moteur_gsg/orchestrator.py` — export `generate_lp_bundle`

## Acceptance

- V12 composite_score ≥ 91 (target Stratospheric ≥ 92)
- V12 Doctrine ≥ 82 (V11 was 80.0)
- Smoke test `generate_lp_bundle("weglot", pages=["lp_listicle"], save_dir="deliverables/bundles/")` produces 1 HTML + 1 summary JSON
- No regression on Impeccable QA / runtime audits
