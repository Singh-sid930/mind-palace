// Procedural score for the palace — pure synthesis, no audio assets. Every
// voice is the WebAudio translation of a formula worked out and tuned in
// tools/music_lab.py: a breathing harmonic drone, distant FM bells struck on
// {k·φ mod 1}, a 1/f air bed, a subliminal binaural layer that rotates
// calm→focus→alertness, and one sting per ambient-event actor. Everything runs
// on the audio thread; the main loop never touches it. Nothing is created until
// start() is called from a user gesture (browsers require it), and a single
// toggle (persisted) mutes the lot.

const PHI = (1 + Math.sqrt(5)) / 2;
const PENTA = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]; // A-minor pentatonic

// Mix levels (carried over from the approved lab mix; tune here to tune all).
const MIX = {
  master: 0.5,
  drone: 0.34,
  air: 0.10,
  bells: 0.56,
  binaural: 0.17,   // subliminal — works on phase, not loudness
  sting: 0.9,
};
// Binaural rotation: EEG-band targets and how long each is held. Real cadence
// is deliberately slow (entrainment needs sustained exposure).
const BINAURAL = { carrier: 120, states: [6, 10, 16], hold: 180, glide: 30 };

// Per-sting: [peak, lowpass cut, reverb decay, reverb wet]. peak is the relative
// loudness the lab settled on (0.7 = default; quieter for ghost/veil/patronus).
const STING = {
  rat:        [0.7, 4000, 1.2, 0.35],
  ghost:      [0.42, 1400, 2.6, 0.6],
  cat:        [0.7, 1400, 1.6, 0.4],
  owl:        [0.7, 850, 1.5, 0.32],
  snitch:     [0.7, 5000, 1.4, 0.4],
  boggart_chest: [0.7, 1800, 1.8, 0.45],
  draft:      [0.7, 900, 2.0, 0.5],
  rumble:     [0.7, 1200, 2.6, 0.55],
  noise_veil: [0.38, 2600, 2.2, 0.55],
  time_glint: [0.7, 2200, 2.3, 0.55],
  peeves:     [0.7, 2600, 1.6, 0.4],
  dementor:   [0.7, 1400, 2.6, 0.5],
  patronus:   [0.5, 1700, 2.4, 0.55],
};

export class PalaceMusic {
  constructor() {
    this.ctx = null;
    this.started = false;
    this.enabled = localStorage.getItem('palace-music') !== 'off';
    this._bellTimer = null;
    this._noise = {}; // cached noise buffers
  }

  // Called from a user gesture (the Begin click). Idempotent.
  start() {
    if (this.started) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    const c = this.ctx;
    this.master = c.createGain();
    this.master.gain.value = this.enabled ? MIX.master : 0;
    this.master.connect(c.destination);
    // Shared castle reverb: a convolver whose impulse is decaying noise.
    this.verb = c.createConvolver();
    this.verb.buffer = this._reverbIR(2.0);
    this.verb.connect(this.master);
    this.started = true;
    this._startDrone();
    this._startAir();
    this._startBinaural();
    this._scheduleBells();
  }

  setEnabled(on) {
    this.enabled = on;
    localStorage.setItem('palace-music', on ? 'on' : 'off');
    if (this.started) {
      const g = this.master.gain, t = this.ctx.currentTime;
      g.cancelScheduledValues(t);
      g.linearRampToValueAtTime(on ? MIX.master : 0, t + 0.4);
      if (on && this.ctx.state === 'suspended') this.ctx.resume();
    }
    return on;
  }
  toggle() { return this.setEnabled(!this.enabled); }
  resume() { if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume(); }

