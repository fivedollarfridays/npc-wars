---
name: cleaning-docs
description: Optimizes agent-facing files for context efficiency by archiving stale plans, tasks, and research docs, and trimming state.md to a rolling window. Runs as part of the reviewing-and-fixing pipeline.
---

# Cleaning Documentation

## When to Use

After completing a sprint (as part of `/reviewing-and-fixing`), or when state.md exceeds 200 lines, or when starting a new sprint and context feels bloated.

## Pipeline Overview

```
1. Measure  →  2. Archive stale docs  →  3. Trim state.md  →  4. Verify
```

## Steps

### 1. Measure Context Budget

```bash
wc -l .paircoder/context/state.md
wc -l CLAUDE.md
find .paircoder/tasks/ -name "*.task.md" | wc -l
find .paircoder/plans/ -name "*.plan.yaml" | wc -l
wc -l docs/*.md 2>/dev/null
```

Flag any file loaded into agent context that exceeds its threshold:

| File | Threshold | Action |
|------|-----------|--------|
| `state.md` | 200 lines | Trim (step 3) |
| `CLAUDE.md` | 300 lines | Review for stale sections |
| Individual task files | N/A | Archive completed sprints (step 2) |
| Plan files | N/A | Archive completed sprints (step 2) |
| Research docs | 500 lines | Archive if sprint is shipped |

### 2. Archive Stale Documents

Archive documents from sprints that are **2+ sprints behind** the current sprint.

```bash
mkdir -p .paircoder/archive/tasks
mkdir -p .paircoder/archive/plans
mkdir -p .paircoder/archive/research
```

**Tasks:** Move completed sprint task files to archive.

```bash
# Example: archiving S8 tasks when current sprint is S10+
mv .paircoder/tasks/T8.*.task.md .paircoder/archive/tasks/
```

**Plans:** Move completed sprint plan files to archive.

```bash
mv .paircoder/plans/plan-*-s8-*.plan.yaml .paircoder/archive/plans/
```

**Research:** Move research docs whose features are fully shipped.

```bash
mv docs/RESEARCH-*.md .paircoder/archive/research/
```

**Rules:**
- Never archive the **current sprint** or **previous sprint** (need for reference)
- Never archive `CLAUDE.md`, `state.md`, `workflow.md`, or `project.md`
- Keep plan files for the current + next planned sprint
- Archive in bulk per sprint, not individual files

### 3. Trim state.md

`state.md` is loaded into every conversation. Keep it under 200 lines.

**Structure to maintain (target: ~120 lines):**

```markdown
# Current State
> Last updated: {date}

## Active Plan
{plan name, status, current sprint — 3 lines}

## Current Focus
{1 line: what is in progress or next}

## What Was Just Done
{Last completed task — 3-5 lines max}

## What's Next
{Next sprint or task — 2-3 lines}

## Completed Sprints (summary only)
| Sprint | Focus | Tasks | Status |
{One row per completed sprint — no task-level detail}

## Current Sprint Tasks
| ID | Title | Status |
{Only the CURRENT sprint's tasks with status}
```

**What to remove:**
- Individual task status tables for completed sprints (replace with summary row)
- Session history entries older than the last 2 sessions
- "What Was Just Done" entries from prior sprints
- Verbose task descriptions (keep only ID + title + status)
- Any section that duplicates information available via `bpsai-pair status`

**What to keep:**
- Current sprint task table with full status
- Summary row for each completed sprint (sprint, focus, task count, done)
- Active plan metadata
- Current focus and next steps

### 4. Verify

After cleanup:

```bash
wc -l .paircoder/context/state.md    # Should be < 200
ls .paircoder/archive/tasks/ | wc -l  # Archived task count
ls .paircoder/archive/plans/ | wc -l  # Archived plan count
```

Confirm no broken references:
- `bpsai-pair task list` still works for current sprint
- `bpsai-pair plan show` still works for current plan
- No git-tracked files were deleted (only moved)

## Archive Layout

```
.paircoder/archive/
├── tasks/          # Completed sprint task files
│   ├── T1.1.task.md ... T1.12.task.md
│   ├── T2.1.task.md ... T2.8.task.md
│   └── ...
├── plans/          # Completed sprint plan files
│   ├── plan-2026-03-s1-engine-tests.plan.yaml
│   └── ...
└── research/       # Shipped research docs
    └── RESEARCH-spectacle-and-human-play.md
```

## Integration with /reviewing-and-fixing

This skill runs as **Stage 0** (before code review):

```
/cleaning-docs  →  /reviewing-code  →  fix all  →  /simplify  →  /finishing-branches
    (trim)            (find)           (fix)       (clean)         (ship)
```

Running first ensures the commit includes doc cleanup alongside code changes, and the trimmed state.md is committed with the sprint.
