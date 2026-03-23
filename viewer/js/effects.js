/**
 * effects.js — Particle effects, spectacle effects, screen shake, kill cam.
 *
 * Contains shatterEffect, deathExplosion, attackSwoosh, applySpectacleEffects,
 * glitchEffect, darkEntranceEffect, skullFlashEffect, pulseWaveEffect,
 * multiballEffect, splitScreenEffect, showBanner, triggerKillCam,
 * updateKillCam, playDeathAnimation.
 */

// Kill cam state
var killCamActive = false;
var killCamTimer = 0;
var killCamX = 0;
var killCamY = 0;
var savedSpeed = 1;
var _deathParticles = [];

function triggerKillCam(canvasEl, x, y, duration) {
  if (killCamActive) return;  // don't stack
  killCamActive = true;
  killCamX = x;
  killCamY = y;
  killCamTimer = duration || 1500;
  savedSpeed = speed || 1;
  speed = 0.25;  // slow-mo

  // Zoom canvas via CSS transform
  canvasEl.style.transition = 'transform 0.3s ease';
  canvasEl.style.transformOrigin = (x / canvasEl.width * 100) + '% ' + (y / canvasEl.height * 100) + '%';
  canvasEl.style.transform = 'scale(1.8)';
}

function updateKillCam(canvasEl, dt) {
  if (!killCamActive) return;
  killCamTimer -= dt;
  if (killCamTimer <= 0) {
    killCamActive = false;
    speed = savedSpeed;
    canvasEl.style.transition = 'transform 0.3s ease';
    canvasEl.style.transform = 'scale(1)';
  }
}

function playDeathAnimation(octx, x, y, color, callback) {
  var frames = [
    { opacity: 0.5, scale: 1.0, delay: 0 },
    { opacity: 0.2, scale: 0.8, delay: 200 },
    { opacity: 0.0, scale: 0.5, delay: 400 },
  ];
  var fillColor = color || '#ff4444';
  var startTime = Date.now();

  function animate() {
    var elapsed = Date.now() - startTime;
    var frame = frames[0];
    for (var i = frames.length - 1; i >= 0; i--) {
      if (elapsed >= frames[i].delay) { frame = frames[i]; break; }
    }

    octx.save();
    octx.globalAlpha = frame.opacity;
    octx.fillStyle = fillColor;
    octx.beginPath();
    octx.arc(x, y, 14 * frame.scale, 0, Math.PI * 2);
    octx.fill();
    octx.restore();

    if (elapsed < 600) {
      requestAnimationFrame(animate);
    } else {
      // particle burst at end
      for (var i = 0; i < 8; i++) {
        var angle = (i / 8) * Math.PI * 2;
        _deathParticles.push({
          x: x, y: y,
          vx: Math.cos(angle) * 2,
          vy: Math.sin(angle) * 2,
          life: 30,
          color: fillColor,
        });
      }
      if (callback) callback();
    }
  }
  animate();
}

function applySpectacleEffects(tier, triggers, effects) {
  var grid = document.getElementById('arena-canvas');
  if (!grid) return;

  // Clear previous effects
  grid.style.animation = '';
  grid.style.boxShadow = '';
  grid.style.filter = '';

  // Remove old banners
  document.querySelectorAll('.spectacle-banner').forEach(function(el) { el.remove(); });

  if (tier === 'calm') return;

  // Smooth, subtle effects only — no flashing, no strobing
  if (tier === 'hype' || tier === 'chaos') {
    grid.style.boxShadow = '0 0 20px rgba(255,62,108,0.3)';
  }

  if (effects.includes('slow_mo')) {
    grid.style.filter = 'saturate(0.7)';
  }

  if (triggers.includes('watcher_attack')) {
    pulseWaveEffect(grid.width / 2, grid.height / 2);
  }

  if (triggers.includes('chain_bump')) {
    multiballEffect([[grid.width / 2, grid.height / 2]]);
  }

  if (triggers.includes('last_2')) {
    splitScreenEffect();
  }

  // Banners
  if (triggers.includes('kill_streak')) {
    showBanner('UNSTOPPABLE', '#ff4400');
  }
  if (triggers.includes('chain_bump')) {
    showBanner('MULTI-BUMP', '#ffaa00');
  }
  if (triggers.includes('last_2')) {
    showBanner('FINAL SHOWDOWN', '#ff0066');
  }
}

