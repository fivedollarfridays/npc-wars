# Current State

> Last updated: 2026-03-23 T41.4 done

## Active Plans

**Plan:** Sprint 41: Browser Viewer Overhaul
- **Sprint:** S41 | **Type:** feature | **Status:** Planned (5 tasks, T41.1-T41.5)
- **Part of:** Phase 3A — Playable Product (S40-S43)
- **Plan ID:** plan-2026-03-s41-viewer

### S41 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T41.1 | Terrain rendering on canvas | 25 | — | done |
| T41.2 | Bot rendering — geometric shapes | 30 | — | done |
| T41.3 | Event FX — traps, abilities, tactical | 20 | T41.1 | done |
| T41.4 | Viewer polish — roster, controls, mobile | 20 | T41.2 | done |
| T41.5 | GATE: Viewer overhaul validation | 15 | all | pending |

### S41 Wave Plan

```
Wave 1 (parallel):  T41.1 (terrain) + T41.2 (bot shapes)         (55 Cx)
Wave 2 (parallel):  T41.3 (event FX) + T41.4 (UI polish)         (40 Cx)
Wave 3:             T41.5 — VIEWER GATE                            (15 Cx)
```

## Current Focus

S41 in progress. Wave 1 complete (T41.1 + T41.2). Wave 2 complete (T41.3 + T41.4). Ready for T41.5 GATE.

## What Was Just Done

**T41.3b: Split viewer/match.html into modular JS files** -- Pure refactor splitting the monolithic 2952-line match.html into index.html (937 lines, HTML+CSS) + 9 JS modules in viewer/js/: audio.js (72), shapes.js (159), renderer.js (245), effects.js (382), events.js (393), live.js (365), controls.js (181), sidebar.js (100), app.js (179). All JS files under 500 lines. No behavior changes. Original match.html renamed to match.html.bak. Updated 21 existing test files to use new read_viewer_content() helper in conftest.py that reads combined viewer files. Added tests/test_viewer_modular.py (19 tests) verifying file structure, script loading order, function placement, and line limits. All 280+ viewer tests pass.

**T41.4: Viewer polish -- roster, controls, mobile** -- Updated roster sidebar to show archetype badge (colored label), equipment text (weapon/armor from stats), score with momentum tier name, and bot name colored by archetype. Roster now sorts alive bots first by score descending, dead bots at bottom. Added zoom controls (mousewheel on canvas + zoom in/out buttons in control bar, 0.5x-3x range via CSS transform). Added mobile responsive layout with media query at 768px (sidebar collapses to bottom panel, canvas fills viewport width). Kill feed already handled new event types from T41.3. Engine: added equipment dict to match stats, added "equipment" to stat_diff _SKIP_KEYS. Viewer modularized by linter into index.html + js/*.js during this task. Added pythonpath to pytest config for conftest imports. Tests: test_viewer_roster.py (8), test_viewer_killfeed.py (6), test_viewer_zoom.py (7), test_viewer_equipment_data.py (2).

**T41.3: Event FX -- traps, abilities, tactical** -- Added canvas rendering for 10 new event types in viewer/match.html: trap_placed (red diamond marker), trap_trigger (orange explosion + damage number), tactical_activate (yellow lightning bolt), ability_damage (purple projectile line + damage), ability_heal (green expanding rings), ability_shield (blue circle outline), ability_slow (purple trailing dots), evolve (golden starburst), crystal_pickup (magenta sparkle particles), wall_blocked (red tile flash). Also added kill feed entries for trap_trigger, tactical_activate, ability_damage/heal/shield/slow, evolve, and crystal_pickup. All effects are subtle and backward compatible with old match JSONs. Added tests/test_viewer_event_fx.py (18 tests).

**T41.2: Bot rendering -- geometric shapes** — Replaced emoji text rendering with canvas-drawn geometric shapes based on archetype. Bots now render as: circle (Balanced), square (Tank), triangle (Assassin), hexagon (Bruiser), diamond (Controller) with archetype-specific colors. Added HP-dependent opacity (4 tiers), momentum aura glow (shadowBlur for tier 3+, brighter for leaders), dead bot X-overlay, and energy bar on canvas. Backward compatible: old matches without archetype data fall back to emoji rendering. Updated both replay and live play renderers. Added tests/test_viewer_bot_shapes.py (10 tests).

**T41.1: Terrain rendering on canvas** — Added terrain tile rendering to browser viewer. Tiles (wall, water, high_ground, cover, crystal) render with muted fill colors, subtle borders, and character indicators (#, triangle, etc). Map name shown in match info header. Backward compatible with matches lacking terrain_tiles. Added tests/test_viewer_data.py validating engine JSON data contract.

**S40 shipped** (PR #35) — PyPI release, generate command fix, README rewrite
**Game renamed:** Kill Switch (battle royale), Code Circuit (F1 racing)

## What's Next

T41.5 (GATE: Viewer overhaul validation) — all Wave 2 tasks done, ready to start.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27-S31 | Phase 1: Foundation | #22-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
| S40 | PyPI Release + Install Flow | #35 | Done |
