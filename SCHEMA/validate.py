#!/usr/bin/env python3
"""
Validate un fichier JSON contre un schema.

Usage:
    python3 SCHEMA/validate.py data/captures/japhy/home/score_hero.json SCHEMA/score_pillar.schema.json
"""
import json, sys, pathlib

try:
    import jsonschema
except ImportError:
    print("✗ jsonschema not installed. Run: pip install jsonschema")
    sys.exit(2)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    target = pathlib.Path(sys.argv[1])
    schema = pathlib.Path(sys.argv[2])
    if not target.exists():
        print(f"✗ Target file not found: {target}")
        sys.exit(1)
    if not schema.exists():
        print(f"✗ Schema file not found: {schema}")
        sys.exit(1)
    data = json.loads(target.read_text())
    sch = json.loads(schema.read_text())
    try:
        jsonschema.validate(instance=data, schema=sch)
        print(f"✓ {target.name} valide contre {schema.name}")
        sys.exit(0)
    except jsonschema.ValidationError as e:
        print(f"✗ Validation error in {target.name}:")
        print(f"  path: {' → '.join(str(p) for p in e.absolute_path)}")
        print(f"  msg : {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
