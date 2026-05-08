# AI Memory & Calibration System - Implementation Template
## GrowthCRO Notion Sync & Learning Engine

**Document Version:** 1.0.0 (Template)
**Status:** Ready for Implementation
**Last Updated:** 2026-04-05

---

## OVERVIEW

This document serves as an **empty template** for implementing the memory and calibration system. It defines:

1. Memory table schema and operations
2. Calibration data structures
3. Correction feedback loops
4. Memory decay and refresh procedures
5. Integration points with learning engine

Use this as a reference during implementation phase.

---

## SECTION 1: MEMORY TABLE SCHEMA

### Core Tables

**Table: `ai_memory`**

```sql
-- [IMPLEMENTATION]: Create this table in Supabase
-- Purpose: Store learned patterns, corrections, validations

-- Column definitions needed:
-- - id (UUID): Primary key
-- - memory_type (VARCHAR): correction | learned_pattern | validation | refutation
-- - content (JSONB): Flexible data storage
-- - source_module (VARCHAR): Which module created this
-- - confidence (FLOAT 0-1): Current confidence level
-- - created_at (TIMESTAMP): When memory was created
-- - last_accessed (TIMESTAMP): For decay calculations
-- - expires_at (TIMESTAMP NULLABLE): Optional expiry
-- - is_active (BOOLEAN): Soft delete flag
-- - validation_count (INT): How many times validated
-- - refutation_count (INT): How many times contradicted
-- - weight (FLOAT): Importance multiplier for learning

-- Indexes needed:
-- - memory_type for filtering
-- - is_active for active query
-- - created_at for time-based queries
-- - source_module for module-specific queries
```

**Table: `ai_memory_history`**

```sql
-- [IMPLEMENTATION]: Create table to track memory evolution
-- Purpose: Audit trail of memory updates and confidence changes

-- Column definitions needed:
-- - id (UUID): Primary key
-- - memory_id (UUID): Reference to ai_memory
-- - old_confidence (FLOAT NULLABLE): Previous confidence
-- - new_confidence (FLOAT): Updated confidence
-- - change_reason (VARCHAR): Why confidence changed
-- - updated_by (VARCHAR): User or system that made change
-- - updated_at (TIMESTAMP): When change occurred
-- - metadata (JSONB): Additional context

-- Indexes:
-- - memory_id for lookups
-- - updated_at for timeline queries
```

**Table: `calibration_feedback`**

```sql
-- [IMPLEMENTATION]: Create table for correction tracking
-- Purpose: Store user overrides for AI calibration

-- Column definitions needed:
-- - id (UUID): Primary key
-- - learning_id (UUID NULLABLE): Reference to ai_learnings
-- - module (VARCHAR): Which module was corrected
-- - ai_suggestion (TEXT): What AI recommended
-- - user_override (TEXT): What user chose instead
-- - reason (TEXT): Why user disagreed
-- - context (JSONB): Full context of the decision
-- - impact (VARCHAR): high | medium | low
-- - corrected_at (TIMESTAMP): When correction occurred
-- - corrected_by (VARCHAR): User ID
-- - was_correct (BOOLEAN NULLABLE): Later validation

-- Indexes:
-- - learning_id for linking to insights
-- - module for tracking per-module calibration
-- - corrected_at for time-based analysis
```

---

## SECTION 2: MEMORY OPERATIONS

### Memory Create/Update Functions

