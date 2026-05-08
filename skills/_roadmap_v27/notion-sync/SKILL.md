# Notion Sync & AI Learning Engine
## Knowledge Management + Continuous Intelligence System pour GrowthCRO

**Version:** 1.0.0
**Status:** Production
**Last Updated:** 2026-04-05

---

## ROLE

Tu opères comme **Ingénieur Knowledge + Data Scientist** de l'écosystème GrowthCRO. Tu pilotes le cœur du système d'apprentissage continu — la synchronisation bidirectionnelle avec la base de connaissance Notion et le moteur qui rend GrowthCRO plus intelligent à chaque audit, chaque recommandation, chaque test A/B.

### Responsabilités Clés

1. **Orchestration Knowledge Notion**
   - Synchroniser contenus Notion ↔ GrowthCRO en temps quasi-réel
   - Indexer + embedder tout contenu pour recherche sémantique
   - Maintenir source of truth (Notion = manuel, GrowthCRO = auto-généré)
   - Gérer conflits + versions

2. **Learning Pipeline**
   - Collecter patterns d'audits, recommandations, tests A/B
   - Détecter insights statiquement significants
   - Scorer confiance (low/medium/high)
   - Alimenter contexte des autres modules (Audit Engine, Recommender, Generator)

3. **Calibration Mémoire**
   - Tracker corrections utilisateur
   - Valider patterns via résultats réels (CVR improvement via Catchr)
   - Refiner scoring de confiance progressivement
   - Maintenir memory table avec ce qui a été appris

4. **UX Interface**
   - Bouton "Synchroniser" (trigger + status)
   - Dashboard insights (patterns découverts, confiance, sources)
   - Visualiser feedback loop (recommandation → CVR impact → learning)

---

## ARCHITECTURE GÉNÉRALE

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTION SYNC LAYER                            │
├──────────────────────────┬──────────────────────────────────────┤
│   PULL (Notion → GC)     │     PUSH (GC → Notion)               │
│ • Fetch pages (API)      │ • Propose learnings                  │
│ • Index + chunk text     │ • Create insight entries             │
│ • Generate embeddings    │ • Update performance refs            │
│ • Store pgvector         │ • Resolve conflicts                  │
└──────────────────────────┴──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│         VECTORSTORE (pgvector/Supabase) + METADATA              │
│  • Notion content (embeddings, source, last_sync, chunk_id)    │
│  • Rankings (confidence scores, validation count)              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│              LEARNING ENGINE                                    │
├─────────────┬──────────────┬──────────────┬──────────────┐     │
│ Audit       │ Recomm.      │ Generation   │ User         │     │
│ Patterns    │ Performance  │ Quality      │ Corrections  │     │
└─────────────┴──────────────┴──────────────┴──────────────┘     │
                           ↓                                      │
│  PATTERN DETECTION       │ INSIGHT GENERATION       │ SCORING  │
│  (anomaly + frequency)   │ (human-readable)        │ (ML)     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│         AI_LEARNINGS TABLE (Context Layer)                      │
│  • Pattern description, confidence, validation_count            │
│  • Applied_to (which modules benefit)                          │
│  • Last_validated, next_review                                 │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────────┐
│    DISTRIBUTED TO ALL MODULES AS CONTEXT                        │
│  (Audit Engine, Recommender, Generator, Page Optimizer)        │
└────────────────────────────────────────────────────────────────┘
```

---

## SYNC PROTOCOL

### 1. Notion API Integration

**Endpoint Base:** `https://api.notion.com/v1`

**Authentication:**
```
Authorization: Bearer {NOTION_API_KEY}
Notion-Version: 2024-02-15
Content-Type: application/json
```

**Content Types Synced:**
- Pages (CRO templates, process docs, case studies)
- Databases (client notes, best practices, competitor analyses)
- Rich text, code blocks, tables
- Metadata: last_edited_time, created_by, last_edited_by

### 2. Pull Protocol (Notion → GrowthCRO)

**Trigger:**
- Manual: Button "Synchroniser" dans UI
- Automatic: Every 6 hours (0, 6, 12, 18 UTC)
- Event-based: Webhooks from Notion (when available)

**Fetch Logic:**

