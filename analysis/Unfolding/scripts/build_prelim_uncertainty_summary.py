#!/usr/bin/env python3
"""Build thrust preliminary uncertainty breakdown, covariance exports, and summary plots.

Inputs (resolved from --base_dir):
  nominal/unfolded_nominal_iter<N>.root  -- IBU-unfolded nominal spectrum + raw stat covariance
  iteration/unfolded_iter<M>.root        -- IBU results at alternative iteration counts (up/down)
  experimental/unfolded_<var>.root       -- one ROOT file per experimental systematic variation
  theory/unfolded_theory_<mc>.root       -- one ROOT file per theory-reweighted MC variation

Uncertainty components computed:
  stat     -- from RooUnfold raw covariance matrix, transformed to differential cross-section basis
  iter     -- envelope of Niter up/down shifts relative to nominal
  exp      -- quadrature of track/event (ntpc7, pt04, ech10, with_met) and neutral (nes, ner) shifts
  theory   -- max envelope of PYTHIA8, HERWIG, SHERPA reweighted shifts
  hadronic -- envelope of up/down hadronic-event correction ratio uncertainty (tgenBefore/tgen)

Covariance model for non-statistical components (configurable via --systematic_cov_model):
  template_correlated: Cov^(c)_ij = Delta_c(i) * Delta_c(j) * rho^stat_ij
  where rho^stat is the correlation matrix derived from the statistical covariance.

Outputs (written to --outdir, default <base_dir>/summary/):
  cov_{stat,iter,exp,theory,hadronic,total}.csv  -- covariance matrices (N_bins x N_bins)
  corr_total.csv                                 -- correlation matrix
  binning.csv, reported_bins.csv                 -- bin edges, centers, reported-range membership
  workflow_summary.json                          -- full provenance and numeric diagnostics

Figures are drawn separately by analysis/plotting/ from these artifacts; this
script produces numbers only and needs no ROOT drawing.
"""

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
from typing import List

import numpy as np
import ROOT


