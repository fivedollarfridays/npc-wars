/**
 * code_overlay.js — Decision trace overlay panel (T65.3).
 *
 * Collapsible panel showing bot decision traces alongside replay.
 * Per-bot toggling, active branch highlighting, round-sync updates.
 */

// Track which bots have trace display enabled
var traceEnabledBots = {};
var codeOverlayVisible = true;

function toggleCodeOverlay() {
  var panel = document.getElementById('code-overlay');
  if (!panel) return;
  codeOverlayVisible = !codeOverlayVisible;
  panel.classList.toggle('collapsed', !codeOverlayVisible);
  var btn = document.getElementById('code-overlay-toggle');
  if (btn) btn.textContent = codeOverlayVisible ? 'Code ▼' : 'Code ▶';
}

function toggleBotTrace(emoji) {
  traceEnabledBots[emoji] = !traceEnabledBots[emoji];
  var idx = emojiIndex[emoji];
  if (idx !== undefined) {
    var btn = document.getElementById('trace-toggle-' + idx);
    if (btn) btn.classList.toggle('active', traceEnabledBots[emoji]);
  }
  updateCodeOverlay(currentRound);
}

function hasTraceData() {
  if (!matchData || !matchData.rounds) return false;
  return matchData.rounds.some(function(r) { return r.decision_traces; });
}

function buildTraceToggles() {
  if (!matchData || !matchData.players) return;
  var container = document.getElementById('trace-bot-toggles');
  if (!container) return;
  container.innerHTML = '';
  var anyTraced = false;

  matchData.players.forEach(function(p) {
    var hasTrace = matchData.rounds.some(function(r) {
      return r.decision_traces && r.decision_traces[p.emoji];
    });
    if (!hasTrace) return;
    anyTraced = true;
    traceEnabledBots[p.emoji] = true;

    var idx = emojiIndex[p.emoji];
    var btn = document.createElement('button');
    btn.className = 'trace-toggle active';
    btn.id = 'trace-toggle-' + idx;
    btn.textContent = p.emoji + ' ' + p.name;
    btn.onclick = function() { toggleBotTrace(p.emoji); };
    container.appendChild(btn);
  });

  return anyTraced;
}

function renderDecisionTrace(emoji, trace) {
  var html = '<div class="trace-bot-header">' + sanitize(emoji) + '</div>';
  if (!trace || !trace.conditions_checked) {
    html += '<div class="trace-inactive">No trace this round</div>';
    return html;
  }

  var branchTaken = trace.branch_taken || 'default';
  trace.conditions_checked.forEach(function(cond) {
    var isActive = cond === branchTaken;
    var cls = isActive ? 'trace-active' : 'trace-inactive';
    var marker = isActive ? '→' : ' ';
    html += '<div class="trace-line ' + cls + '">' +
      '<span class="trace-marker">' + marker + '</span>' +
      '<span class="trace-cond">IF ' + sanitize(cond) + '</span>' +
      '</div>';
  });

  if (branchTaken === 'default') {
    html += '<div class="trace-line trace-active">' +
      '<span class="trace-marker">→</span>' +
      '<span class="trace-cond">DEFAULT (else)</span></div>';
  }

  var snap = trace.state_snapshot;
  if (snap) {
    html += '<div class="trace-state">' +
      'HP:' + snap.hp + ' EN:' + snap.energy +
      ' Enemies:' + snap.enemies_alive + '</div>';
  }
  return html;
}

function updateCodeOverlay(roundIdx) {
  var panel = document.getElementById('code-overlay');
  if (!panel) return;

  if (!hasTraceData()) {
    panel.style.display = 'none';
    return;
  }
  panel.style.display = '';

  var content = document.getElementById('trace-content');
  if (!content) return;

  var round = matchData.rounds[roundIdx];
  if (!round) { content.innerHTML = ''; return; }

  var traces = round.decision_traces || {};
  var parts = [];

  matchData.players.forEach(function(p) {
    if (!traceEnabledBots[p.emoji]) return;
    var trace = traces[p.emoji] || null;
    parts.push(renderDecisionTrace(p.emoji, trace));
  });

  content.innerHTML = parts.join('');
}

function initCodeOverlay() {
  if (!hasTraceData()) {
    var panel = document.getElementById('code-overlay');
    if (panel) panel.style.display = 'none';
    return;
  }
  buildTraceToggles();
}
