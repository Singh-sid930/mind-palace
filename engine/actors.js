// Ambient-event actors: the palace's fleeting inhabitants, a rat along the
// baseboards, the Grey Lady drifting through a wall, an owl on post, a dementor
// gliding the ceiling. Each is a factory (ctx) => { group, update, dispose },
// spawned by the scheduler (events.js) into the active space and torn down after
// a fixed duration. Discipline mirrors kinetics.js: update(t, dt) only mutates
// transforms / material params / the shared particle pool; module temp vectors;
// zero allocation inside update. Actors fade themselves in/out (~0.8s) so a
// despawn never pops.
//
// Geometries and materials are cached at module scope (CACHE) and reused across
// spawns, never disposed. At most ONE event is live, so mutating a shared
// material's opacity per-spawn is safe. Budget: ~40 low-poly geometries + ~30
// tiny materials, well under 1 MB. Per-spawn meshes are just removed with the
// group; the cached geometry/material behind them lives on.

import * as THREE from 'three';

const CACHE = new Map();
const cache = (k, fn) => { let v = CACHE.get(k); if (v === undefined) { v = fn(); CACHE.set(k, v); } return v; };
const geo = (k, fn) => cache('g:' + k, fn);
const M = (k, fn) => cache('m:' + k, fn);
const tbas = (k, color, extra = {}) => M(k, () => new THREE.MeshBasicMaterial({ color, transparent: true, ...extra }));
const tlam = (k, color, extra = {}) => M(k, () => new THREE.MeshLambertMaterial({ color, transparent: true, ...extra }));
const mesh = (gk, gf, m) => new THREE.Mesh(geo(gk, gf), m);

const smooth = (x) => { const c = Math.min(1, Math.max(0, x)); return c * c * (3 - 2 * c); };
const envelope = (t, dur) => smooth(Math.min(1, t / 0.8, Math.max(0, (dur - t) / 0.8)));
const fade = (mats, e) => { for (const it of mats) it.m.opacity = it.base * e; };
const wrap = (v, m) => ((v % m) + m) % m;

// Module temp vectors, no allocation inside update().
const _v = new THREE.Vector3(), _w = new THREE.Vector3(), _look = new THREE.Vector3();
// Size of the shared particle pool (events.js builds its Points from this too,
// so actor scratch and pool can never drift apart).
export const POOL_N = 220;
// Shared scratch for the pool-driven actors (draft/rumble/noise_veil/time_glint).
// Only one event is live at a time, so a single set of buffers is enough.
const _px = new Float32Array(POOL_N), _py = new Float32Array(POOL_N), _pz = new Float32Array(POOL_N), _pk = new Float32Array(POOL_N);

// Deterministic little RNG so a spawn's randomness is stable across its life.
function rng(seed) { let s = (seed >>> 0) || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 0xffffffff; }; }
const gauss = (r) => (r() + r() + r() + r() - 2); // ~N(0, ~0.58), bounded to [-2, 2]

// Perimeter walk: point + facing yaw at arclength s around an inset rectangle.
// Writes into a module scratch (called per frame, no allocation allowed).
const _per = { x: 0, z: 0, a: 0 };
function perimeter(s, x0, x1, z0, z1) {
  const wx = x1 - x0, wz = z1 - z0;
  if (s < wx) { _per.x = x0 + s; _per.z = z0; _per.a = Math.PI / 2; return _per; } s -= wx;
  if (s < wz) { _per.x = x1; _per.z = z0 + s; _per.a = 0; return _per; } s -= wz;
  if (s < wx) { _per.x = x1 - s; _per.z = z1; _per.a = -Math.PI / 2; return _per; } s -= wx;
  _per.x = x0; _per.z = z1 - s; _per.a = Math.PI;
  return _per;
}

// The wall furthest from the player (so a sitter reads on screen), inset a touch.
function nearWall(rect, camera, inset) {
  const dxMin = Math.abs(camera.position.x - rect.minX), dxMax = Math.abs(camera.position.x - rect.maxX);
  const dzMin = Math.abs(camera.position.z - rect.minZ), dzMax = Math.abs(camera.position.z - rect.maxZ);
  const m = Math.max(dxMin, dxMax, dzMin, dzMax);
  if (m === dxMin) return { x: rect.minX + inset, z: rect.cz };
  if (m === dxMax) return { x: rect.maxX - inset, z: rect.cz };
  if (m === dzMin) return { x: rect.cx, z: rect.minZ + inset };
  return { x: rect.cx, z: rect.maxZ - inset };
}

