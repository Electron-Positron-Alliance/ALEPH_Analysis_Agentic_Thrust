#!/usr/bin/env python3
"""
Plot unfolded thrust vs data reco, MC reco, and MC gen using shared ALEPH style.
"""

import argparse
import os
import sys

import ROOT


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot unfolded thrust against data/reco/gen histograms."
    )
    parser.add_argument(
        "--input-root",
        default="unfolded_thrust.root",
        help="Input ROOT file produced by unfold_thrust.py",
    )
    parser.add_argument(
        "--output",
        default="unfolded_vs_data_reco_mcgen.pdf",
        help="Output plot file",
    )
    parser.add_argument("--data-hist", default="data_reco", help="Data reco histogram name")
    parser.add_argument("--reco-hist", default="mc_reco", help="MC reco histogram name")
    parser.add_argument("--gen-hist", default="mc_gen", help="MC gen histogram name")
    parser.add_argument(
        "--unfolded-hist", default="unfolded", help="Unfolded histogram name"
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable unit-area normalization for shape comparison",
    )
    return parser.parse_args()


def add_plotting_path():
    here = os.path.abspath(os.path.dirname(__file__))
    plotting_dir = os.path.abspath(os.path.join(here, "..", "DataProcessing", "plotting"))
    if plotting_dir not in sys.path:
        sys.path.insert(0, plotting_dir)


def normalize(hist, unit_area=True):
    # Convert histogram to differential form (per bin width).
    if unit_area:
        integral = hist.Integral()
        if integral > 0:
            hist.Scale(1.0 / integral)
    hist.Scale(1.0, "width")


def build_ratio_hist_with_errors(numerator, denominator, name):
    ratio = numerator.Clone(name)
    ratio.SetDirectory(0)
    ratio.Reset("ICESM")
    for ibin in range(1, ratio.GetNbinsX() + 1):
        num = numerator.GetBinContent(ibin)
        den = denominator.GetBinContent(ibin)
        if den <= 0:
            ratio.SetBinContent(ibin, 0.0)
            ratio.SetBinError(ibin, 0.0)
            continue

        r = num / den
        e_num = numerator.GetBinError(ibin)
        e_den = denominator.GetBinError(ibin)
        err2 = 0.0
        if num > 0:
            err2 += (e_num / num) ** 2
        if den > 0:
            err2 += (e_den / den) ** 2
        ratio.SetBinContent(ibin, r)
        ratio.SetBinError(ibin, abs(r) * (err2 ** 0.5))
    return ratio


def get_hist(tf, name):
    obj = tf.Get(name)
    if not obj:
        raise KeyError(f"Histogram '{name}' not found in {tf.GetName()}")
    h = obj.Clone(f"{name}_plot")
    h.SetDirectory(0)
    return h


