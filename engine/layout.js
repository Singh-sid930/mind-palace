// Deterministic layout solver. Content files declare ONLY semantics
// (wing, order, connections); this module assigns all geometry. The same
// world data always produces the same castle.
//
// Plan: the hub sits at the origin. Each wing radiates along a cardinal
// direction as a chain: hub -> corridor -> room(order 1) -> corridor ->
// room(order 2) -> ... Rooms are axis-aligned squares; consecutive spaces
// share an edge and get a doorway cut into it. Declared connections that
// are not physical neighbors become glowing portal pairs.

export const ROOM_SIZE = { small: 9, medium: 13, grand: 19 };
export const ROOM_HEIGHT = { small: 4.6, medium: 5.0, grand: 6.6 };
// A descending staircase sinks a stairwell pit into its room's floor. These
// dimensions are shared by the floor-hole cutter (builder) and the prop (props).
export const STAIR_PIT = { depth: 2.4, width: 2.6, run: 3.0 };
const CORRIDOR_LEN = 7;
const CORRIDOR_W = 3.4;
const CORRIDOR_H = 3.4;
export const DOOR_HEIGHT = 2.7;
const EPS = 0.01;

// Cardinal directions (XZ plane): east, north, west, south.
const DIRS = [
  { x: 1, z: 0 },
  { x: 0, z: -1 },
  { x: -1, z: 0 },
  { x: 0, z: 1 },
];

function rect(cx, cz, w, d) {
  return { cx, cz, w, d,
           minX: cx - w / 2, maxX: cx + w / 2,
           minZ: cz - d / 2, maxZ: cz + d / 2 };
}

// --- Branching-wing helpers (see growWing) --------------------------------
// Center of a rect's face in cardinal direction h (h is one of DIRS).
function faceCenter(r, h) {
  if (h.x === 1) return { x: r.maxX, z: r.cz };
  if (h.x === -1) return { x: r.minX, z: r.cz };
  if (h.z === 1) return { x: r.cx, z: r.maxZ };
  return { x: r.cx, z: r.minZ };
}
// A corridor rect of length `len` sprouting from prevRect's `h` face.
function corridorFrom(prevRect, h, len) {
  const f = faceCenter(prevRect, h);
  return h.x !== 0
    ? rect(f.x + h.x * len / 2, f.z, len, CORRIDOR_W)
    : rect(f.x, f.z + h.z * len / 2, CORRIDOR_W, len);
}
// A room of side `size` past the far end of `corridor`, centered on the axis.
function roomPast(corridor, h, size) {
  const f = faceCenter(corridor, h);
  return h.x !== 0
    ? rect(f.x + h.x * size / 2, f.z, size, size)
    : rect(f.x, f.z + h.z * size / 2, size, size);
}
// Left/right unit turns off heading h.
const turnL = (h) => ({ x: -h.z, z: h.x });
const turnR = (h) => ({ x: h.z, z: -h.x });
const sameDir = (a, b) => a.x === b.x && a.z === b.z;
// Axis-aligned overlap test with a margin (keeps unconnected rooms apart so no
// accidental doorways form between them, and leaves wall gaps).
function rectsClash(a, b, pad) {
  return a.minX < b.maxX + pad && a.maxX > b.minX - pad &&
         a.minZ < b.maxZ + pad && a.maxZ > b.minZ - pad;
}
// Attach a corridor+room to prevRect, trying candidate headings in order and
// pushing the room progressively farther out until it clears everything already
// placed (except prevRect, which it is meant to touch). Deterministic: no RNG.
function attach(prevRect, headings, baseLen, size, placed, pad) {
  for (let grow = 0; grow < 20; grow++) {
    const len = baseLen + grow * 3;
    for (const h of headings) {
      const corridor = corridorFrom(prevRect, h, len);
      const room = roomPast(corridor, h, size);
      const clash = placed.some((p) => p !== prevRect &&
        (rectsClash(corridor, p, pad) || rectsClash(room, p, pad)));
      if (!clash) return { h, corridor, room };
    }
  }
  const h = headings[0];
  const corridor = corridorFrom(prevRect, h, baseLen);
  return { h, corridor, room: roomPast(corridor, h, size) };
}

