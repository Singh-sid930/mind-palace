// Turns the solved layout into meshes: floors, walls (with doorway gaps and
// lintels), trim, lights, the star dome and floating room banners.
// Everything is primitives + canvas textures — zero binary assets.

import * as THREE from 'three';
import { palette } from './palettes.js';
import { bannerTexture } from './text.js';

const WALL_T = 0.32;

function lambert(color, extra = {}) {
  return new THREE.MeshLambertMaterial({ color, ...extra });
}

// One wall side runs lo..hi at fixed coordinate `at`. Doors split it into
// segments, each segment becomes a box; each door gets a lintel above it.
function buildWallSide({ group, colliders, axis, at, lo, hi, h, doors, mat, inset }) {
  const segs = [];
  let cursor = lo;
  const sorted = doors.slice().sort((a, b) => (axis === 'x' ? a.z - b.z : a.x - b.x));
  for (const d of sorted) {
    const c = axis === 'x' ? d.z : d.x;
    segs.push([cursor, c - d.width / 2]);
    cursor = c + d.width / 2;
  }
  segs.push([cursor, hi]);

  const make = (a, b, y0, y1) => {
    if (b - a < 0.05 || y1 - y0 < 0.05) return;
    const len = b - a, height = y1 - y0, mid = (a + b) / 2;
    const geo = axis === 'x'
      ? new THREE.BoxGeometry(WALL_T, height, len)
      : new THREE.BoxGeometry(len, height, WALL_T);
    const mesh = new THREE.Mesh(geo, mat);
    const offset = at + inset * (WALL_T / 2);
    if (axis === 'x') mesh.position.set(offset, y0 + height / 2, mid);
    else mesh.position.set(mid, y0 + height / 2, offset);
    group.add(mesh);
    if (y0 < 1.8) {
      const box = new THREE.Box3().setFromObject(mesh);
      colliders.push(box);
    }
  };

  for (const [a, b] of segs) make(a, b, 0, h);
  for (const d of sorted) {
    const c = axis === 'x' ? d.z : d.x;
    make(c - d.width / 2, c + d.width / 2, d.height, h); // lintel
  }
}

function buildSpace(space, layout, group, colliders) {
  const pal = palette(space.paletteName);
  const { rect, h } = space;

  // Floor.
  const floor = new THREE.Mesh(
    new THREE.BoxGeometry(rect.w, 0.2, rect.d),
    lambert(pal.floor)
  );
  floor.position.set(rect.cx, -0.1, rect.cz);
  group.add(floor);

  // Trim rug / inlay for rooms: a slightly lighter inset rectangle.
  if (space.kind === 'room') {
    const inlay = new THREE.Mesh(
      new THREE.BoxGeometry(rect.w * 0.55, 0.04, rect.d * 0.55),
      lambert(pal.trim)
    );
    inlay.position.set(rect.cx, 0.02, rect.cz);
    group.add(inlay);
  }

  const wallMat = lambert(pal.wall);

  // Gather this space's doors per side.
  const doors = layout.doorsBySpace.get(space.id) || [];
  const side = (pred) => doors.filter(pred);

  buildWallSide({ group, colliders, axis: 'x', at: rect.maxX,
    lo: rect.minZ, hi: rect.maxZ, h,
    doors: side((d) => d.axis === 'x' && Math.abs(d.x - rect.maxX) < 0.05),
    mat: wallMat, inset: -1 });
  buildWallSide({ group, colliders, axis: 'x', at: rect.minX,
    lo: rect.minZ, hi: rect.maxZ, h,
    doors: side((d) => d.axis === 'x' && Math.abs(d.x - rect.minX) < 0.05),
    mat: wallMat, inset: 1 });
  buildWallSide({ group, colliders, axis: 'z', at: rect.maxZ,
    lo: rect.minX, hi: rect.maxX, h,
    doors: side((d) => d.axis === 'z' && Math.abs(d.z - rect.maxZ) < 0.05),
    mat: wallMat, inset: -1 });
  buildWallSide({ group, colliders, axis: 'z', at: rect.minZ,
    lo: rect.minX, hi: rect.maxX, h,
    doors: side((d) => d.axis === 'z' && Math.abs(d.z - rect.minZ) < 0.05),
    mat: wallMat, inset: 1 });

  // Corner pillars for rooms (simple square columns, full height).
  if (space.kind === 'room') {
    const pillarMat = lambert(pal.trim);
    const inset = WALL_T + 0.25;
    for (const [px, pz] of [
      [rect.minX + inset, rect.minZ + inset],
      [rect.maxX - inset, rect.minZ + inset],
      [rect.minX + inset, rect.maxZ - inset],
      [rect.maxX - inset, rect.maxZ - inset],
    ]) {
      const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.55, h, 0.55), pillarMat);
      pillar.position.set(px, h / 2, pz);
      group.add(pillar);
      colliders.push(new THREE.Box3().setFromObject(pillar));
    }
  }

  // Room light + floating name banner.
  if (space.kind === 'room') {
    const size = Math.max(rect.w, rect.d);
    const light = new THREE.PointLight(pal.light, size * 2.6, size * 2.6, 1.7);
    light.position.set(rect.cx, h - 0.8, rect.cz);
    group.add(light);

    if (space.room) {
      const tex = bannerTexture({ text: space.room.name, pal });
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
      sprite.scale.set(6, 1.5, 1);
      sprite.position.set(rect.cx, h + 1.1, rect.cz);
      group.add(sprite);
    }
  } else {
    // Dim corridor glow so passages read as inviting, not black.
    const light = new THREE.PointLight(pal.glow, 2.2, 9, 1.8);
    light.position.set(rect.cx, h - 0.5, rect.cz);
    group.add(light);
  }
}

function buildSky(scene) {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 512;
  const ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, 512);
  g.addColorStop(0, '#05040a');
  g.addColorStop(0.6, '#0d0a18');
  g.addColorStop(1, '#191227');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 1024, 512);
  let seed = 12345;
  const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0xffffffff; };
  for (let i = 0; i < 420; i++) {
    const x = rand() * 1024, y = rand() * 400, r = rand() * 1.4 + 0.2;
    ctx.fillStyle = `rgba(255, 245, 220, ${0.25 + rand() * 0.75})`;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(380, 24, 16),
    new THREE.MeshBasicMaterial({ map: tex, side: THREE.BackSide, fog: false })
  );
  scene.add(dome);
}

export function buildWorld(scene, layout) {
  const group = new THREE.Group();
  const colliders = [];

  scene.background = new THREE.Color(0x07060c);
  scene.fog = new THREE.Fog(0x0b0916, 14, 64);
  scene.add(new THREE.AmbientLight(0xfff2dd, 0.5));
  scene.add(new THREE.HemisphereLight(0x303a55, 0x2a2118, 0.65));

  buildSky(scene);
  for (const space of layout.spaces) buildSpace(space, layout, group, colliders);

  // A faint outer ground plane far below fog so gaps never show void.
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(800, 800),
    new THREE.MeshBasicMaterial({ color: 0x07060c })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.35;
  group.add(ground);

  scene.add(group);
  return { group, colliders };
}
