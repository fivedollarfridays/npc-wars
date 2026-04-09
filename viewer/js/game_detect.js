/**
 * game_detect.js — Detect game type from loaded match JSON.
 *
 * Returns "circuit" for Code Circuit races, "killswitch" for Kill Switch.
 * Must be loaded BEFORE app.js so detection is available at init time.
 */

var currentGameType = "killswitch";

function detectGame(data) {
  if (!data) return "killswitch";
  if (data.game === "circuit") return "circuit";
  if (data.grid_size !== undefined || data.terrain_tiles !== undefined) {
    return "killswitch";
  }
  return "killswitch";
}
