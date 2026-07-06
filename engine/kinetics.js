// Kinetic concept props: animated centerpieces whose MOTION is the lesson.
// Same contract as props.js builders — (pal) => { group, update(t) } — and
// referenced by content through the catalog like any other prop. Rules kept
// throughout: updates only mutate transforms, material params and one Points
// buffer; nothing allocates or repaints a canvas per frame, so a whole floor
// of these costs microseconds.

import * as THREE from 'three';
import { lam, DARKWOOD, STONE, METAL } from './common.js';

const bas = (color, extra = {}) => new THREE.MeshBasicMaterial({ color, ...extra });
const GOLD = 0xffd98a;
const BLUE = 0x9ac4ff;
const CREAM = 0xefe6cf;

function smooth(x) { // smoothstep on [0,1]
  const c = Math.min(1, Math.max(0, x));
  return c * c * (3 - 2 * c);
}

function smallPedestal(pal) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.62, 0.14, 10), lam(STONE));
  base.position.y = 0.07;
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.28, 0.8, 8), lam(pal.trim));
  shaft.position.y = 0.54;
  g.add(base, shaft);
  return g;
}

// An arrow of unit length along +Y; scale.y stretches it, rotation.z aims it
// (all kinetic arrows live in a vertical plane facing the room).
function arrow(color, thick = 0.035) {
  const g = new THREE.Group();
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(thick, thick, 0.8, 6), bas(color));
  shaft.position.y = 0.4;
  const tip = new THREE.Mesh(new THREE.ConeGeometry(thick * 2.6, 0.2, 8), bas(color));
  tip.position.y = 0.9;
  g.add(shaft, tip);
  return g;
}

// --- attention_beams: keys orbit a query; beam brightness IS softmax --------
// Three key orbs circle a golden query orb. Each beam's glow follows the live
// softmax of that key's alignment with the query's fixed gaze, so the weights
// visibly flow to whichever key drifts in front of the query.
function attentionBeams(pal) {
  const g = new THREE.Group();
  g.add(smallPedestal(pal));
  const Y = 1.55, R = 0.75;

  const query = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), bas(GOLD));
  query.position.y = Y;
  const gaze = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.22, 8), bas(GOLD));
  gaze.position.set(0, Y, 0.24);
  gaze.rotation.x = Math.PI / 2; // the query "looks" toward the room (+z)
  const light = new THREE.PointLight(GOLD, 1.2, 4, 1.8);
  light.position.y = Y;
  g.add(query, gaze, light);

  const keys = [], beams = [];
  for (let i = 0; i < 3; i++) {
    const key = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 12),
      bas(BLUE, { transparent: true }));
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1, 6, 1, true),
      bas(BLUE, { transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    keys.push(key); beams.push(beam);
    g.add(key, beam);
  }
  const speeds = [0.32, 0.22, 0.27], phases = [0, 2.1, 4.2];
  const _dir = new THREE.Vector3(), _UP = new THREE.Vector3(0, 1, 0);
  const update = (t) => {
    const scores = [];
    for (let i = 0; i < 3; i++) {
      const a = t * speeds[i] + phases[i];
      keys[i].position.set(Math.sin(a) * R, Y + Math.sin(t * 0.9 + i) * 0.06, Math.cos(a) * R);
      scores.push(3 * Math.cos(a)); // alignment with the +z gaze, sharpened
    }
    const m = Math.max(...scores);
    const es = scores.map((s) => Math.exp(s - m));
    const Z = es[0] + es[1] + es[2];
    for (let i = 0; i < 3; i++) {
      const w = es[i] / Z;
      keys[i].material.opacity = 0.35 + 0.65 * w;
      keys[i].scale.setScalar(0.8 + 0.7 * w);
      const k = keys[i].position, q = query.position;
      beams[i].position.set((k.x + q.x) / 2, (k.y + q.y) / 2, (k.z + q.z) / 2);
      beams[i].scale.set(1 + 4 * w, k.distanceTo(q), 1 + 4 * w);
      // Align the cylinder's Y axis with the local query->key direction.
      _dir.subVectors(k, q).normalize();
      beams[i].quaternion.setFromUnitVectors(_UP, _dir);
      beams[i].material.opacity = 0.12 + 0.75 * w;
    }
  };
  return { group: g, update };
}

