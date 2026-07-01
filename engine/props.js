// Parametric prop catalog. Every prop is built from primitives at runtime —
// no mesh files, no textures except procedural canvases. Each builder returns
// { group, update? } where update(t) animates (flames, orbits, sand).
// Content models reference these by name (see world/catalog.json); they can
// configure scale, never geometry.

import * as THREE from 'three';
import { STAIR_PIT } from './layout.js';

const lam = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, ...extra });
const WOOD = 0x4a3320;
const DARKWOOD = 0x33220f;
const STONE = 0x8b8678;
const METAL = 0xb08428;

function flame(pal, r = 0.09) {
  const g = new THREE.Group();
  const core = new THREE.Mesh(
    new THREE.SphereGeometry(r, 8, 8),
    new THREE.MeshBasicMaterial({ color: 0xffd98a })
  );
  core.scale.y = 1.8;
  const halo = new THREE.Mesh(
    new THREE.SphereGeometry(r * 2.2, 8, 8),
    new THREE.MeshBasicMaterial({ color: pal.glow, transparent: true, opacity: 0.22 })
  );
  const light = new THREE.PointLight(0xffc878, 2.2, 5, 1.8);
  light.position.y = r;
  g.add(core, halo, light);
  g.userData.isFlame = true;
  return g;
}

function pedestal(pal) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.18, 0.9), lam(STONE));
  base.position.y = 0.09;
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.34, 0.95, 8), lam(STONE));
  shaft.position.y = 0.66;
  const top = new THREE.Mesh(new THREE.BoxGeometry(0.74, 0.1, 0.74), lam(pal.trim));
  top.position.y = 1.18;
  g.add(base, shaft, top);
  return { group: g };
}

function lectern(pal) {
  const g = new THREE.Group();
  const foot = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.42, 0.12, 8), lam(DARKWOOD));
  foot.position.y = 0.06;
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.12, 1.05, 8), lam(WOOD));
  post.position.y = 0.62;
  const desk = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.06, 0.56), lam(WOOD));
  desk.position.y = 1.18;
  desk.rotation.x = -0.42;
  const lip = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.07, 0.05), lam(DARKWOOD));
  lip.position.set(0, 1.06, 0.245);
  lip.rotation.x = -0.42;
  g.add(foot, post, desk, lip);
  return { group: g };
}

function mirror(pal) {
  const g = new THREE.Group();
  const frame = new THREE.Mesh(new THREE.BoxGeometry(1.5, 2.6, 0.12), lam(METAL));
  frame.position.y = 1.5;
  const arch = new THREE.Mesh(
    new THREE.CylinderGeometry(0.75, 0.75, 0.12, 24, 1, false, 0, Math.PI),
    lam(METAL)
  );
  arch.rotation.z = Math.PI / 2;
  arch.rotation.y = Math.PI / 2;
  arch.position.y = 2.8;
  const glass = new THREE.Mesh(
    new THREE.PlaneGeometry(1.22, 2.3),
    new THREE.MeshStandardMaterial({
      color: 0xbfd4e4, metalness: 0.95, roughness: 0.12,
      emissive: pal.glow, emissiveIntensity: 0.12,
    })
  );
  glass.position.set(0, 1.55, 0.075);
  const mist = new THREE.Mesh(
    new THREE.PlaneGeometry(1.1, 2.15),
    new THREE.MeshBasicMaterial({ color: pal.glow, transparent: true, opacity: 0.1 })
  );
  mist.position.set(0, 1.55, 0.09);
  const feet = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.16, 0.6), lam(DARKWOOD));
  feet.position.y = 0.08;
  g.add(frame, arch, glass, mist, feet);
  const update = (t) => { mist.material.opacity = 0.08 + 0.05 * Math.sin(t * 0.8); };
  return { group: g, update };
}

