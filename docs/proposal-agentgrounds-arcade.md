# Agent Grounds — The Arcade

> **Where Agents Compete.**
> **The cheat code is code.**

---

## Vision

agentgrounds.ai is a late-80s bedroom desk. You sit down at the CRT monitor, grab a cartridge from the rack, slot it in, and play. Each cartridge is a different coding game. Your progress follows you across every game you play.

The browser experience mirrors the CLI. Same games, same bots, same results — different screen. Players who `pip install agent-grounds` on their own rig get the same gameplay as players who visit the site. The arcade is a terminal you can see through a CRT.

---

## The Room

### What You See

A stylized late-1980s bedroom desk fills the viewport. Not a photo — a warm, hand-drawn-style illustration (AI-generated, consistent art direction). The desk is the entire UI. No nav bars, no footers, no hamburger menus.

**On the desk:**
- **The CRT monitor** — beige/cream, chunky. The screen glows with a DOS prompt. This is where gameplay happens.
- **The cartridge rack** — a small desktop organizer holding game cartridges upright. Red label (Kill Switch), blue label (Code Circuit), empty slots (future games).
- **The cartridge slot** — on the front of the console unit beside the monitor. Where you insert the cart.
- **The keyboard** — in front of the monitor. Decorative, sets the era.
- **A notepad** — scribbled bot strategies. Click to open the player guide.
- **A desk drawer** — slightly ajar. Click for profile/settings/inventory.

**On the wall behind the desk:**
- **A bulletin board** — pinned leaderboard printouts, match results. Click for rankings.
- **A poster** — "HACK THE PLANET" or Agent Grounds branding. Click for about/credits.

**Desk clutter (non-interactive, personality):**
- Soda can (click for easter egg)
- Pencil cup
- A sticker on the monitor bezel: "THE CHEAT CODE IS CODE"

### How You Navigate

Point-and-click adventure UI. Hover over an object → it glows subtly. Click → it does something. Tooltip on hover shows the label ("CARTRIDGES", "GUIDE", "PROFILE").

| Object | Action |
|--------|--------|
| Cartridge rack | Select a game |
| Monitor screen | Play (when cartridge loaded) |
| Notepad | Player guide / docs |
| Bulletin board | Leaderboard / community |
| Desk drawer | Profile / settings / inventory |
| Poster | About / credits |

---

## The Cartridges

Each game is a physical cartridge with a distinct label. The label is a small illustrated card (SNES proportions — rectangle with rounded top corners).

**Kill Switch** (LIVE)
- Red/orange label
- Art: silhouetted bots in a shrinking arena, storm closing in
- Subtitle: "BATTLE ROYALE"
- Status indicator: green LED (LIVE)

**Code Circuit** (COMING SOON)
- Blue/green label
- Art: racing flag, circuit board traces forming a track
- Subtitle: "F1 STRATEGY"
- Status: amber LED (COMING SOON)

**Future games**
- Gray/blank label, "???" text
- Status: no LED (LOCKED)

### Cartridge Insertion Flow

1. **Click cartridge in rack** → it lifts out of the slot (CSS transform, slight tilt)
2. **Cartridge slides down** into the console slot with a click sound
3. **Monitor reacts** — screen flickers (CRT static, 0.3s), then boot sequence:

```
C:\AGENTGROUNDS> LOADING KILL_SWITCH.EXE...

  Reading cartridge... OK
  Loading arena...    OK
  Initializing bots.. OK

  ██╗  ██╗██╗██╗     ██╗
  ██║ ██╔╝██║██║     ██║
  █████╔╝ ██║██║     ██║
  ██╔═██╗ ██║██║     ██║
  ██║  ██╗██║███████╗███████╗
  ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝
     S W I T C H

  Press ENTER to continue...
```

4. **Game loads** — the monitor expands to fill most of the viewport. The bedroom fades to the edges. The CRT bezel remains as a visible frame around the game content.

### Cartridge Ejection

Press ESC, click the ⏏ eject button, or type `EXIT` in any game screen → game shrinks back into the monitor → bedroom returns → cartridge pops out of the slot back to the rack.

---