  // --- shared helpers -------------------------------------------------------
  _noiseBuf(kind, dur) {
    const key = kind + ':' + dur.toFixed(2);
    if (this._noise[key]) return this._noise[key];
    const n = Math.floor(dur * this.ctx.sampleRate);
    const buf = this.ctx.createBuffer(1, n, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    let last = 0;
    for (let i = 0; i < n; i++) {
      const w = Math.random() * 2 - 1;
      if (kind === 'pink' || kind === 'brown') { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; }
      else d[i] = w;
    }
    this._noise[key] = buf;
    return buf;
  }

  _reverbIR(decay) {
    const n = Math.floor(decay * 3 * this.ctx.sampleRate);
    const buf = this.ctx.createBuffer(2, n, this.ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = buf.getChannelData(ch);
      const pre = Math.floor(0.03 * this.ctx.sampleRate);
      for (let i = 0; i < n; i++)
        d[i] = i < pre ? 0 : (Math.random() * 2 - 1) * Math.exp(-i / this.ctx.sampleRate / decay);
    }
    return buf;
  }

  // Route a source through the "heard across the castle" colouring: a low-pass,
  // then a dry/wet split into the shared reverb. Returns nothing (self-wiring).
  _distant(node, out, cut, wet) {
    const c = this.ctx;
    const lp = c.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.value = cut;
    node.connect(lp);
    const dry = c.createGain(); dry.gain.value = (1 - wet) * out; lp.connect(dry); dry.connect(this.master);
    const w = c.createGain(); w.gain.value = wet * out; lp.connect(w); w.connect(this.verb);
  }

  // --- ambient bed ----------------------------------------------------------
  _startDrone() {
    const c = this.ctx, f0 = 55, rates = [0.05, 0.05 / PHI, 0.05 / Math.SQRT2, 0.05 / Math.PI, 0.033, 0.041];
    const bus = c.createGain(); bus.gain.value = MIX.drone; bus.connect(this.master);
    for (let n = 1; n <= 6; n++) {
      const osc = c.createOscillator(); osc.frequency.value = n * f0;
      const g = c.createGain(); g.gain.value = 0.62 / n;
      // AM: a slow LFO at an incommensurate rate breathes this harmonic.
      const lfo = c.createOscillator(); lfo.frequency.value = rates[n - 1];
      const lg = c.createGain(); lg.gain.value = (0.38 / n);
      lfo.connect(lg); lg.connect(g.gain);
      osc.connect(g); g.connect(bus);
      osc.start(); lfo.start();
    }
  }

  _startAir() {
    const c = this.ctx;
    const src = c.createBufferSource();
    src.buffer = this._noiseBuf('pink', 8); src.loop = true;
    const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1400; lp.Q.value = 0.5;
    // Slow brightness LFO on the cutoff (the wandering "air").
    const lfo = c.createOscillator(); lfo.frequency.value = 0.07;
    const lg = c.createGain(); lg.gain.value = 600; lfo.connect(lg); lg.connect(lp.frequency);
    const g = c.createGain(); g.gain.value = MIX.air;
    src.connect(lp); lp.connect(g); g.connect(this.master);
    src.start(); lfo.start();
  }

  _startBinaural() {
    const c = this.ctx, B = BINAURAL, t0 = c.currentTime;
    const g = c.createGain(); g.gain.value = MIX.binaural; g.connect(this.master);
    const oscL = c.createOscillator(), oscR = c.createOscillator();
    oscL.frequency.value = B.carrier;
    const panL = c.createStereoPanner(), panR = c.createStereoPanner();
    panL.pan.value = -1; panR.pan.value = 1;
    oscL.connect(panL); panL.connect(g);
    oscR.connect(panR); panR.connect(g);
    // Schedule the right ear's frequency = carrier + beat, gliding between states.
    // Lay down several full cycles ahead; deterministic, so no re-scheduling loop.
    const fr = oscR.frequency; fr.setValueAtTime(B.carrier + B.states[0], t0);
    let t = t0;
    for (let cyc = 0; cyc < 6; cyc++) {
      for (let s = 0; s < B.states.length; s++) {
        const cur = B.carrier + B.states[s];
        const nxt = B.carrier + B.states[(s + 1) % B.states.length];
        fr.setValueAtTime(cur, t); t += B.hold;
        fr.linearRampToValueAtTime(nxt, t + B.glide); t += B.glide;
      }
    }
    oscL.start(); oscR.start();
  }

  _scheduleBells() {
    // A sparse, ever-changing stream: one distant FM bell every ~3–5s.
    let k = 0;
    const ring = () => {
      if (!this.started) return;
      const note = PENTA[Math.floor(((k * PHI * PHI) % 1) * PENTA.length)];
      this._bell(note, (0.55 + 0.45 * ((k * 7) % 3) / 2));
      k++;
      this._bellTimer = setTimeout(ring, 3000 + Math.random() * 2000);
    };
    this._bellTimer = setTimeout(ring, 1500);
  }

  _bell(f, vel = 1) {
    const c = this.ctx, t = c.currentTime;
    const car = c.createOscillator(); car.frequency.value = f;
    const mod = c.createOscillator(); mod.frequency.value = f * PHI; // golden inharmonicity
    const modG = c.createGain();       // frequency deviation = I(t)·f_m
    const I0 = 2.2 * f * PHI;
    modG.gain.setValueAtTime(I0, t);
    modG.gain.exponentialRampToValueAtTime(I0 * 0.02, t + 1.6);
    mod.connect(modG); modG.connect(car.frequency);
    const amp = c.createGain();
    amp.gain.setValueAtTime(0.0001, t);
    amp.gain.exponentialRampToValueAtTime(0.9 * vel, t + 0.01);
    amp.gain.exponentialRampToValueAtTime(0.0005, t + 2.8);
    car.connect(amp);
    this._distant(amp, MIX.bells, 1200, 0.58);
    car.start(t); mod.start(t); car.stop(t + 3.2); mod.stop(t + 3.2);
  }

  // --- event stings ---------------------------------------------------------
  // Fire the sting for an actor (called by the events scheduler on spawn).
  sting(actor) {
    if (!this.started || !this.enabled) return;
    this.resume();
    const cfg = STING[actor]; if (!cfg) return;
    const [peak, cut, decay, wet] = cfg;
    const out = MIX.sting * (peak / 0.7);
    (this['_st_' + actor] || (() => {})).call(this, out, cut, wet, decay);
  }

  // small builders ----------------------------------------------------------
  _noiseSrc(dur, kind = 'white') {
    const s = this.ctx.createBufferSource();
    s.buffer = this._noiseBuf(kind, Math.max(0.05, dur)); return s;
  }
  // A gaussian-ish swell gain over [0,dur] peaking at `center`.
  _swell(g, t0, dur, center, width, amp) {
    const steps = 24;
    for (let i = 0; i <= steps; i++) {
      const tt = (i / steps) * dur;
      const v = amp * Math.exp(-0.5 * ((tt - center) / width) ** 2);
      g.gain.setValueAtTime(Math.max(0.0001, v), t0 + tt);
    }
  }

  _st_rat(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime;
    const bus = c.createGain(); this._distant(bus, out, cut, wet);
    for (let i = 0; i < 13; i++) {
      const when = t0 + Math.random() * 1.15;
      const s = this._noiseSrc(0.05); const hp = c.createBiquadFilter();
      hp.type = 'highpass'; hp.frequency.value = 2600;
      const g = c.createGain(); g.gain.setValueAtTime(0.7, when);
      g.gain.exponentialRampToValueAtTime(0.001, when + 0.04);
      s.connect(hp); hp.connect(g); g.connect(bus); s.start(when); s.stop(when + 0.05);
    }
  }

  _st_ghost(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 4.5;
    const s = this._noiseSrc(dur); const bp = c.createBiquadFilter();
    bp.type = 'bandpass'; bp.frequency.value = 700; bp.Q.value = 0.7;
    const g = c.createGain(); this._swell(g, t0, dur, 2.25, 1.5, 1);
    const sh = c.createOscillator(); sh.frequency.value = 460;
    const sg = c.createGain(); sg.gain.value = 0.18;
    s.connect(bp); bp.connect(g); sh.connect(sg); sg.connect(g);
    this._distant(g, out, cut, wet);
    s.start(t0); s.stop(t0 + dur); sh.start(t0); sh.stop(t0 + dur);
  }

  _st_cat(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 1.8;
    const o1 = c.createOscillator(); o1.frequency.value = 55;
    const o2 = c.createOscillator(); o2.frequency.value = 110;
    const o2g = c.createGain(); o2g.gain.value = 0.4; o2.connect(o2g);
    const am = c.createGain();     // 25 Hz purr modulation
    const lfo = c.createOscillator(); lfo.frequency.value = 25;
    const lg = c.createGain(); lg.gain.value = 0.5; lfo.connect(lg); lg.connect(am.gain);
    am.gain.value = 0.5;
    const env = c.createGain(); this._swell(env, t0, dur, 0.9, 0.6, 1);
    o1.connect(am); o2g.connect(am); am.connect(env);
    this._distant(env, out, cut, wet);
    [o1, o2, lfo].forEach((o) => { o.start(t0); o.stop(t0 + dur); });
  }

  _st_owl(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime;
    const bus = c.createGain(); this._distant(bus, out, cut, wet);
    for (const start of [0.25, 1.05]) {
      const t = t0 + start;
      const o = c.createOscillator();
      o.frequency.setValueAtTime(300, t); o.frequency.linearRampToValueAtTime(268, t + 0.4);
      const g = c.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.9, t + 0.03);
      g.gain.exponentialRampToValueAtTime(0.002, t + 0.4);
      o.connect(g); g.connect(bus); o.start(t); o.stop(t + 0.42);
    }
  }

