#!/usr/bin/env python3
"""Compare charged-only vs energy-flow unfolded thrust distributions.

Addresses reviewer comment J1: show that the energy-flow (charged + neutral)
result is consistent with the charged-only measurement, demonstrating the
neutral hadron correction is well-understood.

Usage:
    python charged_only_vs_energy_flow.py \
        --nominal path/to/unfolded_nominal_iter5.root \
        --no-neutrals path/to/unfolded_no_neutrals.root \
        --output-dir plots/charged_only_vs_energy_flow/
"""

import argparse
import os
import sys

import ROOT


def diff_xsec_clone(h, name):
    """Normalize histogram to differential cross-section: (1/N) dN/dT / bin_width."""
    c = h.Clone(name)
    c.SetDirectory(0)
    n = c.Integral(1, c.GetNbinsX())
    if n > 0.0:
        c.Scale(1.0 / n, "width")
    return c


def get_hist(path, name="unfolded_corrected"):
    """Open ROOT file and retrieve histogram, detached from file."""
    tf = ROOT.TFile.Open(path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open {path}")
    h = tf.Get(name)
    if not h:
        # List available objects for diagnostics
        print(f"  Available objects in {path}:", file=sys.stderr)
        tf.ls()
        raise KeyError(f"Histogram '{name}' not found in {path}")
    out = h.Clone(os.path.basename(path).replace(".root", "") + "_raw")
    out.SetDirectory(0)
    tf.Close()
    return out


def ratio_hist(num, den, name):
    """Compute bin-by-bin ratio num/den with propagated uncertainty."""
    r = num.Clone(name)
    r.SetDirectory(0)
    r.Reset("ICESM")
    for b in range(1, r.GetNbinsX() + 1):
        x = num.GetBinContent(b)
        y = den.GetBinContent(b)
        if y <= 0:
            r.SetBinContent(b, 0.0)
            r.SetBinError(b, 0.0)
            continue
        rv = x / y
        ex = num.GetBinError(b)
        ey = den.GetBinError(b)
        rel2 = 0.0
        if x > 0:
            rel2 += (ex / x) ** 2
        rel2 += (ey / y) ** 2
        r.SetBinContent(b, rv)
        r.SetBinError(b, abs(rv) * (rel2 ** 0.5))
    return r


def myText(x, y, text, size=0.040, ndc=True):
    """Draw text label at (x, y) in NDC coordinates."""
    t = ROOT.TLatex()
    t.SetNDC(ndc)
    t.SetTextFont(42)
    t.SetTextSize(size)
    t.DrawLatex(x, y, text)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--nominal",
        default="Studies/PreliminaryResult/2026-02-17_thrust_iter5/nominal/unfolded_nominal_iter5.root",
        help="Energy-flow (nominal) unfolded ROOT file",
    )
    p.add_argument(
        "--no-neutrals",
        default="Studies/PreliminaryResult/2026-02-17_thrust_iter5/experimental/unfolded_no_neutrals.root",
        help="Charged-only unfolded ROOT file",
    )
    p.add_argument(
        "--hist-name",
        default="unfolded_corrected",
        help="Histogram name inside ROOT files",
    )
    p.add_argument(
        "--output-dir",
        default="Studies/Phase2_Checks_2026-03-03/plots/charged_only_vs_energy_flow",
        help="Directory for output PDFs",
    )
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load and normalise histograms
    print(f"Loading energy-flow nominal: {args.nominal}")
    h_ef_raw = get_hist(args.nominal, args.hist_name)
    h_ef = diff_xsec_clone(h_ef_raw, "h_ef_diff")
    h_ef.SetLineColor(int(ROOT.kBlack))
    h_ef.SetMarkerColor(int(ROOT.kBlack))
    h_ef.SetLineWidth(2)
    h_ef.SetMarkerStyle(20)
    h_ef.SetMarkerSize(0.85)
    h_ef.SetStats(0)

    print(f"Loading charged-only: {args.no_neutrals}")
    h_cn_raw = get_hist(args.no_neutrals, args.hist_name)
    h_cn = diff_xsec_clone(h_cn_raw, "h_cn_diff")
    h_cn.SetLineColor(int(ROOT.kRed + 1))
    h_cn.SetMarkerColor(int(ROOT.kRed + 1))
    h_cn.SetLineWidth(2)
    h_cn.SetMarkerStyle(24)
    h_cn.SetMarkerSize(0.85)
    h_cn.SetStats(0)

    # ------------------------------------------------------------------ canvas
    c = ROOT.TCanvas("c_charged_vs_ef", "", 800, 780)
    pad1 = ROOT.TPad("pad1", "", 0, 0.30, 1, 1.0)
    pad1.SetBottomMargin(0.02)
    pad1.SetLeftMargin(0.15)
    pad1.SetRightMargin(0.04)
    pad1.SetTopMargin(0.09)
    pad1.Draw()
    pad1.cd()
    pad1.SetLogy()

    ymax = max(h_ef.GetMaximum(), h_cn.GetMaximum()) * 15.0
    ymin = 1e-5

    h_ef.SetMaximum(ymax)
    h_ef.SetMinimum(ymin)
    h_ef.GetYaxis().SetTitle("(1/N) dN/dT")
    h_ef.GetYaxis().SetTitleSize(0.058)
    h_ef.GetYaxis().SetTitleOffset(1.30)
    h_ef.GetYaxis().SetLabelSize(0.050)
    h_ef.GetXaxis().SetLabelSize(0)
    h_ef.Draw("E1")
    h_cn.Draw("E1 SAME")

    leg = ROOT.TLegend(0.52, 0.68, 0.93, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.046)
    leg.AddEntry(h_ef, "Energy-flow (nominal)", "pl")
    leg.AddEntry(h_cn, "Charged-only", "pl")
    leg.Draw()

    pad1.cd()
    myText(0.18, 0.925, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV", size=0.048)

    # ---------------------------------------------------------------- ratio pad
    c.cd()
    pad2 = ROOT.TPad("pad2", "", 0, 0.05, 1, 0.30)
    pad2.SetTopMargin(0.02)
    pad2.SetBottomMargin(0.36)
    pad2.SetLeftMargin(0.15)
    pad2.SetRightMargin(0.04)
    pad2.Draw()
    pad2.cd()

    h_ratio = ratio_hist(h_cn, h_ef, "h_ratio_cn_over_ef")
    h_ratio.SetLineColor(int(ROOT.kRed + 1))
    h_ratio.SetMarkerColor(int(ROOT.kRed + 1))
    h_ratio.SetMarkerStyle(24)
    h_ratio.SetMarkerSize(0.75)
    h_ratio.SetLineWidth(2)
    h_ratio.SetStats(0)

    frame = h_ef.Clone("ratio_frame")
    frame.SetDirectory(0)
    frame.Reset("ICESM")
    frame.GetXaxis().SetTitle("Thrust")
    frame.GetYaxis().SetTitle("Charged / EF")
    frame.GetYaxis().SetTitleSize(0.11)
    frame.GetYaxis().SetTitleOffset(0.60)
    frame.GetYaxis().SetLabelSize(0.09)
    frame.GetYaxis().SetNdivisions(505)
    frame.GetXaxis().SetTitleSize(0.13)
    frame.GetXaxis().SetLabelSize(0.11)
    frame.SetMinimum(0.70)
    frame.SetMaximum(1.30)
    frame.Draw("AXIS")

    line = ROOT.TLine(
        frame.GetXaxis().GetXmin(), 1.0,
        frame.GetXaxis().GetXmax(), 1.0,
    )
    line.SetLineStyle(2)
    line.SetLineColor(int(ROOT.kGray + 2))
    line.Draw("SAME")

    h_ratio.Draw("E1 SAME")

    # ------------------------------------------------------------------- save
    outpath = os.path.join(args.output_dir, "charged_only_vs_energy_flow.pdf")
    c.SaveAs(outpath)
    print(f"Wrote: {outpath}")


if __name__ == "__main__":
    ROOT.TH1.AddDirectory(False)
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(0)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
