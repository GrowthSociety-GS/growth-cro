"""Perception layer — DOM heuristics + adaptive DBSCAN clustering + role intent."""
from growthcro.perception.heuristics import (
    NOISE_KEYWORDS,
    NAV_KEYWORDS,
    CTA_PRIMARY_KEYWORDS,
    FOOTER_KEYWORDS,
    ROLE_PRIORITY,
    VIEWPORT_W,
    FOLD_Y,
    bbox_center,
    bbox_area,
    parse_font_size,
    compute_noise_score,
)
from growthcro.perception.vision import (
    compute_adaptive_eps,
    dbscan_1d_vertical,
    refine_clusters_by_y_gap,
)
from growthcro.perception.intent import assign_cluster_role
from growthcro.perception.persist import process_page

__all__ = [
    "NOISE_KEYWORDS", "NAV_KEYWORDS", "CTA_PRIMARY_KEYWORDS", "FOOTER_KEYWORDS",
    "ROLE_PRIORITY", "VIEWPORT_W", "FOLD_Y",
    "bbox_center", "bbox_area", "parse_font_size", "compute_noise_score",
    "compute_adaptive_eps", "dbscan_1d_vertical", "refine_clusters_by_y_gap",
    "assign_cluster_role", "process_page",
]