  _st_snitch(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 1.6;
    const o = c.createOscillator(); o.frequency.value = 2600;
    // lissajous dart on the carrier frequency
    const l1 = c.createOscillator(); l1.frequency.value = 1.3;
    const g1 = c.createGain(); g1.gain.value = 600; l1.connect(g1); g1.connect(o.frequency);
    const l2 = c.createOscillator(); l2.frequency.value = 2.1;
    const g2 = c.createGain(); g2.gain.value = 300; l2.connect(g2); g2.connect(o.frequency);
    const flut = c.createGain();  // 45 Hz wing flutter
    const fl = c.createOscillator(); fl.frequency.value = 45;
    const flg = c.createGain(); flg.gain.value = 0.5; fl.connect(flg); flg.connect(flut.gain); flut.gain.value = 0.5;
    const env = c.createGain(); this._swell(env, t0, dur, dur / 2, dur / 2.6, 1);
    o.connect(flut); flut.connect(env); this._distant(env, out, cut, wet);
    [o, l1, l2, fl].forEach((x) => { x.start(t0); x.stop(t0 + dur); });
  }

  _st_boggart_chest(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime;
    const bus = c.createGain(); this._distant(bus, out, cut, wet);
    for (let i = 0; i < 8; i++) {           // rattle
      const when = t0 + Math.random() * 1.1;
      const s = this._noiseSrc(0.05); const bp = c.createBiquadFilter();
      bp.type = 'bandpass'; bp.frequency.value = 500; bp.Q.value = 1.2;
      const g = c.createGain(); g.gain.setValueAtTime(0.6, when);
      g.gain.exponentialRampToValueAtTime(0.001, when + 0.05);
      s.connect(bp); bp.connect(g); g.connect(bus); s.start(when); s.stop(when + 0.06);
    }
    const tc = t0 + 1.3, s = this._noiseSrc(0.4);  // crack
    const bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1500; bp.Q.value = 0.7;
    const g = c.createGain(); g.gain.setValueAtTime(1, tc); g.gain.exponentialRampToValueAtTime(0.001, tc + 0.3);
    s.connect(bp); bp.connect(g); g.connect(bus); s.start(tc); s.stop(tc + 0.4);
    const th = c.createOscillator(); th.frequency.value = 70;   // thump
    const tg = c.createGain(); tg.gain.setValueAtTime(0.8, tc + 0.05); tg.gain.exponentialRampToValueAtTime(0.001, tc + 0.5);
    th.connect(tg); tg.connect(bus); th.start(tc + 0.05); th.stop(tc + 0.55);
  }