function cauldron(pal) {
  const g = new THREE.Group();
  const pot = new THREE.Mesh(
    new THREE.SphereGeometry(0.62, 16, 12, 0, Math.PI * 2, Math.PI * 0.18, Math.PI * 0.62),
    lam(0x232328)
  );
  pot.position.y = 0.72;
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.52, 0.06, 8, 20), lam(0x35353c));
  rim.rotation.x = Math.PI / 2;
  rim.position.y = 1.08;
  const brew = new THREE.Mesh(
    new THREE.CircleGeometry(0.48, 20),
    new THREE.MeshBasicMaterial({ color: pal.glow })
  );
  brew.rotation.x = -Math.PI / 2;
  brew.position.y = 1.04;
  const legs = new THREE.Group();
  for (let i = 0; i < 3; i++) {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.06, 0.5, 6), lam(0x232328));
    const a = (i / 3) * Math.PI * 2;
    leg.position.set(Math.cos(a) * 0.4, 0.25, Math.sin(a) * 0.4);
    leg.rotation.z = Math.cos(a) * 0.25;
    leg.rotation.x = -Math.sin(a) * 0.25;
    legs.add(leg);
  }
  const glow = new THREE.PointLight(pal.glow, 3, 4.5, 1.8);
  glow.position.y = 1.3;
  g.add(pot, rim, brew, legs, glow);
  const update = (t) => {
    brew.position.y = 1.04 + Math.sin(t * 2.2) * 0.012;
    glow.intensity = 2.6 + Math.sin(t * 3.1) * 0.5;
  };
  return { group: g, update };
}

function bookshelf(pal) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.7, 2.5, 0.42), lam(DARKWOOD));
  body.position.y = 1.25;
  g.add(body);
  let seed = 7;
  const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0xffffffff; };
  const tones = [0x6e3030, 0x274233, 0x32456e, 0x9c7b3f, 0x4c3a6e, 0x8a6a3c];
  for (let shelf = 0; shelf < 4; shelf++) {
    const y = 0.45 + shelf * 0.58;
    const board = new THREE.Mesh(new THREE.BoxGeometry(1.56, 0.05, 0.36), lam(WOOD));
    board.position.set(0, y - 0.26, 0.02);
    g.add(board);
    let x = -0.68;
    while (x < 0.6) {
      const bw = 0.09 + rand() * 0.1;
      const bh = 0.34 + rand() * 0.14;
      const book = new THREE.Mesh(
        new THREE.BoxGeometry(bw, bh, 0.26),
        lam(tones[Math.floor(rand() * tones.length)])
      );
      book.position.set(x + bw / 2, y - 0.24 + bh / 2, 0.04);
      book.rotation.z = (rand() - 0.5) * 0.08;
      g.add(book);
      x += bw + 0.015;
    }
  }
  return { group: g };
}

function statue(pal) {
  const g = new THREE.Group();
  const plinth = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.55, 0.95), lam(STONE));
  plinth.position.y = 0.275;
  const robe = new THREE.Mesh(new THREE.ConeGeometry(0.42, 1.45, 8), lam(0x9b958a));
  robe.position.y = 1.27;
  const chest = new THREE.Mesh(new THREE.SphereGeometry(0.27, 8, 8), lam(0x9b958a));
  chest.position.y = 1.95;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.17, 8, 8), lam(0xa8a297));
  head.position.y = 2.27;
  const hat = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.5, 8), lam(0x8b8678));
  hat.position.y = 2.55;
  hat.rotation.z = 0.12;
  g.add(plinth, robe, chest, head, hat);
  return { group: g };
}

