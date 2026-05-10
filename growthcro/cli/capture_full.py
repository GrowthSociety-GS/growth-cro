#!/usr/bin/env python3
"""
capture_full.py — Orchestrateur V13 SaaS-grade (ghost-first, cloud-native).

Doctrine : **Playwright = source unique de vérité**, pas urllib.
Un vrai navigateur (Chrome + stealth) est invisible pour les CDN (Cloudflare,
Shopify Shield, Akamai) qui bloquent urllib via TLS fingerprint. On capture
une fois avec ghost_capture, puis on dérive `capture.json` du DOM rendered via
`native_capture --html` (ré-utilise 100% du parser existant — même schéma).

**MODES DE CAPTURE (Stage 1) :**
    --cloud              Python Playwright → navigateur distant (Browserless.io, etc.)
                         ZERO install local. Mode par défaut pour le SaaS.
                         Requiert : pip install playwright + env BROWSER_WS_ENDPOINT
    (défaut)             Python Playwright → Chromium local
                         Requiert : pip install playwright && playwright install chromium
    --legacy-node        Node.js ghost_capture.js → Chromium local (DEPRECATED)
                         Requiert : Node.js + npm install playwright
    --legacy-urllib      urllib natif (DEPRECATED, fragile vs CDN)

Chaîne (100% natif, pas d'IA) :
    1. ghost_capture_cloud.py       → data/captures/<label>/<page>/
       (ou ghost_capture.js legacy)    ├─ spatial_v9.json   (bbox clusters)
                                       ├─ page.html         (DOM rendered)
                                       └─ screenshots/*.png
    2. native_capture.py --html     → data/captures/<label>/<page>/
                                       └─ capture.json      (6 piliers sémantiques, dérivé du DOM)
    3. perception_v13.py            → data/captures/<label>/<page>/
                                       └─ perception_v13.json (DBSCAN clusters + roles)
    4. intent_detector_v13.py       → data/captures/<label>/
                                       └─ client_intent.json (intent par client)

Stage 2 (dérivation) passe **toujours** si stage 1 passe, car on lit un fichier
local. Le seul point de friction web est stage 1 (navigation Playwright). Le
Sonnet/LLM reste exclusivement en stage 8 (reco_enricher_v13_api), séparément.

Usage :
    # Mode cloud (SaaS — recommandé)
    BROWSER_WS_ENDPOINT="wss://chrome.browserless.io?token=XXX" \\
    python3 capture_full.py https://japhy.fr japhy dtc_food --cloud

    # Mode local Python (zéro Node.js)
    python3 capture_full.py https://japhy.fr japhy dtc_food --page-type home

    # Mode legacy Node (deprecated)
    python3 capture_full.py https://japhy.fr japhy dtc_food --legacy-node

Options :
    --page-type <type>   home (défaut) | pdp | blog | pricing | collection | lp_leadgen | quiz_vsl
    --cloud              Utilise ghost_capture_cloud.py + navigateur distant
    --no-intent          Skip stage 4
    --skip-ghost         Skip stage 1 si spatial_v9.json + page.html déjà présents
    --skip-capture       Skip stage 2 si capture.json déjà présent
    --legacy-node        Utilise ghost_capture.js (Node, DEPRECATED)
    --legacy-urllib      Utilise urllib (DEPRECATED, fragile vs CDN modernes)

Après capture_full, pour compléter le pipeline (scoring + recos) :
    python3 skills/site-capture/scripts/batch_rescore.py --only <label>
    python3 skills/site-capture/scripts/reco_enricher.py <label> <page>
    python3 skills/site-capture/scripts/reco_enricher_v13.py --client <label> --page <page> --prepare
    python3 skills/site-capture/scripts/reco_enricher_v13_api.py --client <label> --page <page> \\
        --model claude-sonnet-4-6 --max-concurrent 5

v3.0 — 2026-04-17 (pivot cloud-native : Python Playwright + Browserless.io)
v2.0 — 2026-04-15 (pivot ghost-first : Playwright = source unique)
v1.0 — 2026-04-15 (initial : urllib → ghost → perception → intent)
"""

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import time

