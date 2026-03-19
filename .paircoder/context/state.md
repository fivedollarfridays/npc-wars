# Current State

> Last updated: 2026-03-19 T30.7 done

## Active Plans

**Plan:** Sprint 29: Combat Overhaul pt.2 — Dodge, Modifiers, Initiative
- **Sprint:** S29 | **Type:** feature | **Status:** Done (7/7 tasks)
- **Part of:** Phase 1 — Agent Wars v2 Foundation (S27-S31, 35 tasks, 810 Cx)

### S29 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T29.1 | Extract combat helpers from rounds.py | 20 | — | done |
| T29.2 | Dodge system (SPEED-based) | 25 | T29.1 | done |
| T29.3 | Situational to-hit modifiers | 25 | T29.2 | done |
| T29.4 | Initiative system (SPEED priority) | 20 | T29.1 | done |
| T29.5 | Hit probability calculator | 25 | T29.2, T29.3 | done |
| T29.6 | Incoming threat estimator | 20 | T29.5 | done |
| T29.7 | GATE: Mixed archetypes audit | 25 | all | done |

### S29 Wave Plan

```
Wave 1:             T29.1 — Extract helpers          (20 Cx)
Wave 2 (parallel):  T29.2, T29.4 — Dodge + init      (45 Cx)
Wave 3:             T29.3 — Modifiers                  (25 Cx)
Wave 4 (parallel):  T29.5, T29.6 — Hit calc + threat  (45 Cx)
Wave 5:             T29.7 — INTEGRATION GATE           (25 Cx)
```

## Current Focus

S29 complete. All 7 tasks done.

## What Was Just Done

T30.7 (GATE): Integration gate for S30 visual identity. Created `tests/test_s30_integration.py` with 10 tests covering: position data glyph field presence, players array glyph field, glyph rendering in grid frames, ANSI color codes in rendered output, roster glyph display, leader gold diamond overlay, emoji fallback for bots without BOT_GLYPH, all builtin bot source files have distinct BOT_GLYPH, renderer.py arch compliance (286 LOC / 14 functions), and full match regression. All 10 tests pass. No new regressions (pre-existing failures in `test_bot_memory_wiring.py` and `test_fresh_flag.py` are unrelated). Ruff clean.

T30.5: Extended `build_aura_overlay()` in `agentgrounds/wars/cli/overlay.py` with leader gold diamond effect. Leaders with `is_leader=True` get a yellow diamond glyph placed on the first available adjacent empty cell. Diamond can overwrite tier aura dots (higher priority). 8 new tests in `tests/test_aura_extended.py`, all passing. Ruff clean, overlay.py at 161 LOC.

T30.4: Wired render_glyph() into grid + roster. Grid now displays HP-colored glyphs instead of raw emoji (falls back to emoji when no glyph field). Roster shows colored glyphs with crown for leaders. Standings (build_final_roster) also uses render_glyph. Added glyph->name mapping in TerminalRenderer.__init__. 7 new tests in tests/test_renderer_glyph.py, all passing. renderer.py at 286 LOC / 14 functions.

T30.6: Added BOT_GLYPH to all 6 builtin bots (aggro=⚔, tank=■, kiter=◇, random=✦, vibes=◈, starter=◆). Template intentionally left without BOT_GLYPH to test emoji fallback. 4 tests in `tests/test_builtin_glyphs.py` all passing. Ruff clean.

T30.3: Extended `render_glyph()` in `agentgrounds/wars/cli/glyph_render.py` with optional `primary_stat` parameter for stat-based ANSI background colors (power=red, speed=cyan, armor=blue, mind=magenta). Added `get_primary_stat()` helper (returns dominant stat if any >= 35, else None) and `_STAT_BACKGROUNDS` dict. 8 new tests (16 total) in `tests/test_glyph_render.py`, all passing. Ruff clean, arch check clean.

T30.2: Created `agentgrounds/wars/cli/glyph_render.py` with `render_glyph()` function that applies ANSI foreground color based on HP percentage (bright white >75%, green 50-75%, yellow 25-50%, red <=25%). 8 tests in `tests/test_glyph_render.py` all passing. Ruff clean, arch check clean.

T29.7 (GATE): Integration gate for S29. Created `tests/test_s29_integration.py` with 13 tests covering: dodge events in real matches, high-speed dodge rate advantage, initiative kill attribution, resting-target hit-rate modifier, state dict `hit_chance_vs` presence and structure, `incoming_threat` sorting, architecture compliance for `rounds.py` and `rounds_combat.py`, builtin bot regression, and feed "(glancing)" rendering for dodged hits. All 13 tests pass. No regressions introduced (pre-existing failures in `test_bot_memory_wiring.py` are unrelated).

## What's Next

S30 sprint complete (T30.7 GATE passed). Ready for PR or next sprint.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S24 | Experience, Memory, Tournament, Restructure, FX | — | Done |
| S25-S26 | Momentum, King of the Hill | #21 | Done |
| S27 | Stat Budget System | #22 | Done |
| S28 | Roll-Based Combat | #23 | Done |
