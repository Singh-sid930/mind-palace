// Floating diagram widgets: small animated 3D graphics that hover beside a
// text display so every plaque teaches with motion, not only words. Content
// attaches one via an exhibit's `float: { widget, ...params }`; the catalog's
// `widgets` list is the enum. Same discipline as kinetics.js: builders are
// (params, pal) => { group, update(t) }, updates only mutate transforms,
// material params and preallocated buffers (instance matrices/colors, Points
// and vertex positions) — nothing allocates per frame, and widgets add no
// lights. Grids and clouds use InstancedMesh / Points so a wall of widgets
// stays a handful of draw calls.
//
// Extending the library: add a builder here, register it in WIDGET_BUILDERS,
// add the name to world/catalog.json `widgets`. Prefer a new widget over
// bending an ill-fitting one — the motion IS the explanation.

import * as THREE from 'three';

const bas = (color, extra = {}) => new THREE.MeshBasicMaterial({ color, ...extra });
const GOLD = 0xffd98a;
const BLUE = 0x9ac4ff;
const COLD = 0x7f9ab8;
const DIM = 0x3a3450;

// Shared unit geometries; every widget scales these rather than minting its own.
const G = {
  sphere: new THREE.SphereGeometry(1, 10, 10),
  box: new THREE.BoxGeometry(1, 1, 1),
  cyl: new THREE.CylinderGeometry(1, 1, 1, 6),
  cone: new THREE.ConeGeometry(1, 1, 8),
  ring: new THREE.TorusGeometry(1, 0.035, 6, 40),
};

// Soft round sprite for Points (raw points draw as hard squares).
let _sprite = null;
function sprite() {
  if (_sprite) return _sprite;
  const c = document.createElement('canvas');
  c.width = c.height = 32;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.4, 'rgba(255,255,255,0.55)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 32, 32);
  _sprite = new THREE.CanvasTexture(c);
  return _sprite;
}

