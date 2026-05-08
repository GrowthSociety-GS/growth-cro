# Memory System Template — Insight Accuracy Tracking

> **Purpose**: This template tracks AI insights from generation through validation, measuring estimation accuracy and refining confidence scoring over time.

> **Status**: Empty template. Populate as insights are generated and validated.

---

## Insight Memory Log

### Entry Format

Each validated insight generates one memory entry following this structure:

```markdown
## Insight #{ID} — {Title}

**Generation Date**: {YYYY-MM-DD}
**Insight ID**: {UUID from ai_learnings table}
**Vertical**: {SaaS | ecommerce | InsurTech | B2B | Other}
**Recommendation Type**: {CTA | Hero | Form | Copy | Layout | Mobile | Pricing | Other}

### Original Estimate
- **Estimated Lift**: {X}%
- **Sample Size (Audits)**: {N}
- **Confidence Score**: {0–100}%
- **Data Backing**: {Brief summary of pattern}

### Implementation Tracking
- **Implementation Date**: {YYYY-MM-DD}
- **Pages Deployed with Insight**: {N}
- **Deployed Page IDs**: {page_id_1, page_id_2, ...}
- **Team Actions**: {Brief description of how team applied insight}

### Actual Performance (Observed via Catchr)
- **Observation Period**: {start_date} to {end_date}
- **Actual Observed Lift**: {X}% (or "Pending if <30 days since deployment")
- **Sample Size (Pages)**: {N}
- **CVR Baseline**: {X}%
- **CVR Post-Change**: {X}%

### Accuracy Calibration
- **Estimation Error**: {actual − estimated}% (e.g., −2.1%, +5.3%)
- **Error Classification**: {validated | rejected | inconclusive}
  - **Validated**: |error| ≤ 5%
  - **Rejected**: |error| > 15%
  - **Inconclusive**: 5% < |error| ≤ 15% OR sample size <2
- **Confidence Adjustment**: {±X points} (adjusted score after validation)

### Team Feedback
- **Feedback**: {Qualitative notes from team; why did estimate differ?}
- **Factors**: {Complexity differences, client-specific constraints, external effects}

### Outcome & Next Steps
- **Status**: {validated | rejected | inconclusive}
- **Action**: {Archive | Promote | Refine estimate | Investigate further}
- **Recommendation**: {Next steps for team or algorithm}

---
```

### Example Entry (Filled)

```markdown
## Insight #47 — CTAs with Strikethrough Pricing in InsurTech

**Generation Date**: 2026-02-15
**Insight ID**: 550e8400-e29b-41d4-a716-446655440000
**Vertical**: InsurTech
**Recommendation Type**: CTA

### Original Estimate
- **Estimated Lift**: 31%
- **Sample Size (Audits)**: 4
- **Confidence Score**: 78%
- **Data Backing**: 4 InsurTech audits (past 30d) identified pricing CTA issue; strikethrough format recommended on 2 pages

### Implementation Tracking
- **Implementation Date**: 2026-02-18
- **Pages Deployed with Insight**: 2
- **Deployed Page IDs**: page_8834, page_8912
- **Team Actions**: Applied strikethrough pricing CTA to quote request buttons on both pages

### Actual Performance
- **Observation Period**: 2026-02-18 to 2026-04-05
- **Actual Observed Lift**: 28%
- **Sample Size (Pages)**: 2
- **CVR Baseline**: 3.2%
- **CVR Post-Change**: 4.1%

### Accuracy Calibration
- **Estimation Error**: −3% (estimated 31%, actual 28%)
- **Error Classification**: validated
- **Confidence Adjustment**: +8 points (78% → 86%)

### Team Feedback
- **Feedback**: "Estimate was very close. The −3% variance likely due to external traffic quality variation and slight copy tweaks by client."
- **Factors**: Client added additional copy context beyond strikethrough recommendation; slightly different traffic segment during deployment

### Outcome & Next Steps
- **Status**: validated
- **Action**: Promote insight to InsurTech playbook
- **Recommendation**: Use 28–31% as baseline range for strikethrough pricing CTAs in InsurTech vertical going forward

---
```

