// All 2D UI: start screen, interaction prompt, focus panel (with lazy-loaded
// Mermaid rendering), the palace map (M), the knowledge constellation (G)
// and Floo travel (F). Pure DOM + canvas; styled in index.html.

let mermaidPromise = null;
function loadMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs')
      .then((m) => {
        m.default.initialize({ startOnLoad: false, theme: 'dark', darkMode: true });
        return m.default;
      })
      .catch(() => null);
  }
  return mermaidPromise;
}

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
    this._graphNodes = null;
    this.$('graph-canvas').addEventListener('click', (e) => this._graphClick(e));
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
    el.textContent = record.kind === 'portal'
      ? `E — step through to “${record.focus.title}”`
      : `E — study “${record.focus.title}”`;
  }

  // --- panels --------------------------------------------------------------
  closeAll() {
    for (const id of ['focus-panel', 'map-panel', 'graph-panel', 'floo-panel']) {
      this.$(id).style.display = 'none';
    }
    this.openPanel = null;
  }

  toggle(name) {
    const open = this.openPanel === name;
    this.closeAll();
    if (!open) {
      this.$(`${name}-panel`).style.display = 'block';
      this.openPanel = name;
      if (name === 'map') this.drawMap();
      if (name === 'graph') this.drawGraph();
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

    const rects = this.layout.spaces.map((s) => s.rect);
    const minX = Math.min(...rects.map((r) => r.minX)) - 4;
    const maxX = Math.max(...rects.map((r) => r.maxX)) + 4;
    const minZ = Math.min(...rects.map((r) => r.minZ)) - 4;
    const maxZ = Math.max(...rects.map((r) => r.maxZ)) + 4;
    const k = Math.min(W / (maxX - minX), H / (maxZ - minZ));
    const ox = (W - (maxX - minX) * k) / 2;
    const oz = (H - (maxZ - minZ) * k) / 2;
    const px = (x) => ox + (x - minX) * k;
    const pz = (z) => oz + (z - minZ) * k;

    for (const s of this.layout.spaces) {
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

  // --- constellation -------------------------------------------------------
  drawGraph() {
    const canvas = this.$('graph-canvas');
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const rooms = [...new Set(this.graph.concepts.map((c) => c.room))];
    const roomPos = new Map();
    const cx = W / 2, cy = H / 2, R = Math.min(W, H) * 0.33;
    rooms.forEach((rid, i) => {
      const a = (i / Math.max(rooms.length, 1)) * Math.PI * 2 - Math.PI / 2;
      roomPos.set(rid, { x: cx + Math.cos(a) * R, y: cy + Math.sin(a) * R });
    });

    const nodes = new Map();
    const byRoom = new Map();
    for (const c of this.graph.concepts) {
      if (!byRoom.has(c.room)) byRoom.set(c.room, []);
      byRoom.get(c.room).push(c);
    }
    for (const [rid, list] of byRoom) {
      const base = roomPos.get(rid);
      list.forEach((c, i) => {
        const a = (i / list.length) * Math.PI * 2;
        const r = list.length === 1 ? 0 : 52;
        nodes.set(c.id, {
          x: base.x + Math.cos(a) * r, y: base.y + Math.sin(a) * r, concept: c,
        });
      });
    }

    const REL_COLOR = {
      'builds-on': 'rgba(255,196,107,0.7)',
      'part-of': 'rgba(159,232,185,0.6)',
      'relates-to': 'rgba(154,196,255,0.55)',
      'contrasts-with': 'rgba(255,154,122,0.7)',
    };
    for (const e of this.graph.edges) {
      const A = nodes.get(e.from), B = nodes.get(e.to);
      if (!A || !B) continue;
      ctx.strokeStyle = REL_COLOR[e.relation] || 'rgba(255,255,255,0.4)';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(A.x, A.y);
      ctx.lineTo(B.x, B.y);
      ctx.stroke();
    }
    for (const [, n] of nodes) {
      ctx.fillStyle = 'rgba(154,196,255,0.25)';
      ctx.beginPath(); ctx.arc(n.x, n.y, 14, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#cfe4ff';
      ctx.beginPath(); ctx.arc(n.x, n.y, 6, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#e9dfc6';
      ctx.font = '13px Georgia, serif';
      ctx.textAlign = 'center';
      ctx.fillText(n.concept.name, n.x, n.y - 18);
    }
    ctx.fillStyle = 'rgba(233,223,198,0.55)';
    ctx.font = 'italic 13px Georgia, serif';
    ctx.textAlign = 'center';
    ctx.fillText('click a star to travel to its chamber', cx, H - 16);
    this._graphNodes = nodes;
  }

  _graphClick(e) {
    if (!this._graphNodes) return;
    const rect = e.target.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (e.target.width / rect.width);
    const y = (e.clientY - rect.top) * (e.target.height / rect.height);
    for (const [, n] of this._graphNodes) {
      if ((n.x - x) ** 2 + (n.y - y) ** 2 < 18 ** 2) {
        this.closeAll();
        this.onTeleport(n.concept.room);
        return;
      }
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
