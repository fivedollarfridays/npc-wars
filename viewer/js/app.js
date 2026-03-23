/**
 * app.js — Global state, initialization, data loading, playback loop.
 *
 * Declares all shared global variables and wires up the viewer.
 * Must be loaded LAST since it depends on all other modules.
 */

// --- Global state ---
var matchData = null;
var currentRound = 0;
var playing = false;
var playInterval = null;
var speed = 1;
var prevPositions = {};
var interpStartTime = 0;
var interpDuration = 1000;
var interpAnimFrame = null;
var TILE_SIZE = 48;
var EMOJI_SIZE = 32;

// Zoom state
var zoomLevel = 1.0;
var MIN_ZOOM = 0.5;
var MAX_ZOOM = 3.0;
var ZOOM_STEP = 0.25;

// Canvas refs
var canvas, ctx;
// Emoji -> numeric index lookup for safe element IDs
var emojiIndex = {};

// --- Utility functions ---

function sanitize(str) {
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function validateMatchPath(path) {
  return /^results\/match_\d{3,}\.json$/.test(path);
}

function directionArrow(dirStr) {
  var arrows = {
    '(1,0)': '→', '(-1,0)': '←', '(0,-1)': '↑', '(0,1)': '↓',
    '(1,-1)': '↗', '(1,1)': '↘', '(-1,1)': '↙', '(-1,-1)': '↖',
  };
  return arrows[dirStr] || '•';
}

function lerp(a, b, t) {
    return a + (b - a) * Math.max(0, Math.min(1, t));
}

function storePositions(round) {
    prevPositions = {};
    round.positions.forEach(function(pos) {
        prevPositions[pos.emoji] = { x: pos.x, y: pos.y };
    });
}

// --- Data loading ---

document.getElementById('file-input').addEventListener('change', function(e) {
  var file = e.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(ev) {
    try {
      matchData = JSON.parse(ev.target.result);
      initViewer();
    } catch(err) {
      alert('Invalid JSON file');
    }
  };
  reader.readAsText(file);
});

function loadDemo() {
  // Check if there's a match file in the URL params
  var params = new URLSearchParams(window.location.search);
  var matchFile = params.get('match');
  if (matchFile && validateMatchPath(matchFile)) {
    fetch(matchFile)
      .then(function(r) { return r.json(); })
      .then(function(data) { matchData = data; initViewer(); })
      .catch(function() { alert('Could not load match file'); });
    return;
  } else if (matchFile) {
    alert('Invalid match file path');
    return;
  }
  alert('No demo match available. Load a JSON file or pass ?match=results/match_001.json');
}

function initViewer() {
  document.getElementById('load-screen').style.display = 'none';
  document.getElementById('app').style.display = 'block';

  canvas = document.getElementById('arena-canvas');
  ctx = canvas.getContext('2d');

  var gridSize = matchData.grid_size;
  // Resize canvas to fit viewport (leave room for sidebar)
  var arenaWrap = canvas.parentElement;
  var maxSize = Math.min(arenaWrap.clientWidth || 600, window.innerHeight - 150);
  TILE_SIZE = Math.floor(maxSize / gridSize);
  TILE_SIZE = Math.max(24, Math.min(TILE_SIZE, 64));  // clamp 24-64px
  canvas.width = gridSize * TILE_SIZE;
  canvas.height = gridSize * TILE_SIZE;

  var mapName = matchData.map || 'arena';
  document.getElementById('match-info').textContent =
    'Match #' + matchData.match_id + ' \u2014 ' + matchData.players.length + ' bots \u2014 ' + mapName + ' \u2014 ' + matchData.duration_rounds + ' rounds';

  var scrubber = document.getElementById('scrubber');
  scrubber.max = matchData.rounds.length - 1;
  scrubber.value = 0;

  // Initialize audio
  audioEngine.init();
  var stingerNames = [
    'bump', 'chain_bump', 'critical_hit', 'hit', 'human_enter',
    'kill', 'kill_streak', 'match_end', 'near_death', 'rest_heal',
    'storm_damage', 'wall_splat', 'watcher_spawn'
  ];
  stingerNames.forEach(function(name) {
    audioEngine.loadStinger(name, '../audio/assets/' + name + '.wav');
  });

  // Restore volume from localStorage
  var savedVolume = localStorage.getItem('npc-wars-volume');
  if (savedVolume !== null) {
    var vol = parseInt(savedVolume);
    audioEngine.setMasterVolume(vol / 100);
    document.getElementById('volume-slider').value = vol;
  }

  // Build bot list and archetype lookup
  buildBotList();
  buildArchetypeLookup();

  // Mousewheel zoom
  canvas.addEventListener('wheel', function(e) {
    e.preventDefault();
    if (e.deltaY < 0) zoomIn();
    else zoomOut();
  }, { passive: false });

  // Render first frame
  currentRound = 0;
  renderRound(0);
}

// --- Audio controls wiring ---

document.getElementById('volume-slider').addEventListener('input', function(e) {
  audioEngine.setMasterVolume(e.target.value / 100);
  localStorage.setItem('npc-wars-volume', e.target.value);
});
document.getElementById('mute-btn').addEventListener('click', function() {
  audioEngine.toggleMute();
  document.getElementById('mute-btn').textContent = audioEngine.muted ? '\u{1F507}' : '\u{1F50A}';
});

// --- Auto-load from URL param ---

window.addEventListener('load', function() {
  var params = new URLSearchParams(window.location.search);
  var matchFile = params.get('match');
  if (matchFile && validateMatchPath(matchFile)) {
    fetch(matchFile)
      .then(function(r) { return r.json(); })
      .then(function(data) { matchData = data; initViewer(); })
      .catch(function(err) { console.error('Failed to load match:', err); });
    return;
  }
  // Auto-start live mode from URL param
  var liveParam = params.get('live');
  if (liveParam) {
    startLiveFromLoadScreen();
  }
});
