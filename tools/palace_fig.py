"""Shared visual style for palace concept figures.

Run with the `lrm` conda env:  ~/anaconda3/envs/lrm/bin/python

Every figure uses a dark, palace-matching ground (so it blends with the
in-world diagram panel, whose raster background is #10151d) with cream serif
text and a per-wing accent. Import this and call fig()/save() so all of the
palace's figures look like one hand.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "world" / "assets"

# --- palette ---------------------------------------------------------------
BG = "#0e131b"      # figure ground
PANEL = "#141c27"   # axes ground
INK = "#ece3cc"     # cream text
MUTED = "#9bb0c6"   # secondary text / ticks
GRID = "#26323f"
HOT = "#ffd98a"     # warm highlight (shared)

WING = {
    "emerald":  {"accent": "#9fe8b9", "warm": "#e0b870", "cool": "#7fd0a8"},
    "sapphire": {"accent": "#9ac4ff", "warm": "#e6c069", "cool": "#7fa8e0"},
    "amber":    {"accent": "#ffc46b", "warm": "#ffb04a", "cool": "#d9a14e"},
    "parchment":{"accent": "#e0c98a", "warm": "#d9b25a", "cool": "#c9b079"},
    "violet":   {"accent": "#d2a8ff", "warm": "#d8c27a", "cool": "#a88fe0"},
    "crimson":  {"accent": "#ff9a7a", "warm": "#e0a860", "cool": "#d97f6b"},
    "obsidian": {"accent": "#8fe9dc", "warm": "#d9b25a", "cool": "#7fc0b8"},
    "silver":   {"accent": "#c4ceda", "warm": "#d9c07a", "cool": "#8fb0d0"},
    "bronze":   {"accent": "#e8c26a", "warm": "#d98a4a", "cool": "#9fb87a"},
    "verdigris":{"accent": "#7ff2d8", "warm": "#d8b25a", "cool": "#6fb8a8"},
}

# Diverging/sequential colormaps that read well on the dark ground.
def cmap(name="cool"):
    from matplotlib.colors import LinearSegmentedColormap
    stops = {
        "heat": ["#10151d", "#1f3a5f", "#3f7fb0", "#9ac4ff", "#ffe6a6"],
        "emer": ["#10151d", "#1c3b2e", "#2f7d57", "#7fd0a8", "#eafff2"],
        "fire": ["#10151d", "#5c2a1a", "#b0532a", "#ffae5a", "#fff0c8"],
    }[name]
    return LinearSegmentedColormap.from_list(name, stops)


plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Georgia", "Times New Roman"],
    "text.color": INK,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "figure.dpi": 150,
})


def style_ax(ax, wing="sapphire", grid=True):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=11)
    ax.title.set_color(INK)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    if grid:
        ax.grid(True, color=GRID, linewidth=0.6, alpha=0.6)
        ax.set_axisbelow(True)
    return ax


def fig(w=10.0, h=6.0, wing="sapphire", n=1, **kw):
    """Return (figure, axes). n>1 makes a row of panels (or pass nrows/ncols)."""
    nrows = kw.pop("nrows", 1)
    ncols = kw.pop("ncols", n)
    f, axes = plt.subplots(nrows, ncols, figsize=(w, h), **kw)
    f.patch.set_facecolor(BG)
    axlist = np.atleast_1d(axes).ravel() if (nrows * ncols > 1) else [axes]
    for ax in axlist:
        style_ax(ax, wing)
    return f, axes


def suptitle(f, text, wing="sapphire"):
    f.suptitle(text, color=INK, fontsize=19, fontweight="bold", y=0.99)


def save(f, name):
    ASSETS.mkdir(exist_ok=True)
    p = ASSETS / name
    f.savefig(p, facecolor=f.get_facecolor(), bbox_inches="tight",
              pad_inches=0.25, dpi=150)
    plt.close(f)
    return f"world/assets/{name}"
