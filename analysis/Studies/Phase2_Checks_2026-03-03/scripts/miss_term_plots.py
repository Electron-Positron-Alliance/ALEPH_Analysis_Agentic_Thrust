#!/usr/bin/env python3
"""
Miss-term diagnostic plots.

Gen events (from tgen tree) are classified as:
  - matched : uniqueID appears in reco tree AND passes event selection
  - miss    : uniqueID NOT in passing reco events (migration out of acceptance)

Plots thrust, cos(theta_sph), and N_trk distributions for all/matched/miss
gen events, plus an efficiency vs T_gen curve.

Usage (from repo root):
    python Studies/Phase2_Checks_2026-03-03/scripts/miss_term_plots.py \
        --input-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
        --input-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
        --outdir Studies/Phase2_Checks_2026-03-03/plots/miss_term

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
ROOT.gStyle.SetOptTitle(0)
ROOT.TH1.AddDirectory(False)  # prevent histograms from being owned by TFile directories

T_MIN  = 0.50
T_MAX  = 1.00
N_BINS = 50


def parse_args():
    p = argparse.ArgumentParser(description="Miss-term diagnostic plots")
    p.add_argument("--input-reco",
                   default="DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root",
                   help="MC reco ROOT file (tree: t)")
    p.add_argument("--input-gen",
                   default="DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root",
                   help="MC gen ROOT file (tree: tgen)")
    p.add_argument("--reco-tree",  default="t")
    p.add_argument("--gen-tree",   default="tgen")
    p.add_argument("--outdir",     default="Studies/Phase2_Checks_2026-03-03/plots/miss_term")
    return p.parse_args()


def build_passing_ids(reco_file, reco_tree):
    """Return set of uniqueIDs that pass event selection in reco tree."""
    f = ROOT.TFile.Open(reco_file, "READ")
    if not f or f.IsZombie():
        sys.exit(f"Cannot open reco file: {reco_file}")
    tree = f.Get(reco_tree)
    if not tree:
        sys.exit(f"Cannot find tree '{reco_tree}' in {reco_file}")
    passing = set()
    for i in range(tree.GetEntries()):
        tree.GetEntry(i)
        if tree.passEventSelection:
            passing.add(int(tree.uniqueID))
    f.Close()
    print(f"  {len(passing)} reco events pass event selection")
    return passing


def fill_histograms(passing_ids, gen_file, gen_tree):
    """
    Fill thrust, cos(theta_sph), and n_trk for all/matched/miss gen events.
    Returns dicts of histograms.
    """
    f = ROOT.TFile.Open(gen_file, "READ")
    if not f or f.IsZombie():
        sys.exit(f"Cannot open gen file: {gen_file}")
    tree = f.Get(gen_tree)
    if not tree:
        sys.exit(f"Cannot find tree '{gen_tree}' in {gen_file}")

    hists = {}
    for cat in ("all", "matched", "miss"):
        hists[f"thrust_{cat}"] = ROOT.TH1F(
            f"h_thrust_{cat}", ";T_{gen};Events", N_BINS, T_MIN, T_MAX)
        hists[f"costh_{cat}"]  = ROOT.TH1F(
            f"h_costh_{cat}",  ";cos#theta_{sph,gen};Events", 50, -1.0, 1.0)
        hists[f"ntrk_{cat}"]   = ROOT.TH1F(
            f"h_ntrk_{cat}",   ";N_{trk,gen};Events", 60, 0, 60)

    # efficiency numerator / denominator
    h_eff_num = ROOT.TH1F("h_eff_num", ";T_{gen};Matched events", N_BINS, T_MIN, T_MAX)
    h_eff_den = ROOT.TH1F("h_eff_den", ";T_{gen};All gen events", N_BINS, T_MIN, T_MAX)

    n = tree.GetEntries()
    n_matched = 0
    n_miss    = 0
    print(f"  Classifying {n} gen events as matched/miss...")
    for i in range(n):
        tree.GetEntry(i)
        uid    = int(tree.uniqueID)
        thrust = float(tree.Thrust)
        is_matched = (uid in passing_ids)

        if is_matched:
            n_matched += 1
            cat = "matched"
        else:
            n_miss += 1
            cat = "miss"

        if math.isfinite(thrust):
            hists[f"thrust_all"].Fill(thrust)
            hists[f"thrust_{cat}"].Fill(thrust)
            h_eff_den.Fill(thrust)
            if is_matched:
                h_eff_num.Fill(thrust)

        # cos(theta_sph) — stored as cos(STheta) in gen tree
        try:
            costh = math.cos(float(tree.STheta))
            if math.isfinite(costh):
                hists["costh_all"].Fill(costh)
                hists[f"costh_{cat}"].Fill(costh)
        except AttributeError:
            pass

        # N_trk (number of stable particles at gen level)
        try:
            ntrk = int(tree.NTrk)
            hists["ntrk_all"].Fill(ntrk)
            hists[f"ntrk_{cat}"].Fill(ntrk)
        except AttributeError:
            pass

    f.Close()
    print(f"  {n_matched} matched, {n_miss} miss ({100.*n_miss/max(1,n):.1f}% miss rate)")
    return hists, h_eff_num, h_eff_den


def draw_overlay(h_all, h_matched, h_miss, xlabel, outpath):
    """Draw all/matched/miss overlaid, normalized to unit area."""
    c = ROOT.TCanvas("c", "", 800, 600)
    c.SetLeftMargin(0.12)

    cols = {h_all: int(ROOT.kBlack), h_matched: int(ROOT.kBlue+1), h_miss: int(ROOT.kRed)}
    labs = {h_all: "All gen", h_matched: "Matched (reco sel)", h_miss: "Miss"}
    hs = [h_all, h_matched, h_miss]

    ymax = 0.0
    for h in hs:
        if h.Integral(1, h.GetNbinsX()) > 0:
            h.Scale(1.0 / h.Integral(1, h.GetNbinsX()))
        ymax = max(ymax, h.GetMaximum())

    for i, h in enumerate(hs):
        h.SetLineColor(cols[h])
        h.SetLineWidth(2)
        h.SetMaximum(ymax * 1.3)
        h.GetXaxis().SetTitle(xlabel)
        h.GetYaxis().SetTitle("Normalized")
        if i == 0:
            h.Draw("HIST")
        else:
            h.Draw("HIST SAME")

    leg = ROOT.TLegend(0.55, 0.65, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.040)
    for h in hs:
        leg.AddEntry(h, labs[h], "l")
    leg.Draw()

    alabel = ROOT.TLatex()
    alabel.SetNDC(True)
    alabel.SetTextSize(0.040)
    alabel.SetTextFont(42)
    alabel.DrawLatex(0.14, 0.945, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")

    c.SaveAs(outpath)
    c.Close()


def draw_efficiency(h_num, h_den, outpath):
    """Draw reco efficiency = matched / all as a function of T_gen."""
    h_eff = h_num.Clone("h_eff")
    # Binomial errors: the numerator is a SUBSET of the denominator (matched gen
    # events out of all gen events), so the two are correlated and TH1::Divide's
    # default uncorrelated propagation is wrong. Without "B" the error is
    # overstated by a factor 7 at the largest and 11 on average at ~1e5
    # events/bin, which is what makes the efficiency panel appear to span the
    # full 0-1 range.
    h_eff.Divide(h_num, h_den, 1.0, 1.0, "B")
    h_eff.SetTitle(";T_{gen};Reco efficiency (matched / all gen)")
    h_eff.SetLineColor(int(ROOT.kBlue + 1))
    h_eff.SetLineWidth(2)
    h_eff.SetMinimum(0.0)
    h_eff.SetMaximum(1.1)

    c = ROOT.TCanvas("ceff", "", 800, 600)
    c.SetTopMargin(0.08)
    h_eff.Draw("E1")

    line = ROOT.TLine(T_MIN, 1.0, T_MAX, 1.0)
    line.SetLineColor(int(ROOT.kGray + 2))
    line.SetLineStyle(2)
    line.Draw()

    alabel = ROOT.TLatex()
    alabel.SetNDC(True)
    alabel.SetTextSize(0.040)
    alabel.SetTextFont(42)
    alabel.DrawLatex(0.14, 0.945, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")

    c.SaveAs(outpath)
    c.Close()
    return h_eff


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    print("Building passing reco ID set...")
    passing_ids = build_passing_ids(args.input_reco, args.reco_tree)

    print("Filling gen histograms...")
    hists, h_eff_num, h_eff_den = fill_histograms(
        passing_ids, args.input_gen, args.gen_tree)

    print("Saving plots...")
    draw_overlay(hists["thrust_all"], hists["thrust_matched"], hists["thrust_miss"],
                 "T_{gen}",
                 os.path.join(args.outdir, "miss_term_thrust.pdf"))

    draw_overlay(hists["costh_all"], hists["costh_matched"], hists["costh_miss"],
                 "cos#theta_{sph,gen}",
                 os.path.join(args.outdir, "miss_term_costheta.pdf"))

    draw_overlay(hists["ntrk_all"], hists["ntrk_matched"], hists["ntrk_miss"],
                 "N_{trk,gen}",
                 os.path.join(args.outdir, "miss_term_ntrk.pdf"))

    h_eff = draw_efficiency(h_eff_num, h_eff_den,
                            os.path.join(args.outdir, "miss_term_efficiency.pdf"))

    # Save to ROOT file
    fout = ROOT.TFile(os.path.join(args.outdir, "miss_term_histograms.root"), "RECREATE")
    for h in hists.values():
        h.Write()
    h_eff_num.Write()
    h_eff_den.Write()
    h_eff.Write()
    fout.Close()

    print(f"\nDone. Outputs in {args.outdir}")


if __name__ == "__main__":
    main()
