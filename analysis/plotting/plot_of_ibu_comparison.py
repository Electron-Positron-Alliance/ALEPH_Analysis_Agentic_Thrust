#!/usr/bin/env python3
"""
Current IBU result against the OmniFold and IBU reanalyses and ALEPH 2004.

The OmniFold and legacy-IBU curves are built by importing the loaders from
legacy_curves.py rather than reimplementing them, so the ensemble, bootstrap
and systematic weight handling stays in one place. Only the drawing is
replaced, and no part of this needs PyROOT.

Usage (from repo root):
    python analysis/plotting/plot_of_ibu_comparison.py \
        --result-dir <run dir> --aleph-csv <HEPData csv> \
        --legacy-dir <unfold-ee-logtau/Results> --outdir figures
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alephstyle as als
from plot_final_result import TOTAL_COMPONENTS, cov_abs, load_aleph_2004, rebin_to

RATIO_Y_MIN = 0.75


def legacy_curves(legacy_dir, aleph_edges, n_bins, ibu_npz=None, of_h5=None):
    """The canonical loaders, shared with build_prelim_uncertainty_summary.py."""
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "Unfolding", "scripts")))
    import legacy_curves as L

    ibu = L.load_legacy_ibu_thrust_arrays(
        ibu_npz or os.path.join(legacy_dir, "ibu_results.npz"), n_bins)
    of = L.build_legacy_omnifold_thrust_arrays(
        of_h5 or os.path.join(legacy_dir, "unfold_thrust_ee_ZPole_ALEPH.h5"),
        aleph_edges)
    return ibu, of


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result-dir", required=True)
    p.add_argument("--aleph-csv", required=True)
    p.add_argument("--legacy-dir", required=True)
    p.add_argument("--legacy-ibu-npz", default=None)
    p.add_argument("--legacy-of-h5", default=None)
    p.add_argument("--outdir", required=True)
    p.add_argument("--ratio-ymax", type=float, default=1.55)
    return p.parse_args()


def main():
    args = parse_args()
    summary = os.path.join(args.result_dir.rstrip("/"), "summary")
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    binning = pd.read_csv(os.path.join(summary, "binning.csv"))
    centers, nom = binning["center"].values, binning["nominal_diffxsec"].values
    total_abs = np.sqrt(sum(cov_abs(summary, s, len(nom)) ** 2 for s in TOTAL_COMPONENTS))

    aleph = load_aleph_2004(args.aleph_csv)
    # [lows[0]] + highs, as load_aleph_2004_result builds it. Using
    # lows + [highs[-1]] instead differs in the last float digits and
    # moves a few events across bin boundaries.
    edges = np.concatenate([aleph["lows"][:1], aleph["highs"]])
    n = len(aleph["values"])
    ibu, of = legacy_curves(args.legacy_dir, edges, n,
                            args.legacy_ibu_npz, args.legacy_of_h5)

    # ALEPH bins are all 0.01 wide, the same as ours, so this is the 1:1 map
    # ROOT's Rebin performed.
    cur = rebin_to(centers, nom, aleph["lows"], aleph["highs"])
    cur_err = rebin_to(centers, total_abs, aleph["lows"], aleph["highs"])
    ok = cur > 0
    c = 0.5 * (edges[:-1] + edges[1:])

    fig, ax, rax = als.figure_ratio(aspect=0.95)
    ax.fill_between(aleph["lows"][ok], (cur - cur_err)[ok], (cur + cur_err)[ok],
                    step="post", color="0.6", alpha=0.45, linewidth=0,
                    label="Current total uncertainty")
    series = [
        (cur, None, "Current unfolded nominal (IBU)", als.C["unfolded"], "o", True),
        (of["values_thrust"], of["errors_thrust"], "OmniFold reanalysis",
         als.C["mc_genbefore"], "o", False),
        (ibu["values_thrust"], ibu["errors_thrust"], "IBU reanalysis",
         als.C["aleph2004"], "s", False),
        (aleph["values"], aleph["total"], "ALEPH 2004", als.C["mc_gen"], "^", False),
    ]
    for vals, errs, label, color, marker, filled in series:
        m = ok & (np.asarray(vals) > 0)
        ax.errorbar(c[m], np.asarray(vals)[m],
                    yerr=None if errs is None else np.asarray(errs)[m],
                    ls="none", marker=marker, markersize=2.4,
                    markerfacecolor=color if filled else "none",
                    color=color, label=label)
        if errs is None:
            continue
        r = np.divide(np.asarray(vals), cur, out=np.zeros_like(cur), where=ok)
        # Each uncertainty once: the bars carry the curve's own error only,
        # since the current's total is already the band around unity. Same
        # convention as make_final_plot after 23f10c9, and the one the caption
        # in Results.tex describes. The shipped ROOT figure instead propagated
        # the denominator into the bars, showing it twice.
        re = np.divide(np.asarray(errs), cur, out=np.zeros_like(cur), where=ok)
        rax.errorbar(c[m], r[m], yerr=re[m], ls="none", marker=marker,
                     markersize=2.4, markerfacecolor="none", color=color)

    rel = np.divide(cur_err, cur, out=np.zeros_like(cur), where=ok)
    rax.fill_between(aleph["lows"][ok], (1 - rel)[ok], (1 + rel)[ok], step="post",
                     color="0.6", alpha=0.45, linewidth=0)

    ax.set_yscale("log")
    ax.set_ylabel(als.Y["diffxsec"])
    ax.set_xlim(edges[0], edges[-1])
    ax.legend(loc="upper left", framealpha=0.0)
    rax.set_xlabel(als.X["thrust"])
    rax.set_ylabel("Curve / current")
    rax.set_ylim(RATIO_Y_MIN, max(args.ratio_ymax, 1.05))
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "final_result_of_ibu_comparison.pdf"))


if __name__ == "__main__":
    main()
