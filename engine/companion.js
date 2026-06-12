// Gemma, the Whispering Sage — a ghost who drifts at the keeper's shoulder.
// Procedural like everything else: translucent robes, ember eyes, soft glow.
// Being a ghost, she ignores walls (smoothed follow, no collision) — by design.

import * as THREE from 'three';

const GHOST = 0xbfd8e8;

function nameSprite() {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 128;
  const ctx = c.getContext('2d');
  ctx.font = 'italic bold 52px Georgia, serif';
  ctx.textAlign = 'center';
  ctx.shadowColor = 'rgba(0,0,0,0.9)';
  ctx.shadowBlur = 12;
  ctx.fillStyle = 'rgba(207,228,255,0.95)';
  ctx.fillText('Gemma', 256, 62);
  ctx.font = 'italic 30px Georgia, serif';
  ctx.fillStyle = 'rgba(207,228,255,0.6)';
  ctx.fillText('the Whispering Sage', 256, 104);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: tex, transparent: true, depthWrite: false,
  }));
  sprite.scale.set(1.7, 0.42, 1);
  return sprite;
}

export class Companion {
  constructor(scene) {
    const g = new THREE.Group();

    const robeMat = new THREE.MeshLambertMaterial({
      color: GHOST, transparent: true, opacity: 0.42,
      emissive: 0x4a6a8a, emissiveIntensity: 0.5, side: THREE.DoubleSide,
    });
    const robe = new THREE.Mesh(new THREE.ConeGeometry(0.32, 1.0, 12, 1, true), robeMat);
    robe.position.y = 0.5;

    const hood = new THREE.Mesh(new THREE.SphereGeometry(0.21, 12, 10), robeMat.clone());
    hood.material.opacity = 0.5;
    hood.position.y = 1.08;

    // Ember eyes.
    this.eyes = [];
    for (const dx of [-0.07, 0.07]) {
      const eye = new THREE.Mesh(
        new THREE.SphereGeometry(0.022, 6, 6),
        new THREE.MeshBasicMaterial({ color: 0xffe2aa })
      );
      eye.position.set(dx, 1.08, 0.17);
      this.eyes.push(eye);
      g.add(eye);
    }

    // Wispy tail under the robe.
    const tail = new THREE.Mesh(
      new THREE.ConeGeometry(0.16, 0.5, 10, 1, true),
      robeMat.clone()
    );
    tail.material.opacity = 0.22;
    tail.rotation.x = Math.PI;
    tail.position.y = -0.05;

    this.glow = new THREE.PointLight(0x9ac4ff, 0.9, 4, 1.8);
    this.glow.position.y = 0.9;

    const label = nameSprite();
    label.position.y = 1.6;

    g.add(robe, hood, tail, this.glow, label);
    g.position.set(1.2, 0.4, -1.2);
    scene.add(g);

    this.group = g;
    this.robeMats = [robeMat, hood.material, tail.material];
    this.thinking = false;
    this._target = new THREE.Vector3();
    this._look = new THREE.Vector3();
  }

  setThinking(on) {
    this.thinking = on;
  }

  update(dt, camera, t) {
    // Desired spot: ahead-right of the keeper, at hover height.
    const fwd = new THREE.Vector3();
    camera.getWorldDirection(fwd);
    fwd.y = 0;
    if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, -1);
    fwd.normalize();
    const right = new THREE.Vector3(-fwd.z, 0, fwd.x);

    this._target.copy(camera.position)
      .addScaledVector(right, 1.15)
      .addScaledVector(fwd, 1.05);
    this._target.y = 0.42 + Math.sin(t * 1.6) * 0.07;

    // Smooth lag-follow (ghosts don't hurry).
    const k = 1 - Math.exp(-2.6 * dt);
    this.group.position.lerp(this._target, k);

    // Face the keeper.
    this._look.copy(camera.position);
    this._look.y = this.group.position.y;
    this.group.lookAt(this._look);

    // Glow: calm shimmer normally, eager pulse while thinking.
    if (this.thinking) {
      this.glow.intensity = 1.6 + Math.sin(t * 9) * 0.8;
      for (const m of this.robeMats) m.emissiveIntensity = 0.8 + Math.sin(t * 9) * 0.3;
    } else {
      this.glow.intensity = 0.85 + Math.sin(t * 2.1) * 0.2;
      for (const m of this.robeMats) m.emissiveIntensity = 0.5;
    }
  }
}
