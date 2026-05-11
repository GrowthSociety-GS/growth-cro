#!/usr/bin/env python3
"""One-shot migration: replace os.environ / os.getenv with growthcro.config.

Run once for issue #3 of the codebase-cleanup epic. Two passes:

1. **Gut .env self-loader blocks.** Legacy code reimplements its own
   `.env` parsing; with `growthcro/config.py` autoloading, those blocks are
   dead. We detect each `os.environ[<key>] = <value>` assignment, walk up to
   the nearest enclosing loader-head (`env_path = ... ".env"`,
   `def _load_dotenv...`, `if not <env-check>:`), and delete the whole
   region.

2. **Substitute reads.** `os.environ.get("ANTHROPIC_API_KEY")` →
   `config.anthropic_api_key()`, etc. Substitutions are read-only — they
   never touch `os.environ[…]` LHS contexts (which were already gutted in
   pass 1, OR are passed through `config.override_env(...)` for known CLI
   override sites).

After both passes, `from growthcro.config import config` is inserted at the
top of any file that ends up calling `config.*`.

Usage:
    python3 scripts/migrate_env_to_config.py [--dry-run]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {
    "_archive", "__pycache__", "node_modules", "worktrees",
    ".git", ".venv", "venv", "env",
}
ALLOWLIST = {
    ROOT / "growthcro" / "config.py",
    ROOT / "scripts" / "migrate_env_to_config.py",
}


# ─────────────────────────────────────────────────────────────────────
# Pass 1 — gut .env self-loader blocks
# ─────────────────────────────────────────────────────────────────────
LOADER_START_PATTERNS = (
    # `env_path = ROOT / ".env"`, `ENV_FILE = ROOT / ".env"`, etc.
    re.compile(r'^([ \t]*)(?:env_path|env_file|env|ENV_FILE|ENV_PATH)\s*=\s*[^\n]*\.env'),
    # `def _load_dotenv(...):`
    re.compile(r'^([ \t]*)def\s+_load_dotenv(?:_if_needed)?\s*\('),
    # `if not os.environ.get("X"):` / `if not config.x_key():`
    re.compile(r'^([ \t]*)if\s+not\s+(?:os\.environ\.get\(\s*["\'][A-Z0-9_]+["\']\s*\)|config\.[a-z_]+\(\))\s*:\s*$'),
    # `if os.environ.get("X"):` (presence guard before loader)
    re.compile(r'^([ \t]*)if\s+(?:os\.environ\.get\(\s*["\'][A-Z0-9_]+["\']\s*\)|config\.[a-z_]+\(\))\s*:\s*$'),
)

LOADER_ASSIGN_RX = re.compile(
    r'^[ \t]+os\.environ\[\s*(?:["\'][A-Z0-9_]+["\']|[a-zA-Z_][a-zA-Z0-9_]*)\s*\]\s*=\s*'
)

LOADER_BODY_HINTS = (
    re.compile(r'\.env\b'),
    re.compile(r'\bread_text\(\)\.splitlines\(\)'),
    re.compile(r'\bline\.split\(\s*["\']=["\']'),
    re.compile(r'\bline\.startswith\(\s*["\'][A-Z0-9_]+=["\']'),
    re.compile(r'^\s*k\s*,\s*(?:_\s*,\s*)?v\s*=\s*line'),
    re.compile(r'os\.environ\[\s*k\s*\]'),
    re.compile(r'os\.environ\[\s*["\'][A-Z0-9_]+["\']\s*\]\s*='),
)


def _line_indent(s: str) -> int:
    return len(s) - len(s.lstrip(" \t"))


def _block_looks_like_loader(lines: list[str], start: int, end: int) -> bool:
    """A block is a loader if at least one body line matches a loader-hint."""
    body = "".join(lines[start + 1:end])
    if not body.strip():
        return False
    return any(p.search(body) for p in LOADER_BODY_HINTS)


def gut_loader_blocks(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    keep = [True] * len(lines)
    n_blocks = 0

    assign_indices = [i for i, l in enumerate(lines) if LOADER_ASSIGN_RX.match(l)]

    for ai in assign_indices:
        if not keep[ai]:
            continue

        # Walk backward to find the OUTERMOST loader-start. We track the
        # lowest-indent head pattern seen while walking up to the top of file
        # (or to a non-loader, non-blank line at indent 0).
        start = None
        start_indent = -1
        for j in range(ai - 1, -1, -1):
            line = lines[j]
            if not line.strip():
                continue
            li = _line_indent(line)
            is_head = any(pat.match(line) for pat in LOADER_START_PATTERNS)
            if is_head:
                if start is None or li < start_indent:
                    start = j
                    start_indent = li
                continue
            # Treat known intermediate wrappers as "still inside the loader" and walk past them.
            if re.match(
                r'^[ \t]*(?:for\s+line\s+in|with\s+open|if\s+(?:env_path|env_file|env|ENV_FILE|ENV_PATH)\.(?:exists|is_file)\(\)|if\s+line\.startswith|if\s+not\s+line|if\s+line\.strip|if\s+["\']=["\']\s+not\s+in\s+line|k\s*,\s*(?:_\s*,\s*)?v\s*=\s*line)',
                line,
            ):
                continue
            # Lower-indent line that's not a head and not an intermediate → bail unless we already have a start.
            if li == 0:
                break
            if start is not None and li < start_indent:
                # Already have a head; this lower line is unrelated.
                break

        if start is None:
            continue

        # Walk forward from start to end of block: stop at first non-blank
        # line whose indent <= start_indent.
        end = ai + 1
        while end < len(lines):
            line = lines[end]
            if not line.strip():
                end += 1
                continue
            if _line_indent(line) <= start_indent:
                break
            end += 1

        # If start is at indent 0 and is a `<var> = ROOT / ".env"` assignment,
        # the "block" is just that one line. Extend forward to absorb any
        # immediately-following `if <var>.exists():` or `for line in <var>...:`
        # blocks at the same indent.
        if start_indent == 0 and re.match(
            r'^[ \t]*(?:env_path|env_file|env|ENV_FILE|ENV_PATH)\s*=\s*[^\n]*\.env',
            lines[start],
        ):
            varname_match = re.match(r'^\s*(\w+)\s*=', lines[start])
            varname = varname_match.group(1) if varname_match else None
            if varname:
                while end < len(lines):
                    line = lines[end]
                    s = line.strip()
                    if not s:
                        end += 1
                        continue
                    li = _line_indent(line)
                    if li != 0:
                        break
                    if re.match(
                        rf'^if\s+{re.escape(varname)}\.(?:exists|is_file)\(\)',
                        s,
                    ) or re.match(
                        rf'^for\s+line\s+in\s+{re.escape(varname)}\.read_text',
                        s,
                    ):
                        # Absorb this top-level block + its body.
                        end += 1
                        while end < len(lines):
                            inner = lines[end]
                            if not inner.strip():
                                end += 1
                                continue
                            if _line_indent(inner) == 0:
                                break
                            end += 1
                        continue
                    break

        # Sanity check: the block body should look like a loader.
        if not _block_looks_like_loader(lines, start, end):
            continue

        for k in range(start, end):
            keep[k] = False
        n_blocks += 1

    # Drop trailing standalone `_load_dotenv()` / `_load_dotenv_if_needed()` /
    # `_ensure_api_key()` calls.
    standalone_call = re.compile(r'^\s*(?:_load_dotenv(?:_if_needed)?|_ensure_api_key)\s*\(\s*\)\s*$')
    for i, line in enumerate(lines):
        if keep[i] and standalone_call.match(line):
            keep[i] = False

    # Drop function definitions whose entire body was gutted (now empty).
    # A `def X(...):` is empty if the next kept non-blank line is at same-or-lower indent.
    def_rx = re.compile(r'^([ \t]*)(?:async\s+)?def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*$')
    for i, line in enumerate(lines):
        if not keep[i]:
            continue
        m = def_rx.match(line)
        if not m:
            continue
        def_indent = len(m.group(1))
        next_kept = None
        for j in range(i + 1, len(lines)):
            if not keep[j]:
                continue
            if not lines[j].strip():
                continue
            next_kept = j
            break
        if next_kept is None:
            keep[i] = False
            continue
        next_indent = _line_indent(lines[next_kept])
        if next_indent <= def_indent:
            keep[i] = False

    new_text = "".join(l for l, k in zip(lines, keep) if k)
    return new_text, n_blocks


# ─────────────────────────────────────────────────────────────────────
# Pass 2 — read substitutions (NEVER touches LHS assignments)
# ─────────────────────────────────────────────────────────────────────
# Negative lookahead `(?!...)` makes sure we don't match an `os.environ["X"]`
# whose context is `= …` (assignment LHS). For comparisons (`==`), keep matching.
LHS_NA = r'(?!\s*=\s*[^=])'

SUBS: list[tuple[re.Pattern, str]] = [
    # ── Specific known vars: indexed reads ───────────────────────────
    (re.compile(r'os\.environ\[\s*["\']ANTHROPIC_API_KEY["\']\s*\]' + LHS_NA),
     'config.require_anthropic_api_key()'),
    (re.compile(r'os\.environ\[\s*["\']APIFY_TOKEN["\']\s*\]' + LHS_NA),
     'config.require_apify_token()'),
    (re.compile(r'os\.environ\[\s*["\']OPENAI_API_KEY["\']\s*\]' + LHS_NA),
     'config.openai_api_key()'),
    (re.compile(r'os\.environ\[\s*["\']PERPLEXITY_API_KEY["\']\s*\]' + LHS_NA),
     'config.perplexity_api_key()'),

    # ── os.environ.get with default (catch defaulted forms first) ────
    (re.compile(r'os\.environ\.get\(\s*["\']PORT["\']\s*,\s*(\d+)\s*\)'),
     r'config.port(default=\1)'),
    (re.compile(r'int\(\s*config\.port\(default=(\d+)\)\s*\)'),
     r'config.port(default=\1)'),
    (re.compile(r'os\.environ\.get\(\s*["\']GROWTHCRO_WEB_VITALS_PROVIDER["\']\s*,\s*["\']([^"\']*)["\']\s*\)'),
     r'config.web_vitals_provider("\1")'),
    (re.compile(r'os\.environ\.get\(\s*["\']GROWTHCRO_PSI_KEY["\']\s*,\s*["\']([^"\']*)["\']\s*\)'),
     r'(config.psi_key() or "\1")'),
    (re.compile(r'os\.environ\.get\(\s*["\']GROWTHCRO_CRUX_KEY["\']\s*,\s*["\']([^"\']*)["\']\s*\)'),
     r'(config.crux_key() or "\1")'),
    (re.compile(r'os\.environ\.get\(\s*["\']BRIGHTDATA_AUTH["\']\s*,\s*["\'][^"\']*["\']\s*\)'),
     'config.brightdata_auth()'),
    (re.compile(r'os\.environ\.get\(\s*["\']BRIGHTDATA_WSS["\']\s*,\s*["\'][^"\']*["\']\s*\)'),
     'config.brightdata_wss()'),
    (re.compile(r'os\.environ\.get\(\s*["\']BROWSER_WS_ENDPOINT["\']\s*,\s*["\'][^"\']*["\']\s*\)'),
     'config.browser_ws_endpoint()'),
    (re.compile(r'os\.environ\.get\(\s*["\']PATH["\']\s*,\s*["\']([^"\']*)["\']\s*\)'),
     r'config.system_env("PATH", "\1")'),
    (re.compile(r'os\.environ\.get\(\s*["\']SHELL["\']\s*,\s*["\']([^"\']*)["\']\s*\)'),
     r'config.system_env("SHELL", "\1")'),

    # ── Bool toggles (with or without default) ───────────────────────
    (re.compile(r'os\.environ\.get\(\s*["\']GHOST_HEADED["\']\s*(?:,\s*["\']0["\']\s*)?\)\s*==\s*["\']1["\']'),
     'config.is_ghost_headed()'),
    (re.compile(r'os\.environ\.get\(\s*["\']AGGRESSIVE_CMP["\']\s*(?:,\s*["\']0["\']\s*)?\)\s*==\s*["\']1["\']'),
     'config.is_aggressive_cmp()'),

    # ── No-default reads of known vars ───────────────────────────────
    (re.compile(r'os\.environ\.get\(\s*["\']ANTHROPIC_API_KEY["\']\s*\)'),
     'config.anthropic_api_key()'),
    (re.compile(r'os\.environ\.get\(\s*["\']APIFY_TOKEN["\']\s*\)'),
     'config.apify_token()'),
    (re.compile(r'os\.environ\.get\(\s*["\']OPENAI_API_KEY["\']\s*\)'),
     'config.openai_api_key()'),
    (re.compile(r'os\.environ\.get\(\s*["\']PERPLEXITY_API_KEY["\']\s*\)'),
     'config.perplexity_api_key()'),
    (re.compile(r'os\.environ\.get\(\s*["\']GROWTHCRO_CRUX_KEY["\']\s*\)'),
     'config.crux_key()'),
    (re.compile(r'os\.environ\.get\(\s*["\']GROWTHCRO_PSI_KEY["\']\s*\)'),
     'config.psi_key()'),
    (re.compile(r'os\.environ\.get\(\s*["\']BRIGHTDATA_AUTH["\']\s*\)'),
     'config.brightdata_auth()'),
    (re.compile(r'os\.environ\.get\(\s*["\']BRIGHTDATA_WSS["\']\s*\)'),
     'config.brightdata_wss()'),
    (re.compile(r'os\.environ\.get\(\s*["\']BROWSER_WS_ENDPOINT["\']\s*\)'),
     'config.browser_ws_endpoint()'),
    (re.compile(r'os\.environ\.get\(\s*["\']GROWTHCRO_WEB_VITALS_PROVIDER["\']\s*\)'),
     'config.web_vitals_provider()'),
    (re.compile(r'os\.environ\.get\(\s*["\']PATH["\']\s*\)'),
     'config.system_env("PATH")'),
    (re.compile(r'os\.environ\.get\(\s*["\']SHELL["\']\s*\)'),
     'config.system_env("SHELL")'),

    # ── os.getenv(...) variants ──────────────────────────────────────
    (re.compile(r'os\.getenv\(\s*["\']ANTHROPIC_API_KEY["\']\s*\)'),
     'config.anthropic_api_key()'),
    (re.compile(r'os\.getenv\(\s*["\']APIFY_TOKEN["\']\s*\)'),
     'config.apify_token()'),
    (re.compile(r'os\.getenv\(\s*["\']OPENAI_API_KEY["\']\s*\)'),
     'config.openai_api_key()'),
    (re.compile(r'os\.getenv\(\s*["\']PERPLEXITY_API_KEY["\']\s*\)'),
     'config.perplexity_api_key()'),

    # ── Setter for known CLI override sites ──────────────────────────
    (re.compile(r'os\.environ\[\s*["\']GROWTHCRO_WEB_VITALS_PROVIDER["\']\s*\]\s*=\s*([^\n]+)'),
     r'config.override_env("GROWTHCRO_WEB_VITALS_PROVIDER", \1)'),

    # ── Dict spread / merge ──────────────────────────────────────────
    (re.compile(r'\{\s*\*\*\s*os\.environ\s*\}'),
     'config.system_env_copy()'),
    (re.compile(r'\*\*\s*os\.environ\b'),
     '**config.system_env_copy()'),
    (re.compile(r'os\.environ\.copy\(\)'),
     'config.system_env_copy()'),

    # ── Generic identifier passthrough (variable-name access) ────────
    # NOTE: must come after specific literal subs above.
    (re.compile(r'os\.environ\.get\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*([^)]+)\)'),
     r'config.system_env(\1, \2)'),
    (re.compile(r'os\.environ\.get\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)'),
     r'config.system_env(\1)'),
]


# ─────────────────────────────────────────────────────────────────────
# Import insertion
# ─────────────────────────────────────────────────────────────────────
def needs_config_import(text: str) -> bool:
    return "config." in text and "from growthcro.config import config" not in text


def insert_config_import(text: str) -> str:
    """Insert `from growthcro.config import config` after the file's top-level
    imports — never inside a try/except, function body, or `if __name__` block.

    Strategy: walk the first 200 lines; track top-level (indent 0) only.
    Stop tracking once we hit non-trivial top-level code (function def,
    class def, control flow). Insert position is the line just after the
    last top-level import-or-docstring line.
    """
    lines = text.splitlines(keepends=True)
    new_line = "from growthcro.config import config\n"
    if any(l.rstrip() == new_line.rstrip() for l in lines):
        return text

    insert_at = 0
    in_docstring = False
    dq = None

    for i, line in enumerate(lines[:200]):
        stripped = line.strip()
        # Track module-level docstring (first triple-quoted block at indent 0).
        if not in_docstring and i < 50:
            if stripped.startswith(('"""', "'''")):
                q = stripped[:3]
                rest = stripped[3:]
                if q in rest:
                    insert_at = i + 1
                else:
                    in_docstring = True
                    dq = q
                continue
        elif in_docstring:
            if dq and dq in stripped:
                in_docstring = False
                insert_at = i + 1
            continue

        # Skip blank lines / comments.
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level (indent 0) only.
        if line[:1] in (" ", "\t"):
            # Indented — likely inside try/def/class. Don't track but keep scanning;
            # we may emerge back to indent 0 with more imports.
            continue

        if stripped.startswith(("import ", "from ")):
            insert_at = i + 1
            continue

        # Path / ROOT setup at module top: track it so the config import lands
        # AFTER the sys.path tweak. Without this, scripts launched from
        # subdirectories can't find `growthcro/`.
        if (
            stripped.startswith(("ROOT", "PROJECT_ROOT", "REPO_ROOT"))
            or "sys.path.insert" in stripped
            or "sys.path.append" in stripped
            or stripped.startswith("from __future__")
        ):
            insert_at = i + 1
            continue

        # Other top-level statements that should NOT be counted as
        # "import region": try, def, class, if __name__, decorators, etc.
        if stripped.startswith((
            "try:", "try ", "def ", "class ", "@", "if ", "for ", "while ",
            "with ", "async ", "match ",
        )):
            break
        # An expression / assignment at top level — also stop.
        break

    lines.insert(insert_at, new_line)
    return "".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────
