#!/usr/bin/env python3
"""Build thrust preliminary uncertainty breakdown, covariance exports, and summary plots."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, List
from array import array

import numpy as np
import ROOT


TRACK_EVENT_VARS = ["ntpc7", "pt04", "ech10", "with_met"]
NEUTRAL_VARS = ["nes_up", "nes_down", "ner"]
THEORY_VARS = ["pythia8", "herwig", "sherpa"]


def add_plotting_path():
    here = os.path.abspath(os.path.dirname(__file__))
    plotting_dir = os.path.abspath(os.path.join(here, "..", "..", "DataProcessing", "plotting"))
    if plotting_dir not in sys.path:
        sys.path.insert(0, plotting_dir)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-dir", required=True, help="Workflow output directory")
    p.add_argument("--nominal-iter", type=int, default=5)
    p.add_argument("--iter-down", type=int, default=4)
    p.add_argument("--iter-up", type=int, default=6)
    p.add_argument("--hist-name", default="unfolded_corrected")
    p.add_argument("--outdir", default=None)
    p.add_argument(
        "--aleph-csv",
        default=None,
        help=(
            "Path to ALEPH 2004 thrust HEPData table CSV. "
            "If omitted, only repository-local default is tried "
            "(ALEPH/HEPData-ins636645-v1-Table_54.csv)."
        ),
    )
    p.add_argument(
        "--central-range-min",
        type=float,
        default=0.60,
        help="Lower thrust edge for central-range reporting metrics",
    )
    p.add_argument(
        "--central-range-max",
        type=float,
        default=0.95,
        help="Upper thrust edge for central-range reporting metrics",
    )
    p.add_argument(
        "--systematic-cov-model",
        choices=["diagonal", "block", "template_correlated"],
        default="template_correlated",
        help=(
            "Model for non-statistical covariance components "
            "(iteration/experimental/theory/hadronic)."
        ),
    )
    p.add_argument(
        "--block-correlation-rho",
        type=float,
        default=0.50,
        help="Off-diagonal correlation used when --systematic-cov-model=block",
    )
    p.add_argument(
        "--fit-mask-mode",
        choices=["nonzero", "central", "nonzero_and_central"],
        default="nonzero",
        help="Rule to define fit-window mask for theory-facing covariance products.",
    )
    p.add_argument(
        "--include-of-ibu-comparison",
        action="store_true",
        help=(
            "Generate optional comparison figure overlaying current result with "
            "OmniFold and IBU results from unfold-ee-logtau/Results."
        ),
    )
    p.add_argument(
        "--legacy-results-dir",
        default=None,
        help=(
            "Path to unfold-ee-logtau/Results directory. "
            "If omitted, auto-detect sibling ../unfold-ee-logtau/Results."
        ),
    )
    p.add_argument(
        "--legacy-ibu-npz",
        default=None,
        help="Override path to legacy IBU results NPZ (default: <legacy-results-dir>/ibu_results.npz).",
    )
    p.add_argument(
        "--legacy-of-h5",
        default=None,
        help=(
            "Override path to legacy OmniFold H5 file "
            "(default: <legacy-results-dir>/unfold_thrust_ee_ZPole_ALEPH.h5)."
        ),
    )
    p.add_argument(
        "--comparison-output",
        default="final_result_of_ibu_comparison.pdf",
        help="Output filename/path for optional OF+IBU comparison figure.",
    )
    p.add_argument(
        "--comparison-ratio-ymax",
        type=float,
        default=1.55,
        help="Upper y-limit for optional comparison ratio panel.",
    )
    return p.parse_args()


def ensure_exists(path: str, label: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label}: {path}")


def load_hist(path: str, hist_name: str):
    tf = ROOT.TFile.Open(path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open ROOT file: {path}")
    obj = tf.Get(hist_name)
    if not obj:
        tf.Close()
        raise KeyError(f"Missing histogram '{hist_name}' in {path}")
    h = obj.Clone(f"{os.path.basename(path).replace('.root', '')}_{hist_name}")
    h.SetDirectory(0)
    tf.Close()
    return h


def _safe_cmd_output(cmd: List[str], cwd: str) -> str:
    try:
        return subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"


def _git_dirty_state(repo_root: str):
    try:
        rc = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD", "--"],
            cwd=repo_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        if rc == 0:
            return False
        if rc == 1:
            return True
    except Exception:
        pass
    return "unknown"


def collect_provenance(repo_root: str) -> dict:
    root_version = "unavailable"
    roounfold_version = "unavailable"
    roounfold_library = "unavailable"
    try:
        root_version = str(ROOT.gROOT.GetVersion())
        cls = ROOT.gROOT.GetClass("RooUnfoldBayes")
        if cls:
            roounfold_version = f"class_version:{int(cls.GetClassVersion())}"
        lib = ROOT.gSystem.DynamicPathName("libRooUnfold", True)
        if lib:
            roounfold_library = str(lib)
    except Exception:
        pass

    env_state = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "conda_prefix": os.environ.get("CONDA_PREFIX", ""),
        "root_version": root_version,
        "roounfold_version": roounfold_version,
        "roounfold_library": roounfold_library,
        "git_commit": _safe_cmd_output(["git", "rev-parse", "HEAD"], repo_root),
        "git_dirty": _git_dirty_state(repo_root),
    }
    env_fingerprint = hashlib.sha256(
        json.dumps(env_state, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **env_state,
        "env_fingerprint": env_fingerprint,
    }


def load_hist2d(path: str, hist_name: str):
    tf = ROOT.TFile.Open(path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open ROOT file: {path}")
    obj = tf.Get(hist_name)
    if not obj:
        tf.Close()
        raise KeyError(f"Missing histogram '{hist_name}' in {path}")
    h = obj.Clone(f"{os.path.basename(path).replace('.root', '')}_{hist_name}")
    h.SetDirectory(0)
    tf.Close()
    return h


def resolve_aleph_csv(path_hint: str | None) -> str:
    candidates = []
    cwd = os.getcwd()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    repo_local_default = os.path.abspath(
        os.path.join(repo_root, "ALEPH", "HEPData-ins636645-v1-Table_54.csv")
    )

    if path_hint:
        if os.path.isabs(path_hint):
            candidates.append(path_hint)
        else:
            candidates.append(os.path.abspath(os.path.join(cwd, path_hint)))
            candidates.append(os.path.abspath(os.path.join(repo_root, path_hint)))
    else:
        candidates.append(repo_local_default)

    for cand in candidates:
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(
        "ALEPH CSV not found. "
        f"Tried: {', '.join(candidates)}. "
        "Provide an explicit path with --aleph-csv <path/to/HEPData-ins636645-v1-Table_54.csv>."
    )


def load_aleph_2004_result(hep_data_csv: str) -> dict:
    # Ported from unfold-ee-logtau Plotting/Utils.py::loadALEPH2004Result,
    # retaining thrust-space values used for direct comparison.
    vals = []
    with open(hep_data_csv, "r", encoding="utf-8") as f:
        for row in f:
            row = row.strip()
            if not row or row.startswith("#"):
                continue
            if row.startswith("THRUST"):
                continue
            vals.append(row.split(","))

    hepdata = np.asarray(vals, dtype=float)
    centers = hepdata[:, 0]
    lows = hepdata[:, 1]
    highs = hepdata[:, 2]
    values = hepdata[:, 3]
    stat = np.abs(hepdata[:, 4])
    sys1 = np.abs(hepdata[:, 6])
    sys2 = np.abs(hepdata[:, 8])
    total = np.sqrt(stat**2 + sys1**2 + sys2**2)

    edges = np.concatenate([lows[:1], highs])
    return {
        "centers": centers,
        "lows": lows,
        "highs": highs,
        "edges": edges,
        "values": values,
        "stat": stat,
        "sys1": sys1,
        "sys2": sys2,
        "total": total,
    }


def resolve_legacy_results_dir(path_hint: str | None, repo_root: str) -> str:
    candidates = []
    cwd = os.getcwd()
    if path_hint:
        if os.path.isabs(path_hint):
            candidates.append(path_hint)
        else:
            candidates.append(os.path.abspath(os.path.join(cwd, path_hint)))
            candidates.append(os.path.abspath(os.path.join(repo_root, path_hint)))
    else:
        candidates.append(os.path.abspath(os.path.join(repo_root, "..", "unfold-ee-logtau", "Results")))
    for cand in candidates:
        if os.path.isdir(cand):
            return cand
    raise FileNotFoundError(
        "Legacy results directory not found. "
        f"Tried: {', '.join(candidates)}. "
        "Provide --legacy-results-dir <path/to/unfold-ee-logtau/Results>."
    )


def resolve_legacy_input_paths(args, repo_root: str) -> dict[str, str]:
    legacy_dir = resolve_legacy_results_dir(args.legacy_results_dir, repo_root)
    cwd = os.getcwd()

    def resolve_optional(path_hint: str | None, default_name: str) -> str:
        if path_hint:
            if os.path.isabs(path_hint):
                return path_hint
            return os.path.abspath(os.path.join(cwd, path_hint))
        return os.path.join(legacy_dir, default_name)

    ibu_npz = resolve_optional(args.legacy_ibu_npz, "ibu_results.npz")
    of_h5 = resolve_optional(args.legacy_of_h5, "unfold_thrust_ee_ZPole_ALEPH.h5")
    ensure_exists(ibu_npz, "legacy IBU NPZ")
    ensure_exists(of_h5, "legacy OmniFold H5")
    return {
        "legacy_results_dir": legacy_dir,
        "legacy_ibu_npz": ibu_npz,
        "legacy_of_h5": of_h5,
    }


def _calc_hist_with_weight_unc(vals: np.ndarray, bins: np.ndarray, weights: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vals = np.asarray(vals, dtype=np.float64)
    bins = np.asarray(bins, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64).reshape(-1)
    if vals.shape[0] != weights.shape[0]:
        raise ValueError(
            f"histogram values/weights length mismatch: {vals.shape[0]} vs {weights.shape[0]}"
        )
    hist, _ = np.histogram(vals, bins=bins, weights=weights)
    digits = np.digitize(vals, bins)
    errs = np.asarray(
        [np.linalg.norm(weights[digits == i]) for i in range(1, len(bins))],
        dtype=np.float64,
    )
    return hist.astype(np.float64), errs


def _mc_bin_quality(
    *,
    data_counts: np.ndarray,
    data_err: np.ndarray,
    mc_counts: np.ndarray,
    mc_err: np.ndarray,
    rel_mc_unc_max: float = 0.20,
    pull_abs_max: float = 3.0,
) -> np.ndarray:
    data_counts = np.asarray(data_counts, dtype=np.float64)
    data_err = np.asarray(data_err, dtype=np.float64)
    mc_counts = np.asarray(mc_counts, dtype=np.float64)
    mc_err = np.asarray(mc_err, dtype=np.float64)

    sigma = np.sqrt(data_err**2 + mc_err**2)
    rel_mc_unc = np.divide(mc_err, mc_counts, out=np.zeros_like(mc_err), where=mc_counts > 0.0)
    pull = np.divide(
        mc_counts - data_counts,
        sigma,
        out=np.zeros_like(mc_err),
        where=sigma > 0.0,
    )
    good_rel_unc = rel_mc_unc <= rel_mc_unc_max
    good_pull = np.abs(pull) <= pull_abs_max
    return good_rel_unc & good_pull


def load_legacy_ibu_thrust_arrays(legacy_ibu_npz_path: str, n_bins_expected: int) -> dict:
    with np.load(legacy_ibu_npz_path, allow_pickle=True) as f:
        nominal_tau = np.asarray(f["nominal"], dtype=np.float64)
        total_unc_tau = np.asarray(f["total_uncert"], dtype=np.float64)
    if nominal_tau.shape[0] != n_bins_expected or total_unc_tau.shape[0] != n_bins_expected:
        raise ValueError(
            "legacy IBU arrays do not match ALEPH bin count "
            f"({nominal_tau.shape[0]}, {total_unc_tau.shape[0]}) vs {n_bins_expected}"
        )
    return {
        "values_thrust": nominal_tau[::-1].copy(),
        "errors_thrust": total_unc_tau[::-1].copy(),
    }


def build_legacy_omnifold_thrust_arrays(legacy_of_h5_path: str, thrust_edges: np.ndarray) -> dict:
    import h5py

    with h5py.File(legacy_of_h5_path, "r") as f:
        data = {key: f[key][()] for key in f.keys()}

    tau_edges = 1.0 - np.asarray(thrust_edges, dtype=np.float64)[::-1]
    tau_gen = np.exp(np.asarray(data["archived_pythia61_gen"], dtype=np.float64))
    ensemble_weights = np.squeeze(np.asarray(data["ensemble_weights"], dtype=np.float64), axis=0)
    systematic_weights = np.asarray(data["systematic_weights"], dtype=np.float64)
    theory_weights = np.asarray(data["theory_weights"], dtype=np.float64)
    bootstrap_data_weights = np.squeeze(
        np.asarray(data["bootstrap_weights_data"], dtype=np.float64),
        axis=0,
    )
    bootstrap_mc_weights = np.squeeze(
        np.asarray(data["bootstrap_weights_mc"], dtype=np.float64),
        axis=0,
    )
    systematic_names = [
        x.decode("utf-8") if isinstance(x, (bytes, bytearray)) else str(x)
        for x in data["systematic_weights_order"]
    ]

    nominal_counts, nominal_stat = _calc_hist_with_weight_unc(
        tau_gen,
        tau_edges,
        ensemble_weights[0].reshape(-1),
    )

    ensemble_samples = []
    for i in range(1, ensemble_weights.shape[0]):
        counts_i, _ = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            ensemble_weights[i].reshape(-1),
        )
        ensemble_samples.append(counts_i)
    total_ensemble_err = (
        np.std(np.asarray(ensemble_samples, dtype=np.float64), axis=0)
        if ensemble_samples
        else np.zeros_like(nominal_counts)
    )

    systematic_errs = []
    nes = {}
    for i, weights in enumerate(systematic_weights):
        name = systematic_names[i] if i < len(systematic_names) else f"systematic_{i}"
        counts_i, _ = _calc_hist_with_weight_unc(tau_gen, tau_edges, weights.reshape(-1))
        shift_i = nominal_counts - counts_i
        if name == "no_neutrals":
            continue
        if name in ("nes_up", "nes_down"):
            nes[name] = np.abs(shift_i)
            continue
        systematic_errs.append(shift_i)
    if "nes_up" in nes and "nes_down" in nes:
        systematic_errs.append(np.maximum(nes["nes_up"], nes["nes_down"]))
    elif "nes_up" in nes:
        systematic_errs.append(nes["nes_up"])
    elif "nes_down" in nes:
        systematic_errs.append(nes["nes_down"])
    total_exp_systematic_err = (
        np.sqrt(np.sum(np.square(np.stack(systematic_errs, axis=1)), axis=1))
        if systematic_errs
        else np.zeros_like(nominal_counts)
    )

    theory_errs = []
    theory_masks = []
    for i in range(theory_weights.shape[0]):
        counts_i, errs_i = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            theory_weights[i].reshape(-1),
        )
        shift_i = nominal_counts - counts_i
        mask_i = _mc_bin_quality(
            data_counts=nominal_counts,
            data_err=nominal_stat,
            mc_counts=counts_i,
            mc_err=errs_i,
            rel_mc_unc_max=20.0,
            pull_abs_max=1.995,
        )
        theory_errs.append(shift_i)
        theory_masks.append(mask_i)
    if theory_errs:
        theory_err_arr = np.stack(theory_errs, axis=1)
        theory_mask_arr = np.stack(theory_masks, axis=1)
        abs_theory = np.abs(theory_err_arr)
        masked = np.where(theory_mask_arr, abs_theory, np.nan)
        has_valid = np.any(theory_mask_arr, axis=1)
        total_theory_err = np.zeros(abs_theory.shape[0], dtype=np.float64)
        if np.any(has_valid):
            total_theory_err[has_valid] = np.nanmax(masked[has_valid], axis=1)
        if np.any(~has_valid):
            total_theory_err[~has_valid] = np.nanmin(abs_theory[~has_valid], axis=1)
    else:
        total_theory_err = np.zeros_like(nominal_counts)

    boot_data_samples = []
    for i in range(bootstrap_data_weights.shape[0]):
        counts_i, _ = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            bootstrap_data_weights[i].reshape(-1),
        )
        boot_data_samples.append(counts_i)
    bootstrap_data_err = (
        np.std(np.asarray(boot_data_samples, dtype=np.float64), axis=0)
        if boot_data_samples
        else np.zeros_like(nominal_counts)
    )

    boot_mc_samples = []
    for i in range(bootstrap_mc_weights.shape[0]):
        counts_i, _ = _calc_hist_with_weight_unc(
            tau_gen,
            tau_edges,
            bootstrap_mc_weights[i].reshape(-1),
        )
        boot_mc_samples.append(counts_i)
    bootstrap_mc_err = (
        np.std(np.asarray(boot_mc_samples, dtype=np.float64), axis=0)
        if boot_mc_samples
        else np.zeros_like(nominal_counts)
    )

    total_err_tau = np.sqrt(
        nominal_stat**2
        + total_ensemble_err**2
        + bootstrap_data_err**2
        + bootstrap_mc_err**2
        + total_exp_systematic_err**2
        + total_theory_err**2
    )
    bin_widths_tau = tau_edges[1:] - tau_edges[:-1]
    norm = np.sum(ensemble_weights[0]) * bin_widths_tau
    nominal_tau = np.divide(
        nominal_counts,
        norm,
        out=np.zeros_like(nominal_counts),
        where=norm > 0.0,
    )
    total_err_tau = np.divide(
        total_err_tau,
        norm,
        out=np.zeros_like(total_err_tau),
        where=norm > 0.0,
    )
    return {
        "values_thrust": nominal_tau[::-1].copy(),
        "errors_thrust": total_err_tau[::-1].copy(),
    }


def _chi2_ndf(y1: np.ndarray, yerr1: np.ndarray, y2: np.ndarray, yerr2: np.ndarray) -> dict:
    sigma2 = np.asarray(yerr1, dtype=np.float64) ** 2 + np.asarray(yerr2, dtype=np.float64) ** 2
    valid = sigma2 > 0.0
    ndf = int(np.count_nonzero(valid))
    if ndf == 0:
        return {"chi2": 0.0, "ndf": 0, "chi2_per_ndf": 0.0}
    dy = np.asarray(y1, dtype=np.float64) - np.asarray(y2, dtype=np.float64)
    chi2 = float(np.sum((dy[valid] ** 2) / sigma2[valid]))
    return {"chi2": chi2, "ndf": ndf, "chi2_per_ndf": (chi2 / ndf)}


def make_hist_from_binned_values(name: str, edges: np.ndarray, values: np.ndarray, errors: np.ndarray):
    h = ROOT.TH1D(name, name, len(values), array("d", [float(x) for x in edges]))
    h.Sumw2()
    h.SetDirectory(0)
    for i in range(1, len(values) + 1):
        h.SetBinContent(i, float(values[i - 1]))
        h.SetBinError(i, float(errors[i - 1]))
    return h


def load_raw_covariance(path: str) -> np.ndarray | None:
    tf = ROOT.TFile.Open(path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open ROOT file: {path}")
    cov_obj = tf.Get("unfold_covariance")
    cov = None
    if cov_obj:
        cov = cov_obj.Clone("unfold_covariance_detached")
        cov.SetDirectory(0)
    tf.Close()
    if not cov:
        return None
    n = min(cov.GetNbinsX(), cov.GetNbinsY())
    out = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            out[i, j] = float(cov.GetBinContent(i + 1, j + 1))
    return out


def hist_bin_widths(hist) -> np.ndarray:
    return np.asarray(
        [float(hist.GetXaxis().GetBinUpEdge(i) - hist.GetXaxis().GetBinLowEdge(i)) for i in range(1, hist.GetNbinsX() + 1)],
        dtype=np.float64,
    )


def to_diff_xsec(hist):
    out = hist.Clone(hist.GetName() + "_diff")
    out.SetDirectory(0)
    integral = out.Integral(1, out.GetNbinsX())
    if integral > 0.0:
        out.Scale(1.0 / integral, "width")
    return out


def hist_to_array(hist) -> np.ndarray:
    return np.asarray(
        [float(hist.GetBinContent(i)) for i in range(1, hist.GetNbinsX() + 1)],
        dtype=np.float64,
    )


def frac_shift(var: np.ndarray, nom: np.ndarray) -> np.ndarray:
    out = np.zeros_like(nom)
    mask = nom != 0.0
    out[mask] = (var[mask] - nom[mask]) / nom[mask]
    return out


def abs_env(arrays: List[np.ndarray]) -> np.ndarray:
    if not arrays:
        raise ValueError("abs_env requires at least one array")
    stack = np.vstack([np.abs(a) for a in arrays])
    return np.max(stack, axis=0)


def quad_sum(arrays: List[np.ndarray]) -> np.ndarray:
    if not arrays:
        raise ValueError("quad_sum requires at least one array")
    out = np.zeros_like(arrays[0])
    for arr in arrays:
        out = out + np.square(arr)
    return np.sqrt(out)


def arr_to_hist(template, name: str, title: str, arr: np.ndarray, y_title: str):
    h = template.Clone(name)
    h.SetDirectory(0)
    h.Reset("ICESM")
    h.SetTitle(title)
    h.GetYaxis().SetTitle(y_title)
    for i, v in enumerate(arr, start=1):
        h.SetBinContent(i, float(v))
        h.SetBinError(i, 0.0)
    return h


def fractional_uncertainty(abs_err: np.ndarray, counts: np.ndarray, eps: float = 1e-15) -> np.ndarray:
    denom = np.maximum(np.abs(counts), eps)
    return np.divide(np.abs(abs_err), denom)


def summarize_fractional(arr: np.ndarray, mask: np.ndarray | None = None) -> dict:
    vals = np.abs(arr)
    if mask is not None:
        vals = vals[mask]
    if vals.size == 0:
        return {"mean": 0.0, "max": 0.0}
    return {"mean": float(np.mean(vals)), "max": float(np.max(vals))}


def corr_from_cov(cov: np.ndarray) -> np.ndarray:
    n = cov.shape[0]
    corr = np.zeros_like(cov)
    diag = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    for i in range(n):
        for j in range(n):
            denom = diag[i] * diag[j]
            corr[i, j] = cov[i, j] / denom if denom > 0 else 0.0
    return corr


def component_covariance_from_model(
    abs_err: np.ndarray,
    model: str,
    *,
    corr_template: np.ndarray,
    block_rho: float,
) -> np.ndarray:
    vals = np.asarray(abs_err, dtype=np.float64)
    if np.any(vals < 0.0):
        raise ValueError("component_covariance_from_model expects non-negative abs_err")
    n = vals.shape[0]
    if model == "diagonal":
        return np.diag(np.square(vals))
    if model == "block":
        rho = max(-0.99, min(0.99, float(block_rho)))
        corr = np.full((n, n), rho, dtype=np.float64)
        np.fill_diagonal(corr, 1.0)
        return np.outer(vals, vals) * corr
    if model == "template_correlated":
        if corr_template.shape != (n, n):
            raise ValueError(
                f"template correlation shape {corr_template.shape} does not match {(n, n)}"
            )
        corr = np.clip(np.asarray(corr_template, dtype=np.float64), -1.0, 1.0)
        cov = np.outer(vals, vals) * corr
        cov = 0.5 * (cov + cov.T)
        np.fill_diagonal(cov, np.square(vals))
        return cov
    raise ValueError(f"Unsupported covariance model: {model}")


def build_fit_mask(
    mode: str,
    *,
    nom: np.ndarray,
    cov_total: np.ndarray,
    centers: np.ndarray,
    central_min: float,
    central_max: float,
) -> np.ndarray:
    nonzero = (np.abs(nom) > 0.0) & (np.diag(cov_total) > 0.0)
    central = (centers >= central_min) & (centers < central_max)
    if mode == "nonzero":
        return nonzero
    if mode == "central":
        return central
    if mode == "nonzero_and_central":
        return nonzero & central
    raise ValueError(f"Unsupported fit mask mode: {mode}")


def extract_theory_weight_diagnostics(theory_root_path: str) -> dict:
    tf = ROOT.TFile.Open(theory_root_path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open theory ROOT file: {theory_root_path}")

    out = {
        "available": False,
        "coverage_tgenBefore": None,
        "coverage_tgen": None,
        "weights_input_entries": 0,
        "weights_input_mean": None,
        "weights_input_std": None,
        "weights_mapped_entries": 0,
        "weights_mapped_mean": None,
        "weights_mapped_std": None,
    }

    h_cov = tf.Get("theory_weight_coverage")
    h_in = tf.Get("theory_weights_tgenBefore")
    h_map = tf.Get("theory_weights_tgen_mapped")
    if h_cov and h_in and h_map:
        out["available"] = True
        out["coverage_tgenBefore"] = float(h_cov.GetBinContent(1))
        out["coverage_tgen"] = float(h_cov.GetBinContent(2))
        out["weights_input_entries"] = int(h_in.GetEntries())
        out["weights_input_mean"] = float(h_in.GetMean())
        out["weights_input_std"] = float(h_in.GetStdDev())
        out["weights_mapped_entries"] = int(h_map.GetEntries())
        out["weights_mapped_mean"] = float(h_map.GetMean())
        out["weights_mapped_std"] = float(h_map.GetStdDev())

    tf.Close()
    return out


def compute_hadronic_correction_fractional_shift(
    nominal_root: str,
    nominal_counts,
    nominal_diffxsec: np.ndarray,
) -> np.ndarray:
    h_gen_all = load_hist(nominal_root, "mc_gen_all")
    h_gen_before = load_hist(nominal_root, "mc_genBefore")
    nbins = nominal_counts.GetNbinsX()
    if h_gen_all.GetNbinsX() != nbins or h_gen_before.GetNbinsX() != nbins:
        raise ValueError(
            "hadronic correction histograms have inconsistent binning relative to nominal histogram"
        )

    h_up = nominal_counts.Clone("had_corr_up_counts")
    h_down = nominal_counts.Clone("had_corr_down_counts")
    h_up.SetDirectory(0)
    h_down.SetDirectory(0)

    for ibin in range(1, nbins + 1):
        n_before = float(h_gen_before.GetBinContent(ibin))
        n_before_err = float(h_gen_before.GetBinError(ibin))
        n_gen = float(h_gen_all.GetBinContent(ibin))
        n_gen_err = float(h_gen_all.GetBinError(ibin))
        rel = 0.0
        if n_before > 0.0 and n_gen > 0.0:
            rel = math.sqrt((n_before_err / n_before) ** 2 + (n_gen_err / n_gen) ** 2)

        c_nom = float(nominal_counts.GetBinContent(ibin))
        e_nom = float(nominal_counts.GetBinError(ibin))
        up_scale = 1.0 + rel
        down_scale = max(0.0, 1.0 - rel)
        h_up.SetBinContent(ibin, c_nom * up_scale)
        h_down.SetBinContent(ibin, c_nom * down_scale)
        h_up.SetBinError(ibin, e_nom * up_scale)
        h_down.SetBinError(ibin, e_nom * down_scale)

    arr_up = hist_to_array(to_diff_xsec(h_up))
    arr_down = hist_to_array(to_diff_xsec(h_down))
    shift_up = frac_shift(arr_up, nominal_diffxsec)
    shift_down = frac_shift(arr_down, nominal_diffxsec)
    return abs_env([shift_up, shift_down])


def write_csv(path: str, arr: np.ndarray):
    np.savetxt(path, arr, delimiter=",", fmt="%.10e")


def response_diag_fraction(response_counts_hist2d) -> float:
    nx = response_counts_hist2d.GetNbinsX()
    ny = response_counts_hist2d.GetNbinsY()
    n = min(nx, ny)
    total = 0.0
    diag = 0.0
    for ix in range(1, nx + 1):
        for iy in range(1, ny + 1):
            v = float(response_counts_hist2d.GetBinContent(ix, iy))
            total += v
            if ix == iy and ix <= n:
                diag += v
    return (diag / total) if total > 0.0 else 0.0


def make_component_group_plot(
    out_path: str,
    template_hist,
    components: Dict[str, np.ndarray],
    labels: Dict[str, str],
    colors: Dict[str, int],
    line_styles: Dict[str, int],
    *,
    y_min: float,
    y_max: float,
    legend_loc: List[float],
    legend_textsize: float,
    legend_ncols: int,
    legend_entry_sep: float = 0.018,
    legend_column_sep: float = 0.06,
    legend_margin: float = 0.16,
    signed: bool,
):
    from style import ALEPHLegend, apply_style, myText

    c = ROOT.TCanvas(f"c_{os.path.basename(out_path)}", "", 50, 50, 700, 700)
    pad = ROOT.TPad(f"pad_{os.path.basename(out_path)}", "", 0.0, 0.05, 1.0, 1.0)
    pad.SetBottomMargin(0.16)
    pad.SetTopMargin(0.08)
    pad.SetLeftMargin(0.18)
    pad.SetRightMargin(0.04)
    pad.Draw()
    pad.cd()

    keys = list(components.keys())
    frame = template_hist.Clone(f"frame_{os.path.basename(out_path)}")
    frame.Reset("ICESM")
    frame.GetXaxis().SetTitle("Thrust")
    frame.GetYaxis().SetTitle("Uncert. [%]")
    frame.SetMinimum(y_min)
    frame.SetMaximum(y_max)
    apply_style(frame, color=ROOT.kBlack, marker=20, line_style=1, is_data=True)
    frame.GetYaxis().SetTitleOffset(1.30)
    frame.GetXaxis().SetLabelSize(0.047)
    frame.GetYaxis().SetLabelSize(0.047)
    frame.GetXaxis().SetLabelOffset(0.015)
    frame.GetYaxis().SetLabelOffset(0.010)
    frame.GetYaxis().SetNoExponent(True)
    frame.GetYaxis().SetMaxDigits(3)
    frame.GetYaxis().SetNdivisions(505)
    frame.GetXaxis().SetNdivisions(505)
    frame.Draw("AXIS")

    if signed:
        zero = ROOT.TLine(frame.GetXaxis().GetXmin(), 0.0, frame.GetXaxis().GetXmax(), 0.0)
        zero.SetLineStyle(2)
        zero.SetLineColor(ROOT.kGray + 2)
        zero.Draw("SAME")

    leg = ALEPHLegend(loc=legend_loc, textsize=legend_textsize)
    leg.SetNColumns(legend_ncols)
    leg.SetEntrySeparation(legend_entry_sep)
    leg.SetColumnSeparation(legend_column_sep)
    leg.SetMargin(legend_margin)

    drawn_hists = []
    for k in keys:
        # Clip only for display to keep the y-axis readable.
        h = arr_to_hist(template_hist, f"h_{k}_{os.path.basename(out_path)}", "", components[k], "Uncert. [%]")
        for ibin in range(1, h.GetNbinsX() + 1):
            v = float(h.GetBinContent(ibin))
            h.SetBinContent(ibin, max(y_min, min(v, y_max)))
        apply_style(h, color=colors[k], marker=20, line_style=line_styles[k], is_data=True)
        h.SetLineWidth(2)
        h.SetMarkerSize(0.0)
        h.Draw("HIST SAME")
        leg.AddEntry(h, labels[k], "l")
        drawn_hists.append(h)
    leg.Draw()
    # Place ALEPH label just above the plotting content, consistent with the component-panel style.
    myText(0.18, 0.961, "ALEPH e^{+}e^{-}, #sqrt{s} = 91.2 GeV", align=13, size=0.045)

    outdir = os.path.dirname(out_path)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    c.SaveAs(out_path)
    c.Close()


def make_final_plot(
    out_path: str,
    nominal,
    aleph_csv_path: str,
    stat_abs: np.ndarray,
    exp_abs: np.ndarray,
    iter_abs: np.ndarray,
    theory_abs: np.ndarray,
    hadronic_abs: np.ndarray | None = None,
):
    from PlotConfig import plotConfig
    from style import ALEPHLegend, apply_style, myText, style_ratio

    cfg = plotConfig["thrust"]
    cfg["legloc"] = [0.24, 0.58, 0.49, 0.88]

    if hadronic_abs is None:
        hadronic_abs = np.zeros_like(stat_abs)
    total_abs = np.sqrt(stat_abs**2 + exp_abs**2 + iter_abs**2 + theory_abs**2 + hadronic_abs**2)

    def band_hist(name: str, color: int, alpha: float, abs_err: np.ndarray):
        h = nominal.Clone(name)
        h.SetDirectory(0)
        for i, e in enumerate(abs_err, start=1):
            h.SetBinError(i, float(e))
        h.SetFillColorAlpha(color, alpha)
        h.SetLineColor(color)
        h.SetMarkerSize(0.0)
        return h

    h_total = band_hist("h_total_band", ROOT.kGray + 1, 0.45, total_abs)

    h_nom = nominal.Clone("h_nominal_points")
    h_nom.SetDirectory(0)
    h_nom.SetLineColor(ROOT.kBlack)
    h_nom.SetMarkerColor(ROOT.kBlack)
    h_nom.SetMarkerStyle(20)
    h_nom.SetMarkerSize(0.8)

    max_y = max(
        float(h_nom.GetMaximum()),
        float(np.max(nominal_to_array(nominal) + total_abs)),
    )

    c = ROOT.TCanvas("c_final_result", "", 50, 50, 700, 700)
    pad1 = ROOT.TPad("pad1", "", 0.0, 0.30, 1.0, 1.0)
    pad1.SetBottomMargin(0.0)
    pad1.SetTopMargin(0.10)
    pad1.SetLeftMargin(0.20)
    pad1.SetRightMargin(0.05)
    pad1.Draw()
    pad1.cd()
    pad1.SetLogy()

    frame = h_nom.Clone("frame_final")
    frame.Reset("ICESM")
    frame.GetXaxis().SetTitle("Thrust")
    frame.GetYaxis().SetTitle(cfg.get("YTitleDifferential", "1/#sigma d#sigma/dT"))
    nom_vals = nominal_to_array(nominal)
    lower_vals = np.clip(nom_vals - total_abs, 0.0, None)
    pos = lower_vals[lower_vals > 0.0]
    if pos.size == 0:
        pos = nom_vals[nom_vals > 0.0]
    y_min = max(1e-6, float(np.min(pos)) * 0.8) if pos.size > 0 else 1e-6
    frame.SetMinimum(y_min)
    frame.SetMaximum(1.6 * max_y)
    apply_style(frame, color=ROOT.kBlack, marker=20, line_style=1, is_data=True)
    frame.GetYaxis().SetTitleOffset(1.35)
    frame.GetXaxis().SetLabelSize(0.0)
    frame.GetXaxis().SetNdivisions(505)
    frame.Draw("AXIS")

    h_total.Draw("E2 SAME")
    h_nom.Draw("E1 SAME")

    aleph = load_aleph_2004_result(aleph_csv_path)
    h_aleph = make_hist_from_binned_values(
        "h_aleph_2004",
        aleph["edges"],
        aleph["values"],
        aleph["total"],
    )
    apply_style(h_aleph, color=ROOT.kRed + 1, marker=24, line_style=1, is_data=True)
    h_aleph.SetLineWidth(2)
    h_aleph.SetMarkerSize(0.9)
    h_aleph.Draw("PE1 SAME")

    leg = ALEPHLegend(loc=cfg.get("legloc", [0.53, 0.58, 0.94, 0.92]), textsize=0.032)
    leg.AddEntry(h_nom, "Unfolded nominal (N_{iter}=5)", "pl")
    leg.AddEntry(h_total, "Total uncertainty", "f")
    leg.AddEntry(h_aleph, "ALEPH 2004", "pl")
    leg.Draw()
    myText(0.2, 0.925, "ALEPH e^{+}e^{-}, #sqrt{s} = 91.2 GeV", size=0.045)

    c.cd()
    pad2 = ROOT.TPad("pad2", "", 0.0, 0.05, 1.0, 0.30)
    pad2.SetTopMargin(0.00)
    pad2.SetBottomMargin(0.40)
    pad2.SetLeftMargin(0.20)
    pad2.SetRightMargin(0.05)
    pad2.Draw()
    pad2.cd()

    # Build ratio in ALEPH binning so ROOT propagates uncertainties from
    # both histograms with native TH1 error handling.
    h_nom_total = nominal.Clone("h_nom_total_for_ratio")
    h_nom_total.SetDirectory(0)
    for i, e in enumerate(total_abs, start=1):
        h_nom_total.SetBinError(i, float(e))

    h_nom_on_aleph = h_nom_total.Rebin(
        len(aleph["values"]),
        "h_nominal_on_aleph_bins",
        array("d", [float(x) for x in aleph["edges"]]),
    )
    h_nom_on_aleph.SetDirectory(0)

    # Requested ratio definition: ALEPH / Unfolded.
    h_ratio = h_aleph.Clone("h_ratio_aleph_over_unfolded")
    h_ratio.SetDirectory(0)
    h_ratio.Divide(h_aleph, h_nom_on_aleph)

    # Gray band around 1 using unfolded total relative uncertainty.
    h_ratio_band = h_nom_on_aleph.Clone("h_ratio_unfold_unc_band")
    h_ratio_band.SetDirectory(0)
    for ibin in range(1, h_ratio_band.GetNbinsX() + 1):
        nom_content = float(h_nom_on_aleph.GetBinContent(ibin))
        nom_error = float(h_nom_on_aleph.GetBinError(ibin))
        rel = (nom_error / nom_content) if nom_content > 0.0 else 0.0
        h_ratio_band.SetBinContent(ibin, 1.0)
        h_ratio_band.SetBinError(ibin, rel)
    h_ratio_band.SetFillColorAlpha(ROOT.kGray + 1, 0.45)
    h_ratio_band.SetLineColor(ROOT.kGray + 2)
    h_ratio_band.SetMarkerSize(0.0)

    frame2 = h_ratio.Clone("frame_ratio_final")
    frame2.Reset("ICESM")
    style_ratio(frame2, "Thrust")
    frame2.GetYaxis().SetTitle("Ratio")
    frame2.GetYaxis().SetRangeUser(0.75, 1.55)
    frame2.SetMinimum(0.75)
    frame2.SetMaximum(1.55)
    frame2.GetXaxis().SetNdivisions(505)
    frame2.Draw("AXIS")

    unity = ROOT.TLine(frame2.GetXaxis().GetXmin(), 1.0, frame2.GetXaxis().GetXmax(), 1.0)
    unity.SetLineStyle(2)
    unity.SetLineColor(ROOT.kGray + 2)
    unity.Draw("SAME")
    h_ratio_band.Draw("E2 SAME")

    apply_style(h_ratio, color=ROOT.kRed + 1, marker=24, line_style=1, is_data=True)
    style_ratio(h_ratio, "Thrust")
    h_ratio.GetYaxis().SetTitle("Ratio")
    h_ratio.GetYaxis().SetRangeUser(0.75, 1.55)
    h_ratio.GetXaxis().SetNdivisions(505)
    h_ratio.SetMarkerSize(0.85)
    h_ratio.Draw("PE1 SAME")

    ratio_vals = np.asarray(
        [float(h_ratio.GetBinContent(i)) for i in range(1, h_ratio.GetNbinsX() + 1)],
        dtype=np.float64,
    )
    ratio_errs = np.asarray(
        [float(h_ratio.GetBinError(i)) for i in range(1, h_ratio.GetNbinsX() + 1)],
        dtype=np.float64,
    )
    ratio_stats = {
        "max_central": float(np.max(ratio_vals)) if ratio_vals.size else 0.0,
        "max_plus_error": float(np.max(ratio_vals + ratio_errs)) if ratio_vals.size else 0.0,
        "highest_bin_value": float(h_ratio.GetBinContent(h_ratio.GetNbinsX())),
        "highest_bin_error": float(h_ratio.GetBinError(h_ratio.GetNbinsX())),
        "highest_bin_low_edge": float(h_ratio.GetXaxis().GetBinLowEdge(h_ratio.GetNbinsX())),
        "highest_bin_up_edge": float(h_ratio.GetXaxis().GetBinUpEdge(h_ratio.GetNbinsX())),
    }

    outdir = os.path.dirname(out_path)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    c.SaveAs(out_path)
    c.Close()
    return ratio_stats


def make_of_ibu_comparison_plot(
    *,
    out_path: str,
    metrics_json_path: str,
    nominal,
    total_abs: np.ndarray,
    aleph_csv_path: str,
    legacy_ibu_npz_path: str,
    legacy_of_h5_path: str,
    ratio_ymax: float,
) -> dict:
    from PlotConfig import plotConfig
    from style import ALEPHLegend, apply_style, myText, style_ratio

    cfg = plotConfig["thrust"]
    aleph = load_aleph_2004_result(aleph_csv_path)
    n_aleph_bins = int(len(aleph["values"]))

    h_aleph = make_hist_from_binned_values(
        "h_cmp_aleph_2004",
        aleph["edges"],
        aleph["values"],
        aleph["total"],
    )

    h_nom_total = nominal.Clone("h_cmp_nominal_total_for_ratio")
    h_nom_total.SetDirectory(0)
    for i, e in enumerate(total_abs, start=1):
        h_nom_total.SetBinError(i, float(e))
    h_current = h_nom_total.Rebin(
        n_aleph_bins,
        "h_cmp_current_on_aleph",
        array("d", [float(x) for x in aleph["edges"]]),
    )
    h_current.SetDirectory(0)

    ibu = load_legacy_ibu_thrust_arrays(legacy_ibu_npz_path, n_aleph_bins)
    h_ibu = make_hist_from_binned_values(
        "h_cmp_ibu",
        aleph["edges"],
        ibu["values_thrust"],
        ibu["errors_thrust"],
    )

    of = build_legacy_omnifold_thrust_arrays(legacy_of_h5_path, aleph["edges"])
    h_of = make_hist_from_binned_values(
        "h_cmp_of",
        aleph["edges"],
        of["values_thrust"],
        of["errors_thrust"],
    )

    h_current_band = h_current.Clone("h_cmp_current_band")
    h_current_band.SetDirectory(0)
    h_current_band.SetFillColorAlpha(ROOT.kGray + 1, 0.45)
    h_current_band.SetLineColor(ROOT.kGray + 2)
    h_current_band.SetMarkerSize(0.0)

    apply_style(h_current, color=ROOT.kBlack, marker=20, line_style=1, is_data=True)
    h_current.SetLineWidth(2)
    h_current.SetMarkerSize(0.85)
    apply_style(h_of, color=ROOT.kAzure + 2, marker=24, line_style=1, is_data=True)
    h_of.SetLineWidth(2)
    h_of.SetMarkerSize(0.90)
    apply_style(h_ibu, color=ROOT.kBlue + 1, marker=25, line_style=1, is_data=True)
    h_ibu.SetLineWidth(2)
    h_ibu.SetMarkerSize(0.90)
    apply_style(h_aleph, color=ROOT.kRed + 1, marker=26, line_style=1, is_data=True)
    h_aleph.SetLineWidth(2)
    h_aleph.SetMarkerSize(0.90)

    max_y = max(
        float(h_current.GetMaximum() + h_current.GetBinError(h_current.GetMaximumBin())),
        float(h_of.GetMaximum() + h_of.GetBinError(h_of.GetMaximumBin())),
        float(h_ibu.GetMaximum() + h_ibu.GetBinError(h_ibu.GetMaximumBin())),
        float(h_aleph.GetMaximum() + h_aleph.GetBinError(h_aleph.GetMaximumBin())),
    )
    current_vals = np.asarray(
        [float(h_current.GetBinContent(i)) for i in range(1, h_current.GetNbinsX() + 1)],
        dtype=np.float64,
    )
    current_errs = np.asarray(
        [float(h_current.GetBinError(i)) for i in range(1, h_current.GetNbinsX() + 1)],
        dtype=np.float64,
    )
    pos = np.clip(current_vals - current_errs, 0.0, None)
    pos = pos[pos > 0.0]
    y_min = max(1e-6, float(np.min(pos)) * 0.8) if pos.size > 0 else 1e-6

    c = ROOT.TCanvas("c_of_ibu_comparison", "", 50, 50, 700, 700)
    pad1 = ROOT.TPad("pad1_cmp", "", 0.0, 0.30, 1.0, 1.0)
    pad1.SetBottomMargin(0.0)
    pad1.SetTopMargin(0.10)
    pad1.SetLeftMargin(0.20)
    pad1.SetRightMargin(0.05)
    pad1.Draw()
    pad1.cd()
    pad1.SetLogy()

    frame = h_current.Clone("frame_cmp_top")
    frame.Reset("ICESM")
    frame.GetXaxis().SetTitle("Thrust")
    frame.GetYaxis().SetTitle(cfg.get("YTitleDifferential", "1/#sigma d#sigma/dT"))
    frame.SetMinimum(y_min)
    frame.SetMaximum(1.6 * max_y)
    apply_style(frame, color=ROOT.kBlack, marker=20, line_style=1, is_data=True)
    frame.GetYaxis().SetTitleOffset(1.35)
    frame.GetXaxis().SetLabelSize(0.0)
    frame.GetXaxis().SetNdivisions(505)
    frame.Draw("AXIS")

    h_current_band.Draw("E2 SAME")
    h_current.Draw("PE1 SAME")
    h_of.Draw("PE1 SAME")
    h_ibu.Draw("PE1 SAME")
    h_aleph.Draw("PE1 SAME")

    leg = ALEPHLegend(loc=[0.24, 0.56, 0.57, 0.88], textsize=0.030)
    leg.AddEntry(h_current, "Current unfolded nominal (IBU)", "pl")
    leg.AddEntry(h_current_band, "Current total uncertainty", "f")
    leg.AddEntry(h_of, "OmniFold reanalysis", "pl")
    leg.AddEntry(h_ibu, "IBU reanalysis", "pl")
    leg.AddEntry(h_aleph, "ALEPH 2004", "pl")
    leg.Draw()
    myText(0.2, 0.925, "ALEPH e^{+}e^{-}, #sqrt{s} = 91.2 GeV", size=0.045)

    c.cd()
    pad2 = ROOT.TPad("pad2_cmp", "", 0.0, 0.05, 1.0, 0.30)
    pad2.SetTopMargin(0.00)
    pad2.SetBottomMargin(0.40)
    pad2.SetLeftMargin(0.20)
    pad2.SetRightMargin(0.05)
    pad2.Draw()
    pad2.cd()

    y_max_ratio = max(float(ratio_ymax), 1.05)
    y_min_ratio = 0.75
    frame2 = h_current.Clone("frame_cmp_ratio")
    frame2.Reset("ICESM")
    style_ratio(frame2, "Thrust")
    frame2.GetYaxis().SetTitle("Ratio")
    frame2.GetYaxis().SetRangeUser(y_min_ratio, y_max_ratio)
    frame2.SetMinimum(y_min_ratio)
    frame2.SetMaximum(y_max_ratio)
    frame2.GetXaxis().SetNdivisions(505)
    frame2.Draw("AXIS")

    unity = ROOT.TLine(frame2.GetXaxis().GetXmin(), 1.0, frame2.GetXaxis().GetXmax(), 1.0)
    unity.SetLineStyle(2)
    unity.SetLineColor(ROOT.kGray + 2)
    unity.Draw("SAME")

    h_ratio_band = h_current.Clone("h_cmp_ratio_band")
    h_ratio_band.SetDirectory(0)
    for ibin in range(1, h_ratio_band.GetNbinsX() + 1):
        c_nom = float(h_current.GetBinContent(ibin))
        e_nom = float(h_current.GetBinError(ibin))
        rel = (e_nom / c_nom) if c_nom > 0.0 else 0.0
        h_ratio_band.SetBinContent(ibin, 1.0)
        h_ratio_band.SetBinError(ibin, rel)
    h_ratio_band.SetFillColorAlpha(ROOT.kGray + 1, 0.45)
    h_ratio_band.SetLineColor(ROOT.kGray + 2)
    h_ratio_band.SetMarkerSize(0.0)
    h_ratio_band.Draw("E2 SAME")

    ratio_hists = {}
    for key, hist, color, marker in [
        ("aleph_over_current", h_aleph, ROOT.kRed + 1, 26),
        ("of_over_current", h_of, ROOT.kAzure + 2, 24),
        ("ibu_over_current", h_ibu, ROOT.kBlue + 1, 25),
    ]:
        h_ratio = hist.Clone(f"h_ratio_{key}")
        h_ratio.SetDirectory(0)
        h_ratio.Divide(hist, h_current)
        apply_style(h_ratio, color=color, marker=marker, line_style=1, is_data=True)
        style_ratio(h_ratio, "Thrust")
        h_ratio.GetYaxis().SetTitle("Ratio")
        h_ratio.GetYaxis().SetRangeUser(y_min_ratio, y_max_ratio)
        h_ratio.GetXaxis().SetNdivisions(505)
        h_ratio.SetMarkerSize(0.85)
        h_ratio.Draw("PE1 SAME")
        ratio_hists[key] = h_ratio

    outdir = os.path.dirname(out_path)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    c.SaveAs(out_path)
    c.Close()

    curves = {
        "current": h_current,
        "aleph": h_aleph,
        "of": h_of,
        "ibu": h_ibu,
    }
    curve_arrays = {}
    for key, hist in curves.items():
        vals = np.asarray(
            [float(hist.GetBinContent(i)) for i in range(1, hist.GetNbinsX() + 1)],
            dtype=np.float64,
        )
        errs = np.asarray(
            [float(hist.GetBinError(i)) for i in range(1, hist.GetNbinsX() + 1)],
            dtype=np.float64,
        )
        curve_arrays[key] = (vals, errs)

    ratio_metrics = {}
    for key, hist in ratio_hists.items():
        vals = np.asarray(
            [float(hist.GetBinContent(i)) for i in range(1, hist.GetNbinsX() + 1)],
            dtype=np.float64,
        )
        errs = np.asarray(
            [float(hist.GetBinError(i)) for i in range(1, hist.GetNbinsX() + 1)],
            dtype=np.float64,
        )
        finite = np.isfinite(vals) & np.isfinite(errs)
        valid_vals = vals[finite]
        valid_errs = errs[finite]
        ratio_metrics[key] = {
            "max_abs_deviation_from_unity": float(np.max(np.abs(valid_vals - 1.0))) if valid_vals.size else 0.0,
            "max_plus_error": float(np.max(valid_vals + valid_errs)) if valid_vals.size else 0.0,
            "highest_bin_ratio": float(vals[-1]) if vals.size else 0.0,
            "highest_bin_error": float(errs[-1]) if errs.size else 0.0,
        }

    current_vals, current_errs = curve_arrays["current"]
    chi2_metrics = {
        "aleph_vs_current": _chi2_ndf(*curve_arrays["aleph"], current_vals, current_errs),
        "of_vs_current": _chi2_ndf(*curve_arrays["of"], current_vals, current_errs),
        "ibu_vs_current": _chi2_ndf(*curve_arrays["ibu"], current_vals, current_errs),
    }
    metrics = {
        "ratio_mode": "curve_over_current",
        "ratio_y_min": y_min_ratio,
        "ratio_y_max": y_max_ratio,
        "n_bins": n_aleph_bins,
        "ratio_metrics": ratio_metrics,
        "chi2_metrics": chi2_metrics,
        "input_files": {
            "legacy_ibu_npz": legacy_ibu_npz_path,
            "legacy_of_h5": legacy_of_h5_path,
            "aleph_csv": aleph_csv_path,
        },
        "output_pdf": out_path,
    }
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return metrics


def nominal_to_array(hist) -> np.ndarray:
    return np.asarray(
        [float(hist.GetBinContent(i)) for i in range(1, hist.GetNbinsX() + 1)],
        dtype=np.float64,
    )


def transform_cov_counts_to_diffxsec(
    cov_counts: np.ndarray,
    unfolded_counts,
    unfolded_corrected_counts,
) -> np.ndarray:
    u_unf = nominal_to_array(unfolded_counts)
    u_corr = nominal_to_array(unfolded_corrected_counts)
    nb = len(u_corr)
    if cov_counts.shape[0] != nb:
        raise ValueError(
            f"covariance dimension ({cov_counts.shape[0]}) does not match histogram bins ({nb})"
        )

    # Propagate pre-correction covariance to corrected-space via diagonal scaling.
    scale = np.ones(nb, dtype=np.float64)
    mask = np.abs(u_unf) > 0.0
    scale[mask] = u_corr[mask] / u_unf[mask]
    cov_corr = np.diag(scale) @ cov_counts @ np.diag(scale)

    # Transform corrected-count covariance to normalized differential cross section:
    # y_i = u_i / (sum_k u_k * width_i), J_{ik} = d y_i / d u_k.
    widths = hist_bin_widths(unfolded_corrected_counts)
    s = float(np.sum(u_corr))
    if s <= 0.0:
        raise ValueError("invalid total corrected counts for covariance normalization")
    jmat = np.zeros((nb, nb), dtype=np.float64)
    for i in range(nb):
        wi = widths[i] if widths[i] > 0.0 else 1.0
        for k in range(nb):
            delta = 1.0 if i == k else 0.0
            jmat[i, k] = ((delta * s) - u_corr[i]) / (s * s * wi)
    cov_diff = jmat @ cov_corr @ jmat.T
    return cov_diff


def main():
    args = parse_args()
    if args.central_range_min >= args.central_range_max:
        raise ValueError(
            f"invalid central range: [{args.central_range_min}, {args.central_range_max})"
        )
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    base_dir = os.path.abspath(args.base_dir)
    outdir = os.path.abspath(args.outdir or os.path.join(base_dir, "summary"))
    os.makedirs(outdir, exist_ok=True)
    aleph_csv_path = resolve_aleph_csv(args.aleph_csv)

    nominal_root = os.path.join(base_dir, "nominal", f"unfolded_nominal_iter{args.nominal_iter}.root")
    ensure_exists(nominal_root, "nominal ROOT")
    nominal_counts = load_hist(nominal_root, args.hist_name)
    nominal = to_diff_xsec(nominal_counts)
    nom = hist_to_array(nominal)
    nbins = len(nom)

    iter_roots = {
        args.iter_down: os.path.join(base_dir, "iteration", f"unfolded_iter{args.iter_down}.root"),
        args.iter_up: os.path.join(base_dir, "iteration", f"unfolded_iter{args.iter_up}.root"),
    }
    iter_arrays = []
    iter_shift_map = {}
    for it, path in iter_roots.items():
        ensure_exists(path, f"iteration ROOT ({it})")
        arr = hist_to_array(to_diff_xsec(load_hist(path, args.hist_name)))
        iter_arrays.append(arr)
        iter_shift_map[it] = frac_shift(arr, nom)
    iter_shifts = [frac_shift(arr, nom) for arr in iter_arrays]
    delta_iter = abs_env(iter_shifts)

    exp_arrays = {}
    for var in TRACK_EVENT_VARS + NEUTRAL_VARS + ["no_neutrals"]:
        path = os.path.join(base_dir, "experimental", f"unfolded_{var}.root")
        ensure_exists(path, f"experimental ROOT ({var})")
        exp_arrays[var] = hist_to_array(to_diff_xsec(load_hist(path, args.hist_name)))
    exp_shifts = {var: frac_shift(exp_arrays[var], nom) for var in exp_arrays}

    delta_track_event = quad_sum([np.abs(exp_shifts[v]) for v in TRACK_EVENT_VARS])
    delta_nes = abs_env(
        [
            exp_shifts["nes_up"],
            exp_shifts["nes_down"],
        ]
    )
    delta_neutral = quad_sum([delta_nes, np.abs(exp_shifts["ner"])])
    delta_exp_total = quad_sum([delta_track_event, delta_neutral])
    delta_no_neutrals = np.abs(exp_shifts["no_neutrals"])

    theory_arrays = {}
    theory_weight_diagnostics = {}
    for var in THEORY_VARS:
        path = os.path.join(base_dir, "theory", f"unfolded_theory_{var}.root")
        ensure_exists(path, f"theory ROOT ({var})")
        theory_arrays[var] = hist_to_array(to_diff_xsec(load_hist(path, args.hist_name)))
        try:
            theory_weight_diagnostics[var] = extract_theory_weight_diagnostics(path)
        except Exception as exc:
            theory_weight_diagnostics[var] = {
                "available": False,
                "error": str(exc),
            }
    theory_shifts = {var: frac_shift(theory_arrays[var], nom) for var in THEORY_VARS}
    delta_theory = abs_env([theory_shifts[v] for v in THEORY_VARS])

    cov_raw = load_raw_covariance(nominal_root)
    if cov_raw is not None:
        offdiag_raw = cov_raw - np.diag(np.diag(cov_raw))
        if np.count_nonzero(np.abs(offdiag_raw) > 0.0) == 0:
            print(
                "WARNING: unfolded raw covariance has zero off-diagonal entries; "
                "check unfolding covariance configuration.",
                file=sys.stderr,
            )
        unfolded_counts = load_hist(nominal_root, "unfolded")
        cov_stat = transform_cov_counts_to_diffxsec(cov_raw, unfolded_counts, nominal_counts)
    else:
        cov_stat = np.zeros((nbins, nbins), dtype=np.float64)
        for i in range(nbins):
            e = float(nominal.GetBinError(i + 1))
            cov_stat[i, i] = e * e

    offdiag_stat = cov_stat - np.diag(np.diag(cov_stat))
    if cov_raw is not None and np.count_nonzero(np.abs(offdiag_stat) > 0.0) == 0:
        print(
            "WARNING: transformed statistical covariance is diagonal after conversion; "
            "verify covariance propagation inputs.",
            file=sys.stderr,
        )

    nom_abs = np.abs(nom)
    stat_abs = np.sqrt(np.clip(np.diag(cov_stat), 0.0, None))
    iter_abs = delta_iter * nom_abs
    exp_track_event_abs = delta_track_event * nom_abs
    exp_neutral_abs = delta_neutral * nom_abs
    exp_abs = delta_exp_total * nom_abs
    theory_abs = delta_theory * nom_abs
    delta_hadronic = compute_hadronic_correction_fractional_shift(
        nominal_root=nominal_root,
        nominal_counts=nominal_counts,
        nominal_diffxsec=nom,
    )
    hadronic_abs = delta_hadronic * nom_abs
    no_neutrals_abs = delta_no_neutrals * nom_abs
    total_abs = np.sqrt(stat_abs**2 + exp_abs**2 + iter_abs**2 + theory_abs**2 + hadronic_abs**2)

    frac_stat = fractional_uncertainty(stat_abs, nom)
    frac_iter = fractional_uncertainty(iter_abs, nom)
    frac_exp_track_event = fractional_uncertainty(exp_track_event_abs, nom)
    frac_exp_neutral = fractional_uncertainty(exp_neutral_abs, nom)
    frac_exp = fractional_uncertainty(exp_abs, nom)
    frac_theory = fractional_uncertainty(theory_abs, nom)
    frac_hadronic = fractional_uncertainty(hadronic_abs, nom)
    frac_total = fractional_uncertainty(total_abs, nom)
    frac_no_neutrals = fractional_uncertainty(no_neutrals_abs, nom)
    pct_stat = 100.0 * frac_stat
    pct_iter = 100.0 * frac_iter
    pct_exp_track_event = 100.0 * frac_exp_track_event
    pct_exp_neutral = 100.0 * frac_exp_neutral
    pct_exp = 100.0 * frac_exp
    pct_theory = 100.0 * frac_theory

    corr_template = corr_from_cov(cov_stat)
    cov_iter = component_covariance_from_model(
        iter_abs,
        args.systematic_cov_model,
        corr_template=corr_template,
        block_rho=args.block_correlation_rho,
    )
    cov_exp = component_covariance_from_model(
        exp_abs,
        args.systematic_cov_model,
        corr_template=corr_template,
        block_rho=args.block_correlation_rho,
    )
    cov_theory = component_covariance_from_model(
        theory_abs,
        args.systematic_cov_model,
        corr_template=corr_template,
        block_rho=args.block_correlation_rho,
    )
    cov_hadronic = component_covariance_from_model(
        hadronic_abs,
        args.systematic_cov_model,
        corr_template=corr_template,
        block_rho=args.block_correlation_rho,
    )
    cov_total = cov_stat + cov_iter + cov_exp + cov_theory + cov_hadronic
    corr_total = corr_from_cov(cov_total)

    centers = np.asarray(
        [float(nominal.GetXaxis().GetBinCenter(i)) for i in range(1, nominal.GetNbinsX() + 1)],
        dtype=np.float64,
    )
    central_mask = (centers >= args.central_range_min) & (centers < args.central_range_max)
    if np.count_nonzero(central_mask) == 0:
        raise ValueError(
            "central range selected no bins; choose a range that overlaps the thrust binning"
        )
    fit_mask = build_fit_mask(
        args.fit_mask_mode,
        nom=nom,
        cov_total=cov_total,
        centers=centers,
        central_min=args.central_range_min,
        central_max=args.central_range_max,
    )
    fit_idx = np.where(fit_mask)[0]
    if fit_idx.size == 0:
        raise ValueError(
            f"fit mask mode '{args.fit_mask_mode}' selected no bins; adjust mode/range configuration"
        )
    cov_total_fit = cov_total[np.ix_(fit_idx, fit_idx)]
    corr_total_fit = corr_from_cov(cov_total_fit)

    write_csv(os.path.join(outdir, "cov_stat.csv"), cov_stat)
    write_csv(os.path.join(outdir, "cov_iter.csv"), cov_iter)
    write_csv(os.path.join(outdir, "cov_exp.csv"), cov_exp)
    write_csv(os.path.join(outdir, "cov_theory.csv"), cov_theory)
    write_csv(os.path.join(outdir, "cov_hadronic.csv"), cov_hadronic)
    write_csv(os.path.join(outdir, "cov_total.csv"), cov_total)
    write_csv(os.path.join(outdir, "corr_total.csv"), corr_total)
    write_csv(os.path.join(outdir, "cov_total_fitwindow.csv"), cov_total_fit)
    write_csv(os.path.join(outdir, "corr_total_fitwindow.csv"), corr_total_fit)

    with open(os.path.join(outdir, "binning.csv"), "w", encoding="utf-8") as f:
        f.write("bin,low,high,center,nominal_diffxsec\n")
        for i in range(1, nominal.GetNbinsX() + 1):
            f.write(
                f"{i},"
                f"{nominal.GetXaxis().GetBinLowEdge(i):.10f},"
                f"{nominal.GetXaxis().GetBinUpEdge(i):.10f},"
                f"{nominal.GetXaxis().GetBinCenter(i):.10f},"
                f"{nominal.GetBinContent(i):.10e}\n"
            )
    with open(os.path.join(outdir, "fit_mask.csv"), "w", encoding="utf-8") as f:
        f.write("bin,low,high,center,include\n")
        for i in range(1, nominal.GetNbinsX() + 1):
            f.write(
                f"{i},"
                f"{nominal.GetXaxis().GetBinLowEdge(i):.10f},"
                f"{nominal.GetXaxis().GetBinUpEdge(i):.10f},"
                f"{nominal.GetXaxis().GetBinCenter(i):.10f},"
                f"{1 if fit_mask[i - 1] else 0}\n"
            )

    component_plots = {
        "statistical": os.path.join(outdir, "uncertainty_components_statistical.pdf"),
        "unfolding": os.path.join(outdir, "uncertainty_components_unfolding.pdf"),
        "experimental": os.path.join(outdir, "uncertainty_components_experimental.pdf"),
        "theory": os.path.join(outdir, "uncertainty_components_theory.pdf"),
    }
    make_component_group_plot(
        out_path=component_plots["statistical"],
        template_hist=nominal,
        components={"stat": pct_stat},
        labels={"stat": "Statistical"},
        colors={"stat": ROOT.kBlack},
        line_styles={"stat": 1},
        y_min=0.0,
        y_max=50.0,
        legend_loc=[0.62, 0.82, 0.92, 0.90],
        legend_textsize=0.032,
        legend_ncols=1,
        legend_entry_sep=0.016,
        legend_column_sep=0.05,
        legend_margin=0.14,
        signed=False,
    )
    make_component_group_plot(
        out_path=component_plots["unfolding"],
        template_hist=nominal,
        components={
            f"iter_{args.iter_down}": 100.0 * iter_shift_map[args.iter_down],
            f"iter_{args.iter_up}": 100.0 * iter_shift_map[args.iter_up],
        },
        labels={
            f"iter_{args.iter_down}": f"Iteration {args.iter_down}",
            f"iter_{args.iter_up}": f"Iteration {args.iter_up}",
        },
        colors={
            f"iter_{args.iter_down}": ROOT.kAzure + 2,
            f"iter_{args.iter_up}": ROOT.kBlue + 1,
        },
        line_styles={
            f"iter_{args.iter_down}": 2,
            f"iter_{args.iter_up}": 1,
        },
        y_min=-50.0,
        y_max=50.0,
        legend_loc=[0.62, 0.78, 0.92, 0.90],
        legend_textsize=0.030,
        legend_ncols=1,
        legend_entry_sep=0.016,
        legend_column_sep=0.05,
        legend_margin=0.14,
        signed=True,
    )
    make_component_group_plot(
        out_path=component_plots["experimental"],
        template_hist=nominal,
        components={
            "ntpc7": 100.0 * exp_shifts["ntpc7"],
            "pt04": 100.0 * exp_shifts["pt04"],
            "ech10": 100.0 * exp_shifts["ech10"],
            "with_met": 100.0 * exp_shifts["with_met"],
            "nes_up": 100.0 * exp_shifts["nes_up"],
            "nes_down": 100.0 * exp_shifts["nes_down"],
            "ner": 100.0 * exp_shifts["ner"],
            "no_neutrals": 100.0 * exp_shifts["no_neutrals"],
        },
        labels={
            "ntpc7": "N_{TPC} > 7",
            "pt04": "p_{T} > 0.4 GeV",
            "ech10": "E_{ch} > 10 GeV",
            "with_met": "Missing-energy cut",
            "nes_up": "NES up",
            "nes_down": "NES down",
            "ner": "NER",
            "no_neutrals": "No-neutrals xcheck",
        },
        colors={
            "ntpc7": ROOT.kBlue + 1,
            "pt04": ROOT.kAzure + 3,
            "ech10": ROOT.kCyan + 2,
            "with_met": ROOT.kTeal + 2,
            "nes_up": ROOT.kGreen + 2,
            "nes_down": ROOT.kGreen + 3,
            "ner": ROOT.kSpring + 5,
            "no_neutrals": ROOT.kOrange + 7,
        },
        line_styles={
            "ntpc7": 1,
            "pt04": 1,
            "ech10": 1,
            "with_met": 1,
            "nes_up": 1,
            "nes_down": 1,
            "ner": 1,
            "no_neutrals": 1,
        },
        y_min=-50.0,
        y_max=50.0,
        legend_loc=[0.40, 0.20, 0.93, 0.44],
        legend_textsize=0.026,
        legend_ncols=2,
        legend_entry_sep=0.001,
        legend_column_sep=0.025,
        legend_margin=0.12,
        signed=True,
    )
    make_component_group_plot(
        out_path=component_plots["theory"],
        template_hist=nominal,
        components={
            "pythia8": 100.0 * theory_shifts["pythia8"],
            "herwig": 100.0 * theory_shifts["herwig"],
            "sherpa": 100.0 * theory_shifts["sherpa"],
        },
        labels={
            "pythia8": "PYTHIA8",
            "herwig": "HERWIG",
            "sherpa": "SHERPA",
        },
        colors={
            "pythia8": ROOT.kMagenta + 1,
            "herwig": ROOT.kViolet + 1,
            "sherpa": ROOT.kPink + 7,
        },
        line_styles={
            "pythia8": 1,
            "herwig": 2,
            "sherpa": 7,
        },
        y_min=-50.0,
        y_max=50.0,
        legend_loc=[0.68, 0.74, 0.92, 0.90],
        legend_textsize=0.030,
        legend_ncols=1,
        legend_entry_sep=0.016,
        legend_column_sep=0.05,
        legend_margin=0.14,
        signed=True,
    )
    ratio_stats = make_final_plot(
        out_path=os.path.join(outdir, "final_result_uncertainty_breakdown.pdf"),
        nominal=nominal,
        aleph_csv_path=aleph_csv_path,
        stat_abs=stat_abs,
        exp_abs=exp_abs,
        iter_abs=iter_abs,
        theory_abs=theory_abs,
        hadronic_abs=hadronic_abs,
    )
    comparison_plot_path = None
    comparison_metrics_path = None
    comparison_metrics = None
    legacy_inputs = None
    if args.include_of_ibu_comparison:
        legacy_inputs = resolve_legacy_input_paths(args, repo_root)
        comparison_plot_path = (
            args.comparison_output
            if os.path.isabs(args.comparison_output)
            else os.path.join(outdir, args.comparison_output)
        )
        comparison_metrics_path = os.path.join(outdir, "of_ibu_comparison_metrics.json")
        comparison_metrics = make_of_ibu_comparison_plot(
            out_path=comparison_plot_path,
            metrics_json_path=comparison_metrics_path,
            nominal=nominal,
            total_abs=total_abs,
            aleph_csv_path=aleph_csv_path,
            legacy_ibu_npz_path=legacy_inputs["legacy_ibu_npz"],
            legacy_of_h5_path=legacy_inputs["legacy_of_h5"],
            ratio_ymax=args.comparison_ratio_ymax,
        )

    response_counts = load_hist2d(nominal_root, "response_counts")
    resp_diag_frac = response_diag_fraction(response_counts)
    offdiag_corr = np.abs(corr_total - np.diag(np.diag(corr_total)))
    corr_max_offdiag = float(np.max(offdiag_corr))
    nz = offdiag_corr[offdiag_corr > 0.0]
    corr_mean_offdiag_nonzero = float(np.mean(nz)) if nz.size else 0.0

    frac_all = {
        "iteration": frac_iter,
        "exp_track_event": frac_exp_track_event,
        "exp_neutral": frac_exp_neutral,
        "exp_total": frac_exp,
        "theory": frac_theory,
        "hadronic_correction": frac_hadronic,
        "no_neutrals_crosscheck": frac_no_neutrals,
        "stat": frac_stat,
        "total": frac_total,
    }
    mean_abs_fractional = {
        k: summarize_fractional(v)["mean"] for k, v in frac_all.items()
    }
    max_abs_fractional = {
        k: summarize_fractional(v)["max"] for k, v in frac_all.items()
    }
    mean_abs_fractional_central = {
        k: summarize_fractional(v, central_mask)["mean"] for k, v in frac_all.items()
    }
    max_abs_fractional_central = {
        k: summarize_fractional(v, central_mask)["max"] for k, v in frac_all.items()
    }

    summary = {
        "base_dir": base_dir,
        "nominal_iteration": args.nominal_iter,
        "iteration_systematic": [args.iter_down, args.iter_up],
        "central_reporting_range": {
            "variable": "thrust",
            "min_inclusive": args.central_range_min,
            "max_exclusive": args.central_range_max,
            "selected_bins": int(np.count_nonzero(central_mask)),
        },
        "experimental_total_definition": {
            "track_event": TRACK_EVENT_VARS,
            "neutral": {
                "nes_pair": ["nes_up", "nes_down"],
                "ner": "ner",
            },
            "crosscheck_only": ["no_neutrals"],
        },
        "theory_definition": THEORY_VARS,
        "mean_abs_fractional": mean_abs_fractional,
        "max_abs_fractional": max_abs_fractional,
        "mean_abs_fractional_central": mean_abs_fractional_central,
        "max_abs_fractional_central": max_abs_fractional_central,
        "outputs": {
            "cov_stat": os.path.join(outdir, "cov_stat.csv"),
            "cov_iter": os.path.join(outdir, "cov_iter.csv"),
            "cov_exp": os.path.join(outdir, "cov_exp.csv"),
            "cov_theory": os.path.join(outdir, "cov_theory.csv"),
            "cov_hadronic": os.path.join(outdir, "cov_hadronic.csv"),
            "cov_total": os.path.join(outdir, "cov_total.csv"),
            "corr_total": os.path.join(outdir, "corr_total.csv"),
            "fit_mask": os.path.join(outdir, "fit_mask.csv"),
            "cov_total_fitwindow": os.path.join(outdir, "cov_total_fitwindow.csv"),
            "corr_total_fitwindow": os.path.join(outdir, "corr_total_fitwindow.csv"),
            "binning": os.path.join(outdir, "binning.csv"),
            "component_plots": component_plots,
            "final_plot": os.path.join(outdir, "final_result_uncertainty_breakdown.pdf"),
            "aleph_csv": aleph_csv_path,
            "ratio_mode": "aleph_over_unfolded",
            "ratio_y_min": 0.75,
            "ratio_y_max": 1.55,
        },
        "diagnostics": {
            "response_diagonal_fraction": resp_diag_frac,
            "corr_total_max_abs_offdiag": corr_max_offdiag,
            "corr_total_mean_abs_offdiag_nonzero": corr_mean_offdiag_nonzero,
            "corr_total_nonzero_offdiag_entries": int(np.count_nonzero(offdiag_corr > 0.0)),
            "aleph_over_unfolded_ratio": ratio_stats,
            "systematic_covariance_model": args.systematic_cov_model,
            "systematic_covariance_model_params": {
                "block_correlation_rho": float(args.block_correlation_rho),
            },
            "systematic_covariance_note": (
                "Iteration, experimental, theory, and hadronic-correction covariance components use "
                "the configured systematic covariance model."
            ),
            "hadronic_correction_uncertainty_included": True,
            "hadronic_correction_uncertainty_model": (
                "Envelope of up/down hadronic-correction ratio uncertainty propagated through "
                "normalized differential-thrust conversion."
            ),
            "fit_mask_mode": args.fit_mask_mode,
            "fit_window_selected_bins": int(fit_idx.size),
            "fit_window_first_bin": int(fit_idx[0] + 1),
            "fit_window_last_bin": int(fit_idx[-1] + 1),
            "fit_window_zero_variance_bins": int(np.count_nonzero(np.diag(cov_total_fit) <= 0.0)),
            "theory_weight_diagnostics": theory_weight_diagnostics,
            "of_ibu_comparison_enabled": bool(args.include_of_ibu_comparison),
        },
        "provenance": collect_provenance(repo_root),
    }
    if comparison_plot_path is not None:
        summary["outputs"]["of_ibu_comparison_plot"] = comparison_plot_path
        summary["outputs"]["of_ibu_comparison_metrics"] = comparison_metrics_path
        summary["diagnostics"]["of_ibu_input_paths"] = legacy_inputs
        summary["diagnostics"]["of_ibu_comparison_metrics"] = comparison_metrics
    summary_path = os.path.join(outdir, "uncertainty_breakdown.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    add_plotting_path()
    from style import SetALEPHStyle

    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    SetALEPHStyle()
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
