"""Entry point so `python -m growthcro.geo` works.

Delegates immediately to `growthcro.geo.cli.main()` — mono-concern shim.
"""
from growthcro.geo.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
