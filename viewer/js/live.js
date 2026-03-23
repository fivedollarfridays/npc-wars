/**
 * live.js — WebSocket live play mode.
 *
 * Handles connecting to a WebSocket server for real-time play,
 * sending actions, countdown timers, keyboard shortcuts,
 * and live round rendering.
 */

var liveMode = false;
var liveWs = null;
var liveActionSent = false;
var liveCountdownTimer = null;
var liveReconnectAttempted = false;
var liveGridSize = 10;

function startLiveFromLoadScreen() {
  var params = new URLSearchParams(window.location.search);
  var liveParam = params.get('live');
  var url = 'ws://localhost:8765';
  if (liveParam) {
    url = 'ws://' + liveParam;
  } else {
    var input = prompt('WebSocket server URL:', url);
    if (!input) return;
    url = input;
  }
  // Show app with empty state
  document.getElementById('load-screen').style.display = 'none';
  document.getElementById('app').style.display = 'block';
  canvas = document.getElementById('arena-canvas');
  ctx = canvas.getContext('2d');
  canvas.width = liveGridSize * TILE_SIZE;
  canvas.height = liveGridSize * TILE_SIZE;
  document.getElementById('match-info').textContent = 'Live Play -- connecting...';
  audioEngine.init();
  connectLive(url);
}

function startLiveMode() {
  var params = new URLSearchParams(window.location.search);
  var liveParam = params.get('live');
  var url = 'ws://localhost:8765';
  if (liveParam) {
    url = 'ws://' + liveParam;
  } else {
    var input = prompt('WebSocket server URL:', url);
    if (!input) return;
    url = input;
  }
  connectLive(url);
}

function connectLive(url) {
  if (liveWs) {
    liveWs.close();
    liveWs = null;
  }

  liveMode = true;
  liveActionSent = false;
  setLiveStatus('Connecting...', false);
  showLiveUI(true);

  liveWs = new WebSocket(url);

  liveWs.onopen = function() {
    setLiveStatus('Connected - waiting for round...', true);
    liveReconnectAttempted = false;
  };

  liveWs.onmessage = function(event) {
    var data;
    try { data = JSON.parse(event.data); } catch(e) { return; }
    if (data.type === 'state' && data.state) {
      handleLiveState(data.state);
    }
  };

  liveWs.onclose = function() {
    setLiveStatus('Disconnected', false);
    setActionButtonsEnabled(false);
    clearLiveCountdown();
    // Auto-reconnect once after 1s
    if (!liveReconnectAttempted) {
      liveReconnectAttempted = true;
      setTimeout(function() {
        if (liveMode && (!liveWs || liveWs.readyState === WebSocket.CLOSED)) {
          setLiveStatus('Reconnecting...', false);
          connectLive(url);
        }
      }, 1000);
    } else {
      showLiveUI(false);
      liveMode = false;
    }
  };

  liveWs.onerror = function() {
    // onclose will fire after this
  };
}

function handleLiveState(state) {
  // Render the state on the canvas
  var gridSize = state.grid_size || liveGridSize;
  liveGridSize = gridSize;

  if (canvas.width !== gridSize * TILE_SIZE) {
    canvas.width = gridSize * TILE_SIZE;
    canvas.height = gridSize * TILE_SIZE;
  }

  // Build a round-like object for renderRound compatibility
  var round = {
    round: state.round || 0,
    storm_border: state.storm_border || 0,
    positions: state.positions || [],
    events: state.events || [],
    spectacle: state.spectacle || null,
  };

  // Update match info
  document.getElementById('match-info').textContent =
    'Live Play -- Round ' + round.round;
  document.getElementById('round-display').textContent = 'R' + round.round;

  // Build bot list if needed (first state or player change)
  if (state.players) {
    matchData = { players: state.players, grid_size: gridSize, rounds: [] };
    buildBotList();
  }

  // Render using existing canvas logic
  renderLiveRound(round, gridSize);

  // Update sidebar
  updateSidebar(round);

  // Enable actions for this round
  liveActionSent = false;
  setActionButtonsEnabled(true);
  setLiveStatus('Your turn! Choose an action', true);
  startLiveCountdown(2);
}

