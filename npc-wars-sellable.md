# NPC Wars — Get Sellable (Public Release)

**Plan type:** chore
**Status:** 18/18 sprints complete. 2,170 tests passing. GitHub repo already public. Not on PyPI (version 0.1.0 in pyproject.toml). Discord bot code exists but no token. YouTube upload code exists but no credentials.
**Estimated complexity:** 35 points
**Sprint budget:** 1 sprint (1 day)

## Tasks

### T1: Version bump and build (5 pts)
- Bump version to 1.0.0 in pyproject.toml
- `python -m build` to create distribution
- **Acceptance:** dist/ contains .whl and .tar.gz

### T2: Test PyPI publish (10 pts)
- `twine upload --repository testpypi dist/*`
- In a clean venv: `pip install --index-url https://test.pypi.org/simple/ npc-wars`
- Verify `npcwars init && npcwars battle` produces output
- **Depends on:** T1
- **Acceptance:** Package installs and runs from TestPyPI

### T3: Publish to PyPI (5 pts)
- `twine upload dist/*`
- Verify `pip install npc-wars` works in clean venv
- **Depends on:** T2
- **Acceptance:** `pip install npc-wars && npcwars init && npcwars battle` works

### T4: GitHub release (10 pts)
- Create git tag v1.0.0
- Create GitHub release with changelog and release notes
- Include: what the game is, how to install, how to create first bot, link to docs
- **Depends on:** T3
- **Acceptance:** Release page shows v1.0.0 with descriptive notes

### T5: Write announcement draft (5 pts)
- Write announcement post for Reddit (r/gamedev, r/python) and Discord
- HOLD publication until Race and Fighter are also on PyPI (Kevin's 3-game requirement)
- **Depends on:** T4
- **Acceptance:** Draft written and saved, not published

## What to skip
- Don't configure Discord bot. Post-launch community building.
- Don't configure YouTube upload pipeline. Manual uploads fine.
- Don't set up itch.io listing. PyPI + GitHub is enough for initial release.
- Don't build classroom mode. Separate sprint.

## Note
Kevin wants all 3 NPC games (Wars + Race + Fighter) published before public announcement. This plan gets Wars *ready on PyPI*. Hold the announcement until all 3 are live.
