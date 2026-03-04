#!/usr/bin/env python3
"""
Per-bin fractional uncertainty breakdown — three separate panel plots.

Produces three separate PDFs (one per group):
  per_bin_uncertainty_stat.pdf     -- statistical + iteration
  per_bin_uncertainty_exp.pdf      -- experimental variations
  per_bin_uncertainty_theory.pdf   -- theory variations

Plus one grouped summary:
  per_bin_uncertainty_grouped.pdf  -- five groups + total

Fractional shifts computed in differential cross-section space, matching
build_prelim_uncertainty_summary.py.  Y-axis limited to 50%.

Usage (from repo root):
    python Studies/Phase2_Checks_2026-03-03/scripts/per_bin_uncertainty_plot.py \
        [--result-dir Studies/PreliminaryResult/2026-02-17_thrust_iter5/] \
        [--outdir     Studies/Phase2_Checks_2026-03-03/plots/uncertainty_breakdown/]

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-04
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

DEFAULT_RESULT_DIR = "Studies/PreliminaryResult/2026-02-17_thrust_iter5/"
DEFAULT_OUTDIR = "Studies/Phase2_Checks_2026-03-03/plots/uncertainty_breakdown/"

T_MIN_DISPLAY = 0.55
T_MAX_DISPLAY = 1.00
Y_MAX = 50.0

# Figure size for individual panels
FIG_W, FIG_H = 7.0, 4.2


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def get_hist_array(root_path, hname="unfolded_corrected"):
    f = ROOT.TFile.Open(root_path, "READ")
    if not f or f.IsZombie():
        raise OSError(f"Cannot open {root_path}")
    h = f.Get(hname)
    if not h:
        raise KeyError(f"'{hname}' not found in {root_path}")
    h = h.Clone()
    f.Close()
    return np.array([h.GetBinContent(i + 1) for i in range(h.GetNbinsX())])


def to_diffxsec(arr, bin_width=0.01):
    """Normalize raw counts → differential cross-section (matches build_prelim_uncertainty_summary.py)."""
    integral = arr.sum()
    return arr / (integral * bin_width) if integral > 0 else arr.copy()


def cov_to_frac(csv_path, nom, n_bins=50):
    df = pd.read_csv(csv_path, header=None)
    diag = np.array([df.iloc[i, i] for i in range(n_bins)], dtype=float)
    frac = np.zeros(n_bins)
    pos = nom > 0
    frac[pos] = np.sqrt(np.maximum(diag[pos], 0.0)) / nom[pos]
    return frac


def absfrac(syst_raw, nom_diffxsec):
    """|diffxsec_syst - diffxsec_nom| / diffxsec_nom."""
    syst_ds = to_diffxsec(syst_raw)
    frac = np.zeros(len(nom_diffxsec))
    pos = nom_diffxsec > 0
    frac[pos] = np.abs(syst_ds[pos] - nom_diffxsec[pos]) / nom_diffxsec[pos]
    return frac


def envelope(fracs_list):
    return np.max(np.vstack(fracs_list), axis=0)


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def apply_common_style(ax):
    ax.tick_params(axis="both", which="major", labelsize=10.5, direction="in",
                   top=True, right=True, length=5)
    ax.tick_params(axis="both", which="minor", direction="in",
                   top=True, right=True, length=3)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)


def step_plot(ax, edges, values_pct, color, lw, ls="-", label=None, alpha=1.0, zorder=2):
    x = np.repeat(edges, 2)[1:-1]
    y = np.repeat(values_pct, 2)
    ax.plot(x, y, color=color, linewidth=lw, linestyle=ls,
            label=label, alpha=alpha, zorder=zorder)


def save_fig(fig, outdir, stem):
    for ext in ("pdf", "png"):
        p = os.path.join(outdir, f"{stem}.{ext}")
        fig.savefig(p, dpi=150 if ext == "png" else None, bbox_inches="tight")
        print(f"Saved: {p}")


ALEPH_LABEL = r"ALEPH archived data  $e^+e^-$  91.2 GeV"


def make_panel_fig():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    # Extra top margin so the ALEPH label above the frame fits cleanly
    fig.subplots_adjust(left=0.11, right=0.97, top=0.88, bottom=0.14)
    return fig, ax


def finish_panel(ax, ylabel):
    ax.set_xlabel("Thrust $T$", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlim(T_MIN_DISPLAY, T_MAX_DISPLAY)
    ax.set_ylim(0, Y_MAX)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5, integer=True))
    apply_common_style(ax)
    # ALEPH label above the top-left of the axes frame (outside the plot area)
    ax.text(0.0, 1.03, ALEPH_LABEL,
            transform=ax.transAxes, fontsize=9.5,
            ha="left", va="bottom", style="italic", fontweight="bold")


def place_legend(ax, loc="best", ncol=1, fontsize=9.5):
    """Place legend; transparent background so it never obscures data."""
    leg = ax.legend(fontsize=fontsize, loc=loc, framealpha=0.0,
                    handlelength=2.2, ncol=ncol,
                    borderpad=0.5, labelspacing=0.35,
                    edgecolor="none")
    return leg


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--result-dir", default=DEFAULT_RESULT_DIR)
    p.add_argument("--outdir", default=DEFAULT_OUTDIR)
    return p.parse_args()


def main():
    args = parse_args()
    rdir = args.result_dir.rstrip("/") + "/"
    summary = rdir + "summary/"
    outdir = args.outdir.rstrip("/") + "/"
    os.makedirs(outdir, exist_ok=True)

    # ------------------------------------------------------------------
    # Binning
    # ------------------------------------------------------------------
    binning = pd.read_csv(summary + "binning.csv")
    low  = binning["low"].values
    high = binning["high"].values
    nom  = binning["nominal_diffxsec"].values

    mask = low >= T_MIN_DISPLAY
    edges_disp = np.append(low[mask], high[mask][-1])

    def m(a): return a[mask]

    # ------------------------------------------------------------------
    # Load systematic arrays (diffxsec fractional shifts)
    # ------------------------------------------------------------------
    frac_stat     = cov_to_frac(summary + "cov_stat.csv",     nom)
    frac_hadronic = cov_to_frac(summary + "cov_hadronic.csv", nom)
    frac_total    = cov_to_frac(summary + "cov_total.csv",    nom)

    iter4    = absfrac(get_hist_array(rdir + "iteration/unfolded_iter4.root"), nom)
    iter6    = absfrac(get_hist_array(rdir + "iteration/unfolded_iter6.root"), nom)
    frac_iter_env = envelope([iter4, iter6])

    ntpc7    = absfrac(get_hist_array(rdir + "experimental/unfolded_ntpc7.root"),    nom)
    pt04     = absfrac(get_hist_array(rdir + "experimental/unfolded_pt04.root"),     nom)
    ech10    = absfrac(get_hist_array(rdir + "experimental/unfolded_ech10.root"),    nom)
    with_met = absfrac(get_hist_array(rdir + "experimental/unfolded_with_met.root"), nom)
    nes_up   = absfrac(get_hist_array(rdir + "experimental/unfolded_nes_up.root"),   nom)
    nes_down = absfrac(get_hist_array(rdir + "experimental/unfolded_nes_down.root"), nom)
    ner      = absfrac(get_hist_array(rdir + "experimental/unfolded_ner.root"),      nom)
    frac_exp_env = envelope([ntpc7, pt04, ech10, with_met, nes_up, nes_down, ner])

    pythia8 = absfrac(get_hist_array(rdir + "theory/unfolded_theory_pythia8.root"), nom)
    herwig  = absfrac(get_hist_array(rdir + "theory/unfolded_theory_herwig.root"),  nom)
    sherpa  = absfrac(get_hist_array(rdir + "theory/unfolded_theory_sherpa.root"),  nom)
    frac_theory_env = envelope([pythia8, herwig, sherpa])

    # ------------------------------------------------------------------
    # Panel 1: Statistical + iteration
    # ------------------------------------------------------------------
    fig, ax = make_panel_fig()

    step_plot(ax, edges_disp, m(frac_stat)*100,
              "#2166ac", 1.6, label="Stat. (covariance)", zorder=3)
    step_plot(ax, edges_disp, m(iter4)*100,
              "#f4a582", 1.3, ls="--", label=r"Iter. $N=4$")
    step_plot(ax, edges_disp, m(iter6)*100,
              "#d6604d", 1.3, ls=":", label=r"Iter. $N=6$")
    step_plot(ax, edges_disp, m(frac_iter_env)*100,
              "#555555", 1.7, ls=(0, (4, 2)), label="Iter. envelope", zorder=3)

    finish_panel(ax, "Uncert. [%]  (Stat.)")
    # Legend: top-right is free for stat panel (stat is small at high T)
    place_legend(ax, loc="upper right", ncol=2)
    save_fig(fig, outdir, "per_bin_uncertainty_stat")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Panel 2: Experimental
    # ------------------------------------------------------------------
    fig, ax = make_panel_fig()

    step_plot(ax, edges_disp, m(ntpc7)*100,
              "#1a9850", 1.3, label=r"$N_\mathrm{TPC}>7$")
    step_plot(ax, edges_disp, m(pt04)*100,
              "#91cf60", 1.3, ls="--", label=r"Track $p_T>0.4$ GeV")
    step_plot(ax, edges_disp, m(ech10)*100,
              "#d73027", 1.3, label=r"$E_\mathrm{ch}>10$ GeV")
    step_plot(ax, edges_disp, m(with_met)*100,
              "#fc8d59", 1.3, ls="--", label=r"Incl. $\vec{p}_\mathrm{miss}$")
    step_plot(ax, edges_disp, m(nes_up)*100,
              "#4575b4", 1.1, ls=":", label=r"NES $+5\%$")
    step_plot(ax, edges_disp, m(nes_down)*100,
              "#74add1", 1.1, ls=(0, (3, 1, 1, 1)), label=r"NES $-5\%$")
    step_plot(ax, edges_disp, m(ner)*100,
              "#9970ab", 1.3, label="NER")
    step_plot(ax, edges_disp, m(frac_exp_env)*100,
              "black", 1.9, ls="--", label="Exp. envelope", zorder=4)

    finish_panel(ax, "Uncert. [%]  (Exp.)")
    # Exp components are large at low T; bulk at high T is small → legend at upper right
    place_legend(ax, loc="upper right", ncol=2, fontsize=8.8)
    save_fig(fig, outdir, "per_bin_uncertainty_exp")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Panel 3: Theory
    # ------------------------------------------------------------------
    fig, ax = make_panel_fig()

    step_plot(ax, edges_disp, m(pythia8)*100,
              "#762a83", 1.6, label="Pythia 8")
    step_plot(ax, edges_disp, m(herwig)*100,
              "#c2a5cf", 1.6, ls="--", label="Herwig 7.3")
    step_plot(ax, edges_disp, m(sherpa)*100,
              "#de77ae", 1.6, ls=":", label="Sherpa")
    step_plot(ax, edges_disp, m(frac_theory_env)*100,
              "black", 1.9, ls="--", label="Theory envelope", zorder=4)

    finish_panel(ax, "Uncert. [%]  (Theory)")
    # Theory is large at high T (near peak); legend at lower right
    place_legend(ax, loc="upper right", ncol=2, fontsize=9.5)
    save_fig(fig, outdir, "per_bin_uncertainty_theory")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Grouped summary (single panel)
    # ------------------------------------------------------------------
    fig, ax = make_panel_fig()

    step_plot(ax, edges_disp, m(frac_stat)*100,
              "#4e79a7", 1.7, label="Statistical")
    step_plot(ax, edges_disp, m(frac_iter_env)*100,
              "#f28e2b", 1.5, ls="--", label="Iteration")
    step_plot(ax, edges_disp, m(frac_exp_env)*100,
              "#59a14f", 1.7, label="Experimental")
    step_plot(ax, edges_disp, m(frac_theory_env)*100,
              "#e15759", 1.7, label="Theory")
    step_plot(ax, edges_disp, m(frac_hadronic)*100,
              "#9467bd", 1.5, ls=":", label="Hadronic")
    step_plot(ax, edges_disp, m(frac_total)*100,
              "black", 2.1, ls="--", label="Total", zorder=5)

    finish_panel(ax, "Uncert. [%]")
    place_legend(ax, loc="upper right", ncol=2, fontsize=9.5)
    save_fig(fig, outdir, "per_bin_uncertainty_grouped")
    plt.close(fig)


if __name__ == "__main__":
    main()