```python
def sync_pull_notion():
    """
    Orchestrate bidirectional sync with Notion workspace.
    Source of truth: Notion (manual content) | GrowthCRO (auto)
    """

    # Step 1: Authenticate + Get workspace structure
    workspace = fetch_notion_workspace()
    databases = workspace.get_databases()  # Filter by growth_crm_tag

    # Step 2: Fetch all pages with modifications since last sync
    pages = []
    for db in databases:
        new_pages = fetch_database_pages(
            database_id=db.id,
            filter={'property': 'last_edited_time', 'after': LAST_SYNC_TIME}
        )
        pages.extend(new_pages)

    # Step 3: For each page, extract structured content
    for page in pages:
        content = {
            'page_id': page.id,
            'title': extract_title(page),
            'content_blocks': [],
            'metadata': {
                'created_time': page.created_time,
                'last_edited_time': page.last_edited_time,
                'created_by': page.created_by.id,
                'properties': page.properties,
            },
            'status': 'pending_index'
        }

        # Extract all block content
        for block in fetch_page_blocks(page.id):
            if block.type == 'paragraph':
                content['content_blocks'].append({
                    'type': 'text',
                    'value': block.paragraph.rich_text.to_plain_text()
                })
            elif block.type == 'heading_1':
                content['content_blocks'].append({
                    'type': 'heading_1',
                    'value': block.heading_1.rich_text.to_plain_text()
                })
            elif block.type == 'code':
                content['content_blocks'].append({
                    'type': 'code',
                    'language': block.code.language,
                    'value': block.code.rich_text.to_plain_text()
                })
            elif block.type == 'table':
                content['content_blocks'].append({
                    'type': 'table',
                    'value': extract_table_structure(block)
                })
            # ... etc for other block types

        # Store raw content
        store_notion_content(content)

    return pages
```

**Data Model (Raw Notion Storage):**

```sql
CREATE TABLE notion_content_raw (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id VARCHAR NOT NULL UNIQUE,
    workspace_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    content_blocks JSONB NOT NULL,
    metadata JSONB NOT NULL,
    status VARCHAR DEFAULT 'pending_index',  -- pending_index, indexed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notion_created_time TIMESTAMP,
    notion_last_edited_time TIMESTAMP,
    INDEX notion_page_id_idx (page_id),
    INDEX status_idx (status),
    INDEX last_synced_idx (last_synced)
);
```

### 3. Indexing & Chunking Strategy

**Step 1: Semantic Chunking**

```python
def chunk_notion_content(content: dict, chunk_size=512, overlap=50):
    """
    Split Notion content into semantic chunks optimized for embeddings.
    Respects block boundaries for better retrieval.
    """

    chunks = []
    current_chunk = []
    current_length = 0

    for block in content['content_blocks']:
        block_text = block['value']
        block_tokens = len(tokenize(block_text))

        # If adding this block exceeds chunk_size, save current chunk
        if current_length + block_tokens > chunk_size and current_chunk:
            chunk_text = ' '.join([b['value'] for b in current_chunk])
            chunks.append({
                'text': chunk_text,
                'source_page_id': content['page_id'],
                'source_title': content['title'],
                'blocks': len(current_chunk),
                'tokens': current_length,
                'metadata': {
                    'block_types': [b['type'] for b in current_chunk],
                    'created_time': content['metadata']['created_time'],
                    'edited_by': content['metadata']['created_by'],
                }
            })

            # Start new chunk with overlap
            overlap_blocks = []
            overlap_length = 0
            for block in reversed(current_chunk):
                if overlap_length < overlap:
                    overlap_blocks.insert(0, block)
                    overlap_length += len(tokenize(block['value']))
                else:
                    break

            current_chunk = overlap_blocks + [block]
            current_length = overlap_length + block_tokens
        else:
            current_chunk.append(block)
            current_length += block_tokens

    # Don't forget final chunk
    if current_chunk:
        chunk_text = ' '.join([b['value'] for b in current_chunk])
        chunks.append({
            'text': chunk_text,
            'source_page_id': content['page_id'],
            'source_title': content['title'],
            'blocks': len(current_chunk),
            'tokens': current_length,
            'metadata': {
                'block_types': [b['type'] for b in current_chunk],
            }
        })

    return chunks
```

**Step 2: Generate Embeddings (pgvector)**

```python
def generate_embeddings(chunks: list):
    """
    Generate dense embeddings via OpenAI API + store in pgvector.
    Batch embed for efficiency (max 100 chunks per request).
    """

    from openai import OpenAI
    import psycopg2

    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()

    for i in range(0, len(chunks), 100):
        batch = chunks[i:i+100]

        # Embed batch
        embeddings = client.embeddings.create(
            model='text-embedding-3-small',
            input=[c['text'] for c in batch],
            dimensions=1536
        )

        # Store in pgvector
        for chunk, embedding_obj in zip(batch, embeddings.data):
            embedding = embedding_obj.embedding

            cur.execute("""
                INSERT INTO notion_embeddings (
                    page_id, chunk_text, embedding,
                    source_title, block_types, tokens, metadata
                ) VALUES (
                    %s, %s, %s::vector, %s, %s, %s, %s
                )
            """, (
                chunk['source_page_id'],
                chunk['text'],
                embedding,
                chunk['source_title'],
                chunk['metadata']['block_types'],
                chunk['tokens'],
                json.dumps(chunk['metadata'])
            ))

        conn.commit()

    cur.close()
    conn.close()
```

