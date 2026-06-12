#!/usr/bin/env python
"""Headless screenshot harness for the palace (dev tool).

Usage:
    python tools/shoot.py                      # spawn view
    python tools/shoot.py <roomId> [yawDeg]    # inside a specific room

Requires a static server on :8777 (python -m http.server 8777) and playwright.
Writes /tmp/palace-<label>.png and prints the path.
"""

import asyncio
import sys

from playwright.async_api import async_playwright


async def main():
    room = sys.argv[1] if len(sys.argv) > 1 else None
    yaw = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    label = room or "spawn"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            args=["--use-gl=angle", "--use-angle=swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        await page.goto("http://localhost:8777/?debug=1")
        try:
            await page.wait_for_function("window.__palace && window.__palace.ready",
                                         timeout=15000)
        except Exception:
            print("ENGINE DID NOT BECOME READY. Errors:")
            for e in errors:
                print("  -", e)
            await browser.close()
            sys.exit(1)

        if room:
            await page.evaluate(f"window.__palace.teleport('{room}')")
            if yaw:
                pos = await page.evaluate("window.__palace.pos()")
                await page.evaluate(
                    f"window.__palace.pose({pos['x']}, {pos['z']}, {yaw})")
        await page.wait_for_timeout(900)  # let textures/lights settle

        path = f"/tmp/palace-{label}.png"
        await page.screenshot(path=path)
        print(path)
        for e in errors:
            print("console-error:", e)
        await browser.close()


asyncio.run(main())
