# KPI Definitions & Calculation Reference

## Overview

This document provides the canonical KPI calculation formulas, validation rules, and edge case handling for the Dashboard & Analytics Engine. All dashboard queries must reference these definitions.

---

## KPI #1: Projets Actifs (Active Projects)

### Primary Definition

Count of unique, non-archived clients as of the reporting period end.

### SQL Query (Postgres)

```sql
-- Standard active projects count for given period
SELECT COUNT(DISTINCT client_id) AS active_projects_count
FROM clients
WHERE archived = false
  AND created_at <= {period_end}
  AND (archived_at IS NULL OR archived_at > {period_start})
```

### Calculation Details

| Field | Logic |
|-------|-------|
| **Current Value** | Query result (integer) |
| **Previous Period** | Same query applied to previous period window |
| **Trend** | `IF current > previous THEN '↑' (green) ELSE IF current < previous THEN '↓' (red) ELSE '→' (grey)` |
| **Delta** | `current - previous` |
| **Delta %** | `ROUND((delta / NULLIF(previous, 0)) * 100, 1)` |

### Edge Cases

1. **Client Created During Previous Period, Archived During Current**:
   - Counts in previous, not in current
   - Delta = −1 (shows as ↓)

2. **Re-activation (archived → active)**:
   - Set `archived = false`, `archived_at = NULL`
   - Client counts in current period forward

3. **Null `archived_at`**:
   - Client is active (not archived)
   - Condition `archived_at IS NULL OR archived_at > period_start` handles this

### Context & Interpretation

- **Green (↑)**: Growth in active client base; team scaling, retention improving
- **Red (↓)**: Client loss; churn risk, account attrition
- **Neutral (→)**: Stable base; focus on quality over growth
- **Benchmark**: Typical SaaS agency maintains 15–40 active clients

---

## KPI #2: Pages Générées (Generated Pages)

### Primary Definition

Count of distinct pages created (first published) within the measurement period. Excludes draft/unpublished pages.

### SQL Query (Postgres)

```sql
-- Count of distinct pages published in period
SELECT COUNT(DISTINCT page_id) AS pages_generated_count
FROM pages
WHERE created_at >= {period_start}
  AND created_at <= {period_end}
  AND status != 'draft'
```

### Calculation Details

| Field | Logic |
|-------|-------|
| **Current Value** | Query result (integer) |
| **Previous Period** | Same query applied to previous period window |
| **Trend** | `IF current > previous THEN '↑' (green) ELSE IF current < previous THEN '↓' (red) ELSE '→'` |
| **Delta** | `current - previous` |
| **Delta %** | `ROUND((delta / NULLIF(previous, 0)) * 100, 1)` |

### Edge Cases

1. **Draft Pages**:
   - Excluded (status = 'draft')
   - Not counted until published (status = 'building' or 'live')

2. **Multiple Page Versions**:
   - Versions (A/B tests) are separate `page_id` entries
   - Each version counted independently
   - Count reflects page volume, not client count

3. **Page Deleted**:
   - If soft-deleted (status = 'archived'), excluded from count
   - If hard-deleted, removed from query entirely

### Context & Interpretation

- **Green (↑)**: Increased output velocity; team capacity high, client demand strong
- **Red (↓)**: Reduced output; bottleneck in builds, lower client engagement
- **Benchmark**: 10–20 pages/month typical for 20-person CRO team

---

## KPI #3: Délai Moyen (Average Time-to-Deploy)

### Primary Definition

Average calendar days from brief creation to page live deployment, measured across completed briefs.

### SQL Query (Postgres)

```sql
-- Average days from brief creation to page deployment
SELECT
  AVG(EXTRACT(DAY FROM p.deployed_at - b.created_at))::NUMERIC(5,1) AS avg_days_to_deploy
FROM briefs b
JOIN pages p ON b.id = p.parent_brief_id
WHERE b.created_at >= {period_start}
  AND b.created_at <= {period_end}
  AND p.deployed_at IS NOT NULL
  AND p.status = 'live'
```

### Calculation Details

| Field | Logic |
|-------|-------|
| **Current Value** | Average days (1 decimal: e.g., 14.3 days) |
| **Previous Period** | Same query applied to previous period window |
| **Trend** | `IF current < previous THEN '↓' (green = faster) ELSE IF current > previous THEN '↑' (red = slower) ELSE '→'` |
| **Delta** | `current - previous` (negative delta = improvement) |
| **Delta %** | `ROUND((delta / NULLIF(previous, 0)) * 100, 1)` |

