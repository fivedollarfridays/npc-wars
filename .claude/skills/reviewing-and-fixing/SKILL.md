---
name: reviewing-and-fixing
description: Runs doc cleanup, full code review, fixes all findings, simplifies the result, then finishes the branch with commit, PR, and CI verification. Chains cleaning-docs, reviewing-code, fix-all, simplify, and finishing-branches into one pipeline.
---

# Reviewing and Fixing

## When to Use

After completing a sprint or significant batch of work, before merging to main. Chains five stages into a single pipeline that trims context, catches issues, fixes them, cleans up the result, and ships.

## Pipeline Overview

```
/cleaning-docs  →  /reviewing-code  →  fix all  →  /simplify  →  /finishing-branches
    (trim)            (find)           (fix)       (clean)         (ship)
```

## Steps

### Stage 0: Doc Cleanup (`/cleaning-docs`)

Run the cleaning-docs skill to optimize context before committing:

1. **Measure** context budget — flag files over threshold (state.md > 200 lines)
2. **Archive** stale docs — move tasks/plans/research from sprints 2+ behind current to `.paircoder/archive/`
3. **Trim** state.md — collapse completed sprint task tables into summary rows, keep only current sprint detail
4. **Verify** — confirm `wc -l state.md` < 200, no broken references

### Stage 1: Review (`/reviewing-code`)

Run the reviewing-code skill on all changes since the last merge:

```bash
git diff main...HEAD --stat
git diff main...HEAD
```

Launch a reviewer agent that checks:
- Type hints and docstrings on public interfaces
- No hardcoded values, debug statements, or secrets
- Test coverage for new functionality
- Architecture compliance (file size, function count limits)
- Code consistency with existing patterns
- Security issues (XSS, injection, path traversal)

Output in Must Fix / Should Fix / Consider format with file:line references.

### Stage 2: Fix All

Fix every Must Fix and Should Fix item from the review:

1. Read each flagged file
2. Apply the fix directly
3. Skip false positives with a brief note
4. Run tests after all fixes: `python -m pytest --tb=short -q`
5. Run lint: `ruff check .`

**Common fix categories:**
- **Security**: XSS sanitization, path traversal guards, encoding params
- **Consistency**: Type annotations, import style, error handling patterns
- **API cleanliness**: Private imports, duplicate constants, naming
- **Bugs**: Operator precedence, off-by-one, missing edge cases

### Stage 3: Simplify (`/simplify`)

Run the simplify skill on the combined changes (original + fixes):

Launch 3 parallel review agents:

1. **Code Reuse** — find duplicated logic, suggest existing utilities
2. **Code Quality** — flag redundant state, parameter sprawl, copy-paste
3. **Efficiency** — find unnecessary work, missed concurrency, hot-path bloat

Wait for all 3 agents. Aggregate findings and fix each issue directly.
Skip false positives. Run tests after fixing.

### Stage 4: Finish (`/finishing-branches`)

Run the finishing-branches skill:

1. **Pre-merge checks**: `pytest`, `ruff check .`
2. **Security scan**: check for secrets in diff
3. **Review changes**: grep for debug statements, TODOs
4. **Create branch** if on main
5. **Commit** with descriptive message
6. **Push and create PR**
7. **Watch CI** until all checks pass
8. If CI fails, fix, commit, push, re-watch
9. Report "CI is green — PR #N is ready to merge"

## Timing

| Stage | Typical Duration |
|-------|-----------------|
| Doc Cleanup | 1-2 minutes |
| Review | 2-3 minutes (agent) |
| Fix All | 5-10 minutes |
| Simplify | 3-5 minutes (3 parallel agents + fixes) |
| Finish | 2-5 minutes (commit + CI) |
| **Total** | **13-25 minutes** |

## When to Skip Stages

- **Skip Doc Cleanup** if state.md is already under 200 lines and no sprints need archiving
- **Skip Simplify** if the review found zero issues — code is already clean
- **Skip Review** if running immediately after a `/simplify` pass
- **Never skip Finish** — always verify CI passes before declaring done

## Error Recovery

- If CI fails after pushing, check `gh run view --log-failed`
- Common CI failures: missing dependency in pyproject.toml, import not available in clean env
- Fix, commit, push, re-watch — don't declare victory until green
