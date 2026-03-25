/**
 * results.js — Results overlay shown after match ends.
 *
 * Displays winner, kill feed (last 8), top 5 stats, and action buttons
 * (Play Again, Leaderboard, Watch Again). Must be loaded before app.js.
 */

function showResultsOverlay() {
  if (!matchData) return;
  var overlay = document.getElementById('results-overlay');
  if (!overlay) return;

  // --- Winner section ---
  var winnerDiv = document.getElementById('results-winner');
  if (winnerDiv) {
    var winner = matchData.winner;
    var player = matchData.players.find(function(p) { return p.emoji === winner; });
    var name = player ? player.name : 'Unknown';
    winnerDiv.innerHTML =
      '<div style="font-size:64px;">' + sanitize(winner || '') + '</div>' +
      '<div style="font-family:Silkscreen,cursive;font-size:20px;letter-spacing:3px;' +
        'background:linear-gradient(135deg,var(--accent),var(--accent2));' +
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:8px;">WINNER</div>' +
      '<div style="font-size:16px;margin-top:4px;color:var(--text);">' + sanitize(name) + '</div>';
  }

  // --- Kill feed (last 8 eliminations) ---
  var killsDiv = document.getElementById('results-kills');
  if (killsDiv) {
    var kills = [];
    matchData.rounds.forEach(function(round) {
      round.events.forEach(function(evt) {
        if (evt.type === 'kill') {
          kills.push(evt);
        }
      });
    });
    var last8 = kills.slice(-8);
    var killHtml = last8.map(function(k) {
      return '<div style="padding:3px 0;font-size:12px;color:var(--muted);">' +
        '<span style="color:var(--accent);font-weight:700;">R' + sanitize(String(k.round)) + '</span> ' +
        sanitize(k.attacker || '') + ' \u2192 ' + sanitize(k.victim || '') +
        '</div>';
    }).join('');
    killsDiv.innerHTML = killHtml || '<div style="color:var(--muted);font-size:12px;">No eliminations</div>';
  }

  // --- Top 5 stats ---
  var statsDiv = document.getElementById('results-stats');
  if (statsDiv && matchData.stats) {
    var entries = [];
    Object.keys(matchData.stats).forEach(function(emoji) {
      var s = matchData.stats[emoji];
      var player = matchData.players.find(function(p) { return p.emoji === emoji; });
      entries.push({
        emoji: emoji,
        name: player ? player.name : emoji,
        kills: s.kills || 0,
        damage: s.damage_dealt || 0,
        survived: s.survived_rounds || 0,
        score: s.score || 0,
      });
    });
    entries.sort(function(a, b) { return b.score - a.score; });
    var top5 = entries.slice(0, 5);
    var rows = top5.map(function(e, i) {
      return '<tr style="font-size:12px;">' +
        '<td style="padding:4px 8px;color:var(--muted);">' + (i + 1) + '</td>' +
        '<td style="padding:4px 8px;">' + sanitize(e.emoji) + ' ' + sanitize(e.name) + '</td>' +
        '<td style="padding:4px 8px;text-align:right;color:var(--accent);">' + e.kills + '</td>' +
        '<td style="padding:4px 8px;text-align:right;color:var(--accent2);">' + Math.round(e.damage) + '</td>' +
        '<td style="padding:4px 8px;text-align:right;">' + Math.round(e.score) + '</td>' +
        '</tr>';
    }).join('');
    statsDiv.innerHTML =
      '<table style="width:100%;border-collapse:collapse;">' +
      '<thead><tr style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;">' +
      '<th style="padding:4px 8px;text-align:left;">#</th>' +
      '<th style="padding:4px 8px;text-align:left;">Bot</th>' +
      '<th style="padding:4px 8px;text-align:right;">Kills</th>' +
      '<th style="padding:4px 8px;text-align:right;">Dmg</th>' +
      '<th style="padding:4px 8px;text-align:right;">Score</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>';
  }

  overlay.style.display = 'flex';
}

function hideResultsOverlay() {
  var overlay = document.getElementById('results-overlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

function watchAgain() {
  hideResultsOverlay();
  dismissWinner();
  dismissDiff();
  currentRound = 0;
  shownKills.clear();
  document.getElementById('kill-feed').innerHTML = '';
  renderRound(0);
  startPlay();
}