### Edge Cases

1. **Multiple Pages per Brief**:
   - Brief → multiple pages (A/B tests, variations)
   - Use earliest `deployed_at` for each brief
   - Modify join: `AND p.deployed_at = (SELECT MIN(deployed_at) FROM pages WHERE parent_brief_id = b.id AND status = 'live')`

2. **Brief with No Deployed Pages**:
   - Excluded (requires `p.deployed_at IS NOT NULL`)
   - Indicates brief abandoned or still in progress

3. **Audit-to-Deploy vs Brief-to-Deploy**:
   - This KPI measures brief → deploy only
   - Does not include pre-brief discovery/scoping
   - Interpretation: internal team efficiency, not client onboarding time

### Context & Interpretation

- **Green (↓)**: Faster cycle; process efficiency improving, team capable
- **Red (↑)**: Slower cycle; bottleneck (audit, design, dev), increased complexity
- **Benchmark**: SaaS 8–14 days typical, ecommerce 5–10 days (lower complexity)

### Calculation Variations

**By Vertical** (add WHERE clause):
```sql
WHERE b.created_at >= {period_start}
  AND vertical = 'SaaS'
  ...
```

**By Team Member** (add WHERE clause):
```sql
WHERE b.created_at >= {period_start}
  AND b.assigned_to = {user_id}
  ...
```

---

## KPI #4: Score Audit Ø (Average Audit Score)

### Primary Definition

Mean audit score across all completed audits in the period, normalized to 0–108 scale.

### SQL Query (Postgres)

```sql
-- Average audit score for completed audits
SELECT AVG(a.final_score)::NUMERIC(5,1) AS avg_audit_score
FROM audits a
WHERE a.completed_at >= {period_start}
  AND a.completed_at <= {period_end}
  AND a.final_score IS NOT NULL
```

### Calculation Details

| Field | Logic |
|-------|-------|
| **Current Value** | Average score (1 decimal: e.g., 72.4 /108) |
| **Previous Period** | Same query applied to previous period window |
| **Trend** | `IF current > previous THEN '↑' (green = higher maturity) ELSE IF current < previous THEN '↓' (red) ELSE '→'` |
| **Delta** | `current - previous` (positive delta = improvement) |
| **Delta %** | `ROUND((delta / NULLIF(previous, 0)) * 100, 1)` |

### Audit Scoring Framework

**Scale**: 0–108 (sum of all question weights)

**Score Bands**:
| Band | Range | Interpretation |
|------|-------|-----------------|
| **Critical** | 0–20 | No CRO fundamentals; immediate intervention needed |
| **Poor** | 21–40 | Basic issues; foundational fixes required |
| **Fair** | 41–60 | Established processes; optimization opportunities |
| **Good** | 61–80 | Strong maturity; incremental improvements only |
| **Excellent** | 81–108 | Advanced CRO practice; edge-case optimizations |

### Calculation Methods for `final_score`

**Cumulative Scoring**:
- Each audit question has a weight (1–5 points)
- Responses scored 0–weight based on maturity level
- `final_score = SUM(response_score)` across all questions

**Example Audit Structure**:
```
Section 1: Analytics & Measurement (Max: 25 points)
  Q1: GA4 implementation? (0–5)
  Q2: Event tracking complete? (0–5)
  Q3: Conversion funnel defined? (0–5)
  Q4: Attribution model? (0–5)
  Q5: Experiment framework? (0–5)

Section 2: Audience & Data (Max: 20 points)
  ... [similar structure]

Section 3–6: ...
Total: 108 points max
```

### Edge Cases

1. **Incomplete Audits**:
   - If `final_score IS NULL`, exclude from aggregation
   - Only count completed audits (status = 'completed')

2. **Custom Audit Templates**:
   - Different clients may have different audit question sets
   - Normalize to 0–108 scale: `normalized_score = (actual_score / max_score_for_template) * 108`

3. **Audit Retakes**:
   - Same client, multiple audits
   - Count each audit independently
   - No deduplication; shows trajectory over time

### Context & Interpretation

- **Green (↑)**: Client CRO maturity improving; recommended changes being adopted
- **Red (↓)**: Declining maturity; technical debt accumulating, process regression
- **Neutral (→)**: Stable baseline; consistent capability level

