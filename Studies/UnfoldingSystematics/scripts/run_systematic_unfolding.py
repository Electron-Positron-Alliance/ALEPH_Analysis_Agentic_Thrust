#!/usr/bin/env python3
"""Thin wrapper: run unfold_thrust.py + plot_unfolded.py for all systematic variations."""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

CUT_BASED_VARIATIONS = {"ntpc7", "pt04", "ech10", "no_neutrals", "with_met"}
NEUTRAL_RESPONSE_VARIATIONS = {"nes_up", "nes_down", "ner"}


def parse_args():
    p = argparse.ArgumentParser(description="Run unfolding for all available systematic variations")
    p.add_argument("--config", default="Unfolding/unfold_config.json")
    p.add_argument("--temp-dir", default="DataProcessing/temp")
    p.add_argument("--outdir", default="Studies/UnfoldingSystematics/results")
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--include", nargs="*", default=None, help="Only run selected variations")
    p.add_argument(
        "--exclude",
        nargs="*",
        default=["no_event_sel"],
        help="Skip selected variations",
    )
    p.add_argument("--fail-fast", action="store_true", help="Stop on first failed variation")
    p.add_argument(
        "--allow-missing-cut-data",
        action="store_true",
        help="If a cut-based data variation file is missing, fall back to nominal data",
    )
    return p.parse_args()


def parse_variation(path):
    name = os.path.basename(path)
    m = re.match(r"^alephMCRecoAfterCutPaths_1994_thrust_(.+)_t\.root$", name)
    return m.group(1) if m else None


def discover_variations(temp_dir):
    out = []
    pattern = os.path.join(temp_dir, "alephMCRecoAfterCutPaths_1994_thrust_*_t.root")
    for path in sorted(glob.glob(pattern)):
        var = parse_variation(path)
        if var:
            out.append(var)
    uniq = sorted(set(out), key=lambda x: (x != "nominal", x))
    return uniq


def run_cmd(cmd, cwd):
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=False)


def variation_file(nominal_path, variation):
    if variation == "nominal":
        return nominal_path
    dirname, basename = os.path.split(nominal_path)
    token = "_nominal_"
    if token not in basename:
        raise ValueError(
            f"Cannot derive variation file for '{variation}': expected '{token}' in {basename}"
        )
    varied = basename.replace(token, f"_{variation}_", 1)
    return os.path.join(dirname, varied)


def main():
    args = parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    outdir = os.path.abspath(args.outdir)
    temp_dir = os.path.abspath(args.temp_dir)
    cfg = os.path.abspath(args.config)
    with open(cfg, "r", encoding="utf-8") as f:
        cfg_json = json.load(f)

    base_data_file = cfg_json["data_file"]
    base_reco_file = cfg_json["reco_mc_file"]

    # Resolve relative paths exactly like unfold_thrust.py does (relative to config dir).
    cfg_dir = os.path.dirname(cfg)
    if not os.path.isabs(base_data_file):
        base_data_file = os.path.abspath(os.path.join(cfg_dir, base_data_file))
    if not os.path.isabs(base_reco_file):
        base_reco_file = os.path.abspath(os.path.join(cfg_dir, base_reco_file))

    os.makedirs(outdir, exist_ok=True)

    variations = discover_variations(temp_dir)
    if args.include:
        include = set(args.include)
        variations = [v for v in variations if v in include]
    if args.exclude:
        exclude = set(args.exclude)
        variations = [v for v in variations if v not in exclude]

    if not variations:
        raise RuntimeError(f"No variations found in {temp_dir}")

    failures = []
    for var in variations:
        reco_file = variation_file(base_reco_file, var)
        data_file = variation_file(base_data_file, var)

        # Follow run_ibu.py logic:
        # - cut-based systematics: vary data + reco
        # - neutral response systematics: vary reco only, keep nominal data
        if var in NEUTRAL_RESPONSE_VARIATIONS:
            data_file = base_data_file
        elif var in CUT_BASED_VARIATIONS:
            pass
        else:
            # For any non-categorized variation, treat it like a reco-only variation.
            data_file = base_data_file

        if not os.path.exists(reco_file):
            failures.append((var, "input", 0))
            print(f"Missing reco variation file: {reco_file}")
            if args.fail_fast:
                break
            continue

        if var in CUT_BASED_VARIATIONS and not os.path.exists(data_file):
            msg = f"Missing cut-based data variation file: {data_file}"
            if args.allow_missing_cut_data:
                print(f"{msg} (falling back to nominal data)")
                data_file = base_data_file
            else:
                failures.append((var, "input", 0))
                print(msg)
                if args.fail_fast:
                    break
                continue

        out_root = os.path.join(outdir, f"unfolded_{var}.root")
        out_pdf = os.path.join(outdir, f"unfolded_{var}.pdf")

        unfold_cmd = [
            args.python,
            os.path.join(repo_root, "Unfolding", "unfold_thrust.py"),
            "--config",
            cfg,
            "--set",
            f"reco_mc_file={reco_file}",
            "--set",
            f"data_file={data_file}",
            "--set",
            f"out_root={out_root}",
        ]
        rc1 = run_cmd(unfold_cmd, cwd=os.path.dirname(cfg))
        if rc1.returncode != 0:
            failures.append((var, "unfold", rc1.returncode))
            if args.fail_fast:
                break
            continue

        plot_cmd = [
            args.python,
            os.path.join(repo_root, "Unfolding", "plot_unfolded.py"),
            "--input-root",
            out_root,
            "--output",
            out_pdf,
            "--unfolded-hist",
            "unfolded_corrected",
        ]
        rc2 = run_cmd(plot_cmd, cwd=repo_root)
        if rc2.returncode != 0:
            failures.append((var, "plot", rc2.returncode))
            if args.fail_fast:
                break

    print("Completed variations:", ", ".join(variations))
    if failures:
        print("Failures:")
        for var, step, code in failures:
            print(f"  {var}: {step} (exit {code})")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
