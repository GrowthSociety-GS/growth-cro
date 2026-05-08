"""GSG Fix HTML Runtime V26.Z BUG-FIX — patch les LPs cassées par counter-without-JS.

Bug découvert post-Phase 1+E2 : Sonnet génère systématiquement du HTML avec
des chiffres à 0 par défaut (`<span data-target="327">0</span>`) qui dépendent
d'un JS d'animation counter — mais avec les mega-prompts gonflés V26.Z, le
bloc `<script>` est tronqué/oublié. Résultat : page visuellement morte, tous
les chiffres restent à 0.

Aussi : éléments `opacity: 0` qui dépendent d'animations reveal sans trigger,
restent invisibles indéfiniment.

Ce script post-process un HTML cassé en :
1. Pour chaque `<X data-target="N" ...>0</X>` → remplace `>0<` par `>{format(N)}<`
   (valeur finale visible par défaut, JS optionnel peut animer FROM 0)
2. Détecte `opacity: 0` dans CSS sans @keyframes associée → log warning
3. Optionnel : injecte un JS minimal qui anime les counters FROM 0 vers
   data-target via IntersectionObserver (mode --inject-counter-js)

Usage CLI :
    python3 skills/growth-site-generator/scripts/fix_html_runtime.py \\
        --input deliverables/weglot-listicle-V26Z-W123.html \\
        [--output deliverables/weglot-listicle-V26Z-W123.fixed.html] \\
        [--inject-counter-js]   # ajoute le JS d'animation si script absent
        [--in-place]            # overwrite l'input (sauve original en .bak)

Usage module :
    from fix_html_runtime import fix_html_runtime, detect_runtime_bugs
    fixed_html, report = fix_html_runtime(html, inject_js=True)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


# Minimal runtime JS fallback : counter animations + reveal classes au scroll.
# Drop-in script qui résout le bug "page morte sections invisibles" quand
# Sonnet a oublié d'inclure son JS.
RUNTIME_JS_FALLBACK = """
<script>
(function() {
  // V26.Z fix-html-runtime fallback (iter3)
  // 1. Counter animations : anime les data-target qui ont un texte 0
  // 2. Reveal classes : ajoute .revealed/.show/.visible/.in-view/.animated
  //    aux éléments correspondants au scroll OU au load (failsafe)

  // ─── Part 1 : counter animations ───
  const formatNumber = (n, ref) => {
    if (ref.includes(',')) return n.toLocaleString('fr-FR');
    if (ref.includes('.')) return n.toFixed(1);
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return n.toLocaleString('fr-FR');
    return Math.round(n).toString();
  };
  const animate = (el) => {
    const target = parseFloat(el.getAttribute('data-target'));
    if (isNaN(target)) return;
    const refText = el.textContent.trim();
    if (parseFloat(refText.replace(/[\\s,]/g, '')) === target) return; // déjà OK
    el.dataset.animated = '1';
    const duration = 1500;
    const start = performance.now();
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      el.textContent = formatNumber(current, refText);
      if (progress < 1) requestAnimationFrame(tick);
      else el.textContent = formatNumber(target, refText);
    }
    requestAnimationFrame(tick);
  };
  const counterEls = document.querySelectorAll('[data-target]');
  counterEls.forEach(el => {
    const txt = (el.textContent || '').trim();
    if (txt === '0' || txt === '0%' || txt === '0.0') {
      // Reveal-on-scroll for counters at 0
      if ('IntersectionObserver' in window) {
        const obs = new IntersectionObserver(es => {
          es.forEach(e => { if (e.isIntersecting && !e.target.dataset.animated) {
            animate(e.target); obs.unobserve(e.target); } });
        }, { threshold: 0.3 });
        obs.observe(el);
      } else animate(el);
    }
    // Si le texte n'est PAS 0, valeur déjà visible par défaut → no-op
  });

  // ─── Part 2 : reveal classes (.revealed/.show/.visible/.in-view/.animated) ───
  const REVEAL_CLASSES = ['revealed', 'show', 'visible', 'in-view', 'animated', 'is-visible'];
  // Pour chaque classe reveal connue, trouve les éléments qui ont une "base class"
  // mentionnée dans une règle CSS .X.Y { opacity: 1 } et applique .Y au scroll.
  // Approach simple : on lit le CSS, on détecte les paires .X.Y, on applique.
  const styleSheets = document.styleSheets;
  const pairs = new Map(); // base class → reveal class
  for (const sheet of styleSheets) {
    let rules;
    try { rules = sheet.cssRules || sheet.rules; } catch (e) { continue; }
    if (!rules) continue;
    for (const rule of rules) {
      if (!rule.selectorText) continue;
      const m = rule.selectorText.match(/\\.([a-zA-Z][\\w-]*)\\.([a-zA-Z][\\w-]*)/);
      if (m && REVEAL_CLASSES.includes(m[2])) {
        const base = m[1], modifier = m[2];
        if (!pairs.has(base)) pairs.set(base, modifier);
      }
    }
  }
  // Pour chaque paire, applique la classe reveal aux éléments visibles
  pairs.forEach((modifier, base) => {
    const els = document.querySelectorAll('.' + base);
    if ('IntersectionObserver' in window) {
      const obs = new IntersectionObserver(es => {
        es.forEach(e => { if (e.isIntersecting) {
          e.target.classList.add(modifier); obs.unobserve(e.target);
        } });
      }, { threshold: 0.1, rootMargin: '0px 0px -10% 0px' });
      els.forEach(el => obs.observe(el));
    } else {
      // Fallback ultime : tout révéler immédiatement
      els.forEach(el => el.classList.add(modifier));
    }
  });

  // Failsafe absolu : si après 3s certains base elements ne sont toujours pas
  // revealed (e.g. observer pas déclenché car virtualisé), force reveal.
  setTimeout(() => {
    pairs.forEach((modifier, base) => {
      document.querySelectorAll('.' + base + ':not(.' + modifier + ')').forEach(el => {
        el.classList.add(modifier);
      });
    });
  }, 3000);
})();
</script>
"""

# Backwards-compat alias
COUNTER_JS_FALLBACK = RUNTIME_JS_FALLBACK


def detect_reveal_pattern(html: str) -> list[tuple[str, str]]:
    """Détecte le pattern .X{opacity:0} + .X.Y{opacity:1} (reveal classes).

    Ces patterns dépendent d'un JS qui ajoute `.Y` (`.revealed`, `.visible`,
    `.show`, `.in-view`, `.animated`) au scroll via IntersectionObserver.
    Si le JS est absent, les éléments restent invisibles à jamais.

    Returns: list[(base_class, reveal_modifier)] — couples détectés.
    """
    # Find .X { opacity: 0 ; ... }
    base_with_op0 = set(re.findall(
        r'\.([a-zA-Z][\w-]*)\s*\{[^}]*opacity:\s*0[^.\d]', html
    ))
    # Find .X.Y { opacity: 1 ; ... } AND .X.Y { transform: ... } where Y is the reveal trigger
    reveal_targets = re.findall(
        r'\.([a-zA-Z][\w-]*)\.([a-zA-Z][\w-]*)\s*\{[^}]*opacity:\s*1', html
    )
    pairs = []
    for base, modifier in reveal_targets:
        if base in base_with_op0:
            pairs.append((base, modifier))
    return pairs


def detect_runtime_bugs(html: str) -> dict:
    """Audit Python pur des bugs de rendering connus.

    Returns:
      {
        "counters_with_zero_default": int,
        "counters_total": int,
        "scripts_count": int,
        "has_counter_js": bool,
        "opacity_zero_no_animation": int,
        "reveal_pattern_pairs": list[(base, modifier)],
        "has_reveal_js": bool,
        "broken_score": 0.0-1.0  (0 = parfait, 1 = totalement cassé)
      }
    """
    # Counters with 0 default
    targets_with_zero = re.findall(
        r'data-target="([^"]+)"[^>]*>\s*0\s*<', html, re.IGNORECASE
    )
    targets_all = re.findall(r'data-target="([^"]+)"', html, re.IGNORECASE)

    # Scripts
    scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html, re.IGNORECASE)
    has_counter_js = any(
        ('data-target' in s or 'animateCounter' in s or 'IntersectionObserver' in s)
        and (re.search(r'animate|counter|target|tick|requestAnimationFrame', s, re.I))
        for s in scripts
    )

    # Opacity 0 — count occurrences in style/css that aren't followed by an animation
    opacity_zero_count = len(re.findall(r'opacity:\s*0\b(?!\.\d)', html))
    has_keyframes = bool(re.search(r'@keyframes', html))
    has_reveal_transition = bool(re.search(r'transition.*opacity|opacity.*transition', html))
    opacity_zero_no_animation = (
        opacity_zero_count if (not has_keyframes and not has_reveal_transition) else 0
    )

    # V26.Z bug-fix iter3 : detect reveal pattern (.X{opacity:0} + .X.revealed{opacity:1})
    reveal_pairs = detect_reveal_pattern(html)
    # Heuristique : a-t-on un JS qui ajoute classes reveal ?
    reveal_class_names = {modifier for _, modifier in reveal_pairs}
    has_reveal_js = False
    if reveal_pairs:
        for s in scripts:
            for cls in reveal_class_names:
                if (f"classList.add('{cls}'" in s
                    or f'classList.add("{cls}"' in s
                    or f".classList.add('{cls}')" in s
                    or f"add('{cls}'" in s):
                    has_reveal_js = True
                    break
            if has_reveal_js:
                break

    # Broken score : weighted sum
    # V26.Z bug-fix iter2 : ne PAS pénaliser l'absence de JS quand le HTML est
    # self-sufficient (valeurs finales visibles par défaut). La logique métier :
    #   - chiffres à 0 + pas de JS = page morte (critical)
    #   - chiffres à 0 + JS présent = animation marche (ok, c'est la voie nominale)
    #   - chiffres OK + pas de JS = page rend, juste pas d'animation counter (ok)
    #   - chiffres OK + JS présent = animation polish (ok)
    # iter3 : reveal pattern .X{op:0} + .X.revealed{op:1} sans JS = page morte (critical)
    counters_broken = (
        len(targets_with_zero) / max(len(targets_all), 1) if targets_all else 0
    )
    # JS missing penalty UNIQUEMENT si les chiffres sont à 0 (donc le JS est requis)
    js_missing_penalty = 1.0 if (targets_with_zero and not has_counter_js) else 0.0
    # Reveal pattern penalty : si on a des reveal pairs SANS JS qui ajoute les classes
    # → la majorité du contenu est invisible (sections complètes en opacity:0)
    reveal_penalty = 1.0 if (reveal_pairs and not has_reveal_js) else 0.0
    opacity_penalty = min(opacity_zero_no_animation / 20.0, 1.0)

    # Reveal pattern is the most damaging bug (cache des sections entières)
    broken_score = round(
        0.4 * counters_broken
        + 0.2 * js_missing_penalty
        + 0.5 * reveal_penalty       # reveal absent = quasi tout invisible
        + 0.1 * opacity_penalty,
        3
    )
    broken_score = min(broken_score, 1.0)

    return {
        "counters_with_zero_default": len(targets_with_zero),
        "counters_total": len(targets_all),
        "scripts_count": len(scripts),
        "has_counter_js": has_counter_js,
        "opacity_zero_count": opacity_zero_count,
        "has_keyframes": has_keyframes,
        "has_reveal_transition": has_reveal_transition,
        "opacity_zero_no_animation": opacity_zero_no_animation,
        "reveal_pattern_pairs": [list(p) for p in reveal_pairs],
        "has_reveal_js": has_reveal_js,
        "broken_score": broken_score,
        "broken_severity": (
            "critical" if broken_score >= 0.5 else
            "warning" if broken_score >= 0.2 else "ok"
        ),
    }


def _format_target_for_display(target_str: str) -> str:
    """Format un data-target en string visible.

    1300000 → '1 300 000' (espaces FR)
    111368  → '111 368'
    4.9     → '4.9' (préservé)
    327     → '327'
    """
    target_str = target_str.strip()
    try:
        if "." in target_str:
            return target_str  # Float préservé
        n = int(target_str)
        if n >= 1000:
            # FR thousands separator
            return f"{n:,}".replace(",", " ")
        return str(n)
    except (ValueError, TypeError):
        return target_str


def fix_html_runtime(html: str, inject_js: bool = False,
                     fix_reveal_pattern: bool = True) -> tuple[str, dict]:
    """Patch les bugs de rendering connus dans un HTML.

    1. counters>0 default : <X data-target="N">0</X> → >{format(N)}<
    2. reveal pattern (V26.Z iter3) : si .X{opacity:0} + .X.revealed{opacity:1}
       sans JS pour ajouter `.revealed` → patch CSS direct (force opacity 1
       pour les sélecteurs .X) pour rendu safe par défaut + injection JS
       optionnelle qui ré-anime correctement
    3. inject_js : injecte le RUNTIME_JS_FALLBACK (counters + reveals) avant </body>

    Returns: (fixed_html, report)
    """
    report_before = detect_runtime_bugs(html)

    # Fix 1 : counters with 0 default → put final value visible
    pattern = re.compile(
        r'<(\w+)(\s[^>]*data-target="[^"]+"[^>]*)>\s*0\s*<',
        re.IGNORECASE
    )

    def _patcher(m: re.Match) -> str:
        tag = m.group(1)
        attrs = m.group(2)
        target_match = re.search(r'data-target="([^"]+)"', attrs)
        if not target_match:
            return m.group(0)
        formatted = _format_target_for_display(target_match.group(1))
        return f"<{tag}{attrs}>{formatted}<"

    fixed_html = pattern.sub(_patcher, html)

    # Fix 2 (V26.Z iter3) : reveal pattern .X{opacity:0} + .X.revealed{opacity:1}
    # Patch CSS direct : si pas de JS qui ajoute .revealed, on force opacity:1
    # initiale sur les sélecteurs concernés (animations sans dépendance JS)
    reveal_fixed = []
    if fix_reveal_pattern and report_before["reveal_pattern_pairs"]:
        for base, modifier in report_before["reveal_pattern_pairs"]:
            # Pattern à corriger : .X { ... opacity: 0 ... transform: translate(...) ... }
            # On remplace opacity: 0 et transforms hidden par opacity: 1 + translate(0,0)
            css_pattern = re.compile(
                r'(\.' + re.escape(base) + r'\s*\{[^}]*?)opacity:\s*0\b',
                re.IGNORECASE
            )

            def _css_fix_op(match):
                return match.group(1) + 'opacity: 1'

            fixed_html_new = css_pattern.sub(_css_fix_op, fixed_html, count=1)
            if fixed_html_new != fixed_html:
                reveal_fixed.append((base, modifier))
                fixed_html = fixed_html_new
            # Aussi : transforms qui hide le contenu (translateY 20px+, scale 0.x)
            transform_pattern = re.compile(
                r'(\.' + re.escape(base) + r'\s*\{[^}]*?)transform:\s*translate(?:Y|X|3d)?\([^)]+\)',
                re.IGNORECASE
            )

            def _css_fix_transform(match):
                return match.group(1) + 'transform: none'

            fixed_html = transform_pattern.sub(_css_fix_transform, fixed_html, count=1)

    # Fix 3 : inject runtime JS (counters + reveals) si demandé
    needs_js = (
        not report_before["has_counter_js"]
        and (report_before["counters_total"] > 0 or report_before["reveal_pattern_pairs"])
    )
    injected_js = False
    if inject_js and needs_js:
        if "</body>" in fixed_html:
            fixed_html = fixed_html.replace(
                "</body>", RUNTIME_JS_FALLBACK.strip() + "\n</body>", 1
            )
        else:
            fixed_html += "\n" + RUNTIME_JS_FALLBACK.strip()
        injected_js = True

    report_after = detect_runtime_bugs(fixed_html)
    report = {
        "before": report_before,
        "after": report_after,
        "fixed_counters": report_before["counters_with_zero_default"]
                         - report_after["counters_with_zero_default"],
        "fixed_reveal_pairs": reveal_fixed,
        "injected_js": injected_js,
    }
    return fixed_html, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="HTML file path")
    ap.add_argument("--output", help="Output path (default: <input>.fixed.html)")
    ap.add_argument("--in-place", action="store_true",
                    help="Overwrite input (saves original to <input>.bak)")
    ap.add_argument("--inject-counter-js", action="store_true",
                    help="Si pas de counter JS détecté, injecte un fallback minimal")
    ap.add_argument("--detect-only", action="store_true",
                    help="Audit sans patcher")
    args = ap.parse_args()

    in_fp = pathlib.Path(args.input)
    if not in_fp.exists():
        sys.exit(f"❌ {in_fp} not found")
    html = in_fp.read_text()

    if args.detect_only:
        report = detect_runtime_bugs(html)
        print(f"\n══ Runtime audit — {in_fp.name} ══")
        for k, v in report.items():
            print(f"  {k}: {v}")
        return

    fixed_html, report = fix_html_runtime(html, inject_js=args.inject_counter_js)

    if args.in_place:
        bak_fp = in_fp.with_suffix(in_fp.suffix + ".bak")
        shutil.copy(in_fp, bak_fp)
        in_fp.write_text(fixed_html)
        out_path = in_fp
        print(f"✓ Original backed up : {bak_fp.name}")
    else:
        out_fp = pathlib.Path(args.output or (in_fp.with_suffix(".fixed.html")))
        out_fp.write_text(fixed_html)
        out_path = out_fp

    print(f"\n══ Fix HTML Runtime — {in_fp.name} ══")
    b, a = report["before"], report["after"]
    print(f"  Before : counters_zero={b['counters_with_zero_default']}/{b['counters_total']} "
          f"scripts={b['scripts_count']} broken_score={b['broken_score']} ({b['broken_severity']})")
    print(f"  After  : counters_zero={a['counters_with_zero_default']}/{a['counters_total']} "
          f"scripts={a['scripts_count']} broken_score={a['broken_score']} ({a['broken_severity']})")
    print(f"  Fixed counters : {report['fixed_counters']}")
    print(f"  Injected JS    : {report['injected_js']}")
    print(f"\n  Saved : {out_path}")
    print(f"  Open  : open {out_path}")


if __name__ == "__main__":
    main()
