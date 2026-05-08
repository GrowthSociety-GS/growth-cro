#!/usr/bin/env python3
"""
Golden Design Bridge — Cross-category aesthetic matching.

Matches a target aesthetic vector to the closest golden sites by AESTHETIC INTENT,
not business category. A wellness brand can be matched to Stripe's depth techniques
and Aesop's editorial philosophy.

Two-layer matching:
1. Global match: sites whose overall aesthetic vector is closest → philosophy inspiration
2. Technique match: best execution per technique type across ALL sites → CSS techniques

Usage:
    # Find closest golden sites for a given vector
    python3 golden_design_bridge.py --vector '{"energy":2.5,"warmth":4,"density":2,"depth":4,"motion":3,"editorial":3.5,"playful":2,"organic":4.5}'
    
    # Get full benchmark prompt for injection into GSG
    python3 golden_design_bridge.py --vector '...' --prompt

Output: benchmark context + injectable prompt block.
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path


# ─── Constants ────────────────────────────────────────────────────────────────

# Weights for distance calculation — warmth and playful matter most for "feel"
DISTANCE_WEIGHTS = {
    "energy": 1.0,
    "warmth": 1.3,
    "density": 0.8,
    "depth": 1.0,
    "motion": 0.7,
    "editorial": 1.1,
    "playful": 1.2,
    "organic": 0.9,
}

TECHNIQUE_TYPES = [
    "background", "typography", "layout", "depth", 
    "motion", "texture", "color", "signature",
]


# ─── Core Bridge ──────────────────────────────────────────────────────────────

class GoldenDesignBridge:
    """Match target aesthetic to golden sites by vector proximity, not category."""
    
    def __init__(self, golden_base_dir: str = None):
        if golden_base_dir is None:
            golden_base_dir = str(Path(__file__).parent.parent.parent.parent / "data" / "golden")
        
        self.golden_dir = Path(golden_base_dir)
        self.profiles = []
        self.technique_library = []
        self._load_profiles()
    
    def _load_profiles(self):
        """Load all golden site design profiles."""
        
        # Load registry for metadata
        registry = {}
        reg_path = self.golden_dir / "_golden_registry.json"
        if reg_path.exists():
            try:
                data = json.load(open(reg_path))
                for site in data.get("sites", []):
                    registry[site["label"]] = site
            except Exception as e:
                print(f"WARNING: Could not load registry: {e}")
        
        # Find all design_dna.json files
        dna_files = sorted(self.golden_dir.rglob("design_dna.json"))
        
        for dna_path in dna_files:
            try:
                dna = json.load(open(dna_path))
                vector = dna.get("aesthetic_vector")
                if not vector:
                    continue
                
                page_dir = dna_path.parent
                site_label = page_dir.parent.name
                page_type = page_dir.name
                
                site_meta = registry.get(site_label, {})
                
                profile = {
                    "label": site_label,
                    "page": page_type,
                    "category": site_meta.get("category", "unknown"),
                    "url": site_meta.get("url", ""),
                    "vector": vector,
                    "signature": dna.get("signature", ""),
                    "wow_factor": dna.get("wow_factor", ""),
                    "techniques": dna.get("techniques", []),
                    "design_philosophy": dna.get("haiku_analysis", {}).get("design_philosophy", ""),
                    "palette_strategy": dna.get("haiku_analysis", {}).get("palette_strategy", ""),
                    "typography_strategy": dna.get("haiku_analysis", {}).get("typography_strategy", ""),
                }
                
                self.profiles.append(profile)
                
                # Add techniques to the library
                for tech in profile.get("techniques", []):
                    tech_entry = {
                        **tech,
                        "source_site": site_label,
                        "source_page": page_type,
                        "source_category": profile["category"],
                    }
                    self.technique_library.append(tech_entry)
                    
            except Exception as e:
                continue
        
        print(f"Loaded {len(self.profiles)} golden design profiles, {len(self.technique_library)} techniques")
    
    @staticmethod
    def aesthetic_distance(v1: dict, v2: dict) -> float:
        """Weighted Euclidean distance between two aesthetic vectors."""
        total = 0
        for key, weight in DISTANCE_WEIGHTS.items():
            a = v1.get(key, 3.0)
            b = v2.get(key, 3.0)
            total += weight * (a - b) ** 2
        return math.sqrt(total)
    
    def find_closest(self, target: dict, top_n: int = 5) -> list:
        """Find the N golden sites/pages with closest aesthetic vector."""
        distances = []
        for profile in self.profiles:
            dist = self.aesthetic_distance(target, profile["vector"])
            distances.append((profile, dist))
        distances.sort(key=lambda x: x[1])
        return distances[:top_n]
    
    def find_best_techniques(self, technique_type: str, top_n: int = 3) -> list:
        """Find the best executions of a technique type across ALL golden sites."""
        candidates = [t for t in self.technique_library if t.get("type") == technique_type]
        candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        return candidates[:top_n]
    
    def find_techniques_for_vector(self, target: dict, top_per_type: int = 2) -> dict:
        """Find the best techniques per type, biased toward aesthetically close sites."""
        result = {}
        
        for tt in TECHNIQUE_TYPES:
            candidates = [t for t in self.technique_library if t.get("type") == tt]
            
            # Score = technique quality + proximity bonus
            scored = []
            for tech in candidates:
                # Find this technique's site profile
                site_profile = next(
                    (p for p in self.profiles if p["label"] == tech["source_site"] and p["page"] == tech["source_page"]),
                    None
                )
                
                base_score = tech.get("score", 3.0)
                proximity_bonus = 0
                
                if site_profile:
                    dist = self.aesthetic_distance(target, site_profile["vector"])
                    # Closer sites get a bigger bonus (max +1.5 for distance 0)
                    proximity_bonus = max(0, 1.5 - dist * 0.3)
                
                scored.append((tech, base_score + proximity_bonus))
            
            scored.sort(key=lambda x: x[1], reverse=True)
            result[tt] = [t for t, _ in scored[:top_per_type]]
        
        return result
    
    def explain_match(self, target: dict, matched: dict) -> str:
        """Explain WHY two vectors matched — which dimensions are close."""
        close_dims = []
        for key in DISTANCE_WEIGHTS:
            diff = abs(target.get(key, 3) - matched.get(key, 3))
            if diff < 0.8:
                close_dims.append(key)
        
        return f"Proches sur : {', '.join(close_dims)}" if close_dims else "Match global modéré"
    
    def get_design_benchmark(self, target: dict) -> dict:
        """Get full benchmark context for injection into GSG prompt."""
        
        # Layer 1: Global aesthetic match
        closest = self.find_closest(target, top_n=3)
        
        # Layer 2: Best techniques per type (biased by proximity)
        best_techniques = self.find_techniques_for_vector(target, top_per_type=1)
        
        # Format philosophy refs
        philosophy_refs = []
        for profile, dist in closest:
            philosophy_refs.append({
                "site": profile["label"],
                "page": profile["page"],
                "category": profile["category"],
                "distance": round(dist, 2),
                "vector": profile["vector"],
                "signature": profile.get("signature", ""),
                "wow_factor": profile.get("wow_factor", ""),
                "design_philosophy": profile.get("design_philosophy", ""),
                "why_matched": self.explain_match(target, profile["vector"]),
            })
        
        # Format technique refs
        technique_refs = {}
        for tt, techs in best_techniques.items():
            if techs:
                technique_refs[tt] = [{
                    "name": t.get("name", "Unknown"),
                    "source_site": t["source_site"],
                    "source_page": t["source_page"],
                    "source_category": t["source_category"],
                    "score": t.get("score", 0),
                    "css_approach": t.get("css_approach", ""),
                    "why_it_works": t.get("why_it_works", ""),
                } for t in techs]
        
        # Generate injectable prompt
        prompt_block = self._format_prompt(philosophy_refs, technique_refs, target)
        
        return {
            "philosophy_refs": philosophy_refs,
            "technique_refs": technique_refs,
            "prompt_block": prompt_block,
        }
    
    def _format_prompt(self, philosophy_refs: list, technique_refs: dict, target: dict) -> str:
        """Format the benchmark block for injection into the GSG prompt."""
        
        lines = []
        lines.append("## GOLDEN DESIGN BENCHMARK (intelligence esthétique cross-catégorie)")
        lines.append("")
        lines.append(f"Vecteur cible : energy={target.get('energy',3):.1f} warmth={target.get('warmth',3):.1f} "
                      f"density={target.get('density',3):.1f} depth={target.get('depth',3):.1f} "
                      f"motion={target.get('motion',3):.1f} editorial={target.get('editorial',3):.1f} "
                      f"playful={target.get('playful',3):.1f} organic={target.get('organic',3):.1f}")
        lines.append("")
        
        # Philosophy refs
        lines.append("### PHILOSOPHIE DA — Sites dont l'ADN esthétique est le plus proche :")
        lines.append("")
        for ref in philosophy_refs:
            lines.append(f"**{ref['site'].upper()}/{ref['page']}** ({ref['category']}) — distance: {ref['distance']:.1f}")
            if ref.get("signature"):
                lines.append(f"  Signature : {ref['signature']}")
            if ref.get("wow_factor"):
                lines.append(f"  Wow factor : {ref['wow_factor']}")
            if ref.get("design_philosophy"):
                lines.append(f"  Philosophie : {ref['design_philosophy']}")
            lines.append(f"  Match : {ref['why_matched']}")
            lines.append("")
        
        # Technique refs
        lines.append("### TECHNIQUES À EMPRUNTER (cross-catégorie, meilleures exécutions) :")
        lines.append("")
        for tt, techs in technique_refs.items():
            if techs:
                t = techs[0]
                lines.append(f"**{tt.upper()}** → {t['name']} (source: {t['source_site']}/{t['source_page']}, "
                             f"score: {t['score']}/5)")
                if t.get("css_approach"):
                    lines.append(f"  CSS : {t['css_approach']}")
                if t.get("why_it_works"):
                    lines.append(f"  Pourquoi : {t['why_it_works']}")
                lines.append("")
        
        # Consignes
        lines.append("### CONSIGNES CRÉATIVES :")
        lines.append("- Inspire-toi des TECHNIQUES ci-dessus, pas des STYLES.")
        lines.append("- Ton output doit être aussi impressionnant mais visuellement DIFFÉRENT.")
        lines.append("- Ne copie jamais un layout — invente le tien avec le même niveau d'exécution.")
        lines.append("- Fusionne des techniques de sites DIFFÉRENTS pour créer quelque chose d'inédit.")
        lines.append("- Le matching est par intention esthétique, PAS par secteur business.")
        lines.append("  Un site wellness PEUT emprunter la profondeur de Stripe.")
        
        return "\n".join(lines)
    
    def export_technique_library(self, output_path: str = None) -> dict:
        """Export the full technique library as JSON."""
        
        library = {
            "version": "16.0.0",
            "source": "golden_design_extraction",
            "technique_count": len(self.technique_library),
            "techniques": self.technique_library,
        }
        
        if output_path:
            with open(output_path, "w") as f:
                json.dump(library, f, indent=2, ensure_ascii=False)
            print(f"Technique library exported → {output_path} ({len(self.technique_library)} techniques)")
        
        return library


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Golden Design Bridge — Cross-category aesthetic matching")
    parser.add_argument("--vector", type=str, help="Target aesthetic vector as JSON string")
    parser.add_argument("--golden-dir", type=str, default=None, help="Path to golden data directory")
    parser.add_argument("--prompt", action="store_true", help="Output the injectable prompt block")
    parser.add_argument("--top", type=int, default=5, help="Number of closest matches")
    parser.add_argument("--export-library", type=str, default=None, help="Export technique library to JSON")
    parser.add_argument("--stats", action="store_true", help="Show statistics about golden profiles")
    args = parser.parse_args()
    
    bridge = GoldenDesignBridge(args.golden_dir)
    
    if args.stats:
        print(f"\n{'='*60}")
        print(f"Golden Design Intelligence — Statistics")
        print(f"{'='*60}")
        print(f"Profiles loaded: {len(bridge.profiles)}")
        print(f"Techniques catalogued: {len(bridge.technique_library)}")
        print(f"\nBy category:")
        cats = {}
        for p in bridge.profiles:
            cats[p["category"]] = cats.get(p["category"], 0) + 1
        for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {cnt} pages")
        print(f"\nBy technique type:")
        tech_types = {}
        for t in bridge.technique_library:
            tt = t.get("type", "unknown")
            tech_types[tt] = tech_types.get(tt, 0) + 1
        for tt, cnt in sorted(tech_types.items(), key=lambda x: -x[1]):
            print(f"  {tt}: {cnt} techniques")
        
        # Average vectors per category
        print(f"\nAverage aesthetic vectors:")
        cat_vectors = {}
        for p in bridge.profiles:
            cat = p["category"]
            if cat not in cat_vectors:
                cat_vectors[cat] = []
            cat_vectors[cat].append(p["vector"])
        
        for cat, vectors in sorted(cat_vectors.items()):
            avg = {}
            for dim in DISTANCE_WEIGHTS:
                vals = [v.get(dim, 3.0) for v in vectors]
                avg[dim] = round(sum(vals) / len(vals), 1)
            highlights = sorted(avg.items(), key=lambda x: abs(x[1] - 3.0), reverse=True)[:3]
            highlight_str = ", ".join(f"{k}={v}" for k, v in highlights)
            print(f"  {cat:22s}: {highlight_str}")
        
        return
    
    if args.export_library:
        bridge.export_technique_library(args.export_library)
        return
    
    if not args.vector:
        parser.print_help()
        return
    
    target = json.loads(args.vector)
    
    if args.prompt:
        benchmark = bridge.get_design_benchmark(target)
        print(benchmark["prompt_block"])
    else:
        closest = bridge.find_closest(target, top_n=args.top)
        print(f"\nTop {args.top} closest golden sites (by aesthetic intent):\n")
        for profile, dist in closest:
            print(f"  {profile['label']:20s}/{profile['page']:12s} ({profile['category']:18s}) — distance: {dist:.2f}")
            v = profile["vector"]
            print(f"    Vector: e={v['energy']:.1f} w={v['warmth']:.1f} d={v['density']:.1f} "
                  f"dep={v['depth']:.1f} m={v['motion']:.1f} ed={v['editorial']:.1f} "
                  f"p={v['playful']:.1f} o={v['organic']:.1f}")
            if profile.get("signature"):
                print(f"    Signature: {profile['signature']}")
            print(f"    Match: {bridge.explain_match(target, profile['vector'])}")
            print()


if __name__ == "__main__":
    main()