**Embedding Storage Schema:**

```sql
CREATE TABLE notion_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id VARCHAR NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    source_title VARCHAR NOT NULL,
    block_types VARCHAR[],
    tokens INT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES notion_content_raw(page_id) ON DELETE CASCADE,
    INDEX embedding_idx USING ivfflat (embedding vector_cosine_ops),
    INDEX page_id_idx (page_id)
);
```

### 4. Push Protocol (GrowthCRO → Notion)

**Trigger:** Learnings generator completes insight → proposal created

**Push Logic:**

```python
def push_learning_to_notion(learning: dict):
    """
    Propose new learnings as Notion database entries.
    Creates in 'AI Insights' database (append-only, versioned).
    """

    # Create page in target database
    page_data = {
        'parent': {
            'database_id': NOTION_AI_INSIGHTS_DB_ID
        },
        'properties': {
            'Insight': {
                'title': [{'text': {'content': learning['title']}}]
            },
            'Description': {
                'rich_text': [{'text': {'content': learning['description']}}]
            },
            'Confidence': {
                'select': {'name': learning['confidence']}  # low, medium, high
            },
            'Applied To': {
                'multi_select': [
                    {'name': module} for module in learning['applied_to']
                ]
            },
            'Validation Count': {
                'number': learning['validation_count']
            },
            'CVR Impact': {
                'number': learning.get('cvr_impact', None)
            },
            'Tags': {
                'multi_select': [
                    {'name': tag} for tag in learning['tags']
                ]
            }
        }
    }

    # Add examples as child blocks
    children = []
    for example in learning.get('examples', []):
        children.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'text': {'content': example}}]
            }
        })

    # POST to Notion
    response = requests.post(
        f'{NOTION_API_BASE}/pages',
        headers=NOTION_HEADERS,
        json=page_data
    )

    new_page_id = response.json()['id']

    # Store reference locally
    store_pushed_learning(learning['id'], new_page_id, 'notion_pushed')

    return new_page_id
```

### 5. Conflict Resolution

**Priority Matrix:**

| Scenario | Decision | Rule |
|----------|----------|------|
| Content modified in Notion only | Accept Notion version | Notion = source of truth for manual content |
| Content modified in GC only | Accept GC version | GC = source of truth for auto-generated content |
| Both modified (rare) | Notion wins + flag conflict | Content tagged as "needs_review" |
| GC tries to overwrite manual content | Reject + create proposal instead | Cannot overwrite manual Notion content |
| Version conflict (chain) | Use last_edited_time | Use Notion's timestamp as reference |

**Implementation:**

```python
def resolve_sync_conflict(notion_version, gc_version, content_type):
    """
    Resolve conflicts based on source-of-truth rules.
    """

    if content_type == 'manual_notion_content':
        # Notion is always authoritative for manual entries
        return notion_version, 'notion_authoritative'

    elif content_type == 'auto_generated':
        # GC is authoritative for auto-generated
        return gc_version, 'gc_authoritative'

    elif content_type == 'shared_reference':
        # Both modified = flag for human review
        return {
            'notion': notion_version,
            'gc': gc_version,
            'status': 'conflict_needs_review',
            'suggested_resolution': 'manual_merge'
        }, 'conflict'

    # Default: Notion as source of truth
    return notion_version, 'notion_default'
```

---

## EMBEDDING & RETRIEVAL STRATEGY

### 1. Embedding Approach

**Model:** OpenAI `text-embedding-3-small` (1536 dimensions)

**Why this model:**
- Optimized for knowledge retrieval (not conversation)
- Good cost/performance ratio
- Industry standard for semantic search in knowledge bases

**Chunking Parameters:**
- Chunk size: 512 tokens (= ~2KB text)
- Overlap: 50 tokens (respects semantic boundaries)
- Strategy: Respect Notion block boundaries (headings, code blocks)

### 2. Similarity Thresholds

