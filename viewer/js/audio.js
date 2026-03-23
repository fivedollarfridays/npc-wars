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
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.masterGain = this.ctx.createGain();
      this.masterGain.connect(this.ctx.destination);
      this.masterGain.gain.value = this.volume;
      this.ready = true;
    } catch (e) {
      console.warn('Web Audio not available:', e);
    }
  }

  async loadStinger(name, url) {
    if (!this.ctx) return;
    try {
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      this.buffers[name] = await this.ctx.decodeAudioData(arrayBuffer);
    } catch (e) {
      // Stinger not available - skip silently
    }
  }

  play(eventType, tier) {
    if (!this.ready || this.muted) return;
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

  mute() { this.muted = true; if (this.masterGain) this.masterGain.gain.value = 0; }
  unmute() { this.muted = false; if (this.masterGain) this.masterGain.gain.value = this.volume; }
  toggleMute() { this.muted ? this.unmute() : this.mute(); }
}

var audioEngine = new AudioEngine();
