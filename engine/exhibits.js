// Places exhibits in rooms. Content declares WHAT (typed exhibits, in order);
// this module decides WHERE: the first artifact takes the room's center, all
// other exhibits take wall slots in walking order, portals take the leftovers.

import * as THREE from 'three';
import { palette } from './palettes.js';
import { STAIR_PIT } from './layout.js';
import { makeProp } from './props.js';
import { textPanelTexture, portraitTexture, diagramTexture, bannerTexture } from './text.js';

const lam = (color, extra = {}) => new THREE.MeshLambertMaterial({ color, ...extra });

// Usable wall slots for a space: inset points along each wall, skipping
// doorways and corners, facing into the room.
function wallSlots(space, doors, excludeSides = null) {
  const { rect } = space;
  const inset = 0.85, cornerPad = 1.5, spacing = 2.7;
  const slots = [];

  const sides = [
    { key: 'minZ', axis: 'z', at: rect.minZ, coord: 'x', lo: rect.minX, hi: rect.maxX, yaw: 0,
      px: (v) => [v, rect.minZ + inset] },
    { key: 'maxX', axis: 'x', at: rect.maxX, coord: 'z', lo: rect.minZ, hi: rect.maxZ, yaw: -Math.PI / 2,
      px: (v) => [rect.maxX - inset, v] },
    { key: 'maxZ', axis: 'z', at: rect.maxZ, coord: 'x', lo: rect.minX, hi: rect.maxX, yaw: Math.PI,
      px: (v) => [v, rect.maxZ - inset] },
    { key: 'minX', axis: 'x', at: rect.minX, coord: 'z', lo: rect.minZ, hi: rect.maxZ, yaw: Math.PI / 2,
      px: (v) => [rect.minX + inset, v] },
  ];

  for (const side of sides) {
    if (excludeSides && excludeSides.has(side.key)) continue;
    const blocked = doors
      .filter((d) => d.axis === side.axis && Math.abs((side.axis === 'x' ? d.x : d.z) - side.at) < 0.05)
      .map((d) => {
        const c = side.axis === 'x' ? d.z : d.x;
        return [c - d.width / 2 - 1.0, c + d.width / 2 + 1.0];
      });
    const lo = side.lo + cornerPad, hi = side.hi - cornerPad;
    const n = Math.max(1, Math.floor((hi - lo) / spacing));
    for (let i = 0; i <= n; i++) {
      const v = n === 0 ? (lo + hi) / 2 : lo + (i / n) * (hi - lo);
      if (blocked.some(([a, b]) => v > a && v < b)) continue;
      const [x, z] = side.px(v);
      slots.push({ x, z, yaw: side.yaw });
    }
  }
  return slots;
}

function framedPanel({ tex, w, h, pal, glowFrame = false }) {
  const g = new THREE.Group();
  const frame = new THREE.Mesh(
    new THREE.BoxGeometry(w + 0.16, h + 0.16, 0.07),
    glowFrame
      ? new THREE.MeshLambertMaterial({ color: pal.accent, emissive: pal.glow, emissiveIntensity: 0.25 })
      : lam(pal.accent)
  );
  const face = new THREE.Mesh(
    new THREE.PlaneGeometry(w, h),
    new THREE.MeshBasicMaterial({ map: tex })
  );
  face.position.z = 0.045;
  g.add(frame, face);
  return g;
}

function openBook(pal) {
  const g = new THREE.Group();
  for (const s of [-1, 1]) {
    const page = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.025, 0.46), lam(0xe9dfc6));
    page.position.set(s * 0.165, 0, 0);
    page.rotation.z = -s * 0.22;
    const cover = new THREE.Mesh(new THREE.BoxGeometry(0.37, 0.02, 0.5), lam(pal.trim));
    cover.position.set(s * 0.175, -0.025, 0);
    cover.rotation.z = -s * 0.22;
    g.add(page, cover);
  }
  return g;
}