function pointsCloud(n, size, color) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  const mat = new THREE.PointsMaterial({
    color, size, map: sprite(), transparent: true, opacity: 0.9,
    depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true,
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false; // positions churn; a stale bound would blink it out
  return pts;
}

function instanced(geoKey, n, color) {
  const m = new THREE.InstancedMesh(G[geoKey], bas(0xffffff), n);
  m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const c = new THREE.Color(color);
  for (let i = 0; i < n; i++) m.setColorAt(i, c);
  return m;
}

const _M = new THREE.Matrix4();
const _Q = new THREE.Quaternion();
const _S = new THREE.Vector3();
const _P = new THREE.Vector3();
const _C = new THREE.Color();
function setInst(mesh, i, x, y, z, sx, sy, sz) {
  _P.set(x, y, z); _S.set(sx, sy, sz != null ? sz : sx);
  _M.compose(_P, _Q, _S);
  mesh.setMatrixAt(i, _M);
}

function smooth(x) {
  const c = Math.min(1, Math.max(0, x));
  return c * c * (3 - 2 * c);
}
// setInst with a spin about +Z; _Q is shared, so it is restored to identity.
const _AXIS_Z = new THREE.Vector3(0, 0, 1);
function setInstRot(mesh, i, x, y, sx, sy, angle) {
  _P.set(x, y, 0); _S.set(sx, sy, sx);   // depth tracks width — never leave z at 1

  _Q.setFromAxisAngle(_AXIS_Z, angle);
  _M.compose(_P, _Q, _S);
  mesh.setMatrixAt(i, _M);
  _Q.identity();
}
// Deterministic per-index pseudo-random in [0,1) — stable across frames.
function hash(i, k = 0) {
  const s = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return s - Math.floor(s);
}
// Slow organic wander in [0,1], different per seed, no shared period.
function wander(t, seed) {
  return 0.5 + 0.25 * Math.sin(t * (0.31 + 0.11 * seed) + seed * 2.7)
             + 0.25 * Math.sin(t * (0.53 + 0.07 * seed) + seed * 5.1);
}

function arrowMesh(color, thick = 0.03) {
  const g = new THREE.Group();
  const shaft = new THREE.Mesh(G.cyl, bas(color));
  shaft.scale.set(thick, 0.8, thick); shaft.position.y = 0.4;
  const tip = new THREE.Mesh(G.cone, bas(color));
  tip.scale.set(thick * 2.6, 0.2, thick * 2.6); tip.position.y = 0.9;
  g.add(shaft, tip);
  return g; // unit length along +Y; rotate .z to aim, scale .y to stretch
}

// --- arrows_dot: a sweeping vector and its live dot product -----------------
function arrowsDot(p) {
  const g = new THREE.Group();
  const dial = new THREE.Mesh(G.ring, bas(0x8a7f6a, { transparent: true, opacity: 0.5 }));
  dial.scale.setScalar(0.42);
  const u = arrowMesh(GOLD, 0.035); u.scale.y = 0.4; u.rotation.z = -0.6;
  const v = arrowMesh(BLUE, 0.035); v.scale.y = 0.4;
  const bar = new THREE.Mesh(G.box, bas(GOLD, { transparent: true }));
  bar.position.y = -0.58; bar.scale.set(0.5, 0.05, 0.05);
  g.add(dial, u, v, bar);
  if (p.bar === false) bar.visible = false;
  const speed = p.speed || 0.35;
  const update = (t) => {
    if (p.corotate) {
      // both arrows swing together; only their mutual angle breathes — and the
      // bar tracks the gap alone (alignment sees relative angle, cos(A−B))
      u.rotation.z = t * 0.3;
      v.rotation.z = u.rotation.z + 1.1 + 1.0 * Math.sin(t * 0.35);
    } else {
      v.rotation.z = t * speed;
    }
    const cos = Math.cos(v.rotation.z - u.rotation.z);
    bar.scale.x = Math.max(0.02, Math.abs(cos) * 0.8);
    bar.material.color.set(cos >= 0 ? GOLD : COLD);
    bar.material.opacity = 0.35 + 0.6 * Math.abs(cos);
  };
  return { group: g, update };
}

// --- softmax_bars: wandering scores race; heights are the live softmax ------
function softmaxBars(p) {
  const n = Math.min(8, p.n || 4);
  const temp = p.temp || 1;
  const g = new THREE.Group();
  const bars = [];
  const W = 0.16, gap = 0.06, x0 = -((n - 1) * (W + gap)) / 2;
  for (let i = 0; i < n; i++) {
    const b = new THREE.Mesh(G.box, bas(GOLD, { transparent: true }));
    b.position.x = x0 + i * (W + gap);
    bars.push(b); g.add(b);
  }
  const base = new THREE.Mesh(G.box, bas(0x8a7f6a, { transparent: true, opacity: 0.5 }));
  base.position.y = -0.42; base.scale.set(n * (W + gap) + 0.1, 0.03, 0.1);
  g.add(base);
  if (p.independent) for (const b of bars) b.material.color.set(BLUE);
  const update = (t) => {
    const s = [];
    for (let i = 0; i < n; i++) s[i] = (wander(t, i + 1) * 4 - 2) / temp;
    let ws;
    if (p.independent) {
      // sigmoid gates: each bar judged alone, no shared denominator
      ws = s.map((x) => 1 / (1 + Math.exp(-x * 1.6)));
    } else {
      let m = -1e9;
      for (const x of s) if (x > m) m = x;
      let Z = 0;
      const es = s.map((x) => { const e = Math.exp(x - m); Z += e; return e; });
      ws = es.map((e) => e / Z);
    }
    for (let i = 0; i < n; i++) {
      const w = ws[i];
      const h = 0.08 + (p.independent ? 0.55 : 0.75) * w;
      bars[i].scale.set(W, h, W);
      bars[i].position.y = -0.4 + h / 2;
      bars[i].material.opacity = 0.35 + 0.65 * w;
    }
  };
  return { group: g, update };
}

// --- heat_grid: an n×n score matrix, one draw call ---------------------------
// variants: 'row_softmax' (a bright reader walks each row), 'causal' (only the
// lower triangle ever lights — the future stays dark), 'drift' (loose blobs).
function heatGrid(p) {
  const n = Math.min(8, p.n || 5);
  const R = Math.min(8, p.rows || n), C = Math.min(8, p.cols || n); // non-square OK (cross-attention)
  const variant = p.variant || 'row_softmax';
  const cells = instanced('box', R * C, DIM);
  const m = Math.max(R, C);
  const cell = 0.85 / m, pitch = 0.98 / m;
  for (let r = 0; r < R; r++)
    for (let c = 0; c < C; c++)
      setInst(cells, r * C + c,
        (c - (C - 1) / 2) * pitch, ((R - 1) / 2 - r) * pitch, 0, cell, cell, 0.02);
  cells.instanceMatrix.needsUpdate = true;
  const g = new THREE.Group();
  g.add(cells);
  const speed = p.speed || 0.6;
  const update = (t) => {
    const rowT = (t * speed) % R;          // which row the reader is on
    const row = Math.floor(rowT);
    const colT = (rowT - row) * C;         // sweep position within the row
    for (let r = 0; r < R; r++) {
      for (let c = 0; c < C; c++) {
        let v = 0.1 + 0.25 * hash(r * C + c, 7); // resting texture
        if (variant === 'causal' && c > r) v = 0.04;
        else if (variant === 'drift') v = 0.15 + 0.8 * smooth(wander(t * 0.7, r * 3 + c));
        else if (variant === 'diagonal') {
          // diagonal holds steady; off-diagonals flare and get pressed to dark
          const die = smooth(0.5 + 0.5 * Math.sin(t * 0.45 + 2));
          v = r === c ? 0.85 + 0.1 * Math.sin(t * 1.3 + r)
                      : (0.12 + 0.55 * hash(r * C + c, 11)) * (1 - 0.92 * die);
        }
        else if (variant === 'skew') {
          // zero diagonal; upper and lower triangles are mirrored negatives,
          // breathing in anti-phase (gold above, cold blue below)
          const pulse = 0.5 + 0.5 * Math.sin(t * 0.9);
          const amp = c > r ? pulse : 1 - pulse;
          _C.set(r === c ? DIM : c > r ? GOLD : COLD)
            .multiplyScalar(r === c ? 1 : 0.35 + 0.75 * amp);
          cells.setColorAt(r * C + c, _C);
          continue;
        }
        else if (r === row && (variant !== 'causal' || c <= r)) {
          const d = Math.abs(c - colT);
          v += 0.9 * Math.exp(-d * d * 2.2);
        }
        _C.setRGB(0.25 + v * 0.75, 0.2 + v * 0.62, 0.12 + v * 0.3); // ember ramp
        cells.setColorAt(r * C + c, _C);
      }
    }
    cells.instanceColor.needsUpdate = true;
  };
  return { group: g, update };
}

// --- token_stream: a sentence being written, one word at a time -------------
// cache mode: spoken tokens cool to blue (their K/V stay shelved), the current
// token burns gold under a hovering query orb, the future is unlit.
function tokenStream(p) {
  const n = Math.min(9, p.n || 6);
  const cache = p.cache !== false;
  const toks = instanced('box', n, DIM);
  const W = 0.85 / n, pitch = 0.98 / n;
  for (let i = 0; i < n; i++)
    setInst(toks, i, (i - (n - 1) / 2) * pitch, 0, 0, W, W * 0.72, 0.05);
  toks.instanceMatrix.needsUpdate = true;
  const q = new THREE.Mesh(G.sphere, bas(GOLD, { transparent: true, opacity: 0.95 }));
  q.scale.setScalar(0.045);
  const g = new THREE.Group();
  g.add(toks, q);
  const period = p.speed ? 1 / p.speed : 1.1;
  const update = (t) => {
    const k = (t / period) % (n + 1.5);     // brief rest after the line completes
    const cur = Math.floor(k);
    for (let i = 0; i < n; i++) {
      if (i < cur && i < n) _C.set(cache ? BLUE : 0x6b6455).multiplyScalar(cache ? 0.75 : 1);
      else if (i === cur) _C.set(GOLD);
      else _C.set(DIM);
      toks.setColorAt(i, _C);
    }
    toks.instanceColor.needsUpdate = true;
    const qx = (Math.min(cur, n - 1) - (n - 1) / 2) * pitch;
    q.position.set(qx, 0.14 + 0.02 * Math.sin(t * 3), 0);
    q.material.opacity = cur < n ? 0.95 : 0.15;
  };
  return { group: g, update };
}

// --- flow_nodes: a little network with signal pulses running through it -----
function flowNodes(p) {
  const layers = (p.layers && p.layers.length >= 2 ? p.layers : [2, 3, 1]).slice(0, 4);
  const xs = [], nodes = [];
  const span = 0.9, x0 = -span / 2;
  layers.forEach((count, li) => {
    const x = x0 + (li / (layers.length - 1)) * span;
    for (let i = 0; i < count; i++) {
      const y = (i - (count - 1) / 2) * 0.3;
      nodes.push({ x, y, li });
    }
    xs.push(x);
  });
  const inst = instanced('sphere', nodes.length, BLUE);
  nodes.forEach((nd, i) => setInst(inst, i, nd.x, nd.y, 0, 0.045));
  inst.instanceMatrix.needsUpdate = true;
  // Edges: full bipartite between adjacent layers, one static LineSegments.
  const edges = [];
  for (const a of nodes) for (const b of nodes)
    if (b.li === a.li + 1) edges.push([a, b]);
  const epos = new Float32Array(edges.length * 6);
  edges.forEach(([a, b], i) => epos.set([a.x, a.y, 0, b.x, b.y, 0], i * 6));
  const egeo = new THREE.BufferGeometry();
  egeo.setAttribute('position', new THREE.BufferAttribute(epos, 3));
  const lines = new THREE.LineSegments(egeo,
    new THREE.LineBasicMaterial({ color: 0x8a7f6a, transparent: true, opacity: 0.35 }));
  // Pulses: a few glow dots each travelling a (pseudo-random) edge per lap.
  const NP = 5;
  const pulses = pointsCloud(NP, 0.09, GOLD);
  const g = new THREE.Group();
  g.add(lines, inst, pulses);
  const speed = p.speed || 0.55;
  const update = (t) => {
    const arr = pulses.geometry.attributes.position.array;
    for (let i = 0; i < NP; i++) {
      const lap = Math.floor(t * speed + i * 0.37);
      const f = (t * speed + i * 0.37) % 1;
      const e = edges[Math.floor(hash(i, lap) * edges.length)];
      arr[i * 3] = e[0].x + (e[1].x - e[0].x) * f;
      arr[i * 3 + 1] = e[0].y + (e[1].y - e[0].y) * f;
      arr[i * 3 + 2] = 0;
    }
    pulses.geometry.attributes.position.needsUpdate = true;
  };
  return { group: g, update };
}

// --- curve_trace: a named function drawn in the air, a bead riding it -------
const FNS = {
  relu: (x) => Math.max(0, x),
  gelu: (x) => 0.5 * x * (1 + Math.tanh(0.7978845608 * (x + 0.044715 * x * x * x))),
  sigmoid: (x) => 1 / (1 + Math.exp(-x * 2)) - 0.5,
  tanh: (x) => Math.tanh(x * 1.5) * 0.6,
  gauss: (x) => Math.exp(-x * x * 3) - 0.25,
  sin: (x) => 0.45 * Math.sin(x * 4),
  bowl: (x) => x * x - 0.35,
  cos_decay: (x) => 0.45 * Math.cos(Math.min(Math.max((x + 1) / 2, 0), 1) * Math.PI) ,
  exp_rise: (x) => 0.55 * (Math.exp(x) - 1) / (Math.E - 1) - 0.1,
  decay: (x) => 0.85 * Math.exp(-(x + 1) * 1.6) - 0.28,
};
function curveTrace(p) {
  const fn = FNS[p.fn] || FNS.sin;
  const N = 64, X = 0.55, Y = 0.5;
  const pts = [];
  for (let i = 0; i <= N; i++) {
    const x = -1 + (2 * i) / N;
    pts.push(new THREE.Vector3(x * X, Math.min(Y, Math.max(-Y, fn(x))) * 0.75, 0));
  }
  const curve = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.9 }));
  const apos = new Float32Array([-X - 0.05, 0, 0, X + 0.05, 0, 0, 0, -Y * 0.8, 0, 0, Y * 0.8, 0]);
  const ageo = new THREE.BufferGeometry();
  ageo.setAttribute('position', new THREE.BufferAttribute(apos, 3));
  const axes = new THREE.LineSegments(ageo,
    new THREE.LineBasicMaterial({ color: 0x8a7f6a, transparent: true, opacity: 0.45 }));
  const bead = new THREE.Mesh(G.sphere, bas(0xfff3d0));
  bead.scale.setScalar(0.035);
  const g = new THREE.Group();
  g.add(axes, curve, bead);
  const speed = p.speed || 0.25;
  const update = (t) => {
    const f = (t * speed) % 1;
    const i = Math.min(N - 1, Math.floor(f * N));
    const a = pts[i], b = pts[i + 1], k = f * N - i;
    bead.position.set(a.x + (b.x - a.x) * k, a.y + (b.y - a.y) * k, 0.01);
  };
  return { group: g, update };
}

