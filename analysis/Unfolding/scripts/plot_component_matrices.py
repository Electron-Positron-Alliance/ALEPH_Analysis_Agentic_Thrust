#!/usr/bin/env python3
"""
Per-source covariance and correlation matrix figures, one panel per file.

Writes one single-panel figure per uncertainty source plus the total, so the
multipanel layout is assembled in LaTeX (subfigure) rather than baked into the
PDF. That keeps each panel independently sizeable and re-orderable:

  corr_source_{stat,iter,exp,theory,hadronic,isr}.pdf
  cov_source_{stat,iter,exp,theory,hadronic,isr}.pdf
  cov_matrix_total.pdf

The y axis increases upwards, so bin 1 is at the bottom and the diagonal runs
from bottom-left to top-right.

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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ALEPH_LABEL = r"ALEPH archived data, $e^{+}e^{-}$ $\sqrt{s}=91.2$ GeV"

# (csv stem, panel title) in the panel order of the committed figures.
SOURCES = [
    ("cov_stat", "Statistical"),
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


def draw_panel(ax, matrix, title, vlim):
    nb = matrix.shape[0]
    # origin="lower" with extent y from 0 to nb puts bin 1 at the bottom, so the
    # y axis increases upwards and the diagonal runs bottom-left to top-right.
    im = ax.imshow(
        matrix,
        origin="lower",
        cmap="RdBu_r",
        vmin=-vlim,
        vmax=vlim,
        extent=(0, nb, 0, nb),
        interpolation="nearest",
    )
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Thrust bin", fontsize=9)
    ax.set_ylabel("Thrust bin", fontsize=9)
    ax.tick_params(labelsize=8)
    return im


def panel_figure(matrix, vlim, title, cbar_label, out_path):
    """One matrix, one file. Multipanel assembly happens in LaTeX."""
    fig, ax = plt.subplots(figsize=(5.0, 3.9))
    im = draw_panel(ax, matrix, title, vlim)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(cbar_label, fontsize=9)
    cb.ax.tick_params(labelsize=8)
    fig.text(0.5, 0.965, ALEPH_LABEL, ha="center", fontsize=8)
    # bbox_inches="tight" so the colorbar tick labels are not clipped at the edge
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


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

    covs = [load_matrix(args.summary_dir, stem) for stem, _ in SOURCES]
    titles = [title for _, title in SOURCES]
    nb = covs[0].shape[0]
    for stem_title, cov in zip(SOURCES, covs):
        if cov.shape[0] != nb:
            raise ValueError(
                f"{stem_title[0]}.csv is {cov.shape[0]}x{cov.shape[0]}, "
                f"but cov_stat.csv is {nb}x{nb}"
            )

    # One shared covariance scale across sources so panels stay comparable.
    cov_lim = symmetric_limit(covs)
    for (stem, title), cov in zip(SOURCES, covs):
        key = stem.replace("cov_", "")
        panel_figure(correlation_from_covariance(cov), 1.0, title, "Correlation",
                     os.path.join(outdir, f"corr_source_{key}.pdf"))
        panel_figure(cov, cov_lim, title, "Covariance",
                     os.path.join(outdir, f"cov_source_{key}.pdf"))

    cov_total = load_matrix(args.summary_dir, "cov_total")
    panel_figure(cov_total, symmetric_limit([cov_total]), "Total covariance matrix",
                 "Covariance", os.path.join(outdir, "cov_matrix_total.pdf"))

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
