# Notion Sync & AI Learning Engine Skill
## GrowthCRO Knowledge Management System

**Version:** 1.0.0  
**Status:** Production Ready  
**Created:** 2026-04-05

---

## Overview

Complete production-quality skill for the **Notion Sync & AI Learning Engine** — the intelligent knowledge management and continuous improvement system for GrowthCRO.

This skill enables:
- Bidirectional synchronization with Growth Society's Notion workspace
- Semantic indexing of all Notion content via pgvector
- Continuous pattern detection from audits, recommendations, tests
- Automatic insight generation and confidence scoring
- Memory + calibration system for improvement loops
- Integration with all GrowthCRO modules (Audit, Recommender, Generator, Page Optimizer)

---

## Files

### Core Documentation

1. **SKILL.md** (1,329 lines)
   - Complete overview of the system
   - Architecture diagrams
   - Sync protocol summary
   - Learning engine pipeline
   - Module integration points
   - UX flows (Synchroniser button)
   - Deployment checklist

2. **references/sync_protocol.md** (1,182 lines)
   - Complete Notion API reference
   - Pull protocol (Notion → GrowthCRO)
   - Push protocol (GrowthCRO → Notion)
   - Authentication setup
   - Data models and chunking strategy
   - Error handling and retry logic
   - Webhook event processing
   - Rate limiting optimization
   - Monitoring and alerting

3. **references/learning_engine.md** (1,234 lines)
   - Learning pipeline architecture
   - Data collection flows (audit, recommender, generator, user corrections)
   - Pattern detection methods (frequency, correlation, time series, outliers)
   - Insight generation (from patterns to human-readable insights)
   - Module integration points (how each module uses learnings)
   - Confidence scoring deep dive (multi-factor algorithm)
   - Memory and calibration system
   - Learning lifecycle management
   - Operational procedures

4. **references/memory.md** (658 lines)
   - Empty implementation template for memory system
   - Memory table schemas
   - Calibration feedback loop structure
   - Memory decay and refresh procedures
   - Validation and contradiction tracking
   - Integration points with learning engine
   - Monitoring and observability
   - Implementation priorities and testing strategy

---

## Key Concepts

### Sync Protocol

**Pull (Notion → GrowthCRO):**
- Manual trigger: "Synchroniser" button click
- Automatic: Every 6 hours (0, 6, 12, 18 UTC)
- Delta sync: Only pull modified pages since last sync
- Chunking: 512 tokens with 50-token overlap
- Embeddings: OpenAI text-embedding-3-small (1536 dims) stored in pgvector

**Push (GrowthCRO → Notion):**
- Only high-confidence learnings (HIGH or validated MEDIUM)
- Create pages in "AI Insights" database
- Link back via notion_page_id reference
- Update as learning confidence evolves

### Learning Engine

**Data Sources:**
1. Audit patterns (finding frequency by sector)
2. Recommendation performance (CVR lift validation)
3. Generation quality (which copy/structure patterns won)
4. User corrections (calibration signals)

**Pattern Detection:**
- Frequency analysis (χ² tests for statistical significance)
- Correlation detection (Pearson r)
- Time series trends (linear regression on weekly data)
- Outlier identification (IQR method)

**Confidence Scoring:**
- Multi-factor algorithm: sample size (0.25) + significance (0.20) + consistency (0.15) + effect size (0.15) + recency (0.10) + validation rate (0.10) + implementation baseline (0.05)
- Categorical levels: high (0.85+), medium (0.65-0.84), low (<0.65)

### Module Integration

| Module | Receives | Sends |
|--------|----------|-------|
| Audit Engine | Prioritized checklist items (sector patterns) | Finding frequency, severity, sector |
| Recommender | Recommendation type weights (CVR impact) | Performance data (CVR lift) |
| Generator | Copy patterns, structure inspiration | Page metrics (CVR, engagement) |
| Page Optimizer | Testing insights (what to test) | A/B test results |

---

## Database Schema (Quick Reference)

```sql
-- Content Storage
notion_content_raw        -- Raw Notion pages + blocks
notion_embeddings         -- pgvector embeddings (1536 dims)

-- Learning System
ai_learnings              -- Generated insights with confidence
ai_learnings_history      -- Confidence score evolution

-- Memory System
ai_memory                 -- Stored memories (corrections, patterns)
ai_memory_history         -- Memory updates audit trail
calibration_feedback      -- User correction tracking
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Setup Notion API authentication
- [ ] Create database tables (notion_content_raw, embeddings, learnings)
- [ ] Implement pull protocol (fetch, chunk, embed)
- [ ] Setup pgvector in Supabase

### Phase 2: Learning (Week 3-4)
- [ ] Implement pattern detection algorithms
- [ ] Build insight generation pipeline
- [ ] Create confidence scoring system
- [ ] Integrate with Audit Engine

### Phase 3: Integration (Week 5-6)
- [ ] Integrate with Recommender module
- [ ] Integrate with Generator module
- [ ] Implement push protocol (Notion creation)
- [ ] Build "Synchroniser" UI component

### Phase 4: Memory & Calibration (Week 7-8)
- [ ] Implement memory table system
- [ ] Build correction feedback loop
- [ ] Add memory decay functions
- [ ] Setup periodic maintenance tasks

### Phase 5: Polish & Deploy (Week 9)
- [ ] Monitoring and alerting setup
- [ ] Performance optimization
- [ ] Load testing (handle 100+ audits/day)
- [ ] Production deployment

---

## Configuration

### Environment Variables Required

```bash
# Notion
NOTION_API_KEY=secret_xxx...
NOTION_API_VERSION=2024-02-15
NOTION_WORKSPACE_ID=abc123...
NOTION_AI_INSIGHTS_DB_ID=db_insights...
NOTION_SYNC_LOG_DB_ID=db_logs...

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Database
DATABASE_URL=postgresql://user:pass@host/growthcro
SUPABASE_PROJECT_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx

# Application
GROWTHCRO_API_ENDPOINT=https://api.growthcro.local
WEBHOOK_SECRET=xyz123...
```

### Notion Database Schema

**AI Insights Database Properties:**
- Insight (Title)
- Description (Rich Text)
- Confidence (Select: low, medium, high)
- Applied To (Multi-select: audit_engine, recommender, generator)
- Validation Count (Number)
- CVR Impact (Number, optional)
- Tags (Multi-select: sector-based)
- Created (Created Time, auto)
- Last Validated (Date, manual)

---

## Monitoring Checklist

- [ ] Sync success rate > 99%
- [ ] Sync duration < 5 minutes (full run)
- [ ] Embedding errors = 0
- [ ] Learning generation runs 4x daily
- [ ] Confidence scores distributed: high 20%, medium 50%, low 30%
- [ ] Contradiction rate < 10%
- [ ] Memory system response time < 50ms

---

## Troubleshooting

**Notion API 429 (Rate Limit):**
- Implemented exponential backoff (2^attempt seconds)
- Circuit breaker closes after 5 failures

**Embedding Generation Failures:**
- Validate text is < 8191 tokens
- Check OpenAI API quota
- Retry with exponential backoff

**Memory System Performance:**
- Create indexes on: memory_type, is_active, created_at
- Run periodic maintenance (daily, off-peak)
- Archive memories > 1 year old

---

## Support & Documentation

- **SKILL.md**: Start here for overview and architecture
- **sync_protocol.md**: Reference for Notion API specifics
- **learning_engine.md**: Deep dive into pattern detection and insights
- **memory.md**: Implementation guide for calibration system

---

**Production Ready — Version 1.0.0**

