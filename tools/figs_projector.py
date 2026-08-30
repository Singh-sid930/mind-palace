"""Concept figure for the Restricted Section of Soft Shields (projector-shield).

ONE multi-panel figure: world/assets/projector-guillotine.png
  (a) The Guillotine   - bar chart, head kept vs head removed
  (b) Feature migration - encoder | projector, features sorting out
  (c) Information bottleneck - funnel compressing, attenuated gradient

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_projector.py
"""
import sys
sys.path.insert(0, "tools")
import palace_fig as P
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

WING = "emerald"
W = P.WING[WING]
ACCENT = W["accent"]   # encoder / kept / broad signal  (green)
WARM = W["warm"]       # head / pretext / discarded     (amber)
COOL = W["cool"]

ENC_C = ACCENT
HEAD_C = WARM


def panel_a(ax):
    """Guillotine: downstream accuracy with head kept vs removed."""
    P.style_ax(ax, WING, grid=True)
    ax.set_title("(a) The Guillotine", color=P.INK, pad=12)
    labels = ["head KEPT\n(projection z)", "head REMOVED\n(encoder r)"]
    vals = [48, 81]
    colors = [HEAD_C, ENC_C]
    x = np.arange(2)
    bars = ax.bar(x, vals, width=0.55, color=colors, edgecolor=P.INK,
                  linewidth=1.2, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v}",
                ha="center", va="bottom", color=P.INK, fontsize=14,
                fontweight="bold")
    # the gain arrow (climbs in the gap between the bars)
    ax.annotate("", xy=(0.72, 79), xytext=(0.28, 51),
                arrowprops=dict(arrowstyle="-|>", color=P.HOT, lw=2.4,
                                connectionstyle="arc3,rad=-0.2"))
    ax.text(0.5, 64, "+30 pts\nor more", ha="center", va="center",
            color=P.HOT, fontsize=12.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12, color=P.INK)
    ax.set_ylabel("downstream task accuracy", fontsize=12.5)
    ax.set_ylim(0, 100)
    ax.set_xlim(-0.65, 1.65)
    ax.tick_params(axis="x", length=0)
    ax.text(0.5, -0.30, "Cutting the head off after training\n"
            "RAISES downstream performance, the characteristic pattern\n"
            "(Bordes et al., NeurIPS 2023)",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=10.5, color=P.MUTED)


def _box(ax, x, y, w, h, color, label, sub=None, title_fs=14):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.04",
                         linewidth=2.0, edgecolor=color, facecolor=P.PANEL,
                         zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.10, label, ha="center", va="top",
            color=color, fontsize=title_fs, fontweight="bold", zorder=4)
    if sub:
        ax.text(x + w / 2, y + 0.07, sub, ha="center", va="bottom",
                color=P.MUTED, fontsize=10, zorder=4, style="italic")
    return box


def panel_b(ax):
    """Gradient feature migration: features sort into encoder vs head."""
    P.style_ax(ax, WING, grid=False)
    ax.set_title("(b) Gradient feature migration", color=P.INK, pad=12)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # migration band label (top)
    ax.text(5.0, 8.55, "pretext features drift toward the head's OUTPUT",
            ha="center", va="center", color=WARM, fontsize=10.5,
            fontweight="bold", zorder=5)
    # migration arrows: warm features drifting from encoder -> head output
    for i in range(3):
        y0 = 8.05 - i * 0.32
        ax.add_patch(FancyArrowPatch((2.6, y0), (8.6, y0),
                     arrowstyle="-|>", mutation_scale=13,
                     color=WARM, lw=1.5, alpha=0.85, zorder=2))

    # two boxes (sit below the migration band)
    _box(ax, 0.6, 2.9, 3.6, 4.0, ENC_C, "ENCODER", "the body, kept")
    _box(ax, 5.8, 2.9, 3.6, 4.0, HEAD_C, "PROJECTOR HEAD",
         "the funnel, cut off", title_fs=12.5)

    # flow arrow between them
    ax.add_patch(FancyArrowPatch((4.3, 4.9), (5.7, 4.9),
                 arrowstyle="-|>", mutation_scale=18,
                 color=P.MUTED, lw=2.0, zorder=1))

    # downstream-useful features settle in encoder (left)
    rng = np.random.default_rng(3)
    ex = rng.uniform(1.1, 3.7, 7)
    ey = rng.uniform(5.3, 6.1, 7)
    ax.scatter(ex, ey, s=80, color=ENC_C, edgecolor=P.INK, linewidth=0.8,
               zorder=3, marker="o")
    ax.text(2.4, 4.05, "broadly-useful\ndownstream features\nSETTLE here",
            ha="center", va="center", color=P.INK, fontsize=10, zorder=5)

    # pretext-useful features migrate toward head output (right)
    px = rng.uniform(6.2, 9.0, 7)
    py = rng.uniform(5.3, 6.1, 7)
    ax.scatter(px, py, s=80, color=WARM, edgecolor=P.INK, linewidth=0.8,
               zorder=3, marker="s")
    ax.text(7.6, 4.05, "pretext-task-useful\nfeatures MIGRATE\ntoward output",
            ha="center", va="center", color=P.INK, fontsize=10, zorder=5)

    # output marker on the right edge
    ax.text(9.55, 4.9, "z", ha="left", va="center", color=WARM,
            fontsize=13, fontweight="bold")

    ax.text(5.0, 2.1,
            "Emergent, not enforced: the implicit bias of gradient training\n"
            "sorts features by usefulness across the non-linear funnel\n"
            "(Xue et al., ICLR 2024)",
            ha="center", va="top", color=P.MUTED, fontsize=10.5)