### Advanced Metrics

**Score Variance** (shows consistency):
```sql
SELECT
  AVG(a.final_score)::NUMERIC(5,1) AS avg_score,
  STDDEV(a.final_score)::NUMERIC(5,1) AS score_stddev
FROM audits a
WHERE a.completed_at >= {period_start}
  AND a.completed_at <= {period_end}
  AND a.final_score IS NOT NULL
```

- Low variance (STDDEV < 10): Team consistent in audit assessments
- High variance (STDDEV > 20): Wide client maturity spread or auditor variability

---

## KPI #5: Lift CRO Estimé (Estimated CRO Lift)

### Primary Definition

Average estimated CVR lift percentage across all non-rejected recommendations created in the period.

### SQL Query (Postgres)

```sql
-- Average estimated lift across recommendations
SELECT AVG(r.estimated_lift_pct)::NUMERIC(5,1) AS avg_estimated_lift
FROM recommendations r
WHERE r.created_at >= {period_start}
  AND r.created_at <= {period_end}
  AND r.estimated_lift_pct IS NOT NULL
  AND r.status != 'rejected'
```

### Calculation Details

| Field | Logic |
|-------|-------|
| **Current Value** | Average lift % (1 decimal: e.g., 12.4%) |
| **Previous Period** | Same query applied to previous period window |
| **Trend** | `IF current > previous THEN '↑' (green = higher impact) ELSE IF current < previous THEN '↓' (red) ELSE '→'` |
| **Delta** | `current - previous` (percentage points, not %) |
| **Delta %** | `ROUND((delta / NULLIF(previous, 0)) * 100, 1)` |

### Lift Estimation Framework

**Data Sources** (in priority order):
1. **Historical Benchmarks**: Company CRO playbook performance data
2. **Audit Findings**: Issue severity + recommended fix impact
3. **Recommendation Type**: Pre-defined lift expectations by change type
4. **Vertical Context**: Sector-specific lift patterns (e.g., InsurTech CTAs vs SaaS forms)

**Recommendation Type Baselines**:

| Rec Type | Typical Lift Range | Confidence |
|----------|-------------------|------------|
| **CTA Redesign** | 5–15% | Medium |
| **Form Reduction** | 3–12% | High (tested category) |
| **Hero Copy Rewrite** | 7–18% | Medium |
| **Social Proof Addition** | 4–10% | Medium |
| **Pricing Clarity** | 8–20% | Medium |
| **Layout Split (60/40)** | 12–25% | Medium |
| **Mobile Optimization** | 5–15% | High |
| **Page Speed** | 2–8% | High (correlation proven) |

**Estimation Formula**:
```
estimated_lift = base_lift[recommendation_type]
                 × vertical_multiplier[vertical]
                 × audit_severity_factor[severity]
                 × confidence_adjustment
```

**Example Calculation**:
```
Recommendation: CTA color change (blue → high-contrast orange)
Base Lift (CTA Redesign): 10%
Vertical: InsurTech, multiplier: 1.3
Audit Severity: High (critical CTA issue), factor: 1.2
Confidence: 0.85
Estimated Lift = 10% × 1.3 × 1.2 × 0.85 = 13.3%
```

### Edge Cases

1. **Rejected Recommendations**:
   - Excluded from calculation (status = 'rejected')
   - Client may reject recommendation as not feasible or out of scope

2. **Pending Recommendations**:
   - Included (status = 'pending' or 'approved')
   - Use latest estimated_lift_pct value

3. **Zero or Null Estimates**:
   - Rare; indicates recommendation without clear lift metric
   - Exclude from calculation (IS NOT NULL filter)

4. **Compound Recommendations**:
   - Multiple changes bundled (e.g., "CTA + form + copy")
   - Estimate lift for bundle total, not sum of individual components
   - Avoid double-counting

### Context & Interpretation

- **Green (↑)**: Recommendations increasingly high-impact; audit findings severe, solutions potent
- **Red (↓)**: Lower-impact recommendations; audits finding minor issues or lower-confidence fixes
- **Benchmark**: 8–15% average typical for active CRO programs
  - <8%: Low-hanging fruit exhausted or client maturity low
  - >15%: High-impact audit findings or initial engagement phase

### Validation: Estimated vs Actual

