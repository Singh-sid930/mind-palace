#!/usr/bin/env python
"""Records the promo film: scripted camera work through the palace, cut
together with captions and the offline-rendered score.

    ~/anaconda3/envs/story-teller/bin/python tools/promo.py stills   # framing
    ~/anaconda3/envs/story-teller/bin/python tools/promo.py record   # scenes
    python tools/promo.py cut                                        # assemble

Needs serve.py on :8779 (PALACE_PORT=8779) and, for `cut`, ffmpeg plus
docs/media/raw/promo_music.wav from tools/promo_audio.py.
"""
import asyncio
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "docs" / "media" / "raw" / "promo"
OUT = ROOT / "docs" / "media" / "palace-promo.mp4"
VIEW = {"width": 1920, "height": 1080}
URL = "http://localhost:8779/?debug=1"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

CINE = (ROOT / "tools" / "capture.py").read_text()
CINE = CINE[CINE.index("CINE_JS = \"\"\"") + 13: CINE.index("\"\"\"\n\n\nasync def boot")]


async def boot(pw, record_dir):
    browser = await pw.chromium.launch(args=[
        "--use-gl=angle", "--use-angle=gl", "--enable-gpu",
        "--ignore-gpu-blocklist", "--hide-scrollbars"])
    ctx = await browser.new_context(
        viewport=VIEW, record_video_dir=str(record_dir), record_video_size=VIEW)
    page = await ctx.new_page()
    page.on("pageerror", lambda e: print("  pageerror:", e))
    await page.goto(URL)
    await page.wait_for_function("window.__palace && window.__palace.ready", timeout=40000)
    await page.evaluate(CINE)
    # The start scroll and Gemma's ghost are not part of the film.
    await page.evaluate("document.getElementById('start').style.display='none'")
    await page.evaluate("window.__palace.companion.group.visible = false")
    # HUD chrome is for players, not for the film: the key row and the
    # "E, study ..." prompt would sit in every shot.
    await page.add_style_tag(content=(
        "#hud-keys,#hud-prompt,#event-toast,#foot-toast{display:none!important}"))
    return browser, ctx, page


async def face(page, room, title=None, back=3.4, pitch=-2):
    """Stand `back` metres from an exhibit (or the room centre) and look at it."""
    d = await page.evaluate("""([room, title]) => {
      const P = window.__palace;
      const sp = P.layout.spaceById[room];
      const tour = P.levels.tours.get(room) || [];
      let w = null;
      if (title) w = tour.find(x => x.title.toLowerCase().includes(title.toLowerCase()));
      if (!w) w = { x: sp.rect.cx, z: sp.rect.cz };
      return { x: w.x, z: w.z, cx: sp.rect.cx, cz: sp.rect.cz };
    }""", [room, title])
    dx, dz = d["x"] - d["cx"], d["z"] - d["cz"]
    n = math.hypot(dx, dz)
    if n < 0.05:                       # centre artifact: back off toward the door
        dx, dz, n = 0.0, 1.0, 1.0
    cx, cz = d["x"] - dx / n * back, d["z"] - dz / n * back
    yaw = math.degrees(math.atan2(-(d["x"] - cx), -(d["z"] - cz)))
    return cx, cz, yaw


async def orbit(page, room, title, secs, sweep=28, back=3.6, pitch=-2):
    """Slow arc around a target: the shot that sells a kinetic artifact."""
    t = await page.evaluate("""([room, title]) => {
      const P = window.__palace; const sp = P.layout.spaceById[room];
      const tour = P.levels.tours.get(room) || [];
      let w = title ? tour.find(x => x.title.toLowerCase().includes(title.toLowerCase())) : null;
      return { x: w ? w.x : sp.rect.cx, z: w ? w.z : sp.rect.cz,
               cx: sp.rect.cx, cz: sp.rect.cz };
    }""", [room, title])
    # Base bearing: from the target back toward the room's open floor, so the
    # arc swings across the front of the piece rather than into a wall.
    dx, dz = t["x"] - t["cx"], t["z"] - t["cz"]
    base = math.atan2(dx, dz) if math.hypot(dx, dz) > 0.05 else 0.0
    kf = []
    for i, a in enumerate((-math.radians(sweep) / 2, math.radians(sweep) / 2)):
        ang = base + a
        cx, cz = t["x"] - math.sin(ang) * back, t["z"] - math.cos(ang) * back
        yaw = math.degrees(math.atan2(-(t["x"] - cx), -(t["z"] - cz)))
        kf.append({"x": cx, "z": cz, "yaw": yaw, "pitch": pitch,
                   "ms": 0 if i == 0 else int(secs * 1000)})
    await page.evaluate("(k) => window.__cine.glide(k)", kf)