```python
# [IMPLEMENTATION TEMPLATE]

def store_memory(memory_entry: dict) -> dict:
    """
    Store a memory entry.

    Parameters:
    - memory_entry: dict with keys:
      - type (required): 'correction' | 'learned_pattern' | 'validation'
      - content (required): JSONB-serializable data
      - source_module (required): 'audit' | 'recommender' | 'generator'
      - confidence (optional): 0-1 float
      - expires_at (optional): ISO timestamp string

    Returns:
    - dict with 'success', 'memory_id', 'stored_at'

    [TODO] Implement using psycopg2:
    - Connect to database
    - Validate required fields
    - Insert into ai_memory table
    - Return created memory_id and timestamp
    """
    pass


def update_memory_confidence(memory_id: str, new_confidence: float, reason: str) -> dict:
    """
    Update confidence level of memory.
    Also logs history for audit trail.

    Parameters:
    - memory_id: UUID of memory to update
    - new_confidence: New confidence value (0-1)
    - reason: Human-readable reason for change

    Returns:
    - dict with 'success', 'old_confidence', 'new_confidence'

    [TODO] Implement:
    - Fetch old confidence from ai_memory
    - Update to new_confidence
    - Create entry in ai_memory_history
    - Log the change with reason
    """
    pass


def activate_memory(memory_id: str) -> dict:
    """
    Reactivate a memory (soft-undelete).

    [TODO] Implement:
    - Set is_active = TRUE in ai_memory
    - Update last_accessed timestamp
    - Return success status
    """
    pass


def deactivate_memory(memory_id: str) -> dict:
    """
    Soft-delete memory (for later analysis).

    [TODO] Implement:
    - Set is_active = FALSE in ai_memory
    - Preserve all data for audit
    - Return success status
    """
    pass
```

---

## SECTION 3: CALIBRATION FEEDBACK LOOP

### Collecting Corrections

```python
# [IMPLEMENTATION TEMPLATE]

def record_user_correction(correction_data: dict) -> dict:
    """
    Record when user overrides AI suggestion.

    Parameters:
    - correction_data: dict with:
      - module (required): 'audit' | 'recommender' | 'generator'
      - ai_suggestion: What AI recommended
      - user_override: What user chose
      - reason: User's explanation
      - context: Full context object
      - impact: 'high' | 'medium' | 'low'
      - corrected_by: User ID

    Returns:
    - dict with 'success', 'correction_id'

    [TODO] Implement:
    - Validate correction data
    - Insert into calibration_feedback table
    - Assess impact level automatically
    - Queue learning update if high impact
    - Trigger immediate calibration if needed
    """
    pass


def assess_correction_impact(correction: dict) -> str:
    """
    Calculate how much this correction matters.

    Returns: 'high' | 'medium' | 'low'

    [TODO] Implement impact calculation logic:
    - For recommendations: Was recommendation fundamentally wrong?
    - For generator: Did it significantly change output?
    - For audit: Did it change finding severity/priority?
    - Consider module and field affected
    """
    pass


def find_related_learnings(correction: dict) -> list:
    """
    Find learnings that this correction relates to.

    Returns: List of learning_ids that should be reviewed

    [TODO] Implement:
    - Match correction context to learning contexts
    - Find by module, sector, pattern_type
    - Return learnings that might be invalidated
    """
    pass
```

### Applying Corrections to Learnings

```python
# [IMPLEMENTATION TEMPLATE]

def apply_correction_to_learnings(correction_memory: dict) -> dict:
    """
    When high-impact correction occurs, update related learnings.

    Parameters:
    - correction_memory: Memory entry from calibration_feedback

    Returns:
    - dict with list of updated learning_ids

    [TODO] Implement:
    1. Find all related learnings
    2. For each learning:
       - Calculate new correction_rate = corrections / validation_count
       - If correction_rate > threshold (e.g., 30%), downgrade confidence
       - Log the downgrade with reason
       - Store in ai_memory_history
    3. Return summary of changes
    """
    pass


def downgrade_confidence_level(current_level: str) -> str:
    """
    Move confidence one level down.
    high → medium → low

    [TODO] Implement:
    - Simple mapping logic
    - Ensure we don't go below 'low'
    - Return new level
    """
    pass
```

---

## SECTION 4: MEMORY DECAY & REFRESH

### Memory Lifecycle Management

