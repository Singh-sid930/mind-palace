// Everything a passage mouth looks like: the stair flights (ascending arch,
// descending pit-well), the gold threshold archway between sibling wings, the
// Gatekeeper spectre that watches gated mouths, and buildMouth(), which
// assembles prop + destination signboard + hitbox into one interactable.
// The mouths themselves (where, which wall, which pit) come from layout.js.

import * as THREE from 'three';
import { STAIR_PIT } from './layout.js';
import { bannerTexture } from './text.js';
import { lam, STONE, STAIR_GLOW, STAIR_EDGE, STAIR_SIGN_TRIM,
         ARCH_GOLD, ARCH_SIGN_TRIM } from './common.js';

// A descending stairwell that sinks into a floor pit (the builder cuts the hole
// and shafts the walls). Steps drop from the room floor down to a sunken arch at
// the wall; a glowing rim, down-chevrons and a hanging sign mark the mouth.
function descendingStair(pal, opts = {}) {
  const g = new THREE.Group();
  const GLOW = STAIR_GLOW, EDGE = STAIR_EDGE;
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
  const GLOW = STAIR_GLOW, EDGE = STAIR_EDGE;
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

// A walk-through threshold archway: the lateral passage between sibling wings on
// the same floor. Warm GOLD (vs the cool sapphire of the vertical stairs) so a
// sideways crossing reads differently from an up/down one. No steps, no pit.
function archway(pal) {
  const g = new THREE.Group();
  const GOLD = ARCH_GOLD, STONE2 = 0x6b5a3a, RUNE = 0xbf9a4a;
  const H = 2.9, halfW = 1.15;
  for (const sgn of [-1, 1]) {
    const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.34, H, 0.34), lam(STONE2));
    pillar.position.set(sgn * halfW, H / 2, 0);
    g.add(pillar);
    for (let i = 0; i < 3; i++) {
      const band = new THREE.Mesh(
        new THREE.BoxGeometry(0.4, 0.07, 0.4),
        new THREE.MeshLambertMaterial({ color: RUNE, emissive: GOLD, emissiveIntensity: 0.6 })
      );
      band.position.set(sgn * halfW, 0.6 + i * 0.95, 0);
      g.add(band);
    }
  }
  const lintel = new THREE.Mesh(new THREE.BoxGeometry(halfW * 2 + 0.5, 0.34, 0.42), lam(STONE2));
  lintel.position.set(0, H + 0.1, 0);
  g.add(lintel);
  const keystone = new THREE.Mesh(
    new THREE.BoxGeometry(0.42, 0.42, 0.46),
    new THREE.MeshLambertMaterial({ color: RUNE, emissive: GOLD, emissiveIntensity: 0.75 })
  );
  keystone.position.set(0, H + 0.1, 0);
  g.add(keystone);
  const arch = new THREE.Mesh(
    new THREE.TorusGeometry(halfW, 0.09, 10, 24, Math.PI),
    new THREE.MeshLambertMaterial({ color: RUNE, emissive: GOLD, emissiveIntensity: 0.55 })
  );
  arch.position.set(0, H + 0.28, 0);
  g.add(arch);
  // The shimmering threshold you step through.
  const veil = new THREE.Mesh(
    new THREE.PlaneGeometry(halfW * 2 - 0.05, H - 0.1),
    new THREE.MeshBasicMaterial({ color: GOLD, transparent: true, opacity: 0.22,
                                  side: THREE.DoubleSide, depthWrite: false })
  );
  veil.position.set(0, (H - 0.1) / 2 + 0.05, 0);
  g.add(veil);
  const light = new THREE.PointLight(GOLD, 0.9, 6, 1.8);
  light.position.set(0, H / 2, 0.5);
  g.add(light);
  const update = (t) => {
    veil.material.opacity = 0.16 + 0.1 * Math.sin(t * 2.2);
    light.intensity = 0.8 + 0.25 * Math.sin(t * 2.0);
  };
  const signAnchor = { x: 0, y: H + 0.85, z: 0 };
  return { group: g, update, signAnchor };
}

