#!/usr/bin/env python3
"""Scan Bayesian unfolding iterations and evaluate chi2/ndf diagnostics."""

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


def chi2_ndf(obs, exp):
    """Pearson chi2 with expected variance from exp bin counts."""
    nb = min(obs.GetNbinsX(), exp.GetNbinsX())
    chi2 = 0.0
    nused = 0
    for b in range(1, nb + 1):
        o = float(obs.GetBinContent(b))
        e = float(exp.GetBinContent(b))
        if e <= 0.0:
            continue
        chi2 += (o - e) * (o - e) / e
        nused += 1
    ndf = max(1, nused - 1)
    return chi2, ndf, chi2 / ndf


def chi2_ndf_with_errors(h1, h2):
    """Chi2/ndf using combined bin errors from both histograms."""
    nb = min(h1.GetNbinsX(), h2.GetNbinsX())
    chi2 = 0.0
    nused = 0
    for b in range(1, nb + 1):
        x1 = float(h1.GetBinContent(b))
        x2 = float(h2.GetBinContent(b))
        e1 = float(h1.GetBinError(b))
        e2 = float(h2.GetBinError(b))
        var = e1 * e1 + e2 * e2
        if var <= 0.0:
            continue
        chi2 += (x1 - x2) * (x1 - x2) / var
        nused += 1
    ndf = max(1, nused - 1)
    return chi2, ndf, chi2 / ndf


def normalized_clone(h, name):
    c = h.Clone(name)
    c.SetDirectory(0)
    integ = c.Integral(1, c.GetNbinsX())
    if integ > 0.0:
        c.Scale(1.0 / integ)
    return c


def diff_xsec_clone(h, name):
    """Return 1/N dN/dx histogram (unit area, per-bin-width)."""
    c = h.Clone(name)
    c.SetDirectory(0)
    integ = c.Integral(1, c.GetNbinsX())
    if integ > 0.0:
        c.Scale(1.0 / integ, "width")
    return c


def pick_recommended(results):
    # Prefer points with reasonable data agreement first, then pick toy closure nearest unity.
    candidates = [r for r in results if r["refold_chi2_ndf"] <= 2.5]
    if not candidates:
        candidates = list(results)
    candidates.sort(
        key=lambda r: (
            abs(r["toy_closure_mean_chi2_ndf"] - 1.0),
            abs(r["refold_chi2_ndf"] - 2.0),
            r["iteration"],
        )
    )
    return candidates[0]


def make_graph(results, xkey, ykey, title, outpath):
    g = ROOT.TGraph(len(results))
    for i, row in enumerate(results):
        g.SetPoint(i, float(row[xkey]), float(row[ykey]))

    c = ROOT.TCanvas("c_" + ykey, "", 700, 550)
    g.SetTitle(title)
    g.SetMarkerStyle(20)
    g.SetMarkerSize(1.0)
    g.SetLineWidth(2)
    g.Draw("ALP")
    g.GetXaxis().SetTitle("Bayesian iterations")
    g.GetYaxis().SetTitle("chi^{2}/ndf")
    c.SaveAs(outpath)


def find_convergence_iteration(results, key, frac_drop_threshold=0.10, min_points=3):
    """
    Find first iteration where the selected metric flattens:
    fractional drop between consecutive points stays below threshold
    for `min_points` consecutive steps.
    """
    values = [(int(r["iteration"]), float(r[key])) for r in results if int(r["iteration"]) >= 2]
    if len(values) < min_points + 1:
        return None
    small = 0
    for i in range(1, len(values)):
        it_prev, v_prev = values[i - 1]
        it_now, v_now = values[i]
        if v_prev <= 0.0:
            small = 0
            continue
        frac_drop = (v_prev - v_now) / v_prev
        if frac_drop < frac_drop_threshold:
            small += 1
        else:
            small = 0
        if small >= min_points:
            return it_now
    return None


def find_threshold_crossing(results, key, threshold):
    for r in results:
        if int(r["iteration"]) < 2:
            continue
        if float(r[key]) <= threshold:
            return int(r["iteration"])
    return None


