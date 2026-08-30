// The Constellation of Ideas, in 3D. Press G: the palace dissolves into an
// astral projection of itself, each floor a layer of stars at its true tier
// (foundations below, derived arts above), each room a glowing node at its
// real place in the layout, each concept a small star clustered round its
// room. Edges are the knowledge graph (colored by relation); golden and
// sapphire arcs are the actual passages. Drag to orbit, scroll to zoom,
// click any star to travel there.

import * as THREE from 'three';
import { palette } from './palettes.js';

const REL_COLOR = {
  'builds-on': 0xffc46b,
  'part-of': 0x9fe8b9,
  'relates-to': 0x9ac4ff,
  'contrasts-with': 0xff9a7a,
};
const TIER_H = 7;      // vertical metres per knowledge tier
const XZ_SCALE = 0.16; // shrink real room coordinates to constellation space

function textSprite(text, { px = 46, color = '#efe6cf', alpha = 1 } = {}) {
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  ctx.font = `bold ${px}px Georgia, serif`;
  const w = Math.ceil(ctx.measureText(text).width) + 24;
  c.width = w; c.height = px + 26;
  const ctx2 = c.getContext('2d');
  ctx2.font = `bold ${px}px Georgia, serif`;
  ctx2.textAlign = 'center';
  ctx2.textBaseline = 'middle';
  ctx2.shadowColor = 'rgba(0,0,0,0.95)';
  ctx2.shadowBlur = 10;
  ctx2.fillStyle = color;
  ctx2.fillText(text, w / 2, (px + 26) / 2);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: tex, transparent: true, opacity: alpha, depthWrite: false,
  }));
  const k = 0.011;
  sprite.scale.set(w * k, (px + 26) * k, 1);
  return sprite;
}

export class Constellation {
  constructor({ dom, layout, world, graph, roomsById, onTravel }) {
    this.dom = dom;
    this.layout = layout;
    this.world = world;
    this.graph = graph;
    this.roomsById = roomsById;
    this.onTravel = onTravel;
    this.isOpen = false;
    this.built = false;

    // Orbit state.
    this.theta = 0.6; this.phi = 0.9; this.dist = 34;
    this.camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 400);
    this._drag = null;
    this._moved = 0;
    this._ray = new THREE.Raycaster();
    this._pulse = null; // the "you are here" room node