function showBanner(text, color) {
  var banner = document.createElement('div');
  banner.className = 'spectacle-banner';
  banner.style.color = color;
  banner.textContent = text;
  var container = document.getElementById('arena-canvas').parentElement;
  container.style.position = 'relative';
  container.appendChild(banner);
}

function glitchEffect() {
    var arena = document.querySelector('.arena');
    if (!arena) return;
    arena.classList.add('glitch-effect', 'glitch-scanlines');
    setTimeout(function() {
        arena.classList.remove('glitch-effect', 'glitch-scanlines');
    }, 400);
}

// Shatter effect - particle explosion on kill
function shatterEffect(x, y, color) {
  var canvasEl = document.getElementById('arena-canvas');
  if (!canvasEl) return;
  var overlay = document.createElement('canvas');
  overlay.width = canvasEl.width;
  overlay.height = canvasEl.height;
  overlay.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;';
  canvasEl.parentElement.style.position = 'relative';
  canvasEl.parentElement.appendChild(overlay);
  var octx = overlay.getContext('2d');
  var particleCount = 8 + Math.floor(Math.random() * 5); // 8-12 particles
  var particles = [];
  for (var i = 0; i < particleCount; i++) {
    var angle = (Math.PI * 2 * i) / particleCount + (Math.random() - 0.5) * 0.5;
    var speed = 60 + Math.random() * 80;
    particles.push({
      x: x, y: y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      size: 3 + Math.random() * 4,
      opacity: 1.0
    });
  }
  var duration = 500; // 0.5s
  var startTime = performance.now();
  function animate(now) {
    var elapsed = now - startTime;
    var progress = Math.min(elapsed / duration, 1.0);
    octx.clearRect(0, 0, overlay.width, overlay.height);
    particles.forEach(function(p) {
      p.opacity = 1.0 - progress;
      var t = elapsed / 1000;
      var px = p.x + p.vx * t;
      var py = p.y + p.vy * t;
      octx.globalAlpha = p.opacity;
      octx.fillStyle = color;
      octx.fillRect(px - p.size / 2, py - p.size / 2, p.size, p.size);
    });
    octx.globalAlpha = 1.0;
    if (progress < 1.0) {
      requestAnimationFrame(animate);
    } else {
      overlay.remove();
    }
  }
  requestAnimationFrame(animate);
}

function darkEntranceEffect() {
    var arena = document.querySelector('.arena');
    if (!arena) return;
    arena.style.position = 'relative';

    // Create dimming overlay
    var overlay = document.createElement('div');
    overlay.className = 'dark-entrance-overlay';
    overlay.style.background = 'rgba(0,0,0,0.7)';
    arena.appendChild(overlay);

    // Create vignette overlay
    var vignette = document.createElement('div');
    vignette.className = 'dark-entrance-overlay';
    vignette.style.background = 'radial-gradient(ellipse at center, transparent 30%, rgba(128,0,255,0.3) 100%)';
    arena.appendChild(vignette);

    // Phase 1: Dim (0-0.3s)
    requestAnimationFrame(function() {
        overlay.classList.add('active');
        vignette.classList.add('active');
    });

    // Phase 2-3: Watcher emoji scales in (0.3-1.5s)
    setTimeout(function() {
        // Phase 4: Fade out (1.2-1.5s)
        overlay.style.transition = 'opacity 0.3s';
        vignette.style.transition = 'opacity 0.3s';
        overlay.classList.remove('active');
        vignette.classList.remove('active');
        setTimeout(function() {
            overlay.remove();
            vignette.remove();
        }, 300);
    }, 1200);
}

function skullFlashEffect() {
    var arena = document.querySelector('.arena');
    if (!arena) return;
    arena.style.position = 'relative';
    var flash = document.createElement('div');
    flash.style.cssText = 'position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(255,255,255,0.8);pointer-events:none;z-index:55;animation:skull-flash-fade 0.3s forwards;';
    var skull = document.createElement('div');
    skull.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:64px;z-index:56;pointer-events:none;animation:skull-flash-fade 0.3s forwards;';
    skull.textContent = '\u{1F480}';
    arena.appendChild(flash);
    arena.appendChild(skull);
    setTimeout(function() { flash.remove(); skull.remove(); }, 300);
}