from growthcro.config import config

# After relocation under growthcro/cli/, climb 2 levels to repo root.
ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "site-capture" / "scripts"
CAPTURES = ROOT / "data" / "captures"

# Import check_liveness depuis enrich_client (lazy anthropic, zéro dep inutile)
# pour le pre-flight fail-fast avant de lancer Playwright.
try:
    from growthcro.cli.enrich_client import check_liveness as _check_liveness
    _LIVENESS_AVAILABLE = True
except Exception as _e:
    _LIVENESS_AVAILABLE = False
    _LIVENESS_IMPORT_ERR = str(_e)


def preflight_liveness(url: str) -> int:
    """
    Retourne :
       0  → URL saine (2xx/3xx), OK pour ghost
       1  → URL probablement bot-bloquée par CDN (0/403/406/429/503), laisse passer
       2  → URL morte (DNS fail, 404, 410, 5xx), FAIL-FAST
    Diag humain imprimé directement dans la console.
    """
    if not _LIVENESS_AVAILABLE:
        print(f"\n⚠️  Pre-flight skipped (enrich_client import failed: {_LIVENESS_IMPORT_ERR})")
        return 0
    print(f"\n[0/4 pre-flight] Liveness check {url}…")
    live = _check_liveness(url, timeout=10)
    status = live.get("status", 0)
    if live["ok"]:
        print(f"[0/4 pre-flight] ✅ status={status} · final_url={live['final_url']}")
        return 0
    # Cas clairs de mort côté HTTP (404/410/5xx)
    if status in (404, 410):
        print(f"[0/4 pre-flight] ❌ URL retourne {status} — page introuvable.")
        print(f"    Vérifie l'URL, ou corrige dans clients_database.json.")
        return 2
    if 500 <= status < 600:
        print(f"[0/4 pre-flight] ❌ URL retourne {status} — serveur KO.")
        print(f"    Retry plus tard ou vérifie l'état du site.")
        return 2
    # status=0 → introspection du message d'erreur pour distinguer DNS mort
    # (fatal) vs. TLS fingerprint rejeté (bot-block → on passe à Playwright).
    err = (live.get("error") or "").lower()
    dns_markers = [
        "not known", "name or service", "nodename", "servname",
        "gaierror", "no address associated", "temporary failure in name",
        "name resolution",
    ]
    if any(m in err for m in dns_markers):
        print(f"[0/4 pre-flight] ❌ DNS ne résout pas `{url}`.")
        print(f"    Le domaine n'existe pas (ou plus). Corrige l'URL.")
        print(f"    Diag : {live.get('error', '?')}")
        return 2
    # Bot-block signatures (403/406/429/503 ou TLS handshake rejeté, timeout CDN)
    if status in (403, 406, 429, 503):
        print(f"[0/4 pre-flight] 🛡️  urllib bloqué (status={status}) — "
              f"bot-protection CDN probable. Laisse passer à Playwright.")
        return 1
    if status == 0:
        print(f"[0/4 pre-flight] 🛡️  urllib bloqué (status=0, err={live.get('error', '?')[:80]}) — "
              f"probable TLS fingerprint CDN. Laisse passer à Playwright.")
        return 1
    # Inconnu — soft-pass vers Playwright
    print(f"[0/4 pre-flight] ⚠️  status={status} ambigu — on laisse Playwright trancher.")
    return 1