// --- similarity_dial: a sweeping angle and its live cosine ------------------
// Vector u stands still; v sweeps past it. The bar under the dial stretches
// with u·v — long and warm when aligned, vanishing at 90°, cold when opposed.
function similarityDial(pal) {
  const g = new THREE.Group();
  g.add(smallPedestal(pal));
  const Y = 1.6;
  const dial = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.025, 8, 40), lam(METAL));
  dial.position.y = Y;
  g.add(dial);

  const u = arrow(GOLD, 0.04);
  u.position.y = Y; u.scale.y = 0.58; u.rotation.z = -0.5; // fixed reference
  const v = arrow(BLUE, 0.04);
  v.position.y = Y; v.scale.y = 0.58;
  g.add(u, v);

  const bar = new THREE.Mesh(new THREE.BoxGeometry(1, 0.07, 0.07),
    bas(GOLD, { transparent: true }));
  bar.position.y = 0.78;
  g.add(bar);
  const light = new THREE.PointLight(pal.glow, 0.8, 3.5, 1.8);
  light.position.y = Y;
  g.add(light);

  const update = (t) => {
    g.rotation.y = t * 0.12; // slow turntable: readable from every side
    const sweep = -0.5 + Math.sin(t * 0.35) * 2.2; // v roams around u
    v.rotation.z = sweep;
    const cos = Math.cos(sweep - u.rotation.z);
    bar.scale.x = Math.max(0.04, Math.abs(cos)) * 0.9;
    bar.material.color.setHex(cos >= 0 ? GOLD : BLUE);
    bar.material.opacity = 0.35 + 0.6 * Math.abs(cos);
    light.intensity = 0.5 + 0.7 * Math.max(0, cos);
  };
  return { group: g, update };
}

// --- frequency_wheel: nested hands, each twice as fast ----------------------
// A vertical clock of four concentric hands at speeds 1x, 2x, 4x, 8x — the
// ladder of frequencies turning in stone: slow hands to coarse position,
// fast hands to fine.
function frequencyWheel(pal) {
  const g = new THREE.Group();
  g.add(smallPedestal(pal));
  const Y = 1.65;
  const radii = [0.72, 0.55, 0.38, 0.21];
  const hands = [];
  for (let i = 0; i < radii.length; i++) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(radii[i], 0.018, 8, 40), lam(METAL));
    ring.position.y = Y;
    g.add(ring);
    const pivot = new THREE.Group();
    pivot.position.y = Y;
    const hand = new THREE.Mesh(new THREE.BoxGeometry(0.035, radii[i], 0.03),
      bas(i === 0 ? GOLD : BLUE, { transparent: true, opacity: 0.9 }));
    hand.position.y = radii[i] / 2;
    const bead = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 8),
      bas(i === 0 ? GOLD : CREAM));
    bead.position.y = radii[i];
    pivot.add(hand, bead);
    g.add(pivot);
    hands.push(pivot);
  }
  const hub = new THREE.Mesh(new THREE.SphereGeometry(0.06, 10, 10), bas(CREAM));
  hub.position.y = Y;
  const light = new THREE.PointLight(pal.glow, 0.8, 3.5, 1.8);
  light.position.y = Y;
  g.add(hub, light);
  const update = (t) => {
    g.rotation.y = t * 0.1; // slow turntable
    for (let i = 0; i < hands.length; i++) hands[i].rotation.z = -t * 0.35 * (2 ** i);
  };
  return { group: g, update };
}