def panel_c(ax):
    """Information bottleneck: funnel compresses, gradient attenuated."""
    P.style_ax(ax, WING, grid=False)
    ax.set_title("(c) Information bottleneck", color=P.INK, pad=12)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Encoder slab (upstream, broad signal retained), left
    _box(ax, 0.5, 3.7, 2.6, 3.8, ENC_C, "ENCODER", "upstream")
    ax.text(1.8, 4.25, "retains the\nbroader signal", ha="center", va="center",
            color=P.INK, fontsize=10, zorder=5)

    # Funnel (information bottleneck), narrowing toward the loss
    fx0, fx1 = 3.6, 7.4
    ytop0, ybot0 = 7.4, 3.8         # wide mouth (info-rich)
    ytop1, ybot1 = 6.0, 5.2         # narrow waist (compressed)
    funnel = Polygon([(fx0, ytop0), (fx1, ytop1), (fx1, ybot1), (fx0, ybot0)],
                     closed=True, facecolor=HEAD_C, alpha=0.22,
                     edgecolor=HEAD_C, linewidth=2.0, zorder=2)
    ax.add_patch(funnel)
    ax.text((fx0 + fx1) / 2, 7.95, "PROJECTOR HEAD = bottleneck",
            ha="center", va="bottom", color=HEAD_C, fontsize=12,
            fontweight="bold", zorder=5)
    ax.text(4.55, 4.55, "compresses out\ninfo irrelevant to\nthe SSL objective",
            ha="center", va="center", color=P.INK, fontsize=9.5, zorder=5,
            bbox=dict(boxstyle="round,pad=0.25", fc=P.BG, ec="none",
                      alpha=0.78))

    # incoming broad info (many lines) -> squeezed to few at waist
    rng = np.random.default_rng(7)
    for yy in np.linspace(4.1, 7.1, 9):
        ax.plot([3.65, 7.3], [yy, np.interp(yy, [3.8, 7.4], [5.25, 5.95])],
                color=COOL, lw=1.0, alpha=0.5, zorder=1)

    # output z + loss
    ax.add_patch(FancyArrowPatch((7.45, 5.6), (8.7, 5.6),
                 arrowstyle="-|>", mutation_scale=18, color=COOL, lw=2.0,
                 zorder=3))
    ax.text(8.9, 5.6, "z", ha="left", va="center", color=COOL,
            fontsize=13, fontweight="bold")
    ax.text(8.55, 6.7, "SSL\nloss", ha="center", va="center", color=P.MUTED,
            fontsize=10)

    # attenuated gradient flowing back: thick at head, thin into encoder
    ax.add_patch(FancyArrowPatch((7.2, 2.95), (4.0, 2.95),
                 arrowstyle="-|>", mutation_scale=22, color=P.HOT, lw=4.0,
                 alpha=0.9, zorder=3))
    ax.add_patch(FancyArrowPatch((3.9, 2.95), (1.9, 2.95),
                 arrowstyle="-|>", mutation_scale=12, color=P.HOT, lw=1.3,
                 alpha=0.7, zorder=3))
    ax.text(5.6, 2.55, "full gradient pressure", ha="center", va="top",
            color=P.HOT, fontsize=10, fontweight="bold")
    ax.text(2.6, 2.55, "attenuated", ha="center", va="top",
            color=P.HOT, fontsize=9.5, style="italic")

    ax.text(5.0, 1.55,
            "The encoder sits UPSTREAM of the compression, so it keeps the\n"
            "broad signal; the funnel absorbs the burden and attenuates the\n"
            "gradient reaching the encoder (ICLR 2025)",
            ha="center", va="top", color=P.MUTED, fontsize=10.5)


def main():
    f, axes = P.fig(w=20.5, h=7.6, wing=WING, ncols=3)
    P.suptitle(f, "The Soft Shield: why removing the projector head helps",
               wing=WING)
    panel_a(axes[0])
    panel_b(axes[1])
    panel_c(axes[2])
    f.subplots_adjust(left=0.05, right=0.97, top=0.86, bottom=0.16,
                      wspace=0.22)
    out = P.save(f, "projector-guillotine.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
