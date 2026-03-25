/**
 * controls.js — Playback controls, zoom, speed buttons.
 *
 * Handles play/pause, scrubbing, speed changes, zoom in/out,
 * winner banner, diff overlay, and permalink.
 */

function togglePlay() {
  if (playing) {
    stopPlay();
  } else {
    startPlay();
  }
}

function startPlay() {
  playing = true;
  document.getElementById('play-btn').textContent = '\u23F8';
  if (currentRound >= matchData.rounds.length - 1) {
    currentRound = 0;
    shownKills.clear();
    document.getElementById('kill-feed').innerHTML = '';
  }
  storePositions(matchData.rounds[currentRound]);
  interpStartTime = performance.now();
  interpDuration = 1000 / speed;
  interpAnimFrame = requestAnimationFrame(playbackLoop);
}

function playbackLoop(now) {
  if (!playing) return;
  var t = (now - interpStartTime) / interpDuration;
  if (t >= 1) {
    // Advance round
    storePositions(matchData.rounds[currentRound]);
    currentRound++;
    if (currentRound >= matchData.rounds.length) {
      stopPlay();
      showWinner();
      return;
    }
    renderRound(currentRound);
    interpStartTime = now;
  } else if (currentRound + 1 < matchData.rounds.length) {
    // Interpolate positions between current and next round
    renderInterpolatedFrame(matchData.rounds[currentRound], matchData.rounds[currentRound + 1], t);
  }
  interpAnimFrame = requestAnimationFrame(playbackLoop);
}

function stopPlay() {
  playing = false;
  document.getElementById('play-btn').textContent = '\u25B6';
  clearInterval(playInterval);
  if (interpAnimFrame) {
    cancelAnimationFrame(interpAnimFrame);
    interpAnimFrame = null;
  }
}

function setSpeed(s) {
  speed = s;
  document.querySelectorAll('.speed-btns button').forEach(function(b) { b.classList.remove('active'); });
  document.getElementById('sp' + s).classList.add('active');
  interpDuration = 1000 / speed;
}

function scrubTo(val) {
  var idx = parseInt(val);
  currentRound = idx;
  // Reset kill feed up to this point
  shownKills.clear();
  document.getElementById('kill-feed').innerHTML = '';
  for (var i = 0; i <= idx; i++) {
    updateKillFeed(matchData.rounds[i]);
  }
  renderRound(idx);
}

function showWinner() {
  var winner = matchData.winner;
  var player = matchData.players.find(function(p) { return p.emoji === winner; });
  document.getElementById('winner-emoji').textContent = winner;
  document.getElementById('winner-name').textContent = player ? player.name : 'Unknown';
  document.getElementById('winner-banner').style.display = 'flex';
  setTimeout(function() { showDiffOverlay(); showResultsOverlay(); }, 1000);
}

function dismissWinner() {
  document.getElementById('winner-banner').style.display = 'none';
}

function showDiffOverlay() {
    if (!matchData || !matchData.diff) return;
    var overlay = document.getElementById('diff-overlay');
    var tbody = document.getElementById('diff-tbody');
    if (!overlay || !tbody) return;
    tbody.innerHTML = '';
    var diffData = matchData.diff;
    for (const [emoji, playerDiff] of Object.entries(diffData)) {
        var headerRow = document.createElement('tr');
        var headerCell = document.createElement('td');
        headerCell.colSpan = 4;
        headerCell.style.cssText = 'font-weight:bold;padding-top:12px;font-size:14px;';
        headerCell.textContent = emoji;
        headerRow.appendChild(headerCell);
        tbody.appendChild(headerRow);
        if (playerDiff.first_match) {
            var fmRow = document.createElement('tr');
            var fmCell = document.createElement('td');
            fmCell.colSpan = 4;
            fmCell.style.cssText = 'color:var(--accent2);font-weight:bold;font-style:italic;font-size:13px;padding:6px 0;';
            fmCell.textContent = 'FIRST MATCH!';
            fmRow.appendChild(fmCell);
            tbody.appendChild(fmRow);
            var fmEntries = Object.entries(playerDiff).filter(function(e) { return e[0] !== 'first_match'; });
            for (var j = 0; j < fmEntries.length; j++) {
                var statName = fmEntries[j][0], statData = fmEntries[j][1];
                var row = document.createElement('tr');
                row.className = 'diff-row-improved';
                row.innerHTML = '<td>' + sanitize(statName) + '</td><td>\u2014</td><td style="color:var(--accent2)">' + (statData.current !== undefined && statData.current !== null ? statData.current.toFixed(1) : '\u2014') + '</td><td>\u2014</td>';
                tbody.appendChild(row);
            }
            continue;
        }
        var entries = Object.entries(playerDiff).filter(function(e) { return e[0] !== 'first_match'; });
        entries.sort(function(a, b) { return Math.abs(b[1].delta || 0) - Math.abs(a[1].delta || 0); });
        for (const [statName, statData] of entries) {
            var row = document.createElement('tr');
            var validClasses = {'improved':1,'regressed':1,'neutral':1};
            var cls = statData.classification in validClasses ? statData.classification : 'neutral';
            row.className = 'diff-row-' + cls;
            var deltaClass = statData.delta > 0 ? 'diff-delta-positive' : statData.delta < 0 ? 'diff-delta-negative' : 'diff-delta-neutral';
            var deltaText = statData.percentage !== null && statData.percentage !== undefined
                ? (statData.percentage >= 0 ? '+' : '') + statData.percentage.toFixed(1) + '%' : '\u2014';
            row.innerHTML = '<td>' + sanitize(statName) + '</td><td>' + (statData.lifetime_avg !== undefined ? statData.lifetime_avg.toFixed(1) : '\u2014') + '</td><td>' + (statData.current !== undefined ? statData.current.toFixed(1) : '\u2014') + '</td><td class="' + deltaClass + '">' + deltaText + '</td>';
            tbody.appendChild(row);
        }
    }
    overlay.style.display = 'block';
    requestAnimationFrame(function() { overlay.classList.add('visible'); });
}

function dismissDiff() {
    var overlay = document.getElementById('diff-overlay');
    if (overlay) {
        overlay.classList.remove('visible');
        setTimeout(function() { overlay.style.display = 'none'; }, 500);
    }
}

function zoomIn() {
  zoomLevel = Math.min(MAX_ZOOM, zoomLevel + ZOOM_STEP);
  applyZoom();
}

function zoomOut() {
  zoomLevel = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoomLevel - ZOOM_STEP));
  applyZoom();
}

function applyZoom() {
  if (!canvas) return;
  canvas.style.transform = 'scale(' + zoomLevel + ')';
  canvas.style.transformOrigin = 'top left';
  var display = document.getElementById('zoom-display');
  if (display) display.textContent = zoomLevel.toFixed(1) + 'x';
}

function copyPermalink() {
  var id = matchData && matchData.match_id != null ? matchData.match_id : '';
  var url = window.location.origin + '/m/' + id;
  navigator.clipboard.writeText(url).then(function() {
    var btn = document.getElementById('copy-link-btn');
    var orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(function() { btn.textContent = orig; }, 1500);
  }).catch(function() {
    window.prompt('Copy this link:', url);
  });
}