// --- noise_morph: a shape dissolving into noise and finding its way back ----
const SHAPES = {
  ring: (i, n) => { const a = (i / n) * Math.PI * 2; return [Math.cos(a) * 0.38, Math.sin(a) * 0.38]; },
  spiral: (i, n) => { const a = (i / n) * Math.PI * 4, r = 0.08 + 0.32 * (i / n); return [Math.cos(a) * r, Math.sin(a) * r]; },
  smile: (i, n) => { // a face: two eyes + arc mouth — unmistakably "an image"
    if (i < n * 0.15) return [-0.15, 0.15];
    if (i < n * 0.3) return [0.15, 0.15];
    const k = (i - n * 0.3) / (n * 0.7), a = Math.PI * (0.2 + 0.6 * k);
    return [Math.cos(a) * 0.3, -Math.sin(a) * 0.3 + 0.08];
  },
  grid: (i, n) => { const s = Math.ceil(Math.sqrt(n)); return [((i % s) / (s - 1) - 0.5) * 0.7, (Math.floor(i / s) / (s - 1) - 0.5) * 0.7]; },
};
function noiseMorph(p) {
  const n = 90;
  const shape = SHAPES[p.shape] || SHAPES.ring;
  const target = [];
  for (let i = 0; i < n; i++) target.push(shape(i, n));
  const cloud = pointsCloud(n, 0.055, GOLD);
  const g = new THREE.Group();
  g.add(cloud);
  const period = p.speed ? 8 / p.speed : 8;
  const update = (t) => {
    const ph = (t % period) / period;                 // 0→1 over one breath
    const k = smooth(1 - Math.abs(ph * 2 - 1) * 1.15); // shape→noise→shape
    const arr = cloud.geometry.attributes.position.array;
    for (let i = 0; i < n; i++) {
      const nx = (hash(i, 1) - 0.5) * 1.0, ny = (hash(i, 2) - 0.5) * 0.9;
      const jx = 0.02 * Math.sin(t * 1.7 + i), jy = 0.02 * Math.cos(t * 1.3 + i * 2);
      arr[i * 3] = target[i][0] * (1 - k) + nx * k + jx;
      arr[i * 3 + 1] = target[i][1] * (1 - k) + ny * k + jy;
      arr[i * 3 + 2] = 0;
    }
    cloud.geometry.attributes.position.needsUpdate = true;
    cloud.material.color.lerpColors(_C.set(GOLD), _C2.set(COLD), k);
  };
  return { group: g, update };
}
const _C2 = new THREE.Color();