def transform(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    new = text

    # Pass 1: gut loader blocks (now-dead .env autoloaders).
    new, n_gut = gut_loader_blocks(new)
    if n_gut:
        notes.append(f"gutted {n_gut} loader block(s)")

    # Pass 2: read substitutions.
    n_subs = 0
    for pat, repl in SUBS:
        new, k = pat.subn(repl, new)
        n_subs += k
    if n_subs:
        notes.append(f"sub×{n_subs}")

    if "config." in new and needs_config_import(new):
        new = insert_config_import(new)
        notes.append("inserted import")

    return new, notes


def has_active_os_env(text: str) -> bool:
    return bool(re.search(r"\bos\.(environ|getenv)\b", text))


def is_active_py(path: pathlib.Path) -> bool:
    if not path.is_file() or path.suffix != ".py":
        return False
    if path in ALLOWLIST:
        return False
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = 0
    skipped_with_residue: list[pathlib.Path] = []
    for path in sorted(ROOT.rglob("*.py")):
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            continue
        if not is_active_py(path):
            continue
        text = path.read_text(encoding="utf-8")
        new, notes = transform(text)
        if new == text:
            if has_active_os_env(text):
                skipped_with_residue.append(rel)
            continue
        if has_active_os_env(new):
            skipped_with_residue.append(rel)
        if args.dry_run:
            print(f"WOULD-EDIT  {rel}: {', '.join(notes)}")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"EDITED      {rel}: {', '.join(notes)}")
        changed += 1

    print(f"\n{changed} file(s) {'would be ' if args.dry_run else ''}touched.")
    if skipped_with_residue:
        print(f"\n{len(skipped_with_residue)} file(s) still contain os.environ/os.getenv after pass:")
        for p in skipped_with_residue:
            print(f"  - {p}")
        print("→ Hand-fix those before commit.")
    return 0 if not skipped_with_residue else 1


if __name__ == "__main__":
    sys.exit(main())
