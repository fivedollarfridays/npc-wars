# Kill Switch — Road to Completion

> **Platform:** Agent Grounds (agentgrounds.ai)
> **Game:** Kill Switch (battle royale) — formerly "NPC Wars" / "Wars"
> **Date:** 2026-03-26
> **Status:** Phase 4 complete (S51). Rival Training Wheels in progress (S52).
> **Timeline:** 4 sprints remaining (S52-S55) → target completion Q2 2026
> **Thesis:** Your Python file is your character sheet. The diff is the game.
>
> **Naming convention:** Each game under Agent Grounds has its own unique name. Kill Switch (battle royale), Code Circuit (F1 racing). No shared naming pattern — each game is its own brand.

---

## Where We Are

### The Game Today

Agent Grounds: Kill Switch is a battle royale where bots written in Python fight on a grid. Players write a `decide(state)` function — or paste instructions into Claude/GPT to generate one — and watch their bot compete against others. It's installable, playable online, tournament-ready, security-hardened, and launch-polished.

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
| **Balance** | 1000-match sim: no bot >60%, no archetype >60%, 5 maps balanced | S39 |
| **PyPI Package** | `pip install agent-grounds`, CLI entry points, `agentgrounds wars init` | S40 |
| **Browser Viewer** | Canvas replay with interpolation, zoom, kill cam, spectacle effects | S41+ |
| **FastAPI Server** | Bot upload, lobby matchmaking, match execution, replay storage | S42 |
| **Leaderboard + Discord** | Rankings, stats API, Discord bot with 8+ commands | S43 |
| **Character System** | Geometry Wars shapes, stat-driven visuals, archetype colors | S44 |
| **Kill Cam + Sound** | Slow-mo zoom, procedural audio, 16 WAV stingers, hype tiers | S45 |
| **Cosmetics** | 20 items, coin rewards, store page, equip/unequip | S46 |
| **Tournament System** | Bracket engine, API, automated runner, spectator view | S47 |
| **Browser Player Flow** | Landing, editor, lobby, viewer, results — full browser path | S48 |
| **Security Hardening** | AST sandbox, API key hashing, rate limiting, security headers | S49-S50 |
| **Launch Readiness** | Player guide, mobile responsive, lobby UX, SQLite write lock, audio fix | S51 |

**By the numbers:**
- 51 sprints completed (S1-S51)
- 49 PRs merged
- 4,347+ tests passing
- Security hardened (S49-S50): AST sandbox, hashed API keys, rate limiting, CORS, CSP headers
- Player guide, responsive mobile layout, lobby animations
- 13 builtin bots with thematic equipment loadouts
- 5 balance simulation scripts

### What's Missing

The product is launch-ready. What's missing is the *learning curve*:

1. **Training wheels** — new players lose 3-5 matches with no idea why. No coaching, no targeted feedback, no progressive difficulty. The Rival system (S52-S55) fixes this.
2. **Matchmaking brackets** — no skill-based matching yet. Rookies fight veterans.
3. **SDK extraction** — single game, no shared platform layer. Second game (Code Circuit) blocked until this ships.
4. **Advanced analytics** — no coaching beyond post-match diff. The Rival debrief is the first step.

---

## What Shipped: Phase 3A through Phase 4

### Phase 3A: Playable Product (S40-S43) ✅

**Goal:** People can install, play, and compete online. **Done.**

- **S40:** PyPI package (`pip install agent-grounds`), CLI entry points, init flow, README rewrite
- **S41:** Browser viewer overhaul — canvas renderer with interpolation, terrain tiles, equipment shapes, responsive layout, playback controls
- **S42:** FastAPI server — bot upload, lobby matchmaking, match execution, replay storage, API key auth, sandboxed execution
- **S43:** Leaderboard + Discord — rankings, stats API, Discord bot (8+ commands), player profiles, achievement badges

**Exit validated:** Strangers install, create bots with Claude, upload, compete, check leaderboard, get Discord notifications — without asking anyone for help.

### Phase 3B: Spectacle (S44-S47) ✅

