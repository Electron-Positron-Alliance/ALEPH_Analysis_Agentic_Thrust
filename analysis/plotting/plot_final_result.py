#!/usr/bin/env python3
"""
Final unfolded thrust spectrum against ALEPH 2004, with a ratio panel.

Reads only persisted artifacts: summary/{binning,cov_*}.csv, the nominal
unfolded ROOT file (for the detector-level data), and the ALEPH 2004 HEPData
CSV. The total band is the quadrature sum of the six components
build_prelim_uncertainty_summary.py's make_final_plot uses, which excludes the
response MC statistical term that cov_total carries.

Usage (from repo root):
    python analysis/plotting/plot_final_result.py \
        --result-dir <run dir> --aleph-csv <HEPData csv> --outdir figures
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

# The six that make_final_plot sums; cov_mcstat is deliberately not among them.
TOTAL_COMPONENTS = ["stat", "exp", "iter", "theory", "hadronic", "isr"]


def cov_abs(summary_dir: str, stem: str, n: int) -> np.ndarray:
    path = os.path.join(summary_dir, f"cov_{stem}.csv")
    if not os.path.exists(path):
        return np.zeros(n)
    cov = np.loadtxt(path, delimiter=",", ndmin=2)
    return np.sqrt(np.clip(np.diag(cov), 0.0, None))


def load_aleph_2004(csv_path: str) -> dict:
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("#", "THRUST")):
                continue
            rows.append(line.split(","))
    a = np.asarray(rows, dtype=float)
    stat, sys1, sys2 = np.abs(a[:, 4]), np.abs(a[:, 6]), np.abs(a[:, 8])
    return {
        "centers": a[:, 0], "lows": a[:, 1], "highs": a[:, 2], "values": a[:, 3],
        "total": np.sqrt(stat**2 + sys1**2 + sys2**2),
    }


def rebin_to(centers_src, values_src, lows_dst, highs_dst):
    """Average the fine-binned curve into the ALEPH bins."""
    out = np.zeros(len(lows_dst))
    for i, (lo, hi) in enumerate(zip(lows_dst, highs_dst)):
        m = (centers_src >= lo) & (centers_src < hi)
        if m.any():
            out[i] = values_src[m].mean()
    return out


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result-dir", required=True)
    p.add_argument("--aleph-csv", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--nominal-root", default=None)
    p.add_argument("--iterations", type=int, default=5)
    return p.parse_args()


def main():
    args = parse_args()
    rdir = args.result_dir.rstrip("/")
    summary = os.path.join(rdir, "summary")
    nominal_root = args.nominal_root or os.path.join(
        rdir, "nominal", f"unfolded_nominal_iter{args.iterations}.root")
    os.makedirs(args.outdir, exist_ok=True)
    als.use()

    binning = pd.read_csv(os.path.join(summary, "binning.csv"))
    low, high = binning["low"].values, binning["high"].values
    centers, nom = binning["center"].values, binning["nominal_diffxsec"].values
    widths, edges = high - low, np.append(low, high[-1])

    total_abs = np.sqrt(sum(cov_abs(summary, s, len(nom)) ** 2 for s in TOTAL_COMPONENTS))
    aleph = load_aleph_2004(args.aleph_csv)

    with uproot.open(nominal_root) as f:
        raw = np.asarray(f["data_reco"].values(), dtype=float) if "data_reco" in f else None
    if raw is not None:
        raw = raw / (raw.sum() * widths) if raw.sum() > 0 else raw

    fig, ax, rax = als.figure_ratio(aspect=0.95)

    shown = nom > 0
    ax.fill_between(edges[:-1], np.where(shown, nom - total_abs, np.nan),
                    np.where(shown, nom + total_abs, np.nan), step="post",
                    color="0.6", alpha=0.45, linewidth=0, label="Total uncertainty")
    if raw is not None:
        m = raw > 0
        ax.plot(centers[m], raw[m], ls="none", marker="s",
                markerfacecolor="none", color="#e08214", label="Raw data")
    ax.plot(centers[shown], nom[shown], ls="none", marker="o",
            color=als.C["unfolded"], label="Fully corrected")
    ax.errorbar(aleph["centers"], aleph["values"], yerr=aleph["total"], ls="none",
                marker="o", markerfacecolor="none",
                color=als.C["aleph2004"], label="ALEPH 2004")

    ax.set_yscale("log")
    ax.set_ylabel(als.Y["diffxsec"])
    ax.set_xlim(edges[0], edges[-1])
    ax.legend(loc="upper left", framealpha=0.0)

    # Ratio is ALEPH / unfolded, with our total shown as the band around unity
    # so it is not also folded into the points' error bars.
    nom_on_aleph = rebin_to(centers, nom, aleph["lows"], aleph["highs"])
    tot_on_aleph = rebin_to(centers, total_abs, aleph["lows"], aleph["highs"])
    ok = nom_on_aleph > 0
    rel = np.divide(tot_on_aleph, nom_on_aleph, out=np.zeros_like(nom_on_aleph), where=ok)
    rax.fill_between(aleph["lows"][ok], (1 - rel)[ok], (1 + rel)[ok], step="post",
                     color="0.6", alpha=0.45, linewidth=0)
    rax.errorbar(aleph["centers"][ok],
                 np.divide(aleph["values"], nom_on_aleph, out=np.zeros_like(nom_on_aleph),
                           where=ok)[ok],
                 yerr=np.divide(aleph["total"], nom_on_aleph,
                                out=np.zeros_like(nom_on_aleph), where=ok)[ok],
                 ls="none", marker="o", markerfacecolor="none",
                 color=als.C["aleph2004"])
    rax.set_xlabel(als.X["thrust"])
    rax.set_ylabel(als.RATIO["plain"])
    rax.set_ylim(0.7, 1.3)
    als.header(ax)
    als.save(fig, os.path.join(args.outdir, "final_result_uncertainty_breakdown.pdf"))


if __name__ == "__main__":
    main()
