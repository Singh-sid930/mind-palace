// The guiding wisp: a faint will-o'-the-wisp that appears only when you stand
// still or look toward the way onward, then drifts to the doorway that leads
// deeper along the learning path. A gentle nudge layered on top of the always-
// present signposts (see wayfinding.js), it never clutters ordinary walking.
//
// Recommendation = the next chamber in the wing by `order` (from the hub, the
// first chamber of a wing). Purely layout-derived; no content authoring.

import * as THREE from 'three';
import { destRoomThroughDoor } from './wayfinding.js';
import { tipTexture } from './text.js';
import { palette } from './palettes.js';

const GLOW = 0xffe6a6;
const HOVER_Y = 1.55;

// One recommended forward doorway per room: { x, z, destName } or null.
function computeRecommendations(layout, roomsById) {
  const rec = new Map();
  for (const space of layout.spaces) {
    if (space.kind !== 'room' || !space.room) continue;
    const here = space.room;
    let best = null;
    for (const door of layout.doorsBySpace.get(space.id) || []) {
      const destId = destRoomThroughDoor(layout, space.id, door);
      if (!destId) continue;
      const dest = roomsById[destId];
      if (!dest) continue;
      if (here.wing == null) {
        if (dest.wing == null) continue;          // hub: enter a wing...
      } else {
        if (dest.wing !== here.wing) continue;     // ...else stay in this wing
        if (dest.order <= here.order) continue;    // ...and only go forward
      }
      if (best && best.order <= dest.order) continue; // nearest next chamber
      best = { order: dest.order, x: door.x, z: door.z, destName: dest.name };
    }
    rec.set(here.id, best ? { x: best.x, z: best.z, destName: best.destName } : null);
  }
  return rec;
}

export class Wisp {
  constructor(scene, layout, roomsById) {
    this.recommendation = computeRecommendations(layout, roomsById);

    this.group = new THREE.Group();
    this.group.visible = false;
    this.body = new THREE.Group();
    this.group.add(this.body);

    this.core = new THREE.Mesh(
      new THREE.SphereGeometry(0.11, 16, 16),
      new THREE.MeshBasicMaterial({ color: GLOW, transparent: true })
    );
    this.halo = new THREE.Mesh(
      new THREE.SphereGeometry(0.26, 16, 16),
      new THREE.MeshBasicMaterial({ color: GLOW, transparent: true, opacity: 0.25, depthWrite: false })
    );
    this.light = new THREE.PointLight(GLOW, 1.2, 4.5, 1.8);

    this.motes = new THREE.Group();
    this.moteList = [];
    for (let i = 0; i < 3; i++) {
      const m = new THREE.Mesh(
        new THREE.SphereGeometry(0.03, 8, 8),
        new THREE.MeshBasicMaterial({ color: GLOW, transparent: true })
      );
      m.userData.phase = (i / 3) * Math.PI * 2;
      this.motes.add(m);
      this.moteList.push(m);
    }

    this.label = new THREE.Sprite(new THREE.SpriteMaterial({ transparent: true, depthTest: true }));
    this.label.scale.set(1.77, 0.62, 1);
    this.label.position.y = 0.56;

    this.body.add(this.core, this.halo, this.light, this.motes, this.label);
    scene.add(this.group);

    this.opacity = 0;
    this.idle = 0;
    this.haveTarget = false;
    this.curRoom = null;
    this.target = new THREE.Vector3();
    this._prev = new THREE.Vector3();
    this._toDoor = new THREE.Vector3();
    this._fwd = new THREE.Vector3();
    this._placed = false;
  }

  // Switch which room's recommendation the wisp is serving.
  setRoom(roomId) {
    if (roomId === this.curRoom) return;
    this.curRoom = roomId;
    const rec = roomId ? this.recommendation.get(roomId) : null;
    if (!rec) { this.haveTarget = false; return; }
    this.haveTarget = true;
    this.target.set(rec.x, HOVER_Y, rec.z);
    if (!this._placed) { this.group.position.copy(this.target); this._placed = true; }

    const pal = palette('parchment');
    const old = this.label.material.map;
    this.label.material.map = tipTexture({ text: rec.destName, pal });
    this.label.material.needsUpdate = true;
    if (old) old.dispose();
  }

  update(dt, camera, t) {
    // Idle detection from camera movement (no need to reach into player state).
    const moved = camera.position.distanceTo(this._prev);
    this._prev.copy(camera.position);
    if (moved > 0.02) this.idle = 0; else this.idle += dt;

    let show = false;
    if (this.haveTarget) {
      // Drift smoothly toward the recommended doorway.
      this.group.position.lerp(this.target, 1 - Math.pow(0.0015, dt));

      this._toDoor.subVectors(this.target, camera.position); this._toDoor.y = 0;
      const dist = this._toDoor.length();
      this._toDoor.normalize();
      camera.getWorldDirection(this._fwd); this._fwd.y = 0; this._fwd.normalize();
      const facing = this._fwd.dot(this._toDoor) > 0.82; // within ~35 degrees
      show = dist > 1.3 && (this.idle > 1.2 || facing);
    }

    const targetOpacity = show ? 1 : 0;
    this.opacity += (targetOpacity - this.opacity) * Math.min(1, dt * 4);
    this.group.visible = this.opacity > 0.01;
    if (!this.group.visible) return;

    // Bob, spin motes, pulse.
    this.body.position.y = Math.sin(t * 2.0) * 0.07;
    this.motes.rotation.y = t * 1.3;
    this.moteList.forEach((m, i) => {
      const a = m.userData.phase + t * 1.3;
      m.position.set(Math.cos(a) * 0.26, Math.sin(t * 2.4 + i) * 0.1, Math.sin(a) * 0.26);
    });
    const pulse = 0.85 + 0.15 * Math.sin(t * 3.2);

    this.core.material.opacity = this.opacity;
    this.halo.material.opacity = 0.25 * this.opacity * pulse;
    this.label.material.opacity = this.opacity;
    this.moteList.forEach((m) => { m.material.opacity = this.opacity; });
    this.light.intensity = 1.2 * this.opacity * pulse;
  }
}
