// Boot: load world data -> solve layout -> build geometry & exhibits ->
// player + HUD -> run. Also exposes window.__palace for debugging and
// headless screenshot tooling.

import * as THREE from 'three';
import { solveLayout, spaceAt } from './layout.js';
import { LevelManager } from './levels.js';
import { Wisp } from './wisp.js';
import { Footsteps } from './footsteps.js';
import { DiagramPanel } from './diagrampanel.js';
import { palette } from './palettes.js';
import { Player, EYE } from './player.js';
import { Hud } from './hud.js';
import { Companion } from './companion.js';
import { CompanionChat } from './chat.js';
import { Constellation } from './constellation.js';
import { installDebugApi } from './debug.js';

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function loadWorldData() {
  const [world, index, graph] = await Promise.all([
    fetchJson('world/world.json'),
    fetchJson('world/rooms/index.json'),
    fetchJson('world/graph.json'),
  ]);
  const rooms = await Promise.all(index.rooms.map((f) => fetchJson(`world/rooms/${f}`)));
  const roomsById = Object.fromEntries(rooms.map((r) => [r.id, r]));
  return { world, graph, roomsById };
}

// A compact, data-derived overview of the whole palace for the companion: each
// wing, its chambers in walking order, and the concepts each chamber holds.
// Lets Gemma answer "what's next?" and cross-room questions, not just local ones.
function buildPalaceGist(world, roomsById, graph) {
  const byRoom = {};
  for (const c of graph.concepts) (byRoom[c.room] ||= []).push(c.name);
  const lines = [`"${world.title}" — the chambers, by wing:`];
  for (const wing of world.wings) {
    lines.push(`${wing.name}:`);
    Object.values(roomsById)
      .filter((r) => r.wing === wing.id)
      .sort((a, b) => a.order - b.order)
      .forEach((r) => {
        const cs = (byRoom[r.id] || []).slice(0, 5).join(', ');
        lines.push(`  ${r.order}. ${r.name}${cs ? ' — ' + cs : ''}`);
      });
  }
  const hub = roomsById[world.hub];
  if (hub) lines.push(`Hub: ${hub.name} (where the wings meet).`);
  return lines.join('\n');
}