## The Monitor (Gameplay)

When a cartridge is inserted, the CRT monitor becomes the game. The content renders inside the monitor's "screen" area with:

- **CRT scan lines** — subtle horizontal lines at ~15% opacity
- **Screen curvature** — slight CSS border-radius on the viewport
- **Vignette** — darker edges, brighter center
- **Phosphor glow** — bright text has a subtle bloom
- **Monitor bezel** — cream/beige frame visible around the game area

### Terminal Aesthetic

The game pages render as **terminal-styled HTML**. Not fancy React components — monospace fonts, green-on-black (or amber-on-black) text, box-drawing characters for tables. The CRT aesthetic IS the design system.

- **Editor page** — Monaco editor styled as a terminal code editor. Dark background, monospace, line numbers. The submit button is `[SUBMIT BOT] ████████ ENTER`.
- **Viewer page** — match replay renders on the CRT. The canvas viewer with kill cams, effects, audio plays inside the monitor frame.
- **Leaderboard** — DOS-style table with `═══╦═══` box characters, scrollable.
- **Profile** — terminal-styled stat readout with ASCII art borders.

### CLI Parity

The browser game IS the CLI game rendered on a screen. Same `decide(state)` API, same match engine, same replay format. A bot written locally works identically when uploaded to the arcade.

| Local (CLI) | Arcade (Browser) |
|-------------|-----------------|
| Write bots in VS Code | Write bots in Monaco (terminal-styled) |
| `agentgrounds wars play` | Click SUBMIT BOT on CRT |
| ANSI terminal output | Canvas viewer inside CRT frame |
| `agentgrounds wars leaderboard` | Bulletin board → DOS-style table |
| JSON replay files | Same JSON, rendered in viewer |

---

## The Landing Screen (No Cartridge)

When you first arrive, the monitor shows:

```
C:\AGENTGROUNDS> _

   █████╗  ██████╗ ███████╗███╗   ██╗████████╗
  ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
  ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
  ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
  ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
              G R O U N D S

  Where Agents Compete.

  > SELECT CARTRIDGE TO PLAY
  > TYPE 'HELP' FOR COMMANDS

C:\AGENTGROUNDS> _
```

The cursor blinks. Typing commands is an easter egg for devs:
- `HELP` → lists available commands
- `PLAY KILL_SWITCH` → inserts the cartridge
- `PROFILE` → opens player profile
- `LEADERBOARD` → opens rankings
- `ABOUT` → credits
- `EXIT` → "Nice try. You can't leave the arcade."

---

## Persistent Identity

### The Agent ID

First visit: you're anonymous. You can browse the room, look at the shelf.

Click PLAY on any cartridge → prompted to create an Agent ID:

```
C:\AGENTGROUNDS> NEW AGENT DETECTED

  Choose your Agent ID: _

  (or sign in with GitHub / Discord / Google)
```

Once created, your Agent ID persists across all games:
- **Global XP** — earned from any game, levels up your agent
- **Coins** — earned from matches, spent in any game's store
- **Badges** — per-game (Kill Switch rival tiers) + cross-game (achievements)
- **Match history** — every match across every game
- **Bot library** — your bots, stored and versioned

### Migration

Existing Kill Switch players (API key in localStorage) get prompted to link their key to an Agent ID. All progress (rival tier, badges, coins, match history) transfers.

---

## Visual Reference

### Color Palette

```
Room background:     Warm illustration (browns, oranges, muted tones of a lit bedroom)
Desk surface:        Wood grain (#5a3a1a to #8b6914 gradient)
Monitor body:        Beige/cream (#d4c5a0 to #b8a88a)
Monitor screen bg:   Deep black-green (#0a0f0a)
Screen text:         Amber (#ffaa00) or green (#33ff33) — player toggle
Screen bright:       White (#ffffff) with phosphor bloom
Cartridge labels:    Per-game unique colors (red, blue, etc.)
Power LED:           Green (#00ff00) when game loaded
Inactive elements:   Dark gray (#333333)
```

### Typography

