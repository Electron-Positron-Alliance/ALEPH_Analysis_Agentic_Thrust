#!/usr/bin/env python3
"""
mplhep's CMS style with an ALEPH header, for every figure the paper ships.

The style is mplhep's, unmodified except for the font type. What this module
adds is the ALEPH header text and a shared registry of axis labels, colours and
ratio-panel titles, so the same quantity is not spelled three ways.

Canvases stay at CMS's native size; LaTeX's \\includegraphics width decides how
big each figure ends up. Text therefore prints smaller in figures included
narrow, which is inherent to including figures at different widths.

    import alephstyle as als
    als.use()
    fig, ax = als.figure()
    als.header(ax)
    ax.set_xlabel(als.X["thrust"])
    als.save(fig, "figures/foo.pdf")
"""

from __future__ import annotations

import os
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import mplhep as hep

# --------------------------------------------------------------------------- #
# Canvases
# --------------------------------------------------------------------------- #

# CMS style's point sizes are drawn for a canvas this wide. Keep every canvas at
# it and let LaTeX do the scaling, so CMS's proportions survive intact. Building
# small canvases instead makes the text proportionally huge and it collides.
CANVAS_W_IN = 10.0

ASPECT = 0.78
ASPECT_RATIO_PANEL = 1.00
RATIO_SPLIT = (3, 1)

SQRTS_GEV = 91.2
_EXP = "ALEPH"
_EXP_TEXT = "archived data"


def use() -> None:
    """Apply mplhep's CMS style. Call once, before creating any figure."""
    plt.style.use(hep.style.CMS)
    # CMS style leaves this at 3. Type 3 fonts are flagged by arXiv and JHEP
    # production; 42 embeds TrueType instead. The only rcParam we override.
    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})


def figure(aspect: float = ASPECT, scale: float = 1.0, **kw):
    """One panel at CMS's native size. LaTeX sets how big it ends up."""
    w = CANVAS_W_IN * scale
    fig, ax = plt.subplots(figsize=(w, w * aspect), layout="constrained", **kw)
    return fig, ax


def figure_ratio(aspect: float = ASPECT_RATIO_PANEL, scale: float = 1.0, **kw):
    """Main panel over a ratio panel, sharing the x axis."""
    w = CANVAS_W_IN * scale
    fig, (ax, rax) = plt.subplots(
        2,
        1,
        figsize=(w, w * aspect),
        gridspec_kw={"height_ratios": list(RATIO_SPLIT)},
        sharex=True,
        layout="constrained",
        **kw,
    )
    rax.axhline(1.0, color="0.4", lw=plt.rcParams["axes.linewidth"] * 0.6,
                ls="--", zorder=0)
    rax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, prune="upper"))
    return fig, ax, rax


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #


def header(ax, rlabel: str | None = None, **kw):
    """mplhep's experiment label, reading ALEPH instead of CMS."""
    if rlabel is None:
        rlabel = rf"$e^+e^-$ $\sqrt{{s}} = {SQRTS_GEV:g}$ GeV"
    # data=True, or mplhep inserts "Simulation" into the label.
    return hep.label.exp_label(exp=_EXP, text=_EXP_TEXT, rlabel=rlabel, loc=0,
                               data=True, ax=ax, **kw)


def panel_label(ax, text: str, loc: str = "upper left") -> None:
    """Identify one panel of a figure LaTeX assembles from separate files."""
    x, ha = (0.04, "left") if "left" in loc else (0.96, "right")
    y, va = (0.95, "top") if "upper" in loc else (0.05, "bottom")
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va,
            fontsize=plt.rcParams["xtick.labelsize"], fontweight="bold",
            bbox={"facecolor": "white", "edgecolor": "none",
                  "alpha": 0.75, "pad": 1.5})


# --------------------------------------------------------------------------- #
# Labels
# --------------------------------------------------------------------------- #