async function boot() {
  const params = new URLSearchParams(location.search);
  const debug = params.has('debug');

  const { world, graph, roomsById } = await loadWorldData();
  const layout = solveLayout(world, roomsById);
  const palaceGist = buildPalaceGist(world, roomsById, graph);
  const conceptsById = Object.fromEntries(graph.concepts.map((c) => [c.id, c]));

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  document.getElementById('app').appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 500);

  // Floors build lazily: only the spawn level exists now; stairs/floo/teleport
  // build others on first visit. These three are LIVE references — the manager
  // swaps their contents when the keeper changes floors.
  const levels = new LevelManager(scene, layout, roomsById, graph);
  levels.activateFor(world.hub);
  const { colliders, interactables, updates, dome } = levels;
  const wisp = new Wisp(scene, layout, roomsById);
  // Marauder's footsteps: lead through a room's exhibits in study order, then
  // out to the next chamber in learning order. Reads the active floor's tours.
  const footsteps = new Footsteps(scene, layout, roomsById, (rid) => levels.tours.get(rid));
  const diagramPanel = new DiagramPanel(scene);

  // Read-only card shown alongside the floating diagram (pointer stays locked).
  const studyCard = document.getElementById('study-card');
  const showStudyCard = (focus) => {
    document.getElementById('study-title').textContent = focus.title;
    document.getElementById('study-subtitle').textContent = focus.subtitle || '';
    const body = document.getElementById('study-body');
    body.textContent = focus.body || '';
    body.scrollTop = 0;
    studyCard.style.display = 'block';
  };
  const hideStudyCard = () => { studyCard.style.display = 'none'; };
  const closeDiagramStage = () => { diagramPanel.hide(); hideStudyCard(); };
  // The stage counts as open if EITHER piece is up: if a diagram fails to
  // render (bad spec, offline CDN) the card must still be closable on its own.
  const stageOpen = () => diagramPanel.isOpen || studyCard.style.display === 'block';

  const player = new Player(camera, renderer.domElement, colliders);
  player.place(layout.spawn.x, layout.spawn.z, layout.spawn.yaw);

  const teleport = (roomId) => {
    const space = layout.spaceById[roomId];
    if (!space) return;
    levels.activateFor(roomId); // build the destination floor if needed
    // Land between the south wall and the center artifact, facing it.
    const r = space.rect;
    const back = Math.min(r.d / 2 - 1.4, Math.max(3.4, r.d * 0.32));
    player.place(r.cx, r.cz + back, 0);
    flash();
  };

  const hud = new Hud({ layout, world, graph, roomsById, onTeleport: teleport });

  // The 3D Constellation of Ideas (G): floors as star-layers, click to travel.
  const constellation = new Constellation({
    dom: renderer.domElement, layout, world, graph, roomsById,
    onTravel: (roomId) => {
      constellation.close();
      teleport(roomId);
      player.controls.lock();
    },
  });

  // --- Gemma: the companion ghost + her chat ------------------------------
  const companion = new Companion(scene);
  const getLocation = () => {
    const space = spaceAt(layout, camera.position.x, camera.position.z);
    if (!space) return null;
    const wing = world.wings.find((w) => w.id === space.wing);
    const roomId = space.kind === 'room' && space.room ? space.room.id : null;
    return {
      palace: palaceGist,
      room: space.kind === 'room' && space.room ? space.room.name : 'a passage',
      wing: wing ? wing.name : null,
      exhibit: target ? { title: target.focus.title, text: target.focus.body } : null,
      concepts: roomId
        ? graph.concepts.filter((c) => c.room === roomId)
            .map((c) => ({ name: c.name, summary: c.summary }))
        : [],
    };
  };
  const chat = new CompanionChat({
    getLocation,
    onThinking: (v) => companion.setThinking(v),
  });

  // --- start overlay / pointer lock ---------------------------------------
  const startEl = document.getElementById('start');
  const beginBtn = document.getElementById('begin');
  beginBtn.addEventListener('click', () => player.controls.lock());
  player.controls.addEventListener('lock', () => {
    startEl.style.display = 'none';
    player.enabled = true;
    hud.closeAll();
  });
  player.controls.addEventListener('unlock', () => {
    player.enabled = false;
    // Keep overlay hidden while any panel, the chat, or a floating diagram is open.
    if (!hud.openPanel && !chat.isOpen && !diagramPanel.isOpen && !constellation.isOpen) {
      startEl.style.display = 'flex';
    }
  });
  // Clicking the world re-locks the pointer after closing a panel/chat.
  renderer.domElement.addEventListener('click', () => {
    if (!hud.openPanel && !chat.isOpen && !constellation.isOpen && !player.controls.isLocked) {
      player.controls.lock();
    }
  });
  if (debug) {
    startEl.style.display = 'none';
    player.enabled = true;
  }

  // --- interaction targeting ----------------------------------------------
  const raycaster = new THREE.Raycaster();
  raycaster.far = 4.2;
  let target = null;

  function findTarget() {
    raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
    const hits = raycaster.intersectObjects([...interactables.keys()], true);
    for (const h of hits) {
      let o = h.object;
      while (o) {
        if (interactables.has(o)) return interactables.get(o);
        o = o.parent;
      }
    }
    return null;
  }

  document.addEventListener('keydown', (e) => {
    if (e.code === 'KeyE') {
      if (stageOpen()) { closeDiagramStage(); return; }
      if (hud.openPanel === 'focus') { hud.closeAll(); player.controls.lock(); return; }
      if (target) {
        if (target.kind === 'portal') {
          teleport(target.targetRoom);
        } else if (target.kind === 'sign') {
          teleport(target.destRoom);
        } else if (target.kind === 'stair' || target.kind === 'archway') {
          teleport(target.targetRoom);
        } else if (target.focus.mermaid || target.focus.image) {
          // Diagram or image exhibit: float a big panel in the room, keeping the
          // player in control so they can step back and walk around it.
          const sp = spaceAt(layout, camera.position.x, camera.position.z);
          const opts = { camera, rect: sp ? sp.rect : null,
                         pal: palette(sp ? sp.paletteName : 'parchment') };
          if (target.focus.mermaid) diagramPanel.show(target.focus.mermaid, opts);
          else diagramPanel.showImage(target.focus.image, opts);
          showStudyCard(target.focus);
        } else {
          hud.showFocus(target);
          player.controls.unlock();
        }
      }
    } else if (e.code === 'KeyT') {
      if (stageOpen()) closeDiagramStage();
      if (chat.toggle()) player.controls.unlock(); else player.controls.lock();
    } else if (e.code === 'KeyM') {
      if (stageOpen()) closeDiagramStage();
      const pl = { x: camera.position.x, z: camera.position.z, yaw: camera.rotation.y };
      if (hud.toggle('map', pl)) player.controls.unlock(); else player.controls.lock();
    } else if (e.code === 'KeyG') {
      if (stageOpen()) closeDiagramStage();
      hud.closeAll();
      const sp = spaceAt(layout, camera.position.x, camera.position.z);
      const here = sp && sp.kind === 'room' && sp.room ? sp.room.id : null;
      if (constellation.toggle(here)) player.controls.unlock();
      else player.controls.lock();
    } else if (e.code === 'KeyF' && !hud.openPanel) {
      if (stageOpen()) closeDiagramStage();
      hud.toggle('floo');
      player.controls.unlock();
    } else if (e.code === 'KeyP') {
      // Toggle the Marauder's footsteps on/off (persisted).
      footToast(footsteps.toggle());
    } else if (e.code === 'Escape') {
      if (hud.diagramMaxed) hud.closeDiagramMax();
      else if (constellation.isOpen) constellation.close();
      else if (stageOpen()) closeDiagramStage();
      else if (chat.isOpen) chat.close();
      else if (hud.openPanel) hud.closeAll();
    }
  });

  // Scroll the read-only study card with the wheel while the pointer is locked.
  addEventListener('wheel', (e) => {
    if (diagramPanel.isOpen) document.getElementById('study-body').scrollTop += e.deltaY;
  }, { passive: true });

  // Teleport flash.
  const flashEl = document.getElementById('flash');
  function flash() {
    flashEl.style.opacity = '0.85';
    setTimeout(() => { flashEl.style.opacity = '0'; }, 60);
  }

  // Transient confirmation when the footsteps guide is toggled.
  const footToastEl = document.getElementById('foot-toast');
  let footToastTimer = null;
  function footToast(on) {
    footToastEl.textContent = on
      ? '✦ Marauder’s footsteps: guiding'
      : '✦ Marauder’s footsteps: off';
    footToastEl.style.opacity = '1';
    clearTimeout(footToastTimer);
    footToastTimer = setTimeout(() => { footToastEl.style.opacity = '0'; }, 1500);
  }

  // --- debug / screenshot API (window.__palace) -----------------------------
  const debugApi = installDebugApi({
    scene, camera, player, layout, roomsById, interactables, levels,
    wisp, footsteps, diagramPanel, teleport, palette, showStudyCard, companion,
  });

  // --- main loop ------------------------------------------------------------
  const clock = new THREE.Clock();
  let acc = 0;
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    // While the constellation is open, the astral view replaces the palace.
    if (constellation.isOpen) {
      constellation.update(dt, t);
      renderer.render(constellation.scene, constellation.camera);
      debugApi.ready = true;
      return;
    }

    player.update(dt);
    dome.position.set(camera.position.x, 0, camera.position.z);
    companion.update(dt, camera, t);
    wisp.update(dt, camera, t);
    footsteps.update(dt, camera, t);
    diagramPanel.update(dt, t);
    for (const fn of updates) fn(t);

    // Throttled UI updates.
    acc += dt;
    if (acc > 0.15) {
      acc = 0;
      const space = spaceAt(layout, camera.position.x, camera.position.z);
      hud.setLocation(space);
      const hereRoom = space && space.kind === 'room' && space.room ? space.room.id : null;
      wisp.setRoom(hereRoom);
      footsteps.setRoom(hereRoom);
      target = findTarget();
      // A gated passage summons the Gatekeeper: resolve its prerequisite
      // concepts and hand them to the chat so pressing T opens a quiz.
      const gate = target && (target.kind === 'stair' || target.kind === 'archway') && target.gate
        ? target.gate : null;
      chat.setGate(gate ? {
        dest: target.focus.title,
        persona: gate.persona || '',
        prereqs: (gate.prereqs || []).map((id) => conceptsById[id]).filter(Boolean)
          .map((c) => ({ name: c.name, summary: c.summary })),
      } : null);
      hud.setPrompt(hud.openPanel || diagramPanel.isOpen ? null : target);
      if (hud.openPanel === 'map') {
        hud.drawMap({ x: camera.position.x, z: camera.position.z, yaw: camera.rotation.y });
      }
    }

    renderer.render(scene, camera);
    debugApi.ready = true;
  });

  addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    constellation.camera.aspect = innerWidth / innerHeight;
    constellation.camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });
}

boot().catch((err) => {
  document.getElementById('start').innerHTML =
    `<div class="card"><h1>The palace failed to materialize</h1><p>${err.message}</p>
     <p class="muted">Did you run <code>python world.py validate</code>?</p></div>`;
  console.error(err);
});