```python
# [IMPLEMENTATION TEMPLATE]

def refresh_memory_timestamps(memory_ids: list) -> dict:
    """
    Update last_accessed timestamp for memories.
    Used when memory is consulted during operations.

    [TODO] Implement:
    - Batch update last_accessed for given IDs
    - Return count of updated records
    """
    pass


def check_memory_expiry() -> dict:
    """
    Find expired memories and deactivate them.
    Run daily (e.g., via cron job).

    Returns:
    - dict with 'expired_count', 'still_active_count'

    [TODO] Implement:
    - Find all memories with expires_at < NOW()
    - Deactivate them
    - Log for audit
    - Return counts
    """
    pass


def apply_memory_decay(memory_id: str) -> dict:
    """
    Apply confidence decay for old memories.
    Confidence should gradually decrease if not revalidated.

    Parameters:
    - memory_id: UUID of memory to decay

    Returns:
    - dict with 'old_confidence', 'new_confidence', 'days_since_validation'

    [TODO] Implement decay formula:
    - Calculate days since last_accessed
    - Apply exponential decay: new_conf = old_conf * (0.98 ^ days)
    - Only apply if last_accessed > 30 days ago
    - Update confidence in ai_memory
    - Log in ai_memory_history
    """
    pass


def periodic_memory_maintenance():
    """
    Run daily maintenance on memory system.

    [TODO] Implement as scheduled task:
    - Run at off-peak hours (e.g., 02:00 UTC)
    - Call check_memory_expiry()
    - Call apply_memory_decay() for old memories
    - Clean up very stale memories (>1 year, low confidence)
    - Log maintenance summary
    """
    pass
```

---

## SECTION 5: VALIDATION & CONTRADICTION TRACKING

### Memory Validation

```python
# [IMPLEMENTATION TEMPLATE]

def validate_memory(memory_id: str, outcome: str = 'confirmed') -> dict:
    """
    Mark memory as validated or contradicted.

    Parameters:
    - memory_id: UUID of memory to validate
    - outcome: 'confirmed' | 'refuted' | 'partially_confirmed'

    Returns:
    - dict with 'success', 'validation_count', 'refutation_count'

    [TODO] Implement:
    - Update validation_count or refutation_count in ai_memory
    - If refuted: lower confidence significantly
    - If confirmed: boost confidence slightly
    - Store in ai_memory_history as record
    - Recalculate overall confidence
    """
    pass


def get_memory_validation_history(memory_id: str) -> dict:
    """
    Get full validation history of a memory.

    Returns:
    - dict with:
      - validation_count
      - refutation_count
      - validation_rate (0-1)
      - history (list of validations with dates)

    [TODO] Implement:
    - Query ai_memory_history for this memory
    - Count confirmations vs refutations
    - Calculate validation_rate
    - Return formatted history
    """
    pass
```

---

## SECTION 6: MEMORY RECALL & USAGE

### Retrieving Memory for Decision Making

```python
# [IMPLEMENTATION TEMPLATE]

def get_active_memories(filters: dict) -> list:
    """
    Retrieve memories matching filters.

    Parameters:
    - filters: dict with optional keys:
      - memory_type: 'correction' | 'learned_pattern' etc
      - source_module: 'audit' | 'recommender' | 'generator'
      - min_confidence: 0-1 float threshold
      - sector: for sector-specific memories

    Returns:
    - List of memory dicts with full content

    [TODO] Implement:
    - Query ai_memory with WHERE is_active = TRUE
    - Apply all filters
    - Sort by confidence DESC, last_accessed DESC
    - Update last_accessed timestamp
    - Return results
    """
    pass


def get_memory_context_for_module(module: str, context_data: dict) -> dict:
    """
    Get all relevant memories for a module's decision-making.

    Parameters:
    - module: 'audit' | 'recommender' | 'generator'
    - context_data: dict with sector, page_type, etc

    Returns:
    - dict organized by memory_type with all relevant memories

    [TODO] Implement:
    - Fetch memories for this module
    - Filter by context (sector, type, etc)
    - Organize by memory_type
    - Sort by confidence and relevance
    - Return structured dict for prompt injection
    """
    pass


def rank_memories_by_relevance(memories: list, context: dict) -> list:
    """
    Rank memories for relevance to specific decision.

    [TODO] Implement:
    - Calculate relevance score based on:
      - Context match (sector, page_type, etc)
      - Confidence level
      - Recent validations
    - Sort by relevance descending
    - Return ranked list
    """
    pass
```

---

