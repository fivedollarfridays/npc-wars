/**
 * sidebar.js — Roster/combatants list, match info updates.
 *
 * Contains buildBotList and updateSidebar functions that manage
 * the sidebar panel showing bot status, HP bars, energy, scores.
 */

// Momentum tier names matching engine/momentum.py
var MOMENTUM_TIER_NAMES = ['', 'Building', 'Rolling', 'Surging', 'Unstoppable', 'Dominant'];

function buildBotList() {
  var container = document.getElementById('bot-list');
  container.innerHTML = '';
  emojiIndex = {};
  matchData.players.forEach(function(p, idx) {
    emojiIndex[p.emoji] = idx;
    var row = document.createElement('div');
    row.className = 'bot-row';
    row.id = 'bot-' + idx;
    row.dataset.emoji = p.emoji;

    // Archetype info from stats
    var stats = (matchData.stats && matchData.stats[p.emoji]) || {};
    var archetype = stats.archetype || 'Balanced';
    var archetypeColor = ARCHETYPE_COLORS[archetype] || ARCHETYPE_COLORS.Balanced;

    // Equipment from stats
    var equip = stats.equipment || {};
    var weapon = equip.weapon || '';
    var armor = equip.armor || '';
    var equipText = [weapon, armor].filter(Boolean).join(' / ') || '';

    // Momentum tier name
    var momentumName = stats.momentum_name || '';

    row.innerHTML =
      '<div class="bot-emoji">' + sanitize(p.emoji) + '</div>' +
      '<div class="bot-info">' +
        '<div class="bot-name" style="color:' + archetypeColor + '">' + sanitize(p.name) + '<span class="archetype-badge" style="background:' + archetypeColor + ';color:#000">' + sanitize(archetype) + '</span></div>' +
        (equipText ? '<div class="bot-equip">' + sanitize(equipText) + '</div>' : '') +
        '<div class="hp-bar-wrap"><div class="hp-bar" id="hp-' + idx + '" style="width:100%;background:var(--heal);"></div></div>' +
        '<div class="energy-bar-wrap"><div class="energy-bar" id="en-' + idx + '" style="width:100%;"></div></div>' +
      '</div>' +
      '<div>' +
        '<div class="bot-hp-text" id="hptxt-' + idx + '">100</div>' +
        '<div class="bot-score" id="score-' + idx + '">0 pts</div>' +
      '</div>';
    container.appendChild(row);
  });
}

function updateSidebar(round) {
  // Sort bot rows: alive first (by score desc), dead at bottom (by elimination round)
  var container = document.getElementById('bot-list');
  var sortedPositions = [].concat(round.positions).sort(function(a, b) {
    if (a.alive && !b.alive) return -1;
    if (!a.alive && b.alive) return 1;
    return (b.score || 0) - (a.score || 0);
  });
  sortedPositions.forEach(function(pos) {
    var idx = emojiIndex[pos.emoji];
    if (idx === undefined) return;
    var row = document.getElementById('bot-' + idx);
    if (row) container.appendChild(row);
  });

  round.positions.forEach(function(pos) {
    var idx = emojiIndex[pos.emoji];
    if (idx === undefined) return;
    var row = document.getElementById('bot-' + idx);
    if (!row) return;

    if (!pos.alive) {
      row.classList.add('dead');
    } else {
      row.classList.remove('dead');
    }

    var hpBar = document.getElementById('hp-' + idx);
    var enBar = document.getElementById('en-' + idx);
    var hpTxt = document.getElementById('hptxt-' + idx);
    var scoreTxt = document.getElementById('score-' + idx);

    if (hpBar) {
      var pct = Math.max(0, pos.hp / 100) * 100;
      hpBar.style.width = pct + '%';
      hpBar.style.background = pct > 50 ? 'var(--heal)' : pct > 25 ? '#ffaa00' : 'var(--kill)';
    }
    if (enBar) {
      enBar.style.width = Math.max(0, pos.energy / 100) * 100 + '%';
    }
    if (hpTxt) {
      hpTxt.textContent = Math.max(0, Math.round(pos.hp));
    }
    if (scoreTxt) {
      var tierName = MOMENTUM_TIER_NAMES[pos.momentum_tier || 0] || '';
      scoreTxt.textContent = Math.round(pos.score || 0) + ' pts' + (tierName ? ' ' + tierName : '');
    }
  });
}
