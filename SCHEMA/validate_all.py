#!/usr/bin/env python3
"""
Validate TOUS les fichiers pipeline contre leurs schemas.
Stoppe à la première erreur (exit 1), sinon exit 0.

Usage:
    python3 SCHEMA/validate_all.py [--sample N]
    # --sample N : valide seulement N pages au hasard (faster)
"""
import json, sys, pathlib, argparse, random

try:
    import jsonschema
except ImportError:
    print("✗ jsonschema not installed. Run: pip install jsonschema")
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DIR = pathlib.Path(__file__).resolve().parent

PAIRS = [
    # (glob, schema)
    ("data/captures/*/*/score_hero.json", "score_pillar.schema.json"),
    ("data/captures/*/*/score_persuasion.json", "score_pillar.schema.json"),
    ("data/captures/*/*/score_ux.json", "score_pillar.schema.json"),
    ("data/captures/*/*/score_coherence.json", "score_pillar.schema.json"),
    ("data/captures/*/*/score_psycho.json", "score_pillar.schema.json"),
    ("data/captures/*/*/score_tech.json", "score_pillar.schema.json"),
    ("data/captures/*/*/score_page_type.json", "score_page_type.schema.json"),
    ("data/captures/*/*/perception_v13.json", "perception_v13.schema.json"),
    ("data/captures/*/*/recos_enriched.json", "recos_enriched.schema.json"),
    ("playbook/bloc_*_v3.json", "bloc_v3.schema.json"),
    ("playbook/bloc_*_v3-3.json", "bloc_v3.schema.json"),
    ("data/clients_database.json", "clients_database.schema.json"),
    ("data/captures/*/client_intent.json", "client_intent.schema.json"),
    ("deliverables/growthcro_data_v17.json", "dashboard_v17_data.schema.json"),
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sample", type=int, default=0, help="N pages only per glob")
    args = p.parse_args()

    errors = 0
    total = 0

    for glob_pat, schema_name in PAIRS:
        schema = json.loads((SCHEMA_DIR / schema_name).read_text())
        files = list(ROOT.glob(glob_pat))
        if args.sample and len(files) > args.sample:
            files = random.sample(files, args.sample)
        print(f"\n── {glob_pat} ({len(files)} files) → {schema_name} ──")
        for f in files:
            total += 1
            try:
                data = json.loads(f.read_text())
                jsonschema.validate(instance=data, schema=schema)
            except jsonschema.ValidationError as e:
                errors += 1
                rel = f.relative_to(ROOT)
                print(f"  ✗ {rel}")
                print(f"    path: {' → '.join(str(p) for p in e.absolute_path)}")
                print(f"    msg : {e.message[:120]}")
            except json.JSONDecodeError as e:
                errors += 1
                print(f"  ✗ {f.relative_to(ROOT)}: JSON decode error at line {e.lineno}")

    print(f"\n{'═' * 60}")
    if errors == 0:
        print(f"✓ {total} files validated — all passing")
        sys.exit(0)
    else:
        print(f"✗ {errors}/{total} validation errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
