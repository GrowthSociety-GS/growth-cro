"""Creative Bar — per-vertical compact creative criteria (Issue CR-09 #64).

Mono-concern (CONFIG axis): static lookup table of textual creative standards
per ``BusinessCategory``. No business logic, no I/O, no LLM call. The Elite
orchestrator splices the appropriate entry into Section 2 of the Opus system
prompt (≤1000 chars per vertical, ≤6K chars total prompt).

Why textual (not HTML golden) criteria?
---------------------------------------
Per Codex correction #4 (review 2026-05-17), injecting a full HTML golden
into the prompt causes **mimicry** (Opus copies the reference instead of
imagining). Compact textual criteria (~500-1000 chars) communicate the
*standard* without anchoring the visual. Opt-in HTML reference is exposed
via the CLI ``--creative-reference`` flag (max 1, anti-patchwork).

All 12 verticals carry an entry — missing entry raises ``KeyError`` at
``get_creative_bar`` (loud failure, intentional — typo in a Literal would
otherwise silently pass).

Each entry follows the same structure (for predictable Opus parsing):
- Ambition level
- Hero mechanism expectations
- Pattern signature for the vertical
- Mobile / responsive expectations
- Motion expectations
- Proof / evidence expectations
- Anti-patterns specific to the vertical
"""
from __future__ import annotations

from growthcro.models.creative_models import BusinessCategory

# ─────────────────────────────────────────────────────────────────────────────
# CREATIVE_BAR_BY_VERTICAL — 12 entries, one per Literal vertical (CR-01)
# Each ≤1000 chars (asserted at module load).
# ─────────────────────────────────────────────────────────────────────────────