**Goal:** The game is watchable, characters are iconic, tournaments are events. **Done.**

- **S44:** Geometry Wars character system — shapes from archetype, size from ARMOR, color from role, weapon indicators, HP-dependent rendering, momentum aura
- **S45:** Kill cam + sound — slow-mo zoom on eliminations, procedural audio, 16 WAV stingers, hype tiers, screen shake
- **S46:** Cosmetics — 20 items, coin rewards, store page, equip/unequip (monetization via coins, not Stripe yet)
- **S47:** Tournament system — bracket engine, API, automated runner, spectator view

**Exit validated:** Non-players can enjoy watching matches. Tournament brackets work at 8/16/32 player scale.

### Phase 4: Hardening + Launch Readiness (S48-S51) ✅

**Goal:** Secure, polished, and ready for real users. **Done.**

Reality diverged from the original plan (which had Racing/SDK here). What actually shipped:

- **S48:** Browser player flow — landing page, code editor, lobby with countdown, viewer integration, results page. Full browser path from arrival to match replay.
- **S49:** Security hardening — AST sandbox with deny-list (os, sys, subprocess, eval, exec, __import__), API key hashing (bcrypt), XSS sanitization across all HTML pages, security headers (CSP, X-Frame-Options, X-Content-Type-Options)
- **S50:** Security remediation — rate limiting on all mutating endpoints, tournament auth, bot source size cap, CORS enforcement, security logging with client IP
- **S51:** Launch readiness — player guide page, mobile responsive CSS, lobby waiting UX with animations, SQLite write lock for concurrency, audio user-gesture fix

**Exit validated:** Security assessment passed. Mobile works. New players have a guide. Server handles concurrent writes safely.

---

## The Plan: 4 Sprints to Training Wheels

### Phase 5: Training Wheels — The Rival System (S52-S55)

**Goal:** New players learn by fighting a personalized AI that exploits their weakest tactical area.

**Why this, why now:** The biggest churn risk is the first 5 matches. Players lose, don't know why, and leave. Matchmaking brackets (skill-based matching) help but don't *teach*. The Rival system teaches.

#### How the Rival System Works

Each player gets a **Rival AI** — a bot specifically designed to exploit their weakest tactical area. Five tiers, each targeting a different weakness:

| Tier | Name | Exploits | Teaching Goal |
|------|------|----------|---------------|
| 1 | **Bully** | Low aggression | "You're too passive — attack more" |
| 2 | **Storm Chaser** | Bad positioning | "You're standing in the storm" |
| 3 | **Economist** | Energy waste | "You burned all your energy on round 2" |
| 4 | **Counter** | Predictable patterns | "You always attack, never defend" |
| 5 | **Mirror** | Adapts to your strategy | "Beat yourself to prove you've grown" |

After each Rival match, a **debrief** shows the exact mistake, the exact round, and the exact fix. Not "you lost because they had more HP" — rather "Round 4: you used Teleport when you had 12 energy. Fortify costs 8 and would have blocked the 23-damage crit that killed you."

**Beating all 5 tiers = graduation to ranked play.** This is the on-ramp.

#### S52: Rival Engine + Tier 1-2

- Rival selection engine: analyze player match history, identify weakest area
- Tier 1 Rival (Bully): aggressive bot that punishes passive play
- Tier 2 Rival (Storm Chaser): positioning bot that exploits bad movement
- Basic debrief: post-match screen with key mistake, round number, suggested fix
- Rival match mode: `agentgrounds wars rival` CLI command + browser button

#### S53: Tier 3-4 + Match History Analysis

- Tier 3 Rival (Economist): energy-efficient bot that punishes waste
- Tier 4 Rival (Counter): pattern-reading bot that counters repetitive strategies
- Match history analysis: identify trends across last 10 matches
- Enhanced debrief: multi-round analysis, pattern visualization

#### S54: Tier 5 + Watcher Integration

- Tier 5 Rival (Mirror): adaptive bot that mimics and counters your strategy
- Watcher integration: Rival system feeds into spectator commentary
- Graduation flow: beat all 5 tiers → unlock ranked queue with ceremony screen
- Rival rematch: replay any tier after graduation

