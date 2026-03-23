/**
 * effects.js — Particle effects, spectacle effects, screen shake.
 *
 * Contains shatterEffect, deathExplosion, attackSwoosh, applySpectacleEffects,
 * glitchEffect, darkEntranceEffect, skullFlashEffect, pulseWaveEffect,
 * multiballEffect, splitScreenEffect, showBanner.
 */

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

  if (tier === 'heating') {
    grid.style.animation = 'subtle-pulse 2s ease-in-out';
  }

  if (tier === 'intense' || tier === 'hype' || tier === 'chaos') {
    if (triggers.includes('kill') || triggers.includes('kill_streak')) {
      grid.style.animation = 'screen-shake 0.3s ease-in-out';
    }
  }

  if (tier === 'hype' || tier === 'chaos') {
    grid.style.animation = (grid.style.animation ? grid.style.animation + ', ' : '') + 'fire-border 1s ease-in-out infinite';
  }

  if (effects.includes('slow_mo')) {
    grid.style.filter = 'brightness(1.2) saturate(0.5)';
  }

  if (triggers.includes('storm_kill')) {
    glitchEffect();
  }

  if (triggers.includes('watcher_spawn')) {
    darkEntranceEffect();
  }

  if (triggers.includes('near_death')) {
    skullFlashEffect();
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
