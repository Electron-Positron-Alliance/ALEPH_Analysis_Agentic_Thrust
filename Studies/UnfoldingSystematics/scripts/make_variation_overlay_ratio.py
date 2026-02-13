#!/usr/bin/env python3
"""Make a single figure with unfolded variations and ratio to nominal."""

import argparse
import os
import sys

import ROOT


def diff_xsec_clone(h, name):
    c = h.Clone(name)
    c.SetDirectory(0)
    n = c.Integral(1, c.GetNbinsX())
    if n > 0.0:
        c.Scale(1.0 / n, "width")
    return c


def get_hist(path, name="unfolded_corrected"):
    tf = ROOT.TFile.Open(path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open {path}")
    h = tf.Get(name)
    if not h:
        raise KeyError(f"Histogram '{name}' not found in {path}")
    out = h.Clone(os.path.basename(path).replace(".root", "") + "_" + name)
    out.SetDirectory(0)
    tf.Close()
    return out


def ratio_hist(num, den, name):
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="Studies/UnfoldingSystematics/results")
    p.add_argument("--output", default="Studies/UnfoldingSystematics/results/unfolded_all_variations_ratio_nominal.pdf")
    p.add_argument("--hist-name", default="unfolded_corrected")
    args = p.parse_args()

    ordered_vars = ["nominal", "ech10", "ner", "nes_down", "nes_up", "ntpc7", "pt04", "with_met"]
    colors = {
        "nominal": ROOT.kBlack,
        "ech10": ROOT.kBlue + 1,
        "ner": ROOT.kGreen + 2,
        "nes_down": ROOT.kOrange + 7,
        "nes_up": ROOT.kRed + 1,
        "ntpc7": ROOT.kMagenta + 1,
        "pt04": ROOT.kViolet + 1,
        "with_met": ROOT.kAzure + 1,
    }

    hists = {}
    for v in ordered_vars:
        path = os.path.join(args.results_dir, f"unfolded_{v}.root")
        if not os.path.exists(path):
            continue
        h = get_hist(path, args.hist_name)
        h = diff_xsec_clone(h, f"h_{v}_diff")
        h.SetLineColor(colors[v])
        h.SetMarkerColor(colors[v])
        h.SetLineWidth(2)
        h.SetMarkerStyle(20)
        h.SetMarkerSize(0.8)
        h.SetStats(0)
        hists[v] = h

    if "nominal" not in hists:
        raise RuntimeError("nominal variation is required")

    vars_present = [v for v in ordered_vars if v in hists]
    nominal = hists["nominal"]

    c = ROOT.TCanvas("c_all_variations", "", 850, 780)
    pad1 = ROOT.TPad("pad1", "", 0, 0.30, 1, 1.0)
    pad1.SetBottomMargin(0.02)
    pad1.SetLeftMargin(0.14)
    pad1.SetRightMargin(0.04)
    pad1.SetTopMargin(0.08)
    pad1.Draw()
    pad1.cd()
    pad1.SetLogy()

    ymax = max(hists[v].GetMaximum() for v in vars_present) * 10.0
    ymin = 1e-6
    first = True
    for v in vars_present:
        h = hists[v]
        h.GetYaxis().SetTitle("1/N dN/dT")
        h.GetXaxis().SetTitle("Thrust")
        h.SetMaximum(ymax)
        h.SetMinimum(ymin)
        opt = "E1" if first else "E1 SAME"
        h.Draw(opt)
        first = False

    leg = ROOT.TLegend(0.60, 0.52, 0.94, 0.92)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    for v in vars_present:
        leg.AddEntry(hists[v], v, "pl")
    leg.Draw()

    c.cd()
    pad2 = ROOT.TPad("pad2", "", 0, 0.05, 1, 0.30)
    pad2.SetTopMargin(0.02)
    pad2.SetBottomMargin(0.35)
    pad2.SetLeftMargin(0.14)
    pad2.SetRightMargin(0.04)
    pad2.Draw()
    pad2.cd()

    frame = nominal.Clone("ratio_frame")
    frame.Reset("ICESM")
    frame.GetXaxis().SetTitle("Thrust")
    frame.GetYaxis().SetTitle("Variation / nominal")
    frame.GetYaxis().SetTitleSize(0.10)
    frame.GetYaxis().SetTitleOffset(0.5)
    frame.GetYaxis().SetLabelSize(0.08)
    frame.GetYaxis().SetNdivisions(505)
    frame.GetXaxis().SetTitleSize(0.12)
    frame.GetXaxis().SetLabelSize(0.10)
    frame.SetMinimum(0.5)
    frame.SetMaximum(1.5)
    frame.Draw("AXIS")

    line = ROOT.TLine(frame.GetXaxis().GetXmin(), 1.0, frame.GetXaxis().GetXmax(), 1.0)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kGray + 2)
    line.Draw("SAME")

    ratios = []
    for v in vars_present:
        if v == "nominal":
            continue
        r = ratio_hist(hists[v], nominal, f"ratio_{v}")
        r.SetLineColor(colors[v])
        r.SetMarkerColor(colors[v])
        r.SetMarkerStyle(20)
        r.SetMarkerSize(0.65)
        r.SetLineWidth(2)
        r.Draw("E1 SAME")
        ratios.append(r)

    outdir = os.path.dirname(args.output)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    c.SaveAs(args.output)
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