**Post-Deployment Comparison**:
- Deploy recommendation → measure actual CVR lift via Catchr
- Compare `estimated_lift_pct` vs actual observed lift
- Track calibration in `insight_memory` table (see main SKILL.md)

**Recalibration Cadence**:
- Monthly review of top 20% recommendations
- Adjust baseline multipliers if actual avg differs from estimated by >10%
- Example: If "Form Reduction" is hitting +15% actual but estimated 8%, increase baseline to 11%

---

## Cross-KPI Relationships

### KPI Correlation Matrix

| KPI | Influences | Influenced By |
|-----|------------|---------------|
| **Projets Actifs** | Revenue, team capacity planning | Churn, new sales |
| **Pages Générées** | Team utilization, delivery SLA | Process speed, client demand |
| **Délai Moyen** | Client satisfaction, SLA compliance | Complexity, team size, tools |
| **Score Audit Ø** | Lift quality, recommendation relevance | Client maturity, audit depth |
| **Lift CRO Estimé** | Impact potential, campaign prioritization | Audit quality, team expertise |

### Sample KPI Scenario

**Observation**: ↓ Pages Générées (−20% MoM), but ↑ Lift CRO Estimé (+8%)

**Interpretation**:
- Team velocity down (fewer pages shipped)
- Quality of recommendations up (higher estimated impact)
- Possible cause: Shifted to deeper audits, fewer but higher-quality pages
- Action: Monitor Délai Moyen; if increasing, resource constraint; if stable, strategic rebalance

---

## Period-Specific Considerations

### 7-Day Period

- Suitable for: Real-time team monitoring, sprint performance
- Not suitable for: Trend analysis (too noisy), insight generation (low sample)

### 30-Day Period

- Default dashboard period
- Sufficient sample size for all KPIs
- Smooth out weekly variance
- Aligned with typical monthly business reviews

### 90-Day Period

- Suitable for: Strategic planning, seasonal trends
- Longer-term pattern identification
- Sufficient for confidence in Lift estimation calibration

### Custom Period

- User-defined start/end dates
- Previous period = same duration, ending 1 day before custom start
- Example: Custom "Feb 1 — Mar 15" → previous = "Jan 1 — Jan 31" (41 days vs 43 days)

---

## Data Quality & Validation

### Pre-Aggregation Checks

For all KPI queries:

```sql
-- Validate completeness
SELECT
  'Active Projects' AS kpi,
  COUNT(*) AS total_clients,
  COUNT(NULLIF(archived, TRUE)) AS active_count,
  COUNT(NULLIF(archived_at IS NULL, FALSE)) AS missing_archived_at
FROM clients
WHERE created_at <= {period_end};
```

### Expected Data Quality Thresholds

| Check | Threshold | Alert |
|-------|-----------|-------|
| **Null Rate** (any KPI) | <5% | If >5%, flag in admin panel |
| **Audit Score Variance** | 10–50 | If <5 or >60, review audit consistency |
| **Recommendation Count** | ≥3 per audit | If <3, audit may be incomplete |
| **Pages per Recommendation** | <3 avg | If >3, possible bottleneck |

---

## Dashboard Query Performance

### Recommended Indexes

```sql
-- For KPI #1
CREATE INDEX idx_clients_archived_created
  ON clients(archived, created_at);

-- For KPI #2
CREATE INDEX idx_pages_created_status
  ON pages(created_at, status);

-- For KPI #3
CREATE INDEX idx_briefs_created
  ON briefs(created_at);
CREATE INDEX idx_pages_deployed_status
  ON pages(deployed_at, status, parent_brief_id);

-- For KPI #4
CREATE INDEX idx_audits_completed_score
  ON audits(completed_at, final_score);

-- For KPI #5
CREATE INDEX idx_recommendations_created_lift
  ON recommendations(created_at, estimated_lift_pct, status);
```

### Query Optimization Tips

- All period filters use `created_at` or `completed_at` (indexed)
- Avoid full table scans; use partition pruning if >10M rows
- Cache KPI calculations for 15 minutes (update on data change)
- Pre-compute previous period during current period calculation

---

## Changelog

| Date | Change | Impact |
|------|--------|--------|
| 2026-04-05 | Initial KPI definitions v1 | Baseline |
| | | |

---

**Maintained by**: Growth Society — CRO Analytics Team
**Last Reviewed**: April 2026
