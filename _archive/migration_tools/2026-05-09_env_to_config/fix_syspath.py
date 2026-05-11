#!/usr/bin/env python3
"""Post-migration fixer: ensure `from growthcro.config import config` resolves
when scripts are launched directly from a subdirectory.

Strategy: for every active .py file that imports growthcro.config but does
not already manipulate sys.path before the import, insert a 4-line bootstrap
just before the import. The bootstrap walks up parents until it finds
`growthcro/config.py`, then prepends that directory to sys.path.

This is run once for issue #3 of the codebase-cleanup epic, immediately
after migrate_env_to_config.py.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

EXCLUDE_DIRS = {
    "_archive", "__pycache__", "node_modules", "worktrees",
    ".git", ".venv", "venv", "env", "growthcro",
}

BOOTSTRAP = (
    "# growthcro path bootstrap — keep before `from growthcro.config import config`\n"
    "import pathlib as _gc_pl, sys as _gc_sys\n"
    "_gc_root = _gc_pl.Path(__file__).resolve()\n"
    "while _gc_root.parent != _gc_root and not (_gc_root / 'growthcro' / 'config.py').is_file():\n"
    "    _gc_root = _gc_root.parent\n"
    "if str(_gc_root) not in _gc_sys.path:\n"
    "    _gc_sys.path.insert(0, str(_gc_root))\n"
    "del _gc_pl, _gc_sys, _gc_root\n"
)

CONFIG_IMPORT_RX = re.compile(r'^from growthcro\.config import config\s*$', re.MULTILINE)


def needs_bootstrap(text: str) -> bool:
    if "from growthcro.config import config" not in text:
        return False
    if "_gc_root" in text:  # already bootstrapped
        return False
    head = text.split("from growthcro.config import config", 1)[0]
    return "sys.path.insert" not in head and "sys.path.append" not in head


def is_active_py(path: pathlib.Path) -> bool:
    if not path.is_file() or path.suffix != ".py":
        return False
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return False
    return True


def main() -> int:
    fixed = 0
    for path in sorted(ROOT.rglob("*.py")):
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            continue
        if not is_active_py(path):
            continue
        text = path.read_text(encoding="utf-8")
        if not needs_bootstrap(text):
            continue
        new = CONFIG_IMPORT_RX.sub(BOOTSTRAP + "from growthcro.config import config", text, count=1)
        if new == text:
            continue
        path.write_text(new, encoding="utf-8")
        print(f"FIXED  {rel}")
        fixed += 1
    print(f"\n{fixed} file(s) bootstrapped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