def resolve_binary(name, common_paths):
    """
    Résout un binaire avec plusieurs stratégies :
      1) PATH du process actuel
      2) PATH enrichi (Homebrew ARM + Intel + /usr/local + /usr/bin)
      3) Emplacements macOS classiques (nvm, asdf, volta, fnm, MacPorts, DMG installer)
      4) Source le shell interactif utilisateur (`zsh -i -c "command -v <name>"`)
         → charge .zshrc / .bashrc avec toutes les init des version-managers
    Retourne le chemin absolu ou None.
    """
    # 1) PATH du process actuel
    found = shutil.which(name)
    if found:
        return found

    # 2) PATH enrichi
    extended_path = os.pathsep.join([
        config.system_env("PATH", ""),
        "/opt/homebrew/bin",            # Homebrew Apple silicon
        "/usr/local/bin",               # Homebrew Intel + system
        "/usr/local/opt/node/bin",      # Homebrew formula node
        "/opt/local/bin",               # MacPorts
        "/usr/bin", "/bin",
    ])
    found = shutil.which(name, path=extended_path)
    if found:
        return found

    # 3) Emplacements classiques
    home = pathlib.Path.home()
    # nvm — version la plus récente
    nvm_versions = home / ".nvm" / "versions" / "node"
    if nvm_versions.exists():
        versions = sorted([p for p in nvm_versions.iterdir() if p.is_dir()], reverse=True)
        for v in versions:
            candidate = v / "bin" / name
            if candidate.exists():
                return str(candidate)
    # fnm — shell-integration path (~/.local/state/fnm_multishells/...)
    fnm_state = home / ".local" / "state" / "fnm_multishells"
    if fnm_state.exists():
        for shell_dir in sorted(fnm_state.iterdir(), reverse=True):
            cand = shell_dir / "bin" / name
            if cand.exists():
                return str(cand)
    # fnm standalone
    fnm_home = home / "Library" / "Application Support" / "fnm" / "node-versions"
    if fnm_home.exists():
        for v in sorted(fnm_home.iterdir(), reverse=True):
            cand = v / "installation" / "bin" / name
            if cand.exists():
                return str(cand)

    for p in common_paths:
        cand = pathlib.Path(os.path.expandvars(os.path.expanduser(p)))
        if cand.exists():
            return str(cand)

    # 4) Dernier recours : shell interactif (charge .zshrc → nvm/fnm init)
    try:
        shell = config.system_env("SHELL", "/bin/zsh")
        r = subprocess.run(
            [shell, "-i", "-c", f"command -v {name}"],
            capture_output=True, text=True, timeout=5,
        )
        path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        if path and pathlib.Path(path).exists():
            return path
    except Exception:
        pass

    return None


# Résolution binaires
NODE_BIN = resolve_binary("node", [
    "~/.asdf/shims/node",
    "~/.volta/bin/node",
])
PYTHON_BIN = resolve_binary("python3", [
    "~/.pyenv/shims/python3",
    "/opt/homebrew/bin/python3",
    "/usr/local/bin/python3",
]) or sys.executable


def run(cmd, label, cwd=None):
    """Exécute une commande, imprime le temps et le code de sortie, retourne True si OK."""
    print(f"\n[{label}] $ {' '.join(cmd)}")
    t0 = time.time()
    try:
        # Enrichit PATH pour les subprocesses (node/python peuvent appeler d'autres binaires)
        env = config.system_env_copy()
        env["PATH"] = os.pathsep.join([
            env.get("PATH", ""),
            "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin",
        ])
        r = subprocess.run(cmd, cwd=cwd, env=env)
        rc = r.returncode
    except FileNotFoundError as e:
        print(f"[{label}] ❌ binaire introuvable : {e}")
        print(f"    NODE_BIN   = {NODE_BIN}")
        print(f"    PYTHON_BIN = {PYTHON_BIN}")
        print(f"    PATH       = {config.system_env("PATH", "")[:200]}…")
        return False
    except Exception as e:
        print(f"[{label}] ❌ exception: {e}")
        return False
    dt = time.time() - t0
    print(f"[{label}] {'✅' if rc == 0 else '❌'} exit={rc} in {dt:.1f}s")
    return rc == 0


def check(path, label):
    ok = path.exists() and path.stat().st_size > 0
    print(f"  {'✅' if ok else '❌'} {label}: {path}")
    return ok


