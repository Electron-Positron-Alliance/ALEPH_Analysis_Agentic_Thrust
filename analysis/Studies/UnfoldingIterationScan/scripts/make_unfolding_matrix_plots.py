#!/usr/bin/env python3
"""Export unfolding matrix histograms from a ROOT file to PDF plots."""

import argparse
import csv
import os
import sys

import numpy as np
import uproot
from matplotlib.colors import SymLogNorm

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "plotting")))
import alephstyle as als


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", required=True, help="ROOT file from unfold_thrust.py")
    p.add_argument("--outdir", required=True, help="Output directory for PDF plots")
    p.add_argument("--response-prob-hist", default="response_prob_reco_given_gen")
    p.add_argument("--response-counts-hist", default="response_counts")
    p.add_argument("--covariance-hist", default="unfold_covariance")
    p.add_argument("--correlation-hist", default="unfold_correlation")
    return p.parse_args()


def fetch(tf, name):
    """(values, x edges, y edges), or None if the histogram is absent."""
    if name not in tf:
        return None
    h = tf[name]
    return np.asarray(h.values(), dtype=float), h.axes[0].edges(), h.axes[1].edges()


def save_matrix_plot(values, xedges, yedges, xlabel, ylabel, zlabel, outpath,
                     diverging=False, symlog=False):
    fig, ax = als.figure(aspect=0.85)
    if diverging:
        # Signed quantity, so a diverging map centred on zero rather than the
        # sequential kBird this replaces.
        lim = float(np.abs(values).max()) or 1.0
        kw = {"cmap": als.CMAP_DIV}
        if symlog:
            # The endpoint bin's variance exceeds the median off-diagonal entry
            # by orders of magnitude, so a linear scale renders everything else
            # at the zero colour.
            kw["norm"] = SymLogNorm(linthresh=lim * 1e-4, vmin=-lim, vmax=lim, base=10)
        else:
            kw.update(vmin=-lim, vmax=lim)
    else:
        kw = {"cmap": als.CMAP_SEQ, "vmin": 0.0}
    mesh = ax.pcolormesh(xedges, yedges, values.T, **kw)
    # Without this the vector renderer leaves white seams between the quads.
    mesh.set_edgecolor("face")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    cb = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label(zlabel)
    als.header(ax)
    als.save(fig, outpath)


def write_matrix_csv(values, outpath):
    nb = values.shape[0]
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["row_bin"] + [f"bin_{j}" for j in range(1, nb + 1)])
        for i in range(nb):
            writer.writerow([f"bin_{i + 1}"] + [f"{values[i, j]:.10e}" for j in range(nb)])


def write_bin_edges(xedges, outpath):
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bin", "low_edge", "high_edge", "center"])
        for i in range(len(xedges) - 1):
            lo, hi = float(xedges[i]), float(xedges[i + 1])
            writer.writerow([f"bin_{i + 1}", f"{lo:.10e}", f"{hi:.10e}", f"{0.5 * (lo + hi):.10e}"])


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    # The covariance and correlation axes are thrust, not bin index, despite the
    # "Truth bin" titles the producer writes into the ROOT file.
    payload = [
        (args.response_counts_hist, "matrix_response_counts",
         als.X["thrust_reco"], als.X["thrust_gen"], als.Y["counts"], False, False, False),
        (args.response_prob_hist, "matrix_response_probability",
         als.X["thrust_reco"], als.X["thrust_gen"], r"$P(\mathrm{reco}\,|\,\mathrm{gen})$",
         False, False, False),
        (args.covariance_hist, "matrix_unfold_covariance",
         als.X["thrust"], als.X["thrust"], als.Y["covariance"], True, True, True),
        (args.correlation_hist, "matrix_unfold_correlation",
         als.X["thrust"], als.X["thrust"], als.Y["correlation"], True, False, True),
    ]

    with uproot.open(args.input_root) as tf:
        wrote = wrote_csv = 0
        for name, stem, xl, yl, zl, diverging, symlog, export_csv in payload:
            got = fetch(tf, name)
            if got is None:
                print(f"Skipping missing histogram: {name}")
                continue
            values, xedges, yedges = got
            save_matrix_plot(values, xedges, yedges, xl, yl, zl,
                             os.path.join(args.outdir, f"{stem}.pdf"),
                             diverging=diverging, symlog=symlog)
            if export_csv:
                write_matrix_csv(values, os.path.join(args.outdir, f"{stem}.csv"))
                write_bin_edges(xedges, os.path.join(args.outdir, f"{stem}_binning.csv"))
                wrote_csv += 1
            wrote += 1

    if wrote == 0:
        raise RuntimeError("No matrix histograms were found in the input ROOT file")
    print(f"Wrote {wrote} matrix plots and {wrote_csv} matrix CSV exports to: {args.outdir}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
