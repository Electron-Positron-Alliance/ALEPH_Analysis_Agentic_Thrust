#!/usr/bin/env python3
"""
pwflag=5 (neutral hadron) cos(theta) with and without the cleaning cut.

The nominal analysis applies a cleaning cut that suppresses neutral hadrons
in the range -0.19 <= cos(theta) < -0.18. This script overlays the
cos(theta) distribution with and without that cut to document the affected
region and quantify the suppression.

Uses RDataFrame with:
  cos(theta) = pz / sqrt(px^2 + py^2 + pz^2)  for particles with pwflag == 5

Usage (from repo root):
    python Studies/Phase2_Checks_2026-03-03/scripts/pwflag5_costheta_no_cut.py \
        --input-data     DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
        --input-mc       DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
        --input-data-no-sel DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root \
        --input-mc-no-sel   DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_t.root \
        --outdir Studies/Phase2_Checks_2026-03-03/plots/pwflag5_costheta

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-03
"""

import argparse
import os
import sys

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.TH1.AddDirectory(False)  # prevent histograms from being owned by TFile directories

COSTH_EXPR = "pz[pwflag==5] / sqrt(px[pwflag==5]*px[pwflag==5] + py[pwflag==5]*py[pwflag==5] + pz[pwflag==5]*pz[pwflag==5])"
COSTH_BINS = 100
COSTH_MIN  = -1.0
COSTH_MAX  =  1.0
CUT_LO = -0.19
CUT_HI = -0.18


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-data",        required=True)
    p.add_argument("--input-mc",          required=True)
    p.add_argument("--input-data-no-sel", default=None)
    p.add_argument("--input-mc-no-sel",   default=None)
    p.add_argument("--tree",   default="t")
    p.add_argument("--outdir", required=True)
    return p.parse_args()


def fill_costheta_pwflag5(filepath, treename, apply_event_sel, label):
    df = ROOT.RDataFrame(treename, filepath)
    if apply_event_sel:
        df = df.Filter("passEventSelection == 1")
    df = df.Define("costh5", COSTH_EXPR)
    h = df.Histo1D(
        (f"h_costh5_{label}", ";cos#theta (pwflag=5);Particles (normalized)",
         COSTH_BINS, COSTH_MIN, COSTH_MAX),
        "costh5"
    ).GetValue()
    h.SetDirectory(0)
    return h


def draw_comparison(hists, labels, colors, linestyles, outpath, logy=False,
                    cut_lo=None, cut_hi=None, title=""):
    c = ROOT.TCanvas("c", "", 900, 700)
    c.SetLeftMargin(0.12)
    if logy:
        c.SetLogy()

    norm_hists = []
    for h in hists:
        hc = h.Clone(h.GetName() + "_norm")
        if hc.Integral(1, hc.GetNbinsX()) > 0:
            hc.Scale(1.0 / hc.Integral(1, hc.GetNbinsX()))
        norm_hists.append(hc)

    ymax = max(h.GetMaximum() for h in norm_hists) * (10 if logy else 1.4)

    for i, (h, lab, col, ls) in enumerate(zip(norm_hists, labels, colors, linestyles)):
        h.SetMaximum(ymax)
        if logy:
            h.SetMinimum(1e-7)
        h.SetLineColor(col)
        h.SetLineWidth(2)
        h.SetLineStyle(ls)
        if i == 0:
            h.SetTitle(title)
            h.Draw("HIST")
        else:
            h.Draw("HIST SAME")

    if cut_lo is not None and cut_hi is not None:
        box = ROOT.TBox(cut_lo, 0, cut_hi, ymax)
        box.SetFillColor(int(ROOT.kYellow - 9))
        box.SetFillStyle(3001)
        box.Draw()
        for h in norm_hists:
            h.Draw("HIST SAME")
        for x in [cut_lo, cut_hi]:
            ln = ROOT.TLine(x, 0, x, ymax)
            ln.SetLineColor(int(ROOT.kOrange + 7))
            ln.SetLineStyle(2)
            ln.SetLineWidth(2)
            ln.Draw()

    leg = ROOT.TLegend(0.14, 0.70, 0.55, 0.88)
    leg.SetBorderSize(0)
    for h, lab in zip(norm_hists, labels):
        leg.AddEntry(h, lab, "l")
    leg.Draw()

    lbl = ROOT.TLatex()
    lbl.SetNDC(True)
    lbl.SetTextFont(42)
    lbl.SetTextSize(0.037)
    lbl.DrawLatex(0.12, 0.94, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")

    c.SaveAs(outpath)
    c.Close()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    print("Filling with event selection...")
    h_data_sel = fill_costheta_pwflag5(args.input_data, args.tree, True,  "data_sel")
    h_mc_sel   = fill_costheta_pwflag5(args.input_mc,   args.tree, True,  "mc_sel")

    print("Filling without event selection...")
    h_data_nosel = fill_costheta_pwflag5(
        args.input_data_no_sel or args.input_data, args.tree, False, "data_nosel")
    h_mc_nosel   = fill_costheta_pwflag5(
        args.input_mc_no_sel   or args.input_mc,   args.tree, False, "mc_nosel")

    print("Saving plots...")
    draw_comparison(
        [h_data_sel, h_mc_sel],
        ["Data (with sel)", "MC (with sel)"],
        [int(ROOT.kBlack), int(ROOT.kRed)], [1, 1],
        os.path.join(args.outdir, "pwflag5_costheta_data_vs_mc.pdf"),
        cut_lo=CUT_LO, cut_hi=CUT_HI,
        title="pwflag=5 cos(#theta): data vs MC"
    )
    draw_comparison(
        [h_data_sel, h_data_nosel],
        ["Data (with sel)", "Data (no sel)"],
        [int(ROOT.kBlack), int(ROOT.kBlue+1)], [1, 2],
        os.path.join(args.outdir, "pwflag5_costheta_data_with_vs_without_sel.pdf"),
        cut_lo=CUT_LO, cut_hi=CUT_HI,
        title="pwflag=5 cos(#theta): data with vs without event selection"
    )
    draw_comparison(
        [h_mc_sel, h_mc_nosel],
        ["MC (with sel)", "MC (no sel)"],
        [int(ROOT.kRed), int(ROOT.kOrange+1)], [1, 2],
        os.path.join(args.outdir, "pwflag5_costheta_mc_with_vs_without_sel.pdf"),
        cut_lo=CUT_LO, cut_hi=CUT_HI,
        title="pwflag=5 cos(#theta): MC with vs without event selection"
    )
    draw_comparison(
        [h_data_sel, h_mc_sel, h_data_nosel, h_mc_nosel],
        ["Data sel", "MC sel", "Data no-sel", "MC no-sel"],
        [int(ROOT.kBlack), int(ROOT.kRed), int(ROOT.kBlue+1), int(ROOT.kOrange+1)], [1, 1, 2, 2],
        os.path.join(args.outdir, "pwflag5_costheta_all_logy.pdf"),
        logy=True, cut_lo=CUT_LO, cut_hi=CUT_HI,
        title="pwflag=5 cos(#theta): all comparisons (log scale)"
    )

    fout = ROOT.TFile(os.path.join(args.outdir, "pwflag5_costheta_histograms.root"), "RECREATE")
    for h in [h_data_sel, h_mc_sel, h_data_nosel, h_mc_nosel]:
        h.Write()
    fout.Close()

    print(f"\nDone. Outputs in {args.outdir}")


if __name__ == "__main__":
    main()
