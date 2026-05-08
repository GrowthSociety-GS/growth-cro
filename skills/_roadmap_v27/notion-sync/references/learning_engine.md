# Learning Engine - Architecture & Implementation
## Continuous Intelligence System pour GrowthCRO

**Document Version:** 1.0.0
**Last Updated:** 2026-04-05
**Status:** Production Specification

---

## TABLE OF CONTENTS

1. [Learning Pipeline Architecture](#learning-pipeline-architecture)
2. [Data Collection Flows](#data-collection-flows)
3. [Pattern Detection Methods](#pattern-detection-methods)
4. [Insight Generation](#insight-generation)
5. [Module Integration Points](#module-integration-points)
6. [Confidence Scoring Deep Dive](#confidence-scoring-deep-dive)
7. [Memory & Calibration](#memory--calibration)
8. [Learning Lifecycle](#learning-lifecycle)
9. [Operational Procedures](#operational-procedures)

---

## LEARNING PIPELINE ARCHITECTURE

### Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  DATA COLLECTION LAYER                        │
├────────────────┬────────────────┬────────────────┬───────────┤
│  Audit Engine  │  Recommender   │  Generator     │  Page Opt  │
│  (findings)    │  (performance) │  (quality)     │  (A/B)     │
└────────────────┴────────────────┴────────────────┴───────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│            DATA AGGREGATION & NORMALIZATION                   │
│  • Convert to standard format                                 │
│  • Extract features (sector, type, impact)                   │
│  • Store with metadata (source, timestamp, confidence)       │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│             PATTERN DETECTION LAYER                           │
│  • Frequency analysis (χ² test)                              │
│  • Correlation detection (Pearson r)                         │
│  • Outlier identification (IQR)                              │
│  • Time series trends (ARIMA)                                │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│          INSIGHT GENERATION & FORMATTING                      │
│  • Convert patterns to human-readable text                   │
│  • Structure with examples + recommendations                 │
│  • Calculate confidence scores                               │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│             STORAGE & DISTRIBUTION                            │
│  • Store in ai_learnings table                               │
│  • Push to Notion (optional)                                 │
│  • Distribute to relevant modules as context                 │
└──────────────────────────────────────────────────────────────┘
```

### Execution Schedule

```
Every 6 hours (automatic):
  0:00 UTC → Full learning run
  6:00 UTC → Full learning run
  12:00 UTC → Full learning run
  18:00 UTC → Full learning run

On-demand:
  User clicks "Synchroniser" → Immediate learning run
  Critical finding detected → Urgent learning flag

Daily:
  23:00 UTC → Confidence recalibration
  01:00 UTC → Memory cleanup (remove expired learnings)
```

---

## DATA COLLECTION FLOWS

### 1. Audit Engine → Learning Engine

**Trigger:** After each audit completes

**Extracted Data:**

```python
def collect_audit_data(audit_id):
    """
    Collect patterns from completed audit.
    Run immediately after audit.generate_report().
    """

    audit = Audit.get(audit_id)

    audit_data = {
        'source': 'audit_engine',
        'audit_id': audit.id,
        'client_id': audit.client.id,
        'sector': audit.client.sector,
        'website_category': audit.client.website_category,
        'completed_at': audit.completed_at,
        'findings': []
    }

    for finding in audit.findings:

        # Normalize finding
        finding_data = {
            'category': finding.category,  # e.g., 'checkout_friction'
            'severity': finding.severity,  # 0-10
            'page_url': finding.page_url,
            'description': finding.description,
            'recommendation': finding.recommendation,
            'affected_elements': finding.affected_elements,
            'impact_estimate': finding.impact_estimate,  # revenue impact %
            'frequency_in_sector': find_frequency_in_sector(
                finding.category,
                audit.client.sector
            ),
            'is_unique': finding.is_unique_to_client
        }

        audit_data['findings'].append(finding_data)

    # Store for learning
    store_learning_data({
        'type': 'audit_pattern',
        'data': audit_data,
        'received_at': datetime.now()
    })

    # Trigger pattern detection if enough data collected
    if should_trigger_pattern_detection('audit'):
        queue_learning_task('detect_audit_patterns')

    return audit_data


def find_frequency_in_sector(finding_category, sector, lookback_days=90):
    """
    How often does this finding appear in this sector?
    Used to determine if it's a sector-wide pattern or anomaly.
    """

    recent_audits = Audit.objects.filter(
        client__sector=sector,
        completed_at__gte=datetime.now() - timedelta(days=lookback_days),
        is_complete=True
    )

    matching_audits = recent_audits.filter(
        findings__category=finding_category
    ).count()

    frequency = matching_audits / recent_audits.count()

    return {
        'occurrence_rate': frequency,
        'sample_size': recent_audits.count(),
        'lookback_days': lookback_days
    }
```

**Storage Schema:**

```sql
CREATE TABLE learning_data_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL,
    client_id UUID NOT NULL,
    sector VARCHAR NOT NULL,
    finding_category VARCHAR NOT NULL,
    severity INT,
    frequency_in_sector FLOAT,
    impact_estimate FLOAT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX audit_id_idx (audit_id),
    INDEX sector_category_idx (sector, finding_category),
    INDEX received_at_idx (received_at)
);
```

### 2. Recommender → Learning Engine

**Trigger:** When Catchr reports CVR improvement

**Extracted Data:**

```python
def collect_recommendation_performance(test_result_id):
    """
    Link recommendation to actual CVR impact via Catchr.
    Run when A/B test concludes with statistical significance.
    """

    test_result = TestResult.get(test_result_id)
    recommendation = test_result.recommendation

    perf_data = {
        'source': 'recommender',
        'recommendation_id': recommendation.id,
        'recommendation_type': recommendation.type,
        'recommendation_category': recommendation.category,
        'client_id': recommendation.client.id,
        'sector': recommendation.client.sector,
        'baseline_cvr': test_result.baseline_cvr,
        'variant_cvr': test_result.variant_cvr,
        'cvr_improvement_percent': (
            (test_result.variant_cvr - test_result.baseline_cvr) /
            test_result.baseline_cvr * 100
        ),
        'revenue_impact_estimate': test_result.estimated_revenue_lift,
        'statistical_confidence': test_result.p_value,
        'sample_size': test_result.sample_size,
        'test_duration_days': (
            test_result.end_date - test_result.start_date
        ).days,
        'implementation_ease': recommendation.implementation_difficulty,
        'is_positive_result': test_result.cvr_improvement_percent > 0
    }

    # Store performance data
    store_learning_data({
        'type': 'recommendation_performance',
        'data': perf_data,
        'received_at': datetime.now()
    })

    # Update recommendation with performance data
    recommendation.cvr_impact = perf_data['cvr_improvement_percent']
    recommendation.performance_validated = True
    recommendation.save()

    # Trigger pattern detection
    queue_learning_task('detect_recommendation_patterns')

    return perf_data


def normalize_recommendation_type(raw_type: str) -> str:
    """
    Normalize recommendation types across audit + recommender modules.
    Ensures consistency in pattern detection.

    Examples:
    - 'optimize_cta_contrast' → 'cta_contrast_improvement'
    - 'reduce_form_fields' → 'form_field_reduction'
    - 'clarify_pricing_page' → 'pricing_clarity'
    """

    normalization_map = {
        'optimize_cta_contrast': 'cta_contrast_improvement',
        'improve_cta_contrast': 'cta_contrast_improvement',
        'enhance_cta_visibility': 'cta_contrast_improvement',

        'reduce_form_fields': 'form_field_reduction',
        'simplify_form': 'form_field_reduction',
        'minimize_form_fields': 'form_field_reduction',

        'add_trust_signals': 'trust_signal_addition',
        'add_social_proof': 'trust_signal_addition',
        'add_testimonials': 'trust_signal_addition',

        'mobile_optimization': 'mobile_responsiveness',
        'responsive_design': 'mobile_responsiveness',
        'mobile_first': 'mobile_responsiveness',

        'page_speed_optimization': 'performance_improvement',
        'improve_page_speed': 'performance_improvement',
        'optimize_images': 'performance_improvement',
    }

    return normalization_map.get(raw_type, raw_type)
```

**Storage Schema:**

```sql
CREATE TABLE learning_data_recommendation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID NOT NULL,
    recommendation_type VARCHAR NOT NULL,
    sector VARCHAR NOT NULL,
    cvr_improvement_percent FLOAT NOT NULL,
    statistical_confidence FLOAT,  -- p-value
    sample_size INT,
    test_duration_days INT,
    revenue_impact_estimate FLOAT,
    is_positive_result BOOLEAN,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX recommendation_id_idx (recommendation_id),
    INDEX recommendation_type_idx (recommendation_type),
    INDEX sector_idx (sector),
    INDEX cvr_improvement_idx (cvr_improvement_percent DESC),
    INDEX received_at_idx (received_at)
);
```

### 3. Generator → Learning Engine

**Trigger:** When generated page gets performance data

**Extracted Data:**

```python
def collect_generation_quality_metrics(page_id):
    """
    Track which generated outputs (copy, structure) performed best.
    Run periodically to gather performance metrics.
    """

    page = GeneratedPage.get(page_id)

    # Get A/B test results if available
    tests = page.ab_tests.filter(is_completed=True)

    quality_data = {
        'source': 'generator',
        'page_id': page.id,
        'client_id': page.client.id,
        'sector': page.client.sector,
        'page_type': page.page_type,  # landing, product, checkout
        'generated_at': page.created_at,
        'headline': page.headline,
        'headline_pattern': extract_pattern(page.headline),
        'cta_text': page.cta,
        'cta_pattern': extract_pattern(page.cta),
        'section_order': page.section_sequence,
        'tone': page.ai_parameters.get('tone', 'default'),
        'length_category': page.ai_parameters.get('copy_length', 'medium'),
        'performance_metrics': {
            'cvr': page.conversion_rate,
            'bounce_rate': page.bounce_rate,
            'avg_session_duration': page.avg_time_on_page,
            'scroll_depth': page.scroll_depth,
        },
        'test_results': [
            {
                'variant': test.variant_name,
                'cvr_lift': test.cvr_lift_percent,
                'winner': test.is_winner,
                'statistical_significance': test.p_value
            }
            for test in tests
        ],
        'user_satisfaction_score': page.user_feedback_score,  # 1-5
        'editor_quality_rating': page.editor_rating  # 1-5
    }

    store_learning_data({
        'type': 'generation_quality',
        'data': quality_data,
        'received_at': datetime.now()
    })

    queue_learning_task('detect_generation_patterns')

    return quality_data


def extract_pattern(text: str) -> dict:
    """
    Extract structural patterns from generated copy.
    Used to identify high-performing patterns.

    Returns pattern signature like:
    {
      'length': 'short' | 'medium' | 'long',
      'starts_with': 'question' | 'command' | 'benefit',
      'has_number': bool,
      'has_urgency': bool,
      'sentiment': 'positive' | 'neutral' | 'negative'
    }
    """

    from textblob import TextBlob

    blob = TextBlob(text)
    tokens = text.split()

    pattern = {
        'word_count': len(tokens),
        'length_category': 'short' if len(tokens) < 8 else (
            'long' if len(tokens) > 20 else 'medium'
        ),
        'starts_with_question': text.lstrip().startswith('?'),
        'starts_with_command': any(
            tokens[0].lower().endswith(verb)
            for verb in ['discover', 'learn', 'get', 'unlock', 'claim']
        ),
        'starts_with_benefit': any(
            tokens[0].lower() in ['increase', 'boost', 'improve', 'maximize']
        ),
        'has_number': any(char.isdigit() for char in text),
        'has_urgency': any(
            word in text.lower()
            for word in ['now', 'today', 'limited', 'urgent', 'only', 'fast']
        ),
        'sentiment': 'positive' if blob.sentiment.polarity > 0.1 else (
            'negative' if blob.sentiment.polarity < -0.1 else 'neutral'
        ),
        'contains_emoji': any(
            ord(char) > 127 for char in text
        )
    }

    return pattern
```

### 4. User Corrections → Learning Engine

**Trigger:** When team overrides AI suggestion

**Extracted Data:**

```python
def collect_user_correction(module: str, correction_id):
    """
    Record when user overrides AI suggestion (calibration signal).
    Run on every manual override.
    """

    correction = UserCorrection.get(correction_id)

    correction_data = {
        'source': 'user_correction',
        'module': module,  # audit, recommender, generator, page_optimizer
        'correction_id': correction.id,
        'user_id': correction.corrected_by.id,
        'corrected_at': correction.corrected_at,
        'ai_suggestion': correction.ai_value,
        'user_override': correction.user_value,
        'reason': correction.user_comment,
        'full_context': {
            'audit_id': correction.audit_id,
            'client_id': correction.client_id,
            'sector': correction.client.sector if correction.client else None
        },
        'estimated_impact': calculate_correction_impact(correction),
        'ai_confidence': correction.ai_confidence_score  # 0-1
    }

    store_learning_data({
        'type': 'user_correction',
        'data': correction_data,
        'received_at': datetime.now()
    })

    # High-impact corrections warrant immediate learning update
    if correction_data['estimated_impact'] == 'high':
        queue_learning_task('calibrate_from_correction', correction_data)

    return correction_data


def calculate_correction_impact(correction):
    """
    Estimate impact of user correction on final output.
    """

    # For recommendations: impact = whether recommended item was useful
    if correction.module == 'recommender':
        if correction.ai_suggestion.type == 'cta_optimization':
            # If user changed our CTA suggestion, that's high impact
            return 'high'
        return 'medium'

    # For generator: impact = if it affected actual content
    elif correction.module == 'generator':
        word_change = abs(len(correction.ai_value) - len(correction.user_value))
        if word_change > 10:
            return 'high'
        return 'medium' if word_change > 3 else 'low'

    # For audit: impact = if it changed finding severity
    elif correction.module == 'audit':
        if correction.ai_value.severity != correction.user_value.severity:
            return 'high'
        return 'medium'

    return 'low'
```

---

## PATTERN DETECTION METHODS

### 1. Frequency-Based Detection

```python
from scipy.stats import chi2_contingency

def detect_frequency_patterns():
    """
    Find findings/recommendations that appear significantly more often
    than would be expected by chance.

    Uses chi-square test: H0 = pattern is random, H1 = pattern is real
    """

    findings = fetch_recent_findings(days=30)

    # Group by category + sector
    groups = {}
    for finding in findings:
        key = (finding['category'], finding['sector'])
        if key not in groups:
            groups[key] = []
        groups[key].append(finding)

    detected_patterns = []

    for (category, sector), group_findings in groups.items():

        total_audits = count_audits(sector, days=30)
        finding_count = len(group_findings)
        no_finding_count = total_audits - finding_count

        # Chi-square test
        contingency_table = [
            [finding_count, no_finding_count]
        ]

        chi2, p_value, dof, expected = chi2_contingency(contingency_table)

        occurrence_rate = finding_count / total_audits

        if p_value < 0.05 and occurrence_rate > 0.2:  # Significant + common

            pattern = {
                'type': 'frequency_pattern',
                'category': category,
                'sector': sector,
                'occurrence_count': finding_count,
                'total_audits': total_audits,
                'occurrence_rate': occurrence_rate,
                'p_value': p_value,
                'is_significant': True,
                'avg_severity': np.mean([f['severity'] for f in group_findings]),
                'avg_impact': np.mean([f['impact_estimate'] for f in group_findings]),
                'examples': [f['description'] for f in group_findings[:3]]
            }

            detected_patterns.append(pattern)

    return detected_patterns
```

### 2. Correlation-Based Detection

```python
from scipy.stats import pearsonr

def detect_correlation_patterns():
    """
    Find correlations between variables.
    E.g.: "CVR improvements correlate with form field reduction"
    """

    recommendations = fetch_recommendations_with_results(days=90)

    # Extract features
    features = {}
    for rec in recommendations:
        key = rec['type']
        if key not in features:
            features[key] = []

        features[key].append({
            'cvr_lift': rec['cvr_improvement_percent'],
            'implementation_ease': rec['implementation_difficulty'],
            'sector': rec['sector']
        })

    correlations = []

    # Correlate recommendation difficulty vs CVR lift
    difficulties = [f['implementation_ease'] for key in features for f in features[key]]
    lifts = [f['cvr_lift'] for key in features for f in features[key]]

    if len(difficulties) > 5:
        corr_coeff, p_value = pearsonr(difficulties, lifts)

        if p_value < 0.05:
            correlations.append({
                'type': 'correlation_pattern',
                'variable_1': 'implementation_ease',
                'variable_2': 'cvr_improvement',
                'correlation': corr_coeff,
                'p_value': p_value,
                'interpretation': (
                    'Easier implementations tend to have higher impact'
                    if corr_coeff < 0 else
                    'Harder implementations correlate with higher impact'
                )
            })

    return correlations
```

### 3. Time Series Trend Detection

```python
from statsmodels.tsa.seasonal import seasonal_decompose
from scipy.signal import find_peaks

def detect_trend_patterns():
    """
    Identify trending patterns over time.
    E.g.: "Mobile optimization findings increasing week-over-week"
    """

    historical_data = fetch_finding_counts_by_week()

    patterns = []

    for category, sector_data in historical_data.items():
        for sector, weekly_counts in sector_data.items():

            # Convert to time series
            ts = pd.Series(weekly_counts)

            # Calculate trend using simple linear regression
            x = np.arange(len(ts))
            z = np.polyfit(x, ts, 1)
            trend_slope = z[0]

            # Detect if trend is significant (slope > 0.1 per week)
            if abs(trend_slope) > 0.1 and len(ts) >= 8:

                direction = 'increasing' if trend_slope > 0 else 'decreasing'

                patterns.append({
                    'type': 'trend_pattern',
                    'category': category,
                    'sector': sector,
                    'trend_direction': direction,
                    'trend_slope': trend_slope,
                    'weeks_of_data': len(ts),
                    'interpretation': (
                        f'{category} findings are {direction} by {abs(trend_slope):.2f}/week'
                    )
                })

    return patterns
```

### 4. Outlier Detection

```python
from scipy.stats import iqr

def detect_outlier_patterns():
    """
    Find anomalous results or surprising discoveries.
    E.g.: "SaaS sector had unusually high checkout friction"
    """

    recommendations = fetch_recommendations_with_results()

    patterns = []

    # Group by sector
    sectors = {}
    for rec in recommendations:
        sector = rec['sector']
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(rec['cvr_improvement_percent'])

    for sector, cvr_lifts in sectors.items():

        if len(cvr_lifts) < 5:
            continue

        Q1 = np.percentile(cvr_lifts, 25)
        Q3 = np.percentile(cvr_lifts, 75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = [x for x in cvr_lifts if x < lower_bound or x > upper_bound]

        if len(outliers) > 0:
            patterns.append({
                'type': 'outlier_pattern',
                'sector': sector,
                'outlier_count': len(outliers),
                'outlier_values': outliers,
                'median': np.median(cvr_lifts),
                'interpretation': (
                    f'{sector} has {len(outliers)} unusually high/low performers'
                )
            })

    return patterns
```

---

## INSIGHT GENERATION

### From Audit Patterns

```python
def generate_audit_insight(pattern: dict) -> dict:
    """
    Convert audit frequency pattern into actionable insight.
    """

    insight = {
        'type': 'audit_insight',
        'title': (
            f"{pattern['category'].replace('_', ' ').title()}: "
            f"{pattern['sector'].title()} Recurring Issue"
        ),
        'description': f"""
Pattern detected in {pattern['occurrence_count']} out of {pattern['total_audits']} \
audits ({pattern['occurrence_rate']:.0%}) in the {pattern['sector']} sector.

Statistical significance: p={pattern['p_value']:.4f} (highly significant)

Average severity: {pattern['avg_severity']:.1f}/10
Average estimated impact: {pattern['avg_impact']:.1f}%

Key examples from recent audits:
{chr(10).join(f"• {ex}" for ex in pattern['examples'])}
""",
        'pattern_type': pattern['category'],
        'sector': pattern['sector'],
        'applied_to': ['audit_engine'],
        'validation_count': pattern['occurrence_count'],
        'tags': [pattern['sector'], 'recurring_finding', 'high_frequency'],
        'recommendation': (
            f"When auditing {pattern['sector']} clients, prioritize checking for "
            f"{pattern['category'].replace('_', ' ')} issues. This pattern appears "
            f"in {pattern['occurrence_rate']:.0%} of similar audits."
        )
    }

    return insight
```

### From Recommendation Performance

```python
def generate_recommendation_insight(pattern: dict) -> dict:
    """
    Highlight high-performing recommendation types.
    """

    insight = {
        'type': 'recommendation_insight',
        'title': (
            f"High-Impact Recommendation: "
            f"{pattern['recommendation_type'].replace('_', ' ').title()}"
        ),
        'description': f"""
Recommendation type '{pattern['recommendation_type']}' shows exceptional performance:

Average CVR Improvement: {pattern['avg_cvr_lift']:.2f}%
Win Rate: {pattern['win_rate']:.0%} (positive results)
Sample Size: {pattern['sample_size']} validated tests
Average Confidence: {pattern['avg_confidence']:.3f}

Sector Performance:
{format_sector_breakdown(pattern['sector_breakdown'])}

Recommendation: Boost priority of this recommendation type in \
{pattern['primary_sector']} audits based on proven effectiveness.
""",
        'pattern_type': pattern['recommendation_type'],
        'sector': pattern['primary_sector'],
        'applied_to': ['recommender'],
        'validation_count': pattern['sample_size'],
        'cvr_impact': pattern['avg_cvr_lift'],
        'tags': [pattern['primary_sector'], 'high_impact', 'validated'],
        'examples': pattern['example_test_results']
    }

    return insight
```

---

## MODULE INTEGRATION POINTS

### Audit Engine Receives Learnings

```python
def initialize_audit_with_learnings(client, sector):
    """
    Boost audit checklist based on sector-specific patterns.
    """

    # Fetch relevant learnings
    learnings = fetch_learnings(
        applied_to=['audit_engine'],
        sector=sector,
        confidence__gte='medium'
    )

    audit_config = get_default_audit_config()

    for learning in learnings:

        # Find matching checklist items
        for category in learning.get('tags', []):
            matching_items = audit_config['checklist'].filter(
                category=learning['pattern_type']
            )

            for item in matching_items:

                # Boost priority
                priority_boost = {
                    'high': 1.5,
                    'medium': 1.2,
                    'low': 1.0
                }[learning['confidence']]

                item['priority'] *= priority_boost
                item['context'] = f"Sector pattern: {learning['title']}"

    return audit_config
```

### Recommender Receives Learnings

```python
def weight_recommendations(recommendations, sector, learnings_context):
    """
    Adjust recommendation scores based on historical performance.
    """

    weighted_recs = []

    for rec in recommendations:

        # Find learning about this recommendation type
        learning = find_learning(
            recommendation_type=rec.type,
            sector=sector,
            applied_to=['recommender']
        )

        if learning:

            # Boost based on CVR impact + confidence
            impact_multiplier = 1.0 + (
                learning['cvr_impact'] / 100 *
                CONFIDENCE_WEIGHTS[learning['confidence']]
            )

            rec.score *= impact_multiplier
            rec.context_note = (
                f"Based on {learning['validation_count']} validated tests: "
                f"avg {learning['cvr_impact']:.1f}% CVR improvement"
            )

        weighted_recs.append(rec)

    # Sort by weighted score
    return sorted(weighted_recs, key=lambda r: r.score, reverse=True)
```

### Generator Receives Learnings

```python
def inject_learnings_into_generation_prompt(sector, page_type, learnings):
    """
    Provide generation model with high-performing copy patterns.
    """

    relevant_learnings = fetch_learnings(
        applied_to=['generator'],
        sector=sector,
        pattern_type__contains='copy',
        confidence='high'
    )

    prompt_addition = """
## High-Performing Patterns for This Sector

Based on analysis of generated pages in your sector:
"""

    for learning in relevant_learnings:

        prompt_addition += f"""
### {learning['title']}
{learning['description']}

Consider: {learning['recommendation']}
"""

    return prompt_addition
```

---

## CONFIDENCE SCORING DEEP DIVE

### Multi-Factor Scoring Algorithm

```python
def calculate_confidence_score(insight: dict) -> tuple:
    """
    Calculate confidence as weighted combination of:
    1. Data volume (sample size)
    2. Statistical significance (p-value)
    3. Consistency (variance/effect size)
    4. Recency (time since observed)
    5. Validation rate (how often confirmed)

    Returns: (confidence_level, confidence_score)
    """

    base_score = 0.5

    # Factor 1: Sample Size Weight
    sample_size = insight.get('validation_count', 1)
    if sample_size >= 30:
        sample_boost = 0.25
    elif sample_size >= 15:
        sample_boost = 0.15
    elif sample_size >= 8:
        sample_boost = 0.10
    elif sample_size >= 4:
        sample_boost = 0.05
    else:
        sample_boost = 0

    # Factor 2: Statistical Significance
    p_value = insight.get('p_value', 0.05)
    if p_value < 0.001:
        significance_boost = 0.20
    elif p_value < 0.01:
        significance_boost = 0.15
    elif p_value < 0.05:
        significance_boost = 0.10
    else:
        significance_boost = 0

    # Factor 3: Consistency (standard deviation / mean)
    if 'variance' in insight:
        # Lower variance = higher consistency
        cv = insight['variance'] / max(insight['mean'], 0.01)
        consistency_score = max(0, 1 - cv)
        consistency_boost = consistency_score * 0.15
    else:
        consistency_boost = 0

    # Factor 4: Effect Size
    if 'effect_size' in insight:
        effect = insight['effect_size']
        if effect > 0.5:
            effect_boost = 0.15
        elif effect > 0.3:
            effect_boost = 0.10
        elif effect > 0.1:
            effect_boost = 0.05
        else:
            effect_boost = 0
    else:
        effect_boost = 0

    # Factor 5: Recency
    created_at = insight.get('created_at', datetime.now())
    days_old = (datetime.now() - created_at).days

    if days_old < 7:
        recency_bonus = 0.10
    elif days_old < 30:
        recency_bonus = 0.05
    elif days_old < 90:
        recency_bonus = 0
    else:
        recency_bonus = -0.05  # Deduct for stale data

    # Factor 6: Validation Consistency
    if 'validation_history' in insight:
        confirmations = sum(
            1 for v in insight['validation_history']
            if v['status'] == 'confirmed'
        )
        refutations = sum(
            1 for v in insight['validation_history']
            if v['status'] == 'refuted'
        )
        total_validations = confirmations + refutations

        if total_validations > 0:
            validation_rate = confirmations / total_validations
            if validation_rate > 0.8:
                validation_boost = 0.10
            elif validation_rate > 0.6:
                validation_boost = 0.05
            else:
                validation_boost = -0.10
        else:
            validation_boost = 0
    else:
        validation_boost = 0

    # Aggregate
    total_score = (
        base_score +
        sample_boost +
        significance_boost +
        consistency_boost +
        effect_boost +
        recency_bonus +
        validation_boost
    )

    # Clamp to [0, 1]
    final_score = max(0, min(1.0, total_score))

    # Map to categorical
    if final_score >= 0.85:
        confidence = 'high'
    elif final_score >= 0.65:
        confidence = 'medium'
    else:
        confidence = 'low'

    # Log scoring breakdown
    log_scoring_detail({
        'insight_id': insight.get('id'),
        'factors': {
            'sample_boost': sample_boost,
            'significance_boost': significance_boost,
            'consistency_boost': consistency_boost,
            'effect_boost': effect_boost,
            'recency_bonus': recency_bonus,
            'validation_boost': validation_boost
        },
        'final_score': final_score,
        'confidence': confidence
    })

    return confidence, final_score
```

---

## MEMORY & CALIBRATION

### Memory Table Operations

```python
def update_memory_from_correction(correction_data):
    """
    Store user correction as calibration memory.
    Used to improve AI judgment over time.
    """

    memory_entry = {
        'type': 'correction',
        'module': correction_data['module'],
        'ai_was_wrong_about': correction_data['field'],
        'context': correction_data['context'],
        'user_correction': correction_data['override'],
        'impact': correction_data['impact'],
        'weight': IMPACT_TO_WEIGHT[correction_data['impact']],
        'created_at': datetime.now(),
        'expires_at': None  # No expiry - permanent learning
    }

    store_memory(memory_entry)

    # If high-impact, update related learnings
    if correction_data['impact'] == 'high':
        apply_correction_to_learnings(memory_entry)


def apply_correction_to_learnings(correction_memory):
    """
    Update learnings based on correction.
    Lower confidence if frequently corrected.
    """

    related_learnings = find_related_learnings(
        correction_memory['context']
    )

    for learning in related_learnings:

        correction_rate = count_corrections_for_learning(learning.id) / \
                         max(learning['validation_count'], 1)

        # If >30% corrections, downgrade confidence
        if correction_rate > 0.3:
            new_confidence = downgrade_confidence(learning['confidence'])

            update_learning_confidence(
                learning.id,
                new_confidence,
                reason=f"Correction rate {correction_rate:.0%} detected"
            )
```

---

## LEARNING LIFECYCLE

### Statuses

```
pending
  ↓ (scheduled review)
under_review
  ↓ (team validates)
[confirmed OR refuted]
  ↓
archived (after 180 days)
```

### Scheduled Review Process

```python
def schedule_learning_reviews():
    """
    Regularly validate high-impact learnings.
    """

    pending_learnings = fetch_learnings(
        status='pending',
        created_at__lte=datetime.now() - timedelta(days=3)
    )

    for learning in pending_learnings:

        # Create review task
        review_task = {
            'learning_id': learning['id'],
            'title': f"Validate: {learning['title']}",
            'description': f"""
Confidence: {learning['confidence']}
Sample size: {learning['validation_count']}
Last observation: {learning['created_at']}

Is this pattern still valid? Has it changed?
Are there exceptions or edge cases?
Should we adjust confidence?
""",
            'assigned_to': 'cro_team',
            'due_date': datetime.now() + timedelta(days=7)
        }

        create_task(review_task)
```

---

## OPERATIONAL PROCEDURES

### Manual Learning Trigger

```python
def manual_learning_run():
    """
    Run full learning pipeline on demand.
    Called when user clicks "Synchroniser" button.
    """

    log_info('Starting manual learning run...')

    start_time = datetime.now()

    # 1. Collect all new data
    audit_data = collect_recent_audit_data()
    rec_data = collect_recommendation_performance_data()
    gen_data = collect_generation_quality_data()
    correction_data = collect_user_corrections()

    # 2. Detect patterns
    audit_patterns = detect_audit_patterns()
    rec_patterns = detect_recommendation_patterns()
    gen_patterns = detect_generation_patterns()
    trend_patterns = detect_trend_patterns()

    # 3. Generate insights
    insights = []
    for pattern in audit_patterns + rec_patterns + gen_patterns + trend_patterns:
        insight = generate_insight(pattern)
        confidence, score = calculate_confidence_score(insight)
        insight['confidence'] = confidence
        insight['confidence_score'] = score
        insights.append(insight)

    # 4. Store insights
    stored_count = store_learnings(insights)

    # 5. Distribute to modules
    distribute_learnings_to_modules(insights)

    # 6. Optionally push to Notion
    proposed_pushes = []
    for insight in insights:
        if insight['confidence'] == 'high' and insight['validation_count'] > 20:
            proposed_pushes.append(insight)

    duration = (datetime.now() - start_time).total_seconds()

    result = {
        'success': True,
        'insights_generated': len(insights),
        'insights_high_confidence': len([i for i in insights if i['confidence'] == 'high']),
        'stored': stored_count,
        'proposed_pushes_to_notion': len(proposed_pushes),
        'duration_seconds': duration,
        'timestamp': datetime.now().isoformat()
    }

    log_info(f'Learning run completed: {result}')

    return result
```

---

**End of Learning Engine Reference**

