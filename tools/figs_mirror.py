"""I-JEPA latent-prediction figure for the Mirror of Occlusion.

Run with:  ~/anaconda3/envs/lrm/bin/python tools/figs_mirror.py

ONE comprehensive figure, three panels:
  (a) Masked latent prediction schematic
  (b) EMA tracking curve (target = 0.996*target + 0.004*context)
  (c) Representation collapse vs healthy spread

All facts after I-JEPA (Assran et al., CVPR 2023).
"""
import sys
sys.path.insert(0, "tools")
import palace_fig as P

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D

WING = P.WING["emerald"]
ACCENT = WING["accent"]   # green
WARM = WING["warm"]       # gold
COOL = WING["cool"]       # teal
GRAY = "#5a6675"          # masked block color

rng = np.random.default_rng(7)

f = plt.figure(figsize=(20.0, 7.6))
f.patch.set_facecolor(P.BG)
# Three panels with comfortable spacing.
gs = f.add_gridspec(1, 3, left=0.035, right=0.985, top=0.84, bottom=0.07,
                    wspace=0.20, width_ratios=[1.18, 1.0, 1.06])

P.suptitle(f, "I-JEPA, Predicting in Latent Space (Assran et al., CVPR 2023)")
f.suptitle("I-JEPA, Predicting in Latent Space (Assran et al., CVPR 2023)",
           color=P.INK, fontsize=23, fontweight="bold", y=0.965)


# =====================================================================
# (a) Masked latent prediction schematic
# =====================================================================
axa = f.add_subplot(gs[0, 0])
axa.set_facecolor(P.BG)
axa.set_xlim(0, 10)
axa.set_ylim(0, 10)
axa.axis("off")
axa.set_title("(a)  Predict masked patches in LATENT space, never pixels",
              color=P.INK, fontsize=15, fontweight="bold", pad=12, loc="left")

# --- build a small "scene" as a grid of colored numpy blocks ---------
G = 6
# semantic-ish colored field (hues encode "what belongs")
scene = np.zeros((G, G, 3))
base = P.cmap("emer")
for i in range(G):
    for j in range(G):
        t = ((i * 0.6 + j * 0.4) / (G)) + 0.12 * rng.standard_normal()
        t = np.clip(0.18 + 0.7 * (t % 1.0), 0, 1)
        scene[i, j] = base(t)[:3]

# masked target blocks (gray) -- several
masked = {(1, 1), (1, 4), (3, 2), (4, 4), (2, 3)}

def draw_grid(ax, x0, y0, w, show_masked_gray):
    cell = w / G
    for i in range(G):
        for j in range(G):
            yy = y0 + (G - 1 - i) * cell
            xx = x0 + j * cell
            if (i, j) in masked and show_masked_gray:
                ax.add_patch(Rectangle((xx, yy), cell, cell,
                             facecolor=GRAY, edgecolor=P.BG, linewidth=1.4))
                ax.plot([xx, xx + cell], [yy, yy + cell], color="#3a434f", lw=1.0)
                ax.plot([xx, xx + cell], [yy + cell, yy], color="#3a434f", lw=1.0)
            else:
                ax.add_patch(Rectangle((xx, yy), cell, cell,
                             facecolor=scene[i, j], edgecolor=P.BG, linewidth=1.4))
    ax.add_patch(Rectangle((x0, y0), w, w, fill=False,
                 edgecolor=P.GRID, linewidth=1.5))

# CONTEXT image (top-left): visible context patches, targets masked gray
draw_grid(axa, 0.3, 6.6, 2.7, show_masked_gray=True)
axa.text(1.65, 9.65, "Visible context", ha="center", va="bottom",
         color=ACCENT, fontsize=12, fontweight="bold")
axa.text(1.65, 6.35, "(masked = gray)", ha="center", va="top",
         color=P.MUTED, fontsize=9.5)

# FULL image (bottom-left): whole image, nothing masked
draw_grid(axa, 0.3, 0.5, 2.7, show_masked_gray=False)
axa.text(1.65, 0.25, "Full image (seen whole)", ha="center", va="top",
         color=WARM, fontsize=12, fontweight="bold")

# --- boxes for encoders / predictor ----------------------------------
def box(ax, cx, cy, w, h, label, color, sub=None, fc=None):
    fc = fc if fc else P.PANEL
    b = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                       boxstyle="round,pad=0.06,rounding_size=0.14",
                       facecolor=fc, edgecolor=color, linewidth=2.2)
    ax.add_patch(b)
    yo = 0.18 if sub else 0
    ax.text(cx, cy + yo, label, ha="center", va="center",
            color=P.INK, fontsize=11.5, fontweight="bold")
    if sub:
        ax.text(cx, cy - 0.30, sub, ha="center", va="center",
                color=P.MUTED, fontsize=8.8)
    return b

