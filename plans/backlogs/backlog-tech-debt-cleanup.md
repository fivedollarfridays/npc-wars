# Tech Debt Cleanup Sprint

> Four targeted tech debt items surfaced during the S58-T68 review + CI cleanup.
> All non-behavioral refactors or small fixes. Worth doing before the codebase grows.
>
> **Type:** chore
> **Estimated Cx:** ~60
> **Tasks:** 4

---

## Phase 1

### T71.1 — Extract viewer.html inline CSS | Cx: 15 | P0

**Description:** `viewer/viewer.html` is 1002 lines, 812 of which are inline CSS. This exceeds the 400-line source limit. The JS is already properly split into `viewer/js/*.js` modules; the CSS should follow the same pattern. Move the entire `<style>` block content to a new `viewer/viewer.css`, replace the inline block with `<link rel="stylesheet" href="viewer.css">`. No behavior changes — pure extraction. Verify all existing viewer tests still pass and the page renders identically.

**AC:**
- [ ] `viewer/viewer.css` exists containing all CSS that was previously inline
- [ ] `viewer/viewer.html` under 400 lines after extraction
- [ ] `<link rel="stylesheet" href="viewer.css">` replaces the inline `<style>` block
- [ ] All existing viewer tests pass (test_viewer_*, test_viewer_unified, test_viewer_code_overlay, test_viewer_commentary, test_viewer_circuit)
- [ ] Visual diff snapshot or manual smoke: viewer loads a sample match JSON and renders without CSS regressions
- [ ] `bpsai-pair arch check viewer/viewer.html` passes
- [ ] No behavioral change — pure refactor

**Depends on:** none

---

### T71.2 — Split discord_bot/formatters.py at TV boundary | Cx: 15 | P0

**Description:** `discord_bot/formatters.py` is 334 lines (above 200-line warning threshold). Natural split at line 182 where TV-specific formatters begin. Move match/leaderboard formatters to stay in `formatters.py`; move TV/episode/highlight formatters to new `discord_bot/tv_formatters.py`. Update all importers. No behavior change — pure split. Existing tests (`test_tv_formatters.py` in particular) should continue to pass without modification beyond import updates.

**AC:**
- [ ] `discord_bot/formatters.py` contains only match/leaderboard formatters (pre-line-182 content), under 200 lines
- [ ] `discord_bot/tv_formatters.py` contains TV/episode/highlight formatters (post-line-182 content), under 200 lines
- [ ] All importers updated to import from the correct module
- [ ] No import of `formatters` re-exports from `tv_formatters` (split is clean)
- [ ] All discord_bot tests pass (test_formatters, test_tv_formatters, test_tv_posting, test_discord_*)
- [ ] `bpsai-pair arch check` passes on both files
- [ ] No behavioral change — pure refactor

**Depends on:** none

---

### T71.3 — Extract engine/rounds.py helpers to reduce file size | Cx: 20 | P0

**Description:** `engine/rounds.py` is exactly 350 lines, at the test's `<= 350` boundary. The next line-adding change breaks CI. Extract natural helper groups into a companion module (e.g., `engine/rounds_helpers.py` or split by concern into `engine/action_resolution.py` + `engine/override_events.py`). Target: `rounds.py` under 300 lines after extraction, helpers under 200 each. Preserve `resolve_decisions()` as the public entry point; all callers import from `engine.rounds` as before. Include a size-guard test update to reflect the new limit.

**AC:**
- [ ] `engine/rounds.py` under 300 lines after extraction
- [ ] One or more helper modules created, each under 200 lines
- [ ] Public entry point `resolve_decisions` still importable from `engine.rounds`
- [ ] `tests/test_s29_integration.py::TestArchCompliance::test_rounds_py_arch_compliant` passes with updated assertion (`<= 300` or similar)
- [ ] All existing engine and rounds tests pass
- [ ] `bpsai-pair arch check engine/rounds.py` passes
- [ ] `bpsai-pair arch check <new-helper-files>` passes
- [ ] No behavioral change — pure refactor

**Depends on:** none

---

### T71.4 — Fix server/lobby.py fire-and-forget thread | Cx: 10 | P1

**Description:** `server/lobby.py::_run_match_inline` spawns a thread with no join, no result tracking, errors only logged. The S57 change that added this path meant well (inline execution in in-memory mode so local dev works without Redis) but it swallows errors silently, and it's the same change that broke 10+ tests this sprint. Two options: (a) add a `LOBBY_INLINE_ON_NO_REDIS` config flag (default `False`) so production and tests use the queue path, and local dev opts in; or (b) run synchronously in the fallback path — callers wait but get structured error feedback. Pick (a) — it's less disruptive, matches the principle of explicit opt-in, and tests stop needing the `NotInMemoryQueue` helper in `tests/conftest.py`.

**AC:**
- [ ] New env var `LOBBY_INLINE_ON_NO_REDIS` read in `server/lobby.py` (default `False`)
- [ ] Inline execution only happens when the flag is `True` AND `is_in_memory_mode()` is `True`
- [ ] When flag is `False` (default), lobby always uses `enqueue_match()` regardless of backend
- [ ] `tests/conftest.py::NotInMemoryQueue` helper removed (no longer needed)
- [ ] `tests/test_lobby.py`, `test_extended_mode.py`, `test_server_integration.py`, `test_s52_lobby_rival.py` updated to not use `NotInMemoryQueue` (InMemoryQueue works directly now since flag defaults False)
- [ ] `_run_match_inline` kept but documented as opt-in; still logs errors structurally
- [ ] Documentation updated: README or CONTRIBUTING notes the env var for local dev convenience
- [ ] `bpsai-pair arch check` clean
- [ ] All server/lobby tests pass

**Depends on:** none

---

## Delivery Summary

| Task | Title | Cx | P | Depends on |
|------|-------|----|---|------------|
| T71.1 | Extract viewer.html inline CSS | 15 | P0 | — |
| T71.2 | Split discord_bot/formatters.py at TV boundary | 15 | P0 | — |
| T71.3 | Extract engine/rounds.py helpers | 20 | P0 | — |
| T71.4 | Fix server/lobby.py fire-and-forget thread | 10 | P1 | — |

**Total Cx:** 60
**Task count:** 4
**P0 / P1 / P2:** 3 / 1 / 0

---

## Priority Order

All independent — full parallel OK.

1. T71.1 viewer.html CSS (P0)
2. T71.2 formatters.py split (P0)
3. T71.3 rounds.py extraction (P0)
4. T71.4 lobby inline flag (P1)

**Cut list if budget overflows:** T71.4 (P1). Others are size-threshold blockers that will bite within a few commits.

---

## Out of Scope

- Behavioral changes to any of the refactored code
- New features
- Addressing "Consider" items from the S58-T68 review (rate limit docs, circuit sort, commentary re-export, etc.) — those are low priority and not blocking
- viewer.html JS reorganization (JS is already split into viewer/js/*.js)
- discord_bot/formatters.py API surface changes (new arg signatures, new fields) — pure split only

---

## References

- S58-T68 review findings (docs/broadcast-sprint-01-brief.md references it) — the "Should Fix" items this sprint addresses
- Arch constraints: `.claude/rules/architecture.md`
- CI that exposed rounds.py boundary: PR #56
