#!/usr/bin/env python3
"""
Phi spectrum investigation: look for 24-fold HCAL structure in pwflag=4,5.

Computes phi = atan2(py, px) for each particle category and overlays
data vs MC (reco-level) and reco vs gen (MC-level) to determine whether
the excess phi modulation seen in pwflag=4 is of detector (HCAL 24-fold)
or generator (JETSET) origin.

Usage (from repo root):
    python Studies/Phase2_Checks_2026-03-03/scripts/phi_spectrum_investigation.py \
        --input-data    DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
        --input-mc-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
        --input-mc-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
        --outdir Studies/Phase2_Checks_2026-03-03/plots/phi_spectrum

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-03
"""

import argparse
import os
import sys

import ROOT

# Input locations come from analysis/inputs.json via paths.py, not from a fixed
# directory, so a rerun does not silently read another run's ntuples.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))


def _temp(name):
    try:
        import paths
        return paths.temp(name)
    except Exception:
        return os.path.join("DataProcessing", "temp", name)
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)
ROOT.TH1.AddDirectory(False)  # prevent histograms from being owned by TFile directories

PHI_BINS = 120  # reduced from 360 → smoother MC-gen distribution; still resolves 24-fold HCAL structure
PHI_MIN  = -3.14159265
PHI_MAX  =  3.14159265

PWFLAGS = {
    0: ("charged tracks",   int(ROOT.kBlue+1)),
    4: ("photons",          int(ROOT.kOrange+1)),
    5: ("neutral hadrons",  int(ROOT.kGreen+2)),
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-data",
                   default=_temp("LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root"),
                   help="Data reco ROOT file (tree: t)")
    p.add_argument("--input-mc-reco",
                   default=_temp("alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root"),
                   help="MC reco ROOT file (tree: t)")
    p.add_argument("--input-mc-gen",
                   default=_temp("alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root"),
                   help="MC gen ROOT file (tree: tgen)")
    p.add_argument("--reco-tree",  default="t")
    p.add_argument("--gen-tree",   default="tgen")
    p.add_argument("--outdir",     default="Studies/Phase2_Checks_2026-03-03/plots/phi_spectrum")
    return p.parse_args()


def phi_expr(pw):
    """RDataFrame expression for phi = atan2(py, px) for given pwflag."""
    return (f"atan2(py[pwflag=={pw}], px[pwflag=={pw}])")


def fill_phi_hist(filepath, treename, apply_event_sel, pwflag, label):
    """Fill phi histogram for given pwflag using RDataFrame."""
    df = ROOT.RDataFrame(treename, filepath)
    if apply_event_sel:
        df = df.Filter("passEventSelection == 1")
    col = f"phi_pw{pwflag}_{label}"
    df = df.Define(col, phi_expr(pwflag))
    h = df.Histo1D(
        (f"h_{col}", f";#phi (pwflag={pwflag});Particles (normalized)",
         PHI_BINS, PHI_MIN, PHI_MAX),
        col
    ).GetValue()
    h.SetDirectory(0)
    return h