function bannerProp(pal) {
  const g = new THREE.Group();
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 2.9, 8), lam(METAL));
  pole.position.y = 1.45;
  const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.1, 8), lam(METAL));
  bar.rotation.z = Math.PI / 2;
  bar.position.y = 2.75;
  const cloth = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.9),
    lam(pal.trim, { side: THREE.DoubleSide }));
  cloth.position.y = 1.78;
  const sigil = new THREE.Mesh(new THREE.CircleGeometry(0.3, 6),
    new THREE.MeshBasicMaterial({ color: pal.glow, side: THREE.DoubleSide }));
  sigil.position.set(0, 1.85, 0.01);
  g.add(pole, bar, cloth, sigil);
  const update = (t) => { cloth.rotation.y = Math.sin(t * 0.7) * 0.06; sigil.rotation.y = cloth.rotation.y; };
  return { group: g, update };
}

function candelabra(pal) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.3, 0.1, 8), lam(METAL));
  base.position.y = 0.05;
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 1.5, 8), lam(METAL));
  stem.position.y = 0.85;
  g.add(base, stem);
  const flames = [];
  for (const dx of [-0.3, 0, 0.3]) {
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.34, 6), lam(METAL));
    arm.rotation.z = Math.PI / 2;
    arm.position.set(dx / 2, 1.58, 0);
    const candle = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.26, 8), lam(0xe9dfc6));
    candle.position.set(dx, 1.74, 0);
    const f = flame(pal, 0.06);
    f.position.set(dx, 1.9, 0);
    flames.push(f);
    g.add(arm, candle, f);
  }
  const update = (t) => {
    flames.forEach((f, i) => {
      f.scale.setScalar(1 + Math.sin(t * 7 + i * 2.1) * 0.12);
    });
  };
  return { group: g, update };
}

function orrery(pal) {
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.5, 0.16, 12), lam(DARKWOOD));
  base.position.y = 0.08;
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 1.0, 8), lam(METAL));
  post.position.y = 0.66;
  const sun = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 12),
    new THREE.MeshBasicMaterial({ color: 0xffd98a }));
  sun.position.y = 1.3;
  const sunLight = new THREE.PointLight(0xffd98a, 1.4, 3.5, 1.8);
  sunLight.position.y = 1.3;
  g.add(base, post, sun, sunLight);
  const spinner = new THREE.Group();
  spinner.position.y = 1.3;
  const planetTones = [0x9ac4ff, 0xc78f3a, 0x9fe8b9];
  planetTones.forEach((tone, i) => {
    const r = 0.42 + i * 0.27;
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.012, 6, 40), lam(METAL));
    ring.rotation.x = Math.PI / 2;
    const holder = new THREE.Group();
    const planet = new THREE.Mesh(new THREE.SphereGeometry(0.06 + i * 0.015, 8, 8), lam(tone));
    planet.position.x = r;
    holder.add(planet);
    holder.userData.speed = 0.9 - i * 0.28;
    spinner.add(ring, holder);
  });
  g.add(spinner);
  const update = (t) => {
    for (const child of spinner.children) {
      if (child.userData.speed) child.rotation.y = t * child.userData.speed;
    }
  };
  return { group: g, update };
}

function crystalBall(pal) {
  const g = new THREE.Group();
  const { group: ped } = pedestal(pal);
  const orb = new THREE.Mesh(
    new THREE.SphereGeometry(0.3, 16, 16),
    new THREE.MeshStandardMaterial({
      color: 0xcfe4ff, metalness: 0.1, roughness: 0.05,
      transparent: true, opacity: 0.8,
      emissive: pal.glow, emissiveIntensity: 0.35,
    })
  );
  orb.position.y = 1.55;
  const light = new THREE.PointLight(pal.glow, 1.6, 4, 1.8);
  light.position.y = 1.55;
  g.add(ped, orb, light);
  const update = (t) => { orb.material.emissiveIntensity = 0.3 + Math.sin(t * 1.7) * 0.15; };
  return { group: g, update };
}

