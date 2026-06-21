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

export function solveLayout(world, roomsById) {
  // Each level is laid out around its own hub, in its own far-apart region of
  // the plane (reached by staircase, not on foot). One level → behaves as before.
  const LEVEL_GAP = 400;
  const levels = (world.levels && world.levels.length)
    ? world.levels
    : [{ id: null, hub: world.hub }];
  const hasLevels = !!(world.levels && world.levels.length);
  const wingLevelOf = (w) => (hasLevels ? (w.level || world.levels[0].id) : null);

  const spaces = [];
  let spawn = null;

  levels.forEach((level, li) => {
    const ox = li * LEVEL_GAP;
    const hubRoom = roomsById[level.hub];
    const hubSize = ROOM_SIZE[hubRoom.size];
    spaces.push({
      id: level.hub, kind: 'room', room: hubRoom, wing: null, level: level.id,
      rect: rect(ox, 0, hubSize, hubSize),
      h: ROOM_HEIGHT[hubRoom.size],
      paletteName: hubRoom.palette || 'parchment',
    });

    const levelWings = world.wings.filter((w) => wingLevelOf(w) === level.id);
    if (levelWings.length > 4) {
      console.warn(`Level '${level.id}': >4 wings overlap. TODO: ring layout.`);
    }
    levelWings.forEach((wing, i) => {
      const dir = DIRS[i % 4];
      const members = Object.values(roomsById)
        .filter((r) => r.wing === wing.id)
        .sort((a, b) => a.order - b.order);

      let cursor = hubSize / 2; // distance from the hub along dir to last far edge
      members.forEach((room, k) => {
        const size = ROOM_SIZE[room.size];
        // Corridor between previous space and this room.
        const cMid = cursor + CORRIDOR_LEN / 2;
        const isX = dir.x !== 0;
        spaces.push({
          id: `${wing.id}-corridor-${k + 1}`, kind: 'corridor', room: null,
          wing: wing.id, level: level.id,
          rect: isX
            ? rect(ox + dir.x * cMid, 0, CORRIDOR_LEN, CORRIDOR_W)
            : rect(ox, dir.z * cMid, CORRIDOR_W, CORRIDOR_LEN),
          h: CORRIDOR_H,
          paletteName: room.palette || wing.palette,
        });
        cursor += CORRIDOR_LEN;
        // The room itself.
        const rMid = cursor + size / 2;
        spaces.push({
          id: room.id, kind: 'room', room, wing: wing.id, level: level.id,
          rect: isX
            ? rect(ox + dir.x * rMid, 0, size, size)
            : rect(ox, dir.z * rMid, size, size),
          h: ROOM_HEIGHT[room.size],
          paletteName: room.palette || wing.palette,
        });
        cursor += size;
      });
    });

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

  return {
    spaces, spaceById, doors, doorsBySpace, portals, roomNeighbors,
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