#### S55: Polish + Social

- Leaderboard badges for Rival graduation
- Shareable rival replays ("Watch me beat the Mirror")
- XP integration: bonus XP for Rival progression
- Rival stats page: which tier took you the most attempts

---

## What Comes After

### Phase 6: Scale (S56+)

The original Phase 4 plan — Racing, SDK, matchmaking — moves here. The Rival system is higher priority because it fixes retention before we chase growth.

- **Matchmaking brackets** — skill tiers (Rookie/Veteran/Elite/Champion), MMR-based matching, seasonal resets
- **Code Circuit** — F1 racing game, fork Wars experience layer, ship with duplication
- **SDK extraction** — compare Wars and Racing, extract shared infrastructure into `agent-grounds-sdk`
- **Advanced analytics** — coaching dashboard, pattern detection beyond Rival debrief

No sprint numbers assigned yet. Sequencing depends on what we learn from the Rival system and launch metrics.

---

## Timeline Summary

```
2026-03-23  Phase 1+2 complete (S1-S39)
            ▼
S40-S43     Phase 3A: Playable Product ✅
            ▼
S44-S47     Phase 3B: Spectacle ✅
            ▼
S48-S51     Phase 4: Hardening + Launch Readiness ✅
            ▼
            You are here (2026-03-26)
            ▼
S52-S55     Phase 5: Training Wheels (Rival system)
            ▼
S56+        Phase 6: Scale (matchmaking, SDK, second game)
```

## Milestone Markers

| Milestone | Sprint | Status |
|-----------|--------|--------|
| First external player | S40 | ✅ Done |
| 10 uploaded bots | S42 | ✅ Done |
| First Discord match | S43 | ✅ Done |
| First paid cosmetic | S46 | ✅ Done (coin-based) |
| First tournament | S47 | ✅ Done |
| Security assessment passed | S50 | ✅ Done |
| Launch-ready | S51 | ✅ Done |
| Rival Tier 1-2 playable | S52 | In progress |
| All 5 Rival tiers ship | S54 | Planned |
| Rival graduation flow live | S54 | Planned |
| First graduated player | S55 | Planned |

## Revenue Model

| Source | Sprint | Description |
|--------|--------|-------------|
| Character cosmetics | S46 | Skins, colors, effects, weapon visuals (coin-based) |
| Premium features | S56+ | Private lobbies, replay analysis, custom tournaments |
| Tournament entry | S47+ | Paid entry with prize pools (after free tournaments prove demand) |

Core gameplay is always free. Cosmetics are the primary monetization.

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| New players churn before learning | High | Fatal | Rival system (S52-S55) provides structured learning path |
| Rival bots feel unfair | Medium | High | Debrief makes every loss a lesson. Difficulty tuned per tier. |
| Nobody installs it | Medium | Fatal | Soft launch to AI/dev communities first. Guide page ships with S51. |
| Server costs spike | Low | Medium | Start with single-instance. Scale when demand proves out. Match rate limiting. |
| Balance breaks online | Medium | High | Per-sprint balance sims. Quick hotfix process. Community feedback loop. |

## What Doesn't Change

- **Bot file format:** `decide(state) → action` (Python, single file)
- **CLI-first:** Every interaction scriptable, parseable, automatable
- **Deterministic:** Same seed, same inputs, same outcome
- **Agents-developing-agents:** The meta-loop where AI improves its own bots
- **PROMPT.md is the moat:** Domain expertise baked into the generation prompt
- **Free core gameplay:** Progression, abilities, ranked — all free
- **Security model:** AST scanning, sandboxed execution, no networking, hashed API keys

---

*This document reflects the state of Agent Grounds: Kill Switch as of 2026-03-26. 51 sprints shipped, 4,347+ tests, security hardened, launch-ready. Phases 1-4 are complete. The Rival Training Wheels system (S52-S55) is the current focus — teaching new players before scaling to matchmaking and a second game.*
