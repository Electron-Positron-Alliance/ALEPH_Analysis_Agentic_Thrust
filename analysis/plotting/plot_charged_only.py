#!/usr/bin/env python3
"""
Charged-only versus energy-flow unfolded thrust, with a ratio panel.

Both inputs are unfolded ROOT files the workflow already wrote, so this only
normalises and draws. Replaces the ROOT version in
Studies/Phase2_Checks_2026-03-03/scripts/charged_only_vs_energy_flow.py.

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
    with uproot.open(path) as f:
        h = f[HIST]
        v = np.asarray(h.values(), dtype=float)
        e = np.asarray(h.axis().edges(), dtype=float)
    w = np.diff(e)
    total = v.sum()
    return (v / (total * w) if total > 0 else v), e


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

    ef, edges = diff_xsec(os.path.join(
        rdir, "nominal", f"unfolded_nominal_iter{args.iterations}.root"))
    cn, _ = diff_xsec(os.path.join(rdir, "experimental", "unfolded_no_neutrals.root"))
    centers = 0.5 * (edges[:-1] + edges[1:])

    fig, ax, rax = als.figure_ratio(aspect=0.95)
    for vals, label, color, marker in (
        (ef, "Energy-flow (nominal)", als.C["data"], "o"),
        (cn, "Charged-only", als.C["mc_reco"], "s"),
    ):
        m = vals > 0
        ax.plot(centers[m], vals[m], ls="none", marker=marker, markersize=2.4,
                markerfacecolor="none" if marker == "s" else color,
                color=color, label=label)

    ratio = np.divide(cn, ef, out=np.zeros_like(ef), where=ef > 0)
    m = ef > 0
    rax.plot(centers[m], ratio[m], ls="none", marker="s", markersize=2.4,
             markerfacecolor="none", color=als.C["mc_reco"])

    ax.set_yscale("log")
    ax.set_ylabel(als.Y["normalized_thrust"])
    ax.set_xlim(edges[0], edges[-1])
    ax.legend(loc="upper left", framealpha=0.0)
    rax.set_xlabel(als.X["thrust"])
    rax.set_ylabel(als.RATIO["charged_ef"])
    rax.set_ylim(0.7, 1.4)
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "charged_only_vs_energy_flow.pdf"))


if __name__ == "__main__":
    main()
