/**
 * events.js — Event FX rendering and kill feed updates.
 *
 * Handles canvas FX for hits, bumps, traps, abilities, kills, etc.
 * Also manages the kill feed sidebar entries.
 */

var shownKills = new Set();

function renderEventFX(round) {
  round.events.forEach(function(evt) {
    if (evt.type === 'hit') {
      // Find target position
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (target) {
        ctx.fillStyle = 'rgba(255, 62, 62, 0.3)';
        ctx.fillRect(target.x * TILE_SIZE, target.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);

        // Damage number
        ctx.font = '12px "JetBrains Mono", monospace';
        ctx.fillStyle = '#ff3e3e';
        ctx.fillText('-' + evt.damage, target.x * TILE_SIZE + TILE_SIZE / 2, target.y * TILE_SIZE - 2);
        ctx.font = EMOJI_SIZE + 'px serif';

        // Attack swoosh from attacker to target
        var attacker = round.positions.find(function(p) { return p.emoji === evt.attacker; });
        if (attacker) {
          var ax = attacker.x * TILE_SIZE + TILE_SIZE / 2;
          var ay = attacker.y * TILE_SIZE + TILE_SIZE / 2;
          var tx = target.x * TILE_SIZE + TILE_SIZE / 2;
          var ty = target.y * TILE_SIZE + TILE_SIZE / 2;
          attackSwoosh(ax, ay, tx, ty);
        }
      }
    } else if (evt.type === 'bump') {
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (target) {
        var arrow = directionArrow(evt.direction);
        ctx.font = '20px serif';
        ctx.fillStyle = 'rgba(255, 165, 0, 0.9)';
        ctx.fillText(arrow, target.x * TILE_SIZE + TILE_SIZE / 2, target.y * TILE_SIZE + TILE_SIZE / 2);
        ctx.font = EMOJI_SIZE + 'px serif';
      }
    } else if (evt.type === 'wall_splat') {
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (target) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
        ctx.fillRect(target.x * TILE_SIZE, target.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        ctx.font = '12px "JetBrains Mono", monospace';
        ctx.fillStyle = '#ff3e3e';
        ctx.fillText('-' + evt.damage, target.x * TILE_SIZE + TILE_SIZE / 2, target.y * TILE_SIZE - 2);
        ctx.font = EMOJI_SIZE + 'px serif';
      }
    } else if (evt.type === 'storm_bounce') {
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (target) {
        ctx.fillStyle = 'rgba(128, 0, 255, 0.5)';
        ctx.fillRect(target.x * TILE_SIZE, target.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        ctx.font = '12px "JetBrains Mono", monospace';
        ctx.fillStyle = '#aa44ff';
        ctx.fillText('-' + evt.damage, target.x * TILE_SIZE + TILE_SIZE / 2, target.y * TILE_SIZE - 2);
        ctx.font = EMOJI_SIZE + 'px serif';
      }
    } else if (evt.type === 'kill') {
      var victim = round.positions.find(function(p) { return p.emoji === evt.victim; });
      if (victim) {
        var px = victim.x * TILE_SIZE + TILE_SIZE / 2;
        var py = victim.y * TILE_SIZE + TILE_SIZE / 2;
        shatterEffect(px, py, '#ff3e3e');
        deathExplosion(px, py);

        // Kill cam for high-drama kills
        var spectacleTier = round.spectacle ? round.spectacle.tier : 'calm';
        if (spectacleTier === 'intense' || spectacleTier === 'hype' || spectacleTier === 'chaos') {
          triggerKillCam(document.getElementById('arena-canvas'), px, py, 1500);
        }

        // Death animation — use cosmetic death_effect color if equipped
        var victimColor = (typeof ARCHETYPE_COLORS !== 'undefined' && botArchetypes[evt.victim])
          ? ARCHETYPE_COLORS[botArchetypes[evt.victim]] : '#ff4444';
        var victimChar = (typeof characterLookup !== 'undefined') ? characterLookup[evt.victim] : null;
        var victimCosmetics = victimChar ? victimChar.cosmetics : null;
        if (victimCosmetics && victimCosmetics.death_effect) {
          victimColor = victimCosmetics.death_effect.color;
        }
        playDeathAnimation(ctx, px, py, victimColor);
      }
    } else if (evt.type === 'trap_placed') {
      // Small red diamond marker at tile position
      var tx = evt.x * TILE_SIZE + TILE_SIZE / 2;
      var ty = evt.y * TILE_SIZE + TILE_SIZE / 2;
      ctx.globalAlpha = 0.4;
      ctx.fillStyle = '#ff4444';
      ctx.beginPath();
      ctx.moveTo(tx, ty - 6);
      ctx.lineTo(tx + 6, ty);
      ctx.lineTo(tx, ty + 6);
      ctx.lineTo(tx - 6, ty);
      ctx.closePath();
      ctx.fill();
      ctx.globalAlpha = 1.0;
    } else if (evt.type === 'trap_trigger') {
      // Red-orange explosion circle with damage number
      var tx = evt.x * TILE_SIZE + TILE_SIZE / 2;
      var ty = evt.y * TILE_SIZE + TILE_SIZE / 2;
      ctx.fillStyle = '#ff6600';
      ctx.globalAlpha = 0.6;
      ctx.beginPath();
      ctx.arc(tx, ty, TILE_SIZE * 0.6, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1.0;
      ctx.fillStyle = '#ff4444';
      ctx.font = 'bold 12px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('-' + Math.round(evt.damage || 0), tx, ty - TILE_SIZE * 0.4);
      if (window.audioEngine) window.audioEngine.playSynth('trap_trigger');
    } else if (evt.type === 'tactical_activate') {
      // Yellow lightning bolt flash on bot tile
      var bot = round.positions.find(function(p) { return p.emoji === evt.emoji; });
      if (bot) {
        var bx = bot.x * TILE_SIZE + TILE_SIZE / 2;
        var by = bot.y * TILE_SIZE + TILE_SIZE / 2;
        ctx.fillStyle = '#ffdd00';
        ctx.globalAlpha = 0.7;
        ctx.font = (TILE_SIZE * 0.5) + 'px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('\u26A1', bx, by - TILE_SIZE * 0.3);
        ctx.globalAlpha = 1.0;
        if (window.audioEngine) window.audioEngine.playSynth('tactical_activate');
      }
    } else if (evt.type === 'ability_damage') {
      // Purple line from caster toward target
      var caster = round.positions.find(function(p) { return p.emoji === evt.emoji; });
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (caster && target) {
        var cx2 = caster.x * TILE_SIZE + TILE_SIZE / 2;
        var cy2 = caster.y * TILE_SIZE + TILE_SIZE / 2;
        var tx = target.x * TILE_SIZE + TILE_SIZE / 2;
        var ty = target.y * TILE_SIZE + TILE_SIZE / 2;
        ctx.strokeStyle = '#aa44ff';
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.6;
        ctx.shadowColor = '#aa44ff';
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.moveTo(cx2, cy2);
        ctx.lineTo(tx, ty);
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1.0;
        // Damage number on target
        ctx.fillStyle = '#aa44ff';
        ctx.font = 'bold 12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('-' + Math.round(evt.damage || 0), tx, ty - TILE_SIZE * 0.4);
        if (window.audioEngine) window.audioEngine.playSynth('ability_damage');
      }
    } else if (evt.type === 'ability_heal') {
      // Green expanding rings on bot
      var bot = round.positions.find(function(p) { return p.emoji === evt.emoji; });
      if (bot) {
        var bx = bot.x * TILE_SIZE + TILE_SIZE / 2;
        var by = bot.y * TILE_SIZE + TILE_SIZE / 2;
        ctx.strokeStyle = '#00ff88';
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.5;
        ctx.beginPath();
        ctx.arc(bx, by, TILE_SIZE * 0.3, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 0.3;
        ctx.beginPath();
        ctx.arc(bx, by, TILE_SIZE * 0.5, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1.0;
        if (window.audioEngine) window.audioEngine.playSynth('ability_heal');
      }
    } else if (evt.type === 'ability_shield') {
      // Blue circle outline around bot
      var bot = round.positions.find(function(p) { return p.emoji === evt.emoji; });
      if (bot) {
        var bx = bot.x * TILE_SIZE + TILE_SIZE / 2;
        var by = bot.y * TILE_SIZE + TILE_SIZE / 2;
        ctx.strokeStyle = '#4488ff';
        ctx.lineWidth = 3;
        ctx.globalAlpha = 0.6;
        ctx.beginPath();
        ctx.arc(bx, by, TILE_SIZE * 0.45, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1.0;
        if (window.audioEngine) window.audioEngine.playSynth('ability_shield');
      }
    } else if (evt.type === 'ability_slow') {
      // Purple dots trailing from target
      var target = round.positions.find(function(p) { return p.emoji === evt.target; });
      if (target) {
        var tx = target.x * TILE_SIZE + TILE_SIZE / 2;
        var ty = target.y * TILE_SIZE + TILE_SIZE / 2;
        ctx.fillStyle = '#8844cc';
        ctx.globalAlpha = 0.5;
        for (var i = 0; i < 4; i++) {
          var ox = (Math.random() - 0.5) * TILE_SIZE * 0.6;
          var oy = (Math.random() - 0.5) * TILE_SIZE * 0.6;
          ctx.beginPath();
          ctx.arc(tx + ox, ty + oy, 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = 1.0;
        if (window.audioEngine) window.audioEngine.playSynth('ability_slow');
      }
    } else if (evt.type === 'evolve') {
      // Golden starburst expanding from bot
      var bot = round.positions.find(function(p) { return p.emoji === evt.emoji; });
      if (bot) {
        var bx = bot.x * TILE_SIZE + TILE_SIZE / 2;
        var by = bot.y * TILE_SIZE + TILE_SIZE / 2;
        ctx.strokeStyle = '#ffcc00';
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.7;
        var spikes = 8;
        for (var i = 0; i < spikes; i++) {
          var angle = (i / spikes) * Math.PI * 2;
          ctx.beginPath();
          ctx.moveTo(bx, by);
          ctx.lineTo(bx + Math.cos(angle) * TILE_SIZE * 0.5, by + Math.sin(angle) * TILE_SIZE * 0.5);
          ctx.stroke();
        }
        ctx.globalAlpha = 1.0;
        if (window.audioEngine) window.audioEngine.playSynth('evolve');
      }
    } else if (evt.type === 'crystal_pickup') {
      // Magenta sparkle particles at position
      var tx = evt.x * TILE_SIZE + TILE_SIZE / 2;
      var ty = evt.y * TILE_SIZE + TILE_SIZE / 2;
      ctx.fillStyle = '#ff44ff';
      ctx.globalAlpha = 0.6;
      for (var i = 0; i < 5; i++) {
        var ox = (Math.random() - 0.5) * TILE_SIZE * 0.7;
        var oy = (Math.random() - 0.5) * TILE_SIZE * 0.7;
        ctx.beginPath();
        ctx.arc(tx + ox, ty + oy, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1.0;
      if (window.audioEngine) window.audioEngine.playSynth('crystal_pickup');
    } else if (evt.type === 'wall_blocked') {
      // Red flash on wall tile
      ctx.fillStyle = 'rgba(255, 60, 60, 0.4)';
      ctx.fillRect(evt.x * TILE_SIZE, evt.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
    }
  });
}

function updateKillFeed(round) {
  var container = document.getElementById('kill-feed');
  var rn = round.round;

  round.events.forEach(function(evt) {
    if (evt.type === 'kill') {
      var key = evt.round + '-' + evt.victim;
      if (shownKills.has(key)) return;
      shownKills.add(key);

      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      entry.innerHTML = '<span class="round-num">R' + sanitize(String(evt.round)) + '</span> ' + sanitize(evt.attacker) + ' \u2192 ' + sanitize(evt.victim);
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'bump') {
      var key = 'bump-' + rn + '-' + evt.pusher + '-' + evt.target;
      if (shownKills.has(key)) return;
      shownKills.add(key);

      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.pusher + ' bumped ' + evt.target));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'wall_splat') {
      var key = 'wsplat-' + rn + '-' + evt.target;
      if (shownKills.has(key)) return;
      shownKills.add(key);

      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.target + ' wall splat! (-' + evt.damage + ' HP)'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'storm_bounce') {
      var key = 'sbounce-' + rn + '-' + evt.target;
      if (shownKills.has(key)) return;
      shownKills.add(key);

      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.target + ' bounced into storm! (-' + evt.damage + ' HP)'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'trap_trigger') {
      var key = 'trap-' + rn + '-' + evt.victim;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.victim + ' hit trap by ' + evt.owner + ' (-' + Math.round(evt.damage) + ' HP)'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'tactical_activate') {
      var key = 'tact-' + rn + '-' + evt.emoji;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' used ' + (evt.tactical || 'tactical')));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'ability_damage') {
      var key = 'abdmg-' + rn + '-' + evt.emoji + '-' + evt.target;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' ' + (evt.ability || 'ability') + ' \u2192 ' + evt.target + ' (-' + Math.round(evt.damage) + ')'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'ability_heal') {
      var key = 'abheal-' + rn + '-' + evt.emoji;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' healed (+' + Math.round(evt.healed || 0) + ')'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'ability_shield') {
      var key = 'abshld-' + rn + '-' + evt.emoji;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' shielded'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'ability_slow') {
      var key = 'abslow-' + rn + '-' + evt.emoji + '-' + evt.target;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' slowed ' + evt.target));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'evolve') {
      var key = 'evolve-' + rn + '-' + evt.emoji;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' evolved!'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    } else if (evt.type === 'crystal_pickup') {
      var key = 'crystal-' + rn + '-' + evt.emoji;
      if (shownKills.has(key)) return;
      shownKills.add(key);
      var entry = document.createElement('div');
      entry.className = 'kill-entry';
      var span = document.createElement('span');
      span.className = 'round-num';
      span.textContent = 'R' + rn;
      entry.appendChild(span);
      entry.appendChild(document.createTextNode(' ' + evt.emoji + ' picked up crystal (+' + (evt.energy || 0) + ' energy)'));
      container.appendChild(entry);
      container.scrollTop = container.scrollHeight;
    }
  });
}
