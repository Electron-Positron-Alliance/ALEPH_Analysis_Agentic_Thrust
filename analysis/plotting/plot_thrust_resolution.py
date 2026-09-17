#!/usr/bin/env python3
"""
Thrust resolution: (T_reco - T_gen) versus T_gen.

Same inputs, branches and cuts as
Studies/Phase2_Checks_2026-03-03/scripts/thrust_resolution_study.py, but the
reco/gen match is done vectorised through uproot rather than a per-entry
Python loop over both trees.

The ROOT version's y-axis title used `#minus`, which does not render: the
shipped figure shows two stray dots where "T_reco - T_gen" should be.

Usage (from repo root):
    python analysis/plotting/plot_thrust_resolution.py \
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
D_LIM, D_BINS = 0.15, 200


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-reco", required=True)
    p.add_argument("--input-gen", required=True)
    p.add_argument("--reco-tree", default="t")
    p.add_argument("--gen-tree", default="tgen")
    p.add_argument("--outdir", required=True)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    with uproot.open(f"{args.input_reco}:{args.reco_tree}") as t:
        arrs = t.arrays(["uniqueID", "Thrust", "passEventSelection"], library="np")
    sel = arrs["passEventSelection"] == 1
    reco_id = arrs["uniqueID"][sel].astype(np.int64)
    reco_t = arrs["Thrust"][sel].astype(np.float64)

    with uproot.open(f"{args.input_gen}:{args.gen_tree}") as t:
        garrs = t.arrays(["uniqueID", "Thrust"], library="np")
    gen_id = garrs["uniqueID"].astype(np.int64)
    gen_t = garrs["Thrust"].astype(np.float64)

    # Match on uniqueID, the same key the per-entry version used as a dict.
    order = np.argsort(reco_id, kind="stable")
    rid, rt = reco_id[order], reco_t[order]
    pos = np.searchsorted(rid, gen_id)
    pos = np.clip(pos, 0, len(rid) - 1)
    matched = rid[pos] == gen_id

    keep = matched & np.isfinite(gen_t) & (gen_t >= T_MIN) & (gen_t < T_MAX)
    x = gen_t[keep]
    y = rt[pos[keep]] - x
    print(f"reco passing selection: {len(rid)}   gen matched and in range: {keep.sum()}")

    h, xe, ye = np.histogram2d(
        x, y, bins=[N_BINS, D_BINS],
        range=[[T_MIN, T_MAX], [-D_LIM, D_LIM]])

    fig, ax = als.figure(aspect=0.62, scale=1.2)
    mesh = ax.pcolormesh(xe, ye, np.ma.masked_equal(h.T, 0.0), cmap=als.CMAP_SEQ)
    mesh.set_edgecolor("face")
    ax.axhline(0.0, color=als.C["mc_reco"], lw=1.0)
    ax.set_xlabel(als.X["thrust_gen"])
    ax.set_ylabel(als.Y["resolution"])
    cb = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label(als.Y["counts"])
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "thrust_resolution_2d.pdf"))


if __name__ == "__main__":
    main()
