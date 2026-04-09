/**
 * renderer.js — Main canvas rendering: terrain, grid, storm, bots.
 *
 * Contains renderCanvas (the core render function), renderInterpolatedFrame,
 * and renderRound which orchestrates canvas + sidebar + controls updates.
 */

// Character descriptor lookup (populated in renderCanvas, used by events.js)
var characterLookup = {};

// Terrain tile colors (muted, so bots/effects stand out)
var TERRAIN_COLORS = {
  open: null,           // transparent - use default background
  wall: '#2a2a3a',
  water: '#0a1a3a',
  high_ground: '#2a2a1a',
  cover: '#1a2a1a',
  crystal: '#2a1a2a',
};
var TERRAIN_BORDER = {
  wall: '#3a3a4a',
  water: '#1a2a4a',
  high_ground: '#3a3a2a',
  cover: '#2a3a2a',
  crystal: '#3a2a3a',
};

function renderCanvas(round) {
  var gridSize = matchData.grid_size;
  var stormBorder = round.storm_border;

  // Clear
  ctx.fillStyle = '#0d0d18';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw storm overlay
  if (stormBorder > 0) {
    ctx.fillStyle = 'rgba(80, 0, 140, 0.35)';
    // Top strip
    ctx.fillRect(0, 0, canvas.width, stormBorder * TILE_SIZE);
    // Bottom strip
    ctx.fillRect(0, (gridSize - stormBorder) * TILE_SIZE, canvas.width, stormBorder * TILE_SIZE);
    // Left strip
    ctx.fillRect(0, stormBorder * TILE_SIZE, stormBorder * TILE_SIZE, (gridSize - 2 * stormBorder) * TILE_SIZE);
    // Right strip
    ctx.fillRect((gridSize - stormBorder) * TILE_SIZE, stormBorder * TILE_SIZE, stormBorder * TILE_SIZE, (gridSize - 2 * stormBorder) * TILE_SIZE);

    // Storm border line
    ctx.strokeStyle = 'rgba(139, 0, 255, 0.6)';
    ctx.lineWidth = 2;
    ctx.strokeRect(
      stormBorder * TILE_SIZE,
      stormBorder * TILE_SIZE,
      (gridSize - 2 * stormBorder) * TILE_SIZE,
      (gridSize - 2 * stormBorder) * TILE_SIZE
    );
  }

  // Render terrain tiles (before grid lines and bots so they draw on top)
  if (matchData.terrain_tiles) {
    var tiles = matchData.terrain_tiles;
    for (var y = 0; y < tiles.length; y++) {
      for (var x = 0; x < (tiles[y] || []).length; x++) {
        var tile = tiles[y][x];
        var color = TERRAIN_COLORS[tile];
        if (color) {
          ctx.fillStyle = color;
          ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
          var border = TERRAIN_BORDER[tile];
          if (border) {
            ctx.strokeStyle = border;
            ctx.lineWidth = 1;
            ctx.strokeRect(x * TILE_SIZE + 0.5, y * TILE_SIZE + 0.5, TILE_SIZE - 1, TILE_SIZE - 1);
          }
        }
        // Terrain indicators
        if (tile === 'wall') {
          ctx.fillStyle = '#3a3a4a';
          ctx.font = (TILE_SIZE * 0.5) + 'px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('#', x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2);
        } else if (tile === 'crystal') {
          ctx.fillStyle = '#aa44aa';
          ctx.font = (TILE_SIZE * 0.3) + 'px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('\u2726', x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2);
        } else if (tile === 'high_ground') {
          ctx.fillStyle = '#4a4a2a';
          ctx.font = (TILE_SIZE * 0.3) + 'px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('\u25B2', x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2);
        } else if (tile === 'cover') {
          ctx.fillStyle = '#2a4a2a';
          ctx.font = (TILE_SIZE * 0.3) + 'px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('\u2591', x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2);
        }
      }
    }
  }

  // Draw grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.03)';
  ctx.lineWidth = 1;
  for (var i = 0; i <= gridSize; i++) {
    ctx.beginPath();
    ctx.moveTo(i * TILE_SIZE, 0);
    ctx.lineTo(i * TILE_SIZE, canvas.height);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, i * TILE_SIZE);
    ctx.lineTo(canvas.width, i * TILE_SIZE);
    ctx.stroke();
  }

  // Build character descriptor lookup from matchData.players
  characterLookup = {};
  if (matchData && matchData.players) {
    matchData.players.forEach(function(p) {
      if (p.character) {
        var charDesc = Object.assign({}, p.character);
        // Merge cosmetics into character descriptor (graceful when absent)
        if (p.cosmetics) {
          charDesc.cosmetics = p.cosmetics;
        }
        characterLookup[p.emoji] = charDesc;
      }
    });
  }

  // Draw bots
  var BASE_RADIUS = 14;

  round.positions.forEach(function(pos) {
    var px = pos.x * TILE_SIZE + TILE_SIZE / 2;
    var py = pos.y * TILE_SIZE + TILE_SIZE / 2;
    var archetype = botArchetypes[pos.emoji] || null;
    var character = characterLookup[pos.emoji] || null;
    var hasArchetype = archetype !== null || character !== null;
    var radius = BASE_RADIUS;

    if (!pos.alive) {
      if (hasArchetype) {
        drawDeadBot(ctx, px, py, archetype, radius);
      } else {
        // Fallback: skull emoji for old matches without archetype data
        ctx.font = EMOJI_SIZE + 'px serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.globalAlpha = 0.2;
        ctx.fillText('\u{1F480}', px, py - 2);
        ctx.globalAlpha = 1;
      }
      return;
    }

    // Momentum aura glow (tier 3+)
    var mTier = pos.momentum_tier || 0;
    var isLeader = pos.is_leader || false;
    var charCosmetics = character ? character.cosmetics : null;
    drawMomentumAura(ctx, px, py, radius, mTier, isLeader, charCosmetics);

    if (hasArchetype) {
      // Draw geometric shape
      var maxHp = pos.max_hp || 100;
      var hpPct = Math.max(0, pos.hp / maxHp);
      drawBotShape(ctx, px, py, archetype, hpPct, radius, character);
    } else {
      // Fallback: emoji for old matches without archetype data
      ctx.font = EMOJI_SIZE + 'px serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(pos.emoji, px, py - 4);
    }

    // HP bar under bot
    var barWidth = TILE_SIZE - 8;
    var barHeight = 3;
    var barX = pos.x * TILE_SIZE + 4;
    var barY = pos.y * TILE_SIZE + TILE_SIZE - 8;
    var maxHpBar = pos.max_hp || 100;
    var hpPctBar = Math.max(0, pos.hp / maxHpBar);

    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.fillRect(barX, barY, barWidth, barHeight);

    var hpColor = hpPctBar > 0.5 ? '#00ff88' : hpPctBar > 0.25 ? '#ffaa00' : '#ff3e3e';
    ctx.fillStyle = hpColor;
    ctx.fillRect(barX, barY, barWidth * hpPctBar, barHeight);

    // Energy bar (thin, below HP)
    var enBarY = barY + barHeight + 1;
    var enPct = Math.max(0, (pos.energy || 0) / 100);
    ctx.fillStyle = 'rgba(0,0,0,0.3)';
    ctx.fillRect(barX, enBarY, barWidth, 2);
    ctx.fillStyle = 'rgba(0, 229, 255, 0.5)';
    ctx.fillRect(barX, enBarY, barWidth * enPct, 2);

    // Action indicator
    var action = pos.action;
    if (action.startsWith('attack')) {
      ctx.strokeStyle = 'rgba(255, 62, 62, 0.5)';
      ctx.lineWidth = 2;
      ctx.strokeRect(pos.x * TILE_SIZE + 2, pos.y * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4);
    } else if (action === 'defend') {
      ctx.strokeStyle = 'rgba(68, 136, 255, 0.5)';
      ctx.lineWidth = 2;
      ctx.strokeRect(pos.x * TILE_SIZE + 2, pos.y * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4);
    } else if (action === 'rest') {
      ctx.strokeStyle = 'rgba(0, 255, 136, 0.3)';
      ctx.lineWidth = 2;
      ctx.strokeRect(pos.x * TILE_SIZE + 2, pos.y * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4);
    }
  });

  // Draw hit and bump effects — delegated to events.js renderEventFX
  renderEventFX(round);
}

