"""Concept figure for The Causal Cauldron (video wing, silver palette).

The causal 3D VAE: (a) normal vs causal temporal window, (b) space AND time
compression, (c) sliding-window / streaming decode with bounded memory.

Run:  ~/anaconda3/envs/lrm/bin/python tools/figs_cauldron.py
"""
import sys
sys.path.insert(0, "tools")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch
import palace_fig as P

WING = "silver"
ACC = P.WING[WING]["accent"]   # cool silver #c4ceda
WARM = P.WING[WING]["warm"]    # gold #d9c07a
COOL = P.WING[WING]["cool"]    # moonlit blue #8fb0d0
HOT = P.HOT                    # warm highlight #ffd98a
FORBID = "#c98f8f"             # muted rose — the forbidden future


def frame_box(ax, cx, cy, w, h, face, edge=P.GRID, lw=1.4, label=None,
              lc=P.INK, fs=12, ls="-", alpha=1.0, hatch=None, fw="normal"):
    r = Rectangle((cx - w / 2, cy - h / 2), w, h, facecolor=face,
                  edgecolor=edge, lw=lw, linestyle=ls, alpha=alpha,
                  hatch=hatch, zorder=3)
    ax.add_patch(r)
    if label is not None:
        ax.text(cx, cy, label, ha="center", va="center", color=lc,
                fontsize=fs, fontweight=fw, zorder=4)
    return r


def bracket(ax, x0, x1, y, text, color, up=True, fs=12):
    dy = 0.16 if up else -0.16
    tip = 0.10 if up else -0.10
    ax.plot([x0, x0, x1, x1], [y - tip, y, y, y - tip] if up
            else [y - tip, y, y, y - tip], color=color, lw=1.8, zorder=5)
    ax.text((x0 + x1) / 2, y + dy, text, ha="center",
            va="bottom" if up else "top", color=color, fontsize=fs,
            fontweight="bold", zorder=5)