```python
SIMILARITY_THRESHOLDS = {
    'audit_context': 0.75,      # High bar = only highly relevant patterns
    'recommendation_context': 0.70,  # Medium-high = guide recommendations
    'generation_context': 0.65,  # Medium = inspire copy/structure
    'fallback': 0.60            # Catch-all for weak signals
}

def retrieve_relevant_notion_content(query: str, module: str, limit=5):
    """
    Semantic search in Notion embeddings.
    Returns top-K chunks + source pages for context.
    """

    # Generate query embedding
    query_embedding = client.embeddings.create(
        model='text-embedding-3-small',
        input=query,
        dimensions=1536
    ).data[0].embedding

    threshold = SIMILARITY_THRESHOLDS.get(f'{module}_context', 0.60)

    # Vector search in pgvector
    conn = psycopg2.connect(SUPABASE_CONNECTION)
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            id, page_id, source_title, chunk_text,
            1 - (embedding <=> %s::vector) as similarity,
            metadata
        FROM notion_embeddings
        WHERE 1 - (embedding <=> %s::vector) > %s
        ORDER BY similarity DESC
        LIMIT %s
    """, (query_embedding, query_embedding, threshold, limit))

    results = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            'chunk_id': r[0],
            'page_id': r[1],
            'source_title': r[2],
            'text': r[3],
            'similarity': r[4],
            'metadata': r[5]
        }
        for r in results
    ]
```

### 3. Retrieval Contexts

**For Audit Engine:**
```
Query: "e-commerce checkout flow CRO patterns"
Retrieved: [Best practices page, case study: ecom friction patterns, ...]
Use: Populate audit checklist + comparative benchmarks
```

**For Recommender:**
```
Query: "form field abandonment solutions"
Retrieved: [Template: optimized form design, test results: placeholder vs label, ...]
Use: Rank recommendations by proven effectiveness
```

**For Generator:**
```
Query: "hero section copywriting patterns high-converting"
Retrieved: [Template collection, case studies with results, ...]
Use: Inspire + structure for generated copy
```

---

## LEARNING ENGINE PIPELINE

### 1. Data Collection Sources

**A. Audit Patterns**

```python
def collect_audit_patterns():
    """
    After each audit, extract recurring findings across sectors.
    """

    audit = get_latest_audit()

    for finding in audit.findings:
        # Extract pattern
        pattern = {
            'type': finding.category,  # e.g., 'checkout_friction'
            'severity': finding.severity,
            'affected_sector': audit.client.sector,
            'page_url': finding.page,
            'finding_text': finding.description,
            'timestamp': audit.completed_at
        }

        # Check if similar pattern exists
        existing = find_similar_pattern(
            pattern['type'],
            sector=pattern['affected_sector']
        )

        if existing:
            existing['occurrence_count'] += 1
            existing['last_seen'] = pattern['timestamp']
        else:
            pattern['occurrence_count'] = 1
            store_pattern(pattern)

    return audit.findings
```

**B. Recommendation Performance**

```python
def collect_recommendation_performance():
    """
    When Catchr tracks CVR improvement, link back to recommendation.
    """

    catchr_events = fetch_catchr_cvr_improvements()

    for event in catchr_events:
        recommendation = find_recommendation_by_test_id(
            event.recommendation_id
        )

        performance = {
            'recommendation_id': recommendation.id,
            'baseline_cvr': event.baseline_cvr,
            'variant_cvr': event.variant_cvr,
            'lift_percent': ((event.variant_cvr - event.baseline_cvr) /
                            event.baseline_cvr * 100),
            'confidence': event.statistical_confidence,
            'duration_days': event.test_duration,
            'implementation_date': recommendation.implemented_at,
            'sector': recommendation.client.sector,
            'recommendation_type': recommendation.type
        }

        store_recommendation_performance(performance)

    return catchr_events
```

**C. Generation Quality**

```python
def collect_generation_quality_metrics():
    """
    Track which generated outputs (copy, structure) scored highest.
    Sources: user feedback, A/B test results, conversion data.
    """

    generated_pages = find_pages_generated_by_growthcro()

    for page in generated_pages:
        metrics = {
            'page_id': page.id,
            'headline_pattern': extract_headline_pattern(page.headline),
            'cta_pattern': extract_cta_pattern(page.cta),
            'section_order': page.section_order,
            'cvr_score': page.conversion_rate,  # vs baseline
            'engagement_score': page.bounce_rate,
            'user_feedback_score': page.user_satisfaction,
            'sector': page.client.sector,
            'generated_at': page.created_at
        }

        store_generation_metrics(metrics)

    return generated_pages
```

**D. User Corrections (Calibration Data)**

```python
def collect_user_corrections():
    """
    When team overrides AI suggestion → learning opportunity.
    What did we get wrong? How to improve?
    """

    corrections = fetch_all_user_overrides(
        since=last_learning_run
    )

    for correction in corrections:
        calibration = {
            'module': correction.module,  # audit, recommender, generator
            'ai_suggestion': correction.ai_value,
            'user_override': correction.user_value,
            'reason': correction.user_comment,
            'context': correction.full_context,
            'timestamp': correction.corrected_at,
            'corrected_by_user': correction.user_id,
            'impact': correction.estimated_impact  # high/medium/low
        }

        store_user_correction(calibration)

    return corrections
```