  _st_draft(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 3.0;
    const s = this._noiseSrc(dur); const lp = c.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.value = 600;
    const g = c.createGain(); this._swell(g, t0, dur, 1.5, 1.0, 1);
    s.connect(lp); lp.connect(g); this._distant(g, out, cut, wet);
    s.start(t0); s.stop(t0 + dur);
  }

  _st_rumble(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 4.0;
    const g = c.createGain(); this._swell(g, t0, dur, 2.0, 1.3, 1);
    const o1 = c.createOscillator(); o1.frequency.value = 32;
    const o2 = c.createOscillator(); o2.frequency.value = 45;
    const og = c.createGain(); og.gain.value = 0.5; o1.connect(og); o2.connect(og); og.connect(g);
    const s = this._noiseSrc(dur); const lp = c.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.value = 200;
    const ng = c.createGain(); ng.gain.value = 0.8; s.connect(lp); lp.connect(ng); ng.connect(g);
    this._distant(g, out, cut, wet);
    o1.start(t0); o2.start(t0); s.start(t0); o1.stop(t0 + dur); o2.stop(t0 + dur); s.stop(t0 + dur);
  }

  _st_noise_veil(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 3.5;
    // hiss fades out as a tone gathers in the middle, then reverses
    const s = this._noiseSrc(dur); const bp = c.createBiquadFilter();
    bp.type = 'bandpass'; bp.frequency.value = 1500; bp.Q.value = 0.6;
    const ng = c.createGain(); this._swell(ng, t0, dur, 0, dur / 2.2, 0.6);  // loud at ends
    // invert: high at ends -> subtract from a constant by summing a negative-center swell is hard;
    // simpler: noise swell peaks at ends via two half-gaussians
    ng.gain.setValueAtTime(0.6, t0);
    ng.gain.linearRampToValueAtTime(0.05, t0 + dur / 2);
    ng.gain.linearRampToValueAtTime(0.6, t0 + dur);
    const o = c.createOscillator(); o.frequency.value = 330;
    const og = c.createGain(); this._swell(og, t0, dur, dur / 2, dur / 5, 0.5);
    s.connect(bp); bp.connect(ng); o.connect(og);
    const mix = c.createGain(); ng.connect(mix); og.connect(mix);
    this._distant(mix, out, cut, wet);
    s.start(t0); s.stop(t0 + dur); o.start(t0); o.stop(t0 + dur);
  }

