# Kill Switch — Road to Completion

> **Platform:** Agent Grounds (agentgrounds.ai)
> **Game:** Kill Switch (battle royale) — formerly "NPC Wars" / "Wars"
> **Date:** 2026-03-23
> **Status:** Phase 2 complete. Phase 3A next.
> **Timeline:** 11 sprints remaining → target completion Q1 2027
> **Thesis:** Your Python file is your character sheet. The diff is the game.
>
> **Naming convention:** Each game under Agent Grounds has its own unique name. Kill Switch (battle royale), Code Circuit (F1 racing). No shared naming pattern — each game is its own brand.

---

## Where We Are

### The Game Today

Agent Grounds: Wars is a battle royale where bots written in Python fight on a grid. Players write a `decide(state)` function — or paste instructions into Claude/GPT to generate one — and watch their bot compete against others.

**What's built and working:**

| System | Details | Sprint |
|--------|---------|--------|
| **D20 Combat** | Roll-based hits, crits, dodge, initiative, situational modifiers | S28-S29 |
| **Stat Allocation** | 4 stats (POWER/SPEED/ARMOR/MIND), 100-point budget, 6 archetypes | S27 |
| **Equipment** | 23 items across 4 slots (weapon/armor/accessories/tactical), 40-credit budget | S35 |
| **Custom Abilities** | `power_up()` callback defines damage/heal/shield/slow abilities | S36 |
| **Tactical Items** | Battle Cry, Fortify, Teleport, Overdrive — activated with cooldowns | S36 |
| **Traps** | Hidden zones, POWER-scaled damage, 3-round cooldown | S33-S34 |
| **Terrain** | 5 maps (Arena, Fortress, Highlands, Maze, Storm Pit) with walls, water, high ground, cover, crystals | S37 |
| **Callbacks** | setup, on_kill, react, power_up, evolve — level-gated | S33-S36 |
| **XP & Leveling** | 30 levels, SQLite profiles, XP awards, CLI profile command | S32 |
| **Momentum** | Per-round scoring, 5 tiers, King of the Hill leader system | S25-S26 |
| **Post-Match Diff** | Lifetime avg vs current match comparison (▲/▼/─), archetype matchup tracking | S38 |
| **CLI Renderer** | ANSI terminal with HP colors, auras, terrain tiles, kill feed, trap/ability FX | S30+ |
| **Browser Viewer** | Basic HTML/JS replay viewer (match JSON → canvas playback) | S20 |
| **Bot Generation** | `agentgrounds wars generate` builds prompt for Claude/GPT | S20 |
| **Balance** | 1000-match sim: no bot >60%, no archetype >60%, 5 maps balanced | S39 |

