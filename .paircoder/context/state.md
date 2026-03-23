# Current State

> Last updated: 2026-03-23 S40 planned

## Active Plans

**Plan:** Sprint 40: PyPI Release + Install Flow
- **Sprint:** S40 | **Type:** chore | **Status:** Planned (5 tasks, T40.1-T40.5)
- **Part of:** Phase 3A — Playable Product (S40-S43)
- **Plan ID:** plan-2026-03-s40-pypi

### S40 Tasks

| Task | Title | Cx | Depends On | Status |
|------|-------|----|------------|--------|
| T40.1 | Package data + PROMPT.md bundling | 20 | — | pending |
| T40.2 | CI publish pipeline + version management | 20 | T40.1 | pending |
| T40.3 | Init command polish + builtin bot bundling | 20 | T40.1 | done |
| T40.4 | Generate command + README rewrite | 15 | T40.1 | done |
| T40.5 | GATE: Install flow end-to-end validation | 15 | all | pending |

### S40 Wave Plan

```
Wave 1:             T40.1 — package data + PROMPT.md              (20 Cx)
Wave 2 (parallel):  T40.2 + T40.3 + T40.4                        (55 Cx)
Wave 3:             T40.5 — INSTALL FLOW GATE                     (15 Cx)
```

## Current Focus

S40 planned. First sprint of Phase 3A.

## What Was Just Done

**T40.4: Generate command fix + README rewrite** -- Rewrote `_manual_generate()` to wrap prompt with clear AI instructions ("Write me a Python bot file..." / "Output ONLY the Python file"). Usage hints now go to stderr so stdout is a clean pipeable prompt. Rewrote README as a short landing page for external users (install, play, generate, bot example, features, commands). Fixed pre-existing test bug where `test_prompt_md_missing_exits` only monkeypatched one path. Added 9 new README structure tests. All 30 tests pass, ruff clean, arch check clean.

## What's Next

T40.1, T40.2, T40.5 remaining. Execute S40 toward first `pip install agent-grounds` release.

## Completed Sprints

| Sprint | Focus | PR | Status |
|--------|-------|-----|--------|
| S1-S18 | Core through Polish | #1-#18 | Done |
| S20-S26 | Experience → King of the Hill | #21 | Done |
| S27-S31 | Phase 1: Foundation | #22-#27 | Done |
| S32-S39 | Phase 2: Depth | #27-#34 | Done |
