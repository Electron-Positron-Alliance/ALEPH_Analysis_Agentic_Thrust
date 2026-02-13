#!/usr/bin/env python3
"""
Unfold thrust from tree-based ROOT samples using RooUnfold.

Usage:
  python3 unfold_thrust.py --config unfold_config.json [--set key=value ...]
"""

import argparse
import json
import math
import os
import sys
from array import array

import ROOT
from ROOT import RooUnfoldResponse
from ROOT import RooUnfold
from ROOT import RooUnfoldBayes


def parse_args():
    p = argparse.ArgumentParser(description="RooUnfold-based thrust unfolding from TTrees")
    p.add_argument("--config", required=True, help="Path to JSON config file")
    p.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override config as key=value (repeatable), e.g. --set iterations=8",
    )
    return p.parse_args()


def require_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")


def _parse_scalar(raw):
    s = raw.strip()
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def apply_overrides(cfg, overrides):
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}', expected key=value")
        key, raw = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid override '{item}', empty key")
        cfg[key] = _parse_scalar(raw)
    return cfg


def load_config(path, overrides):
    require_file(path)
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not isinstance(cfg, dict):
        raise ValueError("Config must be a JSON object")
    return apply_overrides(cfg, overrides)


def get_cfg(cfg, key, default=None, required=False):
    if key in cfg:
        return cfg[key]
    if required:
        raise KeyError(f"Missing required config key: {key}")
    return default


def get_tree(tfile, tree_name, file_label):
    tree = tfile.Get(tree_name)
    if not tree:
        raise KeyError(f"Tree '{tree_name}' not found in {file_label}")
    return tree


def branch_exists(tree, branch):
    return tree.GetBranch(branch) is not None


def passes_selection(tree, selection_branch):
    if not selection_branch:
        return True
    value = getattr(tree, selection_branch)
    return bool(value)


def make_h1(name, title, bins, xmin, xmax):
    h = ROOT.TH1D(name, title, bins, xmin, xmax)
    h.Sumw2()
    h.SetDirectory(0)
    return h


def make_h2(name, title, bins, xmin, xmax):
    h = ROOT.TH2D(name, title, bins, xmin, xmax, bins, xmin, xmax)
    h.Sumw2()
    h.SetDirectory(0)
    return h


def fill_hist_from_tree(tree, branch, hist, xmin, xmax, selection_branch=None):
    n = tree.GetEntries()
    for i in range(n):
        tree.GetEntry(i)
        if not passes_selection(tree, selection_branch):
            continue
        x = float(getattr(tree, branch))
        if x >= xmin and x < xmax and math.isfinite(x):
            hist.Fill(x)


def build_reco_lookup(tree_reco, id_branch, reco_branch, xmin, xmax, selection_branch=None):
    lookup = {}
    selected_ids = set()
    n = tree_reco.GetEntries()
    for i in range(n):
        tree_reco.GetEntry(i)
        if not passes_selection(tree_reco, selection_branch):
            continue
        ev_id = int(getattr(tree_reco, id_branch))
        selected_ids.add(ev_id)
        x_reco = float(getattr(tree_reco, reco_branch))
        if x_reco >= xmin and x_reco < xmax and math.isfinite(x_reco):
            lookup[ev_id] = x_reco
    return lookup, selected_ids