// The room's longer axis, and the [from, to, fixed-coord] of a wall-to-wall
// crossing along it (used by every "flies across" actor).
function crossing(rect, pad) {
  const alongX = rect.w >= rect.d;
  const a = (alongX ? rect.minX : rect.minZ) - pad;
  const b = (alongX ? rect.maxX : rect.maxZ) + pad;
  const fixed = alongX ? rect.cz : rect.cx;
  return { alongX, a, b, fixed };
}
const placeCross = (obj, alongX, p, y, fixed) => alongX ? obj.position.set(p, y, fixed) : obj.position.set(fixed, y, p);
// Peak-above-`base` for a crossing arc that crests near 60% of room height, // below the eyeline-to-ceiling gap where the earlier arcs disappeared.
const arcAmp = (h, base) => Math.max(0.6, 0.6 * h - base);

// A pair of flapping wing planes on a body (owl, snitch). flap(ph) drives them.
function wings(scale, color) {
  const g = new THREE.Group();
  const wm = tbas('wing:' + color, color, { side: THREE.DoubleSide, opacity: 0.85 });
  const mk = (sgn) => {
    const w = mesh('wing.plane', () => new THREE.PlaneGeometry(0.3, 0.15), wm);
    w.position.x = sgn * 0.15 * scale; w.scale.setScalar(scale);
    const pivot = new THREE.Group(); pivot.add(w); g.add(pivot); return pivot;
  };
  const l = mk(-1), r = mk(1);
  const flap = (ph) => { const a = 0.6 * Math.sin(ph); l.rotation.z = a; r.rotation.z = -a; };
  return { g, flap, mat: wm };
}

// --- rat: baseboard spline OR gaussian 2D random walk -----------------------
function rat(ctx) {
  const { rect, opts, duration } = ctx;
  const g = new THREE.Group();
  const rm = tlam('rat', 0x6a5f52);            // grey-brown fur (was near-black)
  const dk = tlam('rat.dk', 0x2f2a24);         // darker head + tail
  // Nose-forward along +Z: the walk code (perimeter angles + gaussian atan2)
  // orients the rat's +Z axis along its direction of travel.
  const body = mesh('rat.body', () => new THREE.SphereGeometry(0.11, 8, 6), rm);
  body.scale.set(1, 0.8, 1.5); body.position.y = 0.1;
  const head = mesh('rat.head', () => new THREE.SphereGeometry(0.07, 8, 6), dk);
  head.position.set(0, 0.11, 0.17);
  const tail = mesh('rat.tail', () => new THREE.CylinderGeometry(0.006, 0.02, 0.34, 4), dk);
  tail.rotation.x = Math.PI / 2; tail.position.set(0, 0.07, -0.24);
  g.add(body, head, tail);
  const mats = [{ m: rm, base: 1 }, { m: dk, base: 1 }];
  const r = rng((rect.cx * 71 + rect.cz * 13) | 0);
  const inset = 0.55, x0 = rect.minX + inset, x1 = rect.maxX - inset, z0 = rect.minZ + inset, z1 = rect.maxZ - inset;
  const gaussian = opts.walk === 'gaussian';
  const per = 2 * ((x1 - x0) + (z1 - z0));
  let px = gaussian ? rect.cx : x0, pz = gaussian ? rect.cz : z0;
  g.position.set(px, 0, pz);
  const update = (t, dt) => {
    if (gaussian) {
      px = Math.min(x1, Math.max(x0, px + gauss(r) * dt * 1.9));
      pz = Math.min(z1, Math.max(z0, pz + gauss(r) * dt * 1.9));
      _v.set(px - g.position.x, 0, pz - g.position.z);
      g.position.set(px, 0, pz);
      if (_v.lengthSq() > 1e-6) g.rotation.y = Math.atan2(_v.x, _v.z);
    } else {
      const p = perimeter((t * 1.1) % per, x0, x1, z0, z1);
      g.position.set(p.x, 0, p.z); g.rotation.y = p.a;
    }
    g.position.y = 0.04 + Math.abs(Math.sin(t * 12)) * 0.015; // lifted off the floor
    fade(mats, envelope(t, duration));
  };
  return { group: g, update, dispose() {} };
}