---

## Memory Dashboard Aggregates

### Accuracy Metrics (Monthly Review)

| Metric | Value | Status |
|--------|-------|--------|
| **Insights Generated (month)** | {N} | — |
| **Insights Validated** | {N} ({%}%) | — |
| **Insights Rejected** | {N} ({%}%) | — |
| **Insights Inconclusive** | {N} ({%}%) | — |
| **Avg Confidence (at generation)** | {X}% | — |
| **Avg Confidence (post-validation)** | {X}% | ↑/→/↓ |
| **Avg Estimation Error** | {X}% | — |
| **Error Std Dev** | {X}% | — |
| **Error Trending** | {← reducing / → stable / → widening} | Status |

### Accuracy by Vertical

| Vertical | Validated % | Avg Lift Error | Sample Insights |
|----------|-------------|----------------|-----------------|
| **SaaS** | {%} | {X}% | {N} |
| **ecommerce** | {%} | {X}% | {N} |
| **InsurTech** | {%} | {X}% | {N} |
| **B2B** | {%} | {X}% | {N} |

### Accuracy by Recommendation Type

| Type | Validated % | Avg Lift Error | Sample Insights |
|------|-------------|----------------|-----------------|
| **CTA** | {%} | {X}% | {N} |
| **Hero** | {%} | {X}% | {N} |
| **Form** | {%} | {X}% | {N} |
| **Copy** | {%} | {X}% | {N} |
| **Layout** | {%} | {X}% | {N} |
| **Mobile** | {%} | {X}% | {N} |
| **Pricing** | {%} | {X}% | {N} |

---

## Calibration Rules

### Automatic Adjustments

**When an insight is validated**:
- Base confidence increases by: `MIN(8, sample_size)` points
- Baseline lift estimate for that rec type adjusts by ±X% (weighted average of actual errors)

**When an insight is rejected**:
- Base confidence decreases by: `MIN(12, sample_size × 1.5)` points
- Baseline lift estimate reduced conservatively by −20% of observed error

**When inconclusive**:
- No automatic adjustment; mark for team review
- If >3 inconclusive outcomes for same rec type, escalate to data analyst

### Manual Review Cadence

- **Weekly**: Review all completed insights (≥30 days post-deployment)
- **Monthly**: Aggregate accuracy metrics, adjust baseline estimates
- **Quarterly**: Strategic review with CRO team; update playbook with high-confidence patterns

---

## Insight Archive Rules

### Archive Conditions

Insight is marked for archival if:
1. **Low validation rate**: <40% of deployed instances show estimated lift within ±10%
2. **Rejection rate high**: >25% of validation attempts result in rejection
3. **Low confidence**: Confidence score <50% after 2+ validation cycles
4. **Superseded**: Newer insight covers same pattern with higher accuracy

### Archival Process

```
1. Flag insight in admin panel: "Low Accuracy — Recommend Archive"
2. Wait for team confirmation (do not auto-archive)
3. Move to `ai_learnings.in_trash = true`
4. Keep in memory log for historical reference
5. Do not display in dashboard until re-validated
```

---

## Playbook Integration

### High-Confidence Insights → Playbook

When an insight reaches:
- **Confidence**: ≥85%
- **Validated instances**: ≥3
- **Avg estimation error**: <5%

**Action**: Promote to production playbook for that vertical/recommendation type

**Example Playbook Entry**:
```
### InsurTech CTA Pattern: Strikethrough Pricing

**Estimated Lift**: 28–31% (high confidence, 6 pages validated)
**Best Practices**:
  - Use strikethrough on original price
  - Highlight discounted price in contrasting color
  - Test on quote request primary CTA
**Example Pages**: page_8834, page_8912 (top performers)
**Launch Probability**: 85% (historical validation)
```

