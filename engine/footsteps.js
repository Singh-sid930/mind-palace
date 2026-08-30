// The Marauder's footsteps: a trail of glowing prints that marches ahead of the
// keeper along the LEARNING path. Two scales, one seamless trail:
//   • inside a room. Walk the exhibits in study order (the room's exhibit
//     order: central metaphor first, then plaques/diagrams/figures), so the
//     prints show which module to attend to first;
//   • between rooms, once the room is toured, lead out through the doorway
//     that advances the wing's order (order 1 → 2 → 3 …), the same forward rule
//     the guiding wisp uses.
// Purely layout- + order-derived; no content authoring. Created once and lives
// in the main scene (like the wisp), so it follows the keeper across floors.

import * as THREE from 'three';
import { destRoomThroughDoor } from './wayfinding.js';

const N = 7;             // prints visible in the marching trail
const STRIDE = 0.95;     // metres between prints
const VISIBLE = N * STRIDE;
const FOOT_SEP = 0.40;   // left/right separation across the path
const MARCH = 0.9;       // trail speed (m/s)
const EX_REACH = 1.9;    // how near counts as "visited this exhibit"
const DOOR_REACH = 1.5;
const INK = 'rgba(255,223,150,0.96)';

function footTexture() {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 112;
  const ctx = c.getContext('2d');
  ctx.fillStyle = INK;
  // Sole (heel + ball) with toes toward the top (+canvas-up = travel forward).
  ctx.beginPath(); ctx.ellipse(32, 66, 15, 30, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(32, 40, 13, 16, 0, 0, Math.PI * 2); ctx.fill();
  for (const [x, y, r] of [[20, 26, 5], [29, 21, 5.5], [38, 21, 5], [46, 25, 4.4], [53, 32, 3.6]]) {
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const smooth = (x) => { const c = Math.min(1, Math.max(0, x)); return c * c * (3 - 2 * c); };

export class Footsteps {
  constructor(scene, layout, roomsById, getTour) {
    this.layout = layout;
    this.roomsById = roomsById;
    this.getTour = getTour || (() => null);
    this._room = null;
    this._queue = null;   // remaining waypoints: [{x,z,reach}]
    // Guidance is a toggle (P). Persisted, so it stays how the keeper left it: // on for a guided walk, off to roam or head straight somewhere of your own.
    this.enabled = !(typeof localStorage !== 'undefined' && localStorage.getItem('palace-footsteps') === 'off');

    this.group = new THREE.Group();
    const tex = footTexture();
    const geo = new THREE.PlaneGeometry(0.26, 0.52);
    geo.rotateX(-Math.PI / 2);           // lie flat; texture "up" -> world -Z
    this.prints = [];
    for (let i = 0; i < N; i++) {
      const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
        map: tex, transparent: true, depthWrite: false, side: THREE.DoubleSide, opacity: 0,
      }));
      m.renderOrder = 3;
      this.group.add(m);
      this.prints.push(m);
    }
    // A soft ring marking the immediate "go here next" spot.
    this.ring = new THREE.Mesh(
      new THREE.RingGeometry(0.5, 0.62, 32),
      new THREE.MeshBasicMaterial({ color: 0xffd98a, transparent: true, opacity: 0,
                                    side: THREE.DoubleSide, depthWrite: false })
    );
    this.ring.rotation.x = -Math.PI / 2;
    this.ring.renderOrder = 3;
    this.group.add(this.ring);
    scene.add(this.group);
  }

  // The forward doorway from a room (into the next-order chamber, or from the
  // hub into a wing's first chamber), mirrors the wisp's recommendation.
  _forwardDoor(roomId) {
    const here = this.roomsById[roomId];
    if (!here) return null;
    let best = null;
    for (const door of this.layout.doorsBySpace.get(roomId) || []) {
      const destId = destRoomThroughDoor(this.layout, roomId, door);
      if (!destId) continue;
      const dest = this.roomsById[destId];
      if (!dest) continue;
      if (here.wing == null) { if (dest.wing == null) continue; }
      else { if (dest.wing !== here.wing) continue; if (dest.order <= here.order) continue; }
      if (best && best.order <= dest.order) continue;
      best = { order: dest.order, door };
    }
    return best;
  }

  // Exhibits in study order, then the forward doorway (+ a point beyond it so
  // the trail leads on into the corridor toward the next chamber).
  _buildQueue(roomId) {
    const q = [];
    const tour = this.getTour(roomId);
    if (tour) for (const e of tour) q.push({ x: e.x, z: e.z, reach: EX_REACH });
    const fwd = this._forwardDoor(roomId);
    if (fwd) {
      const rc = this.layout.spaceById[roomId].rect;
      let dx = fwd.door.x - rc.cx, dz = fwd.door.z - rc.cz;
      const L = Math.hypot(dx, dz) || 1; dx /= L; dz /= L;
      q.push({ x: fwd.door.x, z: fwd.door.z, reach: DOOR_REACH });
      q.push({ x: fwd.door.x + dx * 5, z: fwd.door.z + dz * 5, reach: DOOR_REACH });
    }
    return q;
  }

  // Called on the throttled tick with the room the keeper stands in (null in a
  // corridor. We keep the existing queue so the trail keeps leading onward).
  setRoom(roomId) {
    if (roomId && roomId !== this._room) {
      this._room = roomId;
      this._queue = this._buildQueue(roomId);
    }
  }

  _hide() {
    for (const p of this.prints) p.material.opacity = 0;
    this.ring.material.opacity = 0;
  }

  setEnabled(on) {
    this.enabled = on;
    try { localStorage.setItem('palace-footsteps', on ? 'on' : 'off'); } catch (e) { /* ignore */ }
    if (!on) this._hide();
  }

  toggle() { this.setEnabled(!this.enabled); return this.enabled; }

  update(dt, camera, t) {
    if (!this.enabled) return;
    const px = camera.position.x, pz = camera.position.z;
    // Consume waypoints the keeper has reached, in order.
    if (this._queue) {
      while (this._queue.length &&
             Math.hypot(this._queue[0].x - px, this._queue[0].z - pz) < this._queue[0].reach) {
        this._queue.shift();
      }
    }
    if (!this._queue || !this._queue.length) { this._hide(); return; }

    const route = [{ x: px, z: pz }, ...this._queue];
    let routeLen = 0;
    for (let i = 0; i < route.length - 1; i++) {
      routeLen += Math.hypot(route[i + 1].x - route[i].x, route[i + 1].z - route[i].z);
    }
    if (routeLen < 0.6) { this._hide(); return; }
    const cap = Math.min(VISIBLE, routeLen);

    // Pulsing ring at the immediate target.
    const tgt = this._queue[0];
    this.ring.position.set(tgt.x, 0.05, tgt.z);
    this.ring.material.opacity = 0.22 + 0.12 * Math.sin(t * 3);
    this.ring.scale.setScalar(0.9 + 0.08 * Math.sin(t * 3));

    // Conveyor of prints: a shared offset marches them forward; the L/R side is
    // keyed to the physical slot, so the alternation stays seamless on wrap.
    const o = (t * MARCH) % STRIDE;
    for (let i = 0; i < N; i++) {
      const p = this.prints[i];
      const s = i * STRIDE + o;
      if (s > cap) { p.material.opacity = 0; continue; }
      const { x, z, tx, tz } = sampleRoute(route, s);
      const side = Math.round(s / STRIDE) % 2 ? 1 : -1;
      p.position.set(x + (-tz) * side * FOOT_SEP / 2, 0.05, z + tx * side * FOOT_SEP / 2);
      p.rotation.y = Math.atan2(-tx, -tz);
      p.scale.x = side; // mirror the print for the opposite foot
      const fin = smooth(s / (STRIDE * 0.9));
      const fout = smooth((cap - s) / (STRIDE * 1.3));
      p.material.opacity = 0.9 * Math.min(fin, fout);
    }
  }
}

// Point + unit tangent at arclength s along a polyline of {x,z}.
function sampleRoute(route, s) {
  for (let i = 0; i < route.length - 1; i++) {
    const a = route[i], b = route[i + 1];
    const dx = b.x - a.x, dz = b.z - a.z;
    const len = Math.hypot(dx, dz);
    if (len < 1e-4) continue;
    if (s <= len) {
      const u = s / len;
      return { x: a.x + dx * u, z: a.z + dz * u, tx: dx / len, tz: dz / len };
    }
    s -= len;
  }
  const a = route[route.length - 2], b = route[route.length - 1];
  const dx = b.x - a.x, dz = b.z - a.z, len = Math.hypot(dx, dz) || 1;
  return { x: b.x, z: b.z, tx: dx / len, tz: dz / len };
}