// --- ghost: a translucent robe drifting in one wall and out the far one ------
function ghost(ctx) {
  const { rect, duration } = ctx;
  const g = new THREE.Group();
  // Stronger cool emissive + higher opacity ceiling so she reads even against
  // bright parchment walls.
  const rmat = tlam('ghost', 0xeaf2fb, { emissive: 0x7ea0c4, emissiveIntensity: 0.75, side: THREE.DoubleSide });
  const robe = mesh('ghost.robe', () => new THREE.ConeGeometry(0.34, 1.5, 12, 1, true), rmat);
  robe.position.y = 0.78;
  const head = mesh('ghost.head', () => new THREE.SphereGeometry(0.2, 12, 10), rmat);
  head.position.y = 1.55;
  g.add(robe, head);
  const mats = [{ m: rmat, base: 0.64 }];
  const { alongX, a, b, fixed } = crossing(rect, 0.6);
  g.rotation.y = alongX ? Math.PI / 2 : 0;
  const update = (t) => {
    placeCross(g, alongX, a + (b - a) * Math.min(1, t / duration), 0.15 + Math.sin(t * 1.3) * 0.06, fixed);
    fade(mats, envelope(t, duration));
  };
  return { group: g, update, dispose() {} };
}

// --- cat: sits by a wall watching the keeper, slinks away if approached ------
function cat(ctx) {
  const { rect, camera, duration } = ctx;
  const g = new THREE.Group();
  const cm = tlam('cat', 0x46413a);            // a touch lighter than before
  const cl = tlam('cat.rim', 0x6f665b);        // lighter chest/rim, reads off dark walls
  const body = mesh('cat.body', () => new THREE.SphereGeometry(0.16, 10, 8), cm);
  body.scale.set(1.6, 0.9, 1); body.position.y = 0.16;
  const chest = mesh('cat.chest', () => new THREE.SphereGeometry(0.09, 8, 8), cl);
  chest.scale.set(0.9, 1.2, 0.7); chest.position.set(0.26, 0.16, 0);
  const head = mesh('cat.head', () => new THREE.SphereGeometry(0.1, 10, 8), cm);
  head.position.set(0.22, 0.24, 0);
  for (const dz of [0.05, -0.05]) {
    const ear = mesh('cat.ear', () => new THREE.ConeGeometry(0.04, 0.08, 5), cm);
    ear.position.set(0.2, 0.33, dz); g.add(ear);
  }
  const tail = mesh('cat.tail', () => new THREE.CylinderGeometry(0.02, 0.03, 0.4, 5), cm);
  tail.position.set(-0.24, 0.22, 0); tail.rotation.z = 1.0;
  const eyes = mesh('cat.eyes', () => new THREE.SphereGeometry(0.028, 8, 8), tbas('cat.eye', 0xfff0a8));
  eyes.position.set(0.31, 0.25, 0);
  g.add(body, chest, head, tail, eyes);
  const mats = [{ m: cm, base: 1 }, { m: cl, base: 1 }];
  const spot = nearWall(rect, camera, 0.7);
  g.position.set(spot.x, 0, spot.z);
  let fleeing = 0;
  const update = (t, dt) => {
    g.rotation.y = Math.atan2(-(camera.position.z - g.position.z), camera.position.x - g.position.x);
    const d = Math.hypot(camera.position.x - g.position.x, camera.position.z - g.position.z);
    if (d < 2.5) fleeing = Math.min(1, fleeing + dt * 1.2);
    if (fleeing > 0) {
      _v.set(g.position.x - camera.position.x, 0, g.position.z - camera.position.z).normalize();
      g.position.addScaledVector(_v, dt * 2.2 * fleeing);
      g.position.y = Math.abs(Math.sin(t * 14)) * 0.02;
    }
    const e = envelope(t, duration) * (1 - fleeing * 0.9);
    fade(mats, e); eyes.material.opacity = e;
  };
  return { group: g, update, dispose() {} };
}