// Build one exhibit at a slot (or center). Returns { group, update?, hit }
// where `hit` is the mesh registered for interaction raycasts.
function buildExhibit(ex, slot, pal, isCenter, roomsById, stairInfo) {
  const g = new THREE.Group();
  g.position.set(slot.x, 0, slot.z);
  g.rotation.y = slot.yaw;
  let update = null;
  let hit;

  if (ex.type === 'artifact') {
    const made = makeProp(ex.prop, pal, ex.scale || 1);
    update = made.update || null;
    g.add(made.group);
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(isCenter ? 1.1 : 0.8, 0.02, 6, 36),
      new THREE.MeshBasicMaterial({ color: pal.glow, transparent: true, opacity: 0.5 })
    );
    ring.rotation.x = Math.PI / 2;
    ring.position.y = 0.03;
    g.add(ring);
    hit = new THREE.Mesh(
      new THREE.CylinderGeometry(0.9, 0.9, 3.2, 8),
      new THREE.MeshBasicMaterial({ visible: false })
    );
    hit.position.y = 1.6;
    g.add(hit);
  } else if (ex.type === 'plaque') {
    if (ex.prop) {
      const made = makeProp(ex.prop, pal);
      g.add(made.group);
      const tex = textPanelTexture({ title: ex.title, body: '', pal, w: 512, h: 256, titleSize: 56 });
      const tablet = framedPanel({ tex, w: 0.8, h: 0.4, pal });
      tablet.position.y = ex.prop === 'lectern' ? 1.45 : 1.5;
      tablet.rotation.x = -0.25;
      g.add(tablet);
      hit = made.group;
    } else {
      const teaser = ex.text.length > 220 ? ex.text.slice(0, 217) + '…' : ex.text;
      const tex = textPanelTexture({ title: ex.title, body: teaser, pal });
      const panel = framedPanel({ tex, w: 1.8, h: 1.35, pal });
      panel.position.y = 1.85;
      g.add(panel);
      hit = panel;
    }
  } else if (ex.type === 'tome') {
    const made = makeProp('lectern', pal);
    g.add(made.group);
    const book = openBook(pal);
    book.position.set(0, 1.28, 0.05);
    book.rotation.x = -0.42;
    g.add(book);
    const glow = new THREE.PointLight(pal.glow, 0.8, 2.5, 1.8);
    glow.position.set(0, 1.6, 0.2);
    g.add(glow);
    hit = made.group;
  } else if (ex.type === 'portrait') {
    const tex = portraitTexture({ name: ex.title, subtitle: ex.subtitle || '', pal });
    const panel = framedPanel({ tex, w: 1.25, h: 1.7, pal });
    panel.position.y = 2.0;
    g.add(panel);
    hit = panel;
  } else if (ex.type === 'diagram') {
    const tex = diagramTexture({ title: ex.title, pal });
    const panel = framedPanel({ tex, w: 1.95, h: 1.45, pal, glowFrame: true });
    panel.position.y = 1.9;
    g.add(panel);
    hit = panel;
  } else if (ex.type === 'image') {
    // A framed picture on the wall; the real image loads asynchronously and the
    // frame rescales to its aspect. Press E to study it large in world space.
    const tex = new THREE.TextureLoader().load(ex.image, (t) => {
      const ar = (t.image.width || 1) / (t.image.height || 1);
      const W = ar >= 1 ? 1.95 : 1.95 * ar;
      const H = ar >= 1 ? 1.95 / ar : 1.95;
      const face = panel.children[1], frame = panel.children[0];
      face.geometry.dispose(); face.geometry = new THREE.PlaneGeometry(W, H);
      frame.geometry.dispose(); frame.geometry = new THREE.BoxGeometry(W + 0.16, H + 0.16, 0.07);
    });
    tex.colorSpace = THREE.SRGBColorSpace;
    const panel = framedPanel({ tex, w: 1.6, h: 1.2, pal, glowFrame: true });
    panel.position.y = 1.95;
    g.add(panel);
    hit = panel;
  } else if (ex.type === 'stair') {
    const down = !!(stairInfo && stairInfo.dir === 'down');
    const made = makeProp('stair', pal, ex.scale || 1, { down, depth: STAIR_PIT.depth });
    update = made.update || null;
    g.add(made.group);
    // A destination signboard mounted above the arch (or above the pit mouth).
    const destName = (roomsById && roomsById[ex.to] && roomsById[ex.to].name)
      || ex.caption || (down ? 'Downstairs' : 'Upstairs');
    const sa = made.signAnchor || { x: 0, y: 3.4, z: 0 };
    // Cool navy banner with a sapphire border — matches the portal, stays legible.
    const signPal = { ...pal, trim: 0x14233a, accent: 0x6ea8ff };
    const signTex = bannerTexture({ text: destName, pal: signPal, w: 1024, h: 200 });
    const signW = 2.6, signH = signW * (200 / 1024);
    const board = new THREE.Mesh(
      new THREE.PlaneGeometry(signW, signH),
      new THREE.MeshBasicMaterial({ map: signTex, transparent: true, side: THREE.DoubleSide })
    );
    board.position.set(sa.x, sa.y, sa.z);
    made.group.add(board);
    // Invisible hit volume: over the ascending flight, or over the pit mouth.
    const hitBox = new THREE.Mesh(
      down ? new THREE.BoxGeometry(2.4, 2.6, STAIR_PIT.run)
           : new THREE.BoxGeometry(1.9, 3.6, 3.4),
      new THREE.MeshBasicMaterial({ visible: false })
    );
    hitBox.position.set(0, down ? 0.6 : 1.5, down ? (STAIR_PIT.run / 2 - 0.85) : 0.2);
    g.add(hitBox);
    hit = hitBox;
  }

  return { group: g, update, hit };
}

