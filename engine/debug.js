// window.__palace: the debug / headless-screenshot API. Nothing in the engine
// depends on this; it exists so tooling (playwright captures, parity checks,
// figure renders) can teleport, pose the camera and open exhibits at will.

import * as THREE from 'three';

export function installDebugApi({ scene, camera, player, layout, roomsById,
                                  interactables, levels, wisp, diagramPanel,
                                  teleport, palette, showStudyCard }) {
  window.__palace = {
    rooms: () => Object.keys(roomsById),
    scene,
    THREE,
    teleport,
    pose: (x, z, yawDeg, pitchDeg = 0) => {
      player.place(x, z, (yawDeg * Math.PI) / 180);
      camera.rotation.x = (pitchDeg * Math.PI) / 180;
    },
    pos: () => ({ x: camera.position.x, z: camera.position.z,
                  yaw: camera.rotation.y }),
    wisp,
    diagramPanel,
    layout,
    levels,
    get signs() { return levels.signs; }, // active floor's signposts
    stairs2: () => {
      const seen = {}; const out = [];
      for (const [o, r] of interactables) {
        if ((r.kind === 'stair' || r.kind === 'archway') && !seen[r.targetRoom]) {
          seen[r.targetRoom] = true;
          const p = new THREE.Vector3();
          o.getWorldPosition(p);
          out.push({ x: p.x, z: p.z, to: r.targetRoom, kind: r.kind, dir: r.dir });
        }
      }
      return out;
    },
    studyDiagram: (roomId, type = 'diagram', noTeleport = false) => {
      const room = roomsById[roomId];
      const ex = room && room.exhibits.find((e) => e.type === type);
      if (!ex) return false;
      const sp = layout.spaceById[roomId];
      if (!noTeleport) teleport(roomId);
      const opts = { camera, rect: sp ? sp.rect : null,
                     pal: palette(sp ? sp.paletteName : 'parchment') };
      if (ex.type === 'image') diagramPanel.showImage(ex.image, opts);
      else diagramPanel.show(ex.spec, opts);
      showStudyCard({ title: ex.title, subtitle: ex.type, body: ex.text || ex.caption || '' });
      return true;
    },
    ready: false,
  };
  return window.__palace;
}