X = {
    "thrust": r"Thrust $T$",
    "thrust_gen": r"$T_\mathrm{gen}$",
    "thrust_reco": r"$T_\mathrm{reco}$",
    "tau": r"$\tau = 1 - T$",
    "logtau": r"$\ln\tau = \ln(1-T)$",
    "thrust_bin": r"Thrust bin",
    "cosTheta": r"$\cos\theta$",
    "cosThetaSph": r"$\cos\theta_\mathrm{Sph}$",
    "phi": r"$\varphi$",
    "pt": r"$p_T$ [GeV]",
    "pmag": r"$|\vec{p}|$ [GeV]",
    "d0": r"$d_0$ [cm]",
    "z0": r"$z_0$ [cm]",
    "ntpc": r"$N_\mathrm{TPC}$",
    "energy": r"$E$ [GeV]",
    "mass": r"$m$ [GeV]",
    "ntrk": r"$N_\mathrm{trk}$",
    "ntrkPlusNeu": r"$N_\mathrm{trk} + N_\mathrm{neu}$",
    "eCh": r"$E_\mathrm{ch}$ [GeV]",
}

Y = {
    "diffxsec": r"$(1/\sigma)\,\mathrm{d}\sigma/\mathrm{d}T$",
    "normalized": r"$(1/N)\,\mathrm{d}N/\mathrm{d}X$",
    "normalized_thrust": r"$(1/N)\,\mathrm{d}N/\mathrm{d}T$",
    "fraction": r"Fraction of particles",
    "efficiency": r"Reconstruction efficiency",
    "uncert": r"Fractional uncertainty [%]",
    "correlation": r"Correlation",
    "covariance": r"Covariance",
    "counts": r"Entries",
    "resolution": r"$T_\mathrm{reco} - T_\mathrm{gen}$",
}

RATIO = {
    "plain": r"Ratio",
    "mc_data": r"MC / Data",
    "aleph": r"Ours / ALEPH 2004",
    "charged_ef": r"Charged / EF",
    "nominal": r"Ratio to nominal",
}


# --------------------------------------------------------------------------- #
# Colour
# --------------------------------------------------------------------------- #

# Sequential for magnitudes, diverging for anything signed (correlations).
CMAP_SEQ = "viridis"
CMAP_DIV = "RdBu_r"

C = {
    "data": "black",
    "mc_reco": "#e41a1c",
    "mc_gen": "#4daf4a",
    "mc_genbefore": "#377eb8",
    "aleph2004": "#e6007e",
    "unfolded": "black",
    "stat": "#4e79a7",
    "mcstat": "#76b7b2",
    "iter": "#f28e2b",
    "exp": "#59a14f",
    "theory": "#e15759",
    "hadronic": "#9467bd",
    "isr": "#e07b39",
    "total": "black",
}

LS = {
    "stat": "-",
    "mcstat": (0, (1, 1)),
    "iter": "--",
    "exp": "-",
    "theory": "-",
    "hadronic": ":",
    "isr": (0, (3, 1, 1, 1)),
    "total": "--",
}


# --------------------------------------------------------------------------- #
# Saving
# --------------------------------------------------------------------------- #


def _font_report(path: str) -> list[str]:
    """Rows of `pdffonts`, or [] if pdffonts is unavailable."""
    try:
        out = subprocess.run(["pdffonts", path], capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    return [ln for ln in out.stdout.splitlines()[2:] if ln.strip()]


def save(fig, path: str, check_fonts: bool = True) -> None:
    """Write the PDF and refuse to ship unembedded or Type 3 fonts."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    # tight: trims the dead margin the fixed canvas leaves around the axes.
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    if check_fonts:
        bad = []
        for row in _font_report(path):
            cols = row.split()
            name, kind, emb = cols[0], " ".join(cols[1:3]), cols[-4]
            if emb != "yes":
                bad.append(f"{name}: not embedded")
            elif kind.startswith("Type 3"):
                bad.append(f"{name}: Type 3")
        if bad:
            raise RuntimeError(f"{path} would ship bad fonts: {'; '.join(bad)}")
    print(f"wrote {path}")
