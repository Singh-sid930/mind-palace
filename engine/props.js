// Parametric furniture catalog. Every prop is built from primitives at runtime, // no mesh files, no textures except procedural canvases. Each builder returns
// { group, update? } where update(t) animates (flames, orbits, sand).
// Content models reference these by name. The legal names are catalog.json's
// "props" list, which must match BUILDERS below; they can configure scale,
// never geometry. Passage structures (stairs, archways, the Gatekeeper) are
// engine-internal and live in passages.js, not here.

import * as THREE from 'three';
import { lam, WOOD, DARKWOOD, STONE, METAL } from './common.js';
import { KINETIC_BUILDERS } from './kinetics.js';

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
  // Slope faces +z, the exhibit slot convention's "into the room" direction.
  const desk = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.06, 0.56), lam(WOOD));
  desk.position.y = 1.18;
  desk.rotation.x = 0.42;
  const lip = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.07, 0.05), lam(DARKWOOD));
  lip.position.set(0, 1.06, 0.245);
  lip.rotation.x = 0.42;
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

const BUILDERS = {
  pedestal, lectern, mirror, cauldron, bookshelf, statue,
  banner: bannerProp, candelabra, orrery, crystal_ball: crystalBall,
  hourglass, table, brazier,
  ...KINETIC_BUILDERS, // animated concept props (kinetics.js)
};

export function makeProp(name, pal, scale = 1) {
  const builder = BUILDERS[name] || pedestal;
  const made = builder(pal);
  made.group.scale.setScalar(scale);
  return made;
}