// --- owl: crosses on an arc, dropping a scroll that falls and fades ----------
function owl(ctx) {
  const { rect, h, duration } = ctx;
  const g = new THREE.Group();
  const bird = new THREE.Group();
  const om = tlam('owl', 0x6b5636);
  const body = mesh('owl.body', () => new THREE.SphereGeometry(0.14, 10, 8), om);
  body.scale.set(1, 1.3, 1);
  const head = mesh('owl.head', () => new THREE.SphereGeometry(0.1, 10, 8), om);
  head.position.y = 0.18;
  const { g: wg, flap, mat: wmat } = wings(1.2, 0x7a6440);
  bird.add(body, head, wg);
  bird.scale.setScalar(1.3);                    // a heftier bird, easier to spot
  const scroll = mesh('owl.scroll', () => new THREE.CylinderGeometry(0.03, 0.03, 0.16, 6), tlam('scroll', 0xe9dfc6));
  scroll.rotation.z = Math.PI / 2; scroll.visible = false;
  g.add(bird, scroll);
  const { alongX, a, b, fixed } = crossing(rect, 0.4);
  bird.rotation.y = alongX ? Math.PI / 2 : 0;
  const amp = arcAmp(h, 0.9);
  const mats = [{ m: om, base: 1 }, { m: wmat, base: 0.85 }];
  let dropped = false, vy = 0;
  const update = (t, dt) => {
    const u = Math.min(1, t / duration);
    placeCross(bird, alongX, a + (b - a) * u, 0.9 + Math.sin(u * Math.PI) * amp, fixed);
    flap(t * 14);
    if (t > duration * 0.5) {
      if (!dropped) { dropped = true; scroll.visible = true; scroll.position.copy(bird.position); scroll.material.opacity = 1; }
      if (scroll.position.y > 0.07) { vy += 2.4 * dt; scroll.position.y -= vy * dt; scroll.rotation.x += dt * 3; }
      else { scroll.position.y = 0.07; scroll.material.opacity = Math.max(0, scroll.material.opacity - dt * 0.5); }
    }
    fade(mats, envelope(t, duration));
  };
  return { group: g, update, dispose() {} };
}

// --- snitch: a bright gold dart with a glow trail, veering off if crowded -----
function snitch(ctx) {
  const { rect, camera, pool, duration } = ctx;
  const g = new THREE.Group();
  const bm = M('snitch', () => new THREE.MeshStandardMaterial({ color: 0xffdf9a, metalness: 0.8, roughness: 0.2, emissive: 0xffbe55, emissiveIntensity: 0.95, transparent: true }));
  const body = mesh('snitch.body', () => new THREE.SphereGeometry(0.1, 14, 12), bm); // ~1.6x
  const { g: wg, flap, mat: wmat } = wings(1.45, 0xfff4d6);                          // ~1.8x
  g.add(body, wg);
  const cx = rect.cx, cz = rect.cz, ax = (rect.w - 1.4) / 2, az = (rect.d - 1.4) / 2;
  const mats = [{ m: bm, base: 1 }, { m: wmat, base: 0.85 }];
  const TR = 20; // a lagging bead-line trail carried in the shared scratch buffers
  for (let i = 0; i < TR; i++) { _px[i] = cx; _py[i] = 1.3; _pz[i] = cz; }
  const update = (t) => {
    let x = cx + Math.sin(t * 1.3) * ax, z = cz + Math.sin(t * 0.9 + 1.7) * az, y = 1.3 + Math.sin(t * 2.1) * 0.4;
    _v.set(x - camera.position.x, 0, z - camera.position.z);
    const d = _v.length();
    if (d < 1.2 && d > 1e-3) { _v.multiplyScalar((1.2 - d) / d); x += _v.x; z += _v.z; }
    _w.set(x - g.position.x, y - g.position.y, z - g.position.z);
    g.position.set(x, y, z);
    if (_w.lengthSq() > 1e-6) { _look.copy(g.position).add(_w); g.lookAt(_look); }
    flap(t * 40);
    const e = envelope(t, duration);
    fade(mats, e);
    // Trail: head snaps to the snitch, each bead chases the one ahead.
    _px[0] = x; _py[0] = y; _pz[0] = z;
    for (let i = 1; i < TR; i++) {
      _px[i] += (_px[i - 1] - _px[i]) * 0.35; _py[i] += (_py[i - 1] - _py[i]) * 0.35; _pz[i] += (_pz[i - 1] - _pz[i]) * 0.35;
    }
    pool.begin(0xffe6a0, 0.07);
    for (let i = 0; i < TR; i++) pool.set(i, _px[i], _py[i], _pz[i]);
    pool.opacity(0.7 * e); pool.commit();
  };
  return { group: g, update, dispose() {}, usesPool: true };
}

