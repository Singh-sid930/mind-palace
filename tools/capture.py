#!/usr/bin/env python
"""Headless footage capture for the README (dev tool).

Records short webm clips of scripted camera work (glides, real WASD walks,
constellation orbits, Gemma chat) via the window.__palace debug API, then
converts them to optimized GIFs in docs/media/.

Usage:
    python tools/capture.py stills               # framing check: PNG per scene
    python tools/capture.py record [scene ...]   # record webm + convert to gif
Scenes: hero exhibits study constellation footsteps gemma

Requires serve.py on :8777 and playwright; the gemma scene also needs Ollama.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "docs" / "media"
RAW = MEDIA / "raw"
VIEW = {"width": 1280, "height": 800}
LAUNCH_ARGS = ["--use-gl=angle", "--use-angle=gl", "--enable-gpu",
               "--ignore-gpu-blocklist"]

# In-page cinematography helpers, installed once the engine is ready.
CINE_JS = """
() => {
  const P = window.__palace;
  const rad = (d) => (d * Math.PI) / 180;
  window.__cine = {
    rect: (roomId) => {
      const r = P.layout.spaceById[roomId].rect;
      return { cx: r.cx, cz: r.cz, w: r.w, d: r.d };
    },
    sign: (destRoom) => {
      const s = P.signs.find((s) => s.destRoom === destRoom);
      return s ? { x: s.x, z: s.z } : null;
    },
    key(code, type = 'keydown') {
      document.dispatchEvent(new KeyboardEvent(type, { code, bubbles: true }));
    },
    // Smooth camera path through absolute keyframes {x, z, yaw, pitch?, ms}.
    // The first keyframe is the start pose; its ms is ignored.
    async glide(kfs) {
      const ease = (u) => (1 - Math.cos(Math.PI * Math.min(1, u))) / 2;
      P.pose(kfs[0].x, kfs[0].z, kfs[0].yaw, kfs[0].pitch || 0);
      for (let i = 1; i < kfs.length; i++) {
        const a = kfs[i - 1], b = kfs[i], t0 = performance.now();
        await new Promise((res) => {
          const step = () => {
            const u = ease((performance.now() - t0) / b.ms);
            let dy = b.yaw - a.yaw;
            while (dy > 180) dy -= 360;
            while (dy < -180) dy += 360;
            P.pose(a.x + (b.x - a.x) * u, a.z + (b.z - a.z) * u,
                   a.yaw + dy * u,
                   (a.pitch || 0) + ((b.pitch || 0) - (a.pitch || 0)) * u);
            if (u < 1) requestAnimationFrame(step); else res();
          };
          step();
        });
      }
    },
    // Hold W and steer toward (x, z) — real player movement with collision.
    async walkTo(x, z, maxMs = 10000, arrive = 1.2) {
      this.key('KeyW');
      const t0 = performance.now();
      await new Promise((res) => {
        const step = () => {
          const p = P.pos();
          const dx = x - p.x, dz = z - p.z;
          if (Math.hypot(dx, dz) < arrive || performance.now() - t0 > maxMs) {
            res(); return;
          }
          const want = Math.atan2(-dx, -dz);
          let dy = want - p.yaw;
          while (dy > Math.PI) dy -= 2 * Math.PI;
          while (dy < -Math.PI) dy += 2 * Math.PI;
          const turn = Math.max(-0.045, Math.min(0.045, dy));
          P.pose(p.x, p.z, ((p.yaw + turn) * 180) / Math.PI);
          requestAnimationFrame(step);
        };
        step();
      });
      this.key('KeyW', 'keyup');
    },
    // Type into the chat input character by character (no key events, so the
    // player never moves), then submit.
    async ask(text, msPerChar = 45) {
      const inp = document.getElementById('chat-input');
      for (const ch of text) {
        inp.value += ch;
        await new Promise((r) => setTimeout(r, msPerChar));
      }
      inp.dispatchEvent(new KeyboardEvent('keydown',
        { code: 'Enter', key: 'Enter', bubbles: true }));
    },
  };
  return true;
}
"""


async def boot(pw, record_dir=None):
    browser = await pw.chromium.launch(args=LAUNCH_ARGS)
    ctx_opts = {"viewport": VIEW}
    if record_dir:
        ctx_opts.update(record_video_dir=str(record_dir),
                        record_video_size=VIEW)
    context = await browser.new_context(**ctx_opts)
    page = await context.new_page()
    page.on("pageerror", lambda e: print("  pageerror:", e))
    await page.goto("http://localhost:8777/?debug=1")
    await page.wait_for_function("window.__palace && window.__palace.ready",
                                 timeout=25000)
    await page.evaluate(CINE_JS)
    return browser, context, page


async def settle(page, room, ms=1200, ghost=False):
    # Gemma's ghost chases the camera and photobombs scripted shots; keep her
    # only in scenes that are about her.
    await page.evaluate(
        f"window.__palace.companion.group.visible = {str(ghost).lower()}")
    await page.evaluate(f"window.__palace.teleport('{room}')")
    await page.wait_for_timeout(ms)


# --- scenes ------------------------------------------------------------------
# Each scene poses/acts on an already-booted page. Durations are real time.

async def scene_hero(page):
    """Undercroft pan, then a real walk through the doorway into the bronze
    Wing of Continuous Motion."""
    await settle(page, "undercroft")
    r = await page.evaluate("window.__cine.rect('undercroft')")
    cx, cz, w, d = r["cx"], r["cz"], r["w"], r["d"]
    sign = await page.evaluate("window.__cine.sign('the-curved-ground')")
    # End the establishing pan aimed straight at the wing's signpost, so the
    # walk that follows never has to sweep across blank wall.
    import math
    px, pz = cx + w * 0.04, cz + d * 0.14
    aim = math.degrees(math.atan2(-(sign["x"] - px), -(sign["z"] - pz)))
    await page.evaluate(
        """(k) => window.__cine.glide(k)""",
        [
            {"x": cx + w * 0.24, "z": cz + d * 0.30, "yaw": 30, "pitch": 3, "ms": 0},
            {"x": px, "z": pz, "yaw": aim, "pitch": 1, "ms": 4200},
        ])
    await page.evaluate(
        "(s) => window.__cine.walkTo(s.x, s.z, 9000, 1.5)", sign)
    # Step onto the corridor's centerline before heading for the room, so the
    # camera glides through the middle of the doorway instead of hugging the jamb.
    tgt = await page.evaluate("window.__cine.rect('the-curved-ground')")
    if abs(sign["x"] - tgt["cx"]) > abs(sign["z"] - tgt["cz"]):
        mid = {"x": sign["x"] + (1.6 if tgt["cx"] > sign["x"] else -1.6),
               "z": tgt["cz"]}
    else:
        mid = {"x": tgt["cx"],
               "z": sign["z"] + (1.6 if tgt["cz"] > sign["z"] else -1.6)}
    await page.evaluate(
        "(m) => window.__cine.walkTo(m.x, m.z, 6000, 0.9)", mid)
    await page.evaluate(
        "(t) => window.__cine.walkTo(t.cx, t.cz, 9000, 3.4)", tgt)
    await page.wait_for_timeout(700)


async def scene_exhibits(page):
    """Slow arcs around three kinetic concept props on different floors."""
    for room, a0, a1, secs in [("the-inkwell", 150, 205, 4.2),
                               ("forge-of-the-query", -30, 25, 4.2),
                               ("the-two-maps", 60, 115, 4.2)]:
        await settle(page, room)
        r = await page.evaluate(f"window.__cine.rect('{room}')")
        cx, cz = r["cx"], r["cz"]
        import math
        R = 4.0
        def at(deg):
            rad = math.radians(deg)
            return {"x": cx + R * math.sin(rad), "z": cz + R * math.cos(rad),
                    "yaw": deg, "pitch": -3}
        await page.evaluate(
            "(k) => window.__cine.glide(k)",
            [dict(at(a0), ms=0), dict(at(a1), ms=int(secs * 1000))])


async def scene_study(page):
    """Press E on a figure exhibit: it unfolds as a floating panel in the room."""
    await settle(page, "the-two-maps")
    r = await page.evaluate("window.__cine.rect('the-two-maps')")
    cx, cz, d = r["cx"], r["cz"], r["d"]
    await page.evaluate(
        "(k) => window.__cine.glide(k)",
        [{"x": cx, "z": cz + d * 0.30, "yaw": 0, "pitch": 0, "ms": 0},
         {"x": cx, "z": cz + d * 0.22, "yaw": 0, "pitch": 0, "ms": 1400}])
    await page.evaluate(
        "window.__palace.studyDiagram('the-two-maps', 'image', true)")
    await page.wait_for_timeout(1800)
    await page.evaluate(
        "(k) => window.__cine.glide(k)",
        [{"x": cx, "z": cz + d * 0.22, "yaw": 0, "pitch": 0, "ms": 0},
         {"x": cx + 2.6, "z": cz + d * 0.30, "yaw": 18, "pitch": 2, "ms": 3200},
         {"x": cx - 2.2, "z": cz + d * 0.32, "yaw": -16, "pitch": 2, "ms": 3600}])
    await page.wait_for_timeout(600)


async def scene_constellation(page):
    """Open the constellation (G) and orbit/zoom the 3D graph of every floor."""
    await settle(page, "attention-atrium")
    await page.keyboard.press("KeyG")
    await page.wait_for_timeout(1500)
    m = page.mouse
    await m.move(640, 400)
    await m.down()
    await m.move(880, 330, steps=45)
    await m.up()
    await page.wait_for_timeout(400)
    for _ in range(3):
        await m.wheel(0, -240)
        await page.wait_for_timeout(220)
    await page.wait_for_timeout(600)
    await m.move(640, 400)
    await m.down()
    await m.move(430, 470, steps=45)
    await m.up()
    await page.wait_for_timeout(400)
    for _ in range(4):
        await m.wheel(0, 260)
        await page.wait_for_timeout(220)
    await page.wait_for_timeout(800)


async def scene_footsteps(page):
    """The Marauder's footsteps marching toward the next thing to learn."""
    await settle(page, "the-curved-ground")
    r = await page.evaluate("window.__cine.rect('the-curved-ground')")
    cx, cz, d = r["cx"], r["cz"], r["d"]
    await page.evaluate(
        "(k) => window.__cine.glide(k)",
        [{"x": cx + 1.5, "z": cz + d * 0.32, "yaw": -14, "pitch": -16, "ms": 0},
         {"x": cx - 1.5, "z": cz + d * 0.30, "yaw": 14, "pitch": -14, "ms": 5200}])
    await page.keyboard.press("KeyP")   # toggle off — toast confirms
    await page.wait_for_timeout(1700)
    await page.keyboard.press("KeyP")   # back on — prints return
    await page.wait_for_timeout(2600)