// --- pull_push: matched pair drawn together, strangers pushed apart ---------
function pullPush(p) {
  const g = new THREE.Group();
  const a = new THREE.Mesh(G.sphere, bas(GOLD)); a.scale.setScalar(0.07);
  const b = new THREE.Mesh(G.sphere, bas(GOLD)); b.scale.setScalar(0.07);
  const c = new THREE.Mesh(G.sphere, bas(COLD)); c.scale.setScalar(0.06);
  const d = new THREE.Mesh(G.sphere, bas(COLD)); d.scale.setScalar(0.06);
  const lpos = new Float32Array(6);
  const lgeo = new THREE.BufferGeometry();
  lgeo.setAttribute('position', new THREE.BufferAttribute(lpos, 3));
  const spring = new THREE.LineSegments(lgeo,
    new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.6 }));
  g.add(a, b, c, d, spring);
  const update = (t) => {
    const k = smooth(0.5 + 0.5 * Math.sin(t * 0.5));  // 0 = scattered, 1 = trained
    const near = 0.34 - 0.24 * k;                     // positives pulled in
    const far = 0.22 + 0.26 * k;                      // negatives pushed out
    a.position.set(-near, 0.05 * Math.sin(t), 0);
    b.position.set(near, 0.05 * Math.cos(t * 1.1), 0);
    c.position.set(-0.1 - far * 0.6, far * 0.8, 0);
    d.position.set(0.15 + far * 0.5, -far * 0.85, 0);
    lpos.set([a.position.x, a.position.y, 0, b.position.x, b.position.y, 0]);
    lgeo.attributes.position.needsUpdate = true;
    spring.material.opacity = 0.15 + 0.55 * k;
  };
  return { group: g, update };
}

// --- stack_rise: depth as a tower; activation climbs it ---------------------
function stackRise(p) {
  const n = Math.min(8, p.n || 5);
  const slabs = instanced('box', n, DIM);
  const H = 0.9, sh = (H / n) * 0.62, pitch = H / n;
  for (let i = 0; i < n; i++)
    setInst(slabs, i, 0, -H / 2 + pitch * (i + 0.5), 0, 0.55 - 0.03 * i, sh, 0.3);
  slabs.instanceMatrix.needsUpdate = true;
  const g = new THREE.Group();
  g.add(slabs);
  let skipDot = null, skipPts = null;
  if (p.skip) { // one long residual arc past the tower, a dot riding it
    const pts = [];
    for (let i = 0; i <= 24; i++) {
      const f = i / 24;
      pts.push(new THREE.Vector3(0.42 + 0.16 * Math.sin(f * Math.PI), -H / 2 + f * H, 0));
    }
    skipPts = pts;
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: BLUE, transparent: true, opacity: 0.6 })));
    skipDot = new THREE.Mesh(G.sphere, bas(BLUE));
    skipDot.scale.setScalar(0.035);
    g.add(skipDot);
  }
  const speed = p.speed || 0.5;
  const update = (t) => {
    const k = (t * speed) % 1.4; // pulse position (with a rest at the top)
    for (let i = 0; i < n; i++) {
      const d = Math.abs((i + 0.5) / n - k);
      const v = 0.18 + 0.85 * Math.exp(-d * d * 34);
      _C.setRGB(0.25 + v * 0.75, 0.2 + v * 0.6, 0.12 + v * 0.3);
      slabs.setColorAt(i, _C);
    }
    slabs.instanceColor.needsUpdate = true;
    if (skipDot) {
      const f = Math.min(1, k / 1.0);
      const i = Math.min(23, Math.floor(f * 24)), fr = f * 24 - i;
      const a2 = skipPts[i], b2 = skipPts[i + 1];
      skipDot.position.set(a2.x + (b2.x - a2.x) * fr, a2.y + (b2.y - a2.y) * fr, 0);
    }
  };
  return { group: g, update };
}

// --- mask_tiles: an image with pieces hidden; the hidden set keeps changing --
function maskTiles(p) {
  const n = Math.min(8, p.n || 6);
  const ratio = p.ratio != null ? p.ratio : 0.5;
  const tiles = instanced('box', n * n, GOLD);
  const cell = 0.8 / n, pitch = 0.92 / n;
  for (let r = 0; r < n; r++)
    for (let c = 0; c < n; c++)
      setInst(tiles, r * n + c,
        (c - (n - 1) / 2) * pitch, ((n - 1) / 2 - r) * pitch, 0, cell, cell, 0.02);
  tiles.instanceMatrix.needsUpdate = true;
  const g = new THREE.Group();
  g.add(tiles);
  const period = p.speed ? 2.2 / p.speed : 2.2;
  const update = (t) => {
    const cyc = Math.floor(t / period);
    const f = smooth(Math.min(1, ((t / period) - cyc) * 3)); // quick fade per reshuffle
    for (let i = 0; i < n * n; i++) {
      const hidden = hash(i, cyc) < ratio;
      const wasHidden = hash(i, cyc - 1) < ratio;
      const dark = wasHidden * (1 - f) + hidden * f;
      // visible tiles keep a faint per-tile tint so the "image" reads as one
      const v = 0.45 + 0.45 * hash(i, 99);
      _C.setRGB(0.25 + v * 0.65, 0.2 + v * 0.55, 0.12 + v * 0.35).multiplyScalar(1 - 0.88 * dark);
      tiles.setColorAt(i, _C);
    }
    tiles.instanceColor.needsUpdate = true;
  };
  return { group: g, update };
}

// --- orbit_phase: clock hands at geometric speeds — position as phases ------
function orbitPhase(p) {
  const g = new THREE.Group();
  const dial = new THREE.Mesh(G.ring, bas(0x8a7f6a, { transparent: true, opacity: 0.5 }));
  dial.scale.setScalar(0.42);
  const nH = Math.min(3, p.hands || 3);
  const hands = [];
  const colors = [GOLD, BLUE, 0xd8a8ff];
  for (let i = 0; i < nH; i++) {
    const h = arrowMesh(colors[i], 0.028);
    h.scale.y = 0.4 - i * 0.08;
    hands.push(h); g.add(h);
  }
  g.add(dial);
  const speed = p.speed || 0.4;
  const update = (t) => {
    for (let i = 0; i < nH; i++) hands[i].rotation.z = -t * speed * Math.pow(3, i);
  };
  return { group: g, update };
}

// --- balance_tilt: two demands on one beam ----------------------------------
function balanceTilt(p) {
  const g = new THREE.Group();
  const post = new THREE.Mesh(G.cyl, bas(0x8a7f6a));
  post.scale.set(0.03, 0.5, 0.03); post.position.y = -0.2;
  const beam = new THREE.Group();
  const bar = new THREE.Mesh(G.box, bas(0xb8a888));
  bar.scale.set(0.8, 0.035, 0.05);
  beam.add(bar);
  const pans = [];
  for (const s of [-1, 1]) {
    const wire = new THREE.Mesh(G.cyl, bas(0x8a7f6a));
    wire.scale.set(0.012, 0.16, 0.012); wire.position.set(s * 0.38, -0.08, 0);
    const pan = new THREE.Mesh(G.cyl, bas(s < 0 ? GOLD : BLUE, { transparent: true }));
    pan.scale.set(0.1, 0.02, 0.1); pan.position.set(s * 0.38, -0.17, 0);
    beam.add(wire, pan); pans.push(pan);
  }
  beam.position.y = 0.05;
  g.add(post, beam);
  const speed = p.speed || 0.35;
  const update = (t) => {
    const k = Math.sin(t * speed);
    beam.rotation.z = 0.3 * k;
    pans[0].material.opacity = 0.45 + 0.5 * Math.max(0, -k);
    pans[1].material.opacity = 0.45 + 0.5 * Math.max(0, k);
  };
  return { group: g, update };
}