// --- dementor: a big tattered silhouette looming at head height as it glides --
function dementor(ctx) {
  const { rect, duration } = ctx;
  const g = new THREE.Group();
  const dm = tlam('dementor', 0x0c0c12, { emissive: 0x101018, side: THREE.DoubleSide, opacity: 0.9 });
  // Robe hangs DOWN from the hood: apex near the shoulders, flare draping toward
  // the floor. ~1.5x the earlier silhouette.
  const robe = mesh('dementor.robe', () => new THREE.ConeGeometry(0.72, 2.8, 12, 1, true), dm);
  robe.position.y = -1.1;
  const hood = mesh('dementor.hood', () => new THREE.SphereGeometry(0.42, 12, 10), dm);
  hood.position.y = 0.1;
  g.add(robe, hood);
  const tatters = [];
  for (let i = 0; i < 6; i++) {
    const tt = mesh('dementor.tat', () => new THREE.PlaneGeometry(0.18, 1.5), dm);
    const a = (i / 6) * Math.PI * 2;
    tt.position.set(Math.cos(a) * 0.52, -1.35, Math.sin(a) * 0.52);
    tatters.push(tt); g.add(tt);
  }
  const mats = [{ m: dm, base: 0.9 }];
  const { alongX, a, b, fixed } = crossing(rect, 0.5);
  const y = 2.6; // hood at eye + ~1m; the ragged robe drapes toward the floor
  const update = (t) => {
    placeCross(g, alongX, a + (b - a) * Math.min(1, t / duration), y, fixed);
    for (let i = 0; i < tatters.length; i++) tatters[i].rotation.x = Math.sin(t * 3 + i * 1.3) * 0.6;
    g.rotation.y = (alongX ? Math.PI / 2 : 0) + Math.sin(t * 0.5) * 0.2;
    fade(mats, envelope(t, duration));
  };
  return { group: g, update, dispose() {} };
}

// --- patronus: a silver stag galloping across, a bright trail behind ---------
function patronus(ctx) {
  const { rect, duration } = ctx;
  const g = new THREE.Group();
  const sm = M('patronus', () => new THREE.MeshBasicMaterial({ color: 0xcfe8ff, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false }));
  const stag = new THREE.Group();
  const torso = mesh('stag.torso', () => new THREE.SphereGeometry(0.22, 10, 8), sm);
  torso.scale.set(1.8, 1, 0.9); torso.position.y = 0.95;
  const neck = mesh('stag.neck', () => new THREE.CylinderGeometry(0.07, 0.1, 0.4, 6), sm);
  neck.position.set(0.34, 1.15, 0); neck.rotation.z = -0.7;
  const head = mesh('stag.head', () => new THREE.SphereGeometry(0.11, 8, 8), sm);
  head.position.set(0.5, 1.32, 0);
  const legs = [];
  for (const [dx, dz] of [[0.22, 0.12], [0.22, -0.12], [-0.22, 0.12], [-0.22, -0.12]]) {
    const leg = mesh('stag.leg', () => new THREE.CylinderGeometry(0.035, 0.02, 0.7, 5), sm);
    leg.position.set(dx, 0.55, dz); legs.push(leg); stag.add(leg);
  }
  for (const dz of [0.09, -0.09]) {
    const an = mesh('stag.antler', () => new THREE.CylinderGeometry(0.012, 0.02, 0.3, 4), sm);
    an.position.set(0.53, 1.45, dz); an.rotation.z = 0.5; stag.add(an);
  }
  stag.add(torso, neck, head);
  const trailMat = M('patronus.trail', () => new THREE.MeshBasicMaterial({ color: 0xcfe8ff, transparent: true, opacity: 0.4, blending: THREE.AdditiveBlending, depthWrite: false }));
  const trail = [];
  for (let i = 0; i < 8; i++) { const tp = mesh('stag.trail', () => new THREE.SphereGeometry(0.05, 6, 6), trailMat); trail.push(tp); g.add(tp); }
  g.add(stag);
  const { alongX, a, b, fixed } = crossing(rect, 0.4);
  stag.rotation.y = alongX ? Math.PI / 2 : 0;
  const mats = [{ m: sm, base: 0.6 }, { m: trailMat, base: 0.4 }];
  const at = (tau) => a + (b - a) * Math.max(0, Math.min(1, tau / duration));
  const update = (t) => {
    const bob = Math.abs(Math.sin(t * 8)) * 0.06;
    placeCross(stag, alongX, at(t), bob, fixed);
    for (let i = 0; i < legs.length; i++) legs[i].rotation.x = Math.sin(t * 10 + i * Math.PI) * 0.5;
    for (let i = 0; i < trail.length; i++) placeCross(trail[i], alongX, at(t - (i + 1) * 0.06), 0.95, fixed);
    fade(mats, envelope(t, duration));
  };
  return { group: g, update, dispose() {} };
}