TRACK_EVENT_VARS = ["ntpc7", "pt04", "ech10", "with_met"]
NEUTRAL_VARS = ["nes_up", "nes_down", "ner"]
THEORY_VARS = ["pythia8", "herwig", "sherpa"]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-dir", required=True, help="Workflow output directory")
    p.add_argument("--nominal-iter", type=int, default=5)
    p.add_argument("--iter-down", type=int, default=4)
    p.add_argument("--iter-up", type=int, default=6)
    p.add_argument("--hist-name", default="unfolded_corrected")
    p.add_argument("--outdir", default=None)
    p.add_argument(
        "--skip-theory",
        action="store_true",
        help=(
            "Continue with a zero theory uncertainty when the theory ROOTs are "
            "absent. Needed for an open-data-only run: the theory variations "
            "require the modern-generator samples."
        ),
    )
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
        "--report-range-min",
        type=float,
        default=0.58,
        help=(
            "Lower thrust edge of the reported range. Populated bins below it have "
            "total uncertainties exceeding their own content and are not reported."
        ),
    )
    p.add_argument(
        "--isr-cache",
        default=None,
        help=(
            "Path to isr_correction_cache.root (pre-computed by run_thrust_prelim_workflow.py). "
            "If omitted, auto-detected at <base-dir>/isr_cache/isr_correction_cache.root."
        ),
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


def _chi2_ndf(y1: np.ndarray, yerr1: np.ndarray, y2: np.ndarray, yerr2: np.ndarray) -> dict:
    sigma2 = np.asarray(yerr1, dtype=np.float64) ** 2 + np.asarray(yerr2, dtype=np.float64) ** 2
    valid = sigma2 > 0.0
    ndf = int(np.count_nonzero(valid))
    if ndf == 0:
        return {"chi2": 0.0, "ndf": 0, "chi2_per_ndf": 0.0}
    dy = np.asarray(y1, dtype=np.float64) - np.asarray(y2, dtype=np.float64)
    chi2 = float(np.sum((dy[valid] ** 2) / sigma2[valid]))
    return {"chi2": chi2, "ndf": ndf, "chi2_per_ndf": (chi2 / ndf)}


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


def compute_isr_correction_fractional_shift(
    nominal_root: str,
    nominal_counts,
    nominal_diffxsec: np.ndarray,
    isr_cache_file: str | None = None,
) -> np.ndarray:
    src = isr_cache_file if (isr_cache_file and os.path.exists(isr_cache_file)) else nominal_root
    h_isr0 = load_hist(src, "mc_isr0")
    h_isr1 = load_hist(src, "mc_isr1")
    nbins = nominal_counts.GetNbinsX()
    if h_isr0.GetNbinsX() != nbins or h_isr1.GetNbinsX() != nbins:
        raise ValueError(
            "ISR correction histograms have inconsistent binning relative to nominal histogram"
        )

    h_up = nominal_counts.Clone("isr_corr_up_counts")
    h_down = nominal_counts.Clone("isr_corr_down_counts")
    h_up.SetDirectory(0)
    h_down.SetDirectory(0)

    for ibin in range(1, nbins + 1):
        n_isr0 = float(h_isr0.GetBinContent(ibin))
        n_isr0_err = float(h_isr0.GetBinError(ibin))
        n_isr1 = float(h_isr1.GetBinContent(ibin))
        n_isr1_err = float(h_isr1.GetBinError(ibin))
        rel = 0.0
        if n_isr0 > 0.0 and n_isr1 > 0.0:
            rel = math.sqrt((n_isr0_err / n_isr0) ** 2 + (n_isr1_err / n_isr1) ** 2)

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


def _rebin_to_edges(
    src_edges: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    dst_edges: np.ndarray,
):
    # Sums contents and adds errors in quadrature, as TH1::Rebin does; source
    # bins whose centre falls outside dst_edges go to under/overflow and drop.
    src_edges = np.asarray(src_edges, dtype=np.float64)
    dst_edges = np.asarray(dst_edges, dtype=np.float64)
    centers = 0.5 * (src_edges[:-1] + src_edges[1:])
    n_dst = len(dst_edges) - 1
    idx = np.searchsorted(dst_edges, centers, side="right") - 1
    keep = (idx >= 0) & (idx < n_dst)
    out_values = np.zeros(n_dst, dtype=np.float64)
    out_err_sq = np.zeros(n_dst, dtype=np.float64)
    np.add.at(out_values, idx[keep], np.asarray(values, dtype=np.float64)[keep])
    np.add.at(out_err_sq, idx[keep], np.asarray(errors, dtype=np.float64)[keep] ** 2)
    return out_values, np.sqrt(out_err_sq)


def _ratio_over(num: np.ndarray, num_err: np.ndarray, den: np.ndarray):
    # TH1::Divide against an error-free denominator: each uncertainty is counted
    # once, so only the numerator's error scales into the ratio.
    num = np.asarray(num, dtype=np.float64)
    num_err = np.asarray(num_err, dtype=np.float64)
    den = np.asarray(den, dtype=np.float64)
    ok = den > 0.0
    ratio = np.divide(num, den, out=np.zeros_like(den), where=ok)
    ratio_err = np.divide(num_err, den, out=np.zeros_like(den), where=ok)
    return ratio, ratio_err


def compute_aleph_over_unfolded_ratio_stats(
    *,
    nominal_edges: np.ndarray,
    nominal_values: np.ndarray,
    total_abs: np.ndarray,
    aleph_csv_path: str,
) -> dict:
    """ALEPH 2004 over the unfolded result, summarised in the ALEPH binning."""
    aleph = load_aleph_2004_result(aleph_csv_path)
    nom_on_aleph, _ = _rebin_to_edges(
        nominal_edges, nominal_values, total_abs, aleph["edges"]
    )
    ratio_vals, ratio_errs = _ratio_over(aleph["values"], aleph["total"], nom_on_aleph)
    return {
        "max_central": float(np.max(ratio_vals)) if ratio_vals.size else 0.0,
        "max_plus_error": float(np.max(ratio_vals + ratio_errs)) if ratio_vals.size else 0.0,
        "highest_bin_value": float(ratio_vals[-1]) if ratio_vals.size else 0.0,
        "highest_bin_error": float(ratio_errs[-1]) if ratio_errs.size else 0.0,
        "highest_bin_low_edge": float(aleph["edges"][-2]),
        "highest_bin_up_edge": float(aleph["edges"][-1]),
    }


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
    isr_cache_file = args.isr_cache
    if isr_cache_file is None:
        auto = os.path.join(base_dir, "isr_cache", "isr_correction_cache.root")
        if os.path.exists(auto):
            isr_cache_file = auto
            print(f"Auto-detected ISR cache: {isr_cache_file}")
        else:
            print("WARNING: ISR cache not found; ISR uncertainty will be zero.", file=sys.stderr)
    os.makedirs(outdir, exist_ok=True)
    aleph_csv_path = resolve_aleph_csv(args.aleph_csv)

    # --- Load nominal unfolded spectrum ---
    nominal_root = os.path.join(base_dir, "nominal", f"unfolded_nominal_iter{args.nominal_iter}.root")
    ensure_exists(nominal_root, "nominal ROOT")
    nominal_counts = load_hist(nominal_root, args.hist_name)

    # Determine whether the ISR correction needs to be applied post-hoc.
    # When run_thrust_prelim_workflow.py produces ROOT files with apply_isr_correction=true it
    # writes an isr_corr histogram into each output file.  Older files (pre-ISR implementation)
    # lack that histogram, so we apply the cached correction here to every loaded histogram so
    # that the nominal central values and all systematic-variant arrays are in the same ISR basis.
    h_isr_corr_to_apply = None
    try:
        load_hist(nominal_root, "isr_corr")
        # ISR already baked in; no post-hoc correction needed.
    except KeyError:
        if isr_cache_file:
            h_isr_corr_to_apply = load_hist(isr_cache_file, "isr_corr")
            print("ISR correction will be applied post-hoc from cache to all loaded histograms.")
    if h_isr_corr_to_apply is not None:
        nominal_counts.Multiply(h_isr_corr_to_apply)

    nominal = to_diff_xsec(nominal_counts)
    nom = hist_to_array(nominal)
    nbins = len(nom)

    # --- Unfolding iteration uncertainty (Niter up/down envelope) ---
    iter_roots = {
        args.iter_down: os.path.join(base_dir, "iteration", f"unfolded_iter{args.iter_down}.root"),
        args.iter_up: os.path.join(base_dir, "iteration", f"unfolded_iter{args.iter_up}.root"),
    }
    iter_arrays = []
    for it, path in iter_roots.items():
        ensure_exists(path, f"iteration ROOT ({it})")
        h_it = load_hist(path, args.hist_name)
        if h_isr_corr_to_apply is not None:
            h_it.Multiply(h_isr_corr_to_apply)
        iter_arrays.append(hist_to_array(to_diff_xsec(h_it)))
    iter_shifts = [frac_shift(arr, nom) for arr in iter_arrays]
    delta_iter = abs_env(iter_shifts)

    # --- Experimental systematic uncertainties ---
    # Track/event variations: ntpc7, pt04, ech10, with_met (quadrature sum -> delta_track_event)
    # Neutral variations: nes_up/down envelope + ner (quadrature sum -> delta_neutral)
    # no_neutrals is a cross-check only; not included in delta_exp_total.
    exp_arrays = {}
    for var in TRACK_EVENT_VARS + NEUTRAL_VARS + ["no_neutrals"]:
        path = os.path.join(base_dir, "experimental", f"unfolded_{var}.root")
        ensure_exists(path, f"experimental ROOT ({var})")
        h_exp = load_hist(path, args.hist_name)
        if h_isr_corr_to_apply is not None:
            h_exp.Multiply(h_isr_corr_to_apply)
        exp_arrays[var] = hist_to_array(to_diff_xsec(h_exp))
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

    # --- Theory uncertainty (MC generator reweighting envelope) ---
    # Each MC (PYTHIA8, HERWIG, SHERPA) is reweighted to data using event-ID-matched weight files.
    # delta_theory = max envelope of the three fractional shifts relative to nominal.
    theory_arrays = {}
    theory_weight_diagnostics = {}
    # The theory variations need the modern-generator samples, which are not part
    # of the ALEPH open data. With --skip-theory the theory uncertainty degrades to
    # zero with a loud warning, matching how a missing ISR cache is handled above,
    # rather than aborting the whole summary.
    _theory_missing = [
        v for v in THEORY_VARS
        if not os.path.exists(os.path.join(base_dir, "theory", f"unfolded_theory_{v}.root"))
    ]
    if _theory_missing and not args.skip_theory:
        raise SystemExit(
            "ERROR: missing theory ROOT(s): " + ", ".join(_theory_missing)
            + "\n       These require the PYTHIA8/Herwig/Sherpa samples, which are"
            + "\n       not part of the open data. Pass --skip-theory to continue"
            + "\n       with a zero theory uncertainty."
        )
    if args.skip_theory:
        print("WARNING: --skip-theory; theory uncertainty will be zero.", file=sys.stderr)
    for var in ([] if args.skip_theory else THEORY_VARS):
        path = os.path.join(base_dir, "theory", f"unfolded_theory_{var}.root")
        ensure_exists(path, f"theory ROOT ({var})")
        h_th = load_hist(path, args.hist_name)
        if h_isr_corr_to_apply is not None:
            h_th.Multiply(h_isr_corr_to_apply)
        theory_arrays[var] = hist_to_array(to_diff_xsec(h_th))
        try:
            theory_weight_diagnostics[var] = extract_theory_weight_diagnostics(path)
        except Exception as exc:
            theory_weight_diagnostics[var] = {
                "available": False,
                "error": str(exc),
            }
    if args.skip_theory:
        theory_shifts = {}
        delta_theory = np.zeros_like(np.asarray(nom, dtype=float))
    else:
        theory_shifts = {var: frac_shift(theory_arrays[var], nom) for var in THEORY_VARS}
        delta_theory = abs_env([theory_shifts[v] for v in THEORY_VARS])

    # --- Statistical covariance from RooUnfold ---
    # The raw covariance is stored in counts space by RooUnfold. It is transformed to the
    # differential cross-section basis via transform_cov_counts_to_diffxsec. If the raw
    # covariance is unavailable, fall back to a diagonal matrix from bin errors.
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

    # --- Absolute and fractional uncertainty arrays per bin ---
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
    isr_hists_available = False
    try:
        delta_isr = compute_isr_correction_fractional_shift(
            nominal_root=nominal_root,
            nominal_counts=nominal_counts,
            nominal_diffxsec=nom,
            isr_cache_file=isr_cache_file,
        )
        isr_hists_available = True
    except KeyError:
        delta_isr = np.zeros_like(nom)
    isr_abs = delta_isr * nom_abs
    no_neutrals_abs = delta_no_neutrals * nom_abs

    # Response-matrix MC statistics, from the Poisson bootstrap
    # (run_response_bootstrap.py). Absent -> zero, so an open-data run without the
    # toys still works. This is the response and efficiency only; the tgenBefore/tgen
    # statistics stay in cov_hadronic and are not counted twice.
    mcstat_csv = os.path.join(outdir, "cov_mcstat.csv")
    if os.path.exists(mcstat_csv):
        cov_mcstat_in = np.loadtxt(mcstat_csv, delimiter=",", ndmin=2)
        if cov_mcstat_in.shape != (nbins, nbins):
            raise ValueError(
                f"{mcstat_csv} is {cov_mcstat_in.shape}, expected ({nbins}, {nbins})"
            )
        mcstat_abs = np.sqrt(np.clip(np.diag(cov_mcstat_in), 0.0, None))
        print(f"Response MC-stat covariance loaded: {mcstat_csv}")
    else:
        cov_mcstat_in = np.zeros((nbins, nbins), dtype=np.float64)
        mcstat_abs = np.zeros_like(stat_abs)
        print("Response MC-stat covariance not found; component set to zero")

    total_abs = np.sqrt(
        stat_abs**2 + mcstat_abs**2 + exp_abs**2 + iter_abs**2
        + theory_abs**2 + hadronic_abs**2 + isr_abs**2
    )

    frac_stat = fractional_uncertainty(stat_abs, nom)
    frac_mcstat = fractional_uncertainty(mcstat_abs, nom)
    frac_isr = fractional_uncertainty(isr_abs, nom)
    frac_iter = fractional_uncertainty(iter_abs, nom)
    frac_exp_track_event = fractional_uncertainty(exp_track_event_abs, nom)
    frac_exp_neutral = fractional_uncertainty(exp_neutral_abs, nom)
    frac_exp = fractional_uncertainty(exp_abs, nom)
    frac_theory = fractional_uncertainty(theory_abs, nom)
    frac_hadronic = fractional_uncertainty(hadronic_abs, nom)
    frac_total = fractional_uncertainty(total_abs, nom)
    frac_no_neutrals = fractional_uncertainty(no_neutrals_abs, nom)
    # --- Build per-component covariance matrices ---
    # All non-statistical components use the statistical correlation matrix as a template:
    #   Cov^(c)_ij = Delta_c(i) * Delta_c(j) * rho^stat_ij
    # This avoids a purely diagonal systematic covariance while keeping component magnitudes
    # tied to the measured per-bin shifts. See --systematic_cov_model for alternatives.
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
    cov_isr = component_covariance_from_model(
        isr_abs,
        args.systematic_cov_model,
        corr_template=corr_template,
        block_rho=args.block_correlation_rho,
    )
    # cov_mcstat is a measured sample covariance, so it enters as-is rather than
    # through component_covariance_from_model.
    cov_mcstat = cov_mcstat_in
    cov_total = (
        cov_stat + cov_mcstat + cov_iter + cov_exp + cov_theory + cov_hadronic + cov_isr
    )
    corr_total = corr_from_cov(cov_total)

    # --- Bin masking: central reporting range and alpha_s fit window ---
    centers = np.asarray(
        [float(nominal.GetXaxis().GetBinCenter(i)) for i in range(1, nominal.GetNbinsX() + 1)],
        dtype=np.float64,
    )
    central_mask = (centers >= args.central_range_min) & (centers < args.central_range_max)
    if np.count_nonzero(central_mask) == 0:
        raise ValueError(
            "central range selected no bins; choose a range that overlaps the thrust binning"
        )
    # Reported range: populated bins at or above --report-range-min. The two
    # populated bins below 0.58 carry total uncertainties of 158% and 365%, so they
    # are excluded; this also aligns the released covariance with the per-bin tables
    # and with ALEPH 2004's 42 bins.
    reported_mask = (
        (np.abs(nom) > 0.0) & (np.diag(cov_total) > 0.0) & (centers >= args.report_range_min)
    )
    if not reported_mask.any():
        raise ValueError(
            f"--report-range-min={args.report_range_min} selected no populated bins"
        )
    reported_idx = np.where(reported_mask)[0]
    print(f"Reported range: {int(reported_mask.sum())} bins, T >= {args.report_range_min}")

    # --- Export covariance matrices and binning to CSV ---
    write_csv(os.path.join(outdir, "cov_stat.csv"), cov_stat)
    write_csv(os.path.join(outdir, "cov_mcstat.csv"), cov_mcstat)
    write_csv(os.path.join(outdir, "cov_iter.csv"), cov_iter)
    write_csv(os.path.join(outdir, "cov_exp.csv"), cov_exp)
    write_csv(os.path.join(outdir, "cov_theory.csv"), cov_theory)
    write_csv(os.path.join(outdir, "cov_hadronic.csv"), cov_hadronic)
    write_csv(os.path.join(outdir, "cov_isr.csv"), cov_isr)
    write_csv(os.path.join(outdir, "cov_total.csv"), cov_total)
    write_csv(os.path.join(outdir, "corr_total.csv"), corr_total)

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
    with open(os.path.join(outdir, "reported_bins.csv"), "w", encoding="utf-8") as f:
        f.write("bin,low,high,center,include\n")
        for i in range(1, nominal.GetNbinsX() + 1):
            f.write(
                f"{i},"
                f"{nominal.GetXaxis().GetBinLowEdge(i):.10f},"
                f"{nominal.GetXaxis().GetBinUpEdge(i):.10f},"
                f"{nominal.GetXaxis().GetBinCenter(i):.10f},"
                f"{1 if reported_mask[i - 1] else 0}\n"
            )

    # --- Derive the numeric diagnostics; figures are produced separately by
    # analysis/plotting/ from these persisted artifacts. ---
    nbins_x = nominal.GetNbinsX()
    nominal_edges = np.asarray(
        [nominal.GetXaxis().GetBinLowEdge(i) for i in range(1, nbins_x + 1)]
        + [nominal.GetXaxis().GetBinUpEdge(nbins_x)],
        dtype=np.float64,
    )
    # The six components make up the band on the final result; the response
    # MC-stat term stays out of it and is carried by cov_total alone.
    final_total_abs = np.sqrt(
        stat_abs**2 + exp_abs**2 + iter_abs**2 + theory_abs**2 + hadronic_abs**2 + isr_abs**2
    )
    ratio_stats = compute_aleph_over_unfolded_ratio_stats(
        nominal_edges=nominal_edges,
        nominal_values=nom,
        total_abs=final_total_abs,
        aleph_csv_path=aleph_csv_path,
    )
    response_counts = load_hist2d(nominal_root, "response_counts")
    resp_diag_frac = response_diag_fraction(response_counts)
    offdiag_corr = np.abs(corr_total - np.diag(np.diag(corr_total)))
    corr_max_offdiag = float(np.max(offdiag_corr))
    nz = offdiag_corr[offdiag_corr > 0.0]
    corr_mean_offdiag_nonzero = float(np.mean(nz)) if nz.size else 0.0

    frac_all = {
        "response_mc_stat": frac_mcstat,
        "iteration": frac_iter,
        "exp_track_event": frac_exp_track_event,
        "exp_neutral": frac_exp_neutral,
        "exp_total": frac_exp,
        "theory": frac_theory,
        "hadronic_correction": frac_hadronic,
        "isr_correction": frac_isr,
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
        "theory_definition": [] if args.skip_theory else THEORY_VARS,
        "mean_abs_fractional": mean_abs_fractional,
        "max_abs_fractional": max_abs_fractional,
        "mean_abs_fractional_central": mean_abs_fractional_central,
        "max_abs_fractional_central": max_abs_fractional_central,
        "outputs": {
            "cov_stat": os.path.join(outdir, "cov_stat.csv"),
            "cov_mcstat": os.path.join(outdir, "cov_mcstat.csv"),
            "cov_iter": os.path.join(outdir, "cov_iter.csv"),
            "cov_exp": os.path.join(outdir, "cov_exp.csv"),
            "cov_theory": os.path.join(outdir, "cov_theory.csv"),
            "cov_hadronic": os.path.join(outdir, "cov_hadronic.csv"),
            "cov_isr": os.path.join(outdir, "cov_isr.csv"),
            "cov_total": os.path.join(outdir, "cov_total.csv"),
            "corr_total": os.path.join(outdir, "corr_total.csv"),
            "reported_bins": os.path.join(outdir, "reported_bins.csv"),
            "binning": os.path.join(outdir, "binning.csv"),
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
            "theory_uncertainty_included": not args.skip_theory,
            "theory_uncertainty_note": (
                "Theory uncertainty is ZERO in this summary: --skip-theory was passed, "
                "so the PYTHIA8/Herwig/Sherpa variations were not read. Theory dominates "
                "the total off-diagonal correlation structure, so corr_total_* and the "
                "totals here are NOT comparable to a full run."
            ) if args.skip_theory else (
                "Max envelope of the three generator-reweighting fractional shifts."
            ),
            "isr_correction_uncertainty_included": isr_hists_available,
            "isr_correction_uncertainty_model": (
                "Envelope of up/down ISR correction ratio uncertainty (mc_isr0/mc_isr1 MC-stat) "
                "propagated through normalized differential-thrust conversion."
            ),
            "report_range_min": args.report_range_min,
            "reported_bins": int(reported_mask.sum()),
            "reported_selected_bins": int(reported_idx.size),
            "reported_first_bin": int(reported_idx[0] + 1),
            "reported_last_bin": int(reported_idx[-1] + 1),
            "theory_weight_diagnostics": theory_weight_diagnostics,
        },
        "provenance": collect_provenance(repo_root),
    }
    summary_path = os.path.join(outdir, "uncertainty_breakdown.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