function buildPortal(targetRoomName, slot, pal) {
  const g = new THREE.Group();
  g.position.set(slot.x, 0, slot.z);
  g.rotation.y = slot.yaw;

  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.95, 0.07, 10, 40),
    new THREE.MeshLambertMaterial({ color: 0x33220f, emissive: pal.glow, emissiveIntensity: 0.7 })
  );
  ring.position.y = 1.55;
  const film = new THREE.Mesh(
    new THREE.CircleGeometry(0.88, 32),
    new THREE.MeshBasicMaterial({
      color: pal.glow, transparent: true, opacity: 0.28, side: THREE.DoubleSide,
    })
  );
  film.position.y = 1.55;
  const light = new THREE.PointLight(pal.glow, 3, 6, 1.6);
  light.position.y = 1.6;
  const step = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.15, 0.12, 16), lam(0x33220f));
  step.position.y = 0.06;
  g.add(ring, film, light, step);

  const update = (t) => {
    ring.rotation.z = t * 0.4;
    film.material.opacity = 0.22 + 0.1 * Math.sin(t * 2.3);
  };
  return { group: g, update, hit: film };
}

// Build all exhibits + portals. Returns { interactables, updates }.
// interactables: hit-object -> { kind, exhibit/room info, focus payload }.
export function buildExhibits(scene, layout, roomsById) {
  const group = new THREE.Group();
  const interactables = new Map();
  const updates = [];

  const register = (hit, record) => {
    hit.traverse
      ? hit.traverse((o) => interactables.set(o, record))
      : interactables.set(hit, record);
    interactables.set(hit, record);
  };

  for (const space of layout.spaces) {
    if (space.kind !== 'room' || !space.room) continue;
    const room = space.room;
    const pal = palette(space.paletteName);
    const doors = layout.doorsBySpace.get(space.id) || [];
    // Staircases get authoritative wall placements from the layout; reserve
    // their walls so other exhibits never land on top of them.
    const roomStairs = (layout.stairs || []).filter((st) => st.roomId === space.id);
    const stairByExhibit = Object.fromEntries(roomStairs.map((st) => [st.exhibitId, st]));
    const excludeSides = new Set(roomStairs.map((st) => st.side));
    const slots = wallSlots(space, doors, excludeSides);
    let slotIdx = 0;
    const takeSlot = () => slots[Math.min(slotIdx++, slots.length - 1)];

    let centerTaken = false;
    for (const ex of room.exhibits) {
      let slot;
      const stairInfo = stairByExhibit[ex.id] || null;
      if (stairInfo) {
        slot = { x: stairInfo.x, z: stairInfo.z, yaw: stairInfo.yaw };
      } else if (ex.type === 'artifact' && !centerTaken) {
        centerTaken = true;
        // Center artifact faces back along the wing toward the hub.
        const yaw = Math.atan2(-space.rect.cx, -space.rect.cz) + Math.PI;
        slot = { x: space.rect.cx, z: space.rect.cz, yaw };
      } else {
        slot = takeSlot();
      }
      const made = buildExhibit(ex, slot, pal, slot.x === space.rect.cx && slot.z === space.rect.cz, roomsById, stairInfo);
      group.add(made.group);
      if (made.update) updates.push(made.update);
      register(made.hit, ex.type === 'stair' ? {
        kind: 'stair',
        roomId: room.id,
        targetRoom: ex.to,
        dir: stairInfo ? stairInfo.dir : 'up',
        focus: {
          title: roomsById[ex.to] ? roomsById[ex.to].name : ex.to,
          subtitle: 'Staircase',
          body: ex.caption || '',
          mermaid: null, image: null,
        },
      } : {
        kind: 'exhibit',
        roomId: room.id,
        focus: {
          title: ex.title,
          subtitle: ex.subtitle || typeLabel(ex.type),
          body: ex.text || ex.caption || '',
          mermaid: ex.type === 'diagram' ? ex.spec : null,
          image: ex.type === 'image' ? ex.image : null,
        },
      });
    }

    // Portals out of this room.
    for (const p of layout.portals) {
      const other = p.a === room.id ? p.b : p.b === room.id ? p.a : null;
      if (!other) continue;
      const target = roomsById[other];
      const slot = takeSlot();
      const made = buildPortal(target.name, slot, pal);
      group.add(made.group);
      updates.push(made.update);
      register(made.hit, {
        kind: 'portal',
        roomId: room.id,
        targetRoom: other,
        focus: {
          title: target.name,
          subtitle: 'Portal',
          body: `A shimmering passage. Press E to step through to “${target.name}.”`,
          mermaid: null,
        },
      });
    }
  }

  scene.add(group);
  return { interactables, updates };
}

function typeLabel(type) {
  return { plaque: 'Plaque', tome: 'Tome — full text', portrait: 'Portrait',
           artifact: 'Artifact', diagram: 'Diagram', image: 'Figure' }[type] || '';
}
