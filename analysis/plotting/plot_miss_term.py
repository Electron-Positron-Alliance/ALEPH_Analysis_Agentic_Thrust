#!/usr/bin/env python3
"""
Miss term: gen events with no selected reco partner.

  miss_term_thrust.pdf      all gen / matched / miss, each area-normalised
  miss_term_efficiency.pdf  matched / all gen, versus T_gen

Same inputs, branches and binning as
Studies/Phase2_Checks_2026-03-03/scripts/miss_term_plots.py; the reco/gen match
is vectorised through uproot rather than a per-entry Python loop.

Usage (from repo root):
    python analysis/plotting/plot_miss_term.py \
        --input-reco <..._thrust_nominal_t.root> \
        --input-gen  <..._thrust_no_event_sel_tgen.root> --outdir figures
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import uproot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alephstyle as als

T_MIN, T_MAX, N_BINS = 0.50, 1.00, 50


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-reco", required=True)
    p.add_argument("--input-gen", required=True)
    p.add_argument("--reco-tree", default="t")
    p.add_argument("--gen-tree", default="tgen")
    p.add_argument("--outdir", required=True)
    return p.parse_args()


def normalised(counts):
    total = counts.sum()
    return counts / total if total > 0 else counts


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    with uproot.open(f"{args.input_reco}:{args.reco_tree}") as t:
        a = t.arrays(["uniqueID", "passEventSelection"], library="np")
    passing = np.unique(a["uniqueID"][a["passEventSelection"] == 1].astype(np.int64))

    with uproot.open(f"{args.input_gen}:{args.gen_tree}") as t:
        g = t.arrays(["uniqueID", "Thrust"], library="np")
    gid = g["uniqueID"].astype(np.int64)
    gt = g["Thrust"].astype(np.float64)

    matched = np.isin(gid, passing, assume_unique=False)
    finite = np.isfinite(gt)
    print(f"gen events: {len(gid)}   matched: {matched.sum()}   "
          f"miss: {(~matched).sum()} ({100.0 * (~matched).sum() / max(1, len(gid)):.1f}%)")

    bins = np.linspace(T_MIN, T_MAX, N_BINS + 1)
    h_all, _ = np.histogram(gt[finite], bins=bins)
    h_matched, _ = np.histogram(gt[finite & matched], bins=bins)
    h_miss, _ = np.histogram(gt[finite & ~matched], bins=bins)

    # --- overlay -----------------------------------------------------------
    fig, ax = als.figure(aspect=0.62, scale=1.2)
    for counts, label, color in (
        (h_all, "All gen", als.C["data"]),
        (h_matched, "Matched (reco sel)", als.C["mc_genbefore"]),
        (h_miss, "Miss", als.C["mc_reco"]),
    ):
        ax.stairs(normalised(counts), bins, color=color, label=label)
    ax.set_xlabel(als.X["thrust_gen"])
    ax.set_ylabel("Normalised")
    ax.set_xlim(T_MIN, T_MAX)
    ax.set_ylim(0, None)
    ax.legend(loc="upper left", framealpha=0.0)
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "miss_term_thrust.pdf"))

    # --- efficiency --------------------------------------------------------
    fig, ax = als.figure(aspect=0.62, scale=1.2)
    eff = np.divide(h_matched, h_all, out=np.zeros(len(h_all), dtype=float),
                    where=h_all > 0)
    # Binomial errors, matching TH1::Divide(..., "B").
    err = np.divide(np.sqrt(np.clip(eff * (1.0 - eff), 0.0, None)),
                    np.sqrt(np.maximum(h_all, 1)),
                    out=np.zeros(len(h_all), dtype=float), where=h_all > 0)
    centers = 0.5 * (bins[:-1] + bins[1:])
    ok = h_all > 0
    ax.errorbar(centers[ok], eff[ok], yerr=err[ok], ls="none", marker="o",
                markersize=2.4, color=als.C["mc_genbefore"])
    ax.set_xlabel(als.X["thrust_gen"])
    ax.set_ylabel(als.Y["efficiency"])
    ax.set_xlim(T_MIN, T_MAX)
    ax.set_ylim(0.0, 1.05)
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "miss_term_efficiency.pdf"))


if __name__ == "__main__":
    main()