# --- the shot list ----------------------------------------------------------
async def s01_hook(page):
    """Open tight on live attention weights, then pull back to the room."""
    await page.evaluate("window.__palace.teleport('forge-of-the-query')")
    await page.wait_for_timeout(900)
    near = await face(page, "forge-of-the-query", "Orb of Likeness", back=1.7)
    mid = await face(page, "forge-of-the-query", "Orb of Likeness", back=2.9)
    await page.evaluate("(k) => window.__cine.glide(k)", [
        {"x": near[0], "z": near[1], "yaw": near[2] - 8, "pitch": 8, "ms": 0},
        {"x": mid[0], "z": mid[1], "yaw": mid[2] + 5, "pitch": 3, "ms": 4200}])


async def s02_walk(page):
    """A real walk: out of the Undercroft into the bronze wing."""
    await page.evaluate("window.__palace.teleport('undercroft')")
    await page.wait_for_timeout(900)
    sign = await page.evaluate("window.__cine.sign('the-curved-ground')")
    r = await page.evaluate("window.__cine.rect('undercroft')")
    px, pz = r["cx"] + r["w"] * 0.06, r["cz"] + r["d"] * 0.16
    aim = math.degrees(math.atan2(-(sign["x"] - px), -(sign["z"] - pz)))
    await page.evaluate("(k) => window.__cine.glide(k)", [
        {"x": r["cx"] + r["w"] * 0.2, "z": r["cz"] + r["d"] * 0.3, "yaw": aim - 26, "pitch": 2, "ms": 0},
        {"x": px, "z": pz, "yaw": aim, "pitch": 0, "ms": 2200}])
    await page.evaluate("(s) => window.__cine.walkTo(s.x, s.z, 7000, 1.5)", sign)
    t = await page.evaluate("window.__cine.rect('the-curved-ground')")
    await page.evaluate("(t) => window.__cine.walkTo(t.cx, t.cz, 8000, 3.2)", t)
    await page.wait_for_timeout(500)


async def s03_artifacts(page):
    """Four kinetic centrepieces, one slow arc each."""
    for room, title, secs in [
        ("the-inkwell", "Where a Droplet Learns", 3.3),
        ("the-two-maps", "The Two Maps", 3.3),
        ("the-court-of-yes-and-no", "Court of Yes and No", 3.3),
        ("the-parallel-whisper", "Whisper Beside the Weight", 3.3),
    ]:
        await page.evaluate(f"window.__palace.teleport('{room}')")
        await page.wait_for_timeout(800)
        await orbit(page, room, title, secs, sweep=26, back=3.3, pitch=-4)


async def s04_widgets(page):
    """The floating diagrams: a velocity field, then a causal mask.

    The widget hovers above its display, so the pitch is computed from its
    height rather than guessed, otherwise the shot is all ceiling.
    """
    EYE = 1.6
    for room, title, wy, back in [("riverworks-atrium", "Lockkeeper", 3.4, 3.0),
                                  ("veil-of-the-future", "Forbidden", 2.5, 2.6)]:
        await page.evaluate(f"window.__palace.teleport('{room}')")
        await page.wait_for_timeout(800)
        cx, cz, yaw = await face(page, room, title, back=back)
        pitch = math.degrees(math.atan2(wy - EYE, back))
        await page.evaluate("(k) => window.__cine.glide(k)", [
            {"x": cx, "z": cz, "yaw": yaw - 3, "pitch": pitch, "ms": 0},
            {"x": cx, "z": cz, "yaw": yaw + 3, "pitch": pitch, "ms": 2800}])