// --- error_scales: a balance that settles as the loss shrinks ---------------
// The beam starts tipped by a fresh error, oscillates and settles level; the
// glow beneath fades with the imbalance. Then a new error arrives and the
// weighing begins again.
function errorScales(pal) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.58, 0.14, 10), lam(STONE));
  base.position.y = 0.07;
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 1.5, 8), lam(METAL));
  post.position.y = 0.89;
  g.add(base, post);

  const beam = new THREE.Group();
  beam.position.y = 1.66;
  const rod = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.05, 0.05), lam(METAL));
  beam.add(rod);
  const pans = [];
  for (const sgn of [-1, 1]) {
    const hang = new THREE.Group();
    hang.position.x = sgn * 0.7;
    const wire = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.42, 4), lam(METAL));
    wire.position.y = -0.21;
    const pan = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.16, 0.05, 12), lam(DARKWOOD));
    pan.position.y = -0.44;
    const orb = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 10),
      bas(sgn < 0 ? GOLD : CREAM));
    orb.position.y = -0.35;
    hang.add(wire, pan, orb);
    beam.add(hang);
    pans.push(hang);
  }
  g.add(beam);
  const glow = new THREE.PointLight(0xff9a7a, 1.0, 3.5, 1.8);
  glow.position.y = 1.0;
  g.add(glow);

  const PERIOD = 9;
  const update = (t) => {
    g.rotation.y = t * 0.09; // slow turntable
    const tc = t % PERIOD;
    // A damped swing from the initial error toward level.
    const tilt = 0.38 * Math.cos(tc * 2.2) * Math.exp(-tc * 0.55);
    beam.rotation.z = tilt;
    for (const hang of pans) hang.rotation.z = -tilt; // pans hang plumb
    glow.intensity = 0.15 + 3.0 * Math.abs(tilt);      // the loss, glowing
  };
  return { group: g, update };
}

// --- variance_balance: the budget that always sums to one -------------------
// Two columns — surviving signal (gold) and admitted static (blue) — trade
// heights as the mixing knob sweeps, while the cap line never moves: however
// beta wanders, the total variance stays exactly one.
function varianceBalance(pal) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.14, 0.7), lam(STONE));
  base.position.y = 0.07;
  g.add(base);
  const H = 1.5, Y0 = 0.14;
  const mk = (x, color) => {
    const col = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1, 0.3),
      bas(color, { transparent: true, opacity: 0.75 }));
    col.position.x = x;
    g.add(col);
    return col;
  };
  const signal = mk(-0.28, GOLD);
  const noise = mk(0.28, BLUE);
  // The immovable budget: a cap frame at total = 1.
  const cap = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.045, 0.4), bas(CREAM));
  cap.position.y = Y0 + H;
  const light = new THREE.PointLight(pal.glow, 0.7, 3.5, 1.8);
  light.position.y = 1.2;
  g.add(cap, light);

  const update = (t) => {
    g.rotation.y = t * 0.11; // slow turntable
    const beta = 0.5 + 0.5 * Math.sin(t * 0.45); // the mixing knob wanders
    const a = (1 - beta) * H, b = beta * H;
    signal.scale.y = Math.max(0.02, a); signal.position.y = Y0 + a / 2;
    noise.scale.y = Math.max(0.02, b);  noise.position.y = Y0 + b / 2;
  };
  return { group: g, update };
}

