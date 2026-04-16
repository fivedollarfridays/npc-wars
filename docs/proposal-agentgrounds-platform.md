# Agent Grounds — Platform Architecture

> **Where Agents Compete. The cheat code is code.**
>
> A gaming platform where the gameplay IS software development.

---

## Strategic Decisions (Locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Entry point | **Arcade-first** | agentgrounds.ai is the front door. pip install is power-user side door. |
| Auth | **GitHub OAuth** | Gets email (paircoder pipeline), username, avatar, AND repo access for git-as-gameplay |
| Git flow | **Full git gameplay** | Fork template → write bot → git push → match runs → results posted. The gameplay IS dev workflow. |
| Integration | **Duplicate first, SDK after** | Wire both games independently, extract shared SDK after both work. Abstract from two, not one. |
| Games at launch | **Kill Switch + Code Circuit** | Both production-ready (57 + 48 sprints). Everything else is stubs. |
| Viewer | **3D engine (Three.js + Rapier)** | Logo arena evolves into match viewer. Same engine, different data source. |
| Monetization funnel | **Games → email → paircoder** | Players are leads. GitHub login captures email. Gaming engagement qualifies leads. |

---

## The Platform

### What It Is

Agent Grounds is an arcade where every game follows the same contract:

```python
def decide(state) -> action
```

Players write Python functions that compete. The platform runs matches, renders replays in 3D, tracks progress across games, and teaches real development skills through gameplay.

### What Makes It a Platform (Not Just Two Games)

1. **One identity** — GitHub login creates an Agent ID that works across all games
2. **One viewer** — the 3D engine renders Kill Switch battles, Code Circuit races, and future games
3. **One progression** — XP, coins, badges earned in any game, visible everywhere
4. **One dev workflow** — git push triggers matches in any game
5. **One email list** — every player is a potential paircoder customer

---

## The Git Flow Gameplay Loop

This is the core innovation. The gameplay IS software development.

### The Loop

```
1. Player signs in with GitHub on agentgrounds.ai
2. Clicks "Play Kill Switch" (or Code Circuit)
3. Forks the template repo: agentgrounds/kill-switch-starter
4. Clones to local machine, opens in VS Code/Cursor
5. Writes their decide() function
6. git push origin main
7. Platform webhook fires → pulls code → validates → runs match
8. Results appear in the arcade (3D viewer, debrief, leaderboard)
9. Player iterates: edit → push → watch → learn → repeat
```

### What Players Learn Without Realizing

- **Git basics** — clone, commit, push, branches
- **CI/CD concept** — push triggers automated testing (the match)
- **Python** — the decide() function IS real Python
- **Testing mindset** — the rival system teaches "write code, see what fails, fix it"
- **Code review** — the debrief IS a code review of their strategy

### The Browser Fallback

Not every player is ready for git on day one. The Monaco editor in the arcade is the quick-start path:

```
Quick Start (browser):       Power User (git):
  Open editor on site          Fork template repo
  Edit template code           Write in VS Code
  Click Submit                 git push
  Watch match                  Watch match (same viewer)

  → Prompt to "level up"       → Full dev workflow
    to the git flow
```

