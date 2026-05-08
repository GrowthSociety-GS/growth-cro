#!/usr/bin/env python3
"""
golden_bridge.py — Golden Dataset Bridge for reco_enricher V16

Provides benchmark context from golden (best-in-class) sites to:
1. Annihilate irrelevant recos (golden also scores low → criterion not a lever)
2. Provide concrete inspiration (golden H1, CTA, structure examples)
3. Detect off-doctrine signals (golden excels differently than doctrine expects)
"""

import json
from pathlib import Path
from typing import Optional

# Category similarity: golden_category -> compatible client categories
CATEGORY_MAP = {
    "dtc_beauty": ["ecommerce_beauty", "ecommerce_wellness", "ecommerce"],
    "dtc_fashion": ["ecommerce_fashion", "ecommerce"],
    "dtc_fitness": ["ecommerce_fitness", "ecommerce_wellness", "ecommerce"],
    "dtc_home": ["ecommerce_home", "ecommerce"],
    "luxury": ["ecommerce_beauty", "ecommerce_fashion", "ecommerce"],
    "subscription": ["ecommerce_food", "ecommerce_wellness", "ecommerce"],
    "saas_b2b": ["saas_b2b", "saas_fintech"],
    "saas_b2c": ["saas_b2c", "app_consumer"],
    "saas_b2b_pm": ["saas_b2b"],
    "devtools_b2b": ["saas_b2b"],
    "fintech": ["saas_fintech", "fintech"],
    "neobank_b2c": ["saas_fintech", "fintech", "app_consumer"],
    "marketplace": ["marketplace", "app_consumer"],
    "app_mobile": ["app_consumer"],
    "formation": ["services_lead_gen", "formation"],
    "leadgen": ["services_lead_gen", "services_insurance"],
}


class GoldenBridge:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.golden_dir = self.root / "data" / "golden"
        self.registry = self._load_registry()
        self._scores_cache = {}
        self._capture_cache = {}

    def _load_registry(self) -> list:
        reg_path = self.golden_dir / "_golden_registry.json"
        if not reg_path.exists():
            return []
        data = json.load(open(reg_path))
        return data.get("sites", [])

    def _load_golden_scores(self, label: str, page_type: str) -> dict:
        key = f"{label}/{page_type}"
        if key in self._scores_cache:
            return self._scores_cache[key]
        result = {}
        page_dir = self.golden_dir / label / page_type

        # Semantic scores
        sem_path = page_dir / "score_semantic.json"
        if sem_path.exists():
            sem = json.load(open(sem_path))
            for crit_id, data in sem.get("scores", {}).items():
                if isinstance(data, dict) and data.get("score") is not None:
                    result[crit_id] = data["score"]

        # Pillar/bloc scores
        for score_file in page_dir.glob("score_*.json"):
            if score_file.name == "score_semantic.json":
                continue
            try:
                sd = json.load(open(score_file))
                for crit in sd.get("criteria", []):
                    cid = crit.get("id") or crit.get("criterion_id")
                    sc = crit.get("score")
                    if cid and sc is not None:
                        result[cid] = sc
            except Exception:
                pass

        self._scores_cache[key] = result
        return result

    def _load_golden_capture(self, label: str, page_type: str) -> dict:
        key = f"{label}/{page_type}"
        if key in self._capture_cache:
            return self._capture_cache[key]
        cap_path = self.golden_dir / label / page_type / "capture.json"
        if not cap_path.exists():
            return {}
        cap = json.load(open(cap_path))
        self._capture_cache[key] = cap
        return cap

    def find_closest_golden(self, client_category: str, page_type: str, n: int = 5) -> list:
        scored = []
        for site in self.registry:
            gold_cat = site.get("category", "")
            gold_biz = site.get("biz", "")
            gold_pages = site.get("pages", {})

            if page_type not in gold_pages:
                continue
            if not (self.golden_dir / site["label"] / page_type).exists():
                continue

            affinity = 0
            compatible_cats = CATEGORY_MAP.get(gold_cat, [])
            if client_category == gold_cat:
                affinity = 10
            elif client_category in compatible_cats:
                affinity = 7
            elif client_category and any(
                client_category.startswith(prefix)
                for prefix in ["ecommerce"] if gold_biz == "ecommerce"
            ):
                affinity = 4
            elif client_category and any(
                client_category.startswith(prefix)
                for prefix in ["saas"] if gold_biz == "saas"
            ):
                affinity = 4
            else:
                affinity = 1

            scored.append((affinity, site["label"], site))

        scored.sort(key=lambda x: -x[0])
        return [(label, site) for _, label, site in scored[:n]]

    def get_benchmark_context(self, client_category: str, page_type: str, crit_id: str) -> dict:
        """
        Build golden benchmark context for a criterion.
        Returns dict with: golden_refs, golden_avg, annihilate, inspiration_block
        """
        closest = self.find_closest_golden(client_category, page_type, n=5)

        refs = []
        all_scores = []
        for label, site in closest:
            scores = self._load_golden_scores(label, page_type)
            cap = self._load_golden_capture(label, page_type)
            hero = cap.get("hero", {})

            score = scores.get(crit_id)
            if score is not None:
                all_scores.append(score)

            ctas = hero.get("ctas") or []
            primary_cta = ctas[0].get("text", "") if ctas else ""

            refs.append({
                "label": label,
                "url": site.get("url", ""),
                "score": score,
                "h1": hero.get("h1", ""),
                "subtitle": hero.get("subtitle", ""),
                "primary_cta": primary_cta,
                "biz": site.get("biz", ""),
                "category": site.get("category", ""),
            })

        if not all_scores:
            return {
                "golden_refs": refs,
                "golden_avg": None,
                "golden_median": None,
                "annihilate": False,
                "inspiration_block": "(aucun golden disponible pour ce critère/page)",
            }

        golden_avg = sum(all_scores) / len(all_scores)
        sorted_scores = sorted(all_scores)
        golden_median = sorted_scores[len(sorted_scores) // 2]

        # Annihilation: golden avg <= 1.0 means even best-in-class struggle
        annihilate = golden_avg <= 1.0

        lines = []
        lines.append(f"Score moyen golden ({len(all_scores)} refs): {golden_avg:.1f}/3")

        top_refs = sorted(refs, key=lambda r: r.get("score") or 0, reverse=True)[:3]
        for r in top_refs:
            sc = r["score"] if r["score"] is not None else "N/A"
            line = f"  - {r['label']} ({r['category']}): score={sc}"
            if r["h1"]:
                line += f' | H1="{r["h1"][:80]}"'
            if r["primary_cta"]:
                line += f' | CTA="{r["primary_cta"][:50]}"'
            lines.append(line)

        if annihilate:
            lines.append("")
            lines.append("⚠️ SIGNAL D'ANNIHILATION : Les best-in-class scorent aussi bas sur ce critère.")
            lines.append("→ Ce critère n'est PAS un levier de conversion pour ce type de business/page.")
            lines.append("→ Si tu maintiens une reco, elle DOIT être P3 maximum et 'nice-to-have'.")
        elif golden_avg >= 2.5:
            lines.append("")
            lines.append("🎯 SIGNAL FORT : Les leaders excellent sur ce critère. L'écart avec le client est un vrai levier.")
            lines.append("→ Inspire-toi des exemples golden ci-dessus pour ta proposition 'after'.")

        return {
            "golden_refs": refs,
            "golden_avg": golden_avg,
            "golden_median": golden_median,
            "annihilate": annihilate,
            "inspiration_block": "\n".join(lines),
        }
