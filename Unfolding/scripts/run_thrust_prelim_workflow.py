#!/usr/bin/env python3
"""Execute the thrust preliminary workflow: nominal, iterations, experimental, and theory runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import date, datetime, timezone


CUT_BASED_VARIATIONS = ["ntpc7", "pt04", "ech10", "no_neutrals", "with_met"]
NEUTRAL_RESPONSE_VARIATIONS = ["nes_up", "nes_down", "ner"]
THEORY_WEIGHT_FILES = {
    "pythia8": "Reweight_Step2_Ensemble_Pythia8.npy",
    "herwig": "Reweight_Step2_Ensemble_Herwig.npy",
    "sherpa": "Reweight_Step2_Ensemble_Sherpa.npy",
}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default="Unfolding/unfold_config.json")
    p.add_argument("--python", default="python3")
    p.add_argument(
        "--conda-env",
        default="py312",
        help="If non-empty, run each python command through conda run -n <env> --no-capture-output",
    )
    p.add_argument("--outdir", default=None)
    p.add_argument("--nominal-iter", type=int, default=5)
    p.add_argument("--iter-down", type=int, default=4)
    p.add_argument("--iter-up", type=int, default=6)
    p.add_argument("--skip-nominal", action="store_true")
    p.add_argument("--skip-iteration", action="store_true")
    p.add_argument("--skip-experimental", action="store_true")
    p.add_argument("--skip-theory", action="store_true")
    p.add_argument("--skip-plots", action="store_true")
    p.add_argument("--fail-fast", action="store_true")
    p.add_argument(
        "--theory-weights-dir",
        default=None,
        help=(
            "Directory containing theory reweighting arrays "
            "(required unless --skip-theory is set)."
        ),
    )
    return p.parse_args()


def run_cmd(cmd: list[str], cwd: str) -> int:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=False).returncode


def python_prefix(args) -> list[str]:
    if args.conda_env:
        return ["conda", "run", "--no-capture-output", "-n", args.conda_env, args.python]
    return [args.python]


def _safe_cmd_output(cmd: list[str], cwd: str) -> str:
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


def collect_provenance(repo_root: str) -> dict[str, object]:
    root_version = "unavailable"
    roounfold_version = "unavailable"
    roounfold_library = "unavailable"
    try:
        import ROOT  # type: ignore

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


def extract_theory_weight_diagnostics_from_root(root_path: str) -> dict[str, object]:
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
    try:
        import ROOT  # type: ignore

        tf = ROOT.TFile.Open(root_path, "READ")
        if not tf or tf.IsZombie():
            out["error"] = "failed_to_open_root"
            return out
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
    except Exception as exc:
        out["error"] = str(exc)
        return out


def variation_file(nominal_path: str, variation: str) -> str:
    if variation == "nominal":
        return nominal_path
    dirname, basename = os.path.split(nominal_path)
    token = "_nominal_"
    if token not in basename:
        raise ValueError(
            f"Cannot derive variation path for '{variation}': expected '{token}' in {basename}"
        )
    varied = basename.replace(token, f"_{variation}_", 1)
    return os.path.join(dirname, varied)


def load_cfg(cfg_path: str) -> dict:
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_cfg_path(cfg_path: str, value: str) -> str:
    if os.path.isabs(value):
        return value
    return os.path.abspath(os.path.join(os.path.dirname(cfg_path), value))


def ensure_exists(path: str, label: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label}: {path}")


def make_unfold_cmd(
    py_prefix: list[str],
    repo_root: str,
    cfg_path: str,
    out_root: str,
    overrides: dict[str, str | int | float | bool],
) -> list[str]:
    cmd = py_prefix + [
        os.path.join(repo_root, "Unfolding", "unfold_thrust.py"),
        "--config",
        cfg_path,
        "--set",
        f"out_root={out_root}",
    ]
    for k, v in overrides.items():
        cmd.extend(["--set", f"{k}={v}"])
    return cmd


def maybe_plot(py_prefix: list[str], repo_root: str, input_root: str, output_pdf: str, do_plot: bool) -> int:
    if not do_plot:
        return 0
    cmd = py_prefix + [
        os.path.join(repo_root, "Unfolding", "plot_unfolded.py"),
        "--input-root",
        input_root,
        "--output",
        output_pdf,
        "--unfolded-hist",
        "unfolded_corrected",
    ]
    return run_cmd(cmd, cwd=repo_root)


def main():
    args = parse_args()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cfg_path = os.path.abspath(args.config)
    cfg = load_cfg(cfg_path)

    if args.outdir is None:
        args.outdir = os.path.join(
            repo_root,
            "Studies",
            "PreliminaryResult",
            f"{date.today().isoformat()}_thrust_iter{args.nominal_iter}",
        )
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    if not args.skip_theory and not args.theory_weights_dir:
        raise ValueError(
            "Missing --theory-weights-dir. Provide the directory that contains "
            "Reweight_Step2_Ensemble_{Pythia8,Herwig,Sherpa}.npy, or set --skip-theory."
        )

    nominal_data = resolve_cfg_path(cfg_path, cfg["data_file"])
    nominal_reco = resolve_cfg_path(cfg_path, cfg["reco_mc_file"])
    nominal_gen = resolve_cfg_path(cfg_path, cfg["gen_mc_file"])

    ensure_exists(nominal_data, "nominal data")
    ensure_exists(nominal_reco, "nominal reco MC")
    ensure_exists(nominal_gen, "nominal gen MC")

    failures: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    py_prefix = python_prefix(args)

    def execute_step(group: str, tag: str, out_root: str, overrides: dict[str, object]):
        os.makedirs(os.path.dirname(out_root), exist_ok=True)
        cmd = make_unfold_cmd(
            py_prefix=py_prefix,
            repo_root=repo_root,
            cfg_path=cfg_path,
            out_root=out_root,
            overrides=overrides,
        )
        rc = run_cmd(cmd, cwd=os.path.dirname(cfg_path))
        rec = {
            "group": group,
            "tag": tag,
            "out_root": out_root,
            "overrides": overrides,
            "returncode": rc,
        }
        records.append(rec)
        if rc != 0:
            failures.append(rec)
            return
        rc_plot = maybe_plot(
            py_prefix=py_prefix,
            repo_root=repo_root,
            input_root=out_root,
            output_pdf=out_root.replace(".root", ".pdf"),
            do_plot=(not args.skip_plots),
        )
        rec["plot_returncode"] = rc_plot
        if rc_plot != 0:
            failures.append(rec)
        if group == "theory":
            rec["theory_weight_diagnostics"] = extract_theory_weight_diagnostics_from_root(
                out_root
            )

    if not args.skip_nominal:
        execute_step(
            group="nominal",
            tag=f"iter{args.nominal_iter}",
            out_root=os.path.join(outdir, "nominal", f"unfolded_nominal_iter{args.nominal_iter}.root"),
            overrides={
                "iterations": args.nominal_iter,
                "calculate_covariance": "true",
                "apply_hadronic_event_correction": "true",
                "apply_theory_event_weights": "false",
            },
        )
        if args.fail_fast and failures:
            raise RuntimeError(f"Workflow aborted after nominal failure: {failures[-1]}")

    if not args.skip_iteration:
        for it in [args.iter_down, args.iter_up]:
            execute_step(
                group="iteration",
                tag=f"iter{it}",
                out_root=os.path.join(outdir, "iteration", f"unfolded_iter{it}.root"),
                overrides={
                    "iterations": it,
                    "calculate_covariance": "false",
                    "apply_hadronic_event_correction": "true",
                    "apply_theory_event_weights": "false",
                },
            )
            if args.fail_fast and failures:
                raise RuntimeError(f"Workflow aborted after iteration failure: {failures[-1]}")

    if not args.skip_experimental:
        for variation in CUT_BASED_VARIATIONS + NEUTRAL_RESPONSE_VARIATIONS:
            reco_file = variation_file(nominal_reco, variation)
            data_file = nominal_data
            if variation in CUT_BASED_VARIATIONS:
                data_file = variation_file(nominal_data, variation)
            ensure_exists(reco_file, f"experimental reco file ({variation})")
            ensure_exists(data_file, f"experimental data file ({variation})")
            execute_step(
                group="experimental",
                tag=variation,
                out_root=os.path.join(outdir, "experimental", f"unfolded_{variation}.root"),
                overrides={
                    "reco_mc_file": reco_file,
                    "data_file": data_file,
                    "iterations": args.nominal_iter,
                    "calculate_covariance": "false",
                    "apply_hadronic_event_correction": "true",
                    "apply_theory_event_weights": "false",
                },
            )
            if args.fail_fast and failures:
                raise RuntimeError(
                    f"Workflow aborted after experimental variation failure: {failures[-1]}"
                )

    if not args.skip_theory:
        theory_weights_dir = os.path.abspath(args.theory_weights_dir)
        for theory_name, filename in THEORY_WEIGHT_FILES.items():
            weight_path = os.path.join(theory_weights_dir, filename)
            ensure_exists(weight_path, f"theory weight file ({theory_name})")
            execute_step(
                group="theory",
                tag=theory_name,
                out_root=os.path.join(outdir, "theory", f"unfolded_theory_{theory_name}.root"),
                overrides={
                    "iterations": args.nominal_iter,
                    "calculate_covariance": "false",
                    "apply_hadronic_event_correction": "true",
                    "apply_theory_event_weights": "true",
                    "theory_variation_weights_path": weight_path,
                    "strict_theory_weight_length": "true",
                    "normalize_weights_mean1": "true",
                },
            )
            if args.fail_fast and failures:
                raise RuntimeError(f"Workflow aborted after theory variation failure: {failures[-1]}")

    summary = {
        "config": cfg_path,
        "output_dir": outdir,
        "nominal_iteration": args.nominal_iter,
        "iteration_systematic": [args.iter_down, args.iter_up],
        "experimental_variations": CUT_BASED_VARIATIONS + NEUTRAL_RESPONSE_VARIATIONS,
        "theory_variations": list(THEORY_WEIGHT_FILES.keys()),
        "records": records,
        "failures": failures,
        "provenance": collect_provenance(repo_root),
    }
    summary_path = os.path.join(outdir, "workflow_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary: {summary_path}")

    if failures:
        print("Failures detected:")
        for fail in failures:
            print(f"  - {fail['group']}:{fail['tag']} rc={fail['returncode']}")
        sys.exit(1)

    print("Workflow completed successfully.")


if __name__ == "__main__":
    main()