async def s05_study(page):
    """Press E on a figure: it unfolds large in the room."""
    await page.evaluate("window.__palace.teleport('the-singular-prism')")
    await page.wait_for_timeout(900)
    r = await page.evaluate("window.__cine.rect('the-singular-prism')")
    await page.evaluate("(k) => window.__cine.glide(k)", [
        {"x": r["cx"], "z": r["cz"] + r["d"] * 0.30, "yaw": 0, "pitch": 0, "ms": 0},
        {"x": r["cx"], "z": r["cz"] + r["d"] * 0.24, "yaw": 0, "pitch": 0, "ms": 1200}])
    await page.evaluate("window.__palace.studyDiagram('the-singular-prism', 'image', true)")
    await page.wait_for_timeout(1500)
    await page.evaluate("(k) => window.__cine.glide(k)", [
        {"x": r["cx"], "z": r["cz"] + r["d"] * 0.24, "yaw": 0, "pitch": 0, "ms": 0},
        {"x": r["cx"] + 2.4, "z": r["cz"] + r["d"] * 0.30, "yaw": 15, "pitch": 2, "ms": 3000}])


async def s06_dementor(page):
    """The quirk: a dementor sweeps the hall, a patronus answers it."""
    await page.evaluate("window.__palace.teleport('the-backward-walk')")
    await page.wait_for_timeout(900)
    r = await page.evaluate("window.__cine.rect('the-backward-walk')")
    await page.evaluate(f"window.__palace.pose({r['cx']}, {r['cz'] + r['d'] * 0.3}, 0, 2)")
    await page.evaluate("window.__palace.events.spawn('dementor-pass')")
    await page.wait_for_timeout(4200)
    await page.evaluate("window.__palace.events.spawn('patronus-answer')")
    await page.wait_for_timeout(4200)


async def s07_footsteps(page):
    """The Marauder's footprints, marching to whatever you have not read."""
    await page.evaluate("window.__palace.teleport('the-curved-ground')")
    await page.wait_for_timeout(900)
    r = await page.evaluate("window.__cine.rect('the-curved-ground')")
    await page.evaluate("(k) => window.__cine.glide(k)", [
        {"x": r["cx"] + 1.4, "z": r["cz"] + r["d"] * 0.30, "yaw": -12, "pitch": -20, "ms": 0},
        {"x": r["cx"] - 1.4, "z": r["cz"] + r["d"] * 0.27, "yaw": 12, "pitch": -18, "ms": 3800}])


async def s08_constellation(page):
    """Every idea in the palace, hanging in 3D."""
    await page.evaluate("window.__palace.teleport('attention-atrium')")
    await page.wait_for_timeout(700)
    await page.keyboard.press("KeyG")
    await page.wait_for_timeout(1400)
    m = page.mouse
    await m.move(960, 540); await m.down()
    await m.move(1320, 430, steps=60); await m.up()
    for _ in range(3):
        await m.wheel(0, -240); await page.wait_for_timeout(200)
    await m.move(960, 540); await m.down()
    await m.move(700, 600, steps=50); await m.up()
    await page.wait_for_timeout(1200)


SCENES = {
    "hook": s01_hook, "walk": s02_walk, "artifacts": s03_artifacts,
    "widgets": s04_widgets, "study": s05_study, "dementor": s06_dementor,
    "footsteps": s07_footsteps, "constellation": s08_constellation,
}
ORDER = list(SCENES)


async def record(names):
    RAW.mkdir(parents=True, exist_ok=True)
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        for name in names:
            print("scene:", name)
            browser, ctx, page = await boot(pw, RAW)
            await SCENES[name](page)
            video = page.video
            await ctx.close()
            Path(await video.path()).rename(RAW / f"{name}.webm")
            await browser.close()


async def stills(names):
    from playwright.async_api import async_playwright
    out = RAW / "stills"; out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser, ctx, page = await boot(pw, RAW)
        for name in names:
            await SCENES[name](page)
            await page.screenshot(path=str(out / f"{name}.png"))
            print(out / f"{name}.png")
        await ctx.close(); await browser.close()


# --- the cut ----------------------------------------------------------------
# (source clip, start, duration, speed). Durations are chosen so the film runs
# to roughly the length of the music bed.
CLIPS = [
    ("hook",          0.9, 4.0, 1.0),
    ("walk",          2.4, 5.0, 1.0),
    ("artifacts",     0.6, 9.5, 1.55),
    ("widgets",       1.0, 5.0, 1.0),
    ("study",         0.8, 5.0, 1.0),
    ("dementor",      1.2, 7.0, 1.0),
    ("footsteps",     0.6, 4.5, 1.0),
    ("constellation", 0.6, 5.0, 1.0),
]
END_CARD = 3.6