function pulseWaveEffect(x, y) {
    var canvasEl = document.getElementById('arena-canvas');
    if (!canvasEl) return;
    var overlay = document.createElement('canvas');
    overlay.width = canvasEl.width;
    overlay.height = canvasEl.height;
    overlay.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:55;';
    canvasEl.parentElement.style.position = 'relative';
    canvasEl.parentElement.appendChild(overlay);
    var octx = overlay.getContext('2d');
    var duration = 600;
    var startTime = performance.now();
    var ringCount = 3;
    function animate(now) {
        var elapsed = now - startTime;
        var progress = Math.min(elapsed / duration, 1.0);
        octx.clearRect(0, 0, overlay.width, overlay.height);
        for (var i = 0; i < ringCount; i++) {
            var ringProgress = Math.max(0, Math.min(1, (progress - i * 0.15) / 0.7));
            if (ringProgress <= 0) continue;
            var radius = ringProgress * Math.max(overlay.width, overlay.height) * 0.4;
            var opacity = (1 - ringProgress) * 0.6;
            octx.beginPath();
            octx.arc(x, y, radius, 0, Math.PI * 2);
            octx.strokeStyle = 'rgba(139, 0, 255, ' + opacity + ')';
            octx.lineWidth = 3 - ringProgress * 2;
            octx.stroke();
        }
        if (progress < 1.0) {
            requestAnimationFrame(animate);
        } else {
            overlay.remove();
        }
    }
    requestAnimationFrame(animate);
}

function multiballEffect(positions) {
    var canvasEl = document.getElementById('arena-canvas');
    if (!canvasEl) return;
    var overlay = document.createElement('canvas');
    overlay.width = canvasEl.width;
    overlay.height = canvasEl.height;
    overlay.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:55;';
    canvasEl.parentElement.style.position = 'relative';
    canvasEl.parentElement.appendChild(overlay);
    var octx = overlay.getContext('2d');
    var balls = [];
    (positions || []).forEach(function(pos) {
        for (var i = 0; i < 3; i++) {
            balls.push({
                x: pos[0], y: pos[1],
                vx: (Math.random() - 0.5) * 200,
                vy: (Math.random() - 0.5) * 200 - 100,
                radius: 3 + Math.random() * 3,
                opacity: 1
            });
        }
    });
    if (balls.length === 0) { overlay.remove(); return; }
    var duration = 800;
    var startTime = performance.now();
    function animate(now) {
        var elapsed = now - startTime;
        var progress = Math.min(elapsed / duration, 1.0);
        var dt = elapsed / 1000;
        octx.clearRect(0, 0, overlay.width, overlay.height);
        balls.forEach(function(b) {
            var px = b.x + b.vx * dt;
            var py = b.y + b.vy * dt + 200 * dt * dt;
            b.opacity = 1 - progress;
            octx.globalAlpha = b.opacity;
            octx.beginPath();
            octx.arc(px, py, b.radius, 0, Math.PI * 2);
            octx.fillStyle = '#ffaa00';
            octx.fill();
        });
        octx.globalAlpha = 1;
        if (progress < 1.0) {
            requestAnimationFrame(animate);
        } else {
            overlay.remove();
        }
    }
    requestAnimationFrame(animate);
}

function splitScreenEffect() {
    var arena = document.querySelector('.arena');
    if (!arena) return;
    arena.style.position = 'relative';
    var existing = arena.querySelector('.split-screen-divider');
    if (existing) return;
    var divider = document.createElement('div');
    divider.className = 'split-screen-divider';
    arena.appendChild(divider);
}

