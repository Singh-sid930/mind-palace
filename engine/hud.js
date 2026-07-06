// All 2D UI: start screen, interaction prompt, focus panel (with lazy-loaded
// Mermaid rendering), the palace map (M) and Floo travel (F). Pure DOM +
// canvas; styled in index.html. (The constellation is 3D — constellation.js.)

import { loadMermaid } from './mermaid.js';
import { spaceAt } from './layout.js';

export class Hud {
  constructor({ layout, world, graph, roomsById, onTeleport }) {
    this.layout = layout;
    this.world = world;
    this.graph = graph;
    this.roomsById = roomsById;
    this.onTeleport = onTeleport;
    this.openPanel = null; // 'focus' | 'map' | 'graph' | 'floo' | null
    this.$ = (id) => document.getElementById(id);
    this.$('hud-title').textContent = world.title;
    this._wireFloo();
    this.$('dia-max').addEventListener('click', () => this.closeDiagramMax());
  }

  // --- diagram maximize ------------------------------------------------------
  get diagramMaxed() { return this.$('dia-max').style.display === 'flex'; }

  maximizeDiagram() {
    const svg = this.$('focus-diagram').querySelector('svg');
    if (!svg) return;
    const big = svg.cloneNode(true);
    big.style.maxWidth = '92vw';
    big.style.maxHeight = '88vh';
    big.style.width = '92vw';
    big.style.height = 'auto';
    const holder = this.$('dia-max-holder');
    holder.innerHTML = '';
    holder.appendChild(big);
    this.$('dia-max').style.display = 'flex';
  }

  closeDiagramMax() {
    this.$('dia-max').style.display = 'none';
  }

  // --- status line ---------------------------------------------------------
  setLocation(space) {
    const el = this.$('hud-room');
    if (!space) { el.textContent = ''; return; }
    const wing = this.world.wings.find((w) => w.id === space.wing);
    el.textContent = space.kind === 'corridor'
      ? `${wing ? wing.name : ''} — passage`
      : `${space.room ? space.room.name : space.id}${wing ? ' · ' + wing.name : ''}`;
  }

  setPrompt(record) {
    const el = this.$('hud-prompt');
    if (!record) { el.style.display = 'none'; return; }
    el.style.display = 'block';
    if (record.kind === 'portal') {
      el.textContent = `E — step through to “${record.focus.title}”`;
    } else if (record.kind === 'stair') {
      const verb = record.dir === 'down' ? 'descend to' : record.dir === 'up' ? 'ascend to' : 'take the staircase to';
      el.textContent = `E — ${verb} “${record.focus.title}”`
        + (record.gate ? '   ·   T — the Gatekeeper will test you' : '');
    } else if (record.kind === 'archway') {
      el.textContent = `E — step through to “${record.focus.title}”`
        + (record.gate ? '   ·   T — the Gatekeeper will test you' : '');
    } else if (record.kind === 'sign') {
      el.textContent = `E — ${record.prompt}`;
    } else {
      el.textContent = `E — study “${record.focus.title}”`;
    }
  }

  // --- panels --------------------------------------------------------------
  closeAll() {
    for (const id of ['focus-panel', 'map-panel', 'floo-panel']) {
      this.$(id).style.display = 'none';
    }
    this.openPanel = null;
  }

  toggle(name, player) {
    const open = this.openPanel === name;
    this.closeAll();
    if (!open) {
      this.$(`${name}-panel`).style.display = 'block';
      this.openPanel = name;
      if (name === 'map') this.drawMap(player);
      if (name === 'floo') {
        const input = this.$('floo-input');
        input.value = '';
        this._flooFilter('');
        setTimeout(() => input.focus(), 0);
      }
    }
    return this.openPanel !== null;
  }

  showFocus(record) {
    this.closeAll();
    this.openPanel = 'focus';
    const p = this.$('focus-panel');
    p.style.display = 'block';
    this.$('focus-title').textContent = record.focus.title;
    this.$('focus-subtitle').textContent = record.focus.subtitle || '';
    this.$('focus-body').textContent = record.focus.body || '';
    const dia = this.$('focus-diagram');
    dia.innerHTML = '';
    dia.style.display = 'none';
    if (record.focus.mermaid) {
      dia.style.display = 'block';
      dia.innerHTML = '<em class="muted">unfolding diagram…</em>';
      loadMermaid().then(async (mermaid) => {
        if (this.openPanel !== 'focus') return;
        if (!mermaid) {
          dia.innerHTML = `<pre>${record.focus.mermaid.replace(/</g, '&lt;')}</pre>`;
          return;
        }
        try {
          const { svg } = await mermaid.render('dia-' + Date.now(), record.focus.mermaid);
          dia.innerHTML = `<button class="dia-zoom" title="maximize">⛶</button>` + svg;
          // Click anywhere on the diagram (or the button) to maximize.
          dia.querySelector('.dia-zoom').addEventListener('click', () => this.maximizeDiagram());
          dia.querySelector('svg').addEventListener('click', () => this.maximizeDiagram());
          dia.querySelector('svg').style.cursor = 'zoom-in';
        } catch {
          dia.innerHTML = `<pre>${record.focus.mermaid.replace(/</g, '&lt;')}</pre>`;
        }
      });
    }
  }

