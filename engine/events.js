// Ambient events: the palace's living background. A Poisson-ish scheduler picks
// ONE event at a time from world/events.json, spawns its actor (actors.js) into
// the active space, runs it for a fixed duration with optional fx (light dim /
// fog pull / a particle burst near the keeper), despawns cleanly, then maybe
// chains a sequel. Idle cost is ~0: no geometry and no per-frame work until an
// event is live. Discipline mirrors kinetics.js, update(t, dt) only mutates
// transforms, material params and the ONE shared particle pool buffer; module
// temp state; no allocation while an event runs.

import * as THREE from 'three';
import { ACTORS, POOL_N } from './actors.js';

const PARK_Y = -999;     // unused pool verts sit here, off-screen
const FOG_NEAR = 3, FOG_FAR = 20; // fog_pull targets (lerped toward, restored)

const smooth = (x) => { const c = Math.min(1, Math.max(0, x)); return c * c * (3 - 2 * c); };
const rng = (seed) => { let s = (seed >>> 0) || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 0xffffffff; }; };

// Scratch for a particle burst, base position + velocity per mote. Module-level
// so a burst never allocates; only one burst is ever live at a time.
const _bx = new Float32Array(POOL_N), _by = new Float32Array(POOL_N), _bz = new Float32Array(POOL_N);
const _bvx = new Float32Array(POOL_N), _bvy = new Float32Array(POOL_N), _bvz = new Float32Array(POOL_N);

// A soft round sprite for the pool's points (else they render as hard squares).
// Radial gradient fading to black so it stays round under additive blending.
// Built and cached once, alongside the pool.
let _sprite = null;
function poolSprite() {
  if (_sprite) return _sprite;
  const c = document.createElement('canvas');
  c.width = c.height = 32;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.4, 'rgba(255,255,255,0.55)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 32, 32);
  _sprite = new THREE.CanvasTexture(c);
  _sprite.colorSpace = THREE.SRGBColorSpace;
  return _sprite;
}

// One THREE.Points shared by every event. Lazily created on first use, never
// disposed. Callers park all verts, then overwrite the ones they use.
class ParticlePool {
  constructor(scene) {
    this.n = POOL_N;
    this.arr = new Float32Array(POOL_N * 3);
    this.geo = new THREE.BufferGeometry();
    this.attr = new THREE.BufferAttribute(this.arr, 3);
    this.geo.setAttribute('position', this.attr);
    this.mat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.05, map: poolSprite(),
      transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
    this.points = new THREE.Points(this.geo, this.mat);
    this.points.frustumCulled = false;
    this.points.visible = false;
    scene.add(this.points);
  }
  begin(color, size) {
    this.points.visible = true; this.mat.color.setHex(color); this.mat.size = size;
    for (let i = 1; i < POOL_N * 3; i += 3) this.arr[i] = PARK_Y; // park every vert
  }
  set(i, x, y, z) { const j = i * 3; this.arr[j] = x; this.arr[j + 1] = y; this.arr[j + 2] = z; }
  opacity(v) { this.mat.opacity = v; }
  commit() { this.attr.needsUpdate = true; }
  end() { this.points.visible = false; this.mat.opacity = 0; }
}

export class AmbientEvents {
  constructor({ scene, defs, getContext, toast, onSting }) {
    this.scene = scene;
    this.defs = defs && Array.isArray(defs.events) ? defs.events : [];
    this.byId = new Map(this.defs.map((d) => [d.id, d]));
    this.getContext = getContext;
    this.toast = toast || (() => {});
    this.onSting = onSting || (() => {});   // fire an actor's audio sting on spawn
    this.cooldowns = new Map();  // def id -> earliest elapsed time it may fire again
    this.pool = null;
    this._live = null;           // { def, actor, t, fx, space }
    this._pending = null;        // a queued chain: { id, space, at, deadline }
    this.now = 0;
    const params = new URLSearchParams(location.search);
    this.fast = params.get('events') === 'fast';
    // Deterministic screenshots: no timer under ?debug=1 unless ?events=fast.
    this.enabled = this.fast || !params.has('debug');
    this._timer = this._delay(true);
  }

  get active() { return this._live ? this._live.def.id : null; }