**By the numbers:**
- 39 sprints completed (S1-S39)
- 15 PRs merged in Phase 1+2 (#20-#34)
- 3,600+ tests passing
- mypy --strict clean on all engine code
- 13 builtin bots with thematic equipment loadouts
- 5 balance simulation scripts

### What's Missing

The engine is feature-complete. What's missing is the *product*:

1. **Can't install it** — not on PyPI, `pip install` doesn't work
2. **Can't play online** — no server, no upload, no matchmaking
3. **Can't compete** — no leaderboard, no ranked mode
4. **Can't share** — no Discord bot, no social features
5. **Characters are emojis** — browser viewer shows 🤖 not a generated character
6. **No sound** — matches are silent
7. **No tournaments** — no Claude vs GPT spectator events
8. **One game** — Wars only, no Racing/Kitchen/Fighter yet

---

## The Plan: 14 Sprints to Completion

### Phase 3A: Playable Product (S40-S43)

**Goal:** People can install, play, and compete online.

**Why first:** You can't build community around a local tool. Every feature after this amplifies a working product. Without `pip install`, nothing else matters.

#### S40: PyPI Release + Install Flow

The single highest-leverage sprint on the roadmap. Everything downstream depends on people being able to install it.

- Package build configuration (pyproject.toml, entry points, data files)
- CI publish pipeline (GitHub Actions → PyPI on tagged release)
- `agentgrounds wars init` creates working arena in any directory
- Fix generate command framing (the "paste into Claude" flow)
- README rewrite for real external users (not internal dev notes)
- Post-install experience polish: error messages, missing dependency handling, first-run guidance

**Gate tests:**
1. Fresh venv, `pip install agent-grounds`, `agentgrounds wars init`, `agentgrounds wars play` — works
2. **External user test:** Have someone who has never seen the project run those three commands with zero context. Watch where they get confused. Fix what they hit. Ten minutes of observation surfaces more onboarding issues than a week of internal testing.

**Exit:** A stranger installs, creates a bot with Claude, and watches their first match — without asking anyone for help.

**Over-invest here.** Every minute spent on this sprint pays dividends in every sprint after it.

#### S41: Browser Viewer Overhaul

The current viewer shows emojis on a canvas. It needs to show a real battle.

- Canvas renderer: draw bots as styled shapes (not emoji text), terrain tiles with fills
- Smooth movement interpolation (lerp between grid positions per frame)
- Terrain rendering: walls as solid blocks, water with wave effect, high ground with elevation
- Equipment visibility: weapon silhouette next to character, armor outline
- Responsive layout: works on mobile screens
- Match loading: drop JSON file, URL parameter, or fetch from server (when available)
- Playback controls: play/pause, speed, scrub, round-by-round

**Exit:** Watching a match in the browser is visually engaging, not a spreadsheet with emojis.

#### S42: Server Layer (Vertical Slice)

Local play is a demo. Online play is a product. Ship the boring version first, make it exciting later.

**In scope (clean vertical slice):**
- FastAPI server with bot upload endpoint (`agentgrounds wars upload my_bot.py`)
- Simple queue matchmaking: collect uploaded bots, run match when 4+ ready
- Match execution: server runs matches, stores replay JSON
- Replay storage: persist indefinitely, serve via API
- Player accounts: API key authentication, match history
- Sandboxed execution: Docker containers per match, network-isolated
- Rate limiting: matches per hour per player

**Deferred (improve an already-working system):**
- WebSocket live spectating → S45 or later
- MMR-based matchmaking → S50 (matchmaking brackets)
- Time-limited lobby with countdown → after queue proves out

**Exit:** Two players upload bots from different machines. They fight on the server. Both watch the replay.

#### S43: Leaderboard + Discord

Competition needs visibility. Community needs a home.

- `agentgrounds wars leaderboard` shows top players with win rate, level, matches
- Web leaderboard page at server endpoint
- Hidden MMR for matchmaking (Elo-based)
- Discord bot: match result announcements, leaderboard command, `!challenge @player`
- Player profile pages: match history, stat trends, equipment loadout, archetype
- Achievement badges: first win, 10 kills, level 10, etc.

**Exit:** Players check their rank, get match results in Discord, challenge friends.

---

### Phase 3B: Spectacle (S44-S47)

**Goal:** The game is watchable, characters are iconic, tournaments are events.

**Why after 3A:** Character visuals need the canvas viewer (S41). Tournaments need the server (S42). Cosmetics need player accounts (S43). Spectacle amplifies a working product.

#### S44: Code-Built Character System

This is the vision: stats + equipment → visual appearance. A tank looks tanky. An assassin looks sleek. You can tell what a bot does by looking at it.

**Approach: Geometry Wars aesthetic.** Styled geometric shapes scaled by stats, not procedural character sprites. Abstract shapes with good color and animation read better at small canvas sizes than detailed sprites. This may be the permanent solution, not a fallback.

- Shape from archetype: circles (balanced), squares (tank), triangles (assassin), diamonds (controller), hexagons (bruiser)
- Size from ARMOR stat: high armor = larger shape, more visual mass
- Border thickness from equipment armor: leather = thin, plate = thick
- Color from archetype: Bruiser = red, Tank = blue, Assassin = purple, Controller = green, Balanced = white
- Weapon indicator: small attached shape (dagger = dot, sword = line, spear = long line, axe = wedge, bow = arc, mace = circle)
- HP-dependent rendering: full HP = bright/saturated, wounded = desaturated, critical = flickering/pulsing
- Momentum aura: tier 3+ gets glow ring, leader gets crown particle effect
- Canvas integration: replace emoji text rendering with drawn shapes

**Exit:** Two bots with different stats and equipment are visually distinct geometric shapes. You know who's the tank without reading the roster. It looks clean, not like a placeholder.

#### S45: Kill Cam + Animations + Sound

Make the viewer a spectator sport.

- Screen shake on critical hits (canvas transform)
- Slow-mo zoom on eliminations (2x zoom, 0.5x speed for 1.5s)
- Death animation: character dims → particles → empty tile
- Web Audio generative sound: sword impact, ability activation, trap trigger, storm ambient
- Terrain-specific ambient: water bubbling, fortress echo
- Round transition effects: brief fade between rounds

**Exit:** Watching a match with sound on is entertaining. Non-players can enjoy it.

#### S46: Character Customization (Monetization)

The functional visual is free. The *look* of that visual is where money comes from.

- Cosmetic system: color palettes, glow effects, weapon skins, armor textures
- Character preview in browser (rotate, zoom, see stats reflected)
- Cosmetic store: purchase with real money or earned currency
- Stripe/payment integration
- Cosmetic items don't affect gameplay — pure visual customization
- "Premium" visual effects: particle trails, custom death animations

**Exit:** Players buy cosmetics. Revenue is generated. Gameplay remains fair.

#### S47: Tournament System + Phase 3 Gate

The AI spectator sport thesis gets tested.

- Tournament brackets: 8/16/32 player single-elimination
- Automated tournament runner: schedule, execute, broadcast
- "Claude vs GPT vs Gemini" showcase event: each AI generates a bot, they fight live
- Spectator mode: watch live with chat, predictions, highlights
- Tournament replay: full bracket with match replays
- Phase 3 validation: full spectator experience end-to-end

**Exit:** An audience watches a live tournament. The spectator sport thesis is proven or disproven.

---

### Phase 4: Scale (S48-S53)

**Goal:** Multiple games, advanced features, growth. Agent Grounds is a platform.

#### S48-S49: Code Circuit → SDK Extraction

**Ship Racing with duplication first, then extract the shared layer.** Abstracting from one example is guessing. Abstracting from two is pattern recognition.

**S48: Code Circuit (with duplication)**
- Fork Wars experience layer, replace domain content with F1 racing
- Tire compounds, weather, pit strategy, DRS, fuel management
- Racing PROMPT.md with real F1 domain knowledge
- Ship to PyPI as `code-circuit`
- Accept code duplication with Wars — deliberately do not abstract yet

**S49: SDK Extraction (from two working games)**
- Compare Wars and Racing implementations side by side
- Extract shared infrastructure into `agent-grounds-sdk`: CLI skeleton, bot scanner, sandbox, renderer framework, replay format, XP system, generate command
- Both games depend on `agent-grounds-sdk` going forward
- SDK documentation and starter template for new games
- Budget as a double sprint if coupling surprises emerge

#### S50: Matchmaking Brackets

Fair fights create engagement.

- Skill tiers: Rookie/Veteran/Elite/Champion/Open
- MMR-based matchmaking (deferred from S42 vertical slice)
- Bracket enforcement
- Seasonal resets with rewards

#### S51: Launch Polish

Ship it.

- Marketing site at agentgrounds.ai
- Onboarding flow: archetype quiz → starter bot → first match in 2 minutes
- Template picker by playstyle (aggressive, defensive, balanced, trapper, mage)
- Press kit with screenshots, GIFs, one-pager

**Deprioritized (nice-to-have, not critical path):**
- **Advanced analytics / coaching tips** — the diff view and replay system already provide feedback. Ship when player base proves demand.
- **Mobile native wrapper** — responsive canvas from S41 covers mobile browsers. Native wrapper is scope creep for a developer audience already at their computers.
- **100-player launch event** — a marketing milestone, not an engineering one. If tournaments work at 32 players (S47), they work. The event happens when it's ready, not on a sprint schedule.

---

## Timeline Summary

```
2026-03-23  Phase 2 complete. You are here.
            ▼
S40-S43     Phase 3A: Playable Product (pip install, viewer, server, Discord)
            ▼
            Milestone: First external players, first online matches
            ▼
S44-S47     Phase 3B: Spectacle (characters, sound, cosmetics, tournaments)
            ▼
            Milestone: First tournament, first revenue
            ▼
S48-S51     Phase 4: Scale (Racing, SDK, matchmaking, launch)
            ▼
            Milestone: Multi-game platform live
            ▼
2027        v1.0 — Agent Grounds is a product, a platform, and a spectator sport
```

**Total remaining: 12 sprints** (S40-S51). Trimmed from 14 by cutting mobile native wrapper and advanced analytics from critical path.

## Milestone Markers

| Milestone | Sprint | What It Proves |
|-----------|--------|---------------|
| First external player | S40 | Someone installs and plays |
| 10 uploaded bots | S42 | Server works, people create |
| First Discord match | S43 | Community loop works |
| First paid cosmetic | S46 | Monetization works |
| First tournament | S47 | Spectator sport validated |
| Racing ships | S48 | Second game works (with duplication) |
| SDK extracted | S49 | Platform architecture validated |

## Revenue Model

| Source | Sprint | Description |
|--------|--------|-------------|
| Character cosmetics | S46 | Skins, colors, effects, weapon visuals |
| Premium features | S50+ | Private lobbies, replay analysis, custom tournaments |
| Tournament entry | S47+ | Paid entry with prize pools (after free tournaments prove demand) |

Core gameplay is always free. Cosmetics are the primary monetization.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Nobody installs it | Medium | Fatal | Soft launch to AI/dev communities first. Iterate on onboarding before broad push. |
| Server costs spike | Low | Medium | Start with single-instance. Scale when demand proves out. Match rate limiting. |
| Balance breaks online | Medium | High | Per-sprint balance sims. Quick hotfix process. Community feedback loop. |
| Spectator sport doesn't work | Medium | Medium | Test with small tournament (S47) before investing in broadcast infrastructure. |
| SDK extraction is harder than expected | Low | Medium | Only extract after 2 working games. Accept some duplication initially. |

## What Doesn't Change

- **Bot file format:** `decide(state) → action` (Python, single file)
- **CLI-first:** Every interaction scriptable, parseable, automatable
- **Deterministic:** Same seed, same inputs, same outcome
- **Agents-developing-agents:** The meta-loop where AI improves its own bots
- **PROMPT.md is the moat:** Domain expertise baked into the generation prompt
- **Free core gameplay:** Progression, abilities, ranked — all free
- **Security model:** AST scanning, sandboxed execution, no networking

---

*This document reflects the state of Agent Grounds: Wars as of 2026-03-23. Phase 1 (Foundation) and Phase 2 (Depth) are complete. 15 sprints shipped, 3,600+ tests, 13 builtin bots, 5 terrain maps, 1000-match balance validation. The game engine is done. Now we make it a product.*
