# Broadcast Bridge Sprint — Laverna Bot + Post-Match Hook

> Two small npc-wars tasks that unblock broadcast Sprint 2 (BC2.x in agentgrounds-web)
> and Phase 2 multi-persona broadcasts. Both are hub-local to npc-wars.
>
> **Type:** feature
> **Estimated Cx:** ~35
> **Tasks:** 2

---

## Phase 1

### T70.1 — Laverna persona → KS bot adapter | Cx: 25 | P0

**Description:** Wire the `laverna` paircoder persona (defined at `.claude/agents/laverna.md`) as an LLM-driven Kill Switch bot. New file `agentgrounds/wars/bots/laverna_llm.py` (or `bots/laverna_llm.py` if bots/ is the convention) implementing npc-wars' `decide(state)` interface used by `cmd_play.py`. Consumes `laverna.md` as the system prompt and calls Claude via the Anthropic SDK, with the current game state serialized as the user message. Defensive playstyle (higher defend ratio, trap placement, ranged preference) should emerge from the persona's paranoid-security framing. Graceful degradation: on LLM unavailability or timeout, falls back to a deterministic defensive heuristic so matches still complete. Per-decision token budget capped under 500 output tokens. Prompt caching enabled on the system prompt block to reduce cost. This is the first of the five paircoder personas to land as a bot; the rest follow in Phase 2.

**AC:**
- [ ] New bot file exists and registers via the normal bot discovery mechanism
- [ ] Bot implements `decide(state)` returning a valid action tuple
- [ ] System prompt loaded from `.claude/agents/laverna.md` (not duplicated inline)
- [ ] Uses Anthropic SDK (`anthropic` package); prompt caching enabled on the system prompt content block
- [ ] Per-decision budget capped at < 500 output tokens (max_tokens set)
- [ ] Fallback deterministic heuristic triggers on SDK error, timeout, or missing API key; match still completes
- [ ] Registered so `agentgrounds killswitch play --bot laverna` or equivalent works end-to-end
- [ ] Over 50 simulated matches vs. baseline bots, laverna's defend ratio > baseline average (statistical check in test)
- [ ] Tests cover: happy decision, fallback on LLM error, action shape validity, prompt caching block present, no API calls in unit tests (mocked SDK)
- [ ] `bpsai-pair arch check` clean on touched files
- [ ] Files each under 250 LOC, ruff clean

**Depends on:** none

---

### T70.2 — Post-match hook: write match JSON to broadcast inbox | Cx: 10 | P0

**Description:** Add an optional post-match hook to `cmd_play.py` (and `cmd_race.py` for Code Circuit) that writes the finalized match JSON to a configurable "broadcast inbox" directory. The broadcast Sprint 2 watcher daemon in agentgrounds-web will poll that directory and trigger episode generation. Controlled via env var `BROADCAST_INBOX_PATH`; when unset, the hook is a no-op (preserves existing behavior). When set, the hook runs after `write_match()` and writes a copy (not a move) to `${BROADCAST_INBOX_PATH}/{game}/{match_id}.json`. Idempotent (overwrite on collision). Silent failures are NOT acceptable — log a warning if the write fails but don't block the match from completing.

**AC:**
- [ ] New helper `engine/broadcast_inbox.py` (or similar) with single function `write_to_inbox(match_data, game)`
- [ ] Reads `BROADCAST_INBOX_PATH` env var; no-op if unset
- [ ] Writes to `{inbox}/{game}/{match_id}.json` (creates dirs as needed)
- [ ] Called from `cmd_play.py` after `write_match()` (Kill Switch path)
- [ ] Called from `cmd_race.py` after race write (Code Circuit path)
- [ ] Overwrites existing file on collision (idempotent)
- [ ] Logs warning on write failure; does NOT raise (match still completes)
- [ ] `game` field is "killswitch" or "circuit" (matches agw `/public/episodes/{game}/` convention)
- [ ] Tests cover: env unset (no-op), env set + write, missing dir (auto-create), write failure logged, idempotent rewrite
- [ ] `bpsai-pair arch check` clean
- [ ] File under 100 LOC, ruff clean

**Depends on:** none

---

## Delivery Summary

| Task | Title | Cx | P | Depends on |
|------|-------|----|---|------------|
| T70.1 | Laverna persona → KS bot adapter | 25 | P0 | — |
| T70.2 | Post-match hook to broadcast inbox | 10 | P0 | — |

**Total Cx:** 35
**Task count:** 2
**P0 / P1 / P2:** 2 / 0 / 0

---

## Priority Order

Both tasks are independent — full parallel OK.

1. T70.1 Laverna bot adapter (P0)
2. T70.2 Post-match hook (P0)

---

## Out of Scope

- Other personas (bellona, divona, nayru, vaivora) — Phase 2
- Broadcast watcher daemon in agw — that's BC2.3 in the agentgrounds-web broadcast Sprint 2 backlog
- Season state tracking — BC2.5 in agw
- Any changes to the match engine itself
- Changes to laverna.md persona content

---

## References

- Broadcast Sprint 2 (agw): `/home/kmasty/projects/agentgrounds-web-broadcast/plans/backlogs/backlog-broadcast-sprint-02.md`
- Broadcast roadmap: on branch `engage/backlog-broadcast-sprint-01` (not yet merged to main) at `docs/broadcast-roadmap.md`
- Persona: `.claude/agents/laverna.md`
- Anthropic SDK prompt caching: https://docs.anthropic.com/claude/docs/prompt-caching