---

## Data Storage: `insight_memory` Table

```sql
CREATE TABLE insight_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Insight Reference
  insight_id UUID NOT NULL UNIQUE REFERENCES ai_learnings(id),
  vertical VARCHAR(50) NOT NULL,
  recommendation_type VARCHAR(50) NOT NULL,

  -- Original Estimate
  original_estimated_lift_pct NUMERIC(5,2) NOT NULL,
  original_confidence_pct NUMERIC(5,1) NOT NULL,
  sample_size_audits INT NOT NULL,

  -- Implementation Tracking
  implemented_audit_count INT DEFAULT 0,
  pages_deployed_with_insight INT DEFAULT 0,
  pages_deployed_list UUID[] DEFAULT ARRAY[]::UUID[],

  -- Actual Performance
  actual_observed_lift_pct NUMERIC(5,2) NULL,
  actual_cvr_baseline NUMERIC(5,2) NULL,
  actual_cvr_post_change NUMERIC(5,2) NULL,

  -- Calibration
  estimation_error_pct NUMERIC(5,2) NULL,
  confidence_adjustment_pct NUMERIC(5,1) DEFAULT 0,
  adjusted_confidence_pct NUMERIC(5,1) NULL,

  -- Classification
  accuracy_status VARCHAR(20) DEFAULT 'pending',
    -- enum: 'pending', 'validated', 'rejected', 'inconclusive'

  -- Metadata
  team_feedback TEXT,
  observation_period_start DATE,
  observation_period_end DATE,
  validation_date DATE,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_insight_memory_insight_id ON insight_memory(insight_id);
CREATE INDEX idx_insight_memory_vertical_type ON insight_memory(vertical, recommendation_type);
CREATE INDEX idx_insight_memory_status ON insight_memory(accuracy_status);
```

---

## Monthly Review Template

**Month**: {YYYY-MM}

### Summary

- Insights generated: {N}
- Insights validated: {N} ({%}%)
- Insights rejected: {N} ({%}%)
- Average confidence pre-validation: {X}%
- Average confidence post-validation: {X}%

### Trends

- Estimation accuracy improving? {Yes/No/Stable}
- Vertical with highest accuracy: {Vertical} ({%}%)
- Recommendation type with highest accuracy: {Type} ({%}%)
- Recommendation type needing recalibration: {Type}

### Recalibrations Made

1. {Rec Type} baseline lift: {Old}% → {New}% (based on {N} validations)
2. {Vertical} multiplier: {Old} → {New}
3. {Other adjustments}

### High-Confidence Insights (Promoted to Playbook)

- {Insight title} (confidence: {X}%, {N} validations)
- {Insight title} (confidence: {X}%, {N} validations)

### Low-Accuracy Insights (Marked for Review)

- {Insight title} (confidence: {X}%, validation rate: {%}%)
- {Insight title} (confidence: {X}%, validation rate: {%}%)

### Next Month Focus

- Increase sample sizes for {recommendation type}
- Investigate calibration drift in {vertical}
- Deep-dive: {Specific challenge or opportunity}

---

## Quick Reference: Validation Checklist

- [ ] Insight deployed to ≥1 page
- [ ] ≥30 days elapsed since deployment
- [ ] Catchr performance data available for all deployed pages
- [ ] CVR baseline calculated (pre-change period)
- [ ] Actual CVR post-change calculated
- [ ] Actual lift = (post_cvr − baseline_cvr) / baseline_cvr × 100
- [ ] Estimation error = actual − estimated
- [ ] Classify: validated (|error| ≤5%) | rejected (>15%) | inconclusive
- [ ] Update `confidence_adjustment_pct` and `adjusted_confidence_pct`
- [ ] Add team feedback notes
- [ ] Update dashboard accuracy metrics
- [ ] If validated + confidence ≥85%: promote to playbook

---

**Last Updated**: April 2026
**Template Owner**: Growth Society — CRO Analytics Team
