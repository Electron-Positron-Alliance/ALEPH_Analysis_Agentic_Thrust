#!/usr/bin/env python3
"""Validate preliminary thrust summary outputs for completeness and matrix sanity."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import ROOT


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-dir", required=True, help="Workflow base directory")
    p.add_argument("--summary-dir", default=None, help="Summary directory (default: <base-dir>/summary)")
    p.add_argument("--sym-tol", type=float, default=1e-8, help="Symmetry tolerance for matrix checks")
    p.add_argument("--corr-tol", type=float, default=1e-8, help="Tolerance for correlation bounds")
    p.add_argument(
        "--strict-fit",
        action="store_true",
        help="Enable strict fit-readiness checks (condition number, zero-variance bins, PSD).",
    )
    p.add_argument(
        "--max-zero-variance-bins",
        type=int,
        default=0,
        help="Maximum allowed bins with non-positive diagonal variance in strict-fit mode.",
    )
    p.add_argument(
        "--max-condition-number",
        type=float,
        default=1.0e16,
        help="Maximum allowed positive-spectrum condition number in strict-fit mode.",
    )
    p.add_argument(
        "--require-provenance",
        action="store_true",
        help="Require immutable provenance block in summary metadata.",
    )
    return p.parse_args()


def fail(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise RuntimeError(msg)


def require_file(path: str):
    if not os.path.exists(path):
        fail(f"Missing required file: {path}")


def load_csv_matrix(path: str) -> np.ndarray:
    arr = np.loadtxt(path, delimiter=",")
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        fail(f"Matrix is not square: {path} shape={arr.shape}")
    if not np.all(np.isfinite(arr)):
        fail(f"Matrix has non-finite entries: {path}")
    return arr


def check_symmetric(name: str, mat: np.ndarray, tol: float):
    delta = np.max(np.abs(mat - mat.T))
    if delta > tol:
        fail(f"{name} is not symmetric within tolerance: max|A-A^T|={delta:.3e}")


def main() -> int:
    args = parse_args()
    base_dir = os.path.abspath(args.base_dir)
    summary_dir = os.path.abspath(args.summary_dir or os.path.join(base_dir, "summary"))
    require_provenance = bool(args.require_provenance or args.strict_fit)

    require_file(summary_dir)

    summary_path = os.path.join(summary_dir, "uncertainty_breakdown.json")
    require_file(summary_path)
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    outputs = summary.get("outputs")
    if not isinstance(outputs, dict):
        fail("summary JSON missing 'outputs' dictionary")

    required_output_keys = [
        "cov_stat",
        "cov_iter",
        "cov_exp",
        "cov_theory",
        "cov_total",
        "corr_total",
        "binning",
        "component_plots",
        "final_plot",
        "ratio_mode",
        "ratio_y_min",
        "ratio_y_max",
    ]
    for key in required_output_keys:
        if key not in outputs:
            fail(f"summary outputs missing key: {key}")
    fit_required_keys = ["fit_mask", "cov_total_fitwindow", "corr_total_fitwindow"]
    if args.strict_fit:
        for key in fit_required_keys:
            if key not in outputs:
                fail(f"strict-fit mode requires summary outputs key: {key}")
    else:
        missing_fit = [k for k in fit_required_keys if k not in outputs]
        if missing_fit:
            print(f"WARNING: missing fit-window outputs: {missing_fit}", file=sys.stderr)

    diagnostics = summary.get("diagnostics")
    if not isinstance(diagnostics, dict):
        fail("summary JSON missing 'diagnostics' dictionary")
    for key in [
        "response_diagonal_fraction",
        "corr_total_max_abs_offdiag",
        "corr_total_nonzero_offdiag_entries",
        "aleph_over_unfolded_ratio",
        "systematic_covariance_model",
        "hadronic_correction_uncertainty_included",
    ]:
        if key not in diagnostics:
            fail(f"summary diagnostics missing key: {key}")
    if args.strict_fit and "fit_mask_mode" not in diagnostics:
        fail("strict-fit mode requires diagnostics.fit_mask_mode")
    if args.strict_fit and "theory_weight_diagnostics" not in diagnostics:
        fail("strict-fit mode requires diagnostics.theory_weight_diagnostics")

    provenance = summary.get("provenance")
    required_provenance_keys = [
        "generated_at_utc",
        "git_commit",
        "git_dirty",
        "python_version",
        "root_version",
        "roounfold_version",
        "env_fingerprint",
    ]
    if provenance is None:
        if require_provenance:
            fail("summary JSON missing required 'provenance' dictionary")
        print("WARNING: summary JSON has no provenance block", file=sys.stderr)
    elif not isinstance(provenance, dict):
        fail("summary JSON provenance must be a dictionary when present")
    else:
        missing_prov = [k for k in required_provenance_keys if k not in provenance]
        if missing_prov and require_provenance:
            fail(f"summary provenance missing keys: {missing_prov}")
        if missing_prov:
            print(f"WARNING: summary provenance missing keys: {missing_prov}", file=sys.stderr)

    require_file(outputs["binning"])
    require_file(outputs["final_plot"])
    if "fit_mask" in outputs:
        require_file(outputs["fit_mask"])

    component_plots = outputs["component_plots"]
    if not isinstance(component_plots, dict):
        fail("outputs.component_plots must be a dictionary")
    for key in ["statistical", "unfolding", "experimental", "theory"]:
        if key not in component_plots:
            fail(f"component_plots missing key: {key}")
        require_file(component_plots[key])

    cov_stat = load_csv_matrix(outputs["cov_stat"])
    cov_iter = load_csv_matrix(outputs["cov_iter"])
    cov_exp = load_csv_matrix(outputs["cov_exp"])
    cov_theory = load_csv_matrix(outputs["cov_theory"])
    cov_had = None
    cov_had_key = "cov_hadronic"
    if cov_had_key in outputs:
        require_file(outputs[cov_had_key])
        cov_had = load_csv_matrix(outputs[cov_had_key])
    elif args.strict_fit:
        fail("strict-fit mode requires outputs.cov_hadronic")
    else:
        print("WARNING: outputs.cov_hadronic missing; assuming legacy summary format", file=sys.stderr)
    cov_isr = None
    cov_isr_key = "cov_isr"
    if cov_isr_key in outputs:
        require_file(outputs[cov_isr_key])
        cov_isr = load_csv_matrix(outputs[cov_isr_key])
    cov_total = load_csv_matrix(outputs["cov_total"])
    corr_total = load_csv_matrix(outputs["corr_total"])
    cov_total_fit = None
    corr_total_fit = None
    if "cov_total_fitwindow" in outputs and "corr_total_fitwindow" in outputs:
        require_file(outputs["cov_total_fitwindow"])
        require_file(outputs["corr_total_fitwindow"])
        cov_total_fit = load_csv_matrix(outputs["cov_total_fitwindow"])
        corr_total_fit = load_csv_matrix(outputs["corr_total_fitwindow"])

    for name, mat in [
        ("cov_stat", cov_stat),
        ("cov_iter", cov_iter),
        ("cov_exp", cov_exp),
        ("cov_theory", cov_theory),
        ("cov_total", cov_total),
        ("corr_total", corr_total),
    ]:
        check_symmetric(name, mat, args.sym_tol)
    if cov_had is not None:
        check_symmetric("cov_hadronic", cov_had, args.sym_tol)
    if cov_isr is not None:
        check_symmetric("cov_isr", cov_isr, args.sym_tol)
    if cov_total_fit is not None:
        check_symmetric("cov_total_fitwindow", cov_total_fit, args.sym_tol)
    if corr_total_fit is not None:
        check_symmetric("corr_total_fitwindow", corr_total_fit, args.sym_tol)

    # Correlation sanity: bounded, and unit diagonal for bins with positive variance.
    if np.max(np.abs(corr_total)) > 1.0 + args.corr_tol:
        fail("corr_total has entries outside [-1, 1] beyond tolerance")
    if corr_total_fit is not None and np.max(np.abs(corr_total_fit)) > 1.0 + args.corr_tol:
        fail("corr_total_fitwindow has entries outside [-1, 1] beyond tolerance")

    var = np.diag(cov_total)
    positive = var > 0.0
    if np.count_nonzero(positive) == 0:
        fail("cov_total has no positive diagonal entries")
    diag_corr = np.diag(corr_total)
    diag_delta = np.max(np.abs(diag_corr[positive] - 1.0))
    if diag_delta > 1e-6:
        fail(f"corr_total diagonal deviates from 1 in positive-variance bins: {diag_delta:.3e}")

    # Check covariance component closure.
    cov_total_model = cov_stat + cov_iter + cov_exp + cov_theory
    if cov_had is not None:
        cov_total_model = cov_total_model + cov_had
    if cov_isr is not None:
        cov_total_model = cov_total_model + cov_isr
    closure_delta = float(np.max(np.abs(cov_total - cov_total_model)))
    if closure_delta > 1e-10:
        fail(f"cov_total is inconsistent with covariance components: max residual {closure_delta:.3e}")

    # If nominal ROOT covariance exists, expect some statistical off-diagonal content.
    nominal_root = os.path.join(base_dir, "nominal", f"unfolded_nominal_iter{summary.get('nominal_iteration', 5)}.root")
    require_file(nominal_root)
    tf = ROOT.TFile.Open(nominal_root, "READ")
    has_root_cov = False
    if tf and (not tf.IsZombie()):
        has_root_cov = bool(tf.Get("unfold_covariance"))
        tf.Close()

    offdiag_stat = cov_stat - np.diag(np.diag(cov_stat))
    nonzero_offdiag_stat = int(np.count_nonzero(np.abs(offdiag_stat) > 0.0))
    if has_root_cov and nonzero_offdiag_stat == 0:
        fail("cov_stat is diagonal despite presence of ROOT unfold_covariance")

    response_diag_fraction = float(diagnostics["response_diagonal_fraction"])
    if not (0.0 <= response_diag_fraction <= 1.0):
        fail(
            f"diagnostics.response_diagonal_fraction out of range [0,1]: {response_diag_fraction}"
        )

    # Fit-readiness diagnostics.
    zero_variance_bins = int(np.count_nonzero(var <= 0.0))
    eigvals = np.linalg.eigvalsh(cov_total)
    min_eig = float(np.min(eigvals)) if eigvals.size else 0.0
    positive_eigs = eigvals[eigvals > 0.0]
    condition_number = math.inf
    if positive_eigs.size > 0:
        condition_number = float(np.max(positive_eigs) / np.min(positive_eigs))

    print(f"cov_total zero/non-positive variance bins: {zero_variance_bins}")
    print(f"cov_total minimum eigenvalue: {min_eig:.6e}")
    print(f"cov_total positive-spectrum condition number: {condition_number:.6e}")
    print(f"cov_total closure residual: {closure_delta:.3e}")

    if args.strict_fit:
        if cov_total_fit is None:
            fail("strict-fit mode requires cov_total_fitwindow")
        fit_var = np.diag(cov_total_fit)
        fit_zero_variance_bins = int(np.count_nonzero(fit_var <= 0.0))
        fit_eigs = np.linalg.eigvalsh(cov_total_fit)
        fit_min_eig = float(np.min(fit_eigs)) if fit_eigs.size else 0.0
        fit_pos_eigs = fit_eigs[fit_eigs > 0.0]
        fit_condition_number = math.inf
        if fit_pos_eigs.size > 0:
            fit_condition_number = float(np.max(fit_pos_eigs) / np.min(fit_pos_eigs))

        print(f"cov_total_fitwindow zero/non-positive variance bins: {fit_zero_variance_bins}")
        print(f"cov_total_fitwindow minimum eigenvalue: {fit_min_eig:.6e}")
        print(f"cov_total_fitwindow positive-spectrum condition number: {fit_condition_number:.6e}")

        if fit_zero_variance_bins > args.max_zero_variance_bins:
            fail(
                f"strict-fit check failed: zero/non-positive variance bins "
                f"{fit_zero_variance_bins} > allowed {args.max_zero_variance_bins}"
            )
        if fit_min_eig < -1e-12:
            fail(f"strict-fit check failed: covariance has negative eigenvalue {fit_min_eig:.3e}")
        if math.isfinite(fit_condition_number) and fit_condition_number > args.max_condition_number:
            fail(
                f"strict-fit check failed: condition number {fit_condition_number:.3e} "
                f"> allowed {args.max_condition_number:.3e}"
            )

    print(f"Validated summary outputs: {summary_path}")
    print(f"cov_stat off-diagonal non-zero entries: {nonzero_offdiag_stat}")
    return 0


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
