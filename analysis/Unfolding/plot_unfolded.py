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
        "--corrected-hist", default="unfolded_corrected", help="Corrected unfolded histogram name"
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


def try_get_hist(tf, name):
    obj = tf.Get(name)
    if not obj:
        return None
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

    # Optional correction-stage histograms — silently skip if absent.
    h_had_corr = try_get_hist(tf, "hadronic_event_sel_corr")
    h_corrected = try_get_hist(tf, args.corrected_hist)

    tf.Close()

    # Compute intermediate stage: IBU + hadronic correction.
    h_unf_had = None
    if h_had_corr is not None:
        h_unf_had = h_unf.Clone("unfolded_had_plot")
        h_unf_had.SetDirectory(0)
        h_unf_had.Multiply(h_had_corr)

    cfg = plotConfig["thrust"]
    cfg["legloc"] = [0.24, 0.50, 0.49, 0.88]
    rebin = int(cfg.get("rebin", 1))
    if rebin > 1:
        h_data.Rebin(rebin)
        h_reco.Rebin(rebin)
        h_gen.Rebin(rebin)
        h_unf.Rebin(rebin)
        if h_unf_had is not None:
            h_unf_had.Rebin(rebin)
        if h_corrected is not None:
            h_corrected.Rebin(rebin)

    if not args.no_normalize:
        normalize(h_data)
        normalize(h_reco)
        normalize(h_gen)
        normalize(h_unf)
        if h_unf_had is not None:
            normalize(h_unf_had)
        if h_corrected is not None:
            normalize(h_corrected)
        ytitle = cfg.get("YTitleDifferential", "Fraction of events")
    else:
        normalize(h_data, unit_area=False)
        normalize(h_reco, unit_area=False)
        normalize(h_gen, unit_area=False)
        normalize(h_unf, unit_area=False)
        if h_unf_had is not None:
            normalize(h_unf_had, unit_area=False)
        if h_corrected is not None:
            normalize(h_corrected, unit_area=False)
        ytitle = "Events / #DeltaThrust"

    # Build sample list: 5 correction-stage entries + mc_reco in background.
    samples = [
        {
            "hist": h_data,
            "label": "Raw data",
            "color": ROOT.kGray + 1,
            "marker": 20,
            "line_style": 1,
            "is_data": True,
            "legend_opt": "pl",
        },
        {
            "hist": h_gen,
            "label": "MC gen (particle level)",
            "color": ROOT.kGreen + 2,
            "marker": 25,
            "line_style": 1,
            "is_data": False,
            "legend_opt": "pl",
        },
        {
            "hist": h_unf,
            "label": "IBU unfolded",
            "color": ROOT.kAzure + 2,
            "marker": 24,
            "line_style": 1,
            "is_data": True,
            "legend_opt": "pl",
        },
        {
            "hist": h_reco,
            "label": "MC reco",
            "color": ROOT.kGray + 2,
            "marker": 24,
            "line_style": 2,
            "is_data": False,
            "legend_opt": "pl",
        },
    ]

    if h_unf_had is not None:
        samples.append(
            {
                "hist": h_unf_had,
                "label": "IBU + had. corr.",
                "color": ROOT.kOrange + 1,
                "marker": 26,
                "line_style": 1,
                "is_data": True,
                "legend_opt": "pl",
            }
        )

    if h_corrected is not None:
        samples.append(
            {
                "hist": h_corrected,
                "label": "IBU + had. + ISR (final)",
                "color": ROOT.kBlack,
                "marker": 21,
                "line_style": 1,
                "is_data": True,
                "legend_opt": "pl",
            }
        )

    for sample in samples:
        h = sample["hist"]
        apply_style(
            h,
            color=sample["color"],
            marker=sample["marker"],
            line_style=sample["line_style"],
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

    legend = ALEPHLegend(loc=cfg.get("legloc", [0.23, 0.7, 0.48, 0.9]), textsize=0.045)

    # Draw order: mc_reco (background/dashed) first, then foreground stages.
    # Identify reco sample for background draw.
    reco_sample = next((s for s in samples if s["label"] == "MC reco"), None)
    fg_samples = [s for s in samples if s["label"] != "MC reco"]

    # Draw order back-to-front: reco (dashed, background), then foreground.
    draw_order = []
    if reco_sample is not None:
        draw_order.append(reco_sample)
    draw_order.extend(fg_samples)

    for idx, sample in enumerate(draw_order):
        draw_opt = "PE1"
        if idx > 0:
            draw_opt += " SAME"
        sample["hist"].Draw(draw_opt)

    # Legend in logical order: data_reco, mc_gen, IBU, IBU+had, final, mc_reco.
    legend_order = ["Raw data", "MC gen (particle level)", "IBU unfolded",
                    "IBU + had. corr.", "IBU + had. + ISR (final)", "MC reco"]
    label_to_sample = {s["label"]: s for s in samples}
    for label in legend_order:
        if label in label_to_sample:
            s = label_to_sample[label]
            legend.AddEntry(s["hist"], s["label"], s["legend_opt"])
    legend.Draw()
    myText(0.2, 0.925, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV", size=0.045)

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

    # Ratio denominator is mc_gen.
    ratio_denom = h_gen
    ratio_styles = [(s["hist"], s["color"], s["marker"], s["line_style"]) for s in samples]
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