// --- funnel_flow: many things pressed through a narrow waist ----------------
function funnelFlow(p) {
  const n = 46;
  const cloud = pointsCloud(n, 0.055, GOLD);
  const ring = new THREE.Mesh(G.ring, bas(BLUE, { transparent: true, opacity: 0.8 }));
  ring.scale.setScalar(0.12);
  const g = new THREE.Group();
  g.add(cloud, ring);
  const speed = p.speed || 0.35;
  const wide = p.reverse ? -0.45 : 0.45; // reverse = expansion out of the waist
  const update = (t) => {
    const arr = cloud.geometry.attributes.position.array;
    for (let i = 0; i < n; i++) {
      const f = (t * speed + hash(i, 3)) % 1;         // 0 wide → 1 narrow (through)
      const spread = Math.max(0.04, 0.42 * (1 - f * 1.35)); // pinches at the ring
      const a = hash(i, 5) * Math.PI * 2;
      const r = spread * (0.3 + 0.7 * hash(i, 8));
      arr[i * 3] = wide * (1 - 2 * f) * -1;
      arr[i * 3 + 1] = Math.cos(a) * r;
      arr[i * 3 + 2] = Math.sin(a) * r * 0.4;
    }
    cloud.geometry.attributes.position.needsUpdate = true;
    ring.rotation.y = Math.PI / 2;
    ring.rotation.x = 0.15 * Math.sin(t * 0.7);
  };
  return { group: g, update };
}

// --- field_warp: a sheet of space, bending ----------------------------------
function fieldWarp(p) {
  const seg = 14;
  const geo = new THREE.PlaneGeometry(0.95, 0.95, seg, seg);
  const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
    color: p.color || BLUE, wireframe: true, transparent: true, opacity: 0.5,
  }));
  mesh.rotation.x = -0.9; // tilted toward the viewer so the relief reads
  const g = new THREE.Group();
  g.add(mesh);
  const pos = geo.attributes.position;
  const amp = p.amp || 0.09, speed = p.speed || 0.6;
  const update = (t) => {
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), y = pos.getY(i);
      pos.setZ(i, amp * Math.sin(x * 7 + t * speed) * Math.cos(y * 6 + t * speed * 0.8));
    }
    pos.needsUpdate = true;
  };
  return { group: g, update };
}

// --- descend_bowl: gradient descent, literally — hops down a loss bowl ------
function descendBowl(p) {
  const N = 48, X = 0.55;
  const pts = [];
  for (let i = 0; i <= N; i++) {
    const x = -1 + (2 * i) / N;
    pts.push(new THREE.Vector3(x * X, (x * x - 0.35) * 0.8, 0));
  }
  const bowl = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color: 0x8a7f6a, transparent: true, opacity: 0.8 }));
  const bead = new THREE.Mesh(G.sphere, bas(GOLD));
  bead.scale.setScalar(0.045);
  const g = new THREE.Group();
  g.add(bowl, bead);
  // Precompute the hop sequence: x <- x - lr * 2x from alternating sides.
  const hops = [];
  let x = 0.95;
  for (let i = 0; i < 9; i++) { hops.push(x); x -= (p.lr || 0.35) * 2 * x; }
  hops.push(0);
  const period = p.speed ? 4.5 / p.speed : 4.5;
  const update = (t) => {
    const cyc = Math.floor(t / period);
    const side = cyc % 2 === 0 ? 1 : -1;              // restart from the other rim
    const f = ((t / period) - cyc) * hops.length;
    const i = Math.min(hops.length - 2, Math.floor(f));
    const k = smooth(Math.min(1, (f - i) * 1.6));     // hop, then settle
    const hx = (hops[i] + (hops[i + 1] - hops[i]) * k) * side;
    bead.position.set(hx * X, (hx * hx - 0.35) * 0.8 + 0.03, 0.01);
  };
  return { group: g, update };
}

// --- rain_bell: random draws rain down and pile up into a bell --------------
function rainBell(p) {
  const bins = 9;
  const inst = instanced('box', bins, GOLD);
  const W = 0.8, bw = W / bins;
  const bell = [];
  for (let i = 0; i < bins; i++) {
    const x = (i - (bins - 1) / 2) / ((bins - 1) / 2);
    bell.push(Math.exp(-x * x * 2.2));
  }
  const ND = 10;
  const drops = pointsCloud(ND, 0.05, 0xfff3d0);
  const g = new THREE.Group();
  g.add(inst, drops);
  const period = p.speed ? 7 / p.speed : 7;
  const update = (t) => {
    const fill = smooth(Math.min(1, ((t % period) / period) * 1.25));
    for (let i = 0; i < bins; i++) {
      const h = 0.03 + 0.5 * bell[i] * fill;
      setInst(inst, i, -W / 2 + bw * (i + 0.5), -0.35 + h / 2, 0, bw * 0.8, h, bw * 0.8);
    }
    inst.instanceMatrix.needsUpdate = true;
    const arr = drops.geometry.attributes.position.array;
    for (let i = 0; i < ND; i++) {
      const cyc = t * 0.85 + hash(i, 4) * 3;
      const lap = Math.floor(cyc), f = cyc - lap;
      // landing spot = mean of three uniforms: bell-shaped by construction
      const u = (hash(i, lap) + hash(i, lap + 17) + hash(i, lap + 31)) / 3;
      const x = (u - 0.5) * W * 1.5;
      const bin = Math.min(bins - 1, Math.max(0, Math.floor((x + W / 2) / bw)));
      const top = -0.32 + 0.5 * bell[bin] * fill;
      arr[i * 3] = x;
      arr[i * 3 + 1] = 0.5 - f * (0.5 - top);
      arr[i * 3 + 2] = 0;
    }
    drops.geometry.attributes.position.needsUpdate = true;
  };
  return { group: g, update };
}

