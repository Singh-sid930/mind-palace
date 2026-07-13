"""README elevation map: the palace's floors as knowledge lineage.

Run with:  ~/anaconda3/envs/lrm/bin/python tools/readme_map.py
Writes docs/media/palace-map.png. Room counts and totals are read live from
the world data so the map can be regenerated whenever the palace grows.
"""
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from palace_fig import BG, PANEL, INK, MUTED, GRID, HOT, WING

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "media" / "palace-map.png"

world = json.loads((ROOT / "world" / "world.json").read_text())
idx = json.loads((ROOT / "world" / "rooms" / "index.json").read_text())["rooms"]
graph = json.loads((ROOT / "world" / "graph.json").read_text())

wing_level = {w["id"]: w["level"] for w in world["wings"]}
hub_level = {l["hub"]: l["id"] for l in world["levels"]}
per_level = Counter()
for f in idx:
    r = json.loads((ROOT / "world" / "rooms" / f).read_text())
    per_level[wing_level.get(r.get("wing")) or hub_level[r["id"]]] += 1

# --- the drawing ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12.2, 8.2))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.9)
ax.axis("off")

def tower(x, y, w, h, palettes, title, sub, rooms):
    """A floor drawn as a slab; one color band per wing palette."""
    band = w / len(palettes)
    for i, p in enumerate(palettes):
        c = WING[p]["accent"]
        ax.add_patch(FancyBboxPatch(
            (x + i * band + 0.03, y + 0.03), band - 0.06, h - 0.06,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=PANEL, edgecolor=c, linewidth=1.8))
        ax.plot([x + i * band + 0.16, x + (i + 1) * band - 0.16],
                [y + h - 0.28, y + h - 0.28], color=c, lw=3, alpha=0.9,
                solid_capstyle="round")
    cx = x + w / 2
    ax.text(cx, y + h - 0.62, title, ha="center", va="center",
            color=INK, fontsize=12.5, fontweight="bold")
    ax.text(cx, y + h / 2 - 0.12, sub, ha="center", va="center",
            color=MUTED, fontsize=9.8, style="italic")
    ax.text(cx, y + 0.30, f"{rooms} rooms", ha="center", va="center",
            color=MUTED, fontsize=9)
    return cx, y, y + h  # center-x, bottom-y, top-y

def stair(x0, y0, x1, y1, bend=0.0, gated=True):
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), connectionstyle=f"arc3,rad={bend}",
        arrowstyle="-|>", mutation_scale=13, linewidth=1.5,
        color=HOT, alpha=0.75, zorder=1))
    if gated:
        mx, my = (x0 + x1) / 2 + bend * (y1 - y0) * 0.5, (y0 + y1) / 2
        ax.scatter([mx], [my], marker="D", s=52, color=BG, edgecolor=HOT,
                   linewidth=1.4, zorder=3)

H = 1.9
# Tier +1 — three towers.
att = tower(0.3, 6.6, 3.0, H, ["obsidian"],
            "Workshop of Attunement", "LoRA — adapting a trained art\nwith small low-rank grafts",
            per_level["attunement"])
wm = tower(4.0, 6.6, 4.0, H, ["emerald", "crimson"],
           "The Upper Floor", "World models (V-JEPA) &\nthe reforged transformer (DiT)",
           per_level["world-models"])
vid = tower(8.7, 6.6, 3.0, H, ["silver"],
            "Gallery of Moving Portraits", "Video diffusion — pictures\ntaught to move",
            per_level["video"])

# Tier 0 — the ground floor.
attn = tower(1.1, 3.7, 4.2, H, ["sapphire"],
             "Hall of Attention", "Queries, keys & values —\nthe transformer's gaze",
             per_level["attention"])
diff = tower(6.7, 3.7, 4.2, H, ["amber"],
             "Hall of Diffusion", "Noise walked backward —\nimages out of static",
             per_level["diffusion"])

# Tier -1 — the basement.
und = tower(2.4, 0.8, 7.2, H, ["violet", "bronze"],
            "The Undercroft (foundations)",
            "Arithmancy — probability, variance, similarity, frequency, SVD\n"
            "Continuous Motion — manifolds, exp/log maps, rotations",
            per_level["foundations"])

# Stairs (every one kept by a Gatekeeper) + the sibling archway.
stair(4.0, 2.7, 3.2, 3.7)              # undercroft -> attention
stair(8.0, 2.7, 8.8, 3.7)              # undercroft -> diffusion
stair(3.2, 5.6, 5.0, 6.6, bend=0.06)   # attention -> upper floor
stair(8.8, 5.6, 7.0, 6.6, bend=-0.06)  # diffusion -> upper floor
stair(2.2, 5.6, 1.8, 6.6)              # attention -> attunement
stair(7.4, 5.6, 3.35, 7.1, bend=0.14)  # diffusion -> attunement
stair(9.6, 5.6, 10.2, 6.6)             # diffusion -> video
stair(4.6, 5.6, 8.65, 7.1, bend=-0.14) # attention -> video
ax.add_patch(FancyArrowPatch((5.3, 4.65), (6.7, 4.65),
             arrowstyle="<|-|>", mutation_scale=11, linewidth=1.3,
             color=MUTED, alpha=0.8, linestyle=(0, (4, 3))))
ax.text(6.0, 4.85, "archway", ha="center", color=MUTED, fontsize=8.5)

# Tier labels, tucked into the left margin of each band.
for y, t in [(8.62, "TIER +1 — BUILT UPON THE GROUND"),
             (5.72, "TIER 0 — THE GROUND FLOOR"),
             (2.82, "TIER −1 — MATHEMATICAL FOUNDATIONS")]:
    ax.text(0.12, y, t, ha="left", va="center",
            color=MUTED, fontsize=7.6, alpha=0.9)

ax.text(6.0, 9.62, "THE PALACE OF MIND — FLOORS AS KNOWLEDGE LINEAGE",
        ha="center", color=INK, fontsize=15, fontweight="bold")
ax.text(6.0, 9.16, "every floor is built from what lies below · every stair is kept by a Gatekeeper (◆) who quizzes you on the prerequisites",
        ha="center", color=MUTED, fontsize=9.5, style="italic")
ax.text(6.0, 0.25,
        f"{len(idx)} rooms  ·  {len(graph['concepts'])} concepts  ·  "
        f"{len(graph['edges'])} edges in the knowledge graph",
        ha="center", color=HOT, fontsize=10)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, facecolor=BG, bbox_inches="tight", pad_inches=0.3, dpi=150)
print(OUT)
