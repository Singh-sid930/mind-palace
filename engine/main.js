// Boot: load world data -> solve layout -> build geometry & exhibits ->
// player + HUD -> run. Also exposes window.__palace for debugging and
// headless screenshot tooling.

import * as THREE from 'three';
import { solveLayout, spaceAt } from './layout.js';
import { buildWorld } from './builder.js';
import { buildExhibits } from './exhibits.js';
import { Player, EYE } from './player.js';
import { Hud } from './hud.js';

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

async function boot() {
  const params = new URLSearchParams(location.search);
  const debug = params.has('debug');

  const { world, graph, roomsById } = await loadWorldData();
  const layout = solveLayout(world, roomsById);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  document.getElementById('app').appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 500);

  const { colliders } = buildWorld(scene, layout);
  const { interactables, updates } = buildExhibits(scene, layout, roomsById);

  const player = new Player(camera, renderer.domElement, colliders);
  player.place(layout.spawn.x, layout.spawn.z, layout.spawn.yaw);

  const teleport = (roomId) => {
    const space = layout.spaceById[roomId];
    if (!space) return;
    // Land between the south wall and the center artifact, facing it.
    const r = space.rect;
    const back = Math.min(r.d / 2 - 1.4, Math.max(3.4, r.d * 0.32));
    player.place(r.cx, r.cz + back, 0);
    flash();
  };

  const hud = new Hud({ layout, world, graph, roomsById, onTeleport: teleport });

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
    // Keep overlay hidden if a HUD panel is open; otherwise show start screen.
    if (!hud.openPanel) startEl.style.display = 'flex';
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
      if (hud.openPanel === 'focus') { hud.closeAll(); player.controls.lock(); return; }
      if (target) {
        if (target.kind === 'portal') teleport(target.targetRoom);
        else {
          hud.showFocus(target);
          player.controls.unlock();
        }
      }
    } else if (e.code === 'KeyM') {
      if (hud.toggle('map')) player.controls.unlock(); else player.controls.lock();
    } else if (e.code === 'KeyG') {
      if (hud.toggle('graph')) player.controls.unlock(); else player.controls.lock();
    } else if (e.code === 'KeyF' && !hud.openPanel) {
      hud.toggle('floo');
      player.controls.unlock();
    } else if (e.code === 'Escape' && hud.openPanel) {
      hud.closeAll();
    }
  });

  // Teleport flash.
  const flashEl = document.getElementById('flash');
  function flash() {
    flashEl.style.opacity = '0.85';
    setTimeout(() => { flashEl.style.opacity = '0'; }, 60);
  }

  // --- debug / screenshot API ----------------------------------------------
  window.__palace = {
    rooms: () => Object.keys(roomsById),
    teleport,
    pose: (x, z, yawDeg, pitchDeg = 0) => {
      player.place(x, z, (yawDeg * Math.PI) / 180);
      camera.rotation.x = (pitchDeg * Math.PI) / 180;
    },
    pos: () => ({ x: camera.position.x, z: camera.position.z,
                  yaw: camera.rotation.y }),
    ready: false,
  };

  // --- main loop ------------------------------------------------------------
  const clock = new THREE.Clock();
  let acc = 0;
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    player.update(dt);
    for (const fn of updates) fn(t);

    // Throttled UI updates.
    acc += dt;
    if (acc > 0.15) {
      acc = 0;
      const space = spaceAt(layout, camera.position.x, camera.position.z);
      hud.setLocation(space);
      target = findTarget();
      hud.setPrompt(hud.openPanel ? null : target);
      if (hud.openPanel === 'map') {
        hud.drawMap({ x: camera.position.x, z: camera.position.z, yaw: camera.rotation.y });
      }
    }

    renderer.render(scene, camera);
    window.__palace.ready = true;
  });

  addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });
}

boot().catch((err) => {
  document.getElementById('start').innerHTML =
    `<div class="card"><h1>The palace failed to materialize</h1><p>${err.message}</p>
     <p class="muted">Did you run <code>python world.py validate</code>?</p></div>`;
  console.error(err);
});
