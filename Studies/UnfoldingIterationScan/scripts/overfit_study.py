#!/usr/bin/env python3
"""Study IBU overfitting indicators vs iterations using pseudo-experiments."""

import argparse
import csv
import importlib.util
import json
import math
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


def make_graph(rows, ykey, title, ytitle, outpath):
    g = ROOT.TGraph(len(rows))
    for i, r in enumerate(rows):
        g.SetPoint(i, float(r["iteration"]), float(r[ykey]))
    c = ROOT.TCanvas("c_" + ykey, "", 760, 560)
    g.SetTitle(title)
    g.SetMarkerStyle(20)
    g.SetMarkerSize(1.0)
    g.SetLineWidth(2)
    g.Draw("ALP")
    g.GetXaxis().SetTitle("Bayesian iterations")
    g.GetYaxis().SetTitle(ytitle)
    c.SaveAs(outpath)


def make_bias_var_plot(rows, outpath):
    gb = ROOT.TGraph(len(rows))
    gv = ROOT.TGraph(len(rows))
    gm = ROOT.TGraph(len(rows))
    for i, r in enumerate(rows):
        x = float(r["iteration"])
        gb.SetPoint(i, x, float(r["avg_bias2"]))
        gv.SetPoint(i, x, float(r["avg_var"]))
        gm.SetPoint(i, x, float(r["avg_mse"]))

    c = ROOT.TCanvas("c_bias_var", "", 760, 560)
    gb.SetTitle("Bias-Variance-MSE vs iterations")
    gb.SetLineColor(ROOT.kBlue + 1)
    gb.SetMarkerColor(ROOT.kBlue + 1)
    gb.SetMarkerStyle(20)
    gb.SetLineWidth(2)
    gv.SetLineColor(ROOT.kRed + 1)
    gv.SetMarkerColor(ROOT.kRed + 1)
    gv.SetMarkerStyle(21)
    gv.SetLineWidth(2)
    gm.SetLineColor(ROOT.kBlack)
    gm.SetMarkerColor(ROOT.kBlack)
    gm.SetMarkerStyle(24)
    gm.SetLineWidth(2)

    gb.Draw("ALP")
    gb.GetXaxis().SetTitle("Bayesian iterations")
    gb.GetYaxis().SetTitle("Average value over truth bins")
    gv.Draw("LP SAME")
    gm.Draw("LP SAME")

    leg = ROOT.TLegend(0.58, 0.68, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.AddEntry(gb, "Avg bias^{2}", "lp")
    leg.AddEntry(gv, "Avg variance", "lp")
    leg.AddEntry(gm, "Avg MSE", "lp")
    leg.Draw()

    c.SaveAs(outpath)


def main():
    p = argparse.ArgumentParser(description="Overfitting diagnostics vs IBU iterations")
    p.add_argument("--config", default="Unfolding/unfold_config.json")
    p.add_argument("--max-iter", type=int, default=20)
    p.add_argument("--n-toys", type=int, default=80)
    p.add_argument("--seed", type=int, default=24680)
    p.add_argument("--outdir", default="Studies/UnfoldingIterationScan/results")
    args = p.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

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

    data_tree_name = unfold_mod.get_cfg(cfg, "data_tree", default="t")
    reco_tree_name = unfold_mod.get_cfg(cfg, "reco_tree", default="t")
    gen_tree_name = unfold_mod.get_cfg(cfg, "gen_tree", default="tgen")
    reco_branch = unfold_mod.get_cfg(cfg, "reco_branch", default="Thrust")
    gen_branch = unfold_mod.get_cfg(cfg, "gen_branch", default="Thrust")
    selection_branch = unfold_mod.get_cfg(cfg, "selection_branch", default="passEventSelection")
    id_branch = unfold_mod.get_cfg(cfg, "id_branch", default="uniqueID")
    bins = int(unfold_mod.get_cfg(cfg, "bins", default=50))
    xmin = float(unfold_mod.get_cfg(cfg, "xmin", default=0.5))
    xmax = float(unfold_mod.get_cfg(cfg, "xmax", default=1.0))

    for path in [data_file, reco_mc_file, gen_mc_file]:
        unfold_mod.require_file(path)

    f_data = ROOT.TFile.Open(data_file, "READ")
    f_reco = ROOT.TFile.Open(reco_mc_file, "READ")
    f_gen = ROOT.TFile.Open(gen_mc_file, "READ")

    tree_data = unfold_mod.get_tree(f_data, data_tree_name, data_file)
    tree_reco = unfold_mod.get_tree(f_reco, reco_tree_name, reco_mc_file)
    tree_gen = unfold_mod.get_tree(f_gen, gen_tree_name, gen_mc_file)

    _h_data = unfold_mod.make_h1("data_reco", "Data;Thrust;Events", bins, xmin, xmax)
    unfold_mod.fill_hist_from_tree(tree_data, "Thrust", _h_data, xmin, xmax, selection_branch=selection_branch)

    response, _h_reco, h_gen, _, _ = unfold_mod.build_response(
        tree_reco=tree_reco,
        tree_gen=tree_gen,
        id_branch=id_branch,
        reco_branch=reco_branch,
        gen_branch=gen_branch,
        reco_selection_branch=selection_branch,
        bins=bins,
        xmin=xmin,
        xmax=xmax,
        RooUnfoldResponse=unfold_mod.RooUnfoldResponse,
    )

    h_reco_expect = response.ApplyToTruth(h_gen).Clone("h_reco_expect")
    h_reco_expect.SetDirectory(0)

    truth = [float(h_gen.GetBinContent(i + 1)) for i in range(bins)]
    valid_bins = [i for i, t in enumerate(truth) if t > 0.0]

    rng = ROOT.TRandom3(args.seed)
    rows = []
    for it in range(1, args.max_iter + 1):
        toy_vals = [[0.0 for _ in range(len(valid_bins))] for _ in range(args.n_toys)]
        for itoy in range(args.n_toys):
            h_toy = h_reco_expect.Clone(f"h_toy_{it}_{itoy}")
            h_toy.SetDirectory(0)
            for b in range(1, bins + 1):
                mu = float(h_reco_expect.GetBinContent(b))
                n = float(rng.PoissonD(mu)) if mu > 0.0 else 0.0
                h_toy.SetBinContent(b, n)
                h_toy.SetBinError(b, math.sqrt(n) if n > 0.0 else 0.0)

            uf = make_unfolder(response, h_toy, it)
            h_u = uf.Hunfold(RooUnfold.kNoError).Clone(f"h_u_{it}_{itoy}")
            h_u.SetDirectory(0)
            for j, ib in enumerate(valid_bins):
                toy_vals[itoy][j] = float(h_u.GetBinContent(ib + 1))

        # Compute per-bin mean and std
        means = []
        stds = []
        for j, ib in enumerate(valid_bins):
            vals = [toy_vals[k][j] for k in range(args.n_toys)]
            m = sum(vals) / len(vals)
            var = sum((x - m) * (x - m) for x in vals) / max(1, len(vals) - 1)
            s = math.sqrt(var)
            means.append(m)
            stds.append(s)

        avg_bias2 = sum((means[j] - truth[valid_bins[j]]) ** 2 for j in range(len(valid_bins))) / max(1, len(valid_bins))
        avg_var = sum(stds[j] ** 2 for j in range(len(valid_bins))) / max(1, len(valid_bins))
        avg_mse = avg_bias2 + avg_var
        avg_frac_unc = sum((stds[j] / truth[valid_bins[j]]) for j in range(len(valid_bins)) if truth[valid_bins[j]] > 0) / max(1, len(valid_bins))
        avg_fluctuation_width = (
            sum(
                (stds[j] / math.sqrt(truth[valid_bins[j]]))
                for j in range(len(valid_bins))
                if truth[valid_bins[j]] > 0
            )
            / max(1, len(valid_bins))
        )

        # Toy covariance-derived correlation metric
        nbin = len(valid_bins)
        cov_toy = [[0.0 for _ in range(nbin)] for _ in range(nbin)]
        for a in range(nbin):
            for b in range(nbin):
                s = 0.0
                for k in range(args.n_toys):
                    s += (toy_vals[k][a] - means[a]) * (toy_vals[k][b] - means[b])
                cov_toy[a][b] = s / max(1, args.n_toys - 1)

        off_sum = 0.0
        off_n = 0
        for a in range(nbin):
            va = cov_toy[a][a]
            if va <= 0:
                continue
            for b in range(nbin):
                if a == b:
                    continue
                vb = cov_toy[b][b]
                if vb <= 0:
                    continue
                rho = cov_toy[a][b] / math.sqrt(va * vb)
                off_sum += abs(rho)
                off_n += 1
        mean_abs_offdiag_corr = off_sum / max(1, off_n)

        rows.append(
            {
                "iteration": it,
                "avg_frac_unc": avg_frac_unc,
                "avg_fluctuation_width": avg_fluctuation_width,
                "avg_bias2": avg_bias2,
                "avg_var": avg_var,
                "avg_mse": avg_mse,
                "mean_abs_offdiag_corr": mean_abs_offdiag_corr,
            }
        )

    csv_path = os.path.join(outdir, "overfit_study.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    summary = {
        "config": cfg_path,
        "n_toys": args.n_toys,
        "seed": args.seed,
        "min_mse_iteration": min(rows, key=lambda r: r["avg_mse"])["iteration"],
        "fluctuation_width_closest_to_1_iteration": min(
            rows, key=lambda r: abs(r["avg_fluctuation_width"] - 1.0)
        )["iteration"],
        "rows": rows,
    }
    json_path = os.path.join(outdir, "overfit_study_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    make_graph(
        rows,
        "avg_frac_unc",
        "Toy average fractional uncertainty vs iterations",
        "<sigma_{toy}/truth>",
        os.path.join(outdir, "overfit_avg_frac_unc_vs_iterations.pdf"),
    )
    make_graph(
        rows,
        "avg_fluctuation_width",
        "Toy fluctuation width vs iterations",
        "<sigma_{toy}/sqrt(truth)>",
        os.path.join(outdir, "overfit_avg_pull_width_vs_iterations.pdf"),
    )
    make_bias_var_plot(rows, os.path.join(outdir, "overfit_bias_variance_mse_vs_iterations.pdf"))
    make_graph(
        rows,
        "mean_abs_offdiag_corr",
        "Mean |off-diagonal correlation| vs iterations",
        "<|rho_{ij}|>, i!=j",
        os.path.join(outdir, "overfit_mean_abs_offdiag_corr_vs_iterations.pdf"),
    )

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"min MSE iteration: {summary['min_mse_iteration']}")
    print(f"fluctuation width closest to 1 iteration: {summary['fluctuation_width_closest_to_1_iteration']}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