The browser editor is training wheels for the git flow. The rival system (Tier 1-5) teaches gameplay. The git flow teaches development.

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    agentgrounds.ai                        │
│                   (Astro + Vercel)                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  Auth     │  │  Git     │  │  3D Viewer            │  │
│  │  GitHub   │  │  Webhook │  │  Three.js + Rapier    │  │
│  │  OAuth    │  │  Listener│  │  (match replays)      │  │
│  └────┬─────┘  └────┬─────┘  └──────────────────────┘  │
│       │              │                                    │
│  ┌────┴──────────────┴───────────────────────────────┐  │
│  │              Platform API                          │  │
│  │  /api/auth/*     — login, profile, email capture   │  │
│  │  /api/git/*      — webhook receiver, repo status   │  │
│  │  /api/platform/* — xp, coins, badges, leaderboard  │  │
│  └────┬──────────────┬───────────────────────────────┘  │
│       │              │                                    │
│  ┌────┴─────┐  ┌────┴──────┐                            │
│  │ Kill     │  │ Code      │  (future cartridges)       │
│  │ Switch   │  │ Circuit   │                             │
│  │ proxy    │  │ proxy     │                             │
│  └────┬─────┘  └────┬──────┘                            │
└───────┼──────────────┼──────────────────────────────────┘
        │              │
   ┌────┴─────┐  ┌────┴──────┐
   │ npc-wars │  │ npc-race  │
   │ FastAPI  │  │ FastAPI   │
   │ (Mac     │  │ (Mac      │
   │  Mini)   │  │  Mini)    │
   └──────────┘  └───────────┘
```

### Platform Services (agentgrounds-web)

| Service | Purpose | Storage |
|---------|---------|---------|
| **Auth** | GitHub OAuth, Agent ID creation, session management | Platform DB (PostgreSQL or SQLite) |
| **Git Integration** | Webhook listener, repo cloning, code extraction | Temp filesystem |
| **Platform DB** | Cross-game identity, XP, coins, badges, email list | Shared DB |
| **API Proxy** | Routes /api/kill-switch/* to npc-wars, /api/code-circuit/* to npc-race | Stateless |
| **3D Viewer** | Renders match replays from any game in Three.js + Rapier | Client-side |
| **Email Pipeline** | Captures GitHub email, tracks engagement, feeds paircoder CRM | Platform DB |

### Per-Game Services (existing, unchanged)

| Game | Server | DB | What It Owns |
|------|--------|----|----|
| **Kill Switch** (npc-wars) | FastAPI on port 8000 | SQLite (players, bots, matches, rivals, cosmetics) | Match execution, bot validation, rival system, leaderboard |
| **Code Circuit** (npc-race) | FastAPI on port 8001 | SQLite (users, cars, submissions, leaderboard) | Race simulation, car validation, league progression, ghost system |

Games keep their existing auth, DB, and logic. The platform wraps them with a unified identity layer.

---

## Database Schema

### Platform DB (new, shared)

```sql
-- Core identity (one per player, linked to GitHub)
CREATE TABLE agents (
    id          TEXT PRIMARY KEY,           -- UUID
    github_id   INTEGER UNIQUE NOT NULL,    -- GitHub user ID
    username    TEXT NOT NULL,               -- GitHub username
    email       TEXT,                        -- From GitHub (paircoder pipeline)
    avatar_url  TEXT,                        -- GitHub avatar
    created_at  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);

-- Cross-game progression
CREATE TABLE agent_xp (
    agent_id    TEXT PRIMARY KEY REFERENCES agents(id),
    total_xp    INTEGER NOT NULL DEFAULT 0,
    level       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE agent_coins (
    agent_id    TEXT PRIMARY KEY REFERENCES agents(id),
    balance     INTEGER NOT NULL DEFAULT 0
);

-- Links platform identity to per-game identity
CREATE TABLE game_links (
    agent_id    TEXT NOT NULL REFERENCES agents(id),
    game_slug   TEXT NOT NULL,              -- 'kill-switch' or 'code-circuit'
    game_player_id TEXT NOT NULL,           -- The player ID in that game's DB
    game_api_key TEXT,                      -- The API key for that game's server
    linked_at   TEXT NOT NULL,
    PRIMARY KEY (agent_id, game_slug)
);

-- GitHub repo tracking (for git-as-gameplay)
CREATE TABLE agent_repos (
    agent_id    TEXT NOT NULL REFERENCES agents(id),
    game_slug   TEXT NOT NULL,
    repo_full_name TEXT NOT NULL,           -- e.g., 'username/kill-switch-bot'
    webhook_id  INTEGER,                    -- GitHub webhook ID (for cleanup)
    last_push   TEXT,
    PRIMARY KEY (agent_id, game_slug)
);

-- Email pipeline tracking (for paircoder funnel)
CREATE TABLE email_pipeline (
    agent_id    TEXT PRIMARY KEY REFERENCES agents(id),
    email       TEXT NOT NULL,
    games_played TEXT NOT NULL DEFAULT '[]', -- JSON array of game slugs
    total_matches INTEGER NOT NULL DEFAULT 0,
    engagement_tier TEXT NOT NULL DEFAULT 'new', -- new, active, engaged, power
    paircoder_contacted BOOLEAN NOT NULL DEFAULT FALSE,
    last_match  TEXT
);
```

### How Game Links Work

```
Player signs in with GitHub
    → Platform creates Agent ID
    → Player clicks "Play Kill Switch"
    → Platform creates player in Kill Switch DB (via KS API)
    → Platform stores the mapping in game_links
    → All future KS API calls use the linked game_player_id
    → Same flow for Code Circuit
```

Existing Kill Switch players (API key in localStorage) get a migration prompt: "Sign in with GitHub to save your progress across games."

---

## GitHub Integration

### Template Repos

Each game has a starter template repo owned by the agentgrounds org:

```
github.com/agentgrounds/kill-switch-starter
├── bot.py              — Template decide() function with comments
├── README.md           — Rules, state dict reference, getting started
├── .github/
│   └── workflows/
│       └── play.yml    — GitHub Action that submits bot to platform
└── .agentgrounds.yaml  — Game config (game: kill-switch, version: 1)
```

```
github.com/agentgrounds/code-circuit-starter
├── car/
│   ├── strategy.py     — Template strategy() function
│   ├── gearbox.py      — Gearbox part template
│   └── cooling.py      — Cooling part template
├── README.md           — Rules, parts reference, getting started
├── .github/
│   └── workflows/
│       └── race.yml    — GitHub Action that submits car to platform
└── .agentgrounds.yaml  — Game config (game: code-circuit, version: 1)
```

### The Webhook Flow

```
Player pushes to their fork
    → GitHub sends webhook to agentgrounds.ai/api/git/webhook
    → Platform validates: is this a linked repo? is the player authenticated?
    → Platform clones the repo (shallow, latest commit only)
    → Platform extracts bot/car code from known paths
    → Platform submits to the game's API (POST /api/submit-bot or /api/submit-car)
    → Match runs via game's normal pipeline
    → Results stored, visible in arcade
    → Optional: post result as commit comment via GitHub API
```

### The GitHub Action Alternative

For players who prefer explicit control, the template includes a GitHub Action:

```yaml
# .github/workflows/play.yml
name: Play on Agent Grounds
on: [push]
jobs:
  submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: agentgrounds/submit-action@v1
        with:
          game: kill-switch
          api-key: ${{ secrets.AGENTGROUNDS_API_KEY }}
```

This gives players a CI/CD pipeline they control. Push → Action runs → bot submitted → match plays. The Action is optional — the webhook does the same thing automatically.

---

## 3D Viewer as Universal Renderer

The agentgrounds-web 3D engine (Three.js + Rapier, 1,341 tests) becomes the rendering layer for all games.

### How It Works

```
Game server produces match JSON
    → Arcade loads JSON
    → 3D adapter converts game-specific data to scene commands
    → Three.js renders: bots/cars, arena/track, effects, camera
    → Rapier handles: destruction debris, ragdoll, collisions
```

### Per-Game Adapters

**Kill Switch Adapter:**
```
match.rounds[].positions → bot IK characters on grid
match.rounds[].events → attack particles, kill cam zoom
match.storm_border → purple volumetric wall
match.terrain_tiles → block types on arena floor
match.eliminations → ragdoll death + debris
match.spectacle.tier → camera behavior + effects intensity
```

**Code Circuit Adapter:**
```
race.frames[].positions → car meshes on track spline
race.frames[].speeds → motion blur intensity
race.frames[].events → overtake camera pan, pit entry
race.track → 3D track geometry from elevation profile
race.weather → rain particles, wet track shader
race.timing → leaderboard overlay, gap display
```

Both adapters output the same primitives: position entities, trigger effects, drive camera. The renderer doesn't know what game it's rendering.

---

## Email Pipeline (Paircoder Funnel)

### The Funnel

```
                    agentgrounds.ai visitors
                            │
                    Sign in with GitHub
                            │ (email captured)
                            ▼
                    Play first game
                            │ (engagement_tier: 'new' → 'active')
                            ▼
                    Play 10+ matches
                            │ (engagement_tier: 'active' → 'engaged')
                            ▼
                    Graduate rival training
                            │ (engagement_tier: 'engaged' → 'power')
                            ▼
                    Outreach: "You've written 50 bots.
                     Want an AI pair programmer?"
                            │
                            ▼
                    paircoder.dev signup
```

### Engagement Tiers

| Tier | Criteria | Count (estimated) | Paircoder Ready? |
|------|----------|-------------------|-----------------|
| **new** | Signed in, 0 matches | 100% of signups | No |
| **active** | 1-9 matches played | ~60% | No |
| **engaged** | 10+ matches, multiple games | ~25% | Warm lead |
| **power** | Rival graduated, git flow active | ~5% | Hot lead |

Power users have proven they can write Python, use git, iterate on code, and respond to automated feedback. They're the exact target for an AI pair programming tool.

---

## Build Plan

### Phase A: GitHub OAuth + Platform DB (during arcade Phase 4-5)

Build alongside the Kill Switch destruction phase of the logo arena:
- GitHub OAuth flow (login, callback, session)
- Platform DB schema (agents, game_links, xp, coins, email_pipeline)
- Agent ID creation on first login
- Profile page (terminal-styled, cross-game)
- Kill Switch game link (auto-create KS player on first play)

### Phase B: Kill Switch Arcade Integration (during arcade Phase 6-7)

Wire Kill Switch into the arcade:
- API proxy: agentgrounds.ai/api/kill-switch/* → npc-wars FastAPI
- Browser editor (Monaco) submits via proxy
- 3D viewer adapter for Kill Switch match JSON
- Leaderboard, badges, rival status via proxy
- Migrate existing KS players to Agent ID

### Phase C: Git Flow + Webhook (during arcade Phase 7-8)

The git-as-gameplay system:
- Template repo: agentgrounds/kill-switch-starter
- Webhook listener: /api/git/webhook
- Repo cloning + code extraction
- Auto-submit to game API on push
- GitHub Action (agentgrounds/submit-action)
- "Link your repo" UI in the arcade

### Phase D: Code Circuit Integration (post-arcade Phase 8)

Second cartridge:
- API proxy for npc-race
- 3D viewer adapter for race replay format
- Game link for Code Circuit players
- Template repo: agentgrounds/code-circuit-starter
- Webhook support for car repos

### Phase E: SDK Extraction (after both games work)

With two games running through the same platform:
- Extract shared auth into agent-grounds-sdk
- Extract shared DB models (agents, game_links, xp)
- Extract webhook/git integration
- Extract API proxy pattern
- Both games import SDK, platform stays thin

### Phase F: Email Pipeline (ongoing)

Not a phase — it's a background system that grows with users:
- Engagement tier tracking (automated, based on match count + games played)
- Weekly digest email (your stats, leaderboard position, new features)
- Paircoder outreach trigger (engagement_tier reaches 'power')
- Unsubscribe handling, CAN-SPAM compliance

---

## What pip install Becomes

pip install doesn't die — it becomes the **local development environment** for the git flow:

```bash
pip install agent-grounds          # Install the SDK
agentgrounds init kill-switch      # Clone starter template
cd kill-switch-bot/
# ... edit bot.py ...
agentgrounds test                  # Run local match (fast feedback)
git push                           # Submit to platform (real match)
```

`agentgrounds test` runs a local match against fill bots — instant feedback, no server needed. `git push` submits to the platform for ranked play against real opponents. This is the same "local dev + remote CI" workflow that every professional developer uses.

---

## What Changes vs. the Original Arcade Proposal

| Original Proposal | Platform Proposal | Why |
|-------------------|-------------------|-----|
| Anonymous play (auto API key) | GitHub login required to play | Email capture for paircoder pipeline |
| Browser editor only | Git flow primary, editor fallback | Teaches real dev skills, stronger engagement |
| Games as iframes/proxied HTML | Games as API backends, 3D viewer renders all | Universal viewer, consistent experience |
| No email capture | Email pipeline with engagement tiers | Monetization via paircoder funnel |
| Cartridge = load game's HTML | Cartridge = configure 3D viewer + API proxy | Platform controls the experience |

The bedroom, CRT monitor, cartridge metaphor, and all visual design remain unchanged. The platform architecture underneath evolves.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GitHub OAuth friction | Low | Medium | Browser editor as zero-auth fallback for first match. Prompt login after. |
| Webhook reliability | Medium | Medium | GitHub Action as backup. Retry queue for failed webhooks. |
| Two-server complexity | Medium | Low | Both on Mac Mini, docker-compose orchestrates. |
| Email deliverability | Medium | Medium | Use established ESP (Resend, Postmark). Warm up domain gradually. |
| SDK extraction harder than expected | Low | Medium | Only extract after two games prove the patterns. Accept duplication until then. |
| Players don't adopt git flow | Medium | Low | Browser editor always available. Git flow is optional upgrade, not requirement. |

---

## Success Metrics

| Metric | Target (3 months) | Measures |
|--------|-------------------|----------|
| GitHub signups | 500 | Platform adoption |
| Email list size | 400 (80% of signups) | Pipeline health |
| Matches played | 5,000 | Engagement |
| Git flow adoption | 20% of active players | Dev workflow teaching |
| Rival graduates | 50 | Game depth engagement |
| Paircoder conversions | 10 | Funnel effectiveness |

---

*Agent Grounds — Where Agents Compete. The cheat code is code.*
