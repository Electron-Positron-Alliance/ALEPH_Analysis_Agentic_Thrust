#!/usr/bin/env python3
"""Plot bin-by-bin fractional-difference variants vs nominal."""

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


def get_unfolded_hist(path, hist_name="unfolded_corrected"):
    tf = ROOT.TFile.Open(path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open {path}")
    h = tf.Get(hist_name)
    if not h:
        raise KeyError(f"Histogram '{hist_name}' not found in {path}")
    out = h.Clone(os.path.basename(path).replace(".root", "") + "_" + hist_name)
    out.SetDirectory(0)
    tf.Close()
    return out


def frac_diff_hist(var_hist, nom_hist, name):
    h = var_hist.Clone(name)
    h.SetDirectory(0)
    h.Reset("ICESM")
    for b in range(1, h.GetNbinsX() + 1):
        v = float(var_hist.GetBinContent(b))
        n = float(nom_hist.GetBinContent(b))
        if n == 0.0:
            h.SetBinContent(b, 0.0)
            h.SetBinError(b, 0.0)
            continue
        fd = (v - n) / n

        ev = float(var_hist.GetBinError(b))
        en = float(nom_hist.GetBinError(b))
        err = ((ev / n) ** 2 + (v * en / (n * n)) ** 2) ** 0.5
        h.SetBinContent(b, fd)
        h.SetBinError(b, err)
    return h


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="Studies/UnfoldingSystematics/results")
    p.add_argument(
        "--output",
        default="Studies/UnfoldingSystematics/results/unfolded_fractional_difference_vs_nominal.pdf",
    )
    p.add_argument("--hist-name", default="unfolded_corrected")
    p.add_argument("--absolute", action="store_true", help="Plot absolute value of fractional difference")
    p.add_argument("--percent", action="store_true", help="Scale y-values by 100")
    p.add_argument("--y-min", type=float, default=None, help="Optional fixed y-axis minimum")
    p.add_argument("--y-max", type=float, default=None, help="Optional fixed y-axis maximum")
    args = p.parse_args()

    ordered_vars = ["nominal", "ech10", "ner", "nes_down", "nes_up", "ntpc7", "pt04", "with_met"]
    colors = {
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
        f = os.path.join(args.results_dir, f"unfolded_{v}.root")
        if not os.path.exists(f):
            continue
        hists[v] = diff_xsec_clone(get_unfolded_hist(f, args.hist_name), f"h_{v}_diff")

    if "nominal" not in hists:
        raise RuntimeError("Missing nominal histogram")

    nom = hists["nominal"]
    vars_present = [v for v in ordered_vars if v in hists and v != "nominal"]

    frac_hists = []
    y_min = 0.0
    y_max = 0.0
    for v in vars_present:
        h = frac_diff_hist(hists[v], nom, f"h_frac_{v}")
        if args.absolute:
            for b in range(1, h.GetNbinsX() + 1):
                h.SetBinContent(b, abs(float(h.GetBinContent(b))))
        if args.percent:
            h.Scale(100.0)
        h.SetLineColor(colors.get(v, ROOT.kBlack))
        h.SetMarkerColor(colors.get(v, ROOT.kBlack))
        h.SetMarkerStyle(20)
        h.SetMarkerSize(0.8)
        h.SetLineWidth(2)
        h.SetStats(0)
        frac_hists.append((v, h))
        for b in range(1, h.GetNbinsX() + 1):
            y = h.GetBinContent(b)
            e = h.GetBinError(b)
            y_min = min(y_min, y - e)
            y_max = max(y_max, y + e)

    pad = 0.15 * max(abs(y_min), abs(y_max), 1e-3)
    y_low = y_min - pad
    y_high = y_max + pad

    c = ROOT.TCanvas("c_fracdiff", "", 900, 650)
    frame = nom.Clone("frame_frac")
    frame.Reset("ICESM")
    frame.GetXaxis().SetTitle("Thrust")
    ytitle = "(variation - nominal) / nominal"
    if args.absolute:
        ytitle = "|(variation - nominal) / nominal|"
    if args.percent:
        ytitle += " [%]"
    frame.GetYaxis().SetTitle(ytitle)
    # Default zoom for absolute percentage view unless explicitly overridden.
    if args.absolute and args.percent and args.y_min is None and args.y_max is None:
        y_low = 0.0
        y_high = 10.0
    if args.y_min is not None:
        y_low = args.y_min
    if args.y_max is not None:
        y_high = args.y_max
    frame.SetMinimum(y_low)
    frame.SetMaximum(y_high)
    frame.Draw("AXIS")

    if not args.absolute:
        zline = ROOT.TLine(frame.GetXaxis().GetXmin(), 0.0, frame.GetXaxis().GetXmax(), 0.0)
        zline.SetLineStyle(2)
        zline.SetLineColor(ROOT.kGray + 2)
        zline.Draw("SAME")

    leg = ROOT.TLegend(0.44, 0.66, 0.94, 0.92)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetNColumns(2)
    leg.SetTextSize(0.030)

    for v, h in frac_hists:
        h.Draw("E1 SAME")
        leg.AddEntry(h, v, "pl")

    leg.Draw()

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
