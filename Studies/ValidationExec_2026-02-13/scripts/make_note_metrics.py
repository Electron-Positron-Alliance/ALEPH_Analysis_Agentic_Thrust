#!/usr/bin/env python3
"""Generate traceable metrics and LaTeX table fragments for the analysis note."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from typing import Dict, List, Tuple

import ROOT


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=False)


def load_hist(root_path: str, hist_name: str):
    tf = ROOT.TFile.Open(root_path, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"failed to open ROOT file: {root_path}")
    obj = tf.Get(hist_name)
    if not obj:
        tf.Close()
        raise KeyError(f"missing histogram '{hist_name}' in {root_path}")
    h = obj.Clone(f"{hist_name}_clone")
    h.SetDirectory(0)
    tf.Close()
    return h


def response_diag_fraction(h2) -> float:
    nbx = h2.GetNbinsX()
    nby = h2.GetNbinsY()
    n = min(nbx, nby)
    diag = 0.0
    total = 0.0
    for i in range(1, nbx + 1):
        for j in range(1, nby + 1):
            v = float(h2.GetBinContent(i, j))
            total += v
            if i == j:
                diag += v
    if total <= 0.0:
        return 0.0
    return diag / total


def mean_abs_offdiag_corr(h2, min_bin_sep: int = 1) -> float:
    nbx = h2.GetNbinsX()
    nby = h2.GetNbinsY()
    n = min(nbx, nby)
    vals: List[float] = []
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i == j:
                continue
            if abs(i - j) < min_bin_sep:
                continue
            vals.append(abs(float(h2.GetBinContent(i, j))))
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def hist_to_array(h1) -> List[float]:
    return [float(h1.GetBinContent(b)) for b in range(1, h1.GetNbinsX() + 1)]


def variation_fractional_shift(var_hist, nom_hist) -> List[float]:
    out = []
    nb = min(var_hist.GetNbinsX(), nom_hist.GetNbinsX())
    for b in range(1, nb + 1):
        nom = float(nom_hist.GetBinContent(b))
        var = float(var_hist.GetBinContent(b))
        if nom != 0.0:
            out.append((var - nom) / nom)
        else:
            out.append(0.0)
    return out


def quad_sum(values: List[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


def build_method_config_table(path: str, cfg: dict, nominal_iter: int) -> None:
    rows = [
        ("Observable", "Thrust $T$"),
        ("Range", f"${cfg['xmin']:.1f} \\le T < {cfg['xmax']:.1f}$"),
        ("Binning", f"{int(cfg['bins'])} uniform bins"),
        ("Reco/gen matching key", "\\texttt{uniqueID}"),
        ("Reco selection branch", "\\texttt{passEventSelection}"),
        ("Nominal IBU iterations", str(int(nominal_iter))),
        ("Hadronic correction", "enabled ($N_{\\mathrm{genBefore}}/N_{\\mathrm{gen}}$)"),
        ("Statistical covariance input", "measured-bin diagonal covariance"),
    ]

    lines = [
        "\\begin{table}[t!]",
        "\\centering",
        "\\begin{tabular}{l l}",
        "\\hline",
        "Item & Nominal configuration \\\\",
        "\\hline",
    ]
    for k, v in rows:
        lines.append(f"{k} & {v} \\\\")
    lines += [
        "\\hline",
        "\\end{tabular}",
        "\\caption{Nominal analysis configuration used in the thrust Iterative Bayesian Unfolding workflow.}",
        "\\label{tab:method_config}",
        "\\end{table}",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def build_systematics_definition_table(path: str) -> None:
    lines = [
        "\\begin{table}[t!]",
        "\\centering",
        "\\begin{tabular}{p{0.25\\textwidth}p{0.33\\textwidth}p{0.34\\textwidth}}",
        "\\hline",
        "Group & Source & Combination in total \\\\",
        "\\hline",
        "Track/event selection & \\texttt{ntpc7}, \\texttt{pt04}, \\texttt{ech10}, \\texttt{with\\_met} & quadrature within group \\\\",
        "Neutral-response modeling & \\texttt{nes\\_up}/\\texttt{nes\\_down}, \\texttt{ner} & max(|up|,|down|) then quadrature \\\\",
        "Stress-test variation & \\texttt{no\\_neutrals} & reported separately (not merged) \\\\",
        "\\hline",
        "\\end{tabular}",
        "\\caption{Systematic-source grouping and nominal combination policy used in this note.}",
        "\\label{tab:systematics_definition}",
        "\\end{table}",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def build_results_key_metrics_table(path: str, result_summary: dict) -> None:
    nominal_iter = int(result_summary["nominal_iteration"])
    rec = result_summary["nominal_iteration_metrics"]
    matrix = result_summary["matrix_metrics"]
    syst = result_summary["systematics_combination"]

    lines = [
        "\\begin{table}[t!]",
        "\\centering",
        "\\begin{tabular}{l c}",
        "\\hline",
        "Metric & Value \\\\",
        "\\hline",
        f"Nominal iterations $N_{{\\mathrm{{iter}}}}$ & {nominal_iter} \\\\",
        f"Refold $\\chi^2/\\mathrm{{ndf}}$ ($1/N\\,dN/dT$) & {rec['refold_diffxsec_chi2_ndf']:.3f} \\\\",
        f"Toy-closure mean $\\chi^2/\\mathrm{{ndf}}$ & {rec['toy_closure_mean_chi2_ndf']:.3f} \\\\",
        f"Response diagonal fraction & {matrix['response_diag_fraction']:.3f} \\\\",
        f"Mean $|\\rho_{{ij}}|$ for $|i-j|\\geq 10$ & {matrix['mean_abs_offdiag_corr_sep_ge_10']:.3e} \\\\",
        f"Mean total systematic fraction (combined groups) & {100.0*syst['mean_abs_total_syst_fraction']:.3f}\\% \\\\",
        "\\hline",
        "\\end{tabular}",
        "\\caption{Key metrics used in the nominal thrust result discussion.}",
        "\\label{tab:results_key_metrics}",
        "\\end{table}",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def read_nominal_iteration_metrics(iter_csv_path: str, iter_summary: dict, nominal_iter: int) -> Tuple[dict, str]:
    if os.path.exists(iter_csv_path):
        with open(iter_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    if int(row["iteration"]) != nominal_iter:
                        continue
                except Exception:
                    continue
                parsed = {"iteration": nominal_iter}
                for k, v in row.items():
                    if k == "iteration":
                        continue
                    try:
                        parsed[k] = float(v)
                    except Exception:
                        parsed[k] = v
                return parsed, iter_csv_path

    rec = dict(iter_summary["recommendation"])
    rec["iteration"] = int(rec["iteration"])
    return rec, "iteration_scan_summary.json:recommendation"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-dir", default="Studies/ValidationExec_2026-02-13")
    p.add_argument("--config", default="Unfolding/unfold_config.json")
    p.add_argument("--tables-dir", default="AnalysisNote/tables")
    p.add_argument("--nominal-iter", type=int, default=None)
    p.add_argument("--nominal-root", default=None)
    p.add_argument("--matrix-dir", default=None)
    args = p.parse_args()

    base_dir = os.path.abspath(args.base_dir)
    tables_dir = os.path.abspath(args.tables_dir)
    os.makedirs(tables_dir, exist_ok=True)
    note_metrics_dir = os.path.join(base_dir, "note_metrics")
    os.makedirs(note_metrics_dir, exist_ok=True)

    iter_summary_path = os.path.join(base_dir, "iteration_scan", "iteration_scan_summary.json")
    iter_csv_path = os.path.join(base_dir, "iteration_scan", "iteration_scan.csv")
    syst_summary_path = os.path.join(base_dir, "systematics_full_1994", "systematics_summary.json")

    cfg = read_json(os.path.abspath(args.config))
    iter_summary = read_json(iter_summary_path)
    syst_summary = read_json(syst_summary_path)

    if args.nominal_iter is not None:
        nominal_iter = int(args.nominal_iter)
    else:
        nominal_iter = int(cfg.get("iterations", iter_summary["recommendation"]["iteration"]))

    default_nominal_root = os.path.join(base_dir, f"unfolded_nominal_iter{nominal_iter}_cov.root")
    fallback_nominal_root = os.path.join(base_dir, "unfolded_nominal_iter7_cov.root")
    if args.nominal_root:
        nominal_root = os.path.abspath(args.nominal_root)
    elif os.path.exists(default_nominal_root):
        nominal_root = default_nominal_root
    else:
        nominal_root = fallback_nominal_root

    default_matrix_dir = os.path.join(base_dir, f"matrices_nominal_iter{nominal_iter}")
    fallback_matrix_dir = os.path.join(base_dir, "matrices_nominal_iter7")
    if args.matrix_dir:
        matrix_dir = os.path.abspath(args.matrix_dir)
    elif os.path.exists(default_matrix_dir):
        matrix_dir = default_matrix_dir
    else:
        matrix_dir = fallback_matrix_dir

    h_resp_counts = load_hist(nominal_root, "response_counts")
    h_corr = load_hist(nominal_root, "unfold_correlation")
    h_cov = load_hist(nominal_root, "unfold_covariance")

    nominal_metrics, nominal_metrics_source = read_nominal_iteration_metrics(
        iter_csv_path, iter_summary, nominal_iter
    )

    matrix_metrics = {
        "response_diag_fraction": response_diag_fraction(h_resp_counts),
        "mean_abs_offdiag_corr_sep_ge_1": mean_abs_offdiag_corr(h_corr, min_bin_sep=1),
        "mean_abs_offdiag_corr_sep_ge_10": mean_abs_offdiag_corr(h_corr, min_bin_sep=10),
        "cov_trace": sum(float(h_cov.GetBinContent(i, i)) for i in range(1, h_cov.GetNbinsX() + 1)),
    }

    # Systematics combination (fractional, bin-by-bin)
    syst_dir = os.path.join(base_dir, "systematics_full_1994")
    nominal_syst_root = os.path.join(syst_dir, "unfolded_nominal.root")
    h_nom = load_hist(nominal_syst_root, "unfolded_corrected")

    var_hists: Dict[str, object] = {}
    for row in syst_summary["rows"]:
        var = row["variation"]
        path = os.path.join(syst_dir, f"unfolded_{var}.root")
        if os.path.exists(path):
            var_hists[var] = load_hist(path, "unfolded_corrected")

    frac_shifts: Dict[str, List[float]] = {}
    for var, h in var_hists.items():
        if var == "nominal":
            continue
        frac_shifts[var] = variation_fractional_shift(h, h_nom)

    nbins = h_nom.GetNbinsX()

    def get_shift(var: str, ibin: int) -> float:
        vals = frac_shifts.get(var, [0.0] * nbins)
        return abs(vals[ibin])

    track_event_vars = ["ntpc7", "pt04", "ech10", "with_met"]
    nes_pair = ("nes_up", "nes_down")

    track_event_env = []
    neutral_env = []
    total_syst = []
    stress_no_neutrals = []
    for i in range(nbins):
        te = quad_sum([get_shift(v, i) for v in track_event_vars])
        nes = max(get_shift(nes_pair[0], i), get_shift(nes_pair[1], i))
        ner = get_shift("ner", i)
        nr = quad_sum([nes, ner])
        tot = quad_sum([te, nr])
        track_event_env.append(te)
        neutral_env.append(nr)
        total_syst.append(tot)
        stress_no_neutrals.append(get_shift("no_neutrals", i))

    section6_summary = {
        "group_definition": {
            "track_event_selection": track_event_vars,
            "neutral_response_pair": list(nes_pair),
            "neutral_response_single": ["ner"],
            "stress_test_reported_separately": ["no_neutrals"],
        },
        "combination_recipe": {
            "nes_pair": "max(abs(nes_up), abs(nes_down))",
            "track_event_group": "quadrature(ntpc7, pt04, ech10, with_met)",
            "neutral_group": "quadrature(nes_pair, ner)",
            "total_systematic": "quadrature(track_event_group, neutral_group)",
            "stress_test": "no_neutrals is reported but excluded from nominal total",
        },
        "mean_abs_track_event_fraction": sum(track_event_env) / len(track_event_env),
        "mean_abs_neutral_response_fraction": sum(neutral_env) / len(neutral_env),
        "mean_abs_total_syst_fraction": sum(total_syst) / len(total_syst),
        "max_abs_total_syst_fraction": max(total_syst),
        "mean_abs_no_neutrals_fraction": sum(stress_no_neutrals) / len(stress_no_neutrals),
        "max_abs_no_neutrals_fraction": max(stress_no_neutrals),
        "rows_from_existing_summary": syst_summary["rows"],
    }

    # Build section 5 summary
    section5_summary = {
        "configuration": {
            "observable": cfg.get("data_branch", "Thrust"),
            "bins": int(cfg["bins"]),
            "xmin": float(cfg["xmin"]),
            "xmax": float(cfg["xmax"]),
            "id_branch": cfg.get("id_branch", "uniqueID"),
            "selection_branch": cfg.get("selection_branch", "passEventSelection"),
            "nominal_iterations": nominal_iter,
        },
        "matrix_metrics": matrix_metrics,
        "sources": {
            "config": os.path.abspath(args.config),
            "iteration_scan_summary": iter_summary_path,
            "iteration_scan_csv": iter_csv_path,
            "nominal_root": nominal_root,
            "matrix_dir": matrix_dir,
        },
    }

    section7_summary = {
        "nominal_iteration": nominal_iter,
        "nominal_iteration_metrics": nominal_metrics,
        "nominal_iteration_metrics_source": nominal_metrics_source,
        "iteration_summary": iter_summary,
        "matrix_metrics": matrix_metrics,
        "systematics_combination": {
            "mean_abs_total_syst_fraction": section6_summary["mean_abs_total_syst_fraction"],
            "max_abs_total_syst_fraction": section6_summary["max_abs_total_syst_fraction"],
        },
        "products": {
            "nominal_root": nominal_root,
            "iteration_scan_dir": os.path.join(base_dir, "iteration_scan"),
            "systematics_dir": os.path.join(base_dir, "systematics_full_1994"),
            "matrix_dir": matrix_dir,
        },
    }

    write_json(os.path.join(note_metrics_dir, "section5_metrics.json"), section5_summary)
    write_json(os.path.join(note_metrics_dir, "section6_systematics_summary.json"), section6_summary)
    write_json(os.path.join(note_metrics_dir, "section7_results_summary.json"), section7_summary)

    build_method_config_table(
        os.path.join(tables_dir, "method_config_table.tex"), cfg, nominal_iter
    )
    build_systematics_definition_table(os.path.join(tables_dir, "systematics_definition_table.tex"))
    build_results_key_metrics_table(
        os.path.join(tables_dir, "results_key_metrics_table.tex"),
        section7_summary,
    )

    print(f"Wrote note metrics to: {note_metrics_dir}")
    print(f"Wrote tables to: {tables_dir}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    main()