function renderInterpolatedFrame(currentRoundData, nextRoundData, t) {
  // Build interpolated round data - only interpolate alive NPCs
  var interpolated = Object.assign({}, currentRoundData);
  interpolated.positions = currentRoundData.positions.map(function(pos) {
    if (!pos.alive) return pos;
    var nextPos = nextRoundData.positions.find(function(p) { return p.emoji === pos.emoji; });
    if (!nextPos || !nextPos.alive) return pos;
    return Object.assign({}, pos, { x: lerp(pos.x, nextPos.x, t), y: lerp(pos.y, nextPos.y, t) });
  });
  renderCanvas(interpolated);
}

function renderRound(idx) {
  if (!matchData || idx < 0 || idx >= matchData.rounds.length) return;

  var round = matchData.rounds[idx];

  // Draw the canvas (storm, grid, bots, effects)
  renderCanvas(round);

  // Update sidebar
  updateSidebar(round);

  // Update controls
  document.getElementById('round-display').textContent = 'R' + round.round;
  document.getElementById('scrubber').value = idx;

  // Add kill feed entries for this round
  updateKillFeed(round);

  // Apply spectacle effects
  var spectacle = round.spectacle;
  if (spectacle) {
    applySpectacleEffects(spectacle.tier, spectacle.triggers || [], spectacle.effects || []);
  }

  // Update commentary ticker
  if (typeof updateCommentary === 'function') updateCommentary(idx);

  // Update code overlay
  if (typeof updateCodeOverlay === 'function') updateCodeOverlay(idx);

  // Play audio stingers for events
  var tier = spectacle ? spectacle.tier : 'calm';
  round.events.forEach(function(evt) {
    audioEngine.play(evt.type, tier);
  });
}
