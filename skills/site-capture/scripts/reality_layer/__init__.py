"""V26.C Reality Layer — connecteurs data réelle (GA4, Meta Ads, Google Ads, Shopify, Clarity).

Réponse à la critique #1 ChatGPT Hardcore Audit (§2.2) :
"GrowthCRO reste OFFLINE. Sans connexion à GA4, Shopify, Stripe, HubSpot,
Calendly, CRM, Meta Ads, Google Ads, Hotjar, Clarity, VWO/Optimizely,
le moteur ne peut pas savoir si une reco augmente réellement la conversion."

Architecture :

  Each connector = subclass of base.Connector with :
    - fetch(client, page, period) → dict of metrics
    - is_configured() → bool (credentials available?)
    - data_freshness() → ISO timestamp of last sync

  Orchestrator (`reality_layer.py`) :
    - Pour (client, page, period), interroge tous les connecteurs configurés
    - Fusionne en data/captures/<client>/<page>/reality_layer.json
    - Compute fields cross-connector (ad_efficiency = revenue / ad_spend, etc.)

  Mode V26.C : code prêt, credentials/activation par client (pas de
  run mass production tant que les comptes ne sont pas connectés).

Connecteurs implémentés (stubs prêts pour activation par client) :
  - catchr.py    : GA4 wrapper (Catchr — Mathis utilise déjà)
  - meta_ads.py  : Meta Marketing API (ad_spend, ROAS, CTR)
  - google_ads.py: Google Ads API (campaign metrics)
  - shopify.py   : Shopify Admin GraphQL (orders, revenue, funnel)
  - clarity.py   : Microsoft Clarity Data Export (heatmaps, rage clicks)

Usage :
    from reality_layer.orchestrator import collect_for_page

    rl = collect_for_page(client="kaiju", page="home",
                          period_days=30, connectors=["catchr", "shopify"])
    # → data/captures/kaiju/home/reality_layer.json written
"""
from .base import Connector, RealityLayerData

__all__ = ["Connector", "RealityLayerData"]
