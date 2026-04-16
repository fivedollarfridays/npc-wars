# Kill Switch — Browser Player Flow Remediation

> Proposal to close the gap between current server capabilities and a complete browser-based player experience.

## Current State

Kill Switch has all the backend pieces: bot editor, lobby state machine, match queue, SSE streaming, WebSocket live play, canvas replay viewer, tournament system. But they're **islands** — nothing connects them into a flow a player can walk through.

**What works end-to-end today:** Editor → submit → fake 30s timer → hardcoded viewer link → replay

**What should work:** Landing → editor → lobby (live player list) → countdown → live match → results → play again

## Principles

- **No new frameworks.** Vanilla JS + existing FastAPI. No React, no build step.
- **Static HTML pages.** Each step is a page, connected by URL navigation + API polling.
- **Progressive enhancement.** SSE for live updates where possible, polling as fallback.
- **Replay-first, live-second.** Replay flow is the priority; live WebSocket gameplay is a stretch goal.

---

## Phase 1: Wire the Flow (Core Path)

### 1.1 Landing Page (`/`)

Create `server/static/index.html` + add root redirect in `app.py`.

**Content:**
- Game title + tagline ("You don't play. You code.")
- Three entry points:
  - **Quick Play** → `/static/editor.html` (write bot, auto-queue)
  - **Tournaments** → `/tournaments` (existing)
  - **Leaderboard** → `/leaderboard` (existing)
- Link to player profile if API key exists in localStorage

**Scope:** 1 HTML file, 1 route change in `app.py`. No backend work.

### 1.2 Fix the Editor → Lobby Connection

The editor already submits bots and shows a fake countdown. Fix it to use real lobby state.

**Changes to `editor.html`:**
- After submit succeeds, poll `GET /api/lobby/status` every 2s (replace fake 30s timer)
- Show **real player list** from lobby status response (emoji + name for each joined bot)
- Show **real countdown** from lobby `time_remaining` field
- When lobby status returns `match_id` (match triggered), redirect to viewer

**Changes to `server/routes/lobby.py`:**
- Ensure `/api/lobby/status` returns: `{players: [{emoji, name}], time_remaining: int, match_id: str|null, status: "waiting"|"running"|"complete"}`
- When match completes, status should include `match_id` so editor can build viewer URL

**No new files.** Fix existing `editor.html` + one route response shape.

### 1.3 Match Redirect + Viewer Integration

When lobby triggers a match:
1. Editor JS detects `match_id` in lobby status
2. Redirects to `/static/viewer/index.html?match=/api/match/{match_id}`
3. Viewer loads match JSON from API (already supports URL param)

**Changes to `server/routes/match.py`:**
- Ensure `GET /api/match/{match_id}` returns match JSON (may already work — verify)
- Add CORS header if viewer is on different path

### 1.4 Results → Play Again Loop

After match replay finishes in the viewer:

**Changes to `viewer/js/app.js`:**
- When playback reaches final frame, show results overlay:
  - Winner (emoji + name)
  - Kill feed (last 8 eliminations)
  - Top 5 stats (kills, damage, survival)
  - "Play Again" button → back to editor with bot code preserved
  - "Leaderboard" button → `/leaderboard`
- Store bot source in `localStorage` so "Play Again" pre-fills the editor

**Scope:** JS changes to existing viewer. No new pages.

---

## Phase 2: Polish the Experience

### 2.1 Lobby Waiting Room Page (Optional Dedicated Page)

If the editor feels too cramped for a lobby UI, create `server/static/lobby.html`:

- Full-screen waiting room after bot submit
- Large player grid (emoji + name + bio for each bot)
- Animated countdown timer
- "Your bot is ready" confirmation
- Fill bot indicators (shows which slots are AI vs human)
- Auto-redirect to viewer on match start

**This is optional** — Phase 1 puts the lobby UI inline in the editor, which may be sufficient.

### 2.2 Pre-Match Countdown Animation

Add a 3-second countdown between lobby close and match start.

**Implementation (viewer-side):**
- Viewer receives match JSON but delays playback by 3s
- During delay, show fullscreen countdown: **3... 2... 1... FIGHT**
- Cyberpunk aesthetic: glitch text, neon flash
- Optional: Web Audio API beep on each count

**Scope:** ~50 lines of JS in the viewer. No backend changes.

### 2.3 Bot Selection (Pick Existing Bot)

Currently the editor only creates new bots. Add "My Bots" panel:

- Fetch `GET /api/bots` (already exists, requires API key)
- Show list of previously submitted bots with name + emoji
- Click to load source into editor
- "Use This Bot" button to join lobby without re-submitting

**Scope:** JS changes to `editor.html` + minor CSS.

### 2.4 SSE Live Match Updates

Replace viewer's JSON-load-and-replay with SSE streaming for matches in progress.

- `GET /api/match/{match_id}/stream` already exists
- Viewer detects if match is still running → switches to SSE mode
- Renders rounds as they arrive (progressive playback)
- Falls back to full JSON load if match already complete

**Scope:** JS changes to `viewer/js/app.js`. SSE endpoint already implemented.

---

## Phase 3: Stretch Goals

### 3.1 Spectator Mode

- `/spectate/{match_id}` — watch someone else's match live
- Tournament matches auto-get spectator links
- Share link via clipboard button

### 3.2 Post-Match Diff Screen

- Dedicated results page showing stat comparison vs lifetime average
- Uses existing `data/stat_diff.py` — just needs a web UI
- XP/coin rewards display (cosmetics integration)

### 3.3 Live WebSocket Gameplay

Wire the existing `viewer/js/live.js` WebSocket mode into the submit flow:
- After lobby closes, server starts WebSocket game server
- Viewer connects via WS instead of loading JSON
- Rounds stream in real-time
- This is the "watch it happen live" experience vs replay

---

## Sprint Mapping (Estimated)

| Sprint | Focus | Cx | Outcome |
|--------|-------|----|---------|
| S48 | 1.1 Landing + 1.2 Lobby wiring + 1.3 Redirect | 80 | Connected flow: editor → real lobby → viewer |
| S49 | 1.4 Results loop + 2.1 Lobby page + 2.2 Countdown | 85 | Complete loop with polish |
| S50 | 2.3 Bot selection + 2.4 SSE streaming | 70 | Returning player flow + live updates |
| S51 | 3.x Stretch goals | TBD | Spectator, diff screen, live WS |

## What We're NOT Doing

- **No SPA framework.** Static pages connected by redirects and API calls.
- **No new database tables.** Lobby and match data structures already exist.
- **No auth overhaul.** Keep the auto-generated API key in localStorage.
- **No mobile optimization.** Desktop browser first.
- **No matchmaking algorithm.** Lobby fills, match runs. Simple.
