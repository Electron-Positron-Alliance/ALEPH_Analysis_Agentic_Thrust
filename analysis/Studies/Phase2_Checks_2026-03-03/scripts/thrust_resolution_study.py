#!/usr/bin/env python3
"""
Thrust resolution study: (T_reco - T_gen) vs T_gen.

Reads two separate ROOT files:
  - reco file: tree 't',    branch 'Thrust', filtered by passEventSelection==1
  - gen  file: tree 'tgen', branch 'Thrust'
Events are matched by uniqueID.

Usage (from repo root, after sourcing thisroot.sh or activating py312):
    python Studies/Phase2_Checks_2026-03-03/scripts/thrust_resolution_study.py \
        --input-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
        --input-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
        --outdir Studies/Phase2_Checks_2026-03-03/plots/thrust_resolution

Outputs:
  thrust_resolution_2d.pdf        - 2D (T_reco - T_gen) vs T_gen
  thrust_resolution_profile.pdf   - sigma(T) as a function of T_gen
  thrust_resolution_bias.pdf      - mean (T_reco - T_gen) as a function of T_gen

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-03
"""

import argparse
import math
import os
import sys

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

T_MIN  = 0.50
T_MAX  = 1.00
N_BINS = 50


def parse_args():
    p = argparse.ArgumentParser(description="Thrust resolution study")
    p.add_argument("--input-reco", required=True,
                   help="MC reco ROOT file (tree: t, branch: Thrust)")
    p.add_argument("--input-gen", required=True,
                   help="MC gen ROOT file (tree: tgen, branch: Thrust)")
    p.add_argument("--reco-tree",  default="t")
    p.add_argument("--gen-tree",   default="tgen")
    p.add_argument("--outdir",     required=True)
    return p.parse_args()


def build_reco_lookup(reco_file, reco_tree):
    """Return dict {uniqueID -> T_reco} for events passing event selection."""
    f = ROOT.TFile.Open(reco_file, "READ")
    if not f or f.IsZombie():
        sys.exit(f"Cannot open reco file: {reco_file}")
    tree = f.Get(reco_tree)
    if not tree:
        sys.exit(f"Cannot find tree '{reco_tree}' in {reco_file}")
    lookup = {}
    n = tree.GetEntries()
    print(f"  Building reco lookup from {n} reco entries...")
    for i in range(n):
        tree.GetEntry(i)
        if not tree.passEventSelection:
            continue
        uid = int(tree.uniqueID)
        thrust = float(tree.Thrust)
        if math.isfinite(thrust) and T_MIN <= thrust < T_MAX:
            lookup[uid] = thrust
    f.Close()
    print(f"  {len(lookup)} reco events pass event selection and thrust range")
    return lookup


def match_and_fill(reco_lookup, gen_file, gen_tree, h2d, h_profile_means, h_profile_rms):
    """Loop gen tree, match by uniqueID, fill resolution histograms."""
    f = ROOT.TFile.Open(gen_file, "READ")
    if not f or f.IsZombie():
        sys.exit(f"Cannot open gen file: {gen_file}")
    tree = f.Get(gen_tree)
    if not tree:
        sys.exit(f"Cannot find tree '{gen_tree}' in {gen_file}")

    # Collect per-slice residuals for profile
    slices = {i: [] for i in range(N_BINS)}
    n = tree.GetEntries()
    matched = 0
    print(f"  Matching {n} gen entries to reco lookup...")
    for i in range(n):
        tree.GetEntry(i)
        uid = int(tree.uniqueID)
        if uid not in reco_lookup:
            continue
        t_gen  = float(tree.Thrust)
        t_reco = reco_lookup[uid]
        if not (math.isfinite(t_gen) and T_MIN <= t_gen < T_MAX):
            continue
        delta = t_reco - t_gen
        h2d.Fill(t_gen, delta)
        # bin index for profile
        ibin = int((t_gen - T_MIN) / (T_MAX - T_MIN) * N_BINS)
        ibin = max(0, min(N_BINS - 1, ibin))
        slices[ibin].append(delta)
        matched += 1

    f.Close()
    print(f"  {matched} matched pairs")

    # Fill profile histograms
    for ibin, deltas in slices.items():
        if len(deltas) < 5:
            continue
        mean = sum(deltas) / len(deltas)
        rms  = math.sqrt(sum((d - mean)**2 for d in deltas) / len(deltas))
        # bin center
        t_center = T_MIN + (ibin + 0.5) * (T_MAX - T_MIN) / N_BINS
        h_profile_means.Fill(t_center, mean)
        h_profile_rms.Fill(t_center, rms)


