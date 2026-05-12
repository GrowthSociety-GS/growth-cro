"""Helpers pour lire un SiteCapture et servir de base au scoring V3."""
import json
import pathlib

def load(label):
    p = pathlib.Path(__file__).resolve().parents[3] / "data" / "captures" / label / "capture.json"
    return json.loads(p.read_text())

def get_hero(cap):           return cap.get("hero", {})
def get_h1(cap):              return get_hero(cap).get("h1", "")
def get_subtitle(cap):        return get_hero(cap).get("subtitle", "")
def get_cta_primary(cap):     return get_hero(cap).get("primaryCta")
def get_social_proof(cap):    return get_hero(cap).get("socialProofInFold", {})
def get_overlays(cap):        return cap.get("overlays", {})
def get_screenshot(cap, key):
    base = pathlib.Path(__file__).resolve().parents[3] / "data" / "captures" / cap["meta"]["label"]
    return str(base / cap["screenshots"][key])

if __name__ == "__main__":
    import sys
    cap = load(sys.argv[1])
    print("H1:", get_h1(cap))
    print("Subtitle:", get_subtitle(cap))
    print("Primary CTA:", get_cta_primary(cap))
    print("Social proof:", get_social_proof(cap))