function hourglass(pal) {
  const g = new THREE.Group();
  const { group: ped } = pedestal(pal);
  g.add(ped);
  const mk = (y, flip) => {
    const cone = new THREE.Mesh(
      new THREE.ConeGeometry(0.22, 0.34, 12, 1, true),
      new THREE.MeshStandardMaterial({
        color: 0xcfe4ff, transparent: true, opacity: 0.35, roughness: 0.1, side: THREE.DoubleSide,
      })
    );
    cone.position.y = y;
    if (flip) cone.rotation.x = Math.PI;
    return cone;
  };
  g.add(mk(1.42, true), mk(1.78, false));
  for (const y of [1.23, 1.97]) {
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.27, 0.05, 12), lam(DARKWOOD));
    cap.position.y = y;
    g.add(cap);
  }
  for (const a of [0, Math.PI * 2 / 3, Math.PI * 4 / 3]) {
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.74, 6), lam(METAL));
    rod.position.set(Math.cos(a) * 0.25, 1.6, Math.sin(a) * 0.25);
    g.add(rod);
  }
  const sand = new THREE.Mesh(new THREE.ConeGeometry(0.17, 0.2, 10), lam(0xc78f3a));
  sand.position.y = 1.36;
  g.add(sand);
  const update = (t) => { sand.scale.setScalar(0.85 + 0.15 * Math.sin(t * 0.5)); };
  return { group: g, update };
}

function table(pal) {
  const g = new THREE.Group();
  const top = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.08, 0.9), lam(WOOD));
  top.position.y = 0.95;
  g.add(top);
  for (const [dx, dz] of [[-0.7, -0.35], [0.7, -0.35], [-0.7, 0.35], [0.7, 0.35]]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.95, 0.09), lam(DARKWOOD));
    leg.position.set(dx, 0.475, dz);
    g.add(leg);
  }
  const runner = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.012, 0.92), lam(pal.trim));
  runner.position.y = 0.995;
  g.add(runner);
  return { group: g };
}

function brazier(pal) {
  const g = new THREE.Group();
  const bowl = new THREE.Mesh(
    new THREE.SphereGeometry(0.4, 12, 8, 0, Math.PI * 2, 0, Math.PI * 0.5),
    lam(0x35353c)
  );
  bowl.rotation.x = Math.PI;
  bowl.position.y = 1.0;
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.1, 0.95, 8), lam(0x232328));
  stem.position.y = 0.5;
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.38, 0.08, 8), lam(0x232328));
  base.position.y = 0.04;
  const f = flame(pal, 0.16);
  f.position.y = 1.12;
  g.add(bowl, stem, base, f);
  const update = (t) => { f.scale.setScalar(1 + Math.sin(t * 6.3) * 0.15); };
  return { group: g, update };
}