// --- ink clouds: order <-> chaos, in either direction -----------------------
// A swarm of luminous motes lerps between a drawn figure and pure scatter.
// `forward` clouds linger on the figure and slowly dissolve (the forward
// process); `reverse` clouds linger on chaos and slowly reassemble (sampling).
function inkCloud(pal, { shape, forward }) {
  const g = new THREE.Group();
  const basin = new THREE.Mesh(
    new THREE.CylinderGeometry(0.55, 0.42, 0.3, 14, 1, true), lam(0x232328));
  basin.position.y = 0.55;
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.4, 0.45, 10), lam(0x232328));
  foot.position.y = 0.22;
  g.add(basin, foot);

  const N = 220, CY = 1.7;
  const shapePos = new Float32Array(N * 3);
  const scatter = new Float32Array(N * 3);
  const jitter = new Float32Array(N);
  let seed = 99;
  const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0xffffffff; };
  for (let i = 0; i < N; i++) {
    const p = shape(i / N);
    shapePos.set([p[0], CY + p[1], p[2]], i * 3);
    // Random point in a sphere: the chaos every figure melts into.
    const th = rand() * Math.PI * 2, ph = Math.acos(2 * rand() - 1), r = 0.72 * Math.cbrt(rand());
    scatter.set([r * Math.sin(ph) * Math.cos(th), CY + r * Math.cos(ph) * 0.75,
                 r * Math.sin(ph) * Math.sin(th)], i * 3);
    jitter[i] = rand() * 0.18;
  }
  const geo = new THREE.BufferGeometry();
  const attr = new THREE.BufferAttribute(new Float32Array(N * 3), 3);
  geo.setAttribute('position', attr);
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({
    color: pal.glow, size: 0.045, transparent: true, opacity: 0.9,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  g.add(pts);
  const light = new THREE.PointLight(pal.glow, 1.0, 4, 1.8);
  light.position.y = CY;
  g.add(light);

  const PERIOD = 12;
  const update = (t) => {
    const tc = (t % PERIOD) / PERIOD;
    for (let i = 0; i < N; i++) {
      const x = (tc + jitter[i]) % 1;
      // hold(0-.2) -> melt(.2-.65) -> hold chaos(.65-.85) -> swift return(.85-1)
      let mix = x < 0.2 ? 0
        : x < 0.65 ? smooth((x - 0.2) / 0.45)
        : x < 0.85 ? 1
        : 1 - smooth((x - 0.85) / 0.15);
      if (!forward) mix = 1 - mix; // reverse rooms dwell in chaos, then gather
      const a = attr.array, j = i * 3;
      a[j]     = shapePos[j]     + (scatter[j]     - shapePos[j])     * mix;
      a[j + 1] = shapePos[j + 1] + (scatter[j + 1] - shapePos[j + 1]) * mix;
      a[j + 2] = shapePos[j + 2] + (scatter[j + 2] - shapePos[j + 2]) * mix;
    }
    attr.needsUpdate = true;
    pts.rotation.y = t * 0.1;
  };
  return { group: g, update };
}

// A two-turn ink spiral (the inkwell's figure).
const spiralShape = (u) => {
  const a = u * Math.PI * 4;
  const r = 0.1 + u * 0.5;
  return [Math.cos(a) * r, (u - 0.5) * 0.25, Math.sin(a) * r];
};
// Two interleaved crescent moons (the backward walk's figure).
const moonsShape = (u) => {
  const half = u < 0.5;
  const v = (half ? u : u - 0.5) * 2;
  const a = Math.PI * (0.15 + 0.7 * v) + (half ? 0 : Math.PI);
  const cx = half ? -0.16 : 0.16, cz = half ? -0.1 : 0.1;
  return [cx + Math.cos(a) * 0.42, Math.sin(u * 40) * 0.03, cz + Math.sin(a) * 0.42 * (half ? 1 : -1)];
};

const dissolvingCloud = (pal) => inkCloud(pal, { shape: spiralShape, forward: true });
const reformingCloud = (pal) => inkCloud(pal, { shape: moonsShape, forward: false });

// --- patch_shuttle: a square cut into tokens and woven back -----------------
// A floating 4x4 panel splits into sixteen tiles that glide into a single
// horizontal thread (the token sequence), hold, and weave back into the image.
function patchShuttle(pal) {
  const g = new THREE.Group();
  g.add(smallPedestal(pal));
  const Y = 1.62, TILE = 0.19, GAP = 0.025;
  const tiles = [], gridPos = [], rowPos = [];
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      const i = r * 4 + c;
      const shade = 0.55 + 0.45 * (((r + c) % 2) ? 0.55 : 1);
      const tile = new THREE.Mesh(
        new THREE.PlaneGeometry(TILE, TILE),
        bas(new THREE.Color(pal.glow).multiplyScalar(shade),
            { side: THREE.DoubleSide, transparent: true, opacity: 0.92 }));
      tiles.push(tile);
      g.add(tile);
      const span = 4 * TILE + 3 * GAP;
      gridPos.push([(c - 1.5) * (TILE + GAP), Y + (1.5 - r) * (TILE + GAP), 0]);
      rowPos.push([(i - 7.5) * (TILE * 0.62), Y, 0]); // the flattened thread
    }
  }
  const light = new THREE.PointLight(pal.glow, 0.8, 3.5, 1.8);
  light.position.y = Y;
  g.add(light);

  const PERIOD = 11;
  const update = (t) => {
    g.rotation.y = t * 0.1; // slow turntable
    const x = (t % PERIOD) / PERIOD;
    for (let i = 0; i < 16; i++) {
      const st = (x + i * 0.012) % 1; // raster-order stagger: the cut has an order
      const mix = st < 0.22 ? 0
        : st < 0.45 ? smooth((st - 0.22) / 0.23)
        : st < 0.72 ? 1
        : 1 - smooth((st - 0.72) / 0.28);
      const a = gridPos[i], b = rowPos[i];
      tiles[i].position.set(a[0] + (b[0] - a[0]) * mix, a[1] + (b[1] - a[1]) * mix, 0);
      const s = 1 - 0.35 * mix; // tokens are smaller than patches
      tiles[i].scale.setScalar(s);
    }
  };
  return { group: g, update };
}

