---
name: running-sprint-tasks
description: Executes all tasks in a sprint using dependency-aware wave parallelization. Groups tasks by dependencies, launches parallel driver agents per wave, follows TDD, and tracks progress in state.md.
---

# Running Sprint Tasks

## When to Use

When a sprint has multiple tasks ready to execute and the user invokes `/start-task` with a wave plan or asks to "run the sprint."

## Prerequisites

- Sprint plan exists with task files in `.paircoder/tasks/`
- Each task file has `depends_on` field listing prerequisite task IDs
- All task files have acceptance criteria

## Steps

### 1. Analyze Dependencies

Read all task files for the sprint. Build a dependency graph and group into waves:

```
Wave 1: Tasks with no dependencies (run in parallel)
Wave 2: Tasks depending only on Wave 1 tasks (run after Wave 1 completes)
Wave 3: Tasks depending on Wave 1-2 tasks (run after Wave 2 completes)
...
```

Tasks within the same wave are independent and run concurrently.

### 2. Present Wave Plan

Show the user the wave grouping before executing:

```
Wave 1 (no deps):     T10.1, T10.2, T10.4        (95 Cx)
Wave 2 (scoring):     T10.3, T10.6, T10.7        (95 Cx)
Wave 3 (metadata):    T10.5, T10.8, T10.9        (120 Cx)
Wave 4 (gate):        T10.10                      (25 Cx)
```

### 3. Execute Each Wave

For each wave, launch tasks as parallel driver agents:

```
For each task in wave:
  1. Read the task file for implementation plan and AC
  2. Launch a driver agent with:
     - Full task context (objective, implementation plan, AC)
     - TDD instruction: write failing tests FIRST, then implement
     - Verification: run tests, ruff check
  3. Agent returns when task passes all checks
```

**Agent prompt template:**

```
Implement task {ID}: {title}

Task spec: {paste full task file content}

Workflow:
1. Write tests in tests/test_{module}.py (TDD — tests first)
2. Run tests to confirm they fail
3. Write implementation
4. Run tests to confirm they pass
5. Run ruff check on new files
6. Report: files created, test count, any issues
```

### 4. Verify Between Waves

After each wave completes:

1. Run the full test suite: `python -m pytest --tb=short -q`
2. Run linter: `ruff check .`
3. Fix any cross-task conflicts (import clashes, naming collisions)
4. Update state.md with completed task IDs

### 5. Final Verification

After all waves complete:

```bash
python -m pytest --tb=short    # Full suite
ruff check .                   # Lint
```

Update state.md with sprint status.

## Parallelization Rules

- **Max 3-4 agents per wave** — more causes context thrashing
- **Isolate file ownership** — no two agents in the same wave should modify the same file
- **If a task touches shared files** (e.g., `game.py`), move it to a later wave or run it solo
- **Integration test tasks** always go in the final wave

## Error Recovery

- If an agent fails, read its output and fix manually
- If tests from Wave N break in Wave N+1, fix before proceeding
- Never skip a failing wave — all tests must pass before the next wave starts

## Example

Sprint 10 (Spectacle & Audio) was executed in 4 waves:

| Wave | Tasks | Cx | Strategy |
|------|-------|----|----------|
| 1 | T10.1 (SpectacleEngine), T10.2 (waveforms), T10.4 (stingers) | 95 | Independent modules |
| 2 | T10.3 (game.py wiring), T10.6 (mixer), T10.7 (hype tracks) | 95 | Depend on engine + audio |
| 3 | T10.5 (video FX), T10.8 (viewer JS), T10.9 (video render) | 120 | Depend on spectacle data |
| 4 | T10.10 (integration tests) | 25 | Validates everything |

Result: 1013 tests → 1103 tests, all passing.
