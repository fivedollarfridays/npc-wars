/**
 * circuit_renderer.js — Canvas rendering for Code Circuit races.
 *
 * Draws a stylized oval track with car positions, lap indicators,
 * and race-specific visual effects. Game-specific counterpart to renderer.js.
 */

var TRACK_COLORS = {
  asphalt: '#1a1a2e',
  kerb_red: '#cc2233',
  kerb_white: '#cccccc',
  grass: '#0a2a0a',
  line: 'rgba(255,255,255,0.15)',
};

var CAR_COLORS = [
  '#ff3e6c', '#00e5ff', '#ffd700', '#00ff88',
  '#ff8800', '#aa44ff', '#44ff44', '#ff4444',
];

function renderCircuitCanvas(round) {
  if (!matchData || !ctx || !canvas) return;

  var w = canvas.width;
  var h = canvas.height;

  // Clear
  ctx.fillStyle = TRACK_COLORS.grass;
  ctx.fillRect(0, 0, w, h);

  // Draw oval track
  var cx = w / 2;
  var cy = h / 2;
  var rx = w * 0.40;
  var ry = h * 0.35;

  // Track surface
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx + 20, ry + 20, 0, 0, Math.PI * 2);
  ctx.fillStyle = TRACK_COLORS.asphalt;
  ctx.fill();

  // Inner grass
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx - 20, ry - 20, 0, 0, Math.PI * 2);
  ctx.fillStyle = TRACK_COLORS.grass;
  ctx.fill();

  // Track center line
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
  ctx.strokeStyle = TRACK_COLORS.line;
  ctx.lineWidth = 1;
  ctx.setLineDash([8, 8]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Start/finish line
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cx + rx, cy - 22);
  ctx.lineTo(cx + rx, cy + 22);
  ctx.stroke();

  // Draw cars on track based on position
  var positions = round.positions || [];
  var numCars = positions.length;

  positions.forEach(function(pos, i) {
    var carIdx = matchData.players
      ? matchData.players.findIndex(function(p) { return p.emoji === pos.emoji; })
      : i;
    if (carIdx < 0) carIdx = i;

    // Place car on track: spread by position, offset per lap progress
    var racePos = pos.position || (i + 1);
    var angle = -Math.PI / 2 + (racePos - 1) * (Math.PI * 2 / Math.max(numCars, 1));

    var carX = cx + rx * Math.cos(angle);
    var carY = cy + ry * Math.sin(angle);

    // Car dot
    var color = CAR_COLORS[carIdx % CAR_COLORS.length];
    ctx.beginPath();
    ctx.arc(carX, carY, 10, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Position number
    ctx.fillStyle = '#000';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(racePos), carX, carY);

    // Emoji label above
    ctx.font = '16px serif';
    ctx.fillStyle = '#fff';
    ctx.fillText(pos.emoji, carX, carY - 18);
  });

  // Lap indicator
  var lapNum = round.round || 0;
  var totalLaps = matchData.laps || '?';
  ctx.fillStyle = '#e0e0f0';
  ctx.font = 'bold 14px monospace';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillText('LAP ' + lapNum + '/' + totalLaps, 12, 12);
}

function renderCircuitRound(idx) {
  if (!matchData || idx < 0 || idx >= matchData.rounds.length) return;
  var round = matchData.rounds[idx];

  renderCircuitCanvas(round);
  updateCircuitSidebar(round);

  document.getElementById('round-display').textContent = 'L' + round.round;
  document.getElementById('scrubber').value = idx;

  updateCircuitEvents(round, idx);

  if (typeof updateCommentary === 'function') updateCommentary(idx);
}