```
Monitor/terminal:    IBM Plex Mono or VT323 (CRT feel)
Cartridge labels:    Press Start 2P or Silkscreen (retro game font)
Room tooltips:       JetBrains Mono (readable, modern)
ASCII art:           Monospace (same as terminal)
```

### Effects (All Toggleable)

- CRT scan lines (horizontal, 15% opacity)
- Screen curvature (CSS border-radius on game viewport)
- Vignette (radial gradient darker at edges)
- Phosphor persistence (slight text blur/glow on bright elements)
- Flicker on cartridge insertion (0.3s static effect)
- Boot sequence text animation (typewriter effect, 50ms per character)

---

## Architecture

### New Repo

```
github.com/fivedollarfridays/agentgrounds-web

├── src/
│   ├── pages/
│   │   ├── index.astro              — the bedroom (landing)
│   │   ├── games/
│   │   │   ├── kill-switch.astro    — KS game frame (loads game in CRT)
│   │   │   └── code-circuit.astro   — CC game frame (coming soon)
│   │   ├── profile.astro            — terminal-styled profile
│   │   ├── leaderboard.astro        — DOS-style rankings
│   │   └── auth/
│   │       ├── login.astro          — Agent ID creation
│   │       └── callback.astro       — OAuth callback
│   ├── components/
│   │   ├── Bedroom.astro            — the room illustration + hotspots
│   │   ├── CRTMonitor.astro         — monitor frame + CRT effects
│   │   ├── CartridgeRack.astro      — game selection shelf
│   │   ├── CartridgeSlot.astro      — insertion dock + animation
│   │   ├── TerminalScreen.astro     — DOS-style text renderer
│   │   └── PointAndClick.astro      — hotspot hover/click system
│   ├── styles/
│   │   ├── room.css                 — bedroom layout + illustration
│   │   ├── crt.css                  — scan lines, curvature, glow
│   │   ├── terminal.css             — monospace, colors, box chars
│   │   └── cartridge.css            — label art, insertion animation
│   ├── audio/
│   │   ├── cartridge-click.wav
│   │   ├── boot-chime.wav
│   │   ├── menu-blip.wav
│   │   └── eject.wav
│   └── assets/
│       ├── bedroom-bg.png           — room illustration
│       ├── cart-kill-switch.svg      — cartridge label art
│       └── cart-code-circuit.svg
├── public/
│   └── favicon.ico
├── astro.config.mjs
└── package.json
```

### Tech Stack

- **Astro** — static-first, fast, islands architecture for interactive parts
- **Vanilla CSS** — CRT effects, room layout, animations (no Tailwind needed)
- **Vanilla JS** — point-and-click hotspots, cartridge animation, terminal typing
- **OAuth** — GitHub + Discord + Google via Auth.js or Lucia
- **API proxy** — Astro server routes proxy to Kill Switch FastAPI backend

### How Games Connect

```
agentgrounds.ai (Astro, static + SSR)
    │
    ├── /api/auth/*           → Auth service (Agent ID, OAuth)
    ├── /api/profile/*        → Platform DB (cross-game progress)
    │
    ├── /api/kill-switch/*    → Kill Switch FastAPI (Mac Mini)
    │   └── existing API: submit-bot, lobby, match, rival, badges, etc.
    │
    └── /api/code-circuit/*   → Code Circuit FastAPI (future)
```

Each game backend stays independent. The arcade frontend is a shell that:
1. Authenticates the player (Agent ID)
2. Passes the Agent ID to game backends via headers
3. Aggregates cross-game stats for the profile
4. Renders game content inside the CRT frame

### Database

**Platform DB (new, shared):**
```sql
agents (id, username, avatar, created_at, last_seen)
agent_oauth (agent_id, provider, provider_id)
agent_xp (agent_id, total_xp, level)
agent_coins (agent_id, balance)
game_links (agent_id, game_slug, game_player_id)  -- links to per-game identity
```

**Per-game DBs (existing, unchanged):**
- Kill Switch: SQLite with players, bots, matches, rival_progress, cosmetics
- Code Circuit: its own DB (when built)

The `game_links` table bridges Agent IDs to per-game player IDs. Kill Switch's existing API key system becomes one provider — like linking a Steam account to an Epic account.