// Attack swoosh animation on hit events
function attackSwoosh(fromX, fromY, toX, toY) {
    var canvasEl = document.getElementById('arena-canvas');
    if (!canvasEl) return;
    var overlay = document.createElement('canvas');
    overlay.width = canvasEl.width;
    overlay.height = canvasEl.height;
    overlay.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:55;';
    canvasEl.parentElement.style.position = 'relative';
    canvasEl.parentElement.appendChild(overlay);
    var octx = overlay.getContext('2d');

    var duration = 300;
    var startTime = performance.now();
    var dx = toX - fromX;
    var dy = toY - fromY;
    var angle = Math.atan2(dy, dx);

    function animate(now) {
        var elapsed = now - startTime;
        var t = Math.min(elapsed / duration, 1.0);
        octx.clearRect(0, 0, overlay.width, overlay.height);

        var len = 30 * t;
        octx.save();
        octx.translate(fromX + dx * t, fromY + dy * t);
        octx.rotate(angle);
        octx.beginPath();
        octx.arc(0, 0, len, -0.5, 0.5);
        octx.strokeStyle = 'rgba(255, 62, 62, ' + (1 - t) + ')';
        octx.lineWidth = 3 - t * 2;
        octx.stroke();
        octx.restore();

        if (t < 1.0) {
            requestAnimationFrame(animate);
        } else {
            overlay.remove();
        }
    }
    requestAnimationFrame(animate);
}

// Death explosion particle burst on kill events
function deathExplosion(x, y) {
    var canvasEl = document.getElementById('arena-canvas');
    if (!canvasEl) return;
    var overlay = document.createElement('canvas');
    overlay.width = canvasEl.width;
    overlay.height = canvasEl.height;
    overlay.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:55;';
    canvasEl.parentElement.style.position = 'relative';
    canvasEl.parentElement.appendChild(overlay);
    var octx = overlay.getContext('2d');

    var particles = [];
    for (var i = 0; i < 16; i++) {
        var angle = (Math.PI * 2 * i) / 16;
        particles.push({
            x: x, y: y,
            vx: Math.cos(angle) * (80 + Math.random() * 60),
            vy: Math.sin(angle) * (80 + Math.random() * 60),
            size: 2 + Math.random() * 3,
            color: Math.random() > 0.5 ? '#ff3e3e' : '#ffaa00',
        });
    }

    var duration = 600;
    var startTime = performance.now();
    function animate(now) {
        var elapsed = now - startTime;
        var t = Math.min(elapsed / duration, 1.0);
        octx.clearRect(0, 0, overlay.width, overlay.height);
        particles.forEach(function(p) {
            var dt = elapsed / 1000;
            var px = p.x + p.vx * dt;
            var py = p.y + p.vy * dt + 150 * dt * dt;
            octx.globalAlpha = 1 - t;
            octx.fillStyle = p.color;
            octx.beginPath();
            octx.arc(px, py, p.size * (1 - t * 0.5), 0, Math.PI * 2);
            octx.fill();
        });
        octx.globalAlpha = 1;
        if (t < 1.0) requestAnimationFrame(animate);
        else overlay.remove();
    }
    requestAnimationFrame(animate);
}

// --- Round transition + winner celebration ---

function showRoundNumber(ctx, canvas, roundNum) {
    ctx.save();
    ctx.globalAlpha = 0.6;
    ctx.fillStyle = '#00e5ff';
    ctx.font = 'bold 32px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('R' + roundNum, canvas.width / 2, canvas.height / 2);
    ctx.restore();
}

function showWinnerCelebration(ctx, canvas, winnerX, winnerY, color) {
    var particles = [];
    for (var i = 0; i < 16; i++) {
        particles.push({
            x: winnerX, y: winnerY,
            vx: (Math.random() - 0.5) * 4,
            vy: -Math.random() * 5 - 2,
            life: 60 + Math.random() * 40,
            color: i % 2 === 0 ? '#ffd700' : (color || '#ffffff'),
        });
    }
    window._winnerParticles = particles;
    ctx.save();
    ctx.fillStyle = '#ffd700';
    ctx.font = 'bold 28px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = '#ffd700';
    ctx.shadowBlur = 20;
    ctx.fillText('WINNER', canvas.width / 2, canvas.height / 2 - 30);
    ctx.shadowBlur = 0;
    ctx.restore();
}

function showMatchIntro(ctx, canvas) {
    ctx.save();
    ctx.fillStyle = '#ff3e6c';
    ctx.font = 'bold 40px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = '#ff3e6c';
    ctx.shadowBlur = 30;
    ctx.fillText('FIGHT!', canvas.width / 2, canvas.height / 2);
    ctx.shadowBlur = 0;
    ctx.restore();
}