// --- bell_slide: one Gaussian; μ slides it, σ breathes it (area held) -------
function bellSlide(p) {
  const N = 48, X = 0.5;
  const pos = new Float32Array((N + 1) * 3);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const curve = new THREE.Line(geo,
    new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.95 }));
  const apos = new Float32Array([-X - 0.05, -0.3, 0, X + 0.05, -0.3, 0]);
  const ageo = new THREE.BufferGeometry();
  ageo.setAttribute('position', new THREE.BufferAttribute(apos, 3));
  const axis = new THREE.LineSegments(ageo,
    new THREE.LineBasicMaterial({ color: 0x8a7f6a, transparent: true, opacity: 0.5 }));
  const g = new THREE.Group();
  g.add(axis, curve);
  const speed = p.speed || 1;
  const update = (t) => {
    const mu = 0.3 * Math.sin(t * 0.37 * speed);
    const sig = 0.55 + 0.28 * Math.sin(t * 0.21 * speed + 2);
    const amp = 0.24 / sig; // taller when narrow: total probability is fixed
    for (let i = 0; i <= N; i++) {
      const x = -1 + (2 * i) / N;
      pos[i * 3] = x * X;
      pos[i * 3 + 1] = -0.3 + amp * Math.exp(-((x - mu) ** 2) / (2 * sig * sig * 0.25));
      pos[i * 3 + 2] = 0;
    }
    geo.attributes.position.needsUpdate = true;
  };
  return { group: g, update };
}

// --- circle_ellipse: SVD in motion — the unit circle rotated, stretched, ----
// rotated. Only the stretch spoils the roundness. stages:true pauses between
// the three motions so each reads separately.
function circleEllipse(p) {
  const N = 40, R = 0.19;
  const base = [];
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2;
    base.push([Math.cos(a) * R, Math.sin(a) * R]);
  }
  const cloud = pointsCloud(N, 0.05, GOLD);
  const g = new THREE.Group();
  g.add(cloud);
  const period = p.speed ? 9 / p.speed : 9;
  const update = (t) => {
    const f = (t % period) / period;
    // three motion phases (+ settle): rotate in, stretch, rotate out
    let rotA = 0, sx = 1, sy = 1, rotB = 0;
    const seg = p.stages ? 0.26 : 0.3; // stages leaves little holds between
    const k1 = smooth(f / seg), k2 = smooth((f - (p.stages ? 0.34 : 0.3)) / seg),
          k3 = smooth((f - (p.stages ? 0.68 : 0.6)) / seg);
    rotA = -Math.PI / 4 * k1;
    sx = 1 + 1.3 * k2; sy = 1 - 0.55 * k2;
    rotB = Math.PI / 4 * k3;
    const ca = Math.cos(rotA), sa = Math.sin(rotA);
    const cb = Math.cos(rotB), sb = Math.sin(rotB);
    const arr = cloud.geometry.attributes.position.array;
    for (let i = 0; i < N; i++) {
      let x = base[i][0], y = base[i][1];
      let x1 = x * ca - y * sa, y1 = x * sa + y * ca;   // Vᵀ
      x1 *= sx; y1 *= sy;                               // Σ — the only stretch
      arr[i * 3] = x1 * cb - y1 * sb;                   // U
      arr[i * 3 + 1] = x1 * sb + y1 * cb;
      arr[i * 3 + 2] = 0;
    }
    cloud.geometry.attributes.position.needsUpdate = true;
    cloud.material.color.set(k2 > 0.05 && k2 < 0.95 ? 0xffe9a8 : GOLD);
  };
  return { group: g, update };
}

// --- decay_bars: a fast-decaying spectrum; a sweeping cut keeps the few -----
function decayBars(p) {
  const heights = p.values || [1, 0.62, 0.45, 0.11, 0.045, 0.015];
  const n = heights.length;
  const inst = instanced('box', n, GOLD);
  const W = 0.8, bw = W / n;
  const H = 0.55;
  for (let i = 0; i < n; i++) {
    const h = 0.02 + heights[i] * H;
    setInst(inst, i, -W / 2 + bw * (i + 0.5), -0.28 + h / 2, 0, bw * 0.7, h, bw * 0.7);
  }
  inst.instanceMatrix.needsUpdate = true;
  const cut = new THREE.Mesh(G.box, bas(BLUE, { transparent: true, opacity: 0.75 }));
  cut.scale.set(W + 0.12, 0.012, 0.05);
  const g = new THREE.Group();
  g.add(inst, cut);
  const update = (t) => {
    const lvl = 0.03 + 0.42 * smooth(0.5 + 0.5 * Math.sin(t * 0.35)); // the keep-line
    cut.position.y = -0.28 + lvl * H / 0.55 * 0.55;
    for (let i = 0; i < n; i++) {
      const kept = heights[i] >= lvl;
      _C.set(kept ? GOLD : DIM);
      inst.setColorAt(i, _C);
    }
    inst.instanceColor.needsUpdate = true;
  };
  return { group: g, update };
}

// --- slide_window: convolution itself — a kernel bracket walks the signal ---
function slideWindow(p) {
  const n = Math.min(10, p.n || 8), k = 3;
  const input = instanced('box', n, CREAMY);
  const output = instanced('box', n - k + 1, DIM);
  const W = 0.9, bw = W / n;
  for (let i = 0; i < n; i++)
    setInst(input, i, -W / 2 + bw * (i + 0.5), 0.14, 0, bw * 0.78, bw * 0.78, 0.04);
  input.instanceMatrix.needsUpdate = true;
  for (let i = 0; i < n - k + 1; i++)
    setInst(output, i, -W / 2 + bw * (i + 1.5), -0.16, 0, bw * 0.78, bw * 0.78, 0.04);
  output.instanceMatrix.needsUpdate = true;
  // the kernel: a wireframe bracket k cells wide gliding along the input row
  const frame = new THREE.Mesh(G.box, bas(GOLD, { transparent: true, opacity: 0.35 }));
  frame.scale.set(bw * k, bw * 1.25, 0.06);
  frame.position.y = 0.14;
  const g = new THREE.Group();
  g.add(input, output, frame);
  const period = p.speed ? 1.1 / p.speed : 1.1;
  const stops = n - k + 1;
  const update = (t) => {
    const cyc = (t / period) % (stops + 1.5);       // pause after each pass
    const pos = Math.min(stops - 1, cyc);
    const stop = Math.floor(pos);
    frame.position.x = -W / 2 + bw * (Math.min(pos, stops - 1) + k / 2);
    for (let i = 0; i < n; i++) {
      const under = i >= pos - 0.3 && i <= pos + k - 0.7;
      _C.set(under ? GOLD : CREAMY).multiplyScalar(under ? 1 : 0.55);
      input.setColorAt(i, _C);
    }
    input.instanceColor.needsUpdate = true;
    for (let i = 0; i < stops; i++) {
      _C.set(i <= stop && cyc < stops + 0.5 ? GOLD : DIM);
      if (i === stop) _C.multiplyScalar(1.2);
      output.setColorAt(i, _C);
    }
    output.instanceColor.needsUpdate = true;
  };
  return { group: g, update };
}
const CREAMY = 0xcfc4a8;

