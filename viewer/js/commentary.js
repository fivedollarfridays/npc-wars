/**
 * commentary.js — Text ticker that displays commentary lines during replay.
 *
 * Reads from matchData.commentary (array of {timestamp, text, tone, line_type}).
 * Play-by-play lines render in white, color commentary in gold.
 * Auto-advances with round playback; manual scrubbing updates commentary.
 * Fades in/out with round transitions. Toggleable via controls.
 */

var commentaryVisible = true;
var commentaryLines = [];
var currentCommentaryIdx = -1;

function initCommentary() {
  if (!matchData || !matchData.commentary) {
    commentaryLines = [];
    return;
  }
  commentaryLines = matchData.commentary;
  currentCommentaryIdx = -1;
  var ticker = document.getElementById('commentary-ticker');
  if (ticker) {
    ticker.style.display = commentaryVisible ? 'block' : 'none';
    ticker.innerHTML = '';
  }
}

function updateCommentary(roundIdx) {
  var ticker = document.getElementById('commentary-ticker');
  if (!ticker || !commentaryVisible) return;
  if (!commentaryLines || commentaryLines.length === 0) {
    ticker.innerHTML = '';
    return;
  }

  var roundNum = matchData.rounds[roundIdx] ? matchData.rounds[roundIdx].round : roundIdx;
  var lines = [];
  for (var i = 0; i < commentaryLines.length; i++) {
    if (commentaryLines[i].timestamp <= roundNum) {
      lines.push(commentaryLines[i]);
    }
  }

  if (lines.length === 0) {
    ticker.style.opacity = '0';
    return;
  }

  var latest = lines[lines.length - 1];
  var latestIdx = commentaryLines.indexOf(latest);
  if (latestIdx === currentCommentaryIdx) return;
  currentCommentaryIdx = latestIdx;

  ticker.style.opacity = '0';
  setTimeout(function() {
    var start = Math.max(0, lines.length - 3);
    var html = '';
    for (var j = start; j < lines.length; j++) {
      var line = lines[j];
      var cls = line.line_type === 'play_by_play' ? 'commentary-pbp' : 'commentary-color';
      html += '<div class="commentary-line ' + cls + '">' + sanitize(line.text) + '</div>';
    }
    ticker.innerHTML = html;
    ticker.style.opacity = '1';
  }, 150);
}

function toggleCommentary() {
  commentaryVisible = !commentaryVisible;
  var ticker = document.getElementById('commentary-ticker');
  var btn = document.getElementById('commentary-toggle');
  if (ticker) {
    ticker.style.display = commentaryVisible ? 'block' : 'none';
  }
  if (btn) {
    btn.classList.toggle('active', commentaryVisible);
  }
}
