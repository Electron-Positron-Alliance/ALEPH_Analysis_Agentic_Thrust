#!/usr/bin/env python3
"""
Per-source covariance and correlation matrix figures, one panel per file.

Writes one single-panel figure per uncertainty source, so the multipanel layout is
assembled in LaTeX rather than baked into the PDF. That keeps each panel
independently sizeable and re-orderable:

  corr_source_{stat,iter,exp,theory,hadronic,isr}.pdf

The y axis increases upwards, so bin 1 is at the bottom and the diagonal runs
from bottom-left to top-right.

Covariance matrices are deliberately NOT plotted. A covariance adds nothing to the
correlation plus the per-bin magnitudes, since
Cov_ij = rho_ij sqrt(Cov_ii Cov_jj), and it cannot be shown on one linear scale:
the endpoint bin's variance exceeds the median off-diagonal entry by three to five
orders of magnitude, so every other element renders at the zero colour. The
covariances are exported as cov_*.csv instead. The total is still loaded here, to
keep the corr_total cross-check below.

Reads the matrices build_prelim_uncertainty_summary.py writes into <summary>:
cov_{stat,iter,exp,theory,hadronic,isr,total}.csv and corr_total.csv, each a
headerless N x N array. Per-source correlations are not written by that script,
so they are derived here as cov_ij / sqrt(cov_ii * cov_jj).

Usage (from repo root):
    python analysis/Unfolding/scripts/plot_component_matrices.py \
        --summary-dir analysis/Studies/PreliminaryResult/<run>/summary
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "plotting")))
import alephstyle as als

# (csv stem, panel title) in the panel order of the committed figures.
SOURCES = [
    ("cov_stat", "Statistical"),
    ("cov_mcstat", "Response MC statistical"),
    ("cov_iter", "Unfolding iteration"),
    ("cov_exp", "Experimental"),
    ("cov_theory", "Theory"),
    ("cov_hadronic", "Hadronic correction"),
    ("cov_isr", "ISR correction"),
]


def load_matrix(summary_dir, stem):
    path = os.path.join(summary_dir, f"{stem}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"missing input matrix: {path}")
    arr = np.loadtxt(path, delimiter=",", ndmin=2)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"{path} is {arr.shape}, expected a square matrix")
    return arr


def correlation_from_covariance(cov):
    """cov_ij / sqrt(cov_ii cov_jj), leaving null rows/columns at zero."""
    d = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    outer = np.outer(d, d)
    corr = np.zeros_like(cov, dtype=float)
    good = outer > 0.0
    corr[good] = cov[good] / outer[good]
    return np.clip(corr, -1.0, 1.0)


def symmetric_limit(matrices):
    """Shared colour limit, symmetric about zero so the diverging map is centred."""
    peak = max((float(np.abs(m).max()) for m in matrices), default=0.0)
    return peak if peak > 0.0 else 1.0


def panel_figure(matrix, vlim, title, cbar_label, out_path):
    """One matrix, one file. Multipanel assembly happens in LaTeX."""
    nb = matrix.shape[0]
    fig, ax = als.figure(aspect=0.85)
    # origin="lower" with extent y from 0 to nb puts bin 1 at the bottom, so the
    # y axis increases upwards and the diagonal runs bottom-left to top-right.
    im = ax.imshow(
        matrix,
        origin="lower",
        cmap=als.CMAP_DIV,
        vmin=-vlim,
        vmax=vlim,
        extent=(0, nb, 0, nb),
        interpolation="nearest",
        # "auto": an equal-aspect axes leaves slack that the layout engine
        # spends on stray margins rather than on the matrix.
        aspect="auto",
    )
    ax.set_xlabel(als.X["thrust_bin"])
    ax.set_ylabel(als.X["thrust_bin"])
    # imshow turns minor ticks off and draws them over the image; keep them off.
    ax.tick_params(which="minor", bottom=False, top=False, left=False, right=False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label(cbar_label)
    als.header(ax)
    als.panel_label(ax, title)
    als.save(fig, out_path)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--summary-dir", required=True,
                   help="Directory holding cov_*.csv and corr_total.csv")
    p.add_argument("--outdir", default=None,
                   help="Output directory for the PDFs (default: --summary-dir)")
    return p.parse_args()


def main():
    args = parse_args()
    outdir = args.outdir or args.summary_dir
    os.makedirs(outdir, exist_ok=True)
    als.use()

    covs = [load_matrix(args.summary_dir, stem) for stem, _ in SOURCES]
    nb = covs[0].shape[0]
    for stem_title, cov in zip(SOURCES, covs):
        if cov.shape[0] != nb:
            raise ValueError(
                f"{stem_title[0]}.csv is {cov.shape[0]}x{cov.shape[0]}, "
                f"but cov_stat.csv is {nb}x{nb}"
            )

    for (stem, title), cov in zip(SOURCES, covs):
        key = stem.replace("cov_", "")
        panel_figure(correlation_from_covariance(cov), 1.0, title, "Correlation",
                     os.path.join(outdir, f"corr_source_{key}.pdf"))

    cov_total = load_matrix(args.summary_dir, "cov_total")

    # corr_total.csv is written by the summary builder; cross-check that the
    # correlation derived here from cov_total agrees with it.
    corr_total_path = os.path.join(args.summary_dir, "corr_total.csv")
    if os.path.exists(corr_total_path):
        ref = load_matrix(args.summary_dir, "corr_total")
        got = correlation_from_covariance(cov_total)
        if ref.shape == got.shape:
            print(f"corr_total cross-check: max |derived - stored| = "
                  f"{np.abs(ref - got).max():.3e}")


if __name__ == "__main__":
    main()