def draw_2d(h2d, outpath):
    c = ROOT.TCanvas("c2d", "", 800, 700)
    c.SetRightMargin(0.15)
    c.SetTopMargin(0.08)
    h2d.Draw("COLZ")
    # Zero line
    line = ROOT.TLine(T_MIN, 0, T_MAX, 0)
    line.SetLineColor(ROOT.kRed)
    line.SetLineWidth(2)
    line.Draw()
    # ALEPH label, drawn in the top margin to clear the COLZ palette
    lbl = ROOT.TLatex()
    lbl.SetNDC(True)
    lbl.SetTextFont(42)
    lbl.SetTextSize(0.037)
    lbl.DrawLatex(0.12, 0.945, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")
    c.SaveAs(outpath)
    c.Close()


def draw_profile(h, ylabel, outpath, ref_line=None):
    c = ROOT.TCanvas("cp", "", 800, 600)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(0.7)
    h.SetLineColor(ROOT.kBlue + 1)
    h.Draw("E1")
    if ref_line is not None:
        line = ROOT.TLine(T_MIN, ref_line, T_MAX, ref_line)
        line.SetLineColor(ROOT.kRed)
        line.SetLineStyle(2)
        line.Draw()
    h.GetYaxis().SetTitle(ylabel)
    h.GetXaxis().SetTitle("T_{gen}")
    # ALEPH label
    lbl = ROOT.TLatex()
    lbl.SetNDC(True)
    lbl.SetTextFont(42)
    lbl.SetTextSize(0.040)
    lbl.DrawLatex(0.14, 0.93, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")
    c.SaveAs(outpath)
    c.Close()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # Resolution 2D: x=T_gen, y=(T_reco - T_gen)
    h2d = ROOT.TH2F("h_res_2d",
                    ";T_{gen};T_{reco} #minus T_{gen}",
                    N_BINS, T_MIN, T_MAX,
                    200, -0.15, 0.15)

    h_mean = ROOT.TH1F("h_res_mean",
                       ";T_{gen};Mean(T_{reco} #minus T_{gen})",
                       N_BINS, T_MIN, T_MAX)
    h_rms  = ROOT.TH1F("h_res_rms",
                       ";T_{gen};RMS(T_{reco} #minus T_{gen})",
                       N_BINS, T_MIN, T_MAX)

    print("Building reco lookup...")
    reco_lookup = build_reco_lookup(args.input_reco, args.reco_tree)

    print("Matching to gen tree and filling histograms...")
    match_and_fill(reco_lookup, args.input_gen, args.gen_tree,
                   h2d, h_mean, h_rms)

    print("Saving plots...")
    draw_2d(h2d, os.path.join(args.outdir, "thrust_resolution_2d.pdf"))
    draw_profile(h_mean, "Mean(T_{reco} #minus T_{gen})",
                 os.path.join(args.outdir, "thrust_resolution_bias.pdf"),
                 ref_line=0.0)
    draw_profile(h_rms, "#sigma(T_{reco} #minus T_{gen})",
                 os.path.join(args.outdir, "thrust_resolution_profile.pdf"))

    # Save histograms to ROOT file
    fout = ROOT.TFile(os.path.join(args.outdir, "thrust_resolution_histograms.root"), "RECREATE")
    h2d.Write()
    h_mean.Write()
    h_rms.Write()
    fout.Close()

    print(f"\nDone. Outputs in {args.outdir}")


if __name__ == "__main__":
    main()