def build_response(
    tree_reco,
    tree_gen,
    id_branch,
    reco_branch,
    gen_branch,
    reco_selection_branch,
    bins,
    xmin,
    xmax,
    RooUnfoldResponse,
):
    h_reco = make_h1("mc_reco", "MC reco;Thrust;Events", bins, xmin, xmax)
    h_gen = make_h1("mc_gen", "MC gen;Thrust;Events", bins, xmin, xmax)
    h_resp_counts = make_h2(
        "response_counts", "Response counts;Reco thrust;Gen thrust", bins, xmin, xmax
    )

    fill_hist_from_tree(
        tree_reco, reco_branch, h_reco, xmin, xmax, selection_branch=reco_selection_branch
    )
    reco_lookup, selected_reco_ids = build_reco_lookup(
        tree_reco, id_branch, reco_branch, xmin, xmax, selection_branch=reco_selection_branch
    )

    response = RooUnfoldResponse(bins, xmin, xmax, bins, xmin, xmax)

    n_gen = tree_gen.GetEntries()
    matched = 0
    for i in range(n_gen):
        tree_gen.GetEntry(i)
        ev_id = int(getattr(tree_gen, id_branch))
        if ev_id not in selected_reco_ids:
            continue
        x_gen = float(getattr(tree_gen, gen_branch))
        if not (x_gen >= xmin and x_gen < xmax and math.isfinite(x_gen)):
            continue

        h_gen.Fill(x_gen)
        if ev_id in reco_lookup:
            x_reco = reco_lookup[ev_id]
            response.Fill(x_reco, x_gen)
            h_resp_counts.Fill(x_reco, x_gen)
            matched += 1
        else:
            response.Miss(x_gen)

    return response, h_reco, h_gen, h_resp_counts, matched


def matrix_to_th2(name, title, mat, bins, xmin, xmax):
    h2 = make_h2(name, title, bins, xmin, xmax)
    nrows = mat.GetNrows()
    ncols = mat.GetNcols()
    for i in range(min(bins, nrows)):
        for j in range(min(bins, ncols)):
            h2.SetBinContent(i + 1, j + 1, float(mat[i][j]))
    return h2


def hist_efficiency(response, bins, xmin, xmax):
    # Efficiency(j) = sum_i response(i,j) / truth(j)
    h_true = response.Htruth()
    mresp = response.Mresponse()
    h_eff = make_h1("efficiency", "Reco efficiency;Thrust;Efficiency", bins, xmin, xmax)
    for b in range(1, bins + 1):
        n_true = h_true.GetBinContent(b)
        eff = 0.0
        if n_true > 0.0:
            n_detected = 0.0
            j = b - 1
            for i in range(mresp.GetNrows()):
                n_detected += float(mresp[i][j])
            eff = max(0.0, n_detected / n_true)
        h_eff.SetBinContent(b, eff)
    return h_eff


def make_measured_cov_from_hist(hist, bins):
    cov = ROOT.TMatrixD(bins, bins)
    for i in range(bins):
        err = float(hist.GetBinError(i + 1))
        cov[i][i] = err * err
    return cov


def integral_in_range(hist):
    """Integral over visible bins (exclude under/overflow)."""
    return hist.Integral(1, hist.GetNbinsX())


def default_genbefore_file_from_gen(gen_file):
    if "_tgen.root" in gen_file:
        return gen_file.replace("_tgen.root", "_tgenBefore.root")
    if "tgen.root" in gen_file:
        return gen_file.replace("tgen.root", "tgenBefore.root")
    return gen_file.replace(".root", "_tgenBefore.root")


def make_hadronic_event_sel_correction(tree_gen, tree_gen_before, gen_branch, bins, xmin, xmax):
    """
    Build correction = (tgenBefore spectrum) / (tgen spectrum used in response),
    then apply it bin-by-bin after unfolding.
    """
    h_gen_all = make_h1("mc_gen_all", "MC gen (all);Thrust;Events", bins, xmin, xmax)
    h_gen_before = make_h1("mc_genBefore", "MC genBefore;Thrust;Events", bins, xmin, xmax)
    fill_hist_from_tree(tree_gen, gen_branch, h_gen_all, xmin, xmax, selection_branch=None)
    fill_hist_from_tree(tree_gen_before, gen_branch, h_gen_before, xmin, xmax, selection_branch=None)

    h_corr = make_h1(
        "hadronic_event_sel_corr",
        "Hadronic event selection correction;Thrust;tgenBefore/tgen",
        bins,
        xmin,
        xmax,
    )
    for b in range(1, bins + 1):
        num = float(h_gen_before.GetBinContent(b))
        den = float(h_gen_all.GetBinContent(b))
        if den > 0.0:
            h_corr.SetBinContent(b, num / den)
        else:
            h_corr.SetBinContent(b, 1.0)
        h_corr.SetBinError(b, 0.0)

    return h_gen_all, h_gen_before, h_corr