function renderLiveRound(round, gridSize) {
  var stormBorder = round.storm_border;

  ctx.fillStyle = '#0d0d18';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Storm overlay
  if (stormBorder > 0) {
    ctx.fillStyle = 'rgba(80, 0, 140, 0.35)';
    ctx.fillRect(0, 0, canvas.width, stormBorder * TILE_SIZE);
    ctx.fillRect(0, (gridSize - stormBorder) * TILE_SIZE, canvas.width, stormBorder * TILE_SIZE);
    ctx.fillRect(0, stormBorder * TILE_SIZE, stormBorder * TILE_SIZE, (gridSize - 2 * stormBorder) * TILE_SIZE);
    ctx.fillRect((gridSize - stormBorder) * TILE_SIZE, stormBorder * TILE_SIZE, stormBorder * TILE_SIZE, (gridSize - 2 * stormBorder) * TILE_SIZE);
    ctx.strokeStyle = 'rgba(139, 0, 255, 0.6)';
    ctx.lineWidth = 2;
    ctx.strokeRect(
      stormBorder * TILE_SIZE, stormBorder * TILE_SIZE,
      (gridSize - 2 * stormBorder) * TILE_SIZE, (gridSize - 2 * stormBorder) * TILE_SIZE
    );
  }

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.03)';
  ctx.lineWidth = 1;
  for (var i = 0; i <= gridSize; i++) {
    ctx.beginPath(); ctx.moveTo(i * TILE_SIZE, 0); ctx.lineTo(i * TILE_SIZE, canvas.height); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * TILE_SIZE); ctx.lineTo(canvas.width, i * TILE_SIZE); ctx.stroke();
  }

  // Draw bots
  var BASE_RADIUS = 14;

  round.positions.forEach(function(pos) {
    var px = pos.x * TILE_SIZE + TILE_SIZE / 2;
    var py = pos.y * TILE_SIZE + TILE_SIZE / 2;
    var archetype = botArchetypes[pos.emoji] || null;
    var hasArchetype = archetype !== null;
    var radius = BASE_RADIUS;

    if (!pos.alive) {
      if (hasArchetype) {
        drawDeadBot(ctx, px, py, archetype, radius);
      } else {
        ctx.font = EMOJI_SIZE + 'px serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.globalAlpha = 0.2;
        ctx.fillText('\u{1F480}', px, py - 2);
        ctx.globalAlpha = 1;
      }
      return;
    }

    // Highlight human bot
    if (pos.is_human) {
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.6)';
      ctx.lineWidth = 2;
      ctx.strokeRect(pos.x * TILE_SIZE + 1, pos.y * TILE_SIZE + 1, TILE_SIZE - 2, TILE_SIZE - 2);
    }

    // Momentum aura glow
    var mTier = pos.momentum_tier || 0;
    var isLeader = pos.is_leader || false;
    drawMomentumAura(ctx, px, py, radius, mTier, isLeader);

    if (hasArchetype) {
      var maxHp = pos.max_hp || 100;
      var hpPct = Math.max(0, pos.hp / maxHp);
      drawBotShape(ctx, px, py, archetype, hpPct, radius);
    } else {
      ctx.font = EMOJI_SIZE + 'px serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(pos.emoji, px, py - 4);
    }

    // HP bar
    var barWidth = TILE_SIZE - 8;
    var barHeight = 3;
    var barX = pos.x * TILE_SIZE + 4;
    var barY = pos.y * TILE_SIZE + TILE_SIZE - 8;
    var maxHpBar = pos.max_hp || 100;
    var hpPct2 = Math.max(0, pos.hp / maxHpBar);
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.fillRect(barX, barY, barWidth, barHeight);
    var hpColor = hpPct2 > 0.5 ? '#00ff88' : hpPct2 > 0.25 ? '#ffaa00' : '#ff3e3e';
    ctx.fillStyle = hpColor;
    ctx.fillRect(barX, barY, barWidth * hpPct2, barHeight);
  });

  // Draw events
  round.events.forEach(function(evt) {
    if (evt.type === 'hit') {
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (target) {
        ctx.fillStyle = 'rgba(255, 62, 62, 0.3)';
        ctx.fillRect(target.x * TILE_SIZE, target.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        ctx.font = '12px "JetBrains Mono", monospace';
        ctx.fillStyle = '#ff3e3e';
        ctx.fillText('-' + evt.damage, target.x * TILE_SIZE + TILE_SIZE / 2, target.y * TILE_SIZE - 2);
        ctx.font = EMOJI_SIZE + 'px serif';
      }
    }
  });
}