  _delay(first) {
    if (this.fast) return 8 + Math.random() * 7;
    return first ? 10 + Math.random() * 10 : 20 + Math.random() * 20;
  }

  _pool() { if (!this.pool) this.pool = new ParticlePool(this.scene); return this.pool; }

  update(t, dt) {
    this.now = t;
    if (this._live) {
      this._live.t += dt;
      this._step(dt);
      if (this._live.t >= this._live.def.duration_s) this._end();
      return;
    }
    if (this._pending) {                       // a chain waiting for its beat
      if (t > this._pending.deadline) { this._pending = null; }
      else if (t >= this._pending.at) {
        const cur = this.getContext();
        if (cur && cur.paused) return;         // hold until the keeper is free
        const def = this.byId.get(this._pending.id), space = this._pending.space;
        this._pending = null;
        if (def) this._spawn(def, space);      // chains ignore cooldown
        return;
      } else return;
    }
    if (!this.enabled) return;
    this._timer -= dt;
    if (this._timer <= 0) {
      const ctx = this.getContext();
      // Reading an exhibit, an open panel, or a fresh teleport holds events.
      // Don't burn the whole delay on a blocked roll, retry shortly, so the
      // event arrives just after the keeper looks up instead of vanishing.
      if (!ctx || ctx.paused) { this._timer = 0.6; return; }
      this._timer = this._delay(false);
      const list = this._eligible(ctx);
      if (list.length) this._spawn(this._pick(list), ctx);
    }
  }

  // Manual trigger (debug/testing). Bypasses the timer, cooldown and rarity so
  // even chain-only events can be summoned; still blocked while an event is live
  // or the keeper is in a panel.
  spawn(id) {
    if (this._live) return false;
    const def = this.byId.get(id);
    if (!def) return false;
    const ctx = this.getContext();
    if (!ctx || ctx.paused) return false;
    this._spawn(def, ctx);
    return true;
  }

  _eligible(ctx) {
    const out = [];
    for (const d of this.defs) {
      if ((d.rarity || 0) <= 0) continue;                       // chain-only
      const cd = this.cooldowns.get(d.id);
      if (cd !== undefined && this.now < cd) continue;
      if (this._matches(d, ctx)) out.push(d);
    }
    return out;
  }

  _matches(d, ctx) {
    const w = d.where || {};
    if (w.levels && w.levels.length && !w.levels.includes(ctx.level)) return false;
    if (w.wings && w.wings.length && !w.wings.includes(ctx.wing)) return false;
    if (w.kinds && w.kinds.length && !w.kinds.includes(ctx.kind)) return false;
    if (w.concepts && w.concepts.length && !w.concepts.some((c) => ctx.concepts.includes(c))) return false;
    return true;
  }

  _pick(list) {
    let total = 0; for (const d of list) total += d.rarity;
    let r = Math.random() * total;
    for (const d of list) { r -= d.rarity; if (r <= 0) return d; }
    return list[list.length - 1];
  }

  _spawn(def, ctx) {
    const make = ACTORS[def.actor];
    if (!make) return;
    const actor = make({ rect: ctx.rect, h: ctx.h, kind: ctx.kind, pal: ctx.pal,
      camera: ctx.camera, pool: this._pool(), opts: def.opts || {}, duration: def.duration_s });
    this.scene.add(actor.group);
    const fx = { lights: null, fog: null, burst: null }, f = def.fx || {};
    if (f.light_dim != null && ctx.lights && ctx.lights.length)
      fx.lights = { arr: ctx.lights, orig: ctx.lights.map((l) => l.intensity), factor: f.light_dim };
    if (f.fog_pull != null && this.scene.fog)
      fx.fog = { near0: this.scene.fog.near, far0: this.scene.fog.far, amount: f.fog_pull };
    // Pool-using actors own the pool; skip the fx burst to avoid clobbering it.
    if (f.particles && !actor.usesPool) fx.burst = this._initBurst(f.particles, ctx);
    actor.update(0, 0);                          // settle at opacity 0 (no 1-frame pop)
    this._live = { def, actor, t: 0, fx, space: ctx };
    this.cooldowns.set(def.id, this.now + (def.cooldown_s || 0));
    if (def.toast) this.toast(def.toast);
    this.onSting(def.actor);              // the creature's sound arrives with it
  }

