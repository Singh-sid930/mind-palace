// A large diagram panel that materializes in world space when you study an
// exhibit's visual. Unlike the flat focus overlay, this hangs in the actual 3D
// room — you keep walking and can step back or around it. The Mermaid diagram
// is rasterized to a texture (see mermaid.js) and shown on a framed plane,
// placed in front of you, clamped inside the room, facing you.

import * as THREE from 'three';
import { renderDiagramTexture } from './mermaid.js';

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const MAX_W = 4.6;   // metres
const MAX_H = 2.9;

export class DiagramPanel {
  constructor(scene) {
    this.scene = scene;
    this.group = null;
    this.token = 0; // guards against races when show() is called rapidly
  }

  get isOpen() { return !!this.group; }

  // spec: Mermaid source. opts: { camera, rect (room bounds), pal (palette) }.
  async show(spec, opts) {
    this.hide();                 // hide() bumps the token, cancelling any in-flight show
    const my = ++this.token;
    const res = await renderDiagramTexture(spec);
    if (!res || my !== this.token) { if (res) res.texture.dispose(); return false; }
    this._spawn(res.texture, res.w, res.h, opts);
    return true;
  }

  // Float an image (by URL) large in world space, same framing as a diagram.
  showImage(url, opts) {
    this.hide();
    const my = ++this.token;
    new THREE.TextureLoader().load(url, (texture) => {
      if (my !== this.token) { texture.dispose(); return; }
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = 8;
      this._spawn(texture, texture.image.width || 1, texture.image.height || 1, opts);
    });
    return true;
  }

  _spawn(texture, w, h, { camera, rect, pal }) {
    // Fit within max bounds, preserving aspect.
    let worldW = MAX_W, worldH = MAX_W * h / w;
    if (worldH > MAX_H) { worldH = MAX_H; worldW = MAX_H * w / h; }

    const group = new THREE.Group();
    const frame = new THREE.Mesh(
      new THREE.BoxGeometry(worldW + 0.2, worldH + 0.2, 0.08),
      new THREE.MeshLambertMaterial({ color: pal.accent, emissive: pal.glow, emissiveIntensity: 0.22 })
    );
    const face = new THREE.Mesh(
      new THREE.PlaneGeometry(worldW, worldH),
      new THREE.MeshBasicMaterial({ map: texture, transparent: true })
    );
    face.position.z = 0.06;
    const light = new THREE.PointLight(pal.glow, 1.1, 7, 1.8);
    light.position.set(0, 0, 1.4);
    group.add(frame, face, light);

    // Place in front of the camera, clamped into the room, facing the player.
    const fwd = new THREE.Vector3();
    camera.getWorldDirection(fwd); fwd.y = 0;
    if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, -1);
    fwd.normalize();
    let px = camera.position.x + fwd.x * 3.4;
    let pz = camera.position.z + fwd.z * 3.4;
    if (rect) {
      px = clamp(px, rect.minX + 1.0, rect.maxX - 1.0);
      pz = clamp(pz, rect.minZ + 1.0, rect.maxZ - 1.0);
    }
    const baseY = Math.max(worldH / 2 + 0.3, 1.7);
    group.position.set(px, baseY, pz);
    group.rotation.y = Math.atan2(camera.position.x - px, camera.position.z - pz);
    group.scale.setScalar(0.7); // grows in via update()

    group.userData = { baseY, frame };
    this.group = group;
    this.scene.add(group);
  }

  hide() {
    this.token++;
    if (!this.group) return;
    const g = this.group;
    this.group = null;
    this.scene.remove(g);
    g.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (o.material.map) o.material.map.dispose();
        o.material.dispose();
      }
    });
  }

  update(dt, t) {
    if (!this.group) return;
    const u = this.group.userData;
    const s = this.group.scale.x + (1 - this.group.scale.x) * Math.min(1, dt * 7);
    this.group.scale.setScalar(s);
    this.group.position.y = u.baseY + Math.sin(t * 1.4) * 0.04;
    u.frame.material.emissiveIntensity = 0.18 + 0.08 * Math.sin(t * 2.5);
  }
}