### 2. Pattern Detection

```python
def detect_patterns(data_source: str):
    """
    Identify statistically significant patterns across collected data.
    Uses frequency + correlation analysis.
    """

    if data_source == 'audit_patterns':
        return detect_audit_patterns()
    elif data_source == 'recommendation_performance':
        return detect_recommendation_patterns()
    elif data_source == 'generation_quality':
        return detect_generation_patterns()
    elif data_source == 'user_corrections':
        return detect_calibration_patterns()


def detect_audit_patterns():
    """
    Example: Find patterns like "checkout friction appears in 60% of
    e-commerce audits" or "mobile nav discovery issues in SaaS".
    """

    from scipy import stats

    # Aggregate by category + sector
    pattern_groups = {}

    for pattern in fetch_all_patterns():
        key = (pattern['type'], pattern['affected_sector'])
        if key not in pattern_groups:
            pattern_groups[key] = []
        pattern_groups[key].append(pattern)

    detected = []

    for (pattern_type, sector), patterns in pattern_groups.items():

        # Calculate frequency
        total_audits_in_sector = count_audits_in_sector(sector)
        occurrence_rate = len(patterns) / total_audits_in_sector

        # Chi-square test: is this pattern overrepresented?
        chi2, p_value = stats.chisquare(
            [len(patterns), total_audits_in_sector - len(patterns)]
        )

        if p_value < 0.05:  # Statistically significant
            detected.append({
                'pattern_type': pattern_type,
                'sector': sector,
                'occurrence_count': len(patterns),
                'occurrence_rate': occurrence_rate,
                'statistical_significance': p_value,
                'severity_avg': np.mean([p['severity'] for p in patterns]),
                'examples': [p['finding_text'] for p in patterns[:3]]
            })

    return detected


def detect_recommendation_patterns():
    """
    Find high-impact recommendation types by sector + CVR improvement.
    """

    perf_data = fetch_recommendation_performance()

    # Group by type + sector
    groups = {}
    for perf in perf_data:
        key = (perf['recommendation_type'], perf['sector'])
        if key not in groups:
            groups[key] = []
        groups[key].append(perf)

    detected = []

    for (rec_type, sector), perfs in groups.items():

        # Average lift
        avg_lift = np.mean([p['lift_percent'] for p in perfs])

        # Consistency (std dev)
        std_lift = np.std([p['lift_percent'] for p in perfs])

        # Win rate (% with positive lift)
        win_count = sum(1 for p in perfs if p['lift_percent'] > 0)
        win_rate = win_count / len(perfs)

        # Only highlight if consistent + positive
        if avg_lift > 2.0 and win_rate > 0.7:
            detected.append({
                'recommendation_type': rec_type,
                'sector': sector,
                'avg_cvr_lift_percent': avg_lift,
                'consistency': 1 - (std_lift / avg_lift),  # 0-1 score
                'win_rate': win_rate,
                'sample_size': len(perfs),
                'avg_confidence': np.mean([p['confidence'] for p in perfs])
            })

    return detected
```

### 3. Insight Generation

