#!/usr/bin/env python3
"""
Per-component uncertainty figures, one group per file.

  uncertainty_components_statistical.pdf   statistical only, unsigned
  uncertainty_components_unfolding.pdf     iteration up/down, signed
  uncertainty_components_experimental.pdf  the eight experimental variations
  uncertainty_components_theory.pdf        the three generators

Reads only what the unfolding workflow already persisted: the per-variation
`unfolded_corrected` histograms and summary/{binning,cov_*}.csv. The ISR
correction is applied during unfolding, so the stored histograms already carry
it and the shifts here match build_prelim_uncertainty_summary.py bin for bin.

Usage (from repo root):
    python analysis/plotting/plot_uncertainty_components.py \
        --result-dir <run dir> --outdir figures
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
import uproot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alephstyle as als

HIST = "unfolded_corrected"
TRACK_EVENT_VARS = ["ntpc7", "pt04", "ech10", "with_met"]
NEUTRAL_VARS = ["nes_up", "nes_down", "ner"]
THEORY_VARS = ["pythia8", "herwig", "sherpa"]

LABELS = {
    "ntpc7": r"$N_\mathrm{TPC} > 7$",
    "pt04": r"$p_T > 0.4$ GeV",
    "ech10": r"$E_\mathrm{ch} > 10$ GeV",
    "with_met": "Missing-energy cut",
    "nes_up": "NES up",
    "nes_down": "NES down",
    "ner": "NER",
    "no_neutrals": "No-neutrals xcheck",
    "pythia8": "Pythia 8",
    "herwig": "Herwig",
    "sherpa": "Sherpa",
}

# Eight experimental variations need eight separable colours; the previous
# ROOT palette put six of them in adjacent greens and teals.
EXP_STYLE = {
    "ntpc7": ("#1f77b4", "-"),
    "pt04": ("#4c9be8", "--"),
    "ech10": ("#17becf", "-"),
    "with_met": ("#2ca02c", "--"),
    "nes_up": ("#7f3fbf", "-"),
    "nes_down": ("#c47ae0", "--"),
    "ner": ("#8c564b", "-."),
    "no_neutrals": ("#ff7f0e", "-"),
}
THEORY_STYLE = {
    "pythia8": ("#762a83", "-"),
    "herwig": ("#d62728", "--"),
    "sherpa": ("#2ca02c", "-."),
}


def diffxsec(values: np.ndarray, widths: np.ndarray) -> np.ndarray:
    total = values.sum()
    return values / (total * widths) if total > 0 else np.zeros_like(values)


def read_variation(path: str, widths: np.ndarray) -> np.ndarray:
    with uproot.open(path) as f:
        return diffxsec(np.asarray(f[HIST].values(), dtype=float), widths)


def frac_shift(var: np.ndarray, nom: np.ndarray) -> np.ndarray:
    out = np.zeros_like(nom)
    m = nom != 0.0
    out[m] = (var[m] - nom[m]) / nom[m]
    return out


def cov_diag_frac(csv_path: str, nom: np.ndarray) -> np.ndarray:
    cov = np.loadtxt(csv_path, delimiter=",", ndmin=2)
    denom = np.maximum(np.abs(nom), 1e-15)
    return np.sqrt(np.clip(np.diag(cov), 0.0, None)) / denom


# Shared with per_bin_uncertainty_plot.py so both uncertainty figure sets span
# the same x range; below this there are no populated bins.
T_MIN_DISPLAY = 0.55


def panel(out_path, edges, curves, ylim, signed, legend_loc="lower right"):
    """One group of component curves. `curves` is [(label, colour, ls, pct)]."""
    fig, ax = als.figure(aspect=0.62)
    lo, hi = ylim
    for label, color, ls, pct in curves:
        # Clip for display only, so one outlying bin cannot set the y scale.
        y = np.clip(pct, lo, hi)
        ax.plot(np.repeat(edges, 2)[1:-1], np.repeat(y, 2),
                color=color, linestyle=ls, label=label)
    if signed:
        ax.axhline(0.0, color="0.5", lw=plt_lw(), ls="--", zorder=0)
    ax.set_xlim(T_MIN_DISPLAY, edges[-1])
    ax.set_ylim(lo, hi)
    ax.set_xlabel(als.X["thrust"])
    ax.set_ylabel(als.Y["uncert"])
    ncol = 2 if len(curves) > 4 else 1
    ax.legend(loc=legend_loc, ncol=ncol, framealpha=0.0)
    als.header(ax)
    als.save(fig, out_path)


def plt_lw():
    import matplotlib.pyplot as plt
    return plt.rcParams["axes.linewidth"] * 0.8


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result-dir", required=True, help="Unfolding run directory")
    p.add_argument("--outdir", required=True)
    p.add_argument("--iter-down", type=int, default=4)
    p.add_argument("--iter-up", type=int, default=6)
    return p.parse_args()


def main():
    args = parse_args()
    rdir = args.result_dir.rstrip("/")
    summary = os.path.join(rdir, "summary")
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    binning = pd.read_csv(os.path.join(summary, "binning.csv"))
    low, high = binning["low"].values, binning["high"].values
    nom = binning["nominal_diffxsec"].values
    widths = high - low
    edges = np.append(low, high[-1])

    def out(stem):
        return os.path.join(args.outdir, f"uncertainty_components_{stem}.pdf")

    panel(out("statistical"), edges,
          [("Statistical", als.C["total"], "-",
            100.0 * cov_diag_frac(os.path.join(summary, "cov_stat.csv"), nom))],
          ylim=(0.0, 20.0), signed=False, legend_loc="upper right")

    iters = []
    for it, (color, ls) in zip((args.iter_down, args.iter_up),
                               (("#1f77b4", "--"), ("#08306b", "-"))):
        arr = read_variation(os.path.join(rdir, "iteration", f"unfolded_iter{it}.root"), widths)
        iters.append((f"Iteration {it}", color, ls, 100.0 * frac_shift(arr, nom)))
    panel(out("unfolding"), edges, iters, ylim=(-5.0, 5.0), signed=True,
          legend_loc="lower right")

    exp = []
    for v in TRACK_EVENT_VARS + NEUTRAL_VARS + ["no_neutrals"]:
        arr = read_variation(os.path.join(rdir, "experimental", f"unfolded_{v}.root"), widths)
        color, ls = EXP_STYLE[v]
        exp.append((LABELS[v], color, ls, 100.0 * frac_shift(arr, nom)))
    panel(out("experimental"), edges, exp, ylim=(-50.0, 50.0), signed=True,
          legend_loc="lower right")

    theory = []
    for v in THEORY_VARS:
        path = os.path.join(rdir, "theory", f"unfolded_theory_{v}.root")
        arr = read_variation(path, widths) if os.path.exists(path) else np.zeros_like(nom)
        color, ls = THEORY_STYLE[v]
        theory.append((LABELS[v], color, ls, 100.0 * frac_shift(arr, nom)))
    panel(out("theory"), edges, theory, ylim=(-50.0, 50.0), signed=True,
          legend_loc="lower right")


if __name__ == "__main__":
    main()
