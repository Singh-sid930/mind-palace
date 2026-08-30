"""Concept figure for The Latent Vault (diffusion wing).

The compression bargain: paint in a 48x-smaller latent, not in pixels.
Three tellings, proportional volumes, the cost that collapses, and the
encode -> diffuse-in-latent -> decode pipeline.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_vault.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]   # warm gold
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]

PIX = "#7fa8d8"    # cool blue for the great hall of pixels
LAT = WARM         # warm gold for the shrunken emblem


def fig_vault():
    f = plt.figure(figsize=(16.5, 10.0))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, height_ratios=[1.02, 0.86],
                        hspace=0.34, wspace=0.20,
                        left=0.055, right=0.955, top=0.855, bottom=0.065)

    P.suptitle(f, "The Latent Vault, Never Diffuse in the Great Hall of Pixels")
    f.text(0.5, 0.905,
           "A frozen VAE folds a 512×512×3 painting into a 64×64×4 emblem, 48× fewer numbers that still carry "
           "everything the picture MEANS. The U-Net labours entirely inside the Glass.",
           ha="center", color=P.MUTED, fontsize=13.2)

    # ======================================================================
    # (a) proportional volumes, the shrinking glass, drawn to scale
    # ======================================================================
    ax = f.add_subplot(gs[0, 0]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(a)  Drawn to scale: 48× fewer numbers", color=P.INK, fontsize=15)

    # pixel square: side scaled so area ∝ value count.  sqrt(48) ≈ 6.93
    side_pix = 6.4
    side_lat = side_pix / np.sqrt(48)   # ≈ 0.924
    x0, y0 = 0.45, 2.35
    ax.add_patch(Rectangle((x0, y0), side_pix, side_pix, facecolor=plt.matplotlib.colors.to_rgba(PIX, 0.20),
                           edgecolor=PIX, lw=2.4, zorder=2))
    # nested latent square in the bottom-left corner
    ax.add_patch(Rectangle((x0, y0), side_lat, side_lat, facecolor=plt.matplotlib.colors.to_rgba(LAT, 0.9),
                           edgecolor=LAT, lw=2.2, zorder=4))
    # pixel-space labels, kept in the upper half so the corner emblem is clear
    ax.text(x0 + side_pix / 2, y0 + side_pix - 0.55, "PIXEL SPACE",
            ha="center", va="center", color=PIX, fontsize=14, fontweight="bold", zorder=5)
    ax.text(x0 + side_pix / 2, y0 + side_pix * 0.62, "512 × 512 × 3",
            ha="center", va="center", color=P.INK, fontsize=13.5, zorder=5)
    ax.text(x0 + side_pix / 2, y0 + side_pix * 0.48, "= 786,432 numbers",
            ha="center", va="center", color=P.INK, fontsize=13.5, fontweight="bold", zorder=5)
    # latent callout: arrow from the emblem out to a clear label on the right
    lx, ly = x0 + side_lat, y0 + side_lat / 2
    ax.annotate("LATENT\n64 × 64 × 4\n= 16,384 numbers",
                xy=(lx + 0.02, ly), xytext=(x0 + side_pix * 0.46, y0 + 0.95),
                ha="left", va="center", color=LAT, fontsize=12, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=LAT, lw=1.9,
                                connectionstyle="arc3,rad=0.15"), zorder=6)
    ax.text(x0 + side_pix / 2, y0 - 0.85, "the gold emblem is the WHOLE latent, drawn to scale",
            ha="center", va="center", color=P.MUTED, fontsize=10.8, fontstyle="italic")

    # ======================================================================
    # (b) the cost that collapses, log-scale horizontal bars
    # ======================================================================
    ax = f.add_subplot(gs[0, 1]); P.style_ax(ax, WING, grid=True)
    ax.set_title("(b)  What shrinking buys (log scale)", color=P.INK, fontsize=15)
    rows = ["numbers\nto store", "positions n\n(self-attention)", "attention\ncost  ∝ n²"]
    pix_vals = [786432, 262144, 262144**2 / 1e6]     # scale n² down to keep bars comparable
    lat_vals = [16384, 4096, 4096**2 / 1e6]
    ratios = [786432 / 16384, 262144 / 4096, (262144**2) / (4096**2)]
    y = np.arange(3)[::-1]
    h = 0.34
    b1 = ax.barh(y + h / 2, pix_vals, h, color=plt.matplotlib.colors.to_rgba(PIX, 0.85),
                 edgecolor=P.GRID, label="pixel space", zorder=3)
    b2 = ax.barh(y - h / 2, lat_vals, h, color=plt.matplotlib.colors.to_rgba(LAT, 0.9),
                 edgecolor=P.GRID, label="latent space", zorder=3)
    ax.set_xscale("log")
    ax.set_xlim(1e3, 1e11)
    ax.set_yticks(y); ax.set_yticklabels(rows, fontsize=12)
    ax.set_xlabel("count (log scale)  ·  n² shown per million", fontsize=11.5)
    # colour key inline (blue = pixel, gold = latent), no legend box to clash
    ax.text(0.985, 0.96, "pixel space", transform=ax.transAxes, color=PIX,
            fontsize=12.5, fontweight="bold", va="top", ha="right")
    ax.text(0.985, 0.90, "latent space", transform=ax.transAxes, color=LAT,
            fontsize=12.5, fontweight="bold", va="top", ha="right")
    # ratio annotations, in a clean column to the right of the bars
    for yy, r in zip(y, ratios):
        txt = f"{r:.0f}× cheaper" if r < 1000 else f"{r/1000:.1f}k× cheaper"
        ax.text(3e8, yy, txt, ha="left", va="center", color=ACC,
                fontsize=13, fontweight="bold")

    # ======================================================================
    # (c) the pipeline, encode -> diffuse in latent -> decode
    # ======================================================================
    ax = f.add_subplot(gs[1,:]); P.style_ax(ax, WING, grid=False)
    ax.set_xlim(0, 16); ax.set_ylim(0, 5.0)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("(c)  The bargain: encode once, diffuse in the latent, decode once",
                 color=P.INK, fontsize=15, pad=10)

    def stage(cx, w, color, title, lines, hh=1.55):
        box = FancyBboxPatch((cx - w / 2, 2.55 - hh / 2), w, hh,
                             boxstyle="round,pad=0.03,rounding_size=0.12",
                             linewidth=2.3, edgecolor=color,
                             facecolor=plt.matplotlib.colors.to_rgba(color, 0.16), zorder=3)
        ax.add_patch(box)
        ax.text(cx, 2.55 + hh / 2 - 0.34, title, ha="center", va="center",
                color=color, fontsize=13, fontweight="bold", zorder=5)
        ax.text(cx, 2.55 - 0.12, lines, ha="center", va="center",
                color=P.INK, fontsize=11.3, zorder=5)

    # pixel-blue endpoints, gold middle (the U-Net lives in gold latent space)
    stage(2.2, 3.5, PIX, "1  ·  VAE ENCODER", "image 512×512×3\n→ clean latent z₀\n64×64×4")
    stage(8.0, 4.6, LAT, "2  ·  DIFFUSE IN LATENT", "U-Net denoises latents ~1000 steps\nself- & cross-attention here\nNEVER sees a pixel")
    stage(13.8, 3.5, PIX, "3  ·  VAE DECODER", "final latent z₀\n→ image 512×512×3\nfrozen, master of detail")

    for xa, xb in [(2.2 + 1.75, 8.0 - 2.3), (8.0 + 2.3, 13.8 - 1.75)]:
        ax.add_artist(FancyArrowPatch((xa + 0.05, 2.55), (xb - 0.05, 2.55),
                                      arrowstyle="-|>", mutation_scale=22,
                                      color=ACC, lw=2.6, zorder=4))
    # under-notes
    ax.text(8.0, 0.72, "The frozen VAE masters PIXEL detail (grain, edges); the U-Net is freed to worry only about "
            "SEMANTIC structure, which is why Stable Diffusion fit on a gaming GPU (~8, 12 GB) while pixel-space "
            "diffusion needed datacenters.",
            ha="center", va="center", color=P.MUTED, fontsize=11.4, fontstyle="italic")

    return P.save(f, "latent-vault-bargain.png")


if __name__ == "__main__":
    print("wrote", fig_vault())
