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

import numpy as np
import ROOT
from ROOT import RooUnfoldResponse
from ROOT import RooUnfold
from ROOT import RooUnfoldBayes


OBSERVABLE_PRESETS = {
    "thrust": {
        "branch": "Thrust",
        "bins": 50,
        "xmin": 0.5,
        "xmax": 1.0,
        "axis_label": "Thrust",
    },
    "c_parameter": {
        "branch": "CParameter",
        "bins": 50,
        "xmin": 0.0,
        "xmax": 1.0,
        "axis_label": "C-parameter",
    },
    "heavy_jet_mass": {
        "branch": "HeavyJetMass",
        "bins": 50,
        "xmin": 0.0,
        "xmax": 0.5,
        "axis_label": "Heavy jet mass",
    },
}


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


def get_observable_preset(name):
    key = str(name).strip().lower()
    if key not in OBSERVABLE_PRESETS:
        supported = ", ".join(sorted(OBSERVABLE_PRESETS.keys()))
        raise ValueError(f"Unsupported observable '{name}'. Supported: {supported}")
    return key, OBSERVABLE_PRESETS[key]


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


def fill_hist_from_tree(
    tree,
    branch,
    hist,
    xmin,
    xmax,
    selection_branch=None,
    id_branch=None,
    weight_lookup=None,
    default_weight=1.0,
):
    n = tree.GetEntries()
    for i in range(n):
        tree.GetEntry(i)
        if not passes_selection(tree, selection_branch):
            continue
        x = float(getattr(tree, branch))
        if x >= xmin and x < xmax and math.isfinite(x):
            weight = float(default_weight)
            if weight_lookup is not None:
                if not id_branch:
                    raise ValueError("id_branch is required when weight_lookup is provided")
                ev_id = int(getattr(tree, id_branch))
                weight = float(weight_lookup.get(ev_id, default_weight))
            if not math.isfinite(weight):
                continue
            hist.Fill(x, weight)


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
    axis_label,
    RooUnfoldResponse,
    gen_weight_lookup=None,
    gen_default_weight=1.0,
):
    h_reco = make_h1("mc_reco", f"MC reco;{axis_label};Events", bins, xmin, xmax)
    h_gen = make_h1("mc_gen", f"MC gen;{axis_label};Events", bins, xmin, xmax)
    h_resp_counts = make_h2(
        "response_counts",
        f"Response counts;Reco {axis_label};Gen {axis_label}",
        bins,
        xmin,
        xmax,
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
    matched_weight_sum = 0.0
    for i in range(n_gen):
        tree_gen.GetEntry(i)
        ev_id = int(getattr(tree_gen, id_branch))
        if ev_id not in selected_reco_ids:
            continue
        x_gen = float(getattr(tree_gen, gen_branch))
        if not (x_gen >= xmin and x_gen < xmax and math.isfinite(x_gen)):
            continue

        weight = float(gen_default_weight)
        if gen_weight_lookup is not None:
            weight = float(gen_weight_lookup.get(ev_id, gen_default_weight))
        if not math.isfinite(weight):
            continue

        h_gen.Fill(x_gen, weight)
        if ev_id in reco_lookup:
            x_reco = reco_lookup[ev_id]
            response.Fill(x_reco, x_gen, weight)
            h_resp_counts.Fill(x_reco, x_gen, weight)
            matched += 1
            matched_weight_sum += weight
        else:
            response.Miss(x_gen, weight)

    return response, h_reco, h_gen, h_resp_counts, matched, matched_weight_sum


def matrix_to_th2(name, title, mat, bins, xmin, xmax):
    h2 = make_h2(name, title, bins, xmin, xmax)
    nrows = mat.GetNrows()
    ncols = mat.GetNcols()
    for i in range(min(bins, nrows)):
        for j in range(min(bins, ncols)):
            h2.SetBinContent(i + 1, j + 1, float(mat[i][j]))
    return h2


def covariance_to_correlation_th2(name, title, cov, bins, xmin, xmax):
    h2 = make_h2(name, title, bins, xmin, xmax)
    nrows = cov.GetNrows()
    ncols = cov.GetNcols()
    for i in range(min(bins, nrows)):
        vii = float(cov[i][i])
        for j in range(min(bins, ncols)):
            vjj = float(cov[j][j])
            denom = math.sqrt(max(0.0, vii) * max(0.0, vjj))
            if denom > 0.0:
                corr = float(cov[i][j]) / denom
                corr = max(-1.0, min(1.0, corr))
            else:
                corr = 0.0
            h2.SetBinContent(i + 1, j + 1, corr)
    return h2


def hist_efficiency(response, bins, xmin, xmax, axis_label):
    # Efficiency(j) = sum_i response(i,j) / truth(j)
    h_true = response.Htruth()
    mresp = response.Mresponse()
    h_eff = make_h1("efficiency", f"Reco efficiency;{axis_label};Efficiency", bins, xmin, xmax)
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


def make_weight_hist(name, title, values):
    if len(values) == 0:
        return None
    max_val = max(values)
    x_max = max(2.0, min(max_val * 1.05, 50.0))
    h = ROOT.TH1D(name, title, 120, 0.0, x_max)
    h.Sumw2()
    h.SetDirectory(0)
    for w in values:
        if math.isfinite(w):
            h.Fill(float(w))
    return h


def build_theory_weight_maps(
    tree_gen,
    tree_weights,
    gen_id_branch,
    weight_id_branch,
    weights_path,
    strict_length=True,
    weight_clipping_max=None,
    normalize_weights_mean1=True,
):
    require_file(weights_path)
    raw_weights = np.load(weights_path)
    if raw_weights.ndim != 1:
        raw_weights = raw_weights.reshape(-1)
    weights = np.asarray(raw_weights, dtype=np.float64)

    n_weight_tree = int(tree_weights.GetEntries())
    if len(weights) != n_weight_tree:
        msg = (
            f"theory weight length mismatch: npy has {len(weights)} entries but "
            f"weight tree has {n_weight_tree} entries"
        )
        if strict_length:
            raise ValueError(msg)
        n_min = min(len(weights), n_weight_tree)
        print(f"WARNING: {msg}; truncating to {n_min}")
        weights = weights[:n_min]

    if not np.all(np.isfinite(weights)):
        raise ValueError("theory weights contain non-finite values")

    if weight_clipping_max is not None and float(weight_clipping_max) > 0.0:
        clip_max = float(weight_clipping_max)
        weights = np.clip(weights, 0.0, clip_max)

    if normalize_weights_mean1:
        mean_w = float(np.mean(weights))
        if not math.isfinite(mean_w) or mean_w <= 0.0:
            raise ValueError(f"invalid mean theory weight for normalization: {mean_w}")
        weights = weights / mean_w

    weight_lookup = {}
    n_dup_weights = 0
    n_iter = min(n_weight_tree, len(weights))
    for i in range(n_iter):
        tree_weights.GetEntry(i)
        ev_id = int(getattr(tree_weights, weight_id_branch))
        if ev_id in weight_lookup:
            n_dup_weights += 1
        weight_lookup[ev_id] = float(weights[i])

    gen_lookup = {}
    gen_mapped_weights = []
    n_gen = int(tree_gen.GetEntries())
    n_gen_matched = 0
    for i in range(n_gen):
        tree_gen.GetEntry(i)
        ev_id = int(getattr(tree_gen, gen_id_branch))
        if ev_id in weight_lookup:
            w = float(weight_lookup[ev_id])
            n_gen_matched += 1
        else:
            w = 1.0
        gen_lookup[ev_id] = w
        gen_mapped_weights.append(w)

    weight_values = [float(v) for v in weights.tolist()]
    h_weight_input = make_weight_hist(
        "theory_weights_tgenBefore",
        "Theory weights on tgenBefore;Weight;Events",
        weight_values,
    )
    h_weight_gen = make_weight_hist(
        "theory_weights_tgen_mapped",
        "Theory weights mapped to tgen;Weight;Events",
        gen_mapped_weights,
    )

    h_coverage = ROOT.TH1D(
        "theory_weight_coverage",
        "Theory-weight coverage;Category;Fraction",
        2,
        0.5,
        2.5,
    )
    h_coverage.Sumw2()
    h_coverage.SetDirectory(0)
    h_coverage.GetXaxis().SetBinLabel(1, "tgenBefore with weight")
    h_coverage.GetXaxis().SetBinLabel(2, "tgen matched")
    frac_tgenbefore = 0.0
    if n_weight_tree > 0:
        frac_tgenbefore = min(1.0, float(len(weights)) / float(n_weight_tree))
    frac_tgen = 0.0
    if n_gen > 0:
        frac_tgen = float(n_gen_matched) / float(n_gen)
    h_coverage.SetBinContent(1, frac_tgenbefore)
    h_coverage.SetBinContent(2, frac_tgen)
    h_coverage.SetBinError(1, 0.0)
    h_coverage.SetBinError(2, 0.0)

    stats = {
        "weights_file": weights_path,
        "n_weight_tree_entries": n_weight_tree,
        "n_weights_loaded": int(len(weights)),
        "n_duplicate_weight_ids": int(n_dup_weights),
        "n_gen_entries": n_gen,
        "n_gen_matched_to_weights": int(n_gen_matched),
        "frac_gen_matched_to_weights": frac_tgen,
        "weight_min": float(np.min(weights)) if len(weights) > 0 else 0.0,
        "weight_max": float(np.max(weights)) if len(weights) > 0 else 0.0,
        "weight_mean": float(np.mean(weights)) if len(weights) > 0 else 0.0,
        "weight_std": float(np.std(weights)) if len(weights) > 0 else 0.0,
    }

    return weight_lookup, gen_lookup, stats, h_weight_input, h_weight_gen, h_coverage


def make_hadronic_event_sel_correction(
    tree_gen,
    tree_gen_before,
    gen_branch,
    bins,
    xmin,
    xmax,
    axis_label,
    id_branch,
    gen_weight_lookup=None,
    genbefore_weight_lookup=None,
):
    """
    Build correction = (tgenBefore spectrum) / (tgen spectrum used in response),
    then apply it bin-by-bin after unfolding.
    """
    h_gen_all = make_h1("mc_gen_all", f"MC gen (all);{axis_label};Events", bins, xmin, xmax)
    h_gen_before = make_h1("mc_genBefore", f"MC genBefore;{axis_label};Events", bins, xmin, xmax)
    fill_hist_from_tree(
        tree_gen,
        gen_branch,
        h_gen_all,
        xmin,
        xmax,
        selection_branch=None,
        id_branch=id_branch,
        weight_lookup=gen_weight_lookup,
        default_weight=1.0,
    )
    fill_hist_from_tree(
        tree_gen_before,
        gen_branch,
        h_gen_before,
        xmin,
        xmax,
        selection_branch=None,
        id_branch=id_branch,
        weight_lookup=genbefore_weight_lookup,
        default_weight=1.0,
    )

    h_corr = make_h1(
        "hadronic_event_sel_corr",
        f"Hadronic event selection correction;{axis_label};tgenBefore/tgen",
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
    observable_name, observable = get_observable_preset(
        get_cfg(cfg, "observable", default="thrust")
    )
    axis_label = observable["axis_label"]

    data_file = get_cfg(cfg, "data_file", required=True)
    reco_mc_file = get_cfg(cfg, "reco_mc_file", required=True)
    gen_mc_file = get_cfg(cfg, "gen_mc_file", required=True)
    genbefore_mc_file = get_cfg(cfg, "genbefore_mc_file", default=default_genbefore_file_from_gen(gen_mc_file))

    data_tree_name = get_cfg(cfg, "data_tree", default="t")
    reco_tree_name = get_cfg(cfg, "reco_tree", default="t")
    gen_tree_name = get_cfg(cfg, "gen_tree", default="tgen")
    genbefore_tree_name = get_cfg(cfg, "genbefore_tree", default="tgenBefore")

    data_branch = get_cfg(cfg, "data_branch", default=observable["branch"])
    reco_branch = get_cfg(cfg, "reco_branch", default=observable["branch"])
    gen_branch = get_cfg(cfg, "gen_branch", default=observable["branch"])
    selection_branch = get_cfg(cfg, "selection_branch", default="passEventSelection")
    id_branch = get_cfg(cfg, "id_branch", default="uniqueID")
    theory_variation_weights_path = get_cfg(cfg, "theory_variation_weights_path", default=None)
    apply_theory_event_weights = bool(
        get_cfg(
            cfg,
            "apply_theory_event_weights",
            default=bool(theory_variation_weights_path),
        )
    )
    theory_weight_tree_name = get_cfg(cfg, "theory_weight_tree", default=genbefore_tree_name)
    theory_weight_id_branch = get_cfg(cfg, "theory_weight_id_branch", default=id_branch)
    strict_theory_weight_length = bool(get_cfg(cfg, "strict_theory_weight_length", default=True))
    normalize_weights_mean1 = bool(get_cfg(cfg, "normalize_weights_mean1", default=True))
    weight_clipping_max = get_cfg(cfg, "weight_clipping_max", default=None)

    bins = int(get_cfg(cfg, "bins", default=observable["bins"]))
    xmin = float(get_cfg(cfg, "xmin", default=observable["xmin"]))
    xmax = float(get_cfg(cfg, "xmax", default=observable["xmax"]))
    iterations = int(get_cfg(cfg, "iterations", default=6))
    calculate_covariance = bool(get_cfg(cfg, "calculate_covariance", default=False))
    mode = str(get_cfg(cfg, "mode", default="nominal")).strip().lower()
    if mode not in {"nominal", "closure"}:
        raise ValueError(f"Invalid mode '{mode}'. Supported modes: nominal, closure")
    closure_check = bool(get_cfg(cfg, "closure_check", default=False)) or mode == "closure"
    apply_hadronic_event_correction = bool(
        get_cfg(cfg, "apply_hadronic_event_correction", default=True)
    )

    out_root = get_cfg(cfg, "out_root", default=f"unfolded_{observable_name}.root")
    if closure_check:
        if out_root.endswith("_closure.root"):
            pass
        elif out_root.endswith(".root"):
            out_root = out_root.replace(".root", "_closure.root")
        else:
            out_root = out_root + "_closure"

    required_files = [reco_mc_file, gen_mc_file, genbefore_mc_file]
    if not closure_check:
        required_files.insert(0, data_file)
    for path in required_files:
        require_file(path)

    f_data = None
    if not closure_check:
        f_data = ROOT.TFile.Open(data_file, "READ")
    f_reco = ROOT.TFile.Open(reco_mc_file, "READ")
    f_gen = ROOT.TFile.Open(gen_mc_file, "READ")
    f_genbefore = ROOT.TFile.Open(genbefore_mc_file, "READ")
    if not closure_check and (not f_data or f_data.IsZombie()):
        raise RuntimeError(f"Failed to open data file: {data_file}")
    if not f_reco or f_reco.IsZombie():
        raise RuntimeError(f"Failed to open reco MC file: {reco_mc_file}")
    if not f_gen or f_gen.IsZombie():
        raise RuntimeError(f"Failed to open gen MC file: {gen_mc_file}")
    if not f_genbefore or f_genbefore.IsZombie():
        raise RuntimeError(f"Failed to open genBefore MC file: {genbefore_mc_file}")

    tree_data = get_tree(f_data, data_tree_name, data_file) if not closure_check else None
    tree_reco = get_tree(f_reco, reco_tree_name, reco_mc_file)
    tree_gen = get_tree(f_gen, gen_tree_name, gen_mc_file)
    tree_genbefore = get_tree(f_genbefore, genbefore_tree_name, genbefore_mc_file)
    tree_theory_weights = get_tree(f_genbefore, theory_weight_tree_name, genbefore_mc_file)

    branch_checks = [
        (tree_reco, reco_tree_name, reco_branch),
        (tree_gen, gen_tree_name, gen_branch),
        (tree_reco, reco_tree_name, id_branch),
        (tree_gen, gen_tree_name, id_branch),
        (tree_genbefore, genbefore_tree_name, gen_branch),
        (tree_theory_weights, theory_weight_tree_name, theory_weight_id_branch),
    ]
    if selection_branch:
        branch_checks.append((tree_reco, reco_tree_name, selection_branch))
    if not closure_check:
        branch_checks.append((tree_data, data_tree_name, data_branch))
        if selection_branch:
            branch_checks.append((tree_data, data_tree_name, selection_branch))

    for tree, tname, bname in branch_checks:
        if not branch_exists(tree, bname):
            raise KeyError(f"Branch '{bname}' not found in tree '{tname}'")

    theory_weight_lookup_genbefore = None
    theory_weight_lookup_gen = None
    theory_weight_stats = None
    h_theory_weights_input = None
    h_theory_weights_gen = None
    h_theory_weight_coverage = None
    if apply_theory_event_weights:
        if not theory_variation_weights_path:
            raise ValueError(
                "apply_theory_event_weights=true but no theory_variation_weights_path provided"
            )
        if not os.path.isabs(theory_variation_weights_path):
            theory_variation_weights_path = os.path.abspath(
                os.path.join(os.path.dirname(args.config), theory_variation_weights_path)
            )
        (
            theory_weight_lookup_genbefore,
            theory_weight_lookup_gen,
            theory_weight_stats,
            h_theory_weights_input,
            h_theory_weights_gen,
            h_theory_weight_coverage,
        ) = build_theory_weight_maps(
            tree_gen=tree_gen,
            tree_weights=tree_theory_weights,
            gen_id_branch=id_branch,
            weight_id_branch=theory_weight_id_branch,
            weights_path=theory_variation_weights_path,
            strict_length=strict_theory_weight_length,
            weight_clipping_max=weight_clipping_max,
            normalize_weights_mean1=normalize_weights_mean1,
        )

    h_data = make_h1("data_reco", f"Data (reco);{axis_label};Events", bins, xmin, xmax)
    if closure_check:
        h_data.SetTitle(f"Closure input (MC reco);{axis_label};Events")
        fill_hist_from_tree(
            tree_reco, reco_branch, h_data, xmin, xmax, selection_branch=selection_branch
        )
    else:
        fill_hist_from_tree(
            tree_data, data_branch, h_data, xmin, xmax, selection_branch=selection_branch
        )

    response, h_reco, h_gen, h_resp_counts, n_match, matched_weight_sum = build_response(
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
        RooUnfoldResponse=RooUnfoldResponse,
        gen_weight_lookup=theory_weight_lookup_gen,
        gen_default_weight=1.0,
    )

    unfold = RooUnfoldBayes(response, h_data, iterations)
    if hasattr(unfold, "SetVerbose"):
        unfold.SetVerbose(0)
    if calculate_covariance:
        measured_cov = make_measured_cov_from_hist(h_data, bins)
        unfold.SetMeasuredCov(measured_cov)
    h_unfolded = unfold.Hunfold(RooUnfold.kNoError)
    h_unfolded = h_unfolded.Clone("unfolded")
    h_unfolded.SetTitle(f"Unfolded ({iterations} iters);{axis_label};Events")

    h_gen_all, h_genbefore, h_hadsel_corr = make_hadronic_event_sel_correction(
        tree_gen=tree_gen,
        tree_gen_before=tree_genbefore,
        gen_branch=gen_branch,
        bins=bins,
        xmin=xmin,
        xmax=xmax,
        axis_label=axis_label,
        id_branch=id_branch,
        gen_weight_lookup=theory_weight_lookup_gen,
        genbefore_weight_lookup=theory_weight_lookup_genbefore,
    )
    h_unfolded_corrected = h_unfolded.Clone("unfolded_corrected")
    h_unfolded_corrected.SetTitle(f"Unfolded corrected ({iterations} iters);{axis_label};Events")
    if apply_hadronic_event_correction:
        # Use ROOT's bin-by-bin multiplication with propagated uncertainties.
        h_unfolded_corrected.Multiply(h_hadsel_corr)

    h_eff = hist_efficiency(response, bins, xmin, xmax, axis_label=axis_label)
    h_mresp = matrix_to_th2(
        "response_prob_reco_given_gen",
        f"Response P(reco|gen);Reco {axis_label};Gen {axis_label}",
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
    if h_theory_weights_input:
        out_objects.append(h_theory_weights_input)
    if h_theory_weights_gen:
        out_objects.append(h_theory_weights_gen)
    if h_theory_weight_coverage:
        out_objects.append(h_theory_weight_coverage)

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
        h_corr = covariance_to_correlation_th2(
            "unfold_correlation",
            "Unfolded correlation;Truth bin;Truth bin",
            cov,
            bins,
            xmin,
            xmax,
        )
        out_objects.append(h_cov)
        out_objects.append(h_corr)

    fout = ROOT.TFile(out_root, "RECREATE")
    for obj in out_objects:
        obj.Write()
    fout.Close()

    if f_data:
        f_data.Close()
    f_reco.Close()
    f_gen.Close()
    f_genbefore.Close()

    print("Unfolding complete (RooUnfold)")
    print(f"  observable: {observable_name} ({axis_label})")
    print(f"  closure check mode: {closure_check}")
    print(f"  data events in range: {int(integral_in_range(h_data))}")
    print(f"  mc reco events in range: {int(integral_in_range(h_reco))}")
    print(f"  mc gen events in range: {int(integral_in_range(h_gen))}")
    print(f"  mc genBefore events in range: {int(integral_in_range(h_genbefore))}")
    print(f"  matched reco<->gen events: {int(n_match)}")
    if apply_theory_event_weights:
        print("  theory event weights: enabled")
        print(f"  theory weights file: {theory_variation_weights_path}")
        print(f"  weighted matched sum: {matched_weight_sum:.3f}")
        print(
            "  theory weight coverage: "
            f"{theory_weight_stats['n_gen_matched_to_weights']}/"
            f"{theory_weight_stats['n_gen_entries']} "
            f"({100.0*theory_weight_stats['frac_gen_matched_to_weights']:.2f}%)"
        )
        print(
            "  theory weight stats: "
            f"mean={theory_weight_stats['weight_mean']:.4f}, "
            f"std={theory_weight_stats['weight_std']:.4f}, "
            f"min={theory_weight_stats['weight_min']:.4g}, "
            f"max={theory_weight_stats['weight_max']:.4g}"
        )
    else:
        print("  theory event weights: disabled")
    if apply_hadronic_event_correction:
        print("  applied correction: hadronic_event_sel_corr = tgenBefore/tgen (bin-by-bin)")
    else:
        print("  applied correction: disabled (apply_hadronic_event_correction=false)")
    print(f"  output ROOT: {out_root}")


if __name__ == "__main__":
    try:
        ROOT.TH1.SetDefaultSumw2(True)
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