def main():
    ap = argparse.ArgumentParser(
        description="Pipeline natif V13 SaaS-grade : ghost → capture.json dérivé → perception → intent"
    )
    ap.add_argument("url", help="URL absolue du site (ex: https://bigmoustache.com)")
    ap.add_argument("label", help="Label client (ex: big_moustache)")
    ap.add_argument("biz_category", help="Catégorie business (ecommerce, saas, leadgen, ...)")
    ap.add_argument("--page-type", default="home",
                    choices=["home", "pdp", "blog", "pricing", "collection",
                             "lp_leadgen", "quiz_vsl"],
                    help="Type de page (défaut: home)")
    ap.add_argument("--cloud", action="store_true",
                    help="Mode cloud : Python Playwright → navigateur distant (Browserless.io)")
    ap.add_argument("--no-intent", action="store_true",
                    help="Skip stage 4 (intent_detector_v13)")
    ap.add_argument("--skip-ghost", action="store_true",
                    help="Skip stage 1 si spatial_v9.json + page.html déjà présents")
    ap.add_argument("--skip-capture", action="store_true",
                    help="Skip stage 2 si capture.json déjà présent")
    ap.add_argument("--legacy-node", action="store_true",
                    help="DEPRECATED : utilise ghost_capture.js (Node) au lieu de Python")
    ap.add_argument("--legacy-urllib", action="store_true",
                    help="DEPRECATED : urllib à la place de ghost (fragile vs CDN)")
    args = ap.parse_args()

    page = args.page_type
    page_dir = CAPTURES / args.label / page
    page_dir.mkdir(parents=True, exist_ok=True)

    spatial_json = page_dir / "spatial_v9.json"
    page_html = page_dir / "page.html"
    cap_json = page_dir / "capture.json"
    perception_json = page_dir / "perception_v13.json"
    intent_json = CAPTURES / args.label / "client_intent.json"

    # Determine capture mode
    if args.legacy_urllib:
        capture_mode = "LEGACY urllib (DEPRECATED)"
    elif args.legacy_node:
        capture_mode = "LEGACY Node.js (DEPRECATED)"
    elif args.cloud:
        capture_mode = "CLOUD (Python Playwright → navigateur distant)"
    else:
        capture_mode = "LOCAL (Python Playwright → Chromium local)"

    print("═" * 64)
    print(f" capture_full.py v3 — {args.label} / {page} ({args.biz_category})")
    print(f" URL    : {args.url}")
    print(f" OUT    : {page_dir}")
    print(f" Mode   : {capture_mode}")
    if args.legacy_node:
        print(f" node   : {NODE_BIN or '❌ introuvable'}")
    print(f" python : {PYTHON_BIN}")
    print("═" * 64)

    # ── Stage 0 : pre-flight liveness (fail-fast sur DNS mort / 404 / 5xx) ──
    # But : éviter le crash Playwright cryptique `ERR_NAME_NOT_RESOLVED` et
    # le temps perdu (~35s) quand l'URL est manifestement fausse.
    # Ne bloque PAS les sites derrière Cloudflare/Datadome (status 0/403/429).
    if not args.skip_ghost:
        preflight_rc = preflight_liveness(args.url)
        if preflight_rc == 2:
            print("\n❌ Pre-flight FAIL — URL morte, on s'arrête avant de lancer Playwright.")
            return 1

    # ═════════════════════════════════════════════════════════════
    # MODE LEGACY : urllib (ancien chemin, fragile vs CDN modernes)
    # ═════════════════════════════════════════════════════════════
    if args.legacy_urllib:
        print("\n⚠️  MODE LEGACY urllib — TLS fingerprint détecté par Cloudflare/Shopify.")
        print("    Utilisé uniquement si on veut 'fast mode' sur site simple.")
        # Stage 1 legacy : capture_site.py (urllib natif → capture.json)
        if args.skip_capture and cap_json.exists():
            print("\n[1/4 capture_site LEGACY] SKIPPED (capture.json présent)")
        else:
            run([PYTHON_BIN, str(SCRIPTS / "capture_site.py"),
                 args.url, args.label, args.biz_category],
                "1/4 capture_site LEGACY", cwd=str(ROOT))
        if not cap_json.exists():
            print(f"\n❌ LEGACY urllib FAILED — bascule sur le mode ghost-first par défaut.")
            print("    (Relance sans --legacy-urllib)")
            return 1
        # Stage 2 legacy : ghost pour spatial/screenshots seulement
        if args.skip_ghost and spatial_json.exists():
            print("\n[2/4 ghost_capture LEGACY] SKIPPED (spatial_v9.json présent)")
        else:
            if not NODE_BIN:
                print("❌ node introuvable — installe Node.js (brew install node) puis relance.")
                return 1
            run([NODE_BIN, str(SCRIPTS / "ghost_capture.js"),
                 "--url", args.url, "--label", args.label,
                 "--page-type", page, "--out-dir", str(page_dir)],
                "2/4 ghost_capture LEGACY", cwd=str(ROOT))

    # ═════════════════════════════════════════════════════════════
    # MODE LEGACY NODE (deprecated — ghost_capture.js)
    # ═════════════════════════════════════════════════════════════
    elif args.legacy_node:
        print("\n⚠️  MODE LEGACY NODE — Utilise ghost_capture.js (Node.js requis)")
        print("    Préférez le mode par défaut (Python Playwright) ou --cloud.")
        need_ghost = not (args.skip_ghost and spatial_json.exists() and page_html.exists())
        if not need_ghost:
            print(f"\n[1/4 ghost_capture.js] SKIPPED (spatial_v9 + page.html présents)")
        else:
            if not NODE_BIN:
                print("\n❌ STAGE 1 — `node` introuvable dans le PATH.")
                print("   Installe Node (brew install node) ou utilise le mode Python :")
                print("   python3 capture_full.py <url> <label> <biz>  (sans --legacy-node)")
                return 1
            run([NODE_BIN, str(SCRIPTS / "ghost_capture.js"),
                 "--url", args.url, "--label", args.label,
                 "--page-type", page, "--out-dir", str(page_dir)],
                "1/4 ghost_capture.js (legacy)", cwd=str(ROOT))

        # Gate, derive, same as before
        if not page_html.exists():
            print(f"\n❌ STAGE 1 FAILED — page.html absent à {page_html}")
            return 1

        if args.skip_capture and cap_json.exists():
            print(f"\n[2/4 native_capture (--html)] SKIPPED (capture.json présent)")
        else:
            run([PYTHON_BIN, str(SCRIPTS / "native_capture.py"),
                 args.url, args.label, page, "--html", str(page_html)],
                "2/4 native_capture (--html)", cwd=str(ROOT))

        if not cap_json.exists():
            print(f"\n❌ STAGE 2 FAILED — capture.json absent")
            return 1

    # ═════════════════════════════════════════════════════════════
    # MODE PYTHON PLAYWRIGHT (défaut ou --cloud) — SaaS-grade
    # ═════════════════════════════════════════════════════════════
    else:
        # ── Stage 1 : ghost_capture_cloud.py (Python Playwright)
        #             → page.html + spatial_v9.json + screenshots
        need_ghost = not (args.skip_ghost and spatial_json.exists() and page_html.exists())
        if not need_ghost:
            print(f"\n[1/4 ghost_capture_cloud.py] SKIPPED (spatial_v9 + page.html présents)")
        else:
            ghost_cmd = [
                PYTHON_BIN, str(ROOT / "ghost_capture_cloud.py"),
                "--url", args.url, "--label", args.label,
                "--page-type", page, "--out-dir", str(page_dir),
            ]
            if args.cloud:
                ghost_cmd.append("--cloud")
            run(ghost_cmd,
                f"1/4 ghost_capture_cloud.py ({'CLOUD' if args.cloud else 'LOCAL'})",
                cwd=str(ROOT))

        # Gate dur : stage 1 est le SEUL vrai point de friction web.
        # Si on n'a pas le HTML rendered, tout le reste est impossible.
        if not page_html.exists():
            print(f"\n❌ STAGE 1 FAILED — page.html absent à {page_html}")
            print("   Causes possibles :")
            print("   - Site derrière Cloudflare Turnstile très agressif (1% des cas)")
            print("   - Site down / timeout réseau")
            print("   - URL invalide")
            print("   Pistes :")
            print("   - Retry (souvent transitoire)")
            print("   - Vérifier l'URL dans un vrai browser")
            print("   - Ajouter proxy résidentiel (future feature)")
            return 1
        if not spatial_json.exists():
            print(f"\n⚠️  spatial_v9.json manquant — perception échouera, scoring visuel dégradé")

        # ── Stage 2 : native_capture.py --html (parse le DOM rendered → capture.json)
        # Ré-utilise 100% du parser existant, juste la source diffère.
        if args.skip_capture and cap_json.exists():
            print(f"\n[2/4 native_capture (--html)] SKIPPED (capture.json présent)")
        else:
            run([PYTHON_BIN, str(SCRIPTS / "native_capture.py"),
                 args.url, args.label, page, "--html", str(page_html)],
                "2/4 native_capture (--html)", cwd=str(ROOT))

        if not cap_json.exists():
            print(f"\n❌ STAGE 2 FAILED — capture.json absent (parser a planté sur le DOM rendered)")
            print(f"    Inspecte {page_html} manuellement pour voir ce qui cloche.")
            return 1

    # ═════════════════════════════════════════════════════════════
    # Stages communs (legacy OU ghost-first)
    # ═════════════════════════════════════════════════════════════

    # ── Stage 3 : perception_v13 (DBSCAN clusters) ────────────────
    if spatial_json.exists():
        run([PYTHON_BIN, str(SCRIPTS / "perception_v13.py"),
             "--client", args.label, "--page", page],
            "3/4 perception_v13", cwd=str(ROOT))
    else:
        print(f"\n[3/4 perception_v13] ⏭️  SKIPPED (spatial_v9.json manquant)")

    # ── Stage 4 : intent_detector_v13 (par client) ────────────────
    if args.no_intent:
        print(f"\n[4/4 intent_detector_v13] SKIPPED (--no-intent)")
    else:
        run([PYTHON_BIN, str(SCRIPTS / "intent_detector_v13.py"),
             "--client", args.label],
            "4/4 intent_detector_v13", cwd=str(ROOT))

    # ── Récap ────────────────────────────────────────────────────
    print("\n" + "═" * 64)
    print(f" RÉCAP : {args.label} / {page}")
    print("─" * 64)
    ok_html = check(page_html, "page.html           (DOM rendered par Playwright)")
    ok_cap = check(cap_json, "capture.json        (6 piliers — dérivés du DOM)")
    ok_spa = check(spatial_json, "spatial_v9.json     (bbox clusters)")
    ok_per = check(perception_json, "perception_v13.json (DBSCAN clusters + rôles)")
    ok_int = check(intent_json, "client_intent.json  (intent par client)")
    shots = page_dir / "screenshots"
    if shots.exists():
        n = sum(1 for _ in shots.glob("*.png"))
        print(f"  📸 screenshots/ : {n} PNG")
    print("═" * 64)

    # captureSource meta (pour traçabilité)
    try:
        import json
        with open(cap_json) as f:
            meta = json.load(f).get("meta", {})
        print(f"  ℹ️  capturedBy     : {meta.get('capturedBy', '?')}")
        print(f"  ℹ️  captureSource  : {meta.get('captureSource', '?')}")
    except Exception:
        pass

    full_ok = ok_cap and ok_spa and ok_per
    if full_ok:
        print("\n✅ Pipeline NATIF complet OK. Next :")
        print(f"   python3 skills/site-capture/scripts/batch_rescore.py --only {args.label}")
        print(f"   python3 skills/site-capture/scripts/reco_enricher.py {args.label} {page}")
        print(f"   python3 skills/site-capture/scripts/reco_enricher_v13.py --client {args.label} --page {page} --prepare")
        print(f"   python3 skills/site-capture/scripts/reco_enricher_v13_api.py --client {args.label} --page {page} --model claude-sonnet-4-6 --max-concurrent 5")
        return 0
    else:
        print("\n⚠️  Pipeline partiel — corriger les artifacts manquants avant scoring.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
