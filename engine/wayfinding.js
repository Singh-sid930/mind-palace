// In-world wayfinding signposts. For every doorway leading out of a room, a
// carved wooden signpost is raised just inside that room, naming the chamber
// that lies beyond and how it relates to the one you stand in. Everything is
// derived from the solved layout + the knowledge graph, no content authoring.
//
// Direction word comes from the layout (deeper into a wing = Onward, back
// toward the hub = Back, the hub itself = Atrium, another wing = Across).
// The italic hint comes from the strongest graph edge between the two rooms'
// concepts (builds-on > part-of > contrasts-with > relates-to).

import * as THREE from 'three';
import { palette } from './palettes.js';
import { signTexture } from './text.js';
import { lam, DARKWOOD, METAL } from './common.js';

const REL_PRIORITY = { 'builds-on': 3, 'part-of': 2, 'contrasts-with': 1, 'relates-to': 0 };

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// Follow a doorway out of `roomId` to the room on the far side. Doors usually
// open onto a corridor; trace through it to the room beyond.
export function destRoomThroughDoor(layout, roomId, door) {
  const otherId = door.a === roomId ? door.b : door.a;
  const other = layout.spaceById[otherId];
  if (!other) return null;
  if (other.kind === 'room') return otherId;
  for (const d2 of layout.doorsBySpace.get(otherId) || []) {
    const farId = d2.a === otherId ? d2.b : d2.a;
    if (farId === roomId) continue;
    const far = layout.spaceById[farId];
    if (far && far.kind === 'room') return farId;
  }
  return null;
}

// Layout-derived direction from room `from` to room `to`.
function directionFor(from, to) {
  if (to.wing == null) return { dir: 'home', word: 'Atrium' };
  if (from.wing == null) return { dir: 'fwd', word: 'Begin' };
  if (from.wing === to.wing) {
    return to.order > from.order ? { dir: 'fwd', word: 'Onward' }
                                 : { dir: 'back', word: 'Back' };
  }
  return { dir: 'across', word: 'Across' };
}

// Strongest concept edge spanning the two rooms, with its direction. `dir` is
// 'DtoR' when the edge points from a concept in the destination to one here.
function roomRelation(edges, conceptRoom, hereId, destId) {
  let best = null;
  for (const e of edges) {
    const fr = conceptRoom[e.from], tr = conceptRoom[e.to];
    let edgeDir = null;
    if (fr === hereId && tr === destId) edgeDir = 'RtoD';
    else if (fr === destId && tr === hereId) edgeDir = 'DtoR';
    else continue;
    if (!best || REL_PRIORITY[e.relation] > REL_PRIORITY[best.relation]) {
      best = { relation: e.relation, dir: edgeDir };
    }
  }
  return best;
}

function relationHint(best) {
  if (!best) return '';
  switch (best.relation) {
    case 'builds-on':
      return best.dir === 'DtoR' ? 'builds on this chamber' : 'the groundwork beneath this';
    case 'part-of':
      return 'part of the same whole';
    case 'contrasts-with':
      return 'a contrasting view';
    case 'relates-to':
      return 'closely entwined';
    default:
      return '';
  }
}

// A post topped by a textured board. The board faces +z in local space; the
// caller rotates the group so it faces into the room.
function buildSignpost(pal, tex) {
  const g = new THREE.Group();
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 2.2, 8), lam(DARKWOOD));
  post.position.y = 1.1;
  const cap = new THREE.Mesh(new THREE.SphereGeometry(0.095, 10, 8), lam(METAL));
  cap.position.y = 2.22;

  const board = new THREE.Group();
  board.position.y = 1.55;
  const frame = new THREE.Mesh(
    new THREE.BoxGeometry(1.66, 1.06, 0.08),
    new THREE.MeshLambertMaterial({ color: pal.accent, emissive: pal.glow, emissiveIntensity: 0.2 })
  );
  const face = new THREE.Mesh(
    new THREE.PlaneGeometry(1.5, 0.94),
    new THREE.MeshBasicMaterial({ map: tex })
  );
  face.position.z = 0.05;
  board.add(frame, face);

  g.add(post, cap, board);
  return g;
}

const TRAVEL_VERB = { home: 'return to', back: 'go back to', across: 'cross to', fwd: 'go to' };

export function buildWayfinding(scene, layout, roomsById, graph, levelId = null) {
  const group = new THREE.Group();
  const interactables = new Map(); // sign mesh -> { kind:'sign', destRoom, prompt }
  const signs = [];                // metadata, for debugging / tooling
  const conceptRoom = {};
  for (const c of graph.concepts) conceptRoom[c.id] = c.room;

  const WALL_INSET = 0.95;   // how far into the room from the wall
  const SIDE_PAD = 0.85;     // along the wall, clear of the opening
  const EDGE_PAD = 1.4;      // keep the post off the corners

  for (const space of layout.spaces) {
    if (space.kind !== 'room' || !space.room) continue;
    if (levelId != null && space.level !== levelId) continue;
    const here = space.room;
    const pal = palette(space.paletteName);

    for (const door of layout.doorsBySpace.get(space.id) || []) {
      const destId = destRoomThroughDoor(layout, space.id, door);
      if (!destId) continue;
      const dest = roomsById[destId];
      if (!dest) continue;

      const { dir, word } = directionFor(here, dest);
      const hint = relationHint(roomRelation(graph.edges, conceptRoom, here.id, destId));
      const tex = signTexture({ dir, word, dest: dest.name, hint, pal });
      const sign = buildSignpost(pal, tex);

      // Place the post just inside the room, beside the opening, facing in.
      let px, pz, yaw;
      const rect = space.rect;
      if (door.axis === 'x') {
        const nx = Math.sign(rect.cx - door.x) || 1;
        const lz = Math.sign(rect.cz - door.z) || 1;
        px = door.x + nx * WALL_INSET;
        pz = clamp(door.z + lz * (door.width / 2 + SIDE_PAD),
                   rect.minZ + EDGE_PAD, rect.maxZ - EDGE_PAD);
        yaw = Math.atan2(nx, 0);
      } else {
        const nz = Math.sign(rect.cz - door.z) || 1;
        const lx = Math.sign(rect.cx - door.x) || 1;
        pz = door.z + nz * WALL_INSET;
        px = clamp(door.x + lx * (door.width / 2 + SIDE_PAD),
                   rect.minX + EDGE_PAD, rect.maxX - EDGE_PAD);
        yaw = Math.atan2(0, nz);
      }
      sign.position.set(px, 0, pz);
      sign.rotation.y = yaw;
      group.add(sign);

      const record = { kind: 'sign', destRoom: destId,
                       prompt: `${TRAVEL_VERB[dir] || 'go to'} “${dest.name}”` };
      sign.traverse((o) => interactables.set(o, record));
      signs.push({ x: px, z: pz, yaw, destRoom: destId, prompt: record.prompt });
    }
  }

  scene.add(group);
  return { group, interactables, signs };
}
