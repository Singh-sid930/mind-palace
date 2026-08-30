"""Concept figures for The Observatory of Sight (wing `sight`, verdigris), the objective-by-objective walk through the contrastive & self-supervised
losses. Companion to tools/figs_vision.py (which draws the emergent-wing,
fusion, and two-judgments panels).

Three figures, all verdigris:
  1. vision-clip-matrix.png, CLIP's N×N similarity matrix, bright diagonal,
     one row highlighted showing softmax competition + the batch-coupling
     consequence (all-gather, ~32K).
  2. vision-siglip-loss.png, the report's worked example as a 3-panel walk:
     sims → ×t+b logits → sigmoid+BCE per cell (exact numbers, t=10 b=−5).
  3. vision-dino-distill.png. DINO self-distillation: local-crop student vs
     EMA global-crop teacher, centering+sharpening balance, and a
     collapsed-vs-healthy feature-spread inset.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_encoders.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from matplotlib.colors import LinearSegmentedColormap
import palace_fig as P

WING = "verdigris"
ACC = P.WING[WING]["accent"]   # bright teal  #7ff2d8
WARM = P.WING[WING]["warm"]    # gold         #d8b25a
COOL = P.WING[WING]["cool"]    # muted teal   #6fb8a8


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# diverging teal map for similarities/logits: dark-cold -> panel -> bright teal
TEAL = LinearSegmentedColormap.from_list(
    "teal", ["#12202a", "#1c3b3a", "#2f6f66", "#4fb39c", "#7ff2d8", "#e9fff8"])
# sequential warm map for probability/loss magnitude (small=dark, large=hot)
LOSS = LinearSegmentedColormap.from_list(
    "loss", ["#12202a", "#3a2f1e", "#7a5a2a", "#d8b25a", "#ffe6a6"])


def annot_heat(ax, M, cmap, vmin, vmax, fmt="{:+.2f}", diag_box=True,
               sub=None, subfmt="{:.3f}", txtsize=15, subsize=11.5):
    """Annotated N×N heatmap; `sub` overlays a second value per cell."""
    n = M.shape[0]
    ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal")
    thresh = vmin + 0.62 * (vmax - vmin)
    for i in range(n):
        for j in range(n):
            val = M[i, j]
            tc = "#0e131b" if val >= thresh else P.INK
            if sub is None:
                ax.text(j, i, fmt.format(val), ha="center", va="center",
                        color=tc, fontsize=txtsize, fontweight="bold")
            else:
                ax.text(j, i - 0.17, fmt.format(val), ha="center", va="center",
                        color=tc, fontsize=txtsize, fontweight="bold")
                ax.text(j, i + 0.25, subfmt.format(sub[i, j]), ha="center",
                        va="center", color=tc, fontsize=subsize)
            if diag_box and i == j:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                       edgecolor=ACC, lw=3.0, zorder=6))
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, labelsize=12.5, colors=P.MUTED)


# ===========================================================================
# 1) CLIP, N×N similarity matrix, softmax competition, batch coupling
# ===========================================================================
def fig_clip_matrix():
    N = 6
    rng = np.random.default_rng(7)
    S = rng.uniform(-0.12, 0.24, (N, N))
    np.fill_diagonal(S, rng.uniform(0.74, 0.9, N))
    hi = 2                                       # highlighted image row (img3)
    S[hi] = np.array([0.10, 0.18, 0.82, 0.05, 0.22, -0.08])  # legible contest

    tau = 5.0                                    # illustrative temperature
    probs = np.exp(S[hi] * tau); probs /= probs.sum()

    f = plt.figure(figsize=(16.8, 8.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.16, 1.0],
                        left=0.06, right=0.975, top=0.79, bottom=0.16,
                        wspace=0.24)

    P.suptitle(f, "CLIP, one shared space, and every caption in the batch "
                  "is a rival", wing=WING)
    f.text(0.5, 0.885,
           "Both encoders project into one space; a batch of N image, caption "
           "pairs makes an N×N cosine-similarity matrix. The objective: the "
           "diagonal high, everything else low.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- (a) the matrix -------------------------------------------------
    ax = f.add_subplot(gs[0, 0])
    ax.set_facecolor(P.PANEL)
    annot_heat(ax, S, TEAL, -0.25, 0.9, fmt="{:+.2f}", txtsize=14.5)
    ax.set_xticklabels(["cap%d" % (k + 1) for k in range(N)])
    ax.set_yticklabels(["img%d" % (k + 1) for k in range(N)])
    ax.set_title("(a)  cosine similarities. The bright diagonal is the "
                 "correct pairs", color=P.INK, fontsize=15, pad=12)
    ax.add_patch(Rectangle((-0.5, hi - 0.5), N, 1, fill=False,
                           edgecolor=WARM, lw=3.4, zorder=7))
    # label the highlighted row from the top of the gutter (clear of panel b's
    # vertically-centered y-axis label)
    ax.annotate("softmax runs\nacross this row",
                xy=(5.55, hi), xycoords="data",
                xytext=(1.02, 0.92), textcoords="axes fraction",
                color=WARM, fontsize=12.5, fontweight="bold",
                ha="left", va="center", annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.8,
                                connectionstyle="arc3,rad=-0.4"))

    # ---- (b) softmax competition on the highlighted row -----------------
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING)
    x = np.arange(N)
    cols = [WARM if k == hi else COOL for k in range(N)]
    bars = ax.bar(x, probs, 0.66, color=cols, edgecolor=P.GRID, zorder=3)
    for k, b in enumerate(bars):
        ax.annotate("{:.2f}".format(b.get_height()),
                    (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha="center",
                    color=(WARM if k == hi else P.INK), fontsize=13,
                    fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(["cap%d" % (k + 1) for k in range(N)], fontsize=12)
    ax.set_ylim(0, 1.04)
    ax.set_ylabel("softmax probability  (row img3)", fontsize=13)
    ax.set_title("(b)  that one row → a single competition", color=P.INK,
                 fontsize=15, pad=12)
    ax.text(0.5, 0.96,
            "softmax(similarity × temperature), cross-entropy pushes "
            "cap3 → 1",
            transform=ax.transAxes, ha="center", va="top", color=ACC,
            fontsize=12.5, fontweight="bold")
    ax.text(0.97, 0.55,
            "move ANY score and\nEVERY bar shifts:\nthe scores are coupled",
            transform=ax.transAxes, ha="right", va="center", color=P.MUTED,
            fontsize=11.8, style="italic")

    # ---- batch-coupling banner -----------------------------------------
    f.text(0.5, 0.05,
           "The softmax denominator sums the whole row → the batch is "
           "coupled → a costly all-gather across GPUs, and more negatives = "
           "better signal, so CLIP trains at batches of ~32K.",
           ha="center", va="center", color=P.INK, fontsize=13.2,
           fontweight="bold",
           bbox=dict(boxstyle="round,pad=0.6", facecolor="#15242a",
                     edgecolor=ACC, linewidth=1.6))
    return P.save(f, "vision-clip-matrix.png")


# ===========================================================================
# 2) SigLIP, worked 3-panel walk with the report's exact numbers
# ===========================================================================
def fig_siglip_loss():
    sims = np.array([[0.82, 0.15, -0.20],
                     [0.10, 0.75, 0.05],
                     [-0.05, 0.22, 0.68]])
    t, b = 10.0, -5.0
    logits = sims * t + b
    probs = sigmoid(logits)
    labels = np.eye(3)
    eps = 1e-12
    bce = -(labels * np.log(probs + eps) + (1 - labels) * np.log(1 - probs + eps))

    f = plt.figure(figsize=(18.8, 8.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 3, left=0.045, right=0.985, top=0.78, bottom=0.19,
                        wspace=0.22)

    P.suptitle(f, "SigLIP. One change: every cell is judged on its own",
               wing=WING)
    f.text(0.5, 0.885,
           "The same N×N matrix, but no row-wise competition. Each cell asks "
           "“do these two match?” and answers alone, sigmoid + binary "
           "cross-entropy, per cell.",
           ha="center", color=P.MUTED, fontsize=13.5)

    labs = ["cap1", "cap2", "cap3"]
    rows = ["img1", "img2", "img3"]

    # ---- (a) similarities ----------------------------------------------
    ax = f.add_subplot(gs[0, 0])
    annot_heat(ax, sims, TEAL, -0.3, 0.9, fmt="{:+.2f}", txtsize=17)
    ax.set_xticklabels(labs); ax.set_yticklabels(rows)
    ax.set_title("(a)  cosine similarity", color=P.INK, fontsize=15.5, pad=10)
    ax.text(0.5, -0.13, "L2-normalized embeddings → sim ∈ [−1, 1]",
            transform=ax.transAxes, ha="center", va="top", color=P.MUTED,
            fontsize=12)

    # ---- (b) logits = sim × t + b --------------------------------------
    ax = f.add_subplot(gs[0, 1])
    annot_heat(ax, logits, TEAL, -7.5, 4.0, fmt="{:+.2f}", txtsize=17)
    ax.set_xticklabels(labs); ax.set_yticklabels(rows)
    ax.set_title("(b)  logit = sim × t + b", color=P.INK, fontsize=15.5,
                 pad=10)
    ax.text(0.5, -0.13,
            "learned scalars  t = 10,  b = −5   (b < 0: most pairs are "
            "non-matches)",
            transform=ax.transAxes, ha="center", va="top", color=WARM,
            fontsize=12, fontweight="bold")

    # ---- (c) sigmoid → prob, then BCE ----------------------------------
    ax = f.add_subplot(gs[0, 2])
    annot_heat(ax, probs, LOSS, 0.0, 1.0, fmt="{:.3f}", sub=bce,
               subfmt="BCE {:.3f}", txtsize=15, subsize=11.5)
    ax.set_xticklabels(labs); ax.set_yticklabels(rows)
    ax.set_title("(c)  sigmoid(logit) → p,  then BCE", color=P.INK,
                 fontsize=15.5, pad=10)
    ax.text(0.5, -0.13,
            "label 1 on the diagonal, 0 elsewhere, then average all N² cells",
            transform=ax.transAxes, ha="center", va="top", color=P.MUTED,
            fontsize=12)

    # ---- the canonical img1 chain, called out along the bottom ---------
    f.text(0.5, 0.06,
           "Row img1, cell by cell:    0.82 → 3.20 → σ = 0.961 → BCE 0.040"
           "      •      0.15 → −3.50 → σ = 0.029 → BCE 0.030"
           "      •      −0.20 → −7.00 → σ = 0.001 → BCE 0.001",
           ha="center", va="center", color=P.INK, fontsize=13.2,
           fontweight="bold",
           bbox=dict(boxstyle="round,pad=0.55", facecolor="#15242a",
                     edgecolor=ACC, linewidth=1.6))
    return P.save(f, "vision-siglip-loss.png")


# ===========================================================================
# 3) DINO, self-distillation schematic + collapse-vs-healthy inset
# ===========================================================================
def _box(ax, xy, w, h, text, fc, ec, fs=13, tc=None, lw=2.0):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.03",
                 facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc or P.INK, fontsize=fs, fontweight="bold", zorder=4)


def _arrow(ax, a, b, color, lw=2.4, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=18,
                 color=color, lw=lw, linestyle=ls,
                 connectionstyle="arc3,rad=%s" % rad, zorder=2))


def fig_dino_distill():
    f = plt.figure(figsize=(17.4, 8.6))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(1, 2, width_ratios=[1.6, 1.0],
                        left=0.025, right=0.978, top=0.79, bottom=0.10,
                        wspace=0.11)

    P.suptitle(f, "DINO. Two views must agree, without collapsing to a "
                  "constant", wing=WING)
    f.text(0.5, 0.885,
           "No labels, no captions. One image, two crops. The local-crop "
           "student must predict what the global-crop teacher sees.",
           ha="center", color=P.MUTED, fontsize=13.5)

    # ---- (a) the self-distillation schematic ---------------------------
    ax = f.add_subplot(gs[0, 0])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_facecolor(P.BG)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(P.GRID)

    # source image
    _box(ax, (0.25, 4.3), 1.5, 1.3, "one\nimage", "#15242a", P.MUTED,
         fs=13, tc=P.INK)

    # crops
    _box(ax, (2.25, 6.85), 1.85, 1.1, "local\ncrops", "#1a2f2a", COOL, fs=12.5)
    _box(ax, (2.25, 2.05), 1.85, 1.1, "global\ncrops", "#2a2415", WARM, fs=12.5)
    _arrow(ax, (1.75, 5.35), (2.25, 7.0), COOL, rad=-0.25)
    _arrow(ax, (1.75, 4.55), (2.25, 2.9), WARM, rad=0.25)

    # student (top) / teacher (bottom), a clear vertical channel between them
    _box(ax, (4.6, 6.55), 2.5, 1.5, "STUDENT\n(gradient-trained)",
         "#173a34", ACC, fs=12.5, tc=ACC)
    _box(ax, (4.6, 1.95), 2.5, 1.5, "TEACHER\n(EMA of student,\nno gradients)",
         "#33291a", WARM, fs=11.5, tc=WARM)
    _arrow(ax, (4.1, 7.4), (4.6, 7.35), COOL)
    _arrow(ax, (4.1, 2.6), (4.6, 2.65), WARM)

    # EMA weight copy (teacher <- student), dashed, runs down the clear channel
    _arrow(ax, (5.85, 6.55), (5.85, 3.45), P.MUTED, lw=1.8, ls="--")
    ax.text(6.05, 5.0, "EMA weight-copy\n(teacher ← student)", color=P.MUTED,
            fontsize=10.5, va="center", ha="left", style="italic")

    # centering + sharpening transforms the teacher output
    _box(ax, (7.55, 1.95), 2.0, 1.5, "center +\nsharpen", "#2a1f33", "#d2a8ff",
         fs=12, tc="#d2a8ff")
    _arrow(ax, (7.1, 2.7), (7.55, 2.7), WARM)

    # the match objective sits at the right; student & processed-teacher meet
    _box(ax, (7.5, 4.9), 2.2, 1.4, "match\n(cross-entropy)", "#15242a",
         ACC, fs=12.5, tc=P.INK)
    _arrow(ax, (7.1, 6.95), (7.55, 6.05), ACC, rad=-0.2)          # student → match
    _arrow(ax, (8.55, 3.45), (8.55, 4.9), "#d2a8ff")             # target → match
    ax.text(8.72, 4.15, "stable\ntarget", color="#d2a8ff", fontsize=10.5,
            va="center", ha="left", style="italic")

    ax.set_title("(a)  self-distillation: student predicts the EMA teacher",
                 color=P.INK, fontsize=15, pad=8, loc="left")

    ax.text(0.02, -0.015,
            "Centering subtracts a running mean (spreads the output); "
            "sharpening uses a low teacher temperature (concentrates it).\n"
            "Neither alone works. The pair is what keeps every view from "
            "mapping to the same constant vector.",
            transform=ax.transAxes, ha="left", va="top", color=P.MUTED,
            fontsize=11.5)

    # ---- (b) collapsed vs healthy feature spread -----------------------
    ax = f.add_subplot(gs[0, 1]); ax.set_facecolor(P.PANEL)
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_color(P.GRID)
    rng = np.random.default_rng(3)
    # healthy: spread cloud
    ang = rng.uniform(0, 2 * np.pi, 90)
    rad = rng.uniform(0.35, 1.0, 90)
    hx, hy = 0.0 + rad * np.cos(ang), 2.1 + rad * np.sin(ang) * 0.85
    ax.scatter(hx, hy, s=34, color=ACC, edgecolor="#0e131b", linewidth=0.4,
               zorder=3, alpha=0.95)
    ax.text(0.0, 3.6, "healthy: features spread", color=ACC, fontsize=13,
            fontweight="bold", ha="center")
    ax.text(0.0, 0.98, "many directions used\n→ useful representation",
            color=P.MUTED, fontsize=11, ha="center", va="top")

    # collapsed: all points at one spot
    cx = rng.normal(0.0, 0.05, 90)
    cy = rng.normal(-2.1, 0.05, 90)
    ax.scatter(cx, cy, s=34, color=WARM, edgecolor="#0e131b", linewidth=0.4,
               zorder=3, alpha=0.9)
    ax.text(0.0, -1.05, "collapsed: one constant point", color=WARM,
            fontsize=13, fontweight="bold", ha="center")
    ax.text(0.0, -2.75, "loss = 0, but every image\nlooks identical → useless",
            color=P.MUTED, fontsize=11, ha="center", va="top")

    ax.axhline(0.0, color=P.GRID, lw=1.0, ls=":")
    ax.set_xlim(-1.7, 1.7); ax.set_ylim(-3.5, 4.15)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(b)  the collapse that this pair prevents", color=P.INK,
                 fontsize=14.5, pad=8)

    return P.save(f, "vision-dino-distill.png")


if __name__ == "__main__":
    print("wrote", fig_clip_matrix())
    print("wrote", fig_siglip_loss())
    print("wrote", fig_dino_distill())