def make_unfolder(response, measured, iterations):
    uf = RooUnfoldBayes(response, measured, iterations)
    if hasattr(uf, "SetVerbose"):
        uf.SetVerbose(0)
    return uf


def main():
    p = argparse.ArgumentParser(description="Scan unfolding iterations")
    p.add_argument("--config", default="Unfolding/unfold_config.json")
    p.add_argument("--max-iter", type=int, default=20)
    p.add_argument("--outdir", default="Studies/UnfoldingIterationScan/results")
    p.add_argument("--n-toys", type=int, default=150)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--delta-conv-threshold", type=float, default=0.10)
    p.add_argument("--delta-shape-conv-threshold", type=float, default=1.0e-7)
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

    data_branch = unfold_mod.get_cfg(cfg, "data_branch", default="Thrust")
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

    h_data = unfold_mod.make_h1("data_reco", "Data;Thrust;Events", bins, xmin, xmax)
    unfold_mod.fill_hist_from_tree(tree_data, data_branch, h_data, xmin, xmax, selection_branch=selection_branch)

    response, h_reco, h_gen, _, _, _ = unfold_mod.build_response(
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

    # Closure input is reconstructed MC with event selection.
    h_closure_in = unfold_mod.make_h1("closure_input", "Closure Input;Thrust;Events", bins, xmin, xmax)
    unfold_mod.fill_hist_from_tree(tree_reco, reco_branch, h_closure_in, xmin, xmax, selection_branch=selection_branch)
    h_reco_expect = response.ApplyToTruth(h_gen).Clone("reco_expect_from_truth")
    h_reco_expect.SetDirectory(0)
    rng = ROOT.TRandom3(args.seed)

    results = []
    prev_unf_data = None
    for it in range(1, args.max_iter + 1):
        uf_data = make_unfolder(response, h_data, it)
        h_unf_data = uf_data.Hunfold(RooUnfold.kNoError).Clone(f"unf_data_it{it}")
        h_unf_data.SetDirectory(0)

        h_refold = response.ApplyToTruth(h_unf_data).Clone(f"refold_it{it}")
        h_refold.SetDirectory(0)

        chi2_refold, ndf_refold, cndf_refold = chi2_ndf(h_data, h_refold)
        h_data_shape = normalized_clone(h_data, f"data_shape_it{it}")
        h_refold_shape = normalized_clone(h_refold, f"refold_shape_it{it}")
        chi2_refold_shape, ndf_refold_shape, cndf_refold_shape = chi2_ndf(h_data_shape, h_refold_shape)
        h_data_diff = diff_xsec_clone(h_data, f"data_diff_it{it}")
        h_refold_diff = diff_xsec_clone(h_refold, f"refold_diff_it{it}")
        chi2_refold_diff, ndf_refold_diff, cndf_refold_diff = chi2_ndf_with_errors(
            h_data_diff, h_refold_diff
        )

        uf_closure = make_unfolder(response, h_closure_in, it)
        h_unf_closure = uf_closure.Hunfold(RooUnfold.kNoError).Clone(f"unf_closure_it{it}")
        h_unf_closure.SetDirectory(0)

        chi2_closure, ndf_closure, cndf_closure = chi2_ndf(h_unf_closure, h_gen)
        h_unf_closure_shape = normalized_clone(h_unf_closure, f"unf_closure_shape_it{it}")
        h_gen_shape = normalized_clone(h_gen, f"gen_shape_it{it}")
        chi2_closure_shape, ndf_closure_shape, cndf_closure_shape = chi2_ndf(h_unf_closure_shape, h_gen_shape)

        toy_vals = []
        for _ in range(args.n_toys):
            h_toy = h_reco_expect.Clone(f"h_toy_it{it}")
            h_toy.SetDirectory(0)
            for b in range(1, h_toy.GetNbinsX() + 1):
                mu = float(h_reco_expect.GetBinContent(b))
                n = float(rng.PoissonD(mu)) if mu > 0.0 else 0.0
                h_toy.SetBinContent(b, n)
                h_toy.SetBinError(b, math.sqrt(n) if n > 0.0 else 0.0)
            uf_toy = make_unfolder(response, h_toy, it)
            h_unf_toy = uf_toy.Hunfold(RooUnfold.kNoError).Clone(f"unf_toy_it{it}")
            h_unf_toy.SetDirectory(0)
            _, _, cndf_toy = chi2_ndf(h_unf_toy, h_gen)
            toy_vals.append(cndf_toy)
        toy_mean = sum(toy_vals) / max(1, len(toy_vals))
        toy_var = sum((x - toy_mean) ** 2 for x in toy_vals) / max(1, len(toy_vals) - 1)
        toy_std = math.sqrt(toy_var)

        if prev_unf_data is None:
            delta_chi2 = 0.0
            delta_ndf = 1
            delta_cndf = 0.0
            delta_shape_chi2 = 0.0
            delta_shape_ndf = 1
            delta_shape_cndf = 0.0
            delta_diff_chi2 = 0.0
            delta_diff_ndf = 1
            delta_diff_cndf = 0.0
        else:
            delta_chi2, delta_ndf, delta_cndf = chi2_ndf(h_unf_data, prev_unf_data)
            h_unf_data_shape = normalized_clone(h_unf_data, f"unf_data_shape_it{it}")
            h_prev_unf_shape = normalized_clone(prev_unf_data, f"prev_unf_shape_it{it}")
            delta_shape_chi2, delta_shape_ndf, delta_shape_cndf = chi2_ndf(
                h_unf_data_shape, h_prev_unf_shape
            )
            h_unf_data_diff = diff_xsec_clone(h_unf_data, f"unf_data_diff_it{it}")
            h_prev_unf_diff = diff_xsec_clone(prev_unf_data, f"prev_unf_diff_it{it}")
            delta_diff_chi2, delta_diff_ndf, delta_diff_cndf = chi2_ndf_with_errors(
                h_unf_data_diff, h_prev_unf_diff
            )

        results.append(
            {
                "iteration": it,
                "refold_chi2": chi2_refold,
                "refold_ndf": ndf_refold,
                "refold_chi2_ndf": cndf_refold,
                "refold_shape_chi2": chi2_refold_shape,
                "refold_shape_ndf": ndf_refold_shape,
                "refold_shape_chi2_ndf": cndf_refold_shape,
                "refold_diffxsec_chi2": chi2_refold_diff,
                "refold_diffxsec_ndf": ndf_refold_diff,
                "refold_diffxsec_chi2_ndf": cndf_refold_diff,
                "closure_chi2": chi2_closure,
                "closure_ndf": ndf_closure,
                "closure_chi2_ndf": cndf_closure,
                "closure_shape_chi2": chi2_closure_shape,
                "closure_shape_ndf": ndf_closure_shape,
                "closure_shape_chi2_ndf": cndf_closure_shape,
                "iter_delta_chi2": delta_chi2,
                "iter_delta_ndf": delta_ndf,
                "iter_delta_chi2_ndf": delta_cndf,
                "iter_delta_shape_chi2": delta_shape_chi2,
                "iter_delta_shape_ndf": delta_shape_ndf,
                "iter_delta_shape_chi2_ndf": delta_shape_cndf,
                "iter_delta_diffxsec_chi2": delta_diff_chi2,
                "iter_delta_diffxsec_ndf": delta_diff_ndf,
                "iter_delta_diffxsec_chi2_ndf": delta_diff_cndf,
                "toy_closure_mean_chi2_ndf": toy_mean,
                "toy_closure_std_chi2_ndf": toy_std,
            }
        )
        prev_unf_data = h_unf_data.Clone(f"unf_data_prev_cache_it{it}")
        prev_unf_data.SetDirectory(0)

    rec = pick_recommended(results)
    conv_it = find_convergence_iteration(results, "iter_delta_chi2_ndf")
    conv_shape_it = find_convergence_iteration(results, "iter_delta_shape_chi2_ndf")
    conv_thr_it = find_threshold_crossing(results, "iter_delta_chi2_ndf", args.delta_conv_threshold)
    conv_shape_thr_it = find_threshold_crossing(
        results, "iter_delta_shape_chi2_ndf", args.delta_shape_conv_threshold
    )

    csv_path = os.path.join(outdir, "iteration_scan.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    summary = {
        "config": os.path.abspath(args.config),
        "max_iter": args.max_iter,
        "recommendation": rec,
        "convergence": {
            "counts_metric": "chi2/ndf(unfolded_N, unfolded_N-1)",
            "shape_metric": "chi2/ndf(unfolded_N_norm, unfolded_N-1_norm)",
            "diffxsec_metric": "chi2/ndf((1/N dN/dT)_N, (1/N dN/dT)_{N-1}) with combined bin errors",
            "counts_flatten_iteration": conv_it,
            "shape_flatten_iteration": conv_shape_it,
            "flatten_rule": "first N where fractional drop stays <10% for 3 consecutive iteration steps",
            "counts_threshold": args.delta_conv_threshold,
            "shape_threshold": args.delta_shape_conv_threshold,
            "counts_threshold_iteration": conv_thr_it,
            "shape_threshold_iteration": conv_shape_thr_it,
            "threshold_rule": "first N where iteration-to-iteration chi2/ndf drops below threshold",
        },
        "metrics": {
            "refold_shape_definition": "chi2(data_reco_norm, refolded_unfolded_norm)/ndf",
            "refold_diffxsec_definition": "chi2((1/N dN/dT)_data, (1/N dN/dT)_refold)/ndf with combined bin errors",
            "closure_definition": "chi2(unfolded_mc_reco_input, mc_gen_truth)/ndf",
            "toy_closure_definition": "mean_toys[ chi2(unfolded_pseudo_reco, mc_gen_truth)/ndf ] with pseudo_reco~Poisson(response*truth)",
        },
    }
    json_path = os.path.join(outdir, "iteration_scan_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    make_graph(
        results,
        "iteration",
        "refold_shape_chi2_ndf",
        "Refolded-vs-Data (shape) chi^{2}/ndf vs iterations",
        os.path.join(outdir, "chi2ndf_refold_shape_vs_iterations.pdf"),
    )
    make_graph(
        results,
        "iteration",
        "toy_closure_mean_chi2_ndf",
        "Toy closure (counts) mean chi^{2}/ndf vs iterations",
        os.path.join(outdir, "chi2ndf_toy_closure_counts_vs_iterations.pdf"),
    )
    make_graph(
        results,
        "iteration",
        "closure_shape_chi2_ndf",
        "Closure (shape) chi^{2}/ndf vs iterations",
        os.path.join(outdir, "chi2ndf_closure_shape_vs_iterations.pdf"),
    )
    make_graph(
        results,
        "iteration",
        "iter_delta_chi2_ndf",
        "Consecutive iterations: chi^{2}/ndf(unfolded_{N}, unfolded_{N-1})",
        os.path.join(outdir, "chi2ndf_iter_delta_counts_vs_iterations.pdf"),
    )
    make_graph(
        results,
        "iteration",
        "iter_delta_shape_chi2_ndf",
        "Consecutive iterations (shape): chi^{2}/ndf(unfolded_{N}, unfolded_{N-1})",
        os.path.join(outdir, "chi2ndf_iter_delta_shape_vs_iterations.pdf"),
    )
    make_graph(
        results,
        "iteration",
        "iter_delta_diffxsec_chi2_ndf",
        "Consecutive iterations (diff xsec): chi^{2}/ndf((1/N dN/dT)_{N}, (1/N dN/dT)_{N-1})",
        os.path.join(outdir, "chi2ndf_iter_delta_diffxsec_vs_iterations.pdf"),
    )

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"Recommended iterations: {rec['iteration']}")
    print(
        "Convergence estimate (counts/shape): "
        f"{conv_it if conv_it is not None else 'none'} / {conv_shape_it if conv_shape_it is not None else 'none'}"
    )
    print(
        "Threshold crossing (counts/shape): "
        f"{conv_thr_it if conv_thr_it is not None else 'none'} / {conv_shape_thr_it if conv_shape_thr_it is not None else 'none'}"
    )
    print(
        "  refold_shape_chi2/ndf="
        f"{rec['refold_shape_chi2_ndf']:.3f}, toy_closure_mean_chi2/ndf={rec['toy_closure_mean_chi2_ndf']:.3f}"
    )


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