CREATIVE_BAR_BY_VERTICAL: dict[BusinessCategory, str] = {
    "saas": (
        "Ambition visuelle elevee. Hero avec mecanisme proprietaire (dashboard "
        "mockup, data viz, founder-led narrative, integration map). Vraie "
        "composition pas empilement de sections. Mobile non sacrifie : "
        "dashboard responsive, pas une image rasterisee. Motion utile (number "
        "ticks, dashboard reveal, code typing) pas decoratif. Preuves sourcees "
        "avec data-evidence-id (numbers, logos, testimonials). Toolbox autorisee "
        ": gradients brand-specific, glass tasteful, depth, conic gradients sur "
        "logos, marquee logos. Anti-patterns vertical : template SaaS fade "
        "'AI-powered platform' + generic mesh gradient + 3 features cards "
        "identiques, stock photo hero 'people in office', checkmark icon list "
        "systematique, fake metrics sans source, gradient mesh AI slop."
    ),
    "ecommerce": (
        "Ambition visuelle elevee. Hero centre produit (pas dashboard) avec "
        "photographie ou rendu produit haute qualite. Storytelling produit > "
        "specs liste. Mobile crucial (60%+ traffic) : carousel touch-friendly, "
        "pinch zoom, sticky add-to-cart. Motion : product reveal, color swap, "
        "AR-hint, scroll-triggered detail close-ups. Preuves : reviews etoilees "
        "(data-evidence-id), UGC photos, badges trust (livraison, retour, "
        "garantie). Toolbox : large hero produit, palette brand pure, "
        "typography editorial pour storytelling, bento grid pour collections. "
        "Anti-patterns : stock photo lifestyle generique, urgency timer fake, "
        "'best seller' sans data, exit-intent pop-up agressif, 5 CTAs."
    ),
    "luxury": (
        "Elegance minimaliste. Large negative space (40%+ de la page vide). "
        "Typography serif premium (Didot, Bodoni, custom) ou sans-serif "
        "editorial ultra-propre. Palette restreinte (2-3 couleurs max), B/W "
        "ou monochrome autorise. Pas de gradient sature ni neon. Mobile "
        "impeccable obligatoire. Motion subtile (fade slow, parallax discret, "
        "image reveal lente). Hero focus produit ou marque (pas dashboard ni "
        "app screenshots). Preuves discretes : badges certifications, presse "
        "prestigieuse (data-evidence-id), heritage. Toolbox : full-bleed "
        "photography editorial, custom illustration, depth via shadow subtle. "
        "Anti-patterns : pop-up urgency, neon colors, glitch effect, comic "
        "sans, emoji partout, '99% off' promo, gradient mesh AI slop."
    ),
    "marketplace": (
        "Ambition visuelle elevee. Hero double-cote : montre l'offre ET la "
        "demande (supply + demand simultanement). Trust signals critiques "
        "(reviews bidirectionnelles, transactions count, success stories). "
        "Mobile : recherche prominente, filters facilement accessibles. "
        "Motion : map reveal, transaction animation, real-time activity feed. "
        "Preuves : metrics liquidite (data-evidence-id), categories volumes, "
        "testimonials des deux cotes. Toolbox : grid asymetrique, photo cards "
        "diverses, badges verified, dynamic counters. Anti-patterns : "
        "homogenise les deux audiences en un seul message, hero generic "
        "'connect with anyone', fake activity feed, stock photo people."
    ),
    "app_acquisition": (
        "Ambition visuelle elevee. Hero centre app : device mockup (phone "
        "frame) avec screen content reel + UI animation. CTA principal = app "
        "store badges (App Store + Google Play). Mobile-first OBLIGATOIRE "
        "(audience target est mobile native). Motion : app screen transition, "
        "feature reveal in-device, ratings ticking. Preuves : star ratings "
        "App Store / Play Store (data-evidence-id), download count, awards. "
        "Toolbox : full-bleed device mockup, parallax phone, video autoplay "
        "muted in device, social proof reviews carousel. Anti-patterns : "
        "screenshot statique sans device frame, stock photo 'happy user with "
        "phone', faux app review, web-first design mobile-afterthought."
    ),
    "media_editorial": (
        "Editorial ambitious. Typography hero comme magazine cover (large "
        "scale, custom kerning, mix serif+sans). Photo journalism haute "
        "qualite ou illustration custom. Grid editorial 12-col flexible. "
        "Mobile : reading optimise, generous line-height, large body text. "
        "Motion : scroll-triggered article reveals, image lazy fade, "
        "marquee headlines. Preuves : bylines journalistes, awards (Pulitzer, "
        "Polk), citations medias peers (data-evidence-id). Toolbox : pull "
        "quotes typographiques, drop caps, sidenotes, footnotes interactives, "
        "full-bleed photo essays. Anti-patterns : SaaS template adapte au "
        "media, stock photo generic, CTA agressif type ecommerce, popup "
        "newsletter intrusif premier scroll."
    ),
    "local_service": (
        "Ambition moderee mais soignee. Hero local-anchored : photo equipe "
        "ou shop reel (pas stock), carte/adresse visible, telephone tap-to-"
        "call. Mobile crucial (search local = mobile). Motion : map zoom, "
        "before/after slider, gallery slide. Preuves : Google Reviews score "
        "+ count (data-evidence-id), badges certifications metier, photos "
        "realisations reelles, BBB / Trustpilot. Toolbox : carte interactive, "
        "horaires structures, sticky CTA call/book, testimonials avec "
        "photo+nom complet local. Anti-patterns : stock photo 'happy "
        "customer', fake reviews 5 etoiles toutes pareilles, '24/7' sans "
        "preuve, hero corporate generic, pas d'adresse visible."
    ),
    "health_wellness": (
        "Ambition visuelle moderee, ton apaisant + scientifique. Hero : "
        "produit ou rituel (pas dashboard ni screenshot app). Palette douce "
        "(beige, sage, sand) ou clinique (white + accent). Typography sans-"
        "serif lisible, body text genereux. Mobile crucial. Motion : breath "
        "rhythm, ingredient reveal, ritual sequence. Preuves : clinical "
        "studies citees (data-evidence-id), certifications (organic, FDA, "
        "dermatologically tested), ingredient transparency, customer photos "
        "avant/apres consenties. Toolbox : full-bleed photo lifestyle "
        "authentique, ingredient close-ups, ritual videos muted. Anti-"
        "patterns : claims medical sans source, '100% natural' vague, "
        "fake before/after, urgency 'only 3 left', neon health-tech vibe."
    ),
    "finance": (
        "Ambition visuelle elevee mais sobre. Hero : product UI + data viz "
        "(pas stock photo 'businessman with laptop'). Palette restreinte "
        "(dark blue + accent, ou green + neutral). Typography sans-serif "
        "precise. Mobile crucial (app banking norm). Motion : number ticks, "
        "chart draw, transaction animation. Preuves : regulator badges "
        "(FDIC, FCA, SEC), security certifications (SOC 2, ISO 27001), "
        "AUM ou volume (data-evidence-id), customer reviews verified. "
        "Toolbox : data viz custom, dashboard mockup, secure-by-design visual "
        "cues. Anti-patterns : stock photo handshake, '10x your money' claim, "
        "fake testimonials, emoji partout, neon crypto vibe (sauf si crypto)."
    ),
    "creator_course": (
        "Ambition visuelle elevee, vibe personnelle + premium. Hero : creator "
        "face reelle (photo pro) + value prop clair, pas stock. Storytelling "
        "personnel (founder narrative). Mobile-first (audience mobile-native). "
        "Motion : module preview, testimonial carousel, before/after student "
        "results. Preuves : student transformations (data-evidence-id), "
        "ratings detailled, social proof student count, creator credentials "
        "(media features, prior wins). Toolbox : video hero autoplay muted "
        "(creator talking head), module bento, testimonials authentiques avec "
        "photo+nom+resultat chiffre. Anti-patterns : urgency 'enroll in next "
        "5 min', fake scarcity, screenshot Zoom generic, '$10K in 30 days' "
        "claim sans preuve, stock photo learner."
    ),
    "enterprise": (
        "Ambition visuelle elevee, ton serieux + premium. Hero : value prop "
        "horizontale (pas vague vision statement) + integration map ou "
        "architecture viz. Palette corporate refined (deep colors + accent). "
        "Typography sans-serif precise, body genereux. Mobile important "
        "(decision makers consultent partout). Motion : integration flow, "
        "data flow, dashboard reveal. Preuves : enterprise logos (Fortune "
        "500, data-evidence-id), security badges (SOC 2 Type II, ISO 27001, "
        "HIPAA, GDPR), analyst recognition (Gartner, Forrester), customer "
        "case studies named. Toolbox : architecture diagrams, integration "
        "logos grid, security badges discrets, demo-request CTA prominent. "
        "Anti-patterns : stock photo handshake corporate, 'leader' claim "
        "vague, fake logos grid, urgency timer."
    ),
    "consumer_brand": (
        "Ambition visuelle TRES elevee, vibe brand-led. Hero : brand statement "
        "fort (typography + photo + couleur signature). Storytelling brand "
        "values + product. Photo lifestyle authentique (pas stock). Mobile "
        "crucial (audience scroll mobile). Motion : brand intro animation, "
        "product reveal, mood shift via scroll. Preuves : community count "
        "(data-evidence-id), press features, customer UGC, awards design. "
        "Toolbox : full-bleed photography editorial, custom typography ou "
        "lettering, palette signature pure, bento brand assets. Anti-patterns "
        ": stock photo, generic 'discover our story', urgency timer fake, "
        "popup newsletter intrusif, 5 CTAs, gradient mesh AI slop."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Module-load invariants — fail fast if a vertical entry blows the cap.
# ─────────────────────────────────────────────────────────────────────────────

_PER_VERTICAL_CHAR_CAP: int = 1000

for _vertical, _criteria in CREATIVE_BAR_BY_VERTICAL.items():
    assert len(_criteria) <= _PER_VERTICAL_CHAR_CAP, (
        f"creative_bar entry {_vertical!r} is {len(_criteria)} chars, "
        f"exceeds {_PER_VERTICAL_CHAR_CAP} cap — split or trim."
    )


def get_creative_bar(business_category: BusinessCategory) -> str:
    """Return the compact creative criteria for ``business_category``.

    Raises ``KeyError`` if the vertical has no entry — loud failure,
    intentional. A new vertical added to the Literal must land here in the
    same commit.
    """
    if business_category not in CREATIVE_BAR_BY_VERTICAL:
        raise KeyError(
            f"no creative_bar entry for business_category={business_category!r}; "
            f"available: {sorted(CREATIVE_BAR_BY_VERTICAL.keys())}"
        )
    return CREATIVE_BAR_BY_VERTICAL[business_category]


__all__ = [
    "CREATIVE_BAR_BY_VERTICAL",
    "get_creative_bar",
]