// --- boggart_chest: a chest that rattles, cracking open if the keeper nears --
function boggart_chest(ctx) {
  const { rect, camera, duration } = ctx;
  const g = new THREE.Group();
  const wm = tlam('chest.wood', 0x5a3a1c), mm = tlam('chest.metal', 0x7a6a48);
  const base = mesh('chest.base', () => new THREE.BoxGeometry(0.7, 0.4, 0.45), wm);
  base.position.y = 0.2;
  const strap = mesh('chest.strap', () => new THREE.BoxGeometry(0.74, 0.44, 0.06), mm);
  strap.position.y = 0.22;
  const lidPivot = new THREE.Group(); lidPivot.position.set(0, 0.4, -0.225);
  const lid = mesh('chest.lid', () => new THREE.BoxGeometry(0.7, 0.14, 0.45), wm);
  lid.position.set(0, 0.07, 0.225); lidPivot.add(lid);
  const glow = mesh('chest.glow', () => new THREE.PlaneGeometry(0.6, 0.35), tbas('chest.glow', 0xff8a4a, { opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  glow.rotation.x = -Math.PI / 2; glow.position.set(0, 0.42, 0);
  g.add(base, strap, lidPivot, glow);
  // Place ~3.5m ahead of the keeper (projected onto the floor, clamped inside
  // the room) so walking up to it triggers the <2m crack-open payoff.
  camera.getWorldDirection(_v); _v.y = 0;
  if (_v.lengthSq() < 1e-6) _v.set(0, 0, -1); else _v.normalize();
  const inset = 0.9;
  const sx = Math.min(rect.maxX - inset, Math.max(rect.minX + inset, camera.position.x + _v.x * 3.5));
  const sz = Math.min(rect.maxZ - inset, Math.max(rect.minZ + inset, camera.position.z + _v.z * 3.5));
  g.position.set(sx, 0, sz);
  g.rotation.y = Math.atan2(camera.position.x - sx, camera.position.z - sz); // lid faces the keeper
  const mats = [{ m: wm, base: 1 }, { m: mm, base: 1 }];
  let open = 0;
  const update = (t, dt) => {
    const d = Math.hypot(camera.position.x - g.position.x, camera.position.z - g.position.z);
    g.position.y = Math.abs(Math.sin(t * 22)) * 0.02;
    g.rotation.z = Math.sin(t * 26) * 0.02;
    const cyc = (t % 1.6) / 1.6;                         // rise then snap shut
    const want = d < 2 ? (cyc < 0.7 ? cyc / 0.7 : 0) : 0;
    open += (want - open) * Math.min(1, dt * (want > open ? 6 : 40));
    lidPivot.rotation.x = -open * 1.1;
    const e = envelope(t, duration);
    glow.material.opacity = open * 0.8 * e;
    fade(mats, e);
  };
  return { group: g, update, dispose() {} };
}

// --- draft (pool): motes of dust sliding sideways across the room ------------
// The chill itself (light dip + fog) is scheduler fx on the event def; this
// actor owns only the drifting dust, so it never traverses the scene's lights.
function draft(ctx) {
  const { rect, h, pool, duration } = ctx;
  const r = rng((rect.cx * 17 + rect.cz * 91) | 0);
  const N = Math.min(pool.n, 130), alongX = rect.w >= rect.d;
  // In a big room a full-rect scatter dissolves into nothing, so concentrate the
  // motes into a mid-height band through the middle third across the short axis.
  const big = rect.w * rect.d > 80;
  for (let i = 0; i < N; i++) {
    const perp = big ? (0.5 + r()) / 3 : r();          // middle third when big
    _px[i] = alongX ? r() * rect.w : perp * rect.w;
    _pz[i] = alongX ? perp * rect.d : r() * rect.d;
    _py[i] = big ? 0.9 + r() * 1.0 : 0.4 + r() * (h - 1.0);
    _pk[i] = r() * Math.PI * 2;
  }
  const update = (t) => {
    pool.begin(0xcfe0f0, 0.045);
    for (let i = 0; i < N; i++) {
      const slide = Math.sin(t * 0.35 + _pk[i]) * 0.6 + t * 0.15;
      const x = rect.minX + (alongX ? wrap(_px[i] + slide, rect.w) : _px[i]);
      const z = rect.minZ + (alongX ? _pz[i] : wrap(_pz[i] + slide, rect.d));
      pool.set(i, x, _py[i] + Math.sin(t * 0.46 + _pk[i]) * 0.08, z);
    }
    pool.opacity((big ? 0.72 : 0.5) * envelope(t, duration)); pool.commit();
  };
  return { group: new THREE.Group(), update, dispose() {}, usesPool: true };
}

// --- rumble (pool): a tiny camera tremor + ceiling dust shaken loose ---------
function rumble(ctx) {
  const { rect, h, camera, pool, duration } = ctx;
  const r = rng((rect.cx * 53 + rect.cz * 29) | 0);
  const N = Math.min(pool.n, 80);
  // Seed a few tight clusters at the ceiling (clumps of dislodged dust) rather
  // than an even spread, so the fall reads as debris, not ambient motes.
  const NC = 4, ccx = [], ccz = [];
  for (let c = 0; c < NC; c++) { ccx.push(rect.minX + 0.8 + r() * (rect.w - 1.6)); ccz.push(rect.minZ + 0.8 + r() * (rect.d - 1.6)); }
  for (let i = 0; i < N; i++) {
    const c = i % NC;
    _px[i] = ccx[c] + (r() - 0.5) * 0.45; _py[i] = h - 0.2;
    _pz[i] = ccz[c] + (r() - 0.5) * 0.45; _pk[i] = r();
  }
  // A wrapper offset added in update and subtracted on dispose, restores the
  // camera exactly, never accumulates. Only x/z (player.update owns y = EYE).
  const off = new THREE.Vector3();
  let roll = 0;
  const update = (t) => {
    const e = envelope(t, duration), amp = 0.035 * e;
    camera.position.sub(off); off.set((r() - 0.5) * amp, 0, (r() - 0.5) * amp); camera.position.add(off);
    camera.rotation.z -= roll; roll = (r() - 0.5) * 0.006 * e; camera.rotation.z += roll;
    pool.begin(0xd8b48a, 0.055);               // warmer, dustier than room motes
    for (let i = 0; i < N; i++) {
      const tt = Math.max(0, t - _pk[i] * 1.5), y = Math.max(0.05, _py[i] - 0.5 * tt * tt);
      pool.set(i, _px[i] + Math.sin(tt * 20 + i) * 0.02, y, _pz[i]);
    }
    pool.opacity(0.7 * e); pool.commit();
  };
  const dispose = () => { camera.position.sub(off); camera.rotation.z -= roll; };
  return { group: new THREE.Group(), update, dispose, usesPool: true };
}

// --- noise_veil (pool): scattered motes gather to a slab, hold, disperse -----
function noise_veil(ctx) {
  const { rect, h, pal, pool, duration } = ctx;
  const r = rng((rect.cx * 37 + rect.cz * 83) | 0);
  const N = Math.min(pool.n, 196), COLS = 14, rows = N / COLS;
  for (let i = 0; i < N; i++) {
    _px[i] = rect.minX + 0.5 + r() * (rect.w - 1); _py[i] = 0.4 + r() * (h - 1); _pz[i] = rect.minZ + 0.5 + r() * (rect.d - 1);
  }
  const wallZ = rect.maxZ - 0.7, slabW = Math.min(rect.w - 1.5, 2.6);
  const update = (t) => {
    const u = t / duration;
    const m = u < 0.35 ? smooth(u / 0.35) : u < 0.7 ? 1 : 1 - smooth((u - 0.7) / 0.3);
    pool.begin(pal.glow, 0.05);
    for (let i = 0; i < N; i++) {
      const tx = rect.cx + ((i % COLS) / (COLS - 1) - 0.5) * slabW;
      const ty = 1.5 + (((i / COLS) | 0) / rows - 0.5) * 1.4;
      const tz = wallZ + Math.sin(i) * 0.04;
      pool.set(i, _px[i] + (tx - _px[i]) * m, _py[i] + (ty - _py[i]) * m, _pz[i] + (tz - _pz[i]) * m);
    }
    pool.opacity((0.3 + 0.6 * m) * envelope(t, duration)); pool.commit();
  };
  return { group: new THREE.Group(), update, dispose() {}, usesPool: true };
}

// --- time_glint (pool + mesh): an hourglass turning back, motes reversed -----
function time_glint(ctx) {
  const { rect, pool, duration } = ctx;
  const g = new THREE.Group();
  const gm = M('glint', () => new THREE.MeshBasicMaterial({ color: 0xffd98a, transparent: true, opacity: 0.85, side: THREE.DoubleSide }));
  const top = mesh('glint.cone', () => new THREE.ConeGeometry(0.12, 0.18, 10, 1, true), gm);
  const bot = mesh('glint.cone', () => new THREE.ConeGeometry(0.12, 0.18, 10, 1, true), gm);
  top.position.y = 0.09; bot.position.y = -0.09; bot.rotation.x = Math.PI;
  const frame = new THREE.Group(); frame.add(top, bot); frame.scale.setScalar(1.5); // bigger glass
  frame.position.set(rect.cx, 1.5, rect.cz);
  g.add(frame);
  const N = Math.min(pool.n, 60), mats = [{ m: gm, base: 0.85 }];
  const update = (t) => {
    const e = envelope(t, duration);
    frame.rotation.y = -t * 2.6;                    // the glass turns BACKWARD, faster
    fade(mats, e);
    pool.begin(0xffd98a, 0.05);
    // A tight, flat ring orbiting backward, legibly circular, not a loose swirl.
    for (let i = 0; i < N; i++) {
      const a = -t * 2.0 - (i / N) * Math.PI * 2;
      pool.set(i, rect.cx + Math.cos(a) * 0.5, 1.5 + Math.sin(t * 2 + i) * 0.03, rect.cz + Math.sin(a) * 0.5);
    }
    pool.opacity(0.7 * e); pool.commit();
  };
  return { group: g, update, dispose() {}, usesPool: true };
}

// --- peeves: two-three books tumble-fly across the room, one by one ----------
function peeves(ctx) {
  const { rect, h, duration } = ctx;
  const g = new THREE.Group();
  const covers = [0x6e3030, 0x274233, 0x32456e], n = 3, mats = [];
  const { alongX, a, b, fixed } = crossing(rect, 0.3);
  const span = (duration / (n + 1)) * 2, amp = arcAmp(h, 1.1);
  const books = [];
  for (let i = 0; i < n; i++) {
    const bm = tlam('peeves' + i, covers[i]);
    const book = mesh('peeves.book', () => new THREE.BoxGeometry(0.26, 0.05, 0.34), bm);
    book.scale.setScalar(1.4);                  // fatter tomes, easier to read
    book.userData = { delay: i * (duration / (n + 1)), sx: (i + 1) * 3.7, sy: (i + 1) * 2.9, sz: (i + 1) * 5.1, off: (i - 1) * 0.5 };
    books.push(book); g.add(book); mats.push({ m: bm, base: 1 });
  }
  const update = (t) => {
    const e = envelope(t, duration);
    for (const bk of books) {
      const u = Math.max(0, Math.min(1, (t - bk.userData.delay) / span));
      placeCross(bk, alongX, a + (b - a) * u, 1.1 + Math.sin(u * Math.PI) * amp, fixed + bk.userData.off);
      bk.rotation.set(t * bk.userData.sx, t * bk.userData.sy, t * bk.userData.sz);
      bk.material.opacity = (u > 0 && u < 1 ? 1 : 0) * e;
    }
  };
  return { group: g, update, dispose() {} };
}

export const ACTORS = {
  rat, ghost, cat, owl, snitch, dementor, patronus,
  boggart_chest, draft, rumble, noise_veil, time_glint, peeves,
};
