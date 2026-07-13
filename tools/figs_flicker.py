"""Concept figure for The Hall of Flickering Frames (video wing, silver).

Panel (a): naive per-frame vs joint denoising — independent frames flicker
           (blob jitters in position/colour), jointly denoised frames stay put.
Panel (b): the data-shape gain — image tensor (H,W,C) vs video tensor
           (T,H,W,C) as frames stacked along a new T axis.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_flicker.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import palace_fig as P

WING = "silver"
ACC = P.WING[WING]["accent"]    # cool silver
WARM = P.WING[WING]["warm"]     # gold
COOL = P.WING[WING]["cool"]     # moonlit blue
FLICKER = "#e08a8a"             # warning red for the incoherent row


def frame_box(ax, x, y, s=0.86, edge=P.GRID, lw=1.4):
    """Draw a frame's border as a square of side s centred at (x+0.5, y+0.5)."""
    ax.add_patch(Rectangle((x + (1 - s) / 2, y + (1 - s) / 2), s, s,
                           fill=True, facecolor="#0b1017", edgecolor=edge,
                           lw=lw, zorder=2))


def main():
    f = plt.figure(figsize=(14.5, 9.4))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 1, height_ratios=[1.05, 1.0], hspace=0.34,
                        left=0.055, right=0.965, top=0.835, bottom=0.085)

    P.suptitle(f, "Scaling Diffusion to Video  —  denoise the frames JOINTLY",
               WING)
    f.text(0.5, 0.905,
           "The framework is unchanged; only the data shape grows a time axis.",
           ha="center", color=P.MUTED, fontsize=14)

    # =====================================================================
    # (a) independent (flicker) vs joint (consistent) frame strips
    # =====================================================================
    ax = f.add_subplot(gs[0]); P.style_ax(ax, WING, grid=False)
    ax.set_xticks([]); ax.set_yticks([])
    N = 6
    ax.set_xlim(-1.55, N + 1.75)
    ax.set_ylim(-0.30, 2.30)
    ax.set_aspect("equal")
    ax.set_title("(a)  Independent per-frame denoising flickers; "
                 "joint denoising stays consistent",
                 color=P.INK, fontsize=15, pad=10)

    rng = np.random.default_rng(3)
    # a "true" resting spot for the subject
    base_cx, base_cy = 0.5, 0.52
    joint_color = COOL

    # top row: JOINT (row y = 1.15), bottom row: INDEPENDENT (row y = 0.05)
    y_joint, y_indep = 1.20, 0.05
    indep_colors = [COOL, "#c9a15a", "#7fb0d0", "#d99a9a", "#8fd0b0", "#b0a0d0"]

    for i in range(N):
        x = float(i)
        # --- joint row: same blob, same colour, gentle intended drift ---
        frame_box(ax, x, y_joint)
        cx = base_cx + 0.05 * i          # smooth, intended motion
        cy = base_cy
        ax.add_patch(Circle((x + cx, y_joint + cy), 0.17, facecolor=joint_color,
                            edgecolor="white", lw=0.8, zorder=3))

        # --- independent row: blob jitters in place AND colour ---
        frame_box(ax, x, y_indep)
        jx = base_cx + 0.05 * i + rng.uniform(-0.22, 0.22)
        jy = base_cy + rng.uniform(-0.20, 0.20)
        r = 0.17 + rng.uniform(-0.05, 0.05)
        ax.add_patch(Circle((x + jx, y_indep + jy), r, facecolor=indep_colors[i],
                            edgecolor="white", lw=0.8, zorder=3))
        ax.text(x + 0.5, y_indep - 0.17, f"frame {i+1}", ha="center",
                va="top", color=P.MUTED, fontsize=10.5)

    # row labels on the left
    ax.text(-0.30, y_joint + 0.5, "JOINT\ndenoising",
            ha="right", va="center", color=ACC, fontsize=12.5,
            fontweight="bold", linespacing=1.3)
    ax.text(-0.30, y_indep + 0.5, "INDEPENDENT\nper frame",
            ha="right", va="center", color=FLICKER, fontsize=12.5,
            fontweight="bold", linespacing=1.3)

    # verdict tags on the right
    ax.text(N + 0.18, y_joint + 0.5, "temporally\nconsistent",
            ha="left", va="center", color=ACC, fontsize=12,
            fontweight="bold", linespacing=1.3)
    ax.text(N + 0.18, y_indep + 0.5, "FLICKER\n(jitter +\ncolour drift)",
            ha="left", va="center", color=FLICKER, fontsize=12,
            fontweight="bold", linespacing=1.3)

    # a faint guide line through the joint blobs to show the intended path
    xs = [i + base_cx + 0.05 * i for i in range(N)]
    ys = [y_joint + base_cy for _ in range(N)]
    ax.plot(xs, ys, color=ACC, lw=1.0, ls=":", alpha=0.5, zorder=1)

    # =====================================================================
    # (b) image tensor (H,W,C) vs video tensor (T,H,W,C)
    # =====================================================================
    ax2 = f.add_subplot(gs[1]); P.style_ax(ax2, WING, grid=False)
    ax2.set_xticks([]); ax2.set_yticks([])
    ax2.set_xlim(0, 13.0)
    ax2.set_ylim(0, 5.6)
    ax2.set_aspect("equal")
    ax2.set_title("(b)  The whole story is one extra axis:  image (H,W,C)  "
                  "→  video (T,H,W,C)", color=P.INK, fontsize=15, pad=12)

    # --- left: a single image tensor, one square with depth for C ---
    def cube_face(ax, x, y, w, h, face, edge=P.GRID, lw=1.6, z=3):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge,
                               lw=lw, zorder=z))

    ix, iy, iw = 1.2, 1.5, 1.9
    dep = 0.40
    # channel depth (back faces)
    cube_face(ax2, ix + dep, iy + dep, iw, iw, "#16202c", z=2)
    ax2.plot([ix, ix + dep], [iy + iw, iy + iw + dep], color=P.GRID, lw=1.4, zorder=2)
    ax2.plot([ix + iw, ix + iw + dep], [iy + iw, iy + iw + dep], color=P.GRID, lw=1.4, zorder=2)
    ax2.plot([ix + iw, ix + iw + dep], [iy, iy + dep], color=P.GRID, lw=1.4, zorder=2)
    cube_face(ax2, ix, iy, iw, iw, "#1c2836", edge=ACC, z=3)
    ax2.text(ix + iw / 2, iy + iw / 2, "1 image", ha="center", va="center",
             color=P.INK, fontsize=13, fontweight="bold")
    ax2.text(ix + iw / 2 + dep / 2, iy + iw + dep + 0.30, "IMAGE",
             ha="center", va="bottom", color=P.MUTED, fontsize=12.5,
             fontweight="bold")
    ax2.text(ix + iw / 2 + dep / 2, iy - 0.35, "(H, W, C)", ha="center",
             va="top", color=ACC, fontsize=14, fontweight="bold")

    # --- arrow --> ---
    ay = iy + iw / 2
    ax2.annotate("", xy=(5.75, ay), xytext=(4.35, ay),
                 arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.4))
    ax2.text(5.05, ay + 0.28, "stack\nalong T", ha="center", va="bottom",
             color=WARM, fontsize=11.5, fontweight="bold", linespacing=1.2)

    # --- right: video tensor — frames stacked along a new T axis ---
    T = 5
    vx0, vy0, vw = 6.35, 0.95, 1.55
    sx, sy = 0.52, 0.44           # offset per frame along the T axis
    for k in range(T - 1, -1, -1):
        fx = vx0 + k * sx
        fy = vy0 + k * sy
        lead = (k == 0)
        cube_face(ax2, fx, fy, vw, vw,
                  "#1c2836" if lead else "#141d28",
                  edge=ACC if lead else P.GRID,
                  lw=1.8 if lead else 1.2, z=10 - k)
        if lead:
            ax2.text(fx + vw / 2, fy + vw / 2, "frame 1", ha="center",
                     va="center", color=P.INK, fontsize=11.5, fontweight="bold")

    top_fx = vx0 + (T - 1) * sx
    top_fy = vy0 + (T - 1) * sy
    # the T axis arrow through the stack (lower-left -> upper-right)
    ax2.annotate("", xy=(top_fx + vw * 0.5, top_fy + vw * 0.5),
                 xytext=(vx0 + vw * 0.5, vy0 + vw * 0.5),
                 arrowprops=dict(arrowstyle="-|>", color=WARM, lw=2.2,
                                 shrinkA=0, shrinkB=0))
    ax2.text(top_fx + vw + 0.15, top_fy + vw * 0.55, "T\n(time)", ha="left",
             va="center", color=WARM, fontsize=13, fontweight="bold",
             linespacing=1.15)
    ax2.text(vx0 + vw / 2 + 0.55, vy0 - 0.35, "(T, H, W, C)", ha="center",
             va="top", color=ACC, fontsize=14, fontweight="bold")
    ax2.text(top_fx + vw / 2, top_fy + vw + 0.30, "VIDEO", ha="center",
             va="bottom", color=P.MUTED, fontsize=12.5, fontweight="bold")

    # framework-unchanged banner, safely below the axes
    f.text(0.5, 0.028,
           "The framework is unchanged — forward noising, ε-prediction, VAE "
           "latents, CFG, the U-Net/DiT denoiser — the whole story is the "
           "extra T axis.",
           ha="center", va="bottom", color=P.INK, fontsize=12.5,
           style="italic")

    return f


if __name__ == "__main__":
    f = main()
    print(P.save(f, "video-shape.png"))
