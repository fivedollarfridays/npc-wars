# Project Context

## What Is This Project?

**Project:** NPC Wars
**Primary Goal:** Build a spectator battle royale where community-submitted bot AIs fight on a grid, with Discord integration, video rendering, and YouTube auto-upload.

## Repository Structure

```
npc-wars/
├── engine/                 # Core game engine (567 LOC)
│   ├── game.py             # Match runner: 8-phase game loop, 200-round cap
│   ├── combat.py           # Bot class, damage calc, death priority
│   ├── grid.py             # Grid bounds, storm border, spawn positions
│   ├── state.py            # State dict builder for bot decide()
│   ├── sandbox.py          # Bot execution sandbox, timeout, validation
│   ├── loader.py           # Dynamic bot loader from bots/ directory
│   └── match_writer.py     # JSON match output
├── bots/                   # Bot AI implementations (5 examples)
│   ├── goose_loose.py      # Balanced hunter (founder bot)
│   ├── example_aggro.py    # Pure aggression
│   ├── example_tank.py     # Defend & counterattack
│   ├── example_kiter.py    # Hit-and-run
│   └── example_random.py   # Random actions (ChaosBot)
├── play.py                 # Interactive match runner + web server
├── run_match.py            # Headless match runner
├── results/                # Match JSON output
├── viewer/                 # Web-based match replay viewer
│   └── match.html          # Canvas-based replay with timeline
├── .paircoder/             # PairCoder system files
└── .claude/                # Claude Code integration
```

## Tech Stack

- **Language:** Python 3.11+
- **Engine:** Pure Python (stdlib only, no external deps)
- **Viewer:** Vanilla HTML/JS/Canvas
- **Testing:** pytest (to be added in S1)
- **Future:** discord.py, Pillow, ffmpeg, google-api-python-client

## Key Constraints

| Constraint | Requirement |
|------------|-------------|
| **Test Coverage** | Minimum 80% coverage |
| **File Size** | Source < 400 lines, Tests < 600 lines |
| **Functions** | < 50 lines each, < 15 per file |
| **Dependencies** | Review required for new deps |
| **Secrets** | Never commit tokens/secrets |
| **Bot Interface** | decide(state) → (action, direction) — must not break |

## Architecture Principles

1. **Simplicity First** — Engine is stdlib-only, keep it that way
2. **Test-Driven** — TDD mandatory for all code changes
3. **Pure Functions** — Data modules (emoji_claims, leaderboard) are pure functions, I/O at edges
4. **Testable Layers** — Discord formatting separate from Discord client (no mock needed)
5. **File Size Limits** — Video renderer may split into video_grid.py + video_render.py

## How to Work Here

1. Read `.paircoder/context/state.md` for current plan/task status
2. Run `/start-task T<sprint>.<seq>` to begin a task
3. Follow TDD: write failing tests first, then implement
4. Run `bpsai-pair arch check <path>` before marking done
5. Update `state.md` after completing each task