def arrow(ax, p0, p1, color, lw=2.2, style="-", rad=0.0):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=18,
                        color=color, lw=lw, linestyle=style,
                        connectionstyle=f"arc3,rad={rad}",
                        shrinkA=2, shrinkB=2)
    ax.add_patch(a)

# Context branch (top)
ce = box(axa, 5.1, 8.0, 1.7, 1.05, "Context", ACCENT, sub="Encoder")
pr = box(axa, 7.6, 8.0, 1.7, 1.05, "Predictor", WARM)
zh = box(axa, 9.45, 8.0, 0.95, 1.05, "ẑ", ACCENT, fc="#1c3b2e")
# Target branch (bottom)
te = box(axa, 5.1, 1.7, 1.7, 1.05, "EMA Target", WARM, sub="Encoder · no grad")
zt = box(axa, 9.45, 1.7, 0.95, 1.05, "z", WARM, fc="#4a3417")

# mask position tokens feeding predictor
mt = box(axa, 7.0, 5.5, 2.05, 0.95, "Mask position", "#b9a0e0",
         sub="tokens (where?)", fc="#241b35")

# arrows context branch
arrow(axa, (3.1, 8.0), (4.22, 8.0), ACCENT)         # ctx img -> CE
arrow(axa, (5.98, 8.0), (6.72, 8.0), ACCENT)        # CE -> predictor
arrow(axa, (7.85, 5.10), (7.62, 6.95), "#b9a0e0")   # mask tokens -> predictor
arrow(axa, (8.48, 8.0), (8.95, 8.0), WARM)          # predictor -> zhat
# arrows target branch
arrow(axa, (3.1, 1.7), (4.22, 1.7), WARM)           # full img -> TE
arrow(axa, (5.98, 1.7), (8.95, 1.7), WARM)          # TE -> z

axa.text(4.6, 8.6, "visible\npatches", ha="center", va="bottom",
         color=P.MUTED, fontsize=8.5)
axa.text(9.45, 8.95, "PREDICTED\nlatent", ha="center", va="bottom",
         color=ACCENT, fontsize=10, fontweight="bold")
axa.text(9.45, 0.78, "TARGET\nlatent", ha="center", va="top",
         color=WARM, fontsize=10, fontweight="bold")

# the comparison: squared L2 in latent space
# red arrows from predicted latent (top) and target latent (bottom) into loss box
arrow(axa, (9.45, 7.42), (9.45, 5.65), "#ff8f8f", lw=2.4, rad=0.0)   # zhat down
arrow(axa, (9.45, 2.30), (9.45, 4.35), "#ff8f8f", lw=2.4, rad=0.0)   # z up
axa.add_patch(FancyBboxPatch((8.15, 4.42), 2.55, 1.18,
              boxstyle="round,pad=0.05,rounding_size=0.12",
              facecolor="#3a1f22", edgecolor="#ff8f8f", linewidth=2.0))
axa.text(9.42, 5.20, "loss = ‖ẑ − z‖²", ha="center", va="center",
         color="#ffd0d0", fontsize=12.5, fontweight="bold")
axa.text(9.42, 4.70, "latent vs latent", ha="center", va="center",
         color="#ff8f8f", fontsize=9.0)

# EMA drift annotation: context encoder -> target encoder
arrow(axa, (5.1, 7.46), (5.1, 2.26), COOL, lw=2.0, style=(0, (4, 3)))
axa.text(4.62, 4.85, "EMA drift\n0.996 / 0.004", ha="right", va="center",
         color=COOL, fontsize=9.5, rotation=90)


# =====================================================================
# (b) EMA tracking curve
# =====================================================================
axb = f.add_subplot(gs[0, 1])
P.style_ax(axb, "emerald")
axb.set_title("(b)  EMA target lags the context encoder",
              color=P.INK, fontsize=15, fontweight="bold", pad=12, loc="left")

steps = np.arange(0, 600)
# "context" weight: a learning trajectory that rises and gets jittery
true = 1.0 - np.exp(-steps / 140.0)
context = true + 0.05 * rng.standard_normal(steps.size) * np.exp(-steps / 600)
context += 0.035 * rng.standard_normal(steps.size)   # persistent jitter

