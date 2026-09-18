#!/usr/bin/env python3
"""
Generate a 1D histogram of (T_reco - T_gen) integrated over all T_gen.

Reads the matched reco/gen ROOT files (same inputs as
analysis/plotting/plot_thrust_resolution.py) and outputs a single 1D histogram PDF.

Usage (from repo root, after sourcing thisroot.sh):
    python Studies/Phase2_Checks_2026-03-03/scripts/thrust_resolution_1d.py \
        --input-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
        --input-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
        --outdir Studies/Phase2_Checks_2026-03-03/plots/thrust_resolution

Output:
    thrust_resolution_1d.pdf  - 1D histogram of (T_reco - T_gen)

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-05
"""

import argparse
import os

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-reco", required=True)
    p.add_argument("--input-gen",  required=True)
    p.add_argument("--reco-tree",  default="t")
    p.add_argument("--gen-tree",   default="tgen")
    p.add_argument("--outdir",     required=True)
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # --- load trees ---
    ROOT.TH1.AddDirectory(False)
    f_reco = ROOT.TFile.Open(args.input_reco)
    f_gen  = ROOT.TFile.Open(args.input_gen)
    t_reco = f_reco.Get(args.reco_tree)
    t_gen  = f_gen.Get(args.gen_tree)

    # build uniqueID → T_gen map
    gen_map = {}
    for ev in t_gen:
        gen_map[int(ev.uniqueID)] = float(ev.Thrust)

    # fill 1D histogram
    h = ROOT.TH1F("h_delta_t", "", 100, -0.06, 0.06)
    h.GetXaxis().SetTitle("T_{reco} #minus T_{gen}")
    h.GetYaxis().SetTitle("Events (normalized)")

    n_total = 0
    for ev in t_reco:
        uid = int(ev.uniqueID)
        if uid not in gen_map:
            continue
        if ev.passEventSelection != 1:
            continue
        delta = float(ev.Thrust) - gen_map[uid]
        h.Fill(delta)
        n_total += 1

    if h.Integral() > 0:
        h.Scale(1.0 / h.Integral())

    # --- draw ---
    c = ROOT.TCanvas("c", "", 600, 500)
    c.SetLeftMargin(0.13)
    c.SetBottomMargin(0.13)
    c.SetTopMargin(0.08)
    c.SetRightMargin(0.05)

    h.SetLineColor(ROOT.kBlack)
    h.SetLineWidth(2)
    h.GetXaxis().SetTitleSize(0.05)
    h.GetYaxis().SetTitleSize(0.05)
    h.GetXaxis().SetTitleOffset(1.1)
    h.Draw("HIST")

    # ALEPH label
    lbl = ROOT.TLatex()
    lbl.SetNDC(True)
    lbl.SetTextFont(42)
    lbl.SetTextSize(0.040)
    lbl.DrawLatex(0.14, 0.93, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")

    out = os.path.join(args.outdir, "thrust_resolution_1d.pdf")
    c.SaveAs(out)
    print(f"Saved: {out}")

    f_reco.Close()
    f_gen.Close()


if __name__ == "__main__":
    main()
