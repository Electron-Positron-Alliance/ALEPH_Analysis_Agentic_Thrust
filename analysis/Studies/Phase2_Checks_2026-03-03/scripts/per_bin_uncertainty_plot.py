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
        [--result-dir <run dir; defaults to run_dir from inputs.json>] \
        [--outdir     Studies/Phase2_Checks_2026-03-03/plots/uncertainty_breakdown/]

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-04
"""

import argparse
import os
import sys

import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import uproot

# Input locations come from analysis/inputs.json via paths.py, not from a fixed
# run directory, so a rerun does not silently read another run's results.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "plotting")))
import alephstyle as als


def _run(*parts):
    try:
        import paths
        return os.path.join(paths.get("run_dir"), *parts)
    except Exception:
        return os.path.join("Studies", "PreliminaryResult", *parts)


DEFAULT_RESULT_DIR = _run()
DEFAULT_OUTDIR = "Studies/Phase2_Checks_2026-03-03/plots/uncertainty_breakdown/"

T_MIN_DISPLAY, T_MAX_DISPLAY = als.THRUST_RANGE
Y_MAX = 50.0


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def get_hist_array(root_path, hname="unfolded_corrected"):
    with uproot.open(root_path) as f:
        if hname not in f:
            raise KeyError(f"'{hname}' not found in {root_path}")
        return np.asarray(f[hname].values(), dtype=float)


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

def step_plot(ax, edges, values_pct, color, lw, ls="-", label=None, alpha=1.0, zorder=2):
    x = np.repeat(edges, 2)[1:-1]
    y = np.repeat(values_pct, 2)
    ax.plot(x, y, color=color, linewidth=lw, linestyle=ls,
            label=label, alpha=alpha, zorder=zorder)


def save_fig(fig, outdir, stem):
    als.save(fig, os.path.join(outdir, f"{stem}.pdf"))


def make_panel_fig():
    return als.figure(aspect=0.55)


def finish_panel(ax, ylabel):
    ax.set_xlabel(als.X["thrust"])
    ax.set_ylabel(ylabel)
    ax.set_xlim(T_MIN_DISPLAY, T_MAX_DISPLAY)
    ax.set_ylim(0, Y_MAX)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5, integer=True))
    als.header(ax)


def place_legend(ax, loc="best", ncol=1, **kw):
    """Place legend; transparent background so it never obscures data."""
    return ax.legend(loc=loc, framealpha=0.0, ncol=ncol, edgecolor="none", **kw)


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
    als.use()

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
    isr_csv = summary + "cov_isr.csv"
    frac_isr = cov_to_frac(isr_csv, nom) if os.path.exists(isr_csv) else np.zeros_like(nom)
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
    place_legend(ax, loc="upper right", ncol=2)
    save_fig(fig, outdir, "per_bin_uncertainty_exp")

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
    place_legend(ax, loc="upper right", ncol=2)
    save_fig(fig, outdir, "per_bin_uncertainty_theory")

    # ------------------------------------------------------------------
    # Grouped summary (single panel)
    # ------------------------------------------------------------------
    fig, ax = make_panel_fig()

    step_plot(ax, edges_disp, m(frac_stat)*100,
              als.C["stat"], 1.7, label="Statistical")
    step_plot(ax, edges_disp, m(frac_iter_env)*100,
              als.C["iter"], 1.5, ls="--", label="Iteration")
    step_plot(ax, edges_disp, m(frac_exp_env)*100,
              als.C["exp"], 1.7, label="Experimental")
    step_plot(ax, edges_disp, m(frac_theory_env)*100,
              als.C["theory"], 1.7, label="Theory")
    step_plot(ax, edges_disp, m(frac_hadronic)*100,
              als.C["hadronic"], 1.5, ls=":", label="Hadronic")
    step_plot(ax, edges_disp, m(frac_isr)*100,
              als.C["isr"], 1.5, ls=(0, (3, 1, 1, 1)), label="ISR corr.")
    step_plot(ax, edges_disp, m(frac_total)*100,
              als.C["total"], 2.1, ls="--", label="Total", zorder=5)

    finish_panel(ax, "Uncert. [%]")
    place_legend(ax, loc="upper right", ncol=2)
    save_fig(fig, outdir, "per_bin_uncertainty_grouped")


if __name__ == "__main__":
    main()
