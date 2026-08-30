// Lazy floor loading. Only the level the keeper stands on is fully built;
// other floors are built on first visit (stair, floo, teleport) and the
// least-recently-visited are disposed beyond a small cache. GPU cost is
// therefore bounded by a couple of floors no matter how large the palace
// grows. The layout itself (pure data) always covers the whole palace, maps,
// the constellation and the companion's gist need no geometry.
//
// The manager owns three LIVE collections that always reflect the ACTIVE
// level: `colliders` (the player holds this array), `interactables` (main
// raycasts this map) and `updates` (per-frame animations). Their identities
// never change; their contents are swapped on level switch.

import { buildEnvironment, buildLevel } from './builder.js';
import { buildExhibits } from './exhibits.js';
import { buildWayfinding } from './wayfinding.js';

const MAX_CACHED = 2; // levels kept built besides the active one

function disposeGroup(scene, group) {
  scene.remove(group);
  group.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    const mats = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
    for (const m of mats) {
      if (m.map) m.map.dispose();
      m.dispose();
    }
  });
}

export class LevelManager {
  constructor(scene, layout, roomsById, graph) {
    this.scene = scene;
    this.layout = layout;
    this.roomsById = roomsById;
    this.graph = graph;
    this.loaded = new Map(); // levelId -> { groups, colliders, interactables, updates, signs, stamp }
    this.activeId = undefined;
    this._stamp = 0;

    this.colliders = [];
    this.interactables = new Map();
    this.updates = [];
    this.tours = new Map(); // roomId -> ordered exhibit waypoints (footsteps guide)

    const env = buildEnvironment(scene);
    this.dome = env.dome;
  }

  levelOf(roomId) {
    const sp = this.layout.spaceById[roomId];
    return sp ? sp.level : null;
  }

  get signs() {
    const rec = this.loaded.get(this.activeId);
    return rec ? rec.signs : [];
  }

  // The active floor's PointLights (ambient events dim these; see events.js).
  get lights() {
    const rec = this.loaded.get(this.activeId);
    const out = [];
    if (rec) for (const g of rec.groups) g.traverse((o) => { if (o.isPointLight) out.push(o); });
    return out;
  }

  // Make the level containing `roomId` the active (visible, walkable) one.
  activateFor(roomId) {
    const levelId = this.levelOf(roomId);
    if (levelId === undefined || levelId === this.activeId) return;

    let rec = this.loaded.get(levelId);
    if (!rec) {
      const world = buildLevel(this.scene, this.layout, levelId);
      const ex = buildExhibits(this.scene, this.layout, this.roomsById, levelId);
      const way = buildWayfinding(this.scene, this.layout, this.roomsById, this.graph, levelId);
      for (const [obj, r] of way.interactables) ex.interactables.set(obj, r);
      for (const [rid, arr] of ex.tours) this.tours.set(rid, arr);
      rec = {
        groups: [world.group, ex.group, way.group],
        colliders: world.colliders,
        interactables: ex.interactables,
        updates: [...world.updates, ...ex.updates],
        signs: way.signs,
      };
      this.loaded.set(levelId, rec);
    }
    rec.stamp = ++this._stamp;

    // Show only the active floor: hidden groups also take their point lights
    // out of the shading pass, so light cost stays one-floor-sized too.
    for (const [id, r] of this.loaded) {
      for (const g of r.groups) g.visible = id === levelId;
    }
    this.activeId = levelId;

    this.colliders.length = 0;
    this.colliders.push(...rec.colliders);
    this.interactables.clear();
    for (const [k, v] of rec.interactables) this.interactables.set(k, v);
    this.updates.length = 0;
    this.updates.push(...rec.updates);

    this._evict();
  }

  _evict() {
    while (this.loaded.size > MAX_CACHED + 1) {
      let oldest = null;
      for (const [id, r] of this.loaded) {
        if (id === this.activeId) continue;
        if (!oldest || r.stamp < oldest.rec.stamp) oldest = { id, rec: r };
      }
      if (!oldest) return;
      for (const g of oldest.rec.groups) disposeGroup(this.scene, g);
      this.loaded.delete(oldest.id);
    }
  }
}
