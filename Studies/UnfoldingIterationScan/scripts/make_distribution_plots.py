#!/usr/bin/env python3
"""Make unfolded and related distribution plots for selected iterations."""

import argparse
import importlib.util
import os
import sys

import ROOT
from ROOT import RooUnfold
from ROOT import RooUnfoldBayes


def load_unfold_module(repo_root):
    path = os.path.join(repo_root, "Unfolding", "unfold_thrust.py")
    spec = importlib.util.spec_from_file_location("unfold_thrust", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_unfolder(response, measured, iterations):
    uf = RooUnfoldBayes(response, measured, iterations)
    if hasattr(uf, "SetVerbose"):
        uf.SetVerbose(0)
    return uf


def add_plotting_path(repo_root):
    plotting_dir = os.path.join(repo_root, "DataProcessing", "plotting")
    if plotting_dir not in sys.path:
        sys.path.insert(0, plotting_dir)


def normalized_clone(h, name):
    c = h.Clone(name)
    c.SetDirectory(0)
    integ = c.Integral(1, c.GetNbinsX())
    if integ > 0:
        c.Scale(1.0 / integ)
    return c


def diff_xsec_clone(h, name):
    """Return 1/N dN/dx representation (normalized by events and bin width)."""
    c = h.Clone(name)
    c.SetDirectory(0)
    nev = c.Integral(1, c.GetNbinsX())
    if nev > 0.0:
        c.Scale(1.0 / nev, "width")
    return c


def positive_min(hists):
    vmin = None
    for h in hists:
        for b in range(1, h.GetNbinsX() + 1):
            v = float(h.GetBinContent(b))
            if v > 0.0:
                if vmin is None or v < vmin:
                    vmin = v
    return vmin if vmin is not None else 1e-10


def build_ratio_hist_with_errors(numerator, denominator, name):
    ratio = numerator.Clone(name)
    ratio.SetDirectory(0)
    ratio.Reset("ICESM")
    ratio.SetStats(0)
    for ibin in range(1, ratio.GetNbinsX() + 1):
        num = numerator.GetBinContent(ibin)
        den = denominator.GetBinContent(ibin)
        if den <= 0.0:
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


def make_plot_with_ratio(
    samples,
    ratio_denom,
    outpath,
    ytitle,
    logy=True,
    legend_loc=(0.23, 0.65, 0.51, 0.88),
    xtitle="Thrust",
):
    from style import ALEPHLegend, style_ratio

    for s in samples:
        s["hist"].SetStats(0)

    canvas = ROOT.TCanvas(os.path.basename(outpath).replace(".", "_"), "", 700, 700)
    pad1 = ROOT.TPad("pad1_" + canvas.GetName(), "", 0, 0.3, 1, 1.0)
    pad1.SetBottomMargin(0)
    pad1.SetTopMargin(0.1)
    pad1.SetLeftMargin(0.20)
    pad1.SetRightMargin(0.05)
    pad1.Draw()
    pad1.cd()
    if logy:
        pad1.SetLogy()

    ymax = max(s["hist"].GetMaximum() for s in samples) * (8.0 if logy else 1.35)
    ymin = positive_min([s["hist"] for s in samples]) * 0.6 if logy else 0.0
    for s in samples:
        h = s["hist"]
        h.GetXaxis().SetTitle(xtitle)
        h.GetYaxis().SetTitle(ytitle)
        h.SetMaximum(ymax)
        if logy:
            h.SetMinimum(ymin)

    # Draw MC/model first, then data-like markers on top.
    draw_order = [s for s in samples if not s.get("is_data", False)] + [s for s in samples if s.get("is_data", False)]
    for i, s in enumerate(draw_order):
        opt = s.get("draw_opt", "HIST")
        if i > 0:
            opt += " SAME"
        s["hist"].Draw(opt)

    legend = ALEPHLegend(loc=list(legend_loc), textsize=0.045)
    for s in samples:
        legend.AddEntry(s["hist"], s["label"], s.get("legend_opt", "l"))
    legend.Draw()

    canvas.cd()
    pad2 = ROOT.TPad("pad2_" + canvas.GetName(), "", 0, 0.05, 1, 0.3)
    pad2.SetTopMargin(0)
    pad2.SetBottomMargin(0.4)
    pad2.SetLeftMargin(0.20)
    pad2.SetRightMargin(0.05)
    pad2.Draw()
    pad2.cd()

    ratio_frame = ratio_denom.Clone("ratio_frame_" + canvas.GetName())
    ratio_frame.Reset("ICESM")
    ratio_frame.SetStats(0)
    style_ratio(ratio_frame, xtitle)
    ratio_frame.GetYaxis().SetTitle("Ratio")
    ratio_frame.Draw("AXIS")

    unity = ROOT.TLine(ratio_denom.GetXaxis().GetXmin(), 1.0, ratio_denom.GetXaxis().GetXmax(), 1.0)
    unity.SetLineStyle(2)
    unity.SetLineColor(ROOT.kGray + 2)
    unity.Draw("SAME")

    for s in samples:
        ratio = build_ratio_hist_with_errors(s["hist"], ratio_denom, f"ratio_{s['hist'].GetName()}")
        ratio.SetLineColor(s["color"])
        ratio.SetMarkerColor(s["color"])
        ratio.SetMarkerStyle(s["marker"])
        ratio.SetLineStyle(s.get("line_style", 1))
        style_ratio(ratio, xtitle)
        ratio.GetYaxis().SetTitle("Ratio")
        ratio.SetMarkerSize(0.9)
        ratio.Draw("E SAME")

    canvas.Print(outpath)
    canvas.Close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="Unfolding/unfold_config.json")
    p.add_argument("--iters", default="4,7,10")
    p.add_argument("--outdir", default="Studies/UnfoldingIterationScan/results")
    args = p.parse_args()

    selected_iters = [int(x.strip()) for x in args.iters.split(",") if x.strip()]
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    add_plotting_path(repo_root)
    from style import SetALEPHStyle, apply_style

    ROOT.gROOT.SetBatch(True)
    SetALEPHStyle()
    ROOT.gStyle.SetOptStat(0)

    unfold_mod = load_unfold_module(repo_root)
    cfg_path = os.path.abspath(args.config)
    cfg_dir = os.path.dirname(cfg_path)
    cfg = unfold_mod.load_config(cfg_path, [])

    data_file = unfold_mod.get_cfg(cfg, "data_file", required=True)
    reco_mc_file = unfold_mod.get_cfg(cfg, "reco_mc_file", required=True)
    gen_mc_file = unfold_mod.get_cfg(cfg, "gen_mc_file", required=True)
    if not os.path.isabs(data_file):
        data_file = os.path.abspath(os.path.join(cfg_dir, data_file))
    if not os.path.isabs(reco_mc_file):
        reco_mc_file = os.path.abspath(os.path.join(cfg_dir, reco_mc_file))
    if not os.path.isabs(gen_mc_file):
        gen_mc_file = os.path.abspath(os.path.join(cfg_dir, gen_mc_file))

    observable_name, observable = unfold_mod.get_observable_preset(
        unfold_mod.get_cfg(cfg, "observable", default="thrust")
    )
    axis_label = observable["axis_label"]

    data_tree_name = unfold_mod.get_cfg(cfg, "data_tree", default="t")
    reco_tree_name = unfold_mod.get_cfg(cfg, "reco_tree", default="t")
    gen_tree_name = unfold_mod.get_cfg(cfg, "gen_tree", default="tgen")
    data_branch = unfold_mod.get_cfg(cfg, "data_branch", default=observable["branch"])
    reco_branch = unfold_mod.get_cfg(cfg, "reco_branch", default=observable["branch"])
    gen_branch = unfold_mod.get_cfg(cfg, "gen_branch", default=observable["branch"])
    selection_branch = unfold_mod.get_cfg(cfg, "selection_branch", default="passEventSelection")
    id_branch = unfold_mod.get_cfg(cfg, "id_branch", default="uniqueID")
    bins = int(unfold_mod.get_cfg(cfg, "bins", default=observable["bins"]))
    xmin = float(unfold_mod.get_cfg(cfg, "xmin", default=observable["xmin"]))
    xmax = float(unfold_mod.get_cfg(cfg, "xmax", default=observable["xmax"]))

    f_data = ROOT.TFile.Open(data_file, "READ")
    f_reco = ROOT.TFile.Open(reco_mc_file, "READ")
    f_gen = ROOT.TFile.Open(gen_mc_file, "READ")

    tree_data = unfold_mod.get_tree(f_data, data_tree_name, data_file)
    tree_reco = unfold_mod.get_tree(f_reco, reco_tree_name, reco_mc_file)
    tree_gen = unfold_mod.get_tree(f_gen, gen_tree_name, gen_mc_file)

    h_data = unfold_mod.make_h1("data_reco", f"Data reco;{axis_label};Events", bins, xmin, xmax)
    unfold_mod.fill_hist_from_tree(tree_data, data_branch, h_data, xmin, xmax, selection_branch=selection_branch)

    response, h_mc_reco, h_mc_gen, h_resp_counts, _, _ = unfold_mod.build_response(
        tree_reco=tree_reco,
        tree_gen=tree_gen,
        id_branch=id_branch,
        reco_branch=reco_branch,
        gen_branch=gen_branch,
        reco_selection_branch=selection_branch,
        bins=bins,
        xmin=xmin,
        xmax=xmax,
        axis_label=axis_label,
        RooUnfoldResponse=unfold_mod.RooUnfoldResponse,
    )

    unfolded = {}
    refolded = {}
    for it in selected_iters:
        uf = make_unfolder(response, h_data, it)
        hu = uf.Hunfold(RooUnfold.kNoError).Clone(f"h_unf_{it}")
        hr = response.ApplyToTruth(hu).Clone(f"h_refold_{it}")
        hu.SetDirectory(0)
        hr.SetDirectory(0)
        unfolded[it] = hu
        refolded[it] = hr

    # Differential representation for plotting: 1/N dN/dT
    h_data_diff = diff_xsec_clone(h_data, "h_data_diff")
    h_mc_reco_diff = diff_xsec_clone(h_mc_reco, "h_mc_reco_diff")
    h_mc_gen_diff = diff_xsec_clone(h_mc_gen, "h_mc_gen_diff")
    unfolded_diff = {it: diff_xsec_clone(unfolded[it], f"h_unf_diff_{it}") for it in selected_iters}
    refolded_diff = {it: diff_xsec_clone(refolded[it], f"h_refold_diff_{it}") for it in selected_iters}
    h_data_shape = normalized_clone(h_data_diff, "h_data_shape")
    h_mc_reco_shape = normalized_clone(h_mc_reco_diff, "h_mc_reco_shape")
    h_mc_gen_shape = normalized_clone(h_mc_gen_diff, "h_mc_gen_shape")
    unfolded_shape = {it: normalized_clone(unfolded_diff[it], f"h_unf_shape_{it}") for it in selected_iters}

    colors = [ROOT.kOrange + 7, ROOT.kGreen + 2, ROOT.kAzure + 1, ROOT.kMagenta + 1, ROOT.kRed + 1]

    # Apply ALEPH style coloring/markers.
    for h, c, m, ls in [
        (h_data_diff, ROOT.kBlack, 20, 1),
        (h_mc_reco_diff, ROOT.kBlue + 1, 24, 1),
        (h_mc_gen_diff, ROOT.kRed + 1, 25, 1),
        (h_data_shape, ROOT.kBlack, 20, 1),
        (h_mc_reco_shape, ROOT.kBlue + 1, 24, 1),
        (h_mc_gen_shape, ROOT.kRed + 1, 25, 1),
    ]:
        apply_style(h, color=c, marker=m, line_style=ls)
        h.SetStats(0)
    for idx, it in enumerate(selected_iters):
        apply_style(unfolded_diff[it], color=colors[idx % len(colors)], marker=24 + idx, line_style=1)
        apply_style(refolded_diff[it], color=colors[idx % len(colors)], marker=24 + idx, line_style=1)
        apply_style(unfolded_shape[it], color=colors[idx % len(colors)], marker=24 + idx, line_style=1)
        unfolded_diff[it].SetStats(0)
        refolded_diff[it].SetStats(0)
        unfolded_shape[it].SetStats(0)

    # 1) Inputs at reco/gen level with ratio to MC gen.
    samples_inputs = [
        {"hist": h_data_diff, "label": "Data reco", "color": ROOT.kBlack, "marker": 20, "line_style": 1, "is_data": True, "draw_opt": "PE1", "legend_opt": "pl"},
        {"hist": h_mc_reco_diff, "label": "MC reco", "color": ROOT.kBlue + 1, "marker": 24, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"},
        {"hist": h_mc_gen_diff, "label": "MC gen truth", "color": ROOT.kRed + 1, "marker": 25, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"},
    ]
    make_plot_with_ratio(
        samples_inputs,
        ratio_denom=h_mc_gen_diff,
        outpath=os.path.join(outdir, "dist_inputs_data_mcreco_mcgen.pdf"),
        ytitle="1/N dN/dT",
        logy=True,
        xtitle=axis_label,
    )

    # 2) Unfolded distributions for selected iterations + MC truth with ratio to truth.
    samples_unf = [{"hist": h_mc_gen_diff, "label": "MC gen truth", "color": ROOT.kBlack, "marker": 20, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"}]
    for idx, it in enumerate(selected_iters):
        samples_unf.append(
            {"hist": unfolded_diff[it], "label": f"Unfolded N={it}", "color": colors[idx % len(colors)], "marker": 24 + idx, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"}
        )
    make_plot_with_ratio(
        samples_unf,
        ratio_denom=h_mc_gen_diff,
        outpath=os.path.join(outdir, "dist_unfolded_selected_iterations.pdf"),
        ytitle="1/N dN/dT",
        logy=True,
        xtitle=axis_label,
    )

    # 3) Refolded (selected iterations) vs data reco with ratio to data.
    samples_ref = [{"hist": h_data_diff, "label": "Data reco", "color": ROOT.kBlack, "marker": 20, "line_style": 1, "is_data": True, "draw_opt": "PE1", "legend_opt": "pl"}]
    for idx, it in enumerate(selected_iters):
        samples_ref.append(
            {"hist": refolded_diff[it], "label": f"Refolded from N={it}", "color": colors[idx % len(colors)], "marker": 24 + idx, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"}
        )
    make_plot_with_ratio(
        samples_ref,
        ratio_denom=h_data_diff,
        outpath=os.path.join(outdir, "dist_refolded_vs_data_selected_iterations.pdf"),
        ytitle="1/N dN/dT",
        logy=True,
        xtitle=axis_label,
    )

    # 4) Shape-normalized unfolded distributions with ratio to truth.
    samples_shape = [{"hist": h_mc_gen_shape, "label": "MC gen truth (norm)", "color": ROOT.kBlack, "marker": 20, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"}]
    for idx, it in enumerate(selected_iters):
        samples_shape.append(
            {"hist": unfolded_shape[it], "label": f"Unfolded N={it} (norm)", "color": colors[idx % len(colors)], "marker": 24 + idx, "line_style": 1, "is_data": False, "draw_opt": "HIST", "legend_opt": "l"}
        )
    make_plot_with_ratio(
        samples_shape,
        ratio_denom=h_mc_gen_shape,
        outpath=os.path.join(outdir, "dist_unfolded_shape_selected_iterations.pdf"),
        ytitle="1/N dN/dT",
        logy=True,
        xtitle=axis_label,
    )

    # 5) Response matrix heatmap
    c5 = ROOT.TCanvas("c_response", "", 750, 650)
    h_resp_counts.SetTitle(f"Response counts;Reco {axis_label};Gen {axis_label}")
    h_resp_counts.Draw("COLZ")
    c5.SaveAs(os.path.join(outdir, "dist_response_counts_matrix.pdf"))

    print(f"Wrote distribution plots for observable '{observable_name}' to: {outdir}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