  // --- map -----------------------------------------------------------------
  drawMap(player) {
    const canvas = this.$('map-canvas');
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Show only the floor the player is standing on.
    const here = player ? spaceAt(this.layout, player.x, player.z) : null;
    const level = here ? here.level : (this.layout.spaces[0] && this.layout.spaces[0].level);
    const levelSpaces = this.layout.spaces.filter((s) => s.level === level);
    if (!levelSpaces.length) return;
    const onLevel = new Set(levelSpaces.map((s) => s.id));
    const heading = this.$('map-panel').querySelector('h2');
    if (heading) {
      const lv = (this.world.levels || []).find((l) => l.id === level);
      heading.textContent = lv ? lv.name : 'The Palace';
    }

    const rects = levelSpaces.map((s) => s.rect);
    const minX = Math.min(...rects.map((r) => r.minX)) - 4;
    const maxX = Math.max(...rects.map((r) => r.maxX)) + 4;
    const minZ = Math.min(...rects.map((r) => r.minZ)) - 4;
    const maxZ = Math.max(...rects.map((r) => r.maxZ)) + 4;
    const k = Math.min(W / (maxX - minX), H / (maxZ - minZ));
    const ox = (W - (maxX - minX) * k) / 2;
    const oz = (H - (maxZ - minZ) * k) / 2;
    const px = (x) => ox + (x - minX) * k;
    const pz = (z) => oz + (z - minZ) * k;

    for (const s of levelSpaces) {
      const r = s.rect;
      ctx.fillStyle = s.kind === 'room' ? 'rgba(233,223,198,0.16)' : 'rgba(233,223,198,0.07)';
      ctx.strokeStyle = 'rgba(212,175,55,0.55)';
      ctx.lineWidth = s.kind === 'room' ? 2 : 1;
      ctx.fillRect(px(r.minX), pz(r.minZ), r.w * k, r.d * k);
      ctx.strokeRect(px(r.minX), pz(r.minZ), r.w * k, r.d * k);
      if (s.kind === 'room' && s.room) {
        ctx.fillStyle = '#e9dfc6';
        ctx.font = `${Math.max(10, 13 * (k / 8))}px Georgia, serif`;
        ctx.textAlign = 'center';
        ctx.fillText(s.room.name, px(r.cx), pz(r.cz) - 4, r.w * k - 8);
      }
    }
    // Portals as dashed arcs.
    ctx.strokeStyle = 'rgba(159,232,185,0.6)';
    ctx.setLineDash([5, 5]);
    for (const p of this.layout.portals) {
      if (!onLevel.has(p.a) || !onLevel.has(p.b)) continue;
      const A = this.layout.spaceById[p.a].rect, B = this.layout.spaceById[p.b].rect;
      ctx.beginPath();
      ctx.moveTo(px(A.cx), pz(A.cz));
      ctx.quadraticCurveTo(
        (px(A.cx) + px(B.cx)) / 2 + 24, (pz(A.cz) + pz(B.cz)) / 2 - 24,
        px(B.cx), pz(B.cz)
      );
      ctx.stroke();
    }
    ctx.setLineDash([]);

    if (player) {
      ctx.fillStyle = '#ffd98a';
      ctx.beginPath();
      ctx.arc(px(player.x), pz(player.z), 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#ffd98a';
      ctx.beginPath();
      ctx.moveTo(px(player.x), pz(player.z));
      ctx.lineTo(px(player.x + Math.sin(player.yaw + Math.PI) * 2.4),
                 pz(player.z + Math.cos(player.yaw + Math.PI) * 2.4));
      ctx.stroke();
    }
  }

  // --- floo travel ---------------------------------------------------------
  _wireFloo() {
    const input = this.$('floo-input');
    input.addEventListener('input', () => this._flooFilter(input.value));
    input.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') {
        const first = this.$('floo-list').querySelector('li');
        if (first) first.click();
      }
      if (e.key === 'Escape') this.closeAll();
    });
  }

  _flooFilter(q) {
    const list = this.$('floo-list');
    list.innerHTML = '';
    const needle = q.trim().toLowerCase();
    const rooms = Object.values(this.roomsById)
      .filter((r) => !needle || r.name.toLowerCase().includes(needle) ||
                     r.id.includes(needle));
    for (const r of rooms.slice(0, 12)) {
      const li = document.createElement('li');
      li.textContent = r.name;
      li.addEventListener('click', () => {
        this.closeAll();
        this.onTeleport(r.id);
      });
      list.appendChild(li);
    }
  }
}