# (start, end, text) in seconds of the finished film. LinkedIn autoplays
# muted, so these carry the whole story.
CAPTIONS = [
    (0.5,  3.8,  "I turned my ML notes into a castle I can walk through"),
    (4.3,  8.7,  "68 rooms  ·  9 floors  ·  every idea in its own place"),
    (9.4,  13.4, "every centrepiece animates the real mathematics"),
    (14.0, 18.3, "attention  ·  diffusion  ·  contrastive learning  ·  LoRA"),
    (19.0, 23.2, "every plaque carries a live diagram over it"),
    (24.0, 28.3, "press E and the figure unfolds in the room"),
    (29.2, 34.8, "and yes, there are dementors"),
    (36.0, 39.8, "footprints lead to whatever you have not read"),
    (40.6, 44.8, "and the whole knowledge graph, in 3D"),
]


def esc(t):
    return t.replace(":", r"\:").replace("'", "")


def make_end_card(path, secs):
    """A still card with the repo link, drawn in the palace's own colours."""
    txt = (
        f"drawtext=fontfile={FONT_B}:text='The Palace of Mind':"
        "fontcolor=0xECE3CC:fontsize=88:x=(w-tw)/2:y=h*0.30,"
        f"drawtext=fontfile={FONT}:text='68 rooms  ·  9 floors  ·  one knowledge graph':"
        "fontcolor=0x9BB0C6:fontsize=40:x=(w-tw)/2:y=h*0.44,"
        f"drawtext=fontfile={FONT_B}:text='singh-sid930.github.io/mind-palace':"
        "fontcolor=0xFFD98A:fontsize=52:x=(w-tw)/2:y=h*0.58,"
        f"drawtext=fontfile={FONT}:text='open source  ·  built as validated JSON':"
        "fontcolor=0x9BB0C6:fontsize=34:x=(w-tw)/2:y=h*0.68"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
        "-i", f"color=c=0x0E131B:s=1920x1080:d={secs}:r=30",
        "-vf", txt + ",fade=t=in:st=0:d=0.5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)


def cut():
    work = RAW / "cut"; work.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, (name, ss, dur, speed) in enumerate(CLIPS):
        src = RAW / f"{name}.webm"
        out = work / f"{i:02d}_{name}.mp4"
        vf = (f"setpts={1/speed:.4f}*PTS," if speed != 1.0 else "") + \
             "scale=1920:1080:force_original_aspect_ratio=increase," \
             "crop=1920:1080,fps=30,format=yuv420p"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", str(ss),
            "-t", str(dur * speed), "-i", str(src), "-vf", vf,
            "-an", "-c:v", "libx264", "-crf", "19", str(out)], check=True)
        parts.append(out)

    end = work / "99_end.mp4"
    make_end_card(end, END_CARD)
    parts.append(end)

    listing = work / "parts.txt"
    listing.write_text("".join(f"file '{p.name}'\n" for p in parts))
    joined = work / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)],
                   check=True)

    body = sum(c[2] for c in CLIPS)
    total = body + END_CARD
    caps = ",".join(
        f"drawtext=fontfile={FONT}:text='{esc(t)}':fontcolor=0xF2EAD6:"
        f"fontsize=46:box=1:boxcolor=0x0A0710@0.55:boxborderw=26:"
        f"x=(w-tw)/2:y=h-190:enable='between(t,{a},{b})'"
        for a, b, t in CAPTIONS)
    fades = f"fade=t=in:st=0:d=0.6,fade=t=out:st={total-0.6:.2f}:d=0.6"

    music = ROOT / "docs" / "media" / "raw" / "promo_music.wav"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined)]
    if music.exists():
        cmd += ["-i", str(music)]
    cmd += ["-vf", f"{caps},{fades}"]
    if music.exists():
        cmd += ["-af", f"afade=t=in:st=0:d=1,afade=t=out:st={total-2.5:.2f}:d=2.5",
                "-shortest", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-crf", "20", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)]
    subprocess.run(cmd, check=True)
    print(OUT, f"{total:.1f}s")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    if mode == "cut":
        cut(); sys.exit(0)
    names = sys.argv[2:] or ORDER
    bad = [n for n in names if n not in SCENES]
    if bad:
        sys.exit(f"unknown scenes: {bad}")
    asyncio.run(stills(names) if mode == "stills" else record(names))