async def scene_gemma(page):
    """Ask Gemma about the room you're standing in."""
    await settle(page, "forge-of-the-query", ghost=True)
    r = await page.evaluate("window.__cine.rect('forge-of-the-query')")
    cx, cz, d = r["cx"], r["cz"], r["d"]
    await page.evaluate(
        "(k) => window.__cine.glide(k)",
        [{"x": cx + 1.2, "z": cz + d * 0.26, "yaw": 8, "pitch": -2, "ms": 0},
         {"x": cx + 0.6, "z": cz + d * 0.24, "yaw": 4, "pitch": -2, "ms": 1200}])
    await page.keyboard.press("KeyT")
    await page.wait_for_timeout(900)
    await page.evaluate(
        "window.__cine.ask('why does the lantern pour more light on some keys than others?')")
    # Wait for the streamed reply to finish (bubble text stops growing).
    await page.wait_for_timeout(3000)
    last, stable = "", 0
    for _ in range(60):
        txt = await page.evaluate(
            "document.getElementById('chat-log').innerText")
        if txt == last:
            stable += 1
            if stable >= 4:
                break
        else:
            stable = 0
        last = txt
        await page.wait_for_timeout(700)
    await page.wait_for_timeout(1500)


SCENES = {
    "hero": scene_hero,
    "exhibits": scene_exhibits,
    "study": scene_study,
    "constellation": scene_constellation,
    "footsteps": scene_footsteps,
    "gemma": scene_gemma,
}