// A descending stairwell that sinks into a floor pit (the builder cuts the hole
// and shafts the walls). Steps drop from the room floor down to a sunken arch at
// the wall; a glowing rim, down-chevrons and a hanging sign mark the mouth.
function descendingStair(pal, opts = {}) {
  const g = new THREE.Group();
  const GLOW = 0x6ea8ff, EDGE = 0xcfe6ff;
  const depth = opts.depth || STAIR_PIT.depth;
  const N = 7, INSET = 0.85;
  const zWall = -INSET;                    // local z of the wall behind the well
  const zNear = STAIR_PIT.run - INSET;     // local z of the pit's room-side edge
  const run = zNear - zWall;               // == STAIR_PIT.run
  const sd = run / N, sh = depth / N, stepW = STAIR_PIT.width - 0.5;
  for (let i = 0; i < N; i++) {
    const yTop = -(i + 1) * sh;            // each tread sits lower, descending to the wall
    const zc = zNear - (i + 0.5) * sd;
    const t = new THREE.Mesh(new THREE.BoxGeometry(stepW, sh, sd), lam(STONE));
    t.position.set(0, yTop - sh / 2, zc);
    g.add(t);
    const lip = new THREE.Mesh(
      new THREE.BoxGeometry(stepW, 0.04, 0.06),
      new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 0.7 })
    );
    lip.position.set(0, yTop, zc + sd / 2);
    g.add(lip);
  }
  // Sunken archway at the bottom of the well, against the wall.
  const archY = -depth + 1.0;
  const arch = new THREE.Mesh(
    new THREE.TorusGeometry(0.85, 0.09, 12, 26, Math.PI),
    new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 1.0 })
  );
  arch.position.set(0, archY, zWall + 0.18);
  g.add(arch);
  for (const sgn of [-1, 1]) {
    const jamb = new THREE.Mesh(
      new THREE.BoxGeometry(0.1, 1.0, 0.1),
      new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 0.7 })
    );
    jamb.position.set(sgn * 0.85, archY - 0.5, zWall + 0.18);
    g.add(jamb);
  }
  const veil = new THREE.Mesh(
    new THREE.PlaneGeometry(1.6, 1.8),
    new THREE.MeshBasicMaterial({ color: GLOW, transparent: true, opacity: 0.4, side: THREE.DoubleSide })
  );
  veil.position.set(0, archY - 0.05, zWall + 0.15);
  g.add(veil);
  // Glowing rim around the pit mouth at floor level — frames the opening.
  const rim = new THREE.Mesh(
    new THREE.BoxGeometry(stepW + 0.5, 0.06, 0.12),
    new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 0.55 })
  );
  rim.position.set(0, 0.04, zNear);
  g.add(rim);
  // Down-pointing chevrons hovering above the mouth — a "descend" beacon.
  const chev = new THREE.Group();
  for (let i = 0; i < 2; i++) {
    for (const sgn of [-1, 1]) {
      const bar = new THREE.Mesh(
        new THREE.BoxGeometry(0.5, 0.09, 0.07),
        new THREE.MeshBasicMaterial({ color: GLOW })
      );
      bar.position.set(sgn * 0.22, 1.5 - i * 0.34, zNear - 0.1);
      bar.rotation.z = -sgn * 0.7;          // inverted vs the ascending chevron → points down
      chev.add(bar);
    }
  }
  g.add(chev);
  const light = new THREE.PointLight(GLOW, 0.7, 5, 2.0);
  light.position.set(0, -depth + 1.2, zWall + 0.6);
  g.add(light);
  const update = (t) => {
    veil.material.opacity = 0.4 + 0.1 * Math.sin(t * 1.6);
    chev.position.y = Math.sin(t * 2.2) * 0.07 - 0.05;
    light.intensity = 0.6 + 0.2 * Math.sin(t * 2.0);
  };
  // The sign hangs above the mouth, facing into the room.
  const signAnchor = { x: 0, y: 2.3, z: zNear - 0.05 };
  return { group: g, update, signAnchor };
}