def main():
    args = parse_args()
    add_plotting_path()

    from PlotConfig import plotConfig
    from style import ALEPHLegend, SetALEPHStyle, apply_style, myText, style_ratio

    ROOT.gROOT.SetBatch(True)
    SetALEPHStyle()

    tf = ROOT.TFile.Open(args.input_root, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open input ROOT file: {args.input_root}")

    h_data = get_hist(tf, args.data_hist)
    h_reco = get_hist(tf, args.reco_hist)
    h_gen = get_hist(tf, args.gen_hist)
    h_unf = get_hist(tf, args.unfolded_hist)
    tf.Close()

    cfg = plotConfig["thrust"]
    cfg["legloc"] = [0.24, 0.58, 0.49, 0.88]
    rebin = int(cfg.get("rebin", 1))
    if rebin > 1:
        h_data.Rebin(rebin)
        h_reco.Rebin(rebin)
        h_gen.Rebin(rebin)
        h_unf.Rebin(rebin)

    if not args.no_normalize:
        normalize(h_data)
        normalize(h_reco)
        normalize(h_gen)
        normalize(h_unf)
        ytitle = cfg.get("YTitleDifferential", "Fraction of events")
    else:
        normalize(h_data, unit_area=False)
        normalize(h_reco, unit_area=False)
        normalize(h_gen, unit_area=False)
        normalize(h_unf, unit_area=False)
        ytitle = "Events / #DeltaThrust"

    samples = [
        {
            "hist": h_data,
            "label": "Data",
            "color": ROOT.kBlack,
            "marker": 20,
            "line_style": 1,
            "is_data": True,
            "legend_opt": "pl",
        },
        {
            "hist": h_reco,
            "label": "MC Reco",
            "color": ROOT.kRed + 1,
            "marker": 20,
            "line_style": 1,
            "is_data": True,
            "legend_opt": "pl",
        },
        {
            "hist": h_gen,
            "label": "MC Gen",
            "color": ROOT.kGreen + 2,
            "marker": 20,
            "line_style": 1,
            "is_data": False,
            "legend_opt": "pl",
        },
        {
            "hist": h_unf,
            "label": "Unfolded",
            "color": ROOT.kBlue + 1,
            "marker": 20,
            "line_style": 1,
            "is_data": True,
            "legend_opt": "pl",
        },
    ]

    for sample in samples:
        h = sample["hist"]
        apply_style(
            h,
            color=sample["color"],
            marker=sample["marker"],
            line_style=sample["line_style"],
            # is_data=sample["is_data"],
        )
        h.GetXaxis().SetTitle("Thrust")
        h.GetYaxis().SetTitle(ytitle)

    max_bin = max(s["hist"].GetMaximum() for s in samples)
    y_max = cfg.get("scale_max_bin_content", 5.0) * max_bin
    for sample in samples:
        sample["hist"].SetMaximum(y_max)
        if cfg.get("SetLogy", False):
            sample["hist"].SetMinimum(max(sample["hist"].GetMinimum(0), 1e-6))

    canvas = ROOT.TCanvas("c_unfolded_compare", "", 50, 50, 700, 700)
    pad1 = ROOT.TPad("pad1", "", 0, 0.3, 1, 1.0)
    pad1.SetBottomMargin(0)
    pad1.SetTopMargin(0.1)
    pad1.SetLeftMargin(0.20)
    pad1.SetRightMargin(0.05)
    pad1.Draw()
    pad1.cd()
    if cfg.get("SetLogy", False):
        pad1.SetLogy()

    legend = ALEPHLegend(loc=cfg.get("legloc", [0.23, 0.7, 0.48, 0.9]), textsize=0.05)

    draw_order = [samples[1], samples[2], samples[3], samples[0]]
    for idx, sample in enumerate(draw_order):
        draw_opt = "PE1"
        if idx > 0:
            draw_opt += " SAME"
        sample["hist"].Draw(draw_opt)

    for sample in samples:
        legend.AddEntry(sample["hist"], sample["label"], sample["legend_opt"])
    legend.Draw()
    myText(0.2, 0.925, "ALEPH e^{+}e^{-}, #sqrt{s} = 91.2 GeV", size=0.045)

    canvas.cd()
    pad2 = ROOT.TPad("pad2", "", 0, 0.05, 1, 0.3)
    pad2.SetTopMargin(0)
    pad2.SetBottomMargin(0.4)
    pad2.SetLeftMargin(0.20)
    pad2.SetRightMargin(0.05)
    pad2.Draw()
    pad2.cd()

    ratio_frame = h_data.Clone("ratio_frame")
    ratio_frame.Reset("ICESM")
    style_ratio(ratio_frame, "Thrust")
    ratio_frame.GetYaxis().SetTitle("Ratio")
    ratio_frame.Draw("AXIS")

    ratio_styles = [
        (h_data, ROOT.kBlack, 20, 1),
        (h_reco, ROOT.kRed + 1, 20, 1),
        (h_gen, ROOT.kGreen + 2, 20, 1),
        (h_unf, ROOT.kBlue + 1, 20, 1)
    ]
    ratio_denom = h_gen
    ratio_hists = []
    unity_line = ROOT.TLine(h_data.GetXaxis().GetXmin(), 1.0, h_data.GetXaxis().GetXmax(), 1.0)
    unity_line.SetLineStyle(2)
    unity_line.SetLineColor(ROOT.kGray + 2)
    unity_line.Draw("SAME")
    for src_hist, color, marker, line_style in ratio_styles:
        ratio = build_ratio_hist_with_errors(src_hist, ratio_denom, f"ratio_{src_hist.GetName()}")
        ratio.SetLineColor(color)
        ratio.SetMarkerColor(color)
        ratio.SetMarkerStyle(marker)
        ratio.SetLineStyle(line_style)
        style_ratio(ratio, "Thrust")
        ratio.SetMarkerSize(0.9)
        ratio.GetYaxis().SetTitle("Ratio")
        ratio.Draw("E SAME")
        ratio_hists.append(ratio)

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    canvas.Print(args.output)
    canvas.Close()
    print(f"Wrote plot: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