```python
def generate_insights(patterns: list):
    """
    Convert raw patterns into human-readable, actionable insights.
    """

    insights = []

    for pattern in patterns:
        if pattern['type'] == 'audit_pattern':
            insight = generate_audit_insight(pattern)
        elif pattern['type'] == 'recommendation_pattern':
            insight = generate_recommendation_insight(pattern)
        elif pattern['type'] == 'generation_pattern':
            insight = generate_generation_insight(pattern)
        elif pattern['type'] == 'calibration_pattern':
            insight = generate_calibration_insight(pattern)

        insights.append(insight)

    return insights


def generate_audit_insight(pattern: dict):
    """
    Transform audit pattern into actionable insight.

    Input:
    {
        'pattern_type': 'checkout_friction',
        'sector': 'e-commerce',
        'occurrence_rate': 0.60,
        'severity_avg': 8.2,
        'examples': [...]
    }

    Output:
    {
        'title': 'Checkout Friction: E-commerce Recurring Issue',
        'description': '60% of e-commerce audits show checkout flow issues...',
        'recommendation': 'Audit checklist should prioritize...',
        'applied_to': ['audit_engine'],
        'confidence': 'high',
        'examples': [...]
    }
    """

    title = f"{pattern['pattern_type'].replace('_', ' ').title()}: \
{pattern['sector'].title()} Recurring Issue"

    description = f"""
Pattern detected across {pattern['occurrence_count']} audits in the
{pattern['sector']} sector ({pattern['occurrence_rate']:.0%} occurrence rate).
Average severity: {pattern['severity_avg']}/10.

Key examples:
{chr(10).join(f"• {ex}" for ex in pattern['examples'])}
"""

    return {
        'title': title,
        'description': description,
        'pattern_type': pattern['pattern_type'],
        'sector': pattern['sector'],
        'applied_to': ['audit_engine'],
        'confidence': 'high' if pattern['occurrence_rate'] > 0.5 else 'medium',
        'validation_count': pattern['occurrence_count'],
        'tags': [pattern['sector'], 'recurring_finding']
    }


def generate_recommendation_insight(pattern: dict):
    """
    Insight from high-impact recommendations.

    Input:
    {
        'recommendation_type': 'cta_contrast_improvement',
        'sector': 'saas',
        'avg_cvr_lift_percent': 3.2,
        'win_rate': 0.85,
        'sample_size': 12
    }

    Output: Insight that should influence Recommender module weighting
    """

    title = f"High-Impact Recommendation: {pattern['recommendation_type'].replace('_', ' ').title()}"

    description = f"""
Recommendation type '{pattern['recommendation_type']}' shows
{pattern['avg_cvr_lift_percent']:.1f}% average CVR lift in {pattern['sector']}
sector (win rate: {pattern['win_rate']:.0%}, n={pattern['sample_size']}).

Recommended: Increase priority of this recommendation type in audits
for {pattern['sector']} clients.
"""

    return {
        'title': title,
        'description': description,
        'cvr_impact': pattern['avg_cvr_lift_percent'],
        'applied_to': ['recommender'],
        'confidence': 'high' if pattern['sample_size'] > 10 else 'medium',
        'validation_count': pattern['sample_size'],
        'tags': [pattern['sector'], 'high_impact'],
        'recommendation_type': pattern['recommendation_type']
    }
```

### 4. Confidence Scoring

```python
def score_confidence(insight: dict, data_source: str):
    """
    Score confidence based on:
    - Sample size (more data = higher confidence)
    - Consistency (low variance = higher confidence)
    - Statistical significance (p-value)
    - Time recency (recent patterns = moderate adjustment)
    """

    base_score = 0.5  # Start at medium

    # Factor 1: Sample size
    if insight['validation_count'] >= 20:
        base_score += 0.3
    elif insight['validation_count'] >= 10:
        base_score += 0.2
    elif insight['validation_count'] >= 5:
        base_score += 0.1

    # Factor 2: Consistency (if available)
    if 'consistency_score' in insight:
        consistency_boost = insight['consistency_score'] * 0.2
        base_score += consistency_boost

    # Factor 3: Win rate / effectiveness
    if 'win_rate' in insight:
        if insight['win_rate'] > 0.8:
            base_score += 0.2
        elif insight['win_rate'] > 0.6:
            base_score += 0.1

    # Factor 4: Time recency
    days_old = (datetime.now() - insight.get('created_at')).days
    if days_old < 7:
        recency_bonus = 0.1
    elif days_old < 30:
        recency_bonus = 0.05
    else:
        recency_bonus = 0
    base_score += recency_bonus

    # Cap at 1.0
    final_score = min(base_score, 1.0)

    # Map to categorical confidence
    if final_score >= 0.8:
        confidence = 'high'
    elif final_score >= 0.6:
        confidence = 'medium'
    else:
        confidence = 'low'

    return confidence, final_score
```

### 5. Storage in AI_LEARNINGS Table

```sql
CREATE TABLE ai_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    pattern_type VARCHAR NOT NULL,
    sector VARCHAR,
    confidence VARCHAR NOT NULL,  -- low, medium, high
    confidence_score FLOAT,
    validation_count INT,
    cvr_impact FLOAT,
    applied_to VARCHAR[],  -- [audit_engine, recommender, generator]
    tags VARCHAR[],
    examples TEXT[],
    data_source VARCHAR,  -- audit_patterns, recommendation_perf, etc
    notion_page_id VARCHAR,  -- if pushed to Notion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_validated TIMESTAMP,
    next_review_date TIMESTAMP,
    review_status VARCHAR DEFAULT 'pending',  -- pending, validated, refuted
    INDEX sector_idx (sector),
    INDEX confidence_idx (confidence),
    INDEX applied_to_idx (applied_to),
    INDEX created_at_idx (created_at)
);

CREATE TABLE ai_learnings_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learning_id UUID NOT NULL REFERENCES ai_learnings(id),
    old_confidence VARCHAR,
    new_confidence VARCHAR,
    reason VARCHAR,
    updated_by VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (learning_id) REFERENCES ai_learnings(id) ON DELETE CASCADE
);
```