// --- guidance_arrows: extrapolating past the prompt -------------------------
// Dim blue: the unconditional pull. Warm: the prompted pull. Gold: the guided
// prediction u + w(c - u), stretching farther past the prompt as w climbs
// toward 7.5 and easing back — steering by exaggerated difference, in motion.
function guidanceArrows(pal) {
  const g = new THREE.Group();
  g.add(smallPedestal(pal));
  const O = new THREE.Vector3(0, 1.15, 0);
  // Directions in the vertical plane (angle from +Y, length).
  const U = { ang: -0.55, len: 0.55 }, C = { ang: -0.18, len: 0.66 };
  const mk = (color, thick) => {
    const a = arrow(color, thick);
    a.position.copy(O);
    g.add(a);
    return a;
  };
  const uA = mk(BLUE, 0.028); uA.rotation.z = U.ang; uA.scale.y = U.len;
  uA.children.forEach((m) => { m.material.transparent = true; m.material.opacity = 0.45; });
  const cA = mk(0xffb04a, 0.03); cA.rotation.z = C.ang; cA.scale.y = C.len;
  const gA = mk(GOLD, 0.045);
  const light = new THREE.PointLight(GOLD, 1.0, 4, 1.8);
  light.position.y = 1.6;
  g.add(light);

  const vec = (d, s = 1) => [Math.sin(-d.ang) * d.len * s, Math.cos(d.ang) * d.len * s];
  const update = (t) => {
    g.rotation.y = t * 0.12; // slow turntable
    const w = 1 + 3.25 * (1 + Math.sin(t * 0.5));            // sweeps 1 .. 7.5
    const [ux, uy] = vec(U), [cx, cy] = vec(C);
    const gx = ux + w * (cx - ux), gy = uy + w * (cy - uy);  // u + w(c - u)
    const len = Math.hypot(gx, gy);
    gA.rotation.z = -Math.atan2(gx, gy);
    gA.scale.y = len;
    light.intensity = 0.5 + 0.18 * w;
  };
  return { group: g, update };
}

export const KINETIC_BUILDERS = {
  attention_beams: attentionBeams,
  similarity_dial: similarityDial,
  frequency_wheel: frequencyWheel,
  error_scales: errorScales,
  variance_balance: varianceBalance,
  dissolving_cloud: dissolvingCloud,
  reforming_cloud: reformingCloud,
  patch_shuttle: patchShuttle,
  guidance_arrows: guidanceArrows,
};
