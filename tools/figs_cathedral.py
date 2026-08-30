"""Concept figure for The U-Net Cathedral (diffusion wing).

An architectural cross-section of the U: the encoder descends (space halves,
channels double), the bottleneck crypt, the decoder climbs back, and luminous
skip-connection arcs bridge matching depths.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_cathedral.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch
from matplotlib.path import Path as MPath
import palace_fig as P

WING = "amber"
ACC = P.WING[WING]["accent"]   # warm gold
WARM = P.WING[WING]["warm"]
COOL = P.WING[WING]["cool"]


# Each level: (label, resolution, channels, block-tags)
# y encodes DEPTH (higher res = higher on the page); the U dips into the crypt.
def fig_cathedral():
    f = plt.figure(figsize=(16.5, 10.2))
    f.patch.set_facecolor(P.BG)
    ax = f.add_axes([0.045, 0.065, 0.91, 0.80])
    ax.set_facecolor(P.BG)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    P.suptitle(f, "The U-Net Cathedral, Descend to Meaning, Climb Back to Detail")
    f.text(0.5, 0.905,
           "Encoder halves space and doubles channels down the left arm  ·  the crypt holds widest context  ·  "
           "the decoder climbs back up the right arm  ·  flying-buttress skips carry crisp detail across",
           ha="center", color=P.MUTED, fontsize=13.2)

    # ---- geometry -----------------------------------------------------------
    # Levels by resolution. y_top is the floor height (the U descends).
    # width of the block encodes channels (wider = more channels).
    # height of the block encodes spatial resolution (taller = higher res).
    levels = [
        # res, channels, y-center, half-height (res), half-width (channels)
        (256, 64),
        (128, 128),
        (64, 256),
        (32, 512),   # bottleneck / crypt
    ]
    # floor y-centres, descending into the crypt
    ys = [8.7, 6.6, 4.6, 2.7]
    # block visual sizing
    def hh(res):   # half-height from resolution (log-ish, legible)
        return {256: 0.62, 128: 0.52, 64: 0.42, 32: 0.34}[res]
    def hw(ch):    # half-width from channels
        return {64: 0.62, 128: 0.78, 256: 0.95, 512: 1.14}[ch]

    x_enc = 4.15    # encoder column centre
    x_dec = 11.85   # decoder column centre
    x_bot = 8.0     # bottleneck centre

    enc_boxes = []   # (x, y, res, ch)
    dec_boxes = []

    def draw_block(x, y, res, ch, color, edge, lw=2.0, label=None, sub=None):
        w = 2 * hw(ch)
        h = 2 * hh(res)
        box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                             boxstyle="round,pad=0.02,rounding_size=0.09",
                             linewidth=lw, edgecolor=edge,
                             facecolor=color, zorder=4)
        ax.add_patch(box)
        if label:
            ax.text(x, y + 0.055, label, ha="center", va="center",
                    color=P.INK, fontsize=13.5, fontweight="bold", zorder=6)
        if sub:
            ax.text(x, y - 0.30, sub, ha="center", va="center",
                    color=P.BG, fontsize=10.5, fontweight="bold", zorder=6)
        return (x, y, w, h)

    # ---- encoder (left arm, descending) ------------------------------------
    for (res, ch), y in zip(levels[:-1], ys[:-1]):
        shade = plt.matplotlib.colors.to_rgba(COOL, 0.30 + 0.13 * levels[:-1].index((res, ch)))
        g = draw_block(x_enc, y, res, ch, shade, COOL,
                       label=f"{res}×{res}",
                       sub=f"{ch} ch")
        enc_boxes.append((x_enc, y, res, ch, g))

    # ---- bottleneck / crypt -------------------------------------------------
    res_b, ch_b = levels[-1]
    yb = ys[-1]
    crypt = draw_block(x_bot, yb, res_b, ch_b,
                       plt.matplotlib.colors.to_rgba(WARM, 0.42), WARM, lw=2.6,
                       label=f"{res_b}×{res_b}", sub=f"{ch_b} ch")
    ax.text(x_bot, yb - 0.72, "THE CRYPT  ·  bottleneck",
            ha="center", va="center", color=WARM, fontsize=12,
            fontstyle="italic", fontweight="bold", zorder=6)
    ax.text(x_bot, yb - 1.08, "widest field of view, deepest meaning",
            ha="center", va="center", color=P.MUTED, fontsize=10.2, zorder=6)

    # ---- decoder (right arm, climbing) -------------------------------------
    for (res, ch), y in zip(levels[:-1], ys[:-1]):
        shade = plt.matplotlib.colors.to_rgba(ACC, 0.26 + 0.12 * levels[:-1].index((res, ch)))
        g = draw_block(x_dec, y, res, ch, shade, ACC,
                       label=f"{res}×{res}",
                       sub=f"{ch} ch")
        dec_boxes.append((x_dec, y, res, ch, g))

    # ---- descent / climb arrows along the arms -----------------------------
    def arm_arrow(x0, y0, x1, y1, color):
        a = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                            mutation_scale=18, color=color, lw=2.0,
                            zorder=3, connectionstyle="arc3,rad=0.0", alpha=0.9)
        ax.add_artist(a)

    # encoder down + into crypt
    pts_enc = [(x_enc, ys[0]), (x_enc, ys[1]), (x_enc, ys[2])]
    for (a, b) in zip(pts_enc, pts_enc[1:]):
        arm_arrow(a[0], a[1] - hh(256) - 0.06, b[0], b[1] + hh(128) + 0.06, COOL)
    arm_arrow(x_enc + hw(256) * 0.4, ys[2] - hh(64), x_bot - hw(512) - 0.05, yb + 0.05, COOL)
    # crypt into decoder + climb up
    arm_arrow(x_bot + hw(512) + 0.05, yb + 0.05, x_dec - hw(256) * 0.4, ys[2] - hh(64), ACC)
    pts_dec = [(x_dec, ys[2]), (x_dec, ys[1]), (x_dec, ys[0])]
    for (a, b) in zip(pts_dec, pts_dec[1:]):
        arm_arrow(a[0], a[1] + hh(64) + 0.06, b[0], b[1] - hh(128) - 0.06, ACC)

    # ---- input / output tokens ---------------------------------------------
    def io_pill(x, y, top, bottom, color):
        box = FancyBboxPatch((x - 1.15, y - 0.42), 2.3, 0.84,
                             boxstyle="round,pad=0.02,rounding_size=0.12",
                             linewidth=2.0, edgecolor=color,
                             facecolor=P.PANEL, zorder=5)
        ax.add_patch(box)
        ax.text(x, y + 0.14, top, ha="center", va="center", color=P.INK,
                fontsize=11.5, fontweight="bold", zorder=6)
        ax.text(x, y - 0.16, bottom, ha="center", va="center", color=color,
                fontsize=10.2, zorder=6)

    io_pill(x_enc, ys[0] + 1.30, "noisy image  x_t", "(H, W, C)  +  timestep t", COOL)
    io_pill(x_dec, ys[0] + 1.30, "predicted noise", "(H, W, C), same shape", ACC)
    # tiny connectors from IO to first blocks
    arm_arrow(x_enc, ys[0] + 1.30 - 0.42, x_enc, ys[0] + hh(256) + 0.05, COOL)
    arm_arrow(x_dec, ys[0] + hh(256) + 0.05, x_dec, ys[0] + 1.30 - 0.42, ACC)

    # ---- skip connections (flying buttresses) ------------------------------
    # deeper skips arc higher so the three buttresses never overlap
    rad = {256: -0.16, 128: -0.26, 64: -0.42}
    for (xe, ye, rese, che, ge), (xd, yd, resd, chd, gd) in zip(enc_boxes, dec_boxes):
        y_arc = ye + hh(rese) + 0.04
        skip = FancyArrowPatch((xe + hw(che) * 0.5, y_arc),
                               (xd - hw(chd) * 0.5, y_arc),
                               connectionstyle=f"arc3,rad={rad[rese]}",
                               arrowstyle="-|>", mutation_scale=17,
                               color=HOTGLOW(rese), lw=2.6, zorder=2, alpha=0.95)
        ax.add_artist(skip)
        # label at the crown of the arc
        peak = y_arc - rad[rese] * (xd - xe) * 0.5
        ax.text((xe + xd) / 2, peak + 0.06, f"skip  {rese}×{rese}",
                ha="center", va="bottom", color=HOTGLOW(rese),
                fontsize=10.8, fontstyle="italic", fontweight="bold", zorder=6)

    # ---- axis labels for the two encoded quantities ------------------------
    ax.annotate("", xy=(1.35, ys[-1] - 0.2), xytext=(1.35, ys[0] + 0.2),
                arrowprops=dict(arrowstyle="-|>", color=P.MUTED, lw=1.6))
    ax.text(1.02, (ys[0] + ys[-1]) / 2, "spatial resolution  ↓\n(space halved each step)",
            ha="center", va="center", color=P.MUTED, fontsize=10.5,
            rotation=90)
    ax.annotate("", xy=(14.75, ys[-1] - 0.2), xytext=(14.75, ys[0] + 0.2),
                arrowprops=dict(arrowstyle="-|>", color=WARM, lw=1.6))
    ax.text(15.15, (ys[0] + ys[-1]) / 2, "channels  ↑\n(meaning deepened)",
            ha="center", va="center", color=WARM, fontsize=10.5, rotation=90)

    # ---- where the four rites sit ------------------------------------------
    ax.text(x_bot, yb + 0.60, "self-attention + cross-attention afforded here",
            ha="center", va="bottom", color=P.INK, fontsize=10.4,
            fontstyle="italic", zorder=6)
    ax.text(x_bot, 4.95, "convolution does the cheap local work up top;\n"
            "attention (cost O(n²)) is spent only in the shrunken lower rooms",
            ha="center", va="center", color=P.MUTED, fontsize=10.6,
            fontstyle="italic", zorder=6)

    # legend of the four rites at each landing
    rites = "Each landing, in fixed order:  ResNet conv  →  inject t  →  self-attention  →  cross-attention (prompt)"
    f.text(0.5, 0.028, rites, ha="center", color=P.INK, fontsize=12.5,
           fontweight="bold")

    return P.save(f, "unet-cathedral.png")


def HOTGLOW(res):
    # brighter arcs for the higher-resolution (more detailed) skips
    return {256: "#ffe6a6", 128: "#ffd07a", 64: "#f0b25a"}[res]


if __name__ == "__main__":
    p = fig_cathedral()
    print("wrote", p)