### 6. Integration with Other Modules

#### **Audit Engine Integration**

```python
# When Audit Engine initializes:
def initialize_audit_with_learnings(client, sector):

    # Fetch learnings relevant to this client's sector
    relevant_patterns = find_learnings(
        applied_to=['audit_engine'],
        sector=sector,
        confidence__gte='medium'
    )

    # Boost audit checklist items that are known patterns
    for learning in relevant_patterns:
        boost_checklist_item(
            category=learning['pattern_type'],
            priority_boost=CONFIDENCE_TO_BOOST[learning['confidence']]
        )

    return audit_engine
```

#### **Recommender Integration**

```python
# When Recommender ranks recommendations:
def weight_recommendations(recommendations, client_sector, learnings_context):

    weighted = []

    for rec in recommendations:

        # Check if there's a learning about this recommendation type
        matching_learning = find_learning(
            recommendation_type=rec.type,
            sector=client_sector
        )

        if matching_learning:
            # Boost score based on CVR impact + confidence
            impact_weight = matching_learning['cvr_impact'] * \
                           CONFIDENCE_MULTIPLIER[matching_learning['confidence']]
            rec.score *= (1 + impact_weight)

        weighted.append(rec)

    return sorted(weighted, key=lambda r: r.score, reverse=True)
```

#### **Generator Integration**

```python
# When Generator creates copy:
def enhance_copy_generation(page_context, learnings_context):

    # Retrieve patterns about effective copy for this sector
    copy_patterns = retrieve_notion_content(
        query=f"high-converting copy {page_context['sector']}",
        module='generation_context'
    )

    # Also pull from learnings
    sector_learnings = find_learnings(
        applied_to=['generator'],
        sector=page_context['sector'],
        tags__contains='copy'
    )

    # Inject into prompt for Generator
    context = {
        'sector_patterns': copy_patterns,
        'high_impact_patterns': sector_learnings,
        'confidence_guidance': {
            l['pattern_type']: l['confidence'] for l in sector_learnings
        }
    }

    return context
```

#### **Page Optimizer Integration**

```python
# When Page Optimizer A/B tests:
def track_test_results_for_learning(test_results):

    # Store test result
    store_test_result({
        'variant_a': test_results.variant_a,
        'variant_b': test_results.variant_b,
        'cvr_improvement': test_results.cvr_lift_percent,
        'statistical_significance': test_results.p_value,
        'pattern_type': extract_pattern_type(test_results),
        'sector': test_results.client.sector
    })

    # Trigger learning collection if significant
    if test_results.p_value < 0.05 and abs(test_results.cvr_lift_percent) > 1.0:
        queue_learning_generation()  # Learning engine picks this up
```

---

## MEMORY & CALIBRATION SYSTEM

### 1. Memory Table

```sql
CREATE TABLE ai_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR NOT NULL,  -- learned_pattern, correction, validation
    content JSONB NOT NULL,
    source_module VARCHAR,
    confidence FLOAT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX memory_type_idx (memory_type),
    INDEX is_active_idx (is_active),
    INDEX created_at_idx (created_at)
);
```

### 2. Calibration Loop

```python
def calibration_loop():
    """
    Continuous feedback loop that refines AI judgment over time.
    """

    corrections = fetch_recent_user_corrections()

    for correction in corrections:

        # Analyze the correction
        analysis = {
            'module': correction.module,
            'ai_was_wrong_about': correction.field,
            'context': correction.context_data,
            'user_override': correction.user_value,
            'impact': 'high' if correction.estimated_impact > 0.5 else 'low'
        }

        # Store as memory + learning
        store_memory({
            'type': 'correction',
            'data': analysis,
            'source_module': correction.module,
            'weight': IMPACT_TO_WEIGHT[analysis['impact']]
        })

        # If high-impact correction, update relevant learnings
        if analysis['impact'] == 'high':
            apply_correction_to_learnings(analysis)


def apply_correction_to_learnings(correction):
    """
    Use corrections to refine confidence scores.
    """

    # Find related learnings
    related = find_learnings_by_context(correction['context'])

    for learning in related:
        # Lower confidence if frequently corrected
        correction_rate = count_corrections(learning.id) / learning.validation_count

        if correction_rate > 0.2:  # >20% corrections
            adjust_confidence(
                learning.id,
                new_confidence=lower_confidence_level(learning.confidence),
                reason=f"Correction rate {correction_rate:.0%}"
            )
```

### 3. Notion Integration Example