function sendLiveAction(type, direction) {
  if (!liveWs || liveWs.readyState !== WebSocket.OPEN || liveActionSent) return;
  liveActionSent = true;
  var action = direction ? [type, direction] : [type];
  liveWs.send(JSON.stringify({ action: action }));
  setActionButtonsEnabled(false);
  clearLiveCountdown();
  document.getElementById('action-countdown').textContent = 'Action sent!';
  setLiveStatus('Action sent -- waiting for next round...', true);
}

function setActionButtonsEnabled(enabled) {
  document.querySelectorAll('.action-panel .action-btn').forEach(function(btn) {
    btn.disabled = !enabled;
  });
}

function startLiveCountdown(seconds) {
  clearLiveCountdown();
  var remaining = seconds;
  var el = document.getElementById('action-countdown');
  el.textContent = remaining + 's remaining';
  liveCountdownTimer = setInterval(function() {
    remaining--;
    if (remaining <= 0) {
      clearLiveCountdown();
      if (!liveActionSent) {
        el.textContent = 'Bot deciding...';
        setActionButtonsEnabled(false);
        setLiveStatus('Timeout -- bot deciding...', true);
      }
    } else {
      el.textContent = remaining + 's remaining';
    }
  }, 1000);
}

function clearLiveCountdown() {
  if (liveCountdownTimer) {
    clearInterval(liveCountdownTimer);
    liveCountdownTimer = null;
  }
}

function setLiveStatus(text, connected) {
  var bar = document.getElementById('live-status');
  bar.style.display = 'flex';
  document.getElementById('live-status-text').textContent = text;
  var dot = document.getElementById('live-dot');
  if (connected) {
    dot.classList.add('connected');
  } else {
    dot.classList.remove('connected');
  }
}

function showLiveUI(show) {
  // Toggle action panel
  var panel = document.getElementById('action-panel');
  if (show) {
    panel.classList.add('visible');
  } else {
    panel.classList.remove('visible');
  }

  // Toggle replay controls visibility
  var replayEls = ['play-btn', 'scrubber', 'sp1', 'sp2', 'sp4'];
  replayEls.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.style.display = show ? 'none' : '';
  });

  // Hide/show live status bar
  document.getElementById('live-status').style.display = show ? 'flex' : 'none';

  // Live play button state
  var btn = document.getElementById('live-play-btn');
  if (btn) {
    btn.textContent = show ? 'Disconnect' : 'Live Play';
    btn.onclick = show ? disconnectLive : startLiveMode;
  }
}

function disconnectLive() {
  liveMode = false;
  if (liveWs) {
    liveReconnectAttempted = true; // prevent auto-reconnect
    liveWs.close();
    liveWs = null;
  }
  showLiveUI(false);
  clearLiveCountdown();
  document.getElementById('live-status').style.display = 'none';
}

// Keyboard shortcuts for live mode
document.addEventListener('keydown', function(e) {
  if (!liveMode || liveActionSent) return;
  // Ignore if focused on an input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

  switch(e.key) {
    case 'ArrowUp':    sendLiveAction('move', 'north'); e.preventDefault(); break;
    case 'ArrowDown':  sendLiveAction('move', 'south'); e.preventDefault(); break;
    case 'ArrowLeft':  sendLiveAction('move', 'west');  e.preventDefault(); break;
    case 'ArrowRight': sendLiveAction('move', 'east');  e.preventDefault(); break;
    case 'w': case 'W': sendLiveAction('attack', 'north'); break;
    case 's': case 'S': sendLiveAction('attack', 'south'); break;
    case 'a': case 'A': sendLiveAction('attack', 'west');  break;
    case 'd': case 'D': sendLiveAction('attack', 'east');  break;
    case 'r': case 'R': sendLiveAction('rest');    break;
    case 'f': case 'F': sendLiveAction('defend');  break;
  }
});
