"""Matplotlib figures (saved as PNG, no window needed)."""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .optimize import OBJ_NAME

COL = {"water": "#4aa3df", "wall": "#444444", "ok": "#2e9e5b", "bad": "#d64545"}


def all_designs(res):
    return list(res["designs"].values()) + list(res["references"])


def draw_section(ax, d):
    """Cross-section with water level, freeboard line and key dimensions."""
    y, H = d["y"], d["H"]
    if d["section"] == "circular":
        D = d["D"]
        t = np.linspace(0, 2 * math.pi, 300)
        ax.plot(D / 2 * np.cos(t), D / 2 + D / 2 * np.sin(t), color=COL["wall"], lw=2)
        xs = np.linspace(-D / 2, D / 2, 400)
        low = D / 2 - np.sqrt(np.maximum((D / 2) ** 2 - xs ** 2, 0))
        ax.fill_between(xs, low, y, where=low <= y, color=COL["water"], alpha=.6)
        ax.hlines(y, -D / 2, D / 2, colors=COL["water"], lw=1.5)
        ax.set_xlim(-D * .75, D * .75)
        ax.set_ylim(-D * .1, D * 1.1)
        ax.set_title(f"Circular, D = {D:.2f} m\ny = {y:.2f} m (y/D = {y / D:.2f})", fontsize=9)
    else:
        b, z, top = d["b"], d["z"], d["bank"]
        wall = [(-top / 2, H), (-b / 2, 0), (b / 2, 0), (top / 2, H)]
        ax.plot(*zip(*wall), color=COL["wall"], lw=2)
        tw = d["T"]
        ax.fill([-b / 2, b / 2, tw / 2, -tw / 2], [0, 0, y, y], color=COL["water"], alpha=.6)
        ax.hlines(y, -tw / 2, tw / 2, colors=COL["water"], lw=1.5)
        ax.hlines(H, -top / 2, top / 2, colors="gray", linestyles="--", lw=1)
        ax.annotate("freeboard", (top / 2, (y + H) / 2), fontsize=7, color="gray",
                    xytext=(4, 0), textcoords="offset points", va="center")
        ax.set_xlim(-top * .75, top * .75 + top * .15)
        ax.set_ylim(-H * .1, H * 1.15)
        ax.set_title(f"{d['label']}, b = {b:.2f} m, z = {z:.2f}\n"
                     f"y = {y:.2f} m, freeboard = {d['fb']:.2f} m", fontsize=9)
    ax.set_aspect("equal")
    ax.set_xlabel("width (m)", fontsize=8)
    ax.set_ylabel("height (m)", fontsize=8)
    ax.grid(alpha=.3)
    ax.tick_params(labelsize=7)


def fig_sections(res, path):
    ds = all_designs(res)
    fig, axs = plt.subplots(1, len(ds), figsize=(4.2 * len(ds), 4), squeeze=False)
    for ax, d in zip(axs[0], ds):
        draw_section(ax, d)
        if d["option"].startswith("reference"):
            ax.set_title(ax.get_title() + "\n(reference)", fontsize=9)
    fig.suptitle("Cross-sections at normal depth (blue = water, dashed = top of freeboard)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_curves(res, path):
    """Left: gross-width scan for open channels. Right: pipe velocity vs depth."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for key, c in (("rectangular", "C0"), ("trapezoidal", "C1")):
        d = res["designs"].get(key)
        if not d or "curve" not in d:
            continue
        cv = d["curve"]
        b = np.array([r["b"] for r in cv])
        A = np.array([r["obj"] for r in cv])
        ok = np.array([r["ok"] for r in cv])
        a1.plot(b, A, color=c, label=f"{d['label']} (z = {d['z']:.2f})")
        a1.plot(b[~ok], A[~ok], ".", color=COL["bad"], ms=3)
        a1.plot(d["b"], d["obj"], "o", color=c, ms=8, mfc="white")
    a1.plot([], [], ".", color=COL["bad"], label="fails a check")
    a1.set_xlabel("bottom width b (m)")
    a1.set_ylabel(OBJ_NAME[res.get("objective", "area")])
    a1.set_title("Objective vs bottom width, each width carrying exactly Q\n(circles = chosen design)", fontsize=10)
    a1.set_xscale("log")
    a1.grid(alpha=.3)
    a1.legend(fontsize=8)
    d = res["designs"].get("circular")
    if d and "partial_curve" in d:
        pc = d["partial_curve"]
        yD = [r["yD"] for r in pc]
        a2.plot(yD, [r["V"] for r in pc], label="velocity / full-flow velocity")
        a2.plot(yD, [r["Q"] for r in pc], label="discharge / full-flow discharge")
        a2.axvline(d["r_vmax"], ls=":", color="C0")
        a2.axvline(d["r_qmax"], ls=":", color="C1")
        a2.axvline(d["y"] / d["D"], color=COL["ok"] if d["ok"] else COL["bad"], lw=2,
                   label=f"design y/D = {d['y'] / d['D']:.2f}")
        a2.set_xlabel("filling ratio y/D")
        a2.set_ylabel("ratio to full flow")
        a2.set_title(f"Partly full circular pipe\nmax velocity at y/D = {d['r_vmax']:.2f}, "
                     f"max discharge at y/D = {d['r_qmax']:.2f}", fontsize=10)
        a2.grid(alpha=.3)
        a2.legend(fontsize=8)
    else:
        a2.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_compare(res, path):
    ds = all_designs(res)
    names = [d["label"] + ("\n(ref.)" if d["option"].startswith("reference") else "")
             for d in ds]
    items = [("Gross section area (m²)", "A_gross"), ("Wetted perimeter (m)", "P"),
             ("Velocity (m/s)", "V"), ("Froude number", "Fr")]
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.8))
    for ax, (title, key) in zip(axs, items):
        vals = [d[key] for d in ds]
        ax.bar(names, vals, color=[COL["ok"] if d["ok"] else COL["bad"] for d in ds])
        ax.set_title(title, fontsize=10)
        ax.tick_params(labelsize=8)
        ax.grid(axis="y", alpha=.3)
        if key == "Fr":
            ax.axhline(1, color="k", ls="--", lw=1)
    fig.suptitle("Comparison (green = passes all checks, red = fails)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def save_all(res, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    fig_sections(res, out / "cross_sections.png")
    fig_curves(res, out / "optimisation_curves.png")
    fig_compare(res, out / "comparison.png")
    return [out / "cross_sections.png", out / "optimisation_curves.png", out / "comparison.png"]