def main():
    args = parse_args()
    cfg = load_config(args.config, args.set)

    data_file = get_cfg(cfg, "data_file", required=True)
    reco_mc_file = get_cfg(cfg, "reco_mc_file", required=True)
    gen_mc_file = get_cfg(cfg, "gen_mc_file", required=True)
    genbefore_mc_file = get_cfg(cfg, "genbefore_mc_file", default=default_genbefore_file_from_gen(gen_mc_file))

    data_tree_name = get_cfg(cfg, "data_tree", default="t")
    reco_tree_name = get_cfg(cfg, "reco_tree", default="t")
    gen_tree_name = get_cfg(cfg, "gen_tree", default="t")
    genbefore_tree_name = get_cfg(cfg, "genbefore_tree", default="tgenBefore")

    data_branch = get_cfg(cfg, "data_branch", default="Thrust")
    reco_branch = get_cfg(cfg, "reco_branch", default="Thrust")
    gen_branch = get_cfg(cfg, "gen_branch", default="Thrust")
    selection_branch = get_cfg(cfg, "selection_branch", default="passEventSelection")
    id_branch = get_cfg(cfg, "id_branch", default="uniqueID")

    bins = int(get_cfg(cfg, "bins", default=25))
    xmin = float(get_cfg(cfg, "xmin", default=0.5))
    xmax = float(get_cfg(cfg, "xmax", default=1.0))
    iterations = int(get_cfg(cfg, "iterations", default=6))
    calculate_covariance = bool(get_cfg(cfg, "calculate_covariance", default=False))
    closure_check = bool(get_cfg(cfg, "closure_check", default=False))

    out_root = get_cfg(cfg, "out_root", default="unfolded_thrust.root")
    if closure_check:
        out_root = out_root.replace(".root", "_closure.root")
        
    for path in [data_file, reco_mc_file, gen_mc_file, genbefore_mc_file]:
        require_file(path)

    f_data = ROOT.TFile.Open(data_file, "READ")
    f_reco = ROOT.TFile.Open(reco_mc_file, "READ")
    f_gen = ROOT.TFile.Open(gen_mc_file, "READ")
    f_genbefore = ROOT.TFile.Open(genbefore_mc_file, "READ")
    if not f_data or f_data.IsZombie():
        raise RuntimeError(f"Failed to open data file: {data_file}")
    if not f_reco or f_reco.IsZombie():
        raise RuntimeError(f"Failed to open reco MC file: {reco_mc_file}")
    if not f_gen or f_gen.IsZombie():
        raise RuntimeError(f"Failed to open gen MC file: {gen_mc_file}")
    if not f_genbefore or f_genbefore.IsZombie():
        raise RuntimeError(f"Failed to open genBefore MC file: {genbefore_mc_file}")

    tree_data = get_tree(f_data, data_tree_name, data_file)
    tree_reco = get_tree(f_reco, reco_tree_name, reco_mc_file)
    tree_gen = get_tree(f_gen, gen_tree_name, gen_mc_file)
    tree_genbefore = get_tree(f_genbefore, genbefore_tree_name, genbefore_mc_file)

    branch_checks = [
        (tree_reco, reco_tree_name, reco_branch),
        (tree_reco, reco_tree_name, selection_branch),
        (tree_gen, gen_tree_name, gen_branch),
        (tree_reco, reco_tree_name, id_branch),
        (tree_gen, gen_tree_name, id_branch),
        (tree_genbefore, genbefore_tree_name, gen_branch),
    ]
    if not closure_check:
        branch_checks.extend(
            [
                (tree_data, data_tree_name, data_branch),
                (tree_data, data_tree_name, selection_branch),
            ]
        )

    for tree, tname, bname in branch_checks:
        if not branch_exists(tree, bname):
            raise KeyError(f"Branch '{bname}' not found in tree '{tname}'")

    h_data = make_h1("data_reco", "Data (reco);Thrust;Events", bins, xmin, xmax)
    if closure_check:
        h_data.SetTitle("Closure input (MC reco);Thrust;Events")
        fill_hist_from_tree(
            tree_reco, reco_branch, h_data, xmin, xmax, selection_branch=selection_branch
        )
    else:
        fill_hist_from_tree(
            tree_data, data_branch, h_data, xmin, xmax, selection_branch=selection_branch
        )

    response, h_reco, h_gen, h_resp_counts, n_match = build_response(
        tree_reco=tree_reco,
        tree_gen=tree_gen,
        id_branch=id_branch,
        reco_branch=reco_branch,
        gen_branch=gen_branch,
        reco_selection_branch=selection_branch,
        bins=bins,
        xmin=xmin,
        xmax=xmax,
        RooUnfoldResponse=RooUnfoldResponse,
    )

    unfold = RooUnfoldBayes(response, h_data, iterations)
    if calculate_covariance:
        measured_cov = make_measured_cov_from_hist(h_data, bins)
        unfold.SetMeasuredCov(measured_cov)
    h_unfolded = unfold.Hunfold(RooUnfold.kNoError)
    h_unfolded = h_unfolded.Clone("unfolded")
    h_unfolded.SetTitle(f"Unfolded ({iterations} iters);Thrust;Events")

    h_gen_all, h_genbefore, h_hadsel_corr = make_hadronic_event_sel_correction(
        tree_gen=tree_gen,
        tree_gen_before=tree_genbefore,
        gen_branch=gen_branch,
        bins=bins,
        xmin=xmin,
        xmax=xmax,
    )
    h_unfolded_corrected = h_unfolded.Clone("unfolded_corrected")
    h_unfolded_corrected.SetTitle(f"Unfolded corrected ({iterations} iters);Thrust;Events")
    # Use ROOT's bin-by-bin multiplication with propagated uncertainties.
    h_unfolded_corrected.Multiply(h_hadsel_corr)

    h_eff = hist_efficiency(response, bins, xmin, xmax)
    h_mresp = matrix_to_th2(
        "response_prob_reco_given_gen",
        "Response P(reco|gen);Reco thrust;Gen thrust",
        response.Mresponse(),
        bins,
        xmin,
        xmax,
    )

    out_objects = [
        h_data,
        h_reco,
        h_gen,
        h_gen_all,
        h_genbefore,
        h_hadsel_corr,
        h_resp_counts,
        h_mresp,
        h_eff,
        h_unfolded,
        h_unfolded_corrected,
    ]

    if calculate_covariance:
        cov = unfold.Eunfold(RooUnfold.kCovariance)
        h_cov = matrix_to_th2(
            "unfold_covariance",
            "Unfolded covariance;Truth bin;Truth bin",
            cov,
            bins,
            xmin,
            xmax,
        )
        out_objects.append(h_cov)

    fout = ROOT.TFile(out_root, "RECREATE")
    for obj in out_objects:
        obj.Write()
    fout.Close()

    f_data.Close()
    f_reco.Close()
    f_gen.Close()
    f_genbefore.Close()

    print("Unfolding complete (RooUnfold)")
    print(f"  closure check mode: {closure_check}")
    print(f"  data events in range: {int(integral_in_range(h_data))}")
    print(f"  mc reco events in range: {int(integral_in_range(h_reco))}")
    print(f"  mc gen events in range: {int(integral_in_range(h_gen))}")
    print(f"  mc genBefore events in range: {int(integral_in_range(h_genbefore))}")
    print(f"  matched reco<->gen events: {int(n_match)}")
    print("  applied correction: hadronic_event_sel_corr = tgenBefore/tgen (bin-by-bin)")
    print(f"  output ROOT: {out_root}")


if __name__ == "__main__":
    try:
        ROOT.TH1.SetDefaultSumw2(True)
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
