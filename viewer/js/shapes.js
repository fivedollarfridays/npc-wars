/**
 * shapes.js — Bot shape drawing functions.
 *
 * Geometric shapes per archetype: circle (Balanced), square (Tank),
 * triangle (Assassin), hexagon (Bruiser), diamond (Controller).
 * Also handles dead bot rendering and momentum aura glow.
 */

// Archetype colors (Geometry Wars aesthetic)
var ARCHETYPE_COLORS = {
  Bruiser: '#ff4444',
  Tank: '#4488ff',
  Assassin: '#aa44ff',
  Controller: '#44ff88',
  Balanced: '#e0e0f0',
};

// Archetype -> shape mapping
var ARCHETYPE_SHAPES = {
  Balanced: 'circle',
  Tank: 'square',
  Assassin: 'triangle',
  Bruiser: 'hexagon',
  Controller: 'diamond',
};

// Build archetype lookup from matchData.stats after match loads
var botArchetypes = {};

function buildArchetypeLookup() {
  botArchetypes = {};
  if (matchData && matchData.stats) {
    for (const [emoji, stats] of Object.entries(matchData.stats)) {
      botArchetypes[emoji] = stats.archetype || 'Balanced';
    }
  }
}

// --- Shape drawing helpers ---

function drawCircle(ctx, cx, cy, r) {
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
}

function drawSquare(ctx, cx, cy, r) {
  const s = r * 1.4;
  ctx.beginPath();
  ctx.roundRect(cx - s / 2, cy - s / 2, s, s, 3);
  ctx.fill();
  ctx.stroke();
}

function drawTriangle(ctx, cx, cy, r) {
  ctx.beginPath();
  ctx.moveTo(cx, cy - r);
  ctx.lineTo(cx - r * 0.866, cy + r * 0.5);
  ctx.lineTo(cx + r * 0.866, cy + r * 0.5);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

function drawHexagon(ctx, cx, cy, r) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    const hx = cx + r * Math.cos(angle);
    const hy = cy + r * Math.sin(angle);
    if (i === 0) ctx.moveTo(hx, hy);
    else ctx.lineTo(hx, hy);
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

function drawDiamond(ctx, cx, cy, r) {
  ctx.beginPath();
  ctx.moveTo(cx, cy - r);
  ctx.lineTo(cx + r, cy);
  ctx.lineTo(cx, cy + r);
  ctx.lineTo(cx - r, cy);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

function drawBotShape(ctx, x, y, archetype, hpPct, radius) {
  const color = ARCHETYPE_COLORS[archetype] || ARCHETYPE_COLORS.Balanced;

  // HP-based opacity
  let alpha = 1.0;
  if (hpPct <= 0.25) alpha = 0.3;
  else if (hpPct <= 0.5) alpha = 0.5;
  else if (hpPct <= 0.75) alpha = 0.7;

  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;

  switch (archetype) {
    case 'Tank': drawSquare(ctx, x, y, radius); break;
    case 'Assassin': drawTriangle(ctx, x, y, radius); break;
    case 'Bruiser': drawHexagon(ctx, x, y, radius); break;
    case 'Controller': drawDiamond(ctx, x, y, radius); break;
    default: drawCircle(ctx, x, y, radius); break;
  }

  ctx.globalAlpha = 1.0;
}

function drawDeadBot(ctx, x, y, archetype, radius) {
  const color = ARCHETYPE_COLORS[archetype] || ARCHETYPE_COLORS.Balanced;
  ctx.globalAlpha = 0.15;
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;

  switch (archetype) {
    case 'Tank': drawSquare(ctx, x, y, radius); break;
    case 'Assassin': drawTriangle(ctx, x, y, radius); break;
    case 'Bruiser': drawHexagon(ctx, x, y, radius); break;
    case 'Controller': drawDiamond(ctx, x, y, radius); break;
    default: drawCircle(ctx, x, y, radius); break;
  }

  // Draw X through the shape
  ctx.globalAlpha = 0.3;
  ctx.strokeStyle = '#ff3e3e';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x - radius * 0.6, y - radius * 0.6);
  ctx.lineTo(x + radius * 0.6, y + radius * 0.6);
  ctx.moveTo(x + radius * 0.6, y - radius * 0.6);
  ctx.lineTo(x - radius * 0.6, y + radius * 0.6);
  ctx.stroke();

  ctx.globalAlpha = 1.0;
}

function drawMomentumAura(ctx, x, y, radius, momentumTier, isLeader) {
  if (momentumTier < 3) return;
  const glowSize = isLeader ? 18 : 12;
  const glowAlpha = isLeader ? 0.6 : 0.35;
  ctx.save();
  ctx.shadowBlur = glowSize;
  ctx.shadowColor = isLeader
    ? 'rgba(255, 200, 50, ' + glowAlpha + ')'
    : 'rgba(255, 255, 255, ' + glowAlpha + ')';
  ctx.beginPath();
  ctx.arc(x, y, radius + 2, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.01)';
  ctx.fill();
  ctx.restore();
}