  _step(dt) {
    const L = this._live, t = L.t, dur = L.def.duration_s;
    L.actor.update(t, dt);
    const e = smooth(Math.min(1, t / 0.8, Math.max(0, (dur - t) / 0.8)));
    if (L.fx.lights) {
      const { arr, orig, factor } = L.fx.lights;
      for (let i = 0; i < arr.length; i++) arr[i].intensity = orig[i] * (1 - e * (1 - factor));
    }
    if (L.fx.fog) {
      const { near0, far0, amount } = L.fx.fog, a = e * amount;
      this.scene.fog.near = near0 + (FOG_NEAR - near0) * a;
      this.scene.fog.far = far0 + (FOG_FAR - far0) * a;
    }
    if (L.fx.burst) this._stepBurst(L.fx.burst, t, dur, e);
  }

  _end() {
    const L = this._live; this._live = null;
    this.scene.remove(L.actor.group);
    if (L.actor.dispose) L.actor.dispose();
    if (L.fx.lights) { const { arr, orig } = L.fx.lights; for (let i = 0; i < arr.length; i++) arr[i].intensity = orig[i]; }
    if (L.fx.fog) { this.scene.fog.near = L.fx.fog.near0; this.scene.fog.far = L.fx.fog.far0; }
    if (this.pool) this.pool.end();
    const ch = L.def.chains;
    if (ch && this.byId.has(ch.event) && Math.random() < (ch.p == null ? 1 : ch.p))
      this._pending = { id: ch.event, space: L.space, at: this.now + 1.4, deadline: this.now + (ch.within_s || 20) };
  }

  // A particle burst near the keeper: frost falls, dust hangs, sparks rise+fade.
  _initBurst(kind, ctx) {
    const cam = ctx.camera, count = 90, r = rng((cam.position.x * 131 + cam.position.z * 57) | 0);
    for (let i = 0; i < count; i++) {
      const ang = r() * Math.PI * 2;
      if (kind === 'sparks') {
        const rad = r() * 1.2;
        _bx[i] = cam.position.x + Math.cos(ang) * rad; _bz[i] = cam.position.z + Math.sin(ang) * rad;
        _by[i] = 0.6 + r() * 1.0; _bvx[i] = (r() - 0.5) * 0.4; _bvy[i] = 0.5 + r() * 0.8; _bvz[i] = (r() - 0.5) * 0.4;
      } else if (kind === 'dust') {
        const rad = r() * 2.6;
        _bx[i] = cam.position.x + Math.cos(ang) * rad; _bz[i] = cam.position.z + Math.sin(ang) * rad;
        _by[i] = 0.3 + r() * 2.2; _bvx[i] = (r() - 0.5) * 0.2; _bvy[i] = (r() - 0.5) * 0.1; _bvz[i] = (r() - 0.5) * 0.2;
      } else {                                    // frost (default)
        const rad = r() * 2.2;
        _bx[i] = cam.position.x + Math.cos(ang) * rad; _bz[i] = cam.position.z + Math.sin(ang) * rad;
        _by[i] = 1.2 + r() * 2.2; _bvx[i] = (r() - 0.5) * 0.1; _bvy[i] = -0.3 - r() * 0.3; _bvz[i] = (r() - 0.5) * 0.1;
      }
    }
    const color = kind === 'sparks' ? 0xffd98a : kind === 'dust' ? 0xd8c9a8 : 0xdff0ff;
    return { kind, count, color, size: kind === 'sparks' ? 0.06 : 0.05 };
  }

  _stepBurst(b, t, dur, e) {
    const pool = this.pool;
    pool.begin(b.color, b.size);
    for (let i = 0; i < b.count; i++) {
      let x = _bx[i] + _bvx[i] * t, y = _by[i] + _bvy[i] * t, z = _bz[i] + _bvz[i] * t;
      if (b.kind === 'frost') { y = Math.max(0.05, y); x += Math.sin(t * 1.3 + i) * 0.05; }
      pool.set(i, x, y, z);
    }
    const life = b.kind === 'sparks' ? Math.max(0, 1 - t / dur) : 1;
    pool.opacity(0.75 * e * life);
    pool.commit();
  }
}