function stair(pal, opts = {}) {
  if (opts.down) return descendingStair(pal, opts);
  const g = new THREE.Group();
  const steps = 8, stepH = 0.22, stepD = 0.36, stepW = 1.9;
  const zTop = -0.4;        // the top step sits near the wall (local -z = wall)
  const topY = steps * stepH;
  // The portal wears a fixed COOL palette regardless of the room, so the arch,
  // veil and signboard pop against warm halls instead of dissolving into them.
  const GLOW = 0x6ea8ff;    // sapphire glow
  const EDGE = 0xcfe6ff;    // pale-blue tread/arch edges
  for (let i = 0; i < steps; i++) {
    // i = 0 is the TOP step (near the wall, tallest); the flight DESCENDS into
    // the room toward +z, so the keeper climbs up out of the hall to the arch.
    const topH = (steps - i) * stepH;     // tread surface height
    const z = zTop + i * stepD;
    const s = new THREE.Mesh(new THREE.BoxGeometry(stepW, topH, stepD), lam(STONE));
    s.position.set(0, topH / 2, z);
    g.add(s);
    // Glowing tread edge on the room-facing lip — the whole flight reads as lit.
    const lip = new THREE.Mesh(
      new THREE.BoxGeometry(stepW, 0.04, 0.06),
      new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 0.7 })
    );
    lip.position.set(0, topH, z + stepD / 2);
    g.add(lip);
  }
  // A luminous archway at the top of the flight. It sits level with the top step
  // (just in front of the wall) — pushing it back any further hides it behind the
  // wall, which occludes the whole portal.
  const archZ = zTop + 0.05;
  const arch = new THREE.Mesh(
    new THREE.TorusGeometry(1.0, 0.1, 12, 28, Math.PI),
    new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 1.0 })
  );
  arch.position.set(0, topY + 1.05, archZ);
  g.add(arch);
  // Two slender jambs so the archway reads as a doorway, not a floating ring.
  for (const sgn of [-1, 1]) {
    const jamb = new THREE.Mesh(
      new THREE.BoxGeometry(0.12, topY + 1.1, 0.12),
      new THREE.MeshLambertMaterial({ color: EDGE, emissive: GLOW, emissiveIntensity: 0.7 })
    );
    jamb.position.set(sgn * 1.0, (topY + 1.05) / 2, archZ);
    g.add(jamb);
  }
  const veil = new THREE.Mesh(
    new THREE.PlaneGeometry(1.9, 2.1),
    new THREE.MeshBasicMaterial({ color: GLOW, transparent: true, opacity: 0.42, side: THREE.DoubleSide })
  );
  veil.position.set(0, (topY + 1.05) / 2 + 0.5, archZ);
  g.add(veil);
  // Upward chevrons above the arch — a clear "go up" beacon.
  const chev = new THREE.Group();
  for (let i = 0; i < 2; i++) {
    for (const sgn of [-1, 1]) {
      const bar = new THREE.Mesh(
        new THREE.BoxGeometry(0.5, 0.09, 0.07),
        new THREE.MeshBasicMaterial({ color: GLOW })
      );
      bar.position.set(sgn * 0.22, topY + 2.95 + i * 0.34, archZ);
      bar.rotation.z = sgn * 0.7;
      chev.add(bar);
    }
  }
  g.add(chev);
  // A faint pillar of light rising from the arch — visible across the hall.
  const shaft = new THREE.Mesh(
    new THREE.CylinderGeometry(0.4, 0.7, 3.0, 16, 1, true),
    new THREE.MeshBasicMaterial({ color: GLOW, transparent: true, opacity: 0.05,
                                  side: THREE.DoubleSide, depthWrite: false })
  );
  shaft.position.set(0, topY + 2.4, archZ);
  g.add(shaft);
  // A soft point light placed WELL in front of the arch so it lights the steps,
  // not the wall behind (lighting the wall would wash out the arch and sign).
  const light = new THREE.PointLight(GLOW, 0.5, 4, 2.0);
  light.position.set(0, topY + 0.6, archZ + 1.6);
  g.add(light);
  const update = (t) => {
    veil.material.opacity = 0.4 + 0.1 * Math.sin(t * 1.6);
    shaft.material.opacity = 0.04 + 0.025 * Math.sin(t * 1.2);
    chev.position.y = Math.sin(t * 2.2) * 0.07;
    light.intensity = 0.45 + 0.15 * Math.sin(t * 2.0);
  };
  // Where a destination signboard mounts: as a lintel just above the arch crown.
  const signAnchor = { x: 0, y: topY + 2.35, z: archZ + 0.05 };
  return { group: g, update, signAnchor };
}

const BUILDERS = {
  pedestal, lectern, mirror, cauldron, bookshelf, statue,
  banner: bannerProp, candelabra, orrery, crystal_ball: crystalBall,
  hourglass, table, brazier, stair,
};

export function makeProp(name, pal, scale = 1, opts = {}) {
  const builder = BUILDERS[name] || pedestal;
  const made = builder(pal, opts);
  made.group.scale.setScalar(scale);
  return made;
}

export const PROP_NAMES = Object.keys(BUILDERS);