## SECTION 7: INTEGRATION WITH LEARNING ENGINE

### Learning Engine ↔ Memory Sync

```python
# [IMPLEMENTATION TEMPLATE]

def sync_learnings_to_memory() -> dict:
    """
    Periodically sync validated learnings into memory system.
    Converts learnings into memories for faster access.

    Run: Daily at 03:00 UTC

    [TODO] Implement:
    - Find learnings with confidence >= 'high'
    - For each learning:
      - Create memory_entry with type='learned_pattern'
      - Set confidence from learning
      - Link to learning_id
      - Store in ai_memory
    - Return count of synced learnings
    """
    pass


def reflect_memory_changes_in_learnings() -> dict:
    """
    Push memory updates back to learning system.
    When confidence of memory changes, update related learnings.

    Run: After each memory update

    [TODO] Implement:
    - Find memory's linked learning_id
    - Update learning's confidence if memory confidence changed
    - Log linkage in ai_memory_history
    - Return updated learning count
    """
    pass
```

---

## SECTION 8: MONITORING & OBSERVABILITY

### Memory System Metrics

```python
# [IMPLEMENTATION TEMPLATE]

def get_memory_system_health() -> dict:
    """
    Get overall health metrics of memory system.

    Returns dict with:
    - total_memories
    - active_memories
    - average_confidence
    - validation_rate (confirmations / total validations)
    - refutation_rate
    - memories_expiring_soon (next 7 days)
    - correction_frequency (corrections per day)

    [TODO] Implement:
    - Query ai_memory for counts and stats
    - Calculate rates from ai_memory_history
    - Find expiring memories
    - Calculate correction frequency
    - Return comprehensive health dict
    """
    pass


def log_memory_operation(operation: str, details: dict) -> None:
    """
    Log all memory operations for audit trail.

    [TODO] Implement:
    - Create log entry with:
      - operation (create, update, delete, validate)
      - timestamp
      - details (what changed)
      - user (who triggered if applicable)
    - Write to logs / monitoring system
    """
    pass
```

---

## SECTION 9: SAMPLE IMPLEMENTATION FLOW

### Complete Correction → Learning Update Flow

```
[SCENARIO: User corrects AI recommendation]

1. User override captured in UI
   → record_user_correction(correction_data)

2. Correction stored in calibration_feedback table
   → Assess impact level

3. If high-impact:
   → find_related_learnings(correction)
   → For each learning:
      → apply_correction_to_learnings()
      → Update confidence in ai_learnings
      → Create memory_history entry

4. Create memory entry:
   → store_memory({
      type: 'correction',
      content: correction_data,
      source_module: 'recommender',
      confidence: impact_level
   })

5. Next module usage:
   → get_memory_context_for_module('recommender', context)
   → Retrieve memory
   → Use in decision-making
   → update last_accessed timestamp

6. If correction later validated:
   → validate_memory(memory_id, 'confirmed')
   → Boost confidence slightly
   → Log in ai_memory_history
```

---

## IMPLEMENTATION PRIORITIES

**Phase 1 (Must Have):**
- [ ] ai_memory table creation
- [ ] store_memory() basic implementation
- [ ] record_user_correction() basic implementation
- [ ] get_active_memories() for retrieval

**Phase 2 (Should Have):**
- [ ] ai_memory_history for audit trail
- [ ] update_memory_confidence() with history tracking
- [ ] apply_correction_to_learnings() integration
- [ ] Memory decay functions

**Phase 3 (Nice to Have):**
- [ ] Advanced validation tracking
- [ ] Memory relevance ranking
- [ ] Comprehensive monitoring dashboard
- [ ] Automated memory maintenance routines

---

## TESTING STRATEGY

```
Unit Tests:
- Test each memory operation function individually
- Test data validation
- Test SQL queries

Integration Tests:
- Test correction → learning update flow
- Test memory decay calculations
- Test module recall integration

Performance Tests:
- Test memory retrieval speed (should be <50ms)
- Test batch operations efficiency
- Test database query performance
```

---

**End of Memory Implementation Template**

Use this document as a checklist and reference guide during development.

