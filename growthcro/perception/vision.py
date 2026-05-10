"""Adaptive 1-D vertical DBSCAN + cluster refinement (no Anthropic call yet).

NOTE — Anthropic Sonnet vision integration is deferred. When wired, this module
will import `growthcro.lib.anthropic_client` (created by issue #6). For now, the
module exposes the pure-geometry clustering primitives only.
"""
from __future__ import annotations

import math

from growthcro.perception.heuristics import bbox_center


def compute_adaptive_eps(points: list[tuple[float, float]]) -> float:
    """Auto-calibrated eps: median nearest-neighbor distance × 1.5. Min 120, max 400."""
    if len(points) < 2:
        return 200.0

    neighbor_dists = []
    for i, p in enumerate(points):
        dmin = float("inf")
        for j, q in enumerate(points):
            if i == j:
                continue
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            if d < dmin:
                dmin = d
        if dmin != float("inf"):
            neighbor_dists.append(dmin)

    if not neighbor_dists:
        return 200.0
    neighbor_dists.sort()
    median = neighbor_dists[len(neighbor_dists) // 2]
    eps = median * 1.5
    return max(120.0, min(400.0, eps))


def dbscan_1d_vertical(elements: list[dict], eps: float, min_samples: int = 2) -> list[int]:
    """Simplified DBSCAN on the vertical axis (y_center).

    Cluster mostly by Y: 2 elements are neighbors if they're vertically within `eps`,
    regardless of X (the natural shape of a "block" on a landing page).

    Returns: list of cluster_id (-1 = noise) of the same length as `elements`.
    """
    n = len(elements)
    if n == 0:
        return []

    labels = [-1] * n
    cluster_id = 0

    # Sort by y_center
    indexed = sorted(enumerate(elements), key=lambda t: bbox_center(t[1].get("bbox", {}))[1])

    visited = [False] * n
    for idx_in_sorted, (orig_i, el) in enumerate(indexed):
        if visited[orig_i]:
            continue
        visited[orig_i] = True

        # Find neighbors (within vertical eps)
        y_i = bbox_center(el.get("bbox", {}))[1]
        neighbors = []
        for idx_j, (orig_j, el_j) in enumerate(indexed):
            if orig_j == orig_i:
                continue
            y_j = bbox_center(el_j.get("bbox", {}))[1]
            if abs(y_j - y_i) <= eps:
                neighbors.append(orig_j)

        if len(neighbors) + 1 < min_samples:
            continue  # remains -1 (noise)

        # New cluster
        labels[orig_i] = cluster_id
        stack = list(neighbors)
        while stack:
            q = stack.pop()
            if not visited[q]:
                visited[q] = True
                y_q = bbox_center(elements[q].get("bbox", {}))[1]
                sub_neighbors = []
                for idx_k, (orig_k, el_k) in enumerate(indexed):
                    if orig_k == q:
                        continue
                    y_k = bbox_center(el_k.get("bbox", {}))[1]
                    if abs(y_k - y_q) <= eps:
                        sub_neighbors.append(orig_k)
                if len(sub_neighbors) + 1 >= min_samples:
                    stack.extend([x for x in sub_neighbors if labels[x] == -1])
            if labels[q] == -1:
                labels[q] = cluster_id

        cluster_id += 1

    return labels


def refine_clusters_by_y_gap(elements: list[dict], labels: list[int], gap_threshold: float = 150.0) -> list[int]:
    """Post-pass: split a cluster whose elements are separated by >gap_threshold of vertical void.

    DBSCAN may chain blocks transitively; this gap-split breaks the artificial chains.
    """
    new_labels = labels.copy()
    unique_clusters = set(l for l in labels if l != -1)
    max_label = max(unique_clusters) if unique_clusters else -1

    for cid in unique_clusters:
        indices = [i for i, l in enumerate(labels) if l == cid]
        if len(indices) < 2:
            continue
        indices.sort(key=lambda i: bbox_center(elements[i].get("bbox", {}))[1])

        current_sub = [indices[0]]
        subclusters = [current_sub]
        for i in range(1, len(indices)):
            y_prev = bbox_center(elements[indices[i - 1]].get("bbox", {}))[1]
            y_curr = bbox_center(elements[indices[i]].get("bbox", {}))[1]
            if y_curr - y_prev > gap_threshold:
                current_sub = [indices[i]]
                subclusters.append(current_sub)
            else:
                current_sub.append(indices[i])

        if len(subclusters) > 1:
            for sub in subclusters[1:]:
                max_label += 1
                for idx in sub:
                    new_labels[idx] = max_label

    return new_labels