// --- lift_matrix: the hat and the vee — three beads rise and unfold into a --
// 3×3 skew matrix (zero diagonal, gold upper mirrored by blue negatives
// below), then read back down to the bare vector. Nothing lost either way.
function liftMatrix(p) {
  const inst = instanced('box', 9, GOLD);
  const pitch = 0.2, cell = 0.13;
  const freeIdx = [[-1, 0, 1], [0, -1, 2], [1, 2, -1]]; // shared free param per cell
  const gridPos = [], rodPos = [], kinds = [];
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
      gridPos.push([(c - 1) * pitch, (1 - r) * pitch + 0.08]);
      const fi = freeIdx[r][c];
      rodPos.push([fi < 0 ? 0 : (fi - 1) * 0.24, -0.34]);
      kinds.push(r === c ? 'zero' : c > r ? 'pos' : 'neg');
    }
  }
  const g = new THREE.Group();
  g.add(inst);
  const period = p.speed ? 7 / p.speed : 7;
  const update = (t) => {
    const f = (t % period) / period;
    const k = smooth(1 - Math.abs(f * 2 - 1) * 1.2); // rod → matrix → rod
    for (let i = 0; i < 9; i++) {
      const x = rodPos[i][0] + (gridPos[i][0] - rodPos[i][0]) * k;
      const y = rodPos[i][1] + (gridPos[i][1] - rodPos[i][1]) * k;
      // diagonal zeros exist only in the matrix costume — they grow in with k
      const s = kinds[i] === 'zero' ? cell * 0.85 * k + 0.001 : cell;
      setInst(inst, i, x, y, 0, s, s, 0.03);
      _C.set(kinds[i] === 'zero' ? DIM : kinds[i] === 'pos' ? GOLD : COLD);
      if (kinds[i] === 'neg') _C.multiplyScalar(0.55 + 0.45 * k); // negatives appear as it lifts
      inst.setColorAt(i, _C);
    }
    inst.instanceMatrix.needsUpdate = true;
    inst.instanceColor.needsUpdate = true;
  };
  return { group: g, update };
}

// --- tangent_touch: a flat line kissing a curve; twin walkers drift apart ---
// The gold bead takes straight steps on the tangent; the blue ghost makes the
// matching move along the arc. Near the touch point they agree; far out the
// gap is the curvature, visible.
function tangentTouch(p) {
  const R = 0.55, touch = { x: 0, y: -0.12 };  // arc center below; touch on top
  const arcPts = [];
  for (let i = 0; i <= 40; i++) {
    const a = Math.PI / 2 + (i / 40 - 0.5) * 1.9; // arc spanning the touch point
    arcPts.push(new THREE.Vector3(touch.x + Math.cos(a) * R, touch.y - R + Math.sin(a) * R, 0));
  }
  const arc = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(arcPts),
    new THREE.LineBasicMaterial({ color: BLUE, transparent: true, opacity: 0.8 }));
  const tan = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-0.5, touch.y, 0), new THREE.Vector3(0.5, touch.y, 0)]),
    new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.9 }));
  const walker = new THREE.Mesh(G.sphere, bas(GOLD));
  walker.scale.setScalar(0.038);
  const ghost = new THREE.Mesh(G.sphere, bas(BLUE, { transparent: true, opacity: 0.9 }));
  ghost.scale.setScalar(0.034);
  const g = new THREE.Group();
  g.add(arc, tan, walker, ghost);
  const period = p.speed ? 6 / p.speed : 6;
  const update = (t) => {
    const f = (t % period) / period;
    const s = Math.sin(f * Math.PI) * 0.48 * (f < 0.5 ? 1 : -1); // out, back, other side
    walker.position.set(s, touch.y, 0.01);
    const a = Math.PI / 2 + s / R; // same arclength walked along the curve
    ghost.position.set(touch.x + Math.cos(a) * R, touch.y - R + Math.sin(a) * R, 0.01);
  };
  return { group: g, update };
}

// --- field_flow: a velocity field, and beads that ride it ------------------
// The emblem of flow matching: arrows ARE the learned field, and generation is
// just following them. `stochastic: true` adds a random kick per step — the
// same field sampled as an SDE (pollen in water) rather than an ODE (a ball on
// a ramp), so one start becomes a cloud of paths.
function fieldFlow(p) {
  const NX = 7, NY = 5, N = NX * NY;
  const arrows = instanced('cone', N, BLUE);
  const g = new THREE.Group();
  g.add(arrows);
  const NB = 14;
  const beads = pointsCloud(NB, 0.06, GOLD);
  g.add(beads);
  const X0 = -0.46, X1 = 0.46, Y0 = -0.3, Y1 = 0.3;
  const jitter = p.stochastic ? 0.02 : 0;
  // The field itself: a rightward drift that swells and leans over time.
  const vx = (x, y, t) => 0.55 + 0.3 * Math.sin(y * 4.5 + t * 0.5);
  const vy = (x, y, t) => 0.34 * Math.sin(x * 3.2 - t * 0.4);
  // Seed the beads down the left edge.
  {
    const arr = beads.geometry.attributes.position.array;
    for (let i = 0; i < NB; i++) {
      arr[i * 3] = X0 + hash(i, 2) * 0.15;
      arr[i * 3 + 1] = Y0 + hash(i, 5) * (Y1 - Y0);
      arr[i * 3 + 2] = 0.01;
    }
  }
  const speed = p.speed || 1;
  const update = (t) => {
    for (let r = 0; r < NY; r++) {
      for (let c = 0; c < NX; c++) {
        const x = X0 + (c / (NX - 1)) * (X1 - X0);
        const y = Y0 + (r / (NY - 1)) * (Y1 - Y0);
        const u = vx(x, y, t), v = vy(x, y, t);
        const mag = Math.hypot(u, v);
        setInstRot(arrows, r * NX + c, x, y,
          0.035, 0.075 + 0.05 * mag, Math.atan2(v, u) - Math.PI / 2);
        _C.set(BLUE).multiplyScalar(0.5 + 0.5 * mag);
        arrows.setColorAt(r * NX + c, _C);
      }
    }
    arrows.instanceMatrix.needsUpdate = true;
    arrows.instanceColor.needsUpdate = true;
    const arr = beads.geometry.attributes.position.array;
    const dt = 0.016 * speed;
    for (let i = 0; i < NB; i++) {
      let x = arr[i * 3], y = arr[i * 3 + 1];
      x += vx(x, y, t) * dt + (jitter ? (Math.random() - 0.5) * jitter : 0);
      y += vy(x, y, t) * dt + (jitter ? (Math.random() - 0.5) * jitter : 0);
      if (x > X1 || y < Y0 - 0.12 || y > Y1 + 0.12) {   // reached data: respawn as noise
        x = X0; y = Y0 + Math.random() * (Y1 - Y0);
      }
      arr[i * 3] = x; arr[i * 3 + 1] = y;
    }
    beads.geometry.attributes.position.needsUpdate = true;
  };
  return { group: g, update };
}