# ===========================================================================
def build():
    f = plt.figure(figsize=(15.2, 10.2))
    f.patch.set_facecolor(P.BG)
    gs = f.add_gridspec(2, 2, height_ratios=[1.02, 1.05],
                        hspace=0.32, wspace=0.20,
                        left=0.055, right=0.965, top=0.858, bottom=0.065)

    P.suptitle(f, "The Causal 3D VAE  —  stir only the past, compress space and time")
    f.text(0.5, 0.928,
           "Wan's workhorse: a 3D convolution that never reaches into the "
           "future, so long reels can stream in bounded memory.",
           ha="center", color=P.MUTED, fontsize=13)

    # -------------------------------------------------------------------
    # (a) NORMAL (bilateral) vs CAUSAL temporal window
    # -------------------------------------------------------------------
    axa = f.add_subplot(gs[0, :])
    axa.set_facecolor(P.PANEL)
    for s in axa.spines.values():
        s.set_color(P.GRID)
    axa.set_xticks([]); axa.set_yticks([])
    axa.set_xlim(-6.0, 6.2)
    axa.set_ylim(-1.05, 4.25)

    idx = list(range(-3, 4))
    bw, bh = 0.9, 0.9
    y_norm, y_caus = 3.15, 0.95

    # shade the future half-plane (frames after the present)
    axa.axvspan(0.5, 6.2, color=FORBID, alpha=0.10, zorder=0)
    axa.axvline(0.5, color=P.MUTED, ls=(0, (4, 3)), lw=1.3, zorder=1)
    axa.text(6.05, 4.0, "future  →", ha="right", va="center",
             color=FORBID, fontsize=12.5, fontweight="bold", style="italic")

    def flabel(i):
        return "t" if i == 0 else ("t%d" % i if i < 0 else "t+%d" % i)

    # --- NORMAL track ---
    axa.text(-5.75, y_norm, "NORMAL\n3D conv", ha="left", va="center",
             color=P.INK, fontsize=12.5, fontweight="bold")
    for i in idx:
        if i == 0:
            fc, lc, lab, fw = ACC, P.BG, "t", "bold"
        elif -2 <= i <= -1:
            fc, lc, lab, fw = COOL, P.BG, flabel(i), "bold"
        elif 1 <= i <= 2:
            fc, lc, lab, fw = HOT, P.BG, flabel(i), "bold"
        else:
            fc, lc, lab, fw = "#1b2531", P.MUTED, flabel(i), "normal"
        frame_box(axa, i, y_norm, bw, bh, fc, lc=lc, label=lab, fw=fw, fs=12.5)
    bracket(axa, -2 - bw / 2, 2 + bw / 2, y_norm + bh / 2 + 0.06,
            "bilateral kernel  [t-2 … t+2]", HOT, up=True, fs=12.5)

    # --- CAUSAL track ---
    axa.text(-5.75, y_caus, "CAUSAL\n3D conv", ha="left", va="center",
             color=P.INK, fontsize=12.5, fontweight="bold")
    for i in idx:
        if i == 0:
            frame_box(axa, i, y_caus, bw, bh, ACC, lc=P.BG, label="t",
                      fw="bold", fs=12.5)
        elif -2 <= i <= -1:
            frame_box(axa, i, y_caus, bw, bh, COOL, lc=P.BG,
                      label=flabel(i), fw="bold", fs=12.5)
        else:
            # forbidden / unused frames: hollow, dashed
            frame_box(axa, i, y_caus, bw, bh, "none", edge=P.MUTED, lw=1.2,
                      label="×" if i > 0 else flabel(i),
                      lc=FORBID if i > 0 else P.MUTED, ls=(0, (3, 2)),
                      fs=14 if i > 0 else 11)
    bracket(axa, -2 - bw / 2, 0 + bw / 2, y_caus - bh / 2 - 0.06,
            "[t-2 … t]   past + present only", ACC, up=False, fs=12.5)

    # annotations placed in the clear band between the two tracks
    axa.annotate("reaches into the FUTURE\n— must hold the whole video",
                 xy=(2, y_norm - bh / 2 - 0.02), xytext=(3.15, 2.05),
                 ha="left", va="center", color=FORBID, fontsize=12,
                 fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=FORBID, lw=1.8))
    axa.annotate("never looks forward",
                 xy=(1.5, y_caus + bh / 2 + 0.02), xytext=(3.15, 1.55),
                 ha="left", va="center", color=ACC, fontsize=12,
                 fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8))

    axa.set_title("(a)  The one change: the decoder's causal mask, applied to time",
                  color=P.INK, fontsize=14.5, loc="left", pad=8)

    # -------------------------------------------------------------------
    # (b) compress SPACE and TIME  — proportional blocks
    # -------------------------------------------------------------------
    axb = f.add_subplot(gs[1, 0])
    axb.set_facecolor(P.PANEL)
    for s in axb.spines.values():
        s.set_color(P.GRID)
    axb.set_xticks([]); axb.set_yticks([])
    axb.set_xlim(0, 10)
    axb.set_ylim(0, 10)
    axb.set_aspect("auto")
    axb.set_title("(b)  Compress space AND time", color=P.INK,
                  fontsize=14.5, loc="left", pad=10)

    # input block: width ∝ 81 frames, height ∝ 512 px
    Hin, Hlat = 4.6, 4.6 / 8.0        # 512 → 64  (8× per side)
    Win, Wlat = 3.7, 3.7 * 21 / 81.0  # 81 → 21   (~4× in time)
    x_in, y_in = 0.85, 3.4
    x_lat = 7.05
    # centre the (short) latent block on the input's vertical mid-line
    y_lat = y_in + (Hin - Hlat) / 2

    frame_box(axb, x_in + Win / 2, y_in + Hin / 2, Win, Hin, "#22303f",
              edge=COOL, lw=1.8)
    # a few internal frame-dividers to read as a stack of many frames
    for k in range(1, 7):
        xx = x_in + Win * k / 7
        axb.plot([xx, xx], [y_in, y_in + Hin], color=COOL, lw=0.7, alpha=0.5)
    frame_box(axb, x_lat + Wlat / 2, y_lat + Hlat / 2, Wlat, Hlat, ACC,
              edge=P.INK, lw=1.8)
    for k in range(1, 3):
        xx = x_lat + Wlat * k / 3
        axb.plot([xx, xx], [y_lat, y_lat + Hlat], color=P.BG, lw=0.7, alpha=0.6)

    axb.text(x_in + Win / 2, y_in - 0.35, "81 frames\n512×512×3",
             ha="center", va="top", color=P.INK, fontsize=12, fontweight="bold")
    axb.text(x_lat + Wlat / 2, y_lat - 0.35, "≈21 latent frames\n64×64×c",
             ha="center", va="top", color=P.INK, fontsize=12, fontweight="bold")

    # encoder arrow
    arr = FancyArrowPatch((x_in + Win + 0.15, y_in + Hin / 2),
                          (x_lat - 0.15, y_lat + Hlat / 2),
                          arrowstyle="-|>", mutation_scale=24, color=WARM,
                          lw=2.4)
    axb.add_patch(arr)
    axb.text((x_in + Win + x_lat) / 2, y_in + Hin / 2 + 0.55,
             "3D causal-conv\nencoder", ha="center", va="bottom",
             color=WARM, fontsize=11.5, fontweight="bold")

    # height bracket (space)
    xb = x_in - 0.34
    axb.plot([xb, xb], [y_in, y_in + Hin], color=P.MUTED, lw=1.6)
    axb.plot([xb, xb + 0.12], [y_in, y_in], color=P.MUTED, lw=1.6)
    axb.plot([xb, xb + 0.12], [y_in + Hin, y_in + Hin], color=P.MUTED, lw=1.6)
    axb.text(xb - 0.18, y_in + Hin / 2, "512 → 64   space ÷8 / side",
             ha="center", va="center", color=COOL, fontsize=11.5,
             fontweight="bold", rotation=90)

    # width bracket (time)
    yb = y_in + Hin + 0.28
    axb.plot([x_in, x_in + Win], [yb, yb], color=P.MUTED, lw=1.6)
    axb.plot([x_in, x_in], [yb, yb - 0.12], color=P.MUTED, lw=1.6)
    axb.plot([x_in + Win, x_in + Win], [yb, yb - 0.12], color=P.MUTED, lw=1.6)
    axb.text(x_in + Win / 2, yb + 0.08, "81 frames  →  21   (time ÷4)",
             ha="center", va="bottom", color=WARM, fontsize=11.5,
             fontweight="bold")

    axb.text(5.0, 1.35,
             "Temporal attention then runs over 21 tokens, not 81:\n"
             "21² vs 81²  ≈  15× fewer pairs  (the T² saving)",
             ha="center", va="center", color=P.INK, fontsize=12,
             fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#182230",
                       edgecolor=WARM, lw=1.2))

    # -------------------------------------------------------------------
    # (c) sliding-window decode + bounded memory
    # -------------------------------------------------------------------
    inner = gs[1, 1].subgridspec(2, 1, height_ratios=[0.9, 1.1], hspace=0.62)

    # (c1) latent timeline with a sliding decode window
    axc = f.add_subplot(inner[0])
    axc.set_facecolor(P.PANEL)
    for s in axc.spines.values():
        s.set_color(P.GRID)
    axc.set_xticks([]); axc.set_yticks([])
    axc.set_xlim(0, 21.6)
    axc.set_ylim(-0.9, 1.5)
    axc.set_title("(c)  Sliding-window decoding  →  streaming",
                  color=P.INK, fontsize=14.5, loc="left", pad=8)

    n = 20
    win_start, win_len = 9, 4        # decode frame t from a window of past latents
    for i in range(n):
        infut = i > win_start + win_len - 1
        inwin = win_start <= i <= win_start + win_len - 1
        if i == win_start + win_len - 1:
            fc, ec = ACC, P.INK                # present frame t
        elif inwin:
            fc, ec = COOL, P.GRID              # past frames in window
        elif infut:
            fc, ec = "#1b2531", P.GRID         # not yet decoded
        else:
            fc, ec = "#2a3646", P.GRID         # already streamed out
        frame_box(axc, i + 0.5, 0.35, 0.82, 0.72, fc, edge=ec, lw=1.1)
    # window outline
    axc.add_patch(Rectangle((win_start - 0.05, -0.10),
                            win_len, 0.90, facecolor="none",
                            edgecolor=HOT, lw=2.4, zorder=6))
    axc.text(win_start + win_len / 2, 1.02, "decode window\n(past only)",
             ha="center", va="bottom", color=HOT, fontsize=11,
             fontweight="bold")
    arrw = FancyArrowPatch((win_start + win_len + 0.1, 1.15),
                           (win_start + win_len + 3.0, 1.15),
                           arrowstyle="-|>", mutation_scale=18, color=HOT,
                           lw=2.0)
    axc.add_patch(arrw)
    axc.text(0.2, -0.62, "latent frames  (time →)", ha="left", va="center",
             color=P.MUTED, fontsize=10.5)

    # (c2) memory: flat (windowed) vs growing (hold whole video)
    axm = f.add_subplot(inner[1])
    P.style_ax(axm, WING)
    L = np.linspace(0, 60, 200)
    axm.plot(L, 0.30 + L * 0.145, color=FORBID, lw=2.6,
             label="hold whole video  (bilateral)")
    axm.plot(L, np.full_like(L, 1.05), color=ACC, lw=2.6,
             label="causal sliding window")
    axm.fill_between(L, 1.05, 0.30 + L * 0.145, color=FORBID, alpha=0.10)
    axm.set_xlim(0, 60); axm.set_ylim(0, 9.6)
    axm.set_xlabel("video length  (seconds)", fontsize=12)
    axm.set_ylabel("peak decode memory", fontsize=12)
    axm.set_yticks([])
    axm.set_xticks([0, 15, 30, 45, 60])
    axm.text(58, 1.55, "bounded — flat", color=ACC, fontsize=11.5,
             ha="right", va="bottom", fontweight="bold")
    axm.legend(facecolor=P.PANEL, edgecolor=P.GRID, labelcolor=P.INK,
               fontsize=10.5, loc="upper left")

    return P.save(f, "video-causal-vae.png")


if __name__ == "__main__":
    print("wrote", build())
