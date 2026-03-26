/* Lobby polling and UI — extracted from editor.html for size limits. */

var _pollInterval = null;
var _lobbyTimerMax = null;

function startLobbyPolling() {
    var lobbyEl = document.getElementById('lobby-status');
    var btn = document.getElementById('submit-btn');
    var panel = document.getElementById('lobby-panel');
    btn.disabled = true;
    panel.style.display = 'block';

    _pollInterval = setInterval(function () {
        fetch('/api/lobby/status')
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
            updateLobbyUI(data);
            if (data.match_id) {
                clearInterval(_pollInterval);
                _pollInterval = null;
                showMatchStarting(data.match_id);
            }
        })
        .catch(function () {
            lobbyEl.textContent = 'Lobby: connection lost, retrying...';
        });
    }, 2000);
}

function showMatchStarting(matchId) {
    var lobbyEl = document.getElementById('lobby-status');
    var title = document.getElementById('lobby-title');
    var dots = document.querySelector('.pulse-dots');
    lobbyEl.textContent = 'Match starting!';
    title.textContent = 'Match starting!';
    dots.textContent = '';
    document.body.classList.add('match-starting');
    setTimeout(function () {
        window.location.href = '/viewer?match=' + matchId;
    }, 1500);
}

function updateLobbyUI(data) {
    var lobbyEl = document.getElementById('lobby-status');
    var title = document.getElementById('lobby-title');
    var playersGrid = document.getElementById('lobby-players');
    var fill = document.getElementById('countdown-fill');
    var countdownText = document.getElementById('countdown-text');

    // Header status text
    var statusText = data.players + '/' + data.max + ' players';
    lobbyEl.textContent = statusText;
    lobbyEl.classList.add('active');
    title.textContent = 'Waiting for players (' + data.players + '/' + data.max + ')';

    // Player badges
    playersGrid.innerHTML = '';
    (data.player_list || []).forEach(function (p) {
        var badge = document.createElement('span');
        badge.className = 'lobby-player-badge';
        badge.textContent = p.emoji + ' ' + p.name;
        playersGrid.appendChild(badge);
    });

    // Countdown progress bar
    if (data.time_remaining !== null) {
        if (_lobbyTimerMax === null) {
            _lobbyTimerMax = data.time_remaining;
        }
        var pct = _lobbyTimerMax > 0
            ? ((1 - data.time_remaining / _lobbyTimerMax) * 100)
            : 100;
        fill.style.width = Math.min(100, Math.max(0, pct)) + '%';
        countdownText.textContent = Math.ceil(data.time_remaining) + 's until match';
    } else {
        fill.style.width = '0%';
        countdownText.textContent = 'Waiting for more players...';
    }
}
