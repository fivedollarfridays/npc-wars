# Agent Grounds: Wars — Road to Completion

> **Date:** 2026-03-23
> **Status:** Phase 2 complete. Phase 3A next.
> **Timeline:** 14 sprints remaining → target completion Q1 2027
> **Thesis:** Your Python file is your character sheet. The diff is the game.

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

The first thing anyone tries is `pip install agent-grounds`. It needs to work.

- Package build configuration (pyproject.toml, entry points, data files)
- CI publish pipeline (GitHub Actions → PyPI on tagged release)
- `agentgrounds wars init` creates working arena in any directory
- Fix generate command framing (the "paste into Claude" flow)
- README rewrite for real external users (not internal dev notes)
- Test: fresh venv, `pip install agent-grounds`, `agentgrounds wars init`, `agentgrounds wars play`

**Exit:** Someone who has never seen the repo runs 3 commands and watches a match.

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

#### S42: Server Layer

Local play is a demo. Online play is a product.

- FastAPI server with bot upload endpoint (`agentgrounds wars upload my_bot.py`)
- Matchmaking: time-limited lobby (60s), bots fill empty slots if < 4 players
- Match execution: server runs matches, stores replay JSON
- Replay storage: persist indefinitely, serve via API
- WebSocket: live spectating (watch match as it runs on server)
- Player accounts: API key authentication, match history
- Sandboxed execution: Docker containers per match, network-isolated
- Rate limiting: matches per hour per player

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

- Character generation engine: map stat allocation to body proportions (ARMOR → bulk, SPEED → lean)
- Weapon rendering: each weapon type has a silhouette (dagger = short blade, spear = long shaft)
- Armor rendering: visual weight class (leather = light outline, plate = thick border)
- Color from archetype: Bruiser = red tones, Tank = blue, Assassin = purple, Controller = green
- HP-dependent rendering: full HP = bright, wounded = desaturated, critical = flickering
- Canvas integration: replace emoji rendering with generated character sprites

**Exit:** Two bots with different stats and equipment look visually distinct on screen. You know who's the tank without reading the roster.

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

#### S48: NPC-SDK Extraction

Wars is the template. Extract what's shared.

- Compare Wars codebase to identify shared vs game-specific code (~70%/30% split)
- Extract into `npc-sdk` package: CLI skeleton, bot scanner, sandbox, renderer framework, replay format, XP system, equipment validation, generate command
- Wars depends on `npc-sdk` going forward
- SDK documentation and starter template for new games

#### S49: NPC Racing

Second game validates the SDK.

- F1-inspired: tire compounds, weather, pit strategy, DRS, fuel management
- Built on `npc-sdk` — copy Wars pattern, replace domain content
- Racing PROMPT.md with real F1 domain knowledge
- Ship to PyPI as `npc-race`
- If the SDK works, any future game is 30% new code

#### S50: Matchmaking Brackets

Fair fights create engagement.

- Skill tiers: Rookie/Veteran/Elite/Champion/Open
- Bracket enforcement: can't smurf lower tiers
- Seasonal resets with rewards
- Promotion/demotion matches

#### S51: Advanced Analytics

Help players improve.

- Per-match heatmaps: where you fought, where you died
- Coaching tips: "You die to tanks 60% — try shifting 5 pts POWER → SPEED"
- Replay analysis: round-by-round decision review
- Build comparison tool: see how your loadout performs vs alternatives

#### S52: Mobile Viewer

Watch everywhere.

- Responsive canvas viewer (already started in S41)
- Lightweight native wrapper or PWA
- Push notifications for match results
- Watch tournaments on mobile

#### S53: Launch Polish + Event

Ship it.

- Marketing site at agentgrounds.ai
- Onboarding flow: archetype quiz → starter bot → first match in 2 minutes
- Template picker by playstyle (aggressive, defensive, balanced, trapper, mage)
- Press kit with screenshots, GIFs, one-pager
- Launch event: 100-player open tournament, streamed, with commentary

---

## Timeline Summary

```
2026-03-23  Phase 2 complete. You are here.
            ▼
S40-S43     Phase 3A: Playable Product (pip install, viewer, server, Discord)
            ▼
            Milestone: First external players
            ▼
S44-S47     Phase 3B: Spectacle (characters, sound, cosmetics, tournaments)
            ▼
            Milestone: First tournament, first revenue
            ▼
S48-S53     Phase 4: Scale (SDK, Racing, matchmaking, analytics, mobile, launch)
            ▼
            Milestone: Multi-game platform, 100-player event
            ▼
2027-03     v1.0 — Agent Grounds is a product, a platform, and a spectator sport
```

## Milestone Markers

| Milestone | Sprint | What It Proves |
|-----------|--------|---------------|
| First external player | S40 | Someone installs and plays |
| 10 uploaded bots | S42 | Server works, people create |
| First Discord match | S43 | Community loop works |
| First paid cosmetic | S46 | Monetization works |
| First tournament | S47 | Spectator sport validated |
| Second game ships | S49 | Platform validated |
| 100-player event | S53 | Scale validated |

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