# target tracks via EMA each step
m = 0.996
target = np.empty_like(context)
target[0] = 0.0
for k in range(1, steps.size):
    target[k] = m * target[k - 1] + (1 - m) * context[k]

axb.plot(steps, context, color=ACCENT, lw=1.3, alpha=0.85,
         label="Context encoder (trained, jittery)")
axb.plot(steps, target, color=WARM, lw=3.0,
         label="EMA target (smooth, lagging)")
axb.set_xlabel("training step", fontsize=12.5)
axb.set_ylabel("weight value (illustrative)", fontsize=12.5)
axb.set_xlim(0, 599)
axb.set_ylim(-0.08, 1.18)
axb.tick_params(labelsize=11)
leg = axb.legend(loc="lower right", fontsize=10.5, frameon=True,
                 facecolor=P.PANEL, edgecolor=P.GRID)
for t in leg.get_texts():
    t.set_color(P.INK)

# the update rule, boxed
axb.text(0.035, 0.965,
         "target ← 0.996·target + 0.004·context",
         transform=axb.transAxes, ha="left", va="top",
         color=P.INK, fontsize=12, fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.4", facecolor=P.PANEL,
                   edgecolor=COOL, linewidth=1.6))
axb.annotate("target only follows, never learns",
             xy=(430, target[430]), xytext=(300, 0.30),
             color=WARM, fontsize=10.5,
             arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.6))


# =====================================================================
# (c) Representation collapse vs healthy spread
# =====================================================================
axc = f.add_subplot(gs[0, 2])
P.style_ax(axc, "emerald", grid=True)
axc.set_title("(c)  Asymmetry forbids representation collapse",
              color=P.INK, fontsize=15, fontweight="bold", pad=12, loc="left")
axc.set_xlim(0, 10)
axc.set_ylim(0, 10)
axc.set_xticks([]); axc.set_yticks([])
axc.set_xlabel("embedding dim 1", fontsize=12)
axc.set_ylabel("embedding dim 2", fontsize=12)

# divide into two sub-regions (left=collapsed, right=healthy)
axc.axvline(5.0, color=P.GRID, lw=1.4)

# LEFT: collapsed -- all points at one spot
cx, cy = 2.5, 5.4
cl = cx + 0.06 * rng.standard_normal(120)
cly = cy + 0.06 * rng.standard_normal(120)
axc.scatter(cl, cly, s=26, color="#ff8f8f", alpha=0.55, edgecolors="none")
axc.scatter([cx], [cy], s=140, color="#ff8f8f", edgecolors=P.INK, linewidths=1.0, zorder=5)
axc.text(2.5, 8.7, "COLLAPSED", ha="center", color="#ff8f8f",
         fontsize=12.5, fontweight="bold")
axc.text(2.5, 8.05, "all inputs → one point", ha="center",
         color=P.MUTED, fontsize=9.8)
axc.text(2.5, 3.0, "zero loss\nzero information", ha="center", va="top",
         color="#ff8f8f", fontsize=10.5, fontweight="bold")

# RIGHT: healthy spread -- a few clusters
centers = [(6.6, 6.8), (8.4, 5.4), (7.0, 3.2), (8.6, 7.8)]
cols = [ACCENT, WARM, COOL, "#b9a0e0"]
for (mx, my), col in zip(centers, cols):
    px = mx + 0.55 * rng.standard_normal(34)
    py = my + 0.55 * rng.standard_normal(34)
    axc.scatter(px, py, s=26, color=col, alpha=0.8, edgecolors="none")
axc.text(7.6, 8.7, "HEALTHY SPREAD", ha="center", color=ACCENT,
         fontsize=12.5, fontweight="bold")
axc.text(7.6, 8.05, "distinct inputs → distinct codes", ha="center",
         color=P.MUTED, fontsize=9.8)

# bottom annotation spanning the asymmetry explanation
axc.add_patch(FancyBboxPatch((0.4, 0.35), 9.2, 1.55,
              boxstyle="round,pad=0.05,rounding_size=0.12",
              facecolor=P.PANEL, edgecolor=COOL, linewidth=1.6))
axc.text(5.0, 1.13,
         "EMA target + stop-gradient asymmetry: only the context encoder learns;\n"
         "the target cannot be optimized, so the two cannot collude into a blank page.",
         ha="center", va="center", color=P.INK, fontsize=10.2)

out = P.save(f, "ijepa-latent-prediction.png")
print("SAVED", out)