---

## Build Plan

### Phase 1: The Room (2 sprints)

**Sprint A: Static Bedroom + CRT Shell**
- Room illustration (AI-generated, positioned with CSS)
- Clickable hotspots (cartridge rack, monitor, notepad, drawer, bulletin board)
- CRT monitor component with scan lines, curvature, vignette
- Terminal screen renderer (typewriter effect, blinking cursor)
- Landing screen DOS prompt with ASCII art title
- No auth, no game loading — just the room and the empty terminal

**Sprint B: Cartridge System + Kill Switch Integration**
- Cartridge insertion animation (click → lift → slide → click → boot sequence)
- Eject flow (shrink → bedroom returns → cart pops out)
- Kill Switch loads inside the CRT frame (iframe or dynamic HTML injection)
- Audio: cartridge click, boot chime, eject sound (deferred to user gesture)
- Mobile: room scales, monitor fills viewport, simplified interaction

### Phase 2: Identity (1 sprint)

**Sprint C: Agent ID + OAuth + Migration**
- Agent ID creation flow (terminal-styled prompt)
- GitHub / Discord / Google OAuth
- Platform DB (agents, oauth, xp, coins)
- Kill Switch migration: link existing API key to Agent ID
- Profile page (terminal-styled, cross-game stats)
- Persistent login (JWT or session cookie)

### Phase 3: Polish (1 sprint)

**Sprint D: Leaderboard, Guide, Effects**
- Bulletin board → cross-game leaderboard (DOS table style)
- Notepad → player guide (terminal-styled, content from existing docs)
- Desk drawer → profile/settings/cosmetics
- CRT effects polish (toggle in settings)
- Sound effects polish
- Responsive design (mobile gets simplified room, direct game access)
- Easter egg terminal commands

---

## What This Unlocks

1. **Brand identity** — agentgrounds.ai IS the arcade. The room is memorable, shareable, instantly communicates the vibe.
2. **Multi-game platform** — each new game is just a new cartridge. The room, auth, profile, leaderboard are reusable.
3. **Content hook** — the room itself is content. Screenshots/recordings of the bedroom + cartridge insertion are marketing material.
4. **CLI parity** — players who prefer terminal keep their workflow. The arcade is for players who want the visual experience.
5. **Cross-game progression** — coins, XP, badges work across all games. Beating Kill Switch's rival ladder earns you status visible in every game.

---

## Decisions (Resolved)

1. **Room illustration:** AI-generated. Ship 3-4 variations, pick the one that reads best at desktop and mobile viewport sizes. Commission an artist later if the product proves out. Good enough now beats perfect later.
2. **CRT text color default:** Amber. Warmer, more distinctive, photographs better than green. Avoids "generic hacker aesthetic." Toggle for green still available.
3. **Mobile experience:** Skip the room entirely on phone. Show cartridge selector directly, load games full screen. The room is a desktop experience. Don't force the metaphor where it doesn't fit.
4. **Domain routing:** Path-based — `agentgrounds.ai/kill-switch`. No subdomains. Single domain, single cert, single deploy. Better SEO.
5. **When to build:** The room and cartridge system are marketing material even before the server is live. Build during game development, wire to live backend when ready. The arcade should be ready to go live the moment the server is.
6. **Interactive terminal:** Ship with visual DOS prompt and blinking cursor as decoration only. Interactive commands (HELP, PLAY, etc.) are a future polish pass — charming but non-converting scope.

## Replays in the Room

Match replays need a home in the room. Every match is a shareable moment — replays are content.

**The VHS tape stack** — a small pile of VHS tapes next to the monitor. Click to see recent match replays. Each tape has a handwritten label: "Match #392 — Shadow Dancer wins!" Click a tape → it loads in the CRT viewer.

Alternative: a **dot-matrix printer** on the desk edge, slowly printing match results. The paper curl shows the last 3-5 matches. Click a result → loads the replay.

Either object becomes the "recent matches" feed, giving replays a physical presence in the room rather than hiding them behind a menu.

---

*Agent Grounds — Where Agents Compete. The cheat code is code.*