// Lay a wing out as a bending "fishbone": a spine that advances outward (and
// turns once, mid-way) with side-chambers budding off alternating sides. Purely
// a function of room order + count, so the same data always yields the same
// castle. Pushes {corridor, room} spaces into `out` and their rects into
// `placed` (shared across wings so they never overlap).
function growWing(wing, members, hubRect, dir, levelId, out, placed) {
  const N = members.length;
  const CORRIDOR = 7, BUD_CORRIDOR = 4, PAD = 1.3;
  // Even-indexed rooms (2nd, 4th, …) bud off the spine; the last room always
  // stays on the spine so a wing ends at its climax chamber, not a side room.
  const isBud = (k) => k % 2 === 1 && k !== N - 1;
  const numSpine = members.filter((_, k) => !isBud(k)).length;
  const bendAt = numSpine >= 3 ? Math.floor(numSpine / 2) : -1; // turn mid-spine

  let heading = dir;
  let prevSpine = hubRect;
  let spineIdx = 0;
  let budCount = 0;
  members.forEach((room, k) => {
    const size = ROOM_SIZE[room.size];
    const paletteName = room.palette || wing.palette;
    if (isBud(k)) {
      // Chamber off the current spine segment, alternating side.
      const first = budCount % 2 === 0 ? turnL(heading) : turnR(heading);
      const second = sameDir(first, turnL(heading)) ? turnR(heading) : turnL(heading);
      budCount++;
      const { corridor, room: rrect } = attach(prevSpine, [first, second], BUD_CORRIDOR, size, placed, PAD);
      out.push({ id: `${wing.id}-corridor-${k + 1}`, kind: 'corridor', room: null,
                 wing: wing.id, level: levelId, rect: corridor, h: CORRIDOR_H, paletteName });
      out.push({ id: room.id, kind: 'room', room, wing: wing.id, level: levelId,
                 rect: rrect, h: ROOM_HEIGHT[room.size], paletteName });
      placed.push(corridor, rrect);
    } else {
      // Spine step: go straight, but at the bend prefer a turn. Never backward.
      const back = { x: -heading.x, z: -heading.z };
      const order = spineIdx === bendAt
        ? [turnL(heading), heading, turnR(heading)]
        : [heading, turnL(heading), turnR(heading)];
      const cands = order.filter((c) => !sameDir(c, back));
      const { h, corridor, room: rrect } = attach(prevSpine, cands, CORRIDOR, size, placed, PAD);
      out.push({ id: `${wing.id}-corridor-${k + 1}`, kind: 'corridor', room: null,
                 wing: wing.id, level: levelId, rect: corridor, h: CORRIDOR_H, paletteName });
      out.push({ id: room.id, kind: 'room', room, wing: wing.id, level: levelId,
                 rect: rrect, h: ROOM_HEIGHT[room.size], paletteName });
      placed.push(corridor, rrect);
      heading = h;
      prevSpine = rrect;
      spineIdx++;
    }
  });
}