def draw_phi_comparison(hists, labels, colors, outpath, title="",
                        n_fold=None):
    """Draw phi comparison with optional n-fold symmetry reference lines."""
    c = ROOT.TCanvas("cphi", "", 900, 640)
    c.SetLeftMargin(0.12)
    c.SetBottomMargin(0.12)
    c.SetTopMargin(0.08)

    norm_hists = []
    for h in hists:
        hc = h.Clone(h.GetName() + "_n")
        if hc.Integral(1, hc.GetNbinsX()) > 0:
            hc.Scale(1.0 / hc.Integral(1, hc.GetNbinsX()))
        norm_hists.append(hc)

    ymax = max(h.GetMaximum() for h in norm_hists) * 1.5

    for i, (h, lab, col) in enumerate(zip(norm_hists, labels, colors)):
        h.SetMaximum(ymax)
        h.SetLineColor(col)
        h.SetLineWidth(1)
        if i == 0:
            h.SetTitle(title)
            h.Draw("HIST")
        else:
            h.Draw("HIST SAME")

    if n_fold is not None:
        import math
        for k in range(n_fold):
            phi_k = PHI_MIN + (2 * math.pi) * k / n_fold
            ln = ROOT.TLine(phi_k, 0, phi_k, ymax)
            ln.SetLineColor(int(ROOT.kGray + 1))
            ln.SetLineStyle(3)
            ln.Draw()

    leg = ROOT.TLegend(0.13, 0.72, 0.50, 0.88)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.038)
    for h, lab in zip(norm_hists, labels):
        leg.AddEntry(h, lab, "l")
    leg.Draw()

    # ALEPH √s label
    alabel = ROOT.TLatex()
    alabel.SetNDC(True)
    alabel.SetTextSize(0.040)
    alabel.SetTextFont(42)
    alabel.DrawLatex(0.12, 0.945, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")

    # Plot title (right-aligned)
    if title:
        tlabel = ROOT.TLatex()
        tlabel.SetNDC(True)
        tlabel.SetTextSize(0.034)
        tlabel.SetTextFont(42)
        tlabel.SetTextAlign(31)
        tlabel.DrawLatex(0.97, 0.945, title)

    c.SaveAs(outpath)
    c.Close()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    fout = ROOT.TFile(os.path.join(args.outdir, "phi_spectrum_histograms.root"), "RECREATE")

    for pw, (desc, col) in PWFLAGS.items():
        print(f"\nProcessing pwflag={pw} ({desc})...")

        print("  Filling reco histograms...")
        h_data = fill_phi_hist(args.input_data,    args.reco_tree, True,  pw, "data")
        h_mc_r = fill_phi_hist(args.input_mc_reco, args.reco_tree, True,  pw, "mc_reco")

        print("  Filling gen histogram...")
        # gen tree uses same phi branches but no pwflag filter needed
        # (gen particles have their own px/py/pwflag)
        h_mc_g = fill_phi_hist(args.input_mc_gen,  args.gen_tree,  False, pw, "mc_gen")

        # Plot 1: data vs MC reco
        draw_phi_comparison(
            [h_data, h_mc_r],
            [f"Data reco (pwflag={pw})", f"MC reco (pwflag={pw})"],
            [int(ROOT.kBlack), int(ROOT.kRed)],
            os.path.join(args.outdir, f"phi_pw{pw}_data_vs_mc_reco.pdf"),
            title=f"#phi distribution: pwflag={pw} ({desc}), data vs MC reco",
            n_fold=(24 if pw in (4, 5) else None)
        )

        # Plot 2: MC reco vs MC gen  (detector effect check)
        draw_phi_comparison(
            [h_mc_r, h_mc_g],
            [f"MC reco (pwflag={pw})", f"MC gen (pwflag={pw})"],
            [int(ROOT.kRed), int(ROOT.kBlue+1)],
            os.path.join(args.outdir, f"phi_pw{pw}_mc_reco_vs_gen.pdf"),
            title=f"#phi distribution: pwflag={pw} ({desc}), MC reco vs gen",
            n_fold=(24 if pw in (4, 5) else None)
        )

        # Plot 3: all three together
        draw_phi_comparison(
            [h_data, h_mc_r, h_mc_g],
            [f"Data reco", f"MC reco", f"MC gen"],
            [int(ROOT.kBlack), int(ROOT.kRed), int(ROOT.kBlue+1)],
            os.path.join(args.outdir, f"phi_pw{pw}_all.pdf"),
            title=f"#phi distribution: pwflag={pw} ({desc})",
            n_fold=(24 if pw in (4, 5) else None)
        )

        for h in [h_data, h_mc_r, h_mc_g]:
            h.Write()

    # Also plot all pwflags overlaid for data and MC reco
    print("\nMaking all-pwflag overlay plots...")
    for source, filepath, tree, sel, slabel in [
        ("data",    args.input_data,    args.reco_tree, True,  "data"),
        ("mc_reco", args.input_mc_reco, args.reco_tree, True,  "MC reco"),
    ]:
        hs, labs, cols = [], [], []
        for pw, (desc, col) in PWFLAGS.items():
            h = fill_phi_hist(filepath, tree, sel, pw, f"{source}_overlay")
            hs.append(h)
            labs.append(f"pwflag={pw} ({desc})")
            cols.append(col)
        draw_phi_comparison(
            hs, labs, cols,
            os.path.join(args.outdir, f"phi_all_pwflags_{source}.pdf"),
            title=f"#phi distribution by pwflag ({slabel})",
            n_fold=24
        )
        for h in hs:
            h.Write()

    fout.Close()
    print(f"\nDone. Outputs in {args.outdir}")


if __name__ == "__main__":
    main()
