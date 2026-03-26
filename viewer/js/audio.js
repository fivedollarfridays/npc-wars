/**
 * audio.js — AudioEngine class for Web Audio API sound playback.
 *
 * Handles stinger loading, playback with spectacle tier volumes,
 * mute/unmute, and master volume control.
 */

class AudioEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.buffers = {};
    this.volume = 0.7;
    this.muted = false;
    this.ready = false;
  }

  init() {
    // Don't create AudioContext yet — browsers require a user gesture
    this.pendingInit = true;
    this._pendingStingers = [];

    // Register one-time user gesture handler
    var self = this;
    var unlock = function() {
      self._createContext();
      document.removeEventListener('click', unlock);
      document.removeEventListener('keydown', unlock);
      document.removeEventListener('touchstart', unlock);
    };
    document.addEventListener('click', unlock, { once: true });
    document.addEventListener('keydown', unlock, { once: true });
    document.addEventListener('touchstart', unlock, { once: true });
  }

  _createContext() {
    if (this.ctx) return; // already created
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      this.masterGain = this.ctx.createGain();
      this.masterGain.connect(this.ctx.destination);
      this.masterGain.gain.value = this.muted ? 0 : this.volume;
      this.ready = true;
      this.pendingInit = false;
      // Load any stingers that were requested before context existed
      this._loadPendingStingers();
      // Hide the "click for sound" indicator
      var indicator = document.getElementById('audio-gesture-hint');
      if (indicator) indicator.style.display = 'none';
    } catch (e) {
      console.warn('Audio not available:', e);
    }
  }

  _loadPendingStingers() {
    var self = this;
    (this._pendingStingers || []).forEach(function(s) {
      self.loadStinger(s.name, s.url);
    });
    this._pendingStingers = [];
  }

  async loadStinger(name, url) {
    if (!this.ctx) {
      // Queue for loading after user gesture unlocks AudioContext
      if (this._pendingStingers) this._pendingStingers.push({ name: name, url: url });
      return;
    }
    try {
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      this.buffers[name] = await this.ctx.decodeAudioData(arrayBuffer);
    } catch (e) {
      // Stinger not available - skip silently
    }
  }

  play(eventType, tier) {
    if (!this.ctx || !this.ready || this.muted) return;
    const buffer = this.buffers[eventType];
    if (!buffer) return;

    const source = this.ctx.createBufferSource();
    const gain = this.ctx.createGain();

    // Viewer volumes are higher than Python TIER_VOLUMES (audio/mixer.py) because
    // browser playback needs more presence than offline video rendering.
    const tierVolumes = { calm: 0.3, heating: 0.5, intense: 0.7, hype: 0.9, chaos: 1.0 };
    gain.gain.value = tierVolumes[tier] || 0.5;

    source.buffer = buffer;
    source.connect(gain);
    gain.connect(this.masterGain);
    source.start(0);
  }

  setMasterVolume(value) {
    this.volume = Math.max(0, Math.min(1, value));
    if (this.masterGain) {
      this.masterGain.gain.value = this.muted ? 0 : this.volume;
    }
  }

  playSynth(type) {
    if (!this.ctx || !this.ready || this.muted) return;
    var ctx = this.ctx;
    var gain = ctx.createGain();
    gain.connect(this.masterGain);

    switch (type) {
      case 'trap_trigger':
        this._synthNoise(gain, 0.05, 0.8);
        this._synthTone(gain, 800, 0.05, 0.5);
        break;
      case 'tactical_activate':
        this._synthSweep(gain, 200, 1200, 0.3, 0.6);
        break;
      case 'ability_damage':
        this._synthTone(gain, 80, 0.15, 0.7);
        this._synthTone(gain, 60, 0.2, 0.5);
        break;
      case 'ability_heal':
        this._synthTone(gain, 523, 0.1, 0.3);
        this._synthTone(gain, 659, 0.1, 0.3, 0.1);
        this._synthTone(gain, 784, 0.1, 0.3, 0.2);
        break;
      case 'ability_shield':
        this._synthTone(gain, 200, 0.3, 0.4);
        break;
      case 'ability_slow':
        this._synthSweep(gain, 600, 200, 0.3, 0.4);
        break;
      case 'crystal_pickup':
        this._synthTone(gain, 1047, 0.05, 0.3);
        this._synthTone(gain, 1319, 0.05, 0.3, 0.05);
        this._synthTone(gain, 1568, 0.05, 0.3, 0.1);
        break;
      case 'evolve':
        this._synthTone(gain, 262, 0.5, 0.4);
        this._synthTone(gain, 330, 0.5, 0.4);
        this._synthTone(gain, 392, 0.5, 0.4);
        break;
    }
  }

  _synthTone(gain, freq, duration, volume, delay) {
    var ctx = this.ctx;
    var osc = ctx.createOscillator();
    var envGain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = freq;
    envGain.gain.setValueAtTime(0, ctx.currentTime + (delay || 0));
    envGain.gain.linearRampToValueAtTime(volume, ctx.currentTime + (delay || 0) + 0.01);
    envGain.gain.linearRampToValueAtTime(0, ctx.currentTime + (delay || 0) + duration);
    osc.connect(envGain);
    envGain.connect(gain);
    osc.start(ctx.currentTime + (delay || 0));
    osc.stop(ctx.currentTime + (delay || 0) + duration + 0.01);
  }

  _synthSweep(gain, startFreq, endFreq, duration, volume) {
    var ctx = this.ctx;
    var osc = ctx.createOscillator();
    var envGain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(startFreq, ctx.currentTime);
    osc.frequency.linearRampToValueAtTime(endFreq, ctx.currentTime + duration);
    envGain.gain.setValueAtTime(volume, ctx.currentTime);
    envGain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration);
    osc.connect(envGain);
    envGain.connect(gain);
    osc.start();
    osc.stop(ctx.currentTime + duration + 0.01);
  }

  _synthNoise(gain, duration, volume) {
    var ctx = this.ctx;
    var bufferSize = ctx.sampleRate * duration;
    var buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * volume;
    }
    var source = ctx.createBufferSource();
    source.buffer = buffer;
    var envGain = ctx.createGain();
    envGain.gain.setValueAtTime(volume, ctx.currentTime);
    envGain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration);
    source.connect(envGain);
    envGain.connect(gain);
    source.start();
  }

  mute() { this.muted = true; if (this.masterGain) this.masterGain.gain.value = 0; }
  unmute() { this.muted = false; if (this.masterGain) this.masterGain.gain.value = this.volume; }
  toggleMute() { this.muted ? this.unmute() : this.mute(); }
}

var audioEngine = new AudioEngine();