# GIF conversion: fps / width / optional speed-up per scene.
GIF = {
    "hero": (12, 760, 1.0),
    "exhibits": (12, 680, 1.0),
    "study": (10, 680, 1.0),
    "constellation": (12, 680, 1.0),
    "footsteps": (12, 680, 1.0),
    "gemma": (10, 760, 1.6),
}


def to_gif(webm, name):
    fps, width, speed = GIF[name]
    out = MEDIA / f"{name}.gif"
    setpts = f"setpts={1/speed:.4f}*PTS," if speed != 1.0 else ""
    vf = (f"{setpts}fps={fps},scale={width}:-1:flags=lanczos,"
          "split[s0][s1];[s0]palettegen=max_colors=96[p];"
          "[s1][p]paletteuse=dither=bayer:bayer_scale=5")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm),
                    "-vf", vf, "-loop", "0", str(out)], check=True)
    mb = out.stat().st_size / 1e6
    print(f"  {out.relative_to(ROOT)}  {mb:.1f} MB")


async def record(names):
    RAW.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        for name in names:
            print(f"scene: {name}")
            browser, context, page = await boot(pw, record_dir=RAW)
            await SCENES[name](page)
            video = page.video
            await context.close()
            path = Path(await video.path())
            final = RAW / f"{name}.webm"
            path.rename(final)
            await browser.close()
            to_gif(final, name)


async def stills(names):
    MEDIA.mkdir(parents=True, exist_ok=True)
    out_dir = Path("/tmp/claude-1000/-home-thelastsid-workspace-mind-palace/"
                   "ea9e582d-1b83-43d4-99bc-af0bd413bb33/scratchpad/stills")
    out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser, context, page = await boot(pw)
        for name in names:
            await SCENES[name](page)
            p = out_dir / f"{name}.png"
            await page.screenshot(path=str(p))
            print(p)
        await browser.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    names = sys.argv[2:] or list(SCENES)
    bad = [n for n in names if n not in SCENES]
    if bad:
        sys.exit(f"unknown scenes: {bad}")
    asyncio.run(stills(names) if mode == "stills" else record(names))