    dom.addEventListener('mousedown', (e) => {
      if (!this.isOpen) return;
      this._drag = { x: e.clientX, y: e.clientY };
      this._moved = 0;
    });
    addEventListener('mousemove', (e) => {
      if (!this.isOpen || !this._drag) return;
      const dx = e.clientX - this._drag.x, dy = e.clientY - this._drag.y;
      this._drag = { x: e.clientX, y: e.clientY };
      this._moved += Math.abs(dx) + Math.abs(dy);
      this.theta -= dx * 0.005;
      this.phi = Math.min(1.45, Math.max(0.12, this.phi - dy * 0.004));
    });
    addEventListener('mouseup', (e) => {
      if (!this.isOpen || !this._drag) return;
      const wasClick = this._moved < 6;
      this._drag = null;
      if (wasClick) this._pick(e);
    });
    addEventListener('wheel', (e) => {
      if (!this.isOpen) return;
      this.dist = Math.min(90, Math.max(7, this.dist * (e.deltaY > 0 ? 1.1 : 0.9)));
    }, { passive: true });
  }

  _build() {
    this.built = true;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x05040a);
    scene.fog = null;
    this.scene = scene;

    const L = this.layout;
    // Each level stacks around the same axis, hub at center. Levels SHARING a
    // tier would overlap exactly (their wings radiate the same way), so each
    // same-tier level is fanned to its own compass bearing around the axis.
    const hubOf = {}, rotOf = {};
    const byTier = new Map();
    for (const lv of L.levels) {
      const hub = L.spaceById[lv.hub];
      hubOf[lv.id] = hub ? { x: hub.rect.cx, z: hub.rect.cz } : { x: 0, z: 0 };
      const tier = lv.tier || 0;
      if (!byTier.has(tier)) byTier.set(tier, []);
      byTier.get(tier).push(lv.id);
    }
    const sepOf = {};
    for (const [, ids] of byTier) {
      ids.forEach((id, i) => {
        rotOf[id] = (i / ids.length) * Math.PI * 2;
        // Levels sharing a tier also step away from the axis, so their HUBS
        // (which all sit at their level's local center) never overlap.
        sepOf[id] = ids.length > 1 ? 3.4 : 0;
      });
    }
    const place = (levelId, cx, cz) => {
      const h = hubOf[levelId], a = rotOf[levelId] || 0, r = sepOf[levelId] || 0;
      const dx = (cx - h.x) * XZ_SCALE, dz = (cz - h.z) * XZ_SCALE;
      return { x: dx * Math.cos(a) - dz * Math.sin(a) + r * Math.cos(a),
               z: dx * Math.sin(a) + dz * Math.cos(a) + r * Math.sin(a) };
    };
    const roomPos = new Map();
    this.roomNodes = [];
    this.conceptStars = [];
    this.clickables = [];

    for (const s of L.spaces) {
      if (s.kind !== 'room' || !s.room) continue;
      const lv = L.levelById[s.level] || { tier: 0 };
      const { x, z } = place(s.level, s.rect.cx, s.rect.cz);
      const p = new THREE.Vector3(x, (lv.tier || 0) * TIER_H, z);
      roomPos.set(s.id, p);
      const pal = palette(s.paletteName);
      const node = new THREE.Mesh(
        new THREE.SphereGeometry(0.34, 14, 14),
        new THREE.MeshBasicMaterial({ color: pal.glow, transparent: true, opacity: 0.95 })
      );
      node.position.copy(p);
      node.userData = { roomId: s.id, baseScale: 1 };
      const halo = new THREE.Mesh(
        new THREE.SphereGeometry(0.62, 12, 12),
        new THREE.MeshBasicMaterial({ color: pal.glow, transparent: true, opacity: 0.16,
                                      blending: THREE.AdditiveBlending, depthWrite: false })
      );
      halo.position.copy(p);
      const label = textSprite(s.room.name, { px: 40 });
      label.position.set(p.x, p.y + 0.85, p.z);
      scene.add(node, halo, label);
      this.roomNodes.push(node);
      this.clickables.push(node);
    }

    // Faint tier rings + floor names anchor the eye to each layer.
    for (const lv of L.levels) {
      const tierY = (lv.tier || 0) * TIER_H;
      let r = 2.5;
      for (const [id, p] of roomPos) {
        if (L.spaceById[id].level === lv.id) r = Math.max(r, Math.hypot(p.x, p.z) + 1.6);
      }
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(r, 0.015, 6, 96),
        new THREE.MeshBasicMaterial({ color: 0x9ac4ff, transparent: true, opacity: 0.14 })
      );
      ring.rotation.x = Math.PI / 2;
      ring.position.y = tierY;
      const name = textSprite(lv.name || lv.id, { px: 34, color: '#9bb0c6', alpha: 0.8 });
      name.position.set(r + 1.4, tierY, 0);
      scene.add(ring, name);
    }

    // Concept stars ring their room; labels appear as you zoom close.
    const starPos = new Map();
    const byRoom = new Map();
    for (const c of this.graph.concepts) {
      if (!byRoom.has(c.room)) byRoom.set(c.room, []);
      byRoom.get(c.room).push(c);
    }
    this.starLabels = [];
    for (const [rid, list] of byRoom) {
      const base = roomPos.get(rid);
      if (!base) continue;
      list.forEach((c, i) => {
        const a = (i / list.length) * Math.PI * 2;
        const rr = list.length === 1 ? 0.9 : 1.25;
        const p = new THREE.Vector3(base.x + Math.cos(a) * rr,
                                    base.y + 0.28 + ((i % 3) - 1) * 0.34,
                                    base.z + Math.sin(a) * rr);
        starPos.set(c.id, p);
        const star = new THREE.Mesh(
          new THREE.OctahedronGeometry(0.11),
          new THREE.MeshBasicMaterial({ color: 0xcfe4ff })
        );
        star.position.copy(p);
        star.userData = { roomId: c.room, concept: c };
        scene.add(star);
        this.conceptStars.push(star);
        this.clickables.push(star);
        const label = textSprite(c.name, { px: 30, color: '#cfe4ff', alpha: 0.9 });
        label.position.set(p.x, p.y + 0.34, p.z);
        label.material.opacity = 0;
        scene.add(label);
        this.starLabels.push({ label, p });
      });
    }

    // Knowledge edges, colored by relation. Cross-floor edges read as lineage.
    const verts = [], cols = [];
    const col = new THREE.Color();
    for (const e of this.graph.edges) {
      const A = starPos.get(e.from), B = starPos.get(e.to);
      if (!A || !B) continue;
      col.setHex(REL_COLOR[e.relation] || 0xffffff);
      verts.push(A.x, A.y, A.z, B.x, B.y, B.z);
      cols.push(col.r, col.g, col.b, col.r, col.g, col.b);
    }
    const eg = new THREE.BufferGeometry();
    eg.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
    eg.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
    scene.add(new THREE.LineSegments(eg, new THREE.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.38,
      blending: THREE.AdditiveBlending, depthWrite: false,
    })));

    // The palace's real passages: bright arcs between the rooms they join.
    for (const psg of this.world.passages || []) {
      const [a, b] = psg.between || [];
      const A = roomPos.get(a), B = roomPos.get(b);
      if (!A || !B) continue;
      const mid = A.clone().add(B).multiplyScalar(0.5);
      mid.y += psg.type === 'archway' ? 1.6 : 0.8;
      const curve = new THREE.QuadraticBezierCurve3(A, mid, B);
      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 24, 0.035, 6),
        new THREE.MeshBasicMaterial({
          color: psg.type === 'archway' ? 0xffcf6b : 0x6ea8ff,
          transparent: true, opacity: 0.6,
          blending: THREE.AdditiveBlending, depthWrite: false,
        })
      );
      scene.add(tube);
    }

    // A whisper of background stars.
    const N = 500, sp = new Float32Array(N * 3);
    let seed = 77;
    const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0xffffffff; };
    for (let i = 0; i < N; i++) {
      sp.set([(rand() - 0.5) * 220, (rand() - 0.5) * 160, (rand() - 0.5) * 220], i * 3);
    }
    const sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
    scene.add(new THREE.Points(sg, new THREE.PointsMaterial({
      color: 0xfff5dc, size: 0.25, transparent: true, opacity: 0.5, depthWrite: false,
    })));

    // Orbit target: the centroid of the tier stack.
    const tiers = L.levels.map((l) => (l.tier || 0) * TIER_H);
    this.center = new THREE.Vector3(0, (Math.min(...tiers) + Math.max(...tiers)) / 2, 0);
  }

  open(currentRoomId = null) {
    if (!this.built) this._build();
    this.isOpen = true;
    this._pulse = this.roomNodes.find((n) => n.userData.roomId === currentRoomId) || null;
    document.getElementById('constellation-hint').style.display = 'block';
  }

  close() {
    this.isOpen = false;
    if (this._pulse) this._pulse.scale.setScalar(1);
    document.getElementById('constellation-hint').style.display = 'none';
  }

  toggle(currentRoomId) {
    if (this.isOpen) this.close(); else this.open(currentRoomId);
    return this.isOpen;
  }

  _pick(e) {
    const nx = (e.clientX / innerWidth) * 2 - 1;
    const ny = -(e.clientY / innerHeight) * 2 + 1;
    this._ray.setFromCamera(new THREE.Vector2(nx, ny), this.camera);
    this._ray.params.Points = { threshold: 0.3 };
    const hits = this._ray.intersectObjects(this.clickables, false);
    if (hits.length) this.onTravel(hits[0].object.userData.roomId);
  }

  update(dt, t) {
    // Camera on its orbit.
    const sp = Math.sin(this.phi), y = Math.cos(this.phi);
    this.camera.position.set(
      this.center.x + this.dist * sp * Math.sin(this.theta),
      this.center.y + this.dist * y,
      this.center.z + this.dist * sp * Math.cos(this.theta)
    );
    this.camera.lookAt(this.center);
    // "You are here" pulse.
    if (this._pulse) this._pulse.scale.setScalar(1.15 + 0.35 * Math.sin(t * 4));
    // Concept labels fade in as you approach their star.
    for (const { label, p } of this.starLabels) {
      const d = this.camera.position.distanceTo(p);
      const target = d < 14 ? Math.min(0.95, (14 - d) / 6) : 0;
      label.material.opacity += (target - label.material.opacity) * Math.min(1, dt * 8);
    }
  }
}