// --- path_race: why a straight path forgives big steps ---------------------
// Both beads take the SAME four big Euler steps. On the straight path the
// bead lands exactly on target; on the curved one each step follows the local
// tangent and cuts the corner, so it drifts off (a dim ghost marks where it
// should have been). Hence: straight path → few steps; curved → many.
function pathRace(p) {
  const AX = -0.42, BX = 0.42, TOP = 0.2, BOT = -0.22;
  const straight = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(AX, TOP, 0), new THREE.Vector3(BX, TOP, 0)]),
    new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.85 }));
  // The curved path: a bowed arc from A to B.
  const curveY = (u) => BOT + 0.3 * Math.sin(u * Math.PI);
  const cpts = [];
  for (let i = 0; i <= 40; i++) {
    const u = i / 40;
    cpts.push(new THREE.Vector3(AX + (BX - AX) * u, curveY(u), 0));
  }
  const curved = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(cpts),
    new THREE.LineBasicMaterial({ color: BLUE, transparent: true, opacity: 0.75 }));
  const beadS = new THREE.Mesh(G.sphere, bas(GOLD));
  beadS.scale.setScalar(0.04);
  const beadC = new THREE.Mesh(G.sphere, bas(BLUE));
  beadC.scale.setScalar(0.04);
  const ghost = new THREE.Mesh(G.sphere, bas(CREAMY, { transparent: true, opacity: 0.4 }));
  ghost.scale.setScalar(0.03);
  const g = new THREE.Group();
  g.add(straight, curved, beadS, beadC, ghost);
  const STEPS = p.steps || 4;
  // Precompute the curved bead's Euler trail: step along the local tangent.
  const trail = [];
  {
    let x = AX, y = curveY(0);
    trail.push([x, y]);
    const du = 1 / STEPS, dx = (BX - AX) * du;
    for (let k = 0; k < STEPS; k++) {
      const u = k / STEPS;
      const slope = (curveY(u + 0.004) - curveY(u - 0.004)) / (0.008 * (BX - AX));
      x += dx; y += slope * dx;          // tangent step — cuts the corner
      trail.push([x, y]);
    }
  }
  const period = p.speed ? 5 / p.speed : 5;
  const update = (t) => {
    const f = (t % period) / period;
    const k = Math.min(STEPS, f * (STEPS + 0.9));   // hop, then rest
    const i = Math.min(STEPS - 1, Math.floor(k));
    const frac = smooth(Math.min(1, (k - i) * 1.7));
    const u0 = i / STEPS, u1 = (i + 1) / STEPS, u = u0 + (u1 - u0) * frac;
    beadS.position.set(AX + (BX - AX) * u, TOP, 0.01);
    const a = trail[i], b = trail[i + 1];
    beadC.position.set(a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac, 0.01);
    ghost.position.set(AX + (BX - AX) * u, curveY(u), 0.005);
  };
  return { group: g, update };
}

// --- fork_paths: commit to a mode, or average into the wall ----------------
// One observation, two valid answers. The gold bead SAMPLES one branch and
// commits (alternating between them); the grey bead takes the mean of both
// and drives straight into the obstacle between them.
function forkPaths(p) {
  const X0 = -0.42, X1 = 0.4, SPREAD = 0.26;
  const branch = (sign) => {
    const pts = [];
    for (let i = 0; i <= 24; i++) {
      const u = i / 24;
      pts.push(new THREE.Vector3(X0 + (X1 - X0) * u, sign * SPREAD * smooth(u), 0));
    }
    return pts;
  };
  const up = branch(1), down = branch(-1);
  const g = new THREE.Group();
  for (const pts of [up, down]) {
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: GOLD, transparent: true, opacity: 0.4 })));
  }
  const wall = new THREE.Mesh(G.box, bas(0xd06a5a, { transparent: true, opacity: 0.65 }));
  wall.scale.set(0.07, 0.16, 0.05);
  wall.position.set(0.16, 0, 0);
  const bead = new THREE.Mesh(G.sphere, bas(GOLD));
  bead.scale.setScalar(0.045);
  const mean = new THREE.Mesh(G.sphere, bas(0x8f8f8f));
  mean.scale.setScalar(0.04);
  g.add(wall, bead, mean);
  const period = p.speed ? 4 / p.speed : 4;
  const update = (t) => {
    const lap = Math.floor(t / period);
    const f = (t % period) / period;
    const u = Math.min(1, f * 1.25);
    const pts = (lap % 2 === 0) ? up : down;        // sample a mode, then commit
    const i = Math.min(23, Math.floor(u * 24)), fr = u * 24 - i;
    const a = pts[i], b = pts[i + 1];
    bead.position.set(a.x + (b.x - a.x) * fr, a.y + (b.y - a.y) * fr, 0.01);
    mean.position.set(X0 + (X1 - X0) * u, 0, 0.01);  // the average of both modes
    const hit = mean.position.x > wall.position.x - 0.05;
    mean.material.color.set(hit ? 0xd06a5a : 0x8f8f8f);
    wall.material.opacity = hit ? 0.9 : 0.55;
  };
  return { group: g, update };
}

export const WIDGET_BUILDERS = {
  field_flow: fieldFlow,
  path_race: pathRace,
  fork_paths: forkPaths,
  rain_bell: rainBell,
  bell_slide: bellSlide,
  circle_ellipse: circleEllipse,
  decay_bars: decayBars,
  slide_window: slideWindow,
  tangent_touch: tangentTouch,
  lift_matrix: liftMatrix,
  arrows_dot: arrowsDot,
  softmax_bars: softmaxBars,
  heat_grid: heatGrid,
  token_stream: tokenStream,
  flow_nodes: flowNodes,
  curve_trace: curveTrace,
  noise_morph: noiseMorph,
  pull_push: pullPush,
  stack_rise: stackRise,
  mask_tiles: maskTiles,
  orbit_phase: orbitPhase,
  balance_tilt: balanceTilt,
  funnel_flow: funnelFlow,
  field_warp: fieldWarp,
  descend_bowl: descendBowl,
};

// Build a floating widget from an exhibit's `float` spec. The wrapper adds the
// gentle levitation bob (phase desyncs neighbours) and an overall scale.
export function makeWidget(spec, pal, phase = 0) {
  const builder = WIDGET_BUILDERS[spec.widget];
  if (!builder) {
    console.warn(`unknown float widget '${spec.widget}'`);
    return null;
  }
  const made = builder(spec, pal);
  const wrap = new THREE.Group();
  wrap.add(made.group);
  wrap.scale.setScalar(0.9 * (spec.scale || 1));
  const inner = made.group;
  const innerUpdate = made.update;
  const update = (t) => {
    inner.position.y = 0.05 * Math.sin(t * 0.8 + phase);
    if (innerUpdate) innerUpdate(t + phase);
  };
  return { group: wrap, update };
}
