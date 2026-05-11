# Follow-up #13 — Resolve persona_narrator prompt_mode architecture (V26.AF compliance)

**Created from**: #8 split decision (2026-05-10)
**Status**: spec drafted, not yet posted to GitHub
**Depends on**: #8 (closes the assert quarantine)
**Related immutable**: CLAUDE.md "Anti-pattern #1" — prompt persona_narrator >8K chars → -28pts régression V26.AA

## Problem statement

`build_persona_narrator_prompt()` today produces:
- `prompt_mode='lite'` ≈ 5,800–7,000 chars (under 8K — OK)
- `prompt_mode='full'` ≈ 13,000+ chars (violates V26.AF immutable — RED)

Issue #8 quarantines 'full' via `assert len(system_prompt) <= 8192`. The path is inert at runtime. This issue specs the **proper** resolution.

## Why 'full' was created (preserve intent)

Best inference from the code (L1131–1140 of original `mode_1_persona_narrator.py`):
- 'full' mode passes higher `max_chars` to `_format_aura_tokens_block` (3,500 vs 1,400)
- 'full' includes additional context blocks (golden_techniques full vs LITE, layout_archetype full vs LITE, v143 verbatims, recos)
- The intent: give Sonnet more grounding for premium output (V26.AA "stratosphérique" goal)

The empirical regression (-28pts when 'full' is used) suggests Sonnet does NOT benefit from 13K+ char system_prompts in practice — the model gets noisier, drifts from the persona, and produces lower-quality copy. The "more context = better" intuition fails at this size.

## Strategic solution

**Two architectural moves**, applied together:

### 1. Anthropic prompt caching (`cache_control`)
Static blocks (persona template, doctrine, anti-AI-slop rules, hard constraints) are **identical across every GSG run**. They should live in cached prompt blocks.

```python
# pseudo
system = [
    {"type": "text", "text": PERSONA_TEMPLATE,      "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": DOCTRINE_BLOCK,        "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": ANTI_AI_SLOP_DOCTRINE, "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": dynamic_brand_block(client)},  # not cached
]
```

Result: cached portion costs 1/10th input tokens after first call. Static doctrine can be 10K+ chars without cost penalty.

### 2. Promote context to user_turns (multi-turn instead of mega-system-prompt)

Instead of cramming brand DNA + AURA + golden refs + archetypes + v143 + recos in `system_prompt`, structure as a **dialogue**:

```
user: "Here is the brand DNA for Weglot." [+ JSON]
assistant: "Understood. Voice: matter-of-fact technical, register: B2B SaaS senior."
user: "Here are the golden design references for SaaS listicle pageType." [+ refs]
assistant: "Noted. Patterns: numbered H1, dense ToC, anchor-driven scan."
user: "Here is the audit recos backlog for this client." [+ recos]
assistant: "Understood. Top 3 priorities: <synthesis>"
user: "Generate the LP copy now, respecting the doctrine."
assistant: <generates LP>
```

Why this works:
- Each user turn is digestible (≤2K chars)
- The assistant "checkpoints" understanding between turns (free reasoning)
- Sonnet's attention works *better* on dialogue history than on long system_prompts (well-documented behavior)
- Total context fed = LARGER than 'full' mode ever was, but spread, with caching, with explicit checkpointing
- We escape the lite/full dichotomy entirely

## Acceptance criteria (draft)

- [ ] `build_persona_narrator_prompt()` returns `(system_messages, user_turns_seq)` instead of monolithic `(system_prompt, user_message)`.
- [ ] `system_messages` is a list of `{type, text, cache_control}` blocks. `len(text)` per block ≤ 4K. Total static blocks marked `cache_control: ephemeral`.
- [ ] `user_turns_seq` is a list of `(role, content)` tuples representing the dialogue. Each ≤ 2K.
- [ ] No single text block exceeds 8K (defensive — V26.AF stays enforced).
- [ ] `mode_1/api_call.py` passes `system=system_messages, messages=user_turns_seq` to Sonnet — uses Anthropic SDK's prompt caching natively.
- [ ] `prompt_mode='full'` path **deleted** (the assert quarantine becomes obsolete; remove it).
- [ ] Multi-judge ≥ baseline on 3 canonical clients (weglot, japhy + 1 random) post-refactor.
- [ ] Token cost reduction documented in commit (cache hit rate from second run onward).

## Estimated effort

- Size: L (12-16h)
- Critical path: design (3h) → refactor `prompt_assembly.py` (4h) → adapt `api_call.py` for SDK caching (2h) → smoke test on 3 clients (3h) → multi-judge regression check (4h)
- Risk: dialogue-mode quality regression vs current 'lite'. Mitigation: A/B test on weglot listicle BEFORE landing.

## Related work

- Anthropic prompt caching docs: https://docs.anthropic.com/claude/docs/prompt-caching
- The `claude-api` skill (`.claude/skills/anthropic-skills/claude-api/`) has examples — use it.
- Existing multi-turn pattern in `enrich_v143_public.py` (archived in #6) had a primitive dialogue structure — review for inspiration before deleting.

## Decision log

- 2026-05-10 — Issue #8 quarantines 'full' via runtime assert (Option D). This issue (#13) takes ownership of the architectural fix.
- Posting to GitHub: held until #8 lands and Mathis says "post #13".