// The Gatekeeper: a stern, STATIONARY spectre that stands beside a gated
// passage and quizzes the keeper on prerequisites before they climb. Colder and
// taller than Gemma, with a slowly turning rune-seal it guards the way with.
function gatekeeper() {
  const g = new THREE.Group();
  const COLD = 0xcfe0ff;
  const robeMat = new THREE.MeshLambertMaterial({
    color: COLD, transparent: true, opacity: 0.4,
    emissive: 0x2a4a6a, emissiveIntensity: 0.6, side: THREE.DoubleSide,
  });
  const robe = new THREE.Mesh(new THREE.ConeGeometry(0.42, 1.7, 14, 1, true), robeMat);
  robe.position.y = 0.85;
  const hood = new THREE.Mesh(new THREE.SphereGeometry(0.26, 14, 12), robeMat.clone());
  hood.material.opacity = 0.5; hood.position.y = 1.75;
  for (const dx of [-0.09, 0.09]) {
    const eye = new THREE.Mesh(
      new THREE.SphereGeometry(0.03, 6, 6),
      new THREE.MeshBasicMaterial({ color: 0xbfe8ff })
    );
    eye.position.set(dx, 1.76, 0.22);
    g.add(eye);
  }
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.42, 0.03, 8, 28),
    new THREE.MeshBasicMaterial({ color: COLD, transparent: true, opacity: 0.5 })
  );
  ring.position.set(0, 1.1, 0.4);
  const glow = new THREE.PointLight(0x9ac4ff, 0.9, 4.5, 1.8);
  glow.position.y = 1.3;
  g.add(robe, hood, ring, glow);
  const update = (t) => {
    g.position.y = Math.sin(t * 1.4) * 0.06;
    ring.rotation.z = t * 0.6;
    glow.intensity = 0.8 + Math.sin(t * 2.3) * 0.25;
  };
  return { group: g, update };
}

// The signboard naming the destination, hung from the prop's signAnchor.
// Colored to match the passage identity: sapphire trim for stairs, gold for archways.
function signboard(kind, destName, pal, anchor) {
  const signPal = kind === 'archway'
    ? { ...pal, trim: ARCH_SIGN_TRIM, accent: ARCH_GOLD }
    : { ...pal, trim: STAIR_SIGN_TRIM, accent: STAIR_GLOW };
  const signW = 2.6, signH = signW * (200 / 1024);
  const board = new THREE.Mesh(
    new THREE.PlaneGeometry(signW, signH),
    new THREE.MeshBasicMaterial({
      map: bannerTexture({ text: destName, pal: signPal, w: 1024, h: 200 }),
      transparent: true, side: THREE.DoubleSide,
    })
  );
  board.position.set(anchor.x, anchor.y, anchor.z);
  return board;
}

// Build a passage MOUTH (stair up/down or lateral archway) at its placement.
// Returns { group, update?, hit, record } — record is the interactable payload.
// Gatekeepers are voiced by the same backend as Gemma. On a static host there
// is nothing behind /api, so they are hidden rather than left standing as mute
// sentries over stairs that open anyway. Floors build lazily, so this keeps a
// registry for the ones already raised AND a flag for the ones raised later.
const _spectres = [];
let _spectresVisible = true;

export function setGatekeepersVisible(v) {
  _spectresVisible = v;
  for (const g of _spectres) g.visible = v;
}

export function buildMouth(mouth, pal, roomsById) {
  const g = new THREE.Group();
  g.position.set(mouth.x, 0, mouth.z);
  g.rotation.y = mouth.yaw;
  const destName = (roomsById && roomsById[mouth.to] && roomsById[mouth.to].name) || 'Onward';

  let update = null, hit;
  if (mouth.kind === 'archway') {
    const made = archway(pal);
    update = made.update || null;
    g.add(made.group);
    made.group.add(signboard('archway', destName, pal, made.signAnchor || { x: 0, y: 3.0, z: 0 }));
    hit = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 2.8, 1.4),
      new THREE.MeshBasicMaterial({ visible: false })
    );
    hit.position.set(0, 1.4, 0.6);
    g.add(hit);
  } else {
    const down = mouth.dir === 'down';
    const made = stair(pal, { down, depth: STAIR_PIT.depth });
    update = made.update || null;
    g.add(made.group);
    made.group.add(signboard('stair', destName, pal, made.signAnchor || { x: 0, y: 3.4, z: 0 }));
    hit = new THREE.Mesh(
      down ? new THREE.BoxGeometry(2.4, 2.6, STAIR_PIT.run)
           : new THREE.BoxGeometry(1.9, 3.6, 3.4),
      new THREE.MeshBasicMaterial({ visible: false })
    );
    hit.position.set(0, down ? 0.6 : 1.5, down ? (STAIR_PIT.run / 2 - 0.85) : 0.2);
    g.add(hit);
  }

  // A gated mouth is watched by a Gatekeeper spectre, standing to one side.
  if (mouth.gate) {
    const gk = gatekeeper();
    gk.group.position.set(1.6, 0, 0.6);
    gk.group.visible = _spectresVisible;
    _spectres.push(gk.group);
    g.add(gk.group);
    const base = update;
    update = (t) => { if (base) base(t); if (gk.group.visible) gk.update(t); };
  }

  const record = {
    kind: mouth.kind,
    roomId: mouth.roomId,
    targetRoom: mouth.to,
    dir: mouth.dir,
    gate: mouth.gate || null,
    focus: {
      title: destName,
      subtitle: mouth.kind === 'archway' ? 'Archway' : 'Staircase',
      body: '', mermaid: null, image: null,
    },
  };
  return { group: g, update, hit, record };
}
