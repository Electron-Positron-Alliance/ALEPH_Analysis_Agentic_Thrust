#!/usr/bin/env python3
"""
Response-matrix MC-statistics covariance by Poisson bootstrap.

RooUnfold's own propagation is unusable here: IncludeSystematics returns the same
unphysical answer for kGammas, kAlphas and kAll (~64x inflation), and kCovToys
needs a RooFit model our plain TH1 RooUnfoldBayes does not provide. So the
response's finite-statistics covariance is estimated directly: each toy gives every
matched gen event a Poisson(1) weight (unfold_thrust.py --set
response_bootstrap_seed=N), re-unfolds the same data, and the sample covariance of
the normalised spectra is written as cov_mcstat.csv.

Only the response and efficiency are fluctuated. tgenBefore is untouched, so the
hadronic-correction statistics remain their own component and are not double
counted.

Usage (from repo root):
    python analysis/Unfolding/scripts/run_response_bootstrap.py \
        --config analysis/Unfolding/unfold_config.json \
        --run-dir analysis/Studies/PreliminaryResult/<run> \
        --ntoys 200 --jobs 25
"""

import argparse
import os
import subprocess
import sys

import numpy as np

BIN_WIDTH_KEYS = ("bins", "xmin", "xmax")


def diffxsec(counts, bin_width):
    total = counts.sum()
    return counts / (total * bin_width) if total > 0 else counts.copy()


def run_toys(args):
    os.makedirs(args.toydir, exist_ok=True)
    pending, running = list(range(args.ntoys)), []
    while pending or running:
        while pending and len(running) < args.jobs:
            k = pending.pop(0)
            out = os.path.join(args.toydir, f"toy_{k:04d}.root")
            if os.path.exists(out) and not args.overwrite:
                continue
            cmd = [
                sys.executable, os.path.join(args.repo_root, "Unfolding", "unfold_thrust.py"),
                "--config", args.config,
                "--set", f"out_root={out}",
                "--set", f"iterations={args.iterations}",
                "--set", "calculate_covariance=false",
                "--set", "apply_hadronic_event_correction=true",
                "--set", f"apply_isr_correction={'true' if args.isr_corr_file else 'false'}",
                "--set", f"response_bootstrap_seed={k + 1}",
            ]
            if args.isr_corr_file:
                cmd += ["--set", f"isr_corr_file={args.isr_corr_file}"]
            log = open(out.replace(".root", ".log"), "w")
            running.append((k, subprocess.Popen(cmd, stdout=log, stderr=log), log))
        done = [t for t in running if t[1].poll() is not None]
        for k, proc, log in done:
            log.close()
            running.remove((k, proc, log))
            if proc.returncode != 0:
                print(f"  !! toy {k} failed rc={proc.returncode}")
        if running:
            running[0][1].wait()
    return sorted(
        os.path.join(args.toydir, f) for f in os.listdir(args.toydir) if f.endswith(".root")
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--ntoys", type=int, default=200)
    p.add_argument("--jobs", type=int, default=25)
    p.add_argument("--iterations", type=int, default=5)
    p.add_argument("--toydir", default=None)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    args.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    args.config = os.path.abspath(args.config)
    args.run_dir = os.path.abspath(args.run_dir)
    args.toydir = args.toydir or os.path.join(args.run_dir, "mcstat_toys")
    isr = os.path.join(args.run_dir, "isr_cache", "isr_correction_cache.root")
    args.isr_corr_file = isr if os.path.exists(isr) else None

    import ROOT
    ROOT.gROOT.SetBatch(True)

    print(f"running {args.ntoys} toys, {args.jobs} at a time -> {args.toydir}")
    paths = run_toys(args)
    print(f"collected {len(paths)} toy files")

    nominal_path = os.path.join(args.run_dir, "nominal", f"unfolded_nominal_iter{args.iterations}.root")
    fh = ROOT.TFile.Open(nominal_path)
    hn = fh.Get("unfolded_corrected")
    nb = hn.GetNbinsX()
    bw = hn.GetXaxis().GetBinWidth(1)
    nom = diffxsec(np.array([hn.GetBinContent(i + 1) for i in range(nb)]), bw)
    # Read the edges out before closing: using hn afterwards segfaults.
    low_edges = [hn.GetXaxis().GetBinLowEdge(i + 1) for i in range(nb)]
    fh.Close()

    rows = []
    for path in paths:
        f = ROOT.TFile.Open(path)
        h = f.Get("unfolded_corrected")
        if not h:
            f.Close()
            continue
        rows.append(diffxsec(np.array([h.GetBinContent(i + 1) for i in range(nb)]), bw))
        f.Close()
    toys = np.vstack(rows)
    print(f"usable toys: {toys.shape[0]}")

    cov = np.cov(toys, rowvar=False, ddof=1)
    out_csv = os.path.join(args.run_dir, "summary", "cov_mcstat.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    np.savetxt(out_csv, cov, delimiter=",", fmt="%.10e")
    print(f"wrote {out_csv}")

    sig = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    frac = np.zeros(nb)
    m = nom > 0
    frac[m] = 100.0 * sig[m] / nom[m]
    print("\nper-bin response MC-stat uncertainty [%] (reported range):")
    for i, lo in enumerate(low_edges):
        if nom[i] > 0 and lo >= 0.58 - 1e-9:
            print(f"   [{lo:.2f},{lo + bw:.2f}) {frac[i]:6.2f}%")


if __name__ == "__main__":
    main()
