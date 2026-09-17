#!/usr/bin/env python3
"""
Detector-level data/MC figures: the pwflag particle sets and the event variables.

Reads the per-sample `*_hists.root` that DataProcessing/plotting/plot.py already
writes (plot.py:272, write_sample_hists), so this does no event loop and no
selection of its own. The histograms are normalised and rebinned there; this
only draws them.

Usage (from repo root):
    python analysis/plotting/plot_detector_level.py --hist-dir <dir> --outdir figures
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import uproot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alephstyle as als

# key -> (label, colour, whether it is drawn as points with error bars)
SAMPLES = [
    ("data", "Data", als.C["data"], True),
    ("mc_reco", "MC reco", als.C["mc_reco"], False),
    ("mc_gen", "MC gen", als.C["mc_gen"], False),
    ("mc_genbefore", "MC genBefore", als.C["mc_genbefore"], False),
]

# Which stem in the *_hists.root filename belongs to which sample key.
FILE_KEYS = [
    ("_thrust_no_event_sel_tgenBefore_hists.root", "mc_genbefore"),
    ("_thrust_no_event_sel_tgen_hists.root", "mc_gen"),
    ("LEP1Data", "data"),
    ("alephMCRecoAfterCutPaths", "mc_reco"),
]

PWFLAG_NAMES = ["Charged tracks", "Charged leptons 1", "Charged leptons 2",
                "V0", "Photons", "Neutral hadrons"]

# Quantities drawn on a log y axis, matching PlotConfig's SetLogy.
LOGY = {"d0", "z0", "energy", "mass", "pt", "pmag", "eCh", "evis", "missP",
        "ntrk", "ntrkPlusNeu", "nneu", "sprime"}

# (1/N) dN/dX with the actual observable, not the "1/N dN/dX" placeholder the
# ROOT config used on all 58 figures.
YSYMBOL = {
    "cosTheta": r"\cos\theta", "phi": r"\varphi", "pt": "p_T", "pmag": r"|\vec{p}|",
    "d0": "d_0", "z0": "z_0", "ntpc": r"N_\mathrm{TPC}", "energy": "E", "mass": "m",
    "ntrk": r"N_\mathrm{trk}", "ntrkPlusNeu": r"N_\mathrm{trk{+}neu}",
    "eCh": r"E_\mathrm{ch}", "cosThetaSph": r"\cos\theta_\mathrm{Sph}",
}

XLABEL = {
    "cosTheta": als.X["cosTheta"], "phi": als.X["phi"], "pt": als.X["pt"],
    "pmag": als.X["pmag"], "d0": als.X["d0"], "z0": als.X["z0"],
    "ntpc": als.X["ntpc"], "energy": als.X["energy"], "mass": als.X["mass"],
    "ntrk": als.X["ntrk"], "ntrkPlusNeu": als.X["ntrkPlusNeu"],
    "eCh": als.X["eCh"], "cosThetaSph": als.X["cosThetaSph"],
}


def ylabel_for(qty):
    sym = YSYMBOL.get(qty, "X")
    return rf"$(1/N)\,\mathrm{{d}}N/\mathrm{{d}}{sym}$"


def resolve_sample_files(hist_dir):
    """Map sample key -> *_hists.root path, by filename."""
    found = {}
    for path in sorted(glob.glob(os.path.join(hist_dir, "*_hists.root"))):
        base = os.path.basename(path)
        for needle, key in FILE_KEYS:
            if needle in base and key not in found:
                found[key] = path
                break
    return found


def read(path, name):
    with uproot.open(path) as f:
        if name not in f:
            return None
        h = f[name]
        return (np.asarray(h.values(), dtype=float),
                np.asarray(h.errors(), dtype=float),
                np.asarray(h.axis().edges(), dtype=float))


def draw(var, files, xlabel, ylabel, logy, category, out_path):
    series = []
    for key, label, color, is_data in SAMPLES:
        if key not in files:
            continue
        got = read(files[key], var)
        if got is None:
            continue
        series.append((label, color, is_data, *got))
    if not series:
        return False
    if not any(s[2] for s in series):
        return False

    fig, ax, rax = als.figure_ratio(aspect=0.95)
    edges = series[0][5]
    centers = 0.5 * (edges[:-1] + edges[1:])
    data = next(s for s in series if s[2])

    for label, color, is_data, vals, errs, edg in series:
        if is_data:
            ax.errorbar(centers, vals, yerr=errs, fmt="o", color=color,
                        markersize=2.2, label=label, zorder=5)
        else:
            ax.stairs(vals, edg, color=color, label=label)
            ratio = np.divide(vals, data[3], out=np.zeros_like(vals),
                              where=data[3] > 0)
            rax.stairs(ratio, edg, color=color)

    # Neutral pwflag categories have no d0/z0/ntpc, so some panels are empty.
    pos = [s[3][s[3] > 0] for s in series if (s[3] > 0).any()]
    if logy:
        ax.set_yscale("log")
        if pos:
            allpos = np.concatenate(pos)
            ax.set_ylim(allpos.min() * 0.5, allpos.max() * 50)
    else:
        peak = max((s[3].max() for s in series), default=0.0)
        ax.set_ylim(0, peak * 1.5 if peak > 0 else 1.0)

    ax.set_ylabel(ylabel)
    ax.set_xlim(edges[0], edges[-1])
    rax.set_xlabel(xlabel)
    rax.set_ylabel(als.RATIO["mc_data"])
    # 0.1-1.9 as the ROOT style used: MC genBefore has no event selection
    # and differs from data by more than a +-50% window would show.
    rax.set_ylim(0.1, 1.9)
    handles, labels = ax.get_legend_handles_labels()
    order = sorted(range(len(labels)), key=lambda i: labels[i] != "Data")
    # The pwflag category names the legend rather than extending the header,
    # which at this panel width would overrun the beam/energy label.
    ax.legend([handles[i] for i in order], [labels[i] for i in order],
              loc="upper right", framealpha=0.0, title=category)
    als.header(ax)
    als.save(fig, out_path)
    return True


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hist-dir", required=True,
                   help="Directory holding the *_hists.root written by plot.py")
    p.add_argument("--outdir", required=True)
    p.add_argument("--only", nargs="+", default=None)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    als.use()
    files = resolve_sample_files(args.hist_dir)
    if "data" not in files:
        raise SystemExit(f"no data *_hists.root found in {args.hist_dir}")

    jobs = []
    for pw in range(6):
        for qty in ["cosTheta", "phi", "pt", "pmag", "d0", "z0", "ntpc", "energy", "mass"]:
            jobs.append((f"pwflag{pw}_{qty}", XLABEL[qty], ylabel_for(qty),
                         PWFLAG_NAMES[pw]))
    for var in ["ntrk", "ntrkPlusNeu", "eCh", "cosThetaSph"]:
        jobs.append((var, XLABEL[var], ylabel_for(var), None))

    wrote = 0
    for var, xlabel, ylabel, category in jobs:
        if args.only and var not in args.only:
            continue
        ok = draw(var, files, xlabel, ylabel,
                  var.split("_")[-1] in LOGY or var in LOGY,
                  category, os.path.join(args.outdir, f"{var}.pdf"))
        wrote += bool(ok)
    print(f"wrote {wrote} detector-level figures to {args.outdir}")


if __name__ == "__main__":
    main()
