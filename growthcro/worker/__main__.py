"""Allow `python -m growthcro.worker` to invoke the CLI."""

from growthcro.worker.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