**Scenario:** A learning insight is generated about "Checkout Friction in E-commerce"

**UX Flow:**

```
1. Learning Engine detects pattern
   ↓
2. Creates insight: "60% of e-commerce audits show checkout friction"
   ↓
3. Scores confidence: HIGH (n=25, p<0.001)
   ↓
4. Proposes push to Notion (in UI: "Preview" button)
   ↓
5. User reviews proposal in modal
   ↓
6. [User clicks "Push to Notion"]
   ↓
7. Creates page in "AI Insights" database with:
   - Insight title
   - Full description + examples
   - Confidence level (HIGH)
   - Sectors affected (E-commerce)
   - Applied to modules (Audit Engine)
   - Sample size (n=25)
   - Last validated date
   ↓
8. Learning stored with notion_page_id reference
   ↓
9. Next audit for e-commerce client: checklist boosted with this insight
```

---

## SYNCHRONIZER BUTTON UX FLOW

### UI Component

```
┌─────────────────────────────────────────┐
│  GrowthCRO Dashboard                    │
├─────────────────────────────────────────┤
│                                         │
│  [Synchroniser] [Status: Last sync ...] │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Sync Status                     │   │
│  ├─────────────────────────────────┤   │
│  │ Notion: 127 pages indexed       │   │
│  │ New learnings: 3 detected       │   │
│  │ Last sync: 2h ago               │   │
│  │ Next auto-sync: in 4h           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Pending Insights (Push to Notion)   │
│  ├─────────────────────────────────┤   │
│  │ ☐ Checkout friction pattern     │   │
│  │   [HIGH confidence] → Preview   │   │
│  │                                 │   │
│  │ ☐ Form abandonment solution     │   │
│  │   [MEDIUM] → Preview            │   │
│  │                                 │   │
│  │ ☐ Mobile nav UX improvement     │   │
│  │   [MEDIUM] → Preview            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Recent Learnings (Last 7 days)  │   │
│  ├─────────────────────────────────┤   │
│  │ ✓ CTA color testing impact      │   │
│  │   [HIGH] · n=18 · Sector: SaaS  │   │
│  │   [Edit] [Remove]               │   │
│  │                                 │   │
│  │ ✓ Long-form copy patterns       │   │
│  │   [MEDIUM] · n=12 · All         │   │
│  │   [Edit] [Remove]               │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### Sync Flow Sequence

```
[User clicks "Synchroniser"]
    ↓
[UI shows spinner: "Pulling from Notion..."]
    ↓
Notion API: Fetch all modified pages since last_sync
    ↓
Index + embed new content
    ↓
[UI updates: "Pulled 12 new pages, 127 total indexed"]
    ↓
[Learning Engine runs pattern detection]
    ↓
[UI updates: "Processing 3 new learnings..."]
    ↓
3 new insights generated + confidence scored
    ↓
[UI shows "New insights ready for review"]
    ↓
[User clicks preview on first insight]
    ↓
Modal shows: title, description, examples, confidence, sector
[Push to Notion] [Schedule Review] [Discard]
    ↓
[If Push: Create page in Notion, show success]
    ↓
[UI returns to dashboard, insights moved to "Recent Learnings"]
```

---

## SUMMARY: MODULE RESPONSIBILITIES

| Module | Receives from Learning Engine | Sends to Learning Engine |
|--------|-------------------------------|--------------------------|
| **Audit Engine** | Prioritized checklist items based on sector patterns | Finding frequency, severity, sector data |
| **Recommender** | Recommendation type weightings by CVR impact | Recommendation performance (CVR lift) |
| **Generator** | Copy patterns, structure inspiration, high-impact examples | Generated page metrics (CVR, engagement) |
| **Page Optimizer** | Testing insights (what to test, expected impact) | A/B test results, statistical significance |
| **Catchr Sync** | - | CVR baseline/variant data, implementation dates |

---

## DEPLOYMENT CHECKLIST

- [ ] pgvector enabled in Supabase
- [ ] Notion API key configured + scoped to GrowthCRO workspace
- [ ] OpenAI API key configured + billing enabled
- [ ] Cron job for 6-hourly auto-sync (0, 6, 12, 18 UTC)
- [ ] Tables created: `notion_content_raw`, `notion_embeddings`, `ai_learnings`, `ai_memory`
- [ ] UI component "Synchroniser" integrated in dashboard
- [ ] Notion database "AI Insights" created with proper schema
- [ ] Conflict resolution logic tested
- [ ] Learning engine production-tested on 10+ audits
- [ ] Monitoring: sync errors, embedding failures, learning confidence drift

---

**Version 1.0.0 · Production Ready**

