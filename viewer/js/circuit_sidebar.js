/**
 * circuit_sidebar.js — Sidebar panels for Code Circuit races.
 *
 * Shows car standings with positions and lap_time, plus an event feed
 * for overtakes, spins, fastest laps. Game-specific counterpart to sidebar.js.
 */

function buildCircuitCarList() {
  var container = document.getElementById('bot-list');
  container.innerHTML = '';
  emojiIndex = {};
  var players = matchData.players || [];
  players.forEach(function(p, idx) {
    emojiIndex[p.emoji] = idx;
    var row = document.createElement('div');
    row.className = 'bot-row';
    row.id = 'bot-' + idx;
    row.dataset.emoji = p.emoji;

    var color = typeof CAR_COLORS !== 'undefined'
      ? CAR_COLORS[idx % CAR_COLORS.length]
      : 'var(--text)';

    row.innerHTML =
      '<div class="bot-emoji">' + sanitize(p.emoji) + '</div>' +
      '<div class="bot-info">' +
        '<div class="bot-name" style="color:' + color + '">' + sanitize(p.name) + '</div>' +
        '<div class="bot-equip" id="pos-' + idx + '">P' + (idx + 1) + '</div>' +
        '<div class="hp-bar-wrap"><div class="hp-bar" id="hp-' + idx + '" style="width:100%;background:' + color + ';"></div></div>' +
      '</div>' +
      '<div>' +
        '<div class="bot-hp-text" id="hptxt-' + idx + '">--</div>' +
        '<div class="bot-score" id="score-' + idx + '">L0</div>' +
      '</div>';
    container.appendChild(row);
  });
}

function updateCircuitSidebar(round) {
  var positions = (round.positions || []).slice().sort(function(a, b) {
    return (a.position || 99) - (b.position || 99);
  });

  var container = document.getElementById('bot-list');
  positions.forEach(function(pos) {
    var idx = emojiIndex[pos.emoji];
    if (idx === undefined) return;
    var row = document.getElementById('bot-' + idx);
    if (row) container.appendChild(row);

    var posEl = document.getElementById('pos-' + idx);
    if (posEl) posEl.textContent = 'P' + (pos.position || '?');

    var hpTxt = document.getElementById('hptxt-' + idx);
    if (hpTxt) {
      var lt = pos.lap_time;
      hpTxt.textContent = lt != null ? lt.toFixed(1) + 's' : '--';
    }

    var scoreTxt = document.getElementById('score-' + idx);
    if (scoreTxt) scoreTxt.textContent = 'L' + (round.round || 0);
  });
}

var shownCircuitEvents = new Set();

function updateCircuitEvents(round, roundIdx) {
  var feed = document.getElementById('kill-feed');
  if (!feed) return;

  var events = matchData.events || [];
  var roundNum = round.round || roundIdx;

  for (var i = 0; i < events.length; i++) {
    var evt = events[i];
    if (evt.tick > roundNum) break;
    var key = evt.type + '-' + evt.tick + '-' + (evt.cars || []).join(',');
    if (shownCircuitEvents.has(key)) continue;
    shownCircuitEvents.add(key);

    var icon = _eventIcon(evt.type);
    var text = icon + ' ' + (evt.cars || []).join(' vs ') + ' — ' + evt.type;
    var entry = document.createElement('div');
    entry.className = 'kill-entry';
    entry.innerHTML = '<span class="round-num">L' + sanitize(String(evt.tick)) + '</span> ' + sanitize(text);
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
  }
}

function _eventIcon(type) {
  var icons = {
    OVERTAKE: '\u{1F3CE}',
    SPIN: '\u{1F300}',
    FASTEST_LAP: '\u26A1',
    BATTLE: '\u2694',
    SAFETY_CAR: '\u{1F6A8}',
    PIT_STOP: '\u{1F527}',
  };
  return icons[type] || '\u{1F3C1}';
}
