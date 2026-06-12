// First-person movement: PointerLockControls for look, WASD for walk,
// circle-vs-AABB sliding collision against wall boxes. Fixed eye height.

import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

export const EYE = 1.62;
const RADIUS = 0.42;
const SPEED = 4.4;
const SPRINT = 8.2;

export class Player {
  constructor(camera, dom, colliders) {
    this.camera = camera;
    this.controls = new PointerLockControls(camera, dom);
    this.colliders = colliders;
    this.keys = new Set();
    this.enabled = false;

    document.addEventListener('keydown', (e) => this.keys.add(e.code));
    document.addEventListener('keyup', (e) => this.keys.delete(e.code));
    window.addEventListener('blur', () => this.keys.clear());
  }

  place(x, z, yaw) {
    this.camera.position.set(x, EYE, z);
    this.camera.rotation.set(0, yaw, 0, 'YXZ');
  }

  update(dt) {
    if (!this.enabled) return;
    const fwd = new THREE.Vector3();
    this.camera.getWorldDirection(fwd);
    fwd.y = 0;
    if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, -1);
    fwd.normalize();
    const right = new THREE.Vector3(-fwd.z, 0, fwd.x);

    const move = new THREE.Vector3();
    if (this.keys.has('KeyW') || this.keys.has('ArrowUp')) move.add(fwd);
    if (this.keys.has('KeyS') || this.keys.has('ArrowDown')) move.sub(fwd);
    if (this.keys.has('KeyD') || this.keys.has('ArrowRight')) move.add(right);
    if (this.keys.has('KeyA') || this.keys.has('ArrowLeft')) move.sub(right);
    if (move.lengthSq() === 0) return;

    move.normalize().multiplyScalar(
      (this.keys.has('ShiftLeft') || this.keys.has('ShiftRight') ? SPRINT : SPEED) * dt
    );

    const p = this.camera.position;
    p.x += move.x;
    p.z += move.z;
    this.resolveCollisions(p);
    p.y = EYE;
  }

  resolveCollisions(p) {
    for (let pass = 0; pass < 2; pass++) {
      for (const box of this.colliders) {
        // Closest point on the box footprint to the player circle.
        const cx = Math.max(box.min.x, Math.min(p.x, box.max.x));
        const cz = Math.max(box.min.z, Math.min(p.z, box.max.z));
        const dx = p.x - cx, dz = p.z - cz;
        const d2 = dx * dx + dz * dz;
        if (d2 >= RADIUS * RADIUS) continue;
        if (d2 < 1e-9) {
          // Player center inside the box: push out along the smallest overlap.
          const pushX = Math.min(p.x - box.min.x + RADIUS, box.max.x - p.x + RADIUS);
          const pushZ = Math.min(p.z - box.min.z + RADIUS, box.max.z - p.z + RADIUS);
          if (pushX < pushZ) {
            p.x = (p.x - box.min.x < box.max.x - p.x) ? box.min.x - RADIUS : box.max.x + RADIUS;
          } else {
            p.z = (p.z - box.min.z < box.max.z - p.z) ? box.min.z - RADIUS : box.max.z + RADIUS;
          }
          continue;
        }
        const d = Math.sqrt(d2);
        const push = (RADIUS - d) / d;
        p.x += dx * push;
        p.z += dz * push;
      }
    }
  }
}
