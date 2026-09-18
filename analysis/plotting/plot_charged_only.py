#!/usr/bin/env python3
"""
Charged-only versus energy-flow unfolded thrust, with a ratio panel.

Both inputs are unfolded ROOT files the workflow already wrote, so this only
normalises and draws.

Usage (from repo root):
    python analysis/plotting/plot_charged_only.py --result-dir <run dir> --outdir figures
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import uproot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alephstyle as als

HIST = "unfolded_corrected"


def diff_xsec(path):
    """Values, statistical errors and edges, normalised to a differential rate."""
    with uproot.open(path) as f:
        h = f[HIST]
        v = np.asarray(h.values(), dtype=float)
        err = np.asarray(h.errors(), dtype=float)
        e = np.asarray(h.axis().edges(), dtype=float)
    w = np.diff(e)
    total = v.sum()
    if total <= 0:
        return v, err, e
    # The errors scale with the values, as TH1::Scale does.
    return v / (total * w), err / (total * w), e


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result-dir", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--iterations", type=int, default=5)
    return p.parse_args()


def main():
    args = parse_args()
    rdir = args.result_dir.rstrip("/")
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    ef, ef_err, edges = diff_xsec(os.path.join(
        rdir, "nominal", f"unfolded_nominal_iter{args.iterations}.root"))
    cn, cn_err, _ = diff_xsec(os.path.join(rdir, "experimental", "unfolded_no_neutrals.root"))
    centers = 0.5 * (edges[:-1] + edges[1:])

    fig, ax, rax = als.figure_ratio(aspect=0.95)
    # Matches Fig 16; printed at 0.70\textwidth.
    als.enlarge_y_labels(ax, rax)
    for vals, errs, label, color, marker in (
        (ef, ef_err, "Energy-flow (nominal)", als.C["data"], "o"),
        (cn, cn_err, "Charged-only", als.C["mc_reco"], "s"),
    ):
        m = vals > 0
        ax.errorbar(centers[m], vals[m], yerr=errs[m], ls="none", marker=marker,
                    markerfacecolor="none" if marker == "s" else color,
                    color=color, label=label)

    # Ratio carries the charged-only statistical error only; the two samples
    # share the same events, so the energy-flow error is not independent.
    m = ef > 0
    ratio = np.divide(cn, ef, out=np.zeros_like(ef), where=m)
    ratio_err = np.divide(cn_err, ef, out=np.zeros_like(ef), where=m)
    rax.errorbar(centers[m], ratio[m], yerr=ratio_err[m], ls="none", marker="s",
                 markerfacecolor="none", color=als.C["mc_reco"])

    ax.set_yscale("log")
    # Range from the bins inside the plotted window, not all 50, or the bins
    # below 0.58 leave a decade of empty axis.
    shown = (centers >= als.THRUST_RANGE[0]) & (centers <= als.THRUST_RANGE[1])
    vis = np.concatenate([v[shown & (v > 0)] for v in (ef, cn)])
    ax.set_ylim(vis.min() * 0.4, vis.max() * 30)
    ax.set_ylabel(als.Y["normalized_thrust"])
    ax.set_xlim(*als.THRUST_RANGE)
    ax.legend(loc="upper left", framealpha=0.0)
    rax.set_xlabel(als.X["thrust"])
    rax.set_ylabel(als.RATIO["plain"])
    rax.set_ylim(0.7, 1.4)
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "charged_only_vs_energy_flow.pdf"))


if __name__ == "__main__":
    main()