export function solveLayout(world, roomsById) {
  // Each level is laid out around its own hub, then packed left-to-right along
  // +x with a fixed pad between bounding boxes (reached by staircase, not on
  // foot). The pad only has to defeat the fog (far = 64) so floors never see
  // each other; packing by extent means any number of levels of any size fit.
  const LEVEL_PAD = 140;
  const levels = (world.levels && world.levels.length)
    ? world.levels
    : [{ id: null, hub: world.hub }];
  const hasLevels = !!(world.levels && world.levels.length);
  const wingLevelOf = (w) => (hasLevels ? (w.level || world.levels[0].id) : null);
  // Each level carries a signed tier (elevation): foundations are negative,
  // ground is 0, derived floors are positive. Stairs read tiers to know up/down.
  const resolvedLevels = levels.map((l) => ({ ...l, tier: Number.isFinite(l.tier) ? l.tier : 0 }));
  const levelById = Object.fromEntries(resolvedLevels.map((l) => [l.id, l]));

  const spaces = [];
  let spawn = null;
  let cursorX = 0;

  levels.forEach((level) => {
    // Lay the level out around its own local origin first; shift it into its
    // packed region once its extent is known.
    const levelSpaces = [];
    const hubRoom = roomsById[level.hub];
    const hubSize = ROOM_SIZE[hubRoom.size];
    const hubRect = rect(0, 0, hubSize, hubSize);
    levelSpaces.push({
      id: level.hub, kind: 'room', room: hubRoom, wing: null, level: level.id,
      rect: hubRect,
      h: ROOM_HEIGHT[hubRoom.size],
      paletteName: hubRoom.palette || 'parchment',
    });

    const levelWings = world.wings.filter((w) => wingLevelOf(w) === level.id);
    if (levelWings.length > 4) {
      console.warn(`Level '${level.id}': >4 wings overlap. TODO: ring layout.`);
    }
    // Each wing grows as a branching fishbone in its own cardinal sector; the
    // shared `placed` list keeps wings (and their side-chambers) from colliding.
    const placed = [hubRect];
    levelWings.forEach((wing, i) => {
      const dir = DIRS[i % 4];
      const members = Object.values(roomsById)
        .filter((r) => r.wing === wing.id)
        .sort((a, b) => a.order - b.order);
      growWing(wing, members, hubRect, dir, level.id, levelSpaces, placed);
    });

    // Pack: shift the whole level so its west edge starts at cursorX.
    const minX = Math.min(...levelSpaces.map((s) => s.rect.minX));
    const maxX = Math.max(...levelSpaces.map((s) => s.rect.maxX));
    const ox = cursorX - minX;
    for (const s of levelSpaces) {
      s.rect = rect(s.rect.cx + ox, s.rect.cz, s.rect.w, s.rect.d);
      spaces.push(s);
    }
    cursorX += (maxX - minX) + LEVEL_PAD;

    if (level.hub === world.hub) {
      const firstDir = DIRS[0];
      spawn = { x: ox, z: 0, yaw: Math.atan2(-firstDir.x, -firstDir.z) };
    }
  });

  // --- Doors: every pair of spaces sharing an edge gets a doorway. ---------
  const doors = [];
  for (let i = 0; i < spaces.length; i++) {
    for (let j = i + 1; j < spaces.length; j++) {
      const A = spaces[i].rect, B = spaces[j].rect;
      // A's east edge touching B's west edge (or vice versa).
      for (const [a, b] of [[spaces[i], spaces[j]], [spaces[j], spaces[i]]]) {
        if (Math.abs(a.rect.maxX - b.rect.minX) < EPS) {
          const lo = Math.max(a.rect.minZ, b.rect.minZ);
          const hi = Math.min(a.rect.maxZ, b.rect.maxZ);
          if (hi - lo > 2) {
            doors.push({ a: a.id, b: b.id, axis: 'x',
                         x: a.rect.maxX, z: (lo + hi) / 2,
                         width: Math.min(2.6, hi - lo - 1.2), height: DOOR_HEIGHT });
          }
        }
        if (Math.abs(a.rect.maxZ - b.rect.minZ) < EPS) {
          const lo = Math.max(a.rect.minX, b.rect.minX);
          const hi = Math.min(a.rect.maxX, b.rect.maxX);
          if (hi - lo > 2) {
            doors.push({ a: a.id, b: b.id, axis: 'z',
                         x: (lo + hi) / 2, z: a.rect.maxZ,
                         width: Math.min(2.6, hi - lo - 1.2), height: DOOR_HEIGHT });
          }
        }
      }
    }
  }

  // --- Physical room adjacency (through corridors) for portal planning. ----
  const touch = new Map(); // spaceId -> Set(spaceId)
  for (const d of doors) {
    if (!touch.has(d.a)) touch.set(d.a, new Set());
    if (!touch.has(d.b)) touch.set(d.b, new Set());
    touch.get(d.a).add(d.b);
    touch.get(d.b).add(d.a);
  }
  const spaceById = Object.fromEntries(spaces.map((s) => [s.id, s]));
  const roomNeighbors = new Map(); // roomId -> Set(roomId)
  for (const s of spaces.filter((s) => s.kind === 'room')) {
    const seen = new Set();
    for (const n1 of touch.get(s.id) || []) {
      if (spaceById[n1].kind === 'room') seen.add(n1);
      else for (const n2 of touch.get(n1) || []) {
        if (n2 !== s.id && spaceById[n2].kind === 'room') seen.add(n2);
      }
    }
    roomNeighbors.set(s.id, seen);
  }

  // --- Portals: declared connections that aren't physical neighbors. -------
  const portals = [];
  const seenPairs = new Set();
  for (const s of spaces.filter((s) => s.kind === 'room')) {
    for (const target of s.room?.connections || []) {
      const key = [s.id, target].sort().join('::');
      if (seenPairs.has(key)) continue;
      seenPairs.add(key);
      if (!(roomNeighbors.get(s.id) || new Set()).has(target)) {
        portals.push({ a: s.id, b: target });
      }
    }
  }

  // Doors grouped by space for the wall builder.
  const doorsBySpace = new Map();
  for (const d of doors) {
    for (const id of [d.a, d.b]) {
      if (!doorsBySpace.has(id)) doorsBySpace.set(id, []);
      doorsBySpace.get(id).push(d);
    }
  }

  // --- Passages: typed links between rooms (see world.passages). -------------
  // Each passage expands into a "mouth" in each of its two end rooms, placed on
  // a free wall. This one structure is authoritative for the floor-hole cutter
  // (builder), the prop placer (exhibits) and the gatekeeper ghost. A stair
  // "descends" when the destination tier is lower; an archway is lateral.
  const tierOfRoom = (roomId) => {
    const sp = spaceById[roomId];
    const lv = sp ? levelById[sp.level] : null;
    return lv && Number.isFinite(lv.tier) ? lv.tier : 0;
  };
  const SIDE_YAW = { minZ: 0, maxZ: Math.PI, minX: Math.PI / 2, maxX: -Math.PI / 2 };
  const INSET = 0.85;

  // First pass: turn each passage into two raw mouths (one per end room).
  const rawMouths = [];
  for (const psg of world.passages || []) {
    const [aId, bId] = psg.between || [];
    if (!spaceById[aId] || !spaceById[bId]) continue;   // skip refs not yet built
    for (const [self, other] of [[aId, bId], [bId, aId]]) {
      const dir = psg.type === 'archway'
        ? 'lateral'
        : (tierOfRoom(other) < tierOfRoom(self) ? 'down' : 'up');
      rawMouths.push({
        passageId: psg.id, type: psg.type, kind: psg.type === 'archway' ? 'archway' : 'stair',
        roomId: self, to: other, dir,
        gate: psg.gate && psg.gate.at === self ? psg.gate : null,
      });
    }
  }

  // Second pass: assign each room's mouths to distinct free walls + geometry.
  const mouths = [];
  const byRoom = {};
  for (const m of rawMouths) (byRoom[m.roomId] || (byRoom[m.roomId] = [])).push(m);
  for (const roomId of Object.keys(byRoom)) {
    const r = spaceById[roomId].rect;
    const sideDoors = doorsBySpace.get(roomId) || [];
    const hasDoor = (side) => {
      if (side === 'minZ' || side === 'maxZ') {
        const at = side === 'minZ' ? r.minZ : r.maxZ;
        return sideDoors.some((d) => d.axis === 'z' && Math.abs(d.z - at) < 0.05);
      }
      const at = side === 'minX' ? r.minX : r.maxX;
      return sideDoors.some((d) => d.axis === 'x' && Math.abs(d.x - at) < 0.05);
    };
    const free = ['minZ', 'maxZ', 'minX', 'maxX'].filter((sd) => !hasDoor(sd));
    byRoom[roomId].forEach((m, i) => {
      const side = free[i % free.length] || 'minZ';
      let x, z;
      if (side === 'minZ') { x = r.cx; z = r.minZ + INSET; }
      else if (side === 'maxZ') { x = r.cx; z = r.maxZ - INSET; }
      else if (side === 'minX') { x = r.minX + INSET; z = r.cz; }
      else { x = r.maxX - INSET; z = r.cz; }
      let pit = null;
      if (m.kind === 'stair' && m.dir === 'down') {
        const hw = STAIR_PIT.width / 2, run = STAIR_PIT.run;
        if (side === 'minZ') pit = { minX: r.cx - hw, maxX: r.cx + hw, minZ: r.minZ, maxZ: r.minZ + run };
        else if (side === 'maxZ') pit = { minX: r.cx - hw, maxX: r.cx + hw, minZ: r.maxZ - run, maxZ: r.maxZ };
        else if (side === 'minX') pit = { minX: r.minX, maxX: r.minX + run, minZ: r.cz - hw, maxZ: r.cz + hw };
        else pit = { minX: r.maxX - run, maxX: r.maxX, minZ: r.cz - hw, maxZ: r.cz + hw };
      }
      mouths.push({ ...m, side, x, z, yaw: SIDE_YAW[side], level: spaceById[roomId].level, pit });
    });
  }

  return {
    spaces, spaceById, doors, doorsBySpace, portals, roomNeighbors,
    levels: resolvedLevels, levelById, mouths, tierOfRoom,
    spawn: spawn || { x: 0, z: 0, yaw: Math.atan2(-DIRS[0].x, -DIRS[0].z) },
  };
}

// Which space contains this point (for HUD room labels / map)?
export function spaceAt(layout, x, z) {
  for (const s of layout.spaces) {
    if (x >= s.rect.minX - EPS && x <= s.rect.maxX + EPS &&
        z >= s.rect.minZ - EPS && z <= s.rect.maxZ + EPS) return s;
  }
  return null;
}