  _st_time_glint(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime;
    // a bell run BACKWARD: swell up to the strike, then a sparkle
    const car = c.createOscillator(); car.frequency.value = 523.25;
    const mod = c.createOscillator(); mod.frequency.value = 523.25 * PHI;
    const modG = c.createGain(); const I0 = 2.0 * 523.25 * PHI;
    modG.gain.setValueAtTime(I0 * 0.02, t0); modG.gain.linearRampToValueAtTime(I0, t0 + 1.5);
    mod.connect(modG); modG.connect(car.frequency);
    const amp = c.createGain();
    amp.gain.setValueAtTime(0.0005, t0); amp.gain.linearRampToValueAtTime(0.9, t0 + 1.5);
    amp.gain.exponentialRampToValueAtTime(0.001, t0 + 1.7);
    car.connect(amp);
    const sp = c.createOscillator(); sp.frequency.value = 1046.5;
    const sg = c.createGain(); sg.gain.setValueAtTime(0.3, t0 + 1.5); sg.gain.exponentialRampToValueAtTime(0.001, t0 + 2.4);
    sp.connect(sg);
    const bus = c.createGain(); amp.connect(bus); sg.connect(bus);
    this._distant(bus, out, cut, wet);
    car.start(t0); mod.start(t0); sp.start(t0 + 1.5);
    car.stop(t0 + 1.8); mod.stop(t0 + 1.8); sp.stop(t0 + 2.5);
  }

  _st_peeves(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime;
    const bus = c.createGain(); this._distant(bus, out, cut, wet);
    for (let i = 0; i < 20; i++) {          // page riffle
      const when = t0 + Math.random() * 1.5;
      const s = this._noiseSrc(0.02); const hp = c.createBiquadFilter();
      hp.type = 'highpass'; hp.frequency.value = 3000;
      const g = c.createGain(); g.gain.setValueAtTime(0.4, when); g.gain.exponentialRampToValueAtTime(0.001, when + 0.02);
      s.connect(hp); hp.connect(g); g.connect(bus); s.start(when); s.stop(when + 0.025);
    }
    for (const [start, f0] of [[0.6, 400], [1.2, 300]]) {  // book-drops
      const t = t0 + start, o = c.createOscillator();
      o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f0 / 2, t + 0.3);
      const g = c.createGain(); g.gain.setValueAtTime(0.5, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
      o.connect(g); g.connect(bus); o.start(t); o.stop(t + 0.32);
    }
  }

  _st_dementor(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime, dur = 7;
    const g = c.createGain(); this._swell(g, t0, dur, 2.6, 1.5, 1);
    for (const df of [1.0, 1.06, 0.94]) {   // descending minor cluster
      const o = c.createOscillator();
      o.frequency.setValueAtTime(190 * df, t0); o.frequency.exponentialRampToValueAtTime(190 * df * 0.55, t0 + dur);
      const og = c.createGain(); og.gain.value = 0.5; o.connect(og); og.connect(g); o.start(t0); o.stop(t0 + dur);
    }
    const sub = c.createOscillator();
    sub.frequency.setValueAtTime(95, t0); sub.frequency.exponentialRampToValueAtTime(52, t0 + dur);
    const sg = c.createGain(); sg.gain.value = 0.7; sub.connect(sg); sg.connect(g); sub.start(t0); sub.stop(t0 + dur);
    const s = this._noiseSrc(dur); const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 400;
    const ng = c.createGain(); ng.gain.value = 0.8; s.connect(lp); lp.connect(ng); ng.connect(g); s.start(t0); s.stop(t0 + dur);
    this._distant(g, out, cut, wet);
  }

  _st_patronus(out, cut, wet) {
    const c = this.ctx, t0 = c.currentTime;
    const ratios = [1, 5 / 4, 3 / 2, 2, 5 / 2, 3]; // just intonation
    const bus = c.createGain(); this._distant(bus, out, cut, wet);
    ratios.forEach((r, k) => {
      const t = t0 + k * 0.22, f = 523.25 * r;
      const o1 = c.createOscillator(); o1.frequency.value = f;
      const o2 = c.createOscillator(); o2.frequency.value = f * 1.003; // shimmer
      const g = c.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.6, t + 0.01);
      g.gain.exponentialRampToValueAtTime(0.001, t + 1.8);
      o1.connect(g); o2.connect(g); g.connect(bus);
      o1.start(t); o2.start(t); o1.stop(t + 1.9); o2.stop(t + 1.9);
    });
  }
}
