"""Concept figures for The Observatory of Sight (wing `sight`, verdigris) and
its basement companion The Two Judgments (wing `math`, violet).

Three figures:
  1. vision-emergent-wing.png  (verdigris), bird-wing & plane-wing crops land
     at nearby points in a sketched feature space; the compression-pressure
     mechanism annotated.
  2. vision-fusion.png         (verdigris), the SigLIP + DINOv2 fusion flow
     (the OpenVLA pattern) with a selection-heuristic side table.
  3. two-judgments.png         (violet, basement, PURE MATH labels only), softmax coupling a score vector into rival probabilities vs sigmoid+BCE
     giving each score its own independent yes/no.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_vision.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyArrowPatch, FancyBboxPatch, Polygon,
                                Circle, Rectangle, Ellipse)
import palace_fig as P


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


# ===========================================================================
# Figure 1, vision-emergent-wing.png  (verdigris)
# ===========================================================================
def fig_emergent_wing():
    WING = "verdigris"
    ACC = P.WING[WING]["accent"]   # bright teal
    WARM = P.WING[WING]["warm"]    # gold
    COOL = P.WING[WING]["cool"]    # muted teal

    f = plt.figure(figsize=(16.8, 8.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.02, 1.0], wspace=0.14,
                        left=0.035, right=0.975, top=0.80, bottom=0.075)

    P.suptitle(f, "How “wing” emerges without labels, "
                  "compression, not supervision", WING)
    f.text(0.5, 0.885,
           "A local crop must predict its global context. Two parts that share "
           "silhouette and context must predict the same whole, so the "
           "efficient code gives them one shared address.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- panel (a): two crops predicting the same global context ----------
    ax = f.add_subplot(gs[0, 0]); ax.set_facecolor(P.BG)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(P.GRID)
    ax.set_title("(a)  local crop  →  predict the whole scene",
                 color=P.INK, fontsize=15, pad=10)

    def crop_box(cx, cy, kind, label):
        w, h = 2.5, 2.0
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                     boxstyle="round,pad=0.05,rounding_size=0.12",
                     facecolor=P.PANEL, edgecolor=ACC, linewidth=1.8))
        if kind == "bird":
            # a feathered curved wing
            xs = np.linspace(-1.0, 1.0, 60)
            top = 0.30 + 0.55 * np.cos(xs * 1.2)
            bot = -0.10 - 0.10 * np.cos(xs * 1.4)
            poly = np.column_stack([np.r_[xs, xs[::-1]],
                                    np.r_[top, bot[::-1]]])
            poly = poly * [1.0, 1.0] + [cx, cy]
            ax.add_patch(Polygon(poly, closed=True, facecolor=COOL,
                                 edgecolor=P.INK, linewidth=1.2, alpha=0.9))
            for fx in np.linspace(-0.8, 0.85, 6):
                fy = 0.30 + 0.55 * np.cos(fx * 1.2)
                ax.plot([cx + fx, cx + fx], [cy - 0.05, cy + fy],
                        color=P.INK, lw=0.7, alpha=0.5)
        else:
            # a swept plane wing (triangle) with an engine pod
            poly = np.array([[-1.05, -0.15], [1.0, 0.15], [1.0, 0.55],
                             [-0.2, 0.55]]) + [cx, cy]
            ax.add_patch(Polygon(poly, closed=True, facecolor=WARM,
                                 edgecolor=P.INK, linewidth=1.2, alpha=0.9))
            ax.add_patch(Ellipse((cx + 0.35, cy - 0.05), 0.55, 0.28,
                         facecolor="#243342", edgecolor=P.INK, linewidth=1.0))
        ax.text(cx, cy - 1.35, label, color=P.INK, fontsize=12.5,
                ha="center", va="center", fontweight="bold")

    crop_box(2.0, 7.7, "bird", "a bird-wing crop")
    crop_box(2.0, 3.1, "plane", "a plane-wing crop")

    # the shared global-context target
    gx, gy = 7.4, 5.4
    ax.add_patch(FancyBboxPatch((gx - 2.3, gy - 2.35), 4.6, 4.7,
                 boxstyle="round,pad=0.08,rounding_size=0.2",
                 facecolor="#12202a", edgecolor=WARM, linewidth=2.0))
    # a sky with a small flying silhouette
    for yy, aa in [(1.4, 0.25), (0.7, 0.18)]:
        ax.plot([gx - 2.0, gx + 2.0], [gy + yy, gy + yy],
                color=COOL, lw=1.0, alpha=aa)
    ax.plot([gx - 0.9, gx, gx + 0.9], [gy + 0.15, gy + 0.55, gy + 0.15],
            color=P.INK, lw=2.4, solid_capstyle="round")
    ax.scatter([gx], [gy + 0.42], color=P.INK, s=30)
    ax.text(gx, gy + 2.0, "predicted global context",
            color=WARM, fontsize=12.5, ha="center", fontweight="bold")
    ax.text(gx, gy - 1.65,
            "elongated planar shape,\nattached to a body,\nagainst sky / in flight",
            color=P.INK, fontsize=11.5, ha="center", va="center")

    for cy in (7.7, 3.1):
        ax.add_patch(FancyArrowPatch((3.35, cy), (gx - 2.45, gy + (cy - 5.4) * 0.35),
                     arrowstyle="-|>", mutation_scale=20, color=ACC, lw=2.2,
                     connectionstyle="arc3,rad=%.2f" % (0.12 if cy > 5 else -0.12)))
    ax.text(4.95, 5.65, "must\npredict", color=ACC, fontsize=11.5,
            ha="center", va="center", fontweight="bold")

    # ---- panel (b): the sketched feature space ----------------------------
    ax2 = f.add_subplot(gs[0, 1]); P.style_ax(ax2, WING, grid=True)
    ax2.set_title("(b)  feature space: same context → same address",
                  color=P.INK, fontsize=15, pad=10)
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 10)
    ax2.set_xticks([]); ax2.set_yticks([])
    ax2.set_xlabel("feature dimension  →", fontsize=12)
    ax2.set_ylabel("feature dimension  →", fontsize=12)

    # the shared "wing" neighbourhood
    wx, wy = 6.8, 6.6
    ax2.add_patch(Circle((wx, wy), 1.55, facecolor=ACC, alpha=0.14,
                         edgecolor=ACC, linewidth=1.6, linestyle="--"))
    ax2.scatter([wx - 0.55], [wy + 0.35], s=210, color=COOL,
                edgecolor=P.INK, linewidth=1.2, zorder=5)
    ax2.scatter([wx + 0.6], [wy - 0.45], s=210, color=WARM,
                edgecolor=P.INK, linewidth=1.2, zorder=5)
    ax2.text(wx - 0.55, wy + 0.95, "bird\nwing", color=COOL, fontsize=11,
             ha="center", va="center", fontweight="bold")
    ax2.text(wx + 0.6, wy - 1.15, "plane\nwing", color=WARM, fontsize=11,
             ha="center", va="center", fontweight="bold")
    ax2.text(wx, wy + 2.05, "one shared code", color=ACC, fontsize=13,
             ha="center", fontweight="bold")

    # unrelated concepts scattered far away
    others = [(2.1, 2.3, "wheel"), (2.7, 7.6, "eye"),
              (7.9, 2.2, "leaf"), (1.7, 5.0, "face")]
    for ox, oy, name in others:
        ax2.scatter([ox], [oy], s=150, color=P.MUTED, edgecolor=P.INK,
                    linewidth=1.0, zorder=4, alpha=0.85)
        ax2.text(ox, oy - 0.75, name, color=P.MUTED, fontsize=10.5,
                 ha="center", va="center")

    ax2.annotate("keeping them apart\nwould waste capacity\nfor no gain",
                 xy=(wx - 1.4, wy - 1.0), xytext=(3.3, 4.0),
                 color=P.INK, fontsize=11.5, va="center", ha="center",
                 fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8,
                                 connectionstyle="arc3,rad=-0.2"))

    f.text(0.5, 0.028,
           "Honest caveat: nothing names these codes. They align with human "
           "categories only where visual statistics happen to, often, not always.",
           ha="center", color=P.MUTED, fontsize=11.5, style="italic")

    return P.save(f, "vision-emergent-wing.png")


# ===========================================================================
# Figure 2, vision-fusion.png  (verdigris)
# ===========================================================================
def fig_fusion():
    WING = "verdigris"
    ACC = P.WING[WING]["accent"]
    WARM = P.WING[WING]["warm"]
    COOL = P.WING[WING]["cool"]

    f = plt.figure(figsize=(17.0, 8.8))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.5, 1.0], wspace=0.10,
                        left=0.035, right=0.975, top=0.80, bottom=0.07)

    P.suptitle(f, "Two eyes, fused, the OpenVLA pattern", WING)
    f.text(0.5, 0.885,
           "Manipulation needs both “what is it” (semantic) and "
           "“where exactly is it” (spatial). Run both encoders and "
           "concatenate their features.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- left: the flow diagram -------------------------------------------
    ax = f.add_subplot(gs[0, 0]); ax.set_facecolor(P.BG)
    ax.set_xlim(0, 12); ax.set_ylim(0, 10)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(P.GRID)

    def box(cx, cy, w, h, title, sub, edge, sub_col=None):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                     boxstyle="round,pad=0.06,rounding_size=0.16",
                     facecolor=P.PANEL, edgecolor=edge, linewidth=2.0))
        ax.text(cx, cy + (0.28 if sub else 0.0), title, color=P.INK,
                fontsize=13.5, ha="center", va="center", fontweight="bold")
        if sub:
            ax.text(cx, cy - 0.42, sub, color=sub_col or P.MUTED,
                    fontsize=10.5, ha="center", va="center")

    def arrow(x0, y0, x1, y1, col=ACC, rad=0.0):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                     mutation_scale=20, color=col, lw=2.4,
                     connectionstyle="arc3,rad=%.2f" % rad))

    box(1.35, 5.0, 2.0, 1.6, "image", "", ACC)
    box(5.3, 7.5, 3.5, 1.7, "SigLIP", "semantic,\nlanguage-aligned", WARM, WARM)
    box(5.3, 2.5, 3.5, 1.7, "DINOv2", "spatial, dense,\nprecise", COOL, COOL)
    box(8.9, 5.0, 1.9, 1.5, "concat", "", ACC)
    box(11.0, 5.0, 1.9, 1.5, "projector", "", ACC)

    arrow(2.4, 5.35, 3.55, 7.2, WARM, 0.18)
    arrow(2.4, 4.65, 3.55, 2.8, COOL, -0.18)
    arrow(7.1, 7.2, 8.05, 5.55, WARM, 0.16)
    arrow(7.1, 2.8, 8.05, 4.45, COOL, -0.16)
    arrow(9.9, 5.0, 10.0, 5.0, ACC)

    # projector -> LLM (leaving the frame to the right)
    ax.add_patch(FancyArrowPatch((11.95, 5.0), (12.0, 5.0), arrowstyle="-|>",
                 mutation_scale=20, color=ACC, lw=2.4))
    ax.text(11.0, 3.75, "↓  to the LLM", color=ACC, fontsize=12.5,
            ha="center", fontweight="bold")
    ax.text(8.9, 6.15, "features joined\nside by side", color=P.MUTED,
            fontsize=10.5, ha="center", va="center")

    ax.set_title("image  →  SigLIP ⊕ DINOv2  →  concat  →  "
                 "projector  →  LLM", color=P.INK, fontsize=14.5, pad=12)

    # ---- right: the selection heuristic table -----------------------------
    ax2 = f.add_subplot(gs[0, 1]); ax2.set_facecolor(P.BG)
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 10)
    ax2.set_xticks([]); ax2.set_yticks([])
    for sp in ax2.spines.values():
        sp.set_color(P.GRID)
    ax2.set_title("Which eye do you need?", color=P.INK, fontsize=15, pad=12)

    rows = [
        ("language grounding / zero-shot", "SigLIP", WARM),
        ("dense spatial / depth / matching", "DINOv2", COOL),
        ("both (robotics, manipulation)", "fuse both", ACC),
        ("video / world models", "V-JEPA", P.MUTED),
        ("diffusion text encoder", "CLIP / T5", P.MUTED),
    ]
    y = 8.3
    dy = 1.55
    ax2.text(0.4, 9.2, "need", color=P.MUTED, fontsize=11.5,
             fontweight="bold")
    ax2.text(6.7, 9.2, "choose", color=P.MUTED, fontsize=11.5,
             fontweight="bold")
    for i, (need, pick, col) in enumerate(rows):
        yy = y - i * dy
        ax2.add_patch(FancyBboxPatch((0.2, yy - 0.62), 9.6, 1.2,
                      boxstyle="round,pad=0.02,rounding_size=0.1",
                      facecolor=(P.PANEL if i % 2 == 0 else "#101821"),
                      edgecolor=P.GRID, linewidth=1.0))
        ax2.text(0.5, yy, need, color=P.INK, fontsize=11.5, va="center")
        ax2.text(6.7, yy, pick, color=col, fontsize=12.5, va="center",
                 fontweight="bold")

    f.text(0.5, 0.028,
           "Nuance: semantic-vs-spatial is a strength gradient, not a hard "
           "boundary, SigLIP has some spatial signal; DINOv2's features "
           "are semantically structured, just not language-aligned.",
           ha="center", color=P.MUTED, fontsize=11.5, style="italic")

    return P.save(f, "vision-fusion.png")


# ===========================================================================
# Figure 3, two-judgments.png  (violet, BASEMENT, pure math only)
# ===========================================================================
def fig_two_judgments():
    WING = "violet"
    ACC = P.WING[WING]["accent"]   # lilac
    WARM = P.WING[WING]["warm"]    # gold
    COOL = P.WING[WING]["cool"]    # periwinkle

    f = plt.figure(figsize=(17.0, 8.8))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, wspace=0.14, left=0.055, right=0.965,
                        top=0.80, bottom=0.10)

    P.suptitle(f, "Two ways to turn scores into verdicts", WING)
    f.text(0.5, 0.885,
           "A relative judgment ranks rivals against each other; an absolute "
           "judgment asks each score, alone, a yes/no.",
           ha="center", color=P.MUTED, fontsize=13.5)

    scores = np.array([2.0, 1.0, 0.1])
    names = ["s₁", "s₂", "s₃"]

    # ---- left: softmax, coupled ------------------------------------------
    ax = f.add_subplot(gs[0, 0]); ax.set_facecolor(P.BG)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(P.GRID)
    ax.set_title("(a)  RELATIVE, softmax over rivals",
                 color=P.INK, fontsize=15.5, pad=10)

    ax.text(5.0, 9.05, r"$p_i \;=\; e^{\,s_i}\,/\,\sum_j e^{\,s_j}$",
            color=ACC, fontsize=17, ha="center", va="center")

    def prob_bars(base_x, base_y, sc, title_col, tag):
        e = np.exp(sc); p = e / e.sum()
        bw = 1.15
        for i, (val, nm) in enumerate(zip(p, names)):
            x = base_x + i * 1.55
            ax.add_patch(Rectangle((x, base_y), bw, val * 3.2,
                         facecolor=COOL if i else WARM, edgecolor=P.INK,
                         linewidth=1.0, alpha=0.92))
            ax.text(x + bw / 2, base_y + val * 3.2 + 0.28, "%.2f" % val,
                    color=P.INK, fontsize=12, ha="center", fontweight="bold")
            ax.text(x + bw / 2, base_y - 0.42, nm, color=P.MUTED,
                    fontsize=12, ha="center")
        ax.text(base_x + 2.4, base_y - 1.05, tag, color=title_col,
                fontsize=11.5, ha="center", fontweight="bold")
        return p

    ax.text(1.0, 6.65, "scores  →  exponentiate  →  normalise",
            color=P.INK, fontsize=12, fontweight="bold")
    p0 = prob_bars(0.9, 2.4, scores, P.MUTED,
                   "scores  (2.0, 1.0, 0.1)")

    # after nudging ONE score, EVERY probability moves
    scores2 = scores.copy(); scores2[2] += 1.6
    p1 = prob_bars(5.6, 2.4, scores2, WARM,
                   "raise only s₃  →  all three shift")

    ax.add_patch(FancyArrowPatch((4.35, 4.0), (5.45, 4.0), arrowstyle="-|>",
                 mutation_scale=20, color=WARM, lw=2.2))
    ax.text(5.0, 0.7,
            "always sums to 1, one winner;\n"
            "nudge any score and every other moves.",
            color=ACC, fontsize=12.5, fontweight="bold", ha="center",
            va="center")

    # ---- right: sigmoid + BCE, independent -------------------------------
    ax2 = f.add_subplot(gs[0, 1]); ax2.set_facecolor(P.BG)
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 10)
    ax2.set_xticks([]); ax2.set_yticks([])
    for sp in ax2.spines.values():
        sp.set_color(P.GRID)
    ax2.set_title("(b)  ABSOLUTE, a sigmoid gate per score",
                  color=P.INK, fontsize=15.5, pad=10)

    ax2.text(5.0, 9.05, r"$\sigma(s+b)=\dfrac{1}{1+e^{-(s+b)}}$",
             color=ACC, fontsize=16, ha="center", va="center")

    # a sigmoid curve with three scores read independently on it
    xs = np.linspace(-5, 5, 300)
    ys = 1 / (1 + np.exp(-xs))
    # map math coords into the panel: x in [0.8,9.2], y baseline raised so the
    # BCE box below has clear air
    def MX(x): return 0.8 + (x + 5) / 10 * 8.4
    def MY(y): return 2.55 + y * 4.5
    ax2.plot(MX(xs), MY(ys), color=ACC, lw=2.6)
    ax2.plot([MX(-5), MX(5)], [MY(0.5), MY(0.5)], color=P.GRID, lw=1.0, ls=":")
    ax2.plot([MX(0), MX(0)], [MY(0), MY(1)], color=P.GRID, lw=1.0, ls=":")
    ax2.text(MX(-4.4), MY(1.0) + 0.1, "yes (1)", color=P.MUTED, fontsize=10.5)
    ax2.text(MX(-4.9), MY(0.0) - 0.55, "no (0)", color=P.MUTED, fontsize=10.5)

    demo = [(-3.0, "s₁", WARM), (0.6, "s₂", COOL), (2.4, "s₃", COOL)]
    for sx, nm, col in demo:
        py = 1 / (1 + np.exp(-sx))
        ax2.plot([MX(sx), MX(sx)], [MY(0), MY(py)], color=col, lw=1.4, ls="--",
                 alpha=0.8)
        ax2.scatter([MX(sx)], [MY(py)], s=150, color=col, edgecolor=P.INK,
                    linewidth=1.1, zorder=6)
        ax2.text(MX(sx), MY(0) - 0.35, nm, color=P.MUTED, fontsize=12,
                 ha="center")
        ax2.text(MX(sx) + 0.15, MY(py) + 0.22, "%.2f" % py, color=col,
                 fontsize=11, ha="left", fontweight="bold")

    ax2.text(5.0, 7.7,
             "each score gets its own yes/no, no rivals, no sum-to-1",
             color=P.INK, fontsize=12, ha="center", fontweight="bold")

    # BCE box
    ax2.add_patch(FancyBboxPatch((0.7, 0.35), 8.6, 0.95,
                  boxstyle="round,pad=0.05,rounding_size=0.1",
                  facecolor=P.PANEL, edgecolor=ACC, linewidth=1.6))
    ax2.text(2.9, 0.83, r"$-\,[\,y\log p + (1-y)\log(1-p)\,]$",
             color=ACC, fontsize=14.5, ha="center", va="center")
    ax2.text(7.4, 0.83, "a learned bias b shifts\nthe default when yeses are rare",
             color=P.MUTED, fontsize=10.5, ha="center", va="center")

    return P.save(f, "two-judgments.png")


if __name__ == "__main__":
    print("wrote", fig_emergent_wing())
    print("wrote", fig_fusion())
    print("wrote", fig_two_judgments())
