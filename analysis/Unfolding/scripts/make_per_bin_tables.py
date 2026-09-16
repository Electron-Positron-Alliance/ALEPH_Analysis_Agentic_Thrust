#!/usr/bin/env python3
"""
Regenerate the three per-bin uncertainty LaTeX tables.

  per_bin_uncertainty_table.tex             -- our breakdown, one column per component
  per_bin_uncertainty_table_aleph.tex       -- ours vs ALEPH 2004 value and total
  per_bin_uncertainty_table_comparison.tex  -- ours vs ALEPH 2004, component by component

Per-bin components are computed with the helpers in
Studies/Phase2_Checks_2026-03-03/scripts/per_bin_uncertainty_plot.py, so these
tables and the per_bin_uncertainty_*.pdf figures cannot drift apart. The ALEPH
2004 side uses load_aleph_2004_result from build_prelim_uncertainty_summary.py.

Bins with a zero unfolded spectrum are emitted commented out, matching the
committed tables.

Usage (from repo root):
    python analysis/Unfolding/scripts/make_per_bin_tables.py \
        --result-dir analysis/Studies/PreliminaryResult/<run> \
        --aleph-csv <HEPData-ins636645-v1-Table_54.csv> \
        --outdir tables
"""

import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "Studies",
                                "Phase2_Checks_2026-03-03", "scripts"))

from build_prelim_uncertainty_summary import load_aleph_2004_result  # noqa: E402
from per_bin_uncertainty_plot import (  # noqa: E402
    cov_to_frac, get_hist_array, to_diffxsec,
)

# Every column is the diagonal of the matching cov_*.csv, which makes Total the
# quadrature of the shown columns exactly: cov_total is their sum (verified to
# 7e-12). Note cov_exp is the quadrature of the track/event and neutral groups,
# not their envelope, so it differs from the envelope curves the per-bin figures
# draw; cov_iter and cov_theory equal their envelopes exactly.
COMPONENTS = ["stat", "mcstat", "iter", "exp", "theory", "hadronic", "isr", "total"]

# The paper reports the range common to both measurements (Results.tex: T >= 0.58).
# Populated bins below it are emitted commented out, as in the committed tables.
T_REPORT_MIN = 0.58


def fmt_value(v):
    """Match the committed tables: 4 significant digits, LaTeX scientific below 1e-4."""
    if v <= 0:
        return r"\multicolumn{1}{c}{---}"
    s = f"{v:.4g}"
    if "e" in s:
        mant, exp = s.split("e")
        return rf"${float(mant):.2f}\times10^{{{int(exp)}}}$"
    return s


def load_components(result_dir):
    rdir = result_dir.rstrip("/") + "/"
    summary = rdir + "summary/"
    nom_raw = get_hist_array(rdir + "nominal/unfolded_nominal_iter5.root")
    nom = to_diffxsec(nom_raw)
    nb = len(nom)

    def cov(name):
        path = summary + f"cov_{name}.csv"
        if not os.path.exists(path):
            raise FileNotFoundError(f"missing {path}; run build_prelim_uncertainty_summary.py")
        return cov_to_frac(path, nom, n_bins=nb)

    comp = {name: cov(name) for name in COMPONENTS}

    # Total must be the quadrature of the components, or the table cannot be
    # checked by a reader adding the columns up.
    quad = np.sqrt(sum(comp[k] ** 2 for k in COMPONENTS if k != "total"))
    resid = float(np.abs(quad - comp["total"]).max())
    if resid > 1e-6:
        raise ValueError(
            f"Total is not the quadrature of the components (max residual {resid:.3e})"
        )
    print(f"Total vs quadrature of components: max residual {resid:.2e}")
    return nom, comp


def bin_edges(n, lo=0.5, hi=1.0):
    w = (hi - lo) / n
    return [(lo + i * w, lo + (i + 1) * w) for i in range(n)]


def write_table(path, header, body_rows, caption, label, pre="", post=""):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\\begin{table}[t!]\n\\centering\n\\scriptsize\n")
        f.write(pre)
        f.write(header)
        f.write("\\hline\n")
        for r in body_rows:
            f.write(r + "\n")
        f.write("\\hline\n\\end{tabular}\n")
        f.write(post)
        f.write("\\normalsize\n")
        f.write(f"\\caption{{{caption}}}\n\\label{{{label}}}\n\\end{{table}}")
    print(f"wrote {path}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result-dir", required=True)
    p.add_argument("--aleph-csv", required=True)
    p.add_argument("--outdir", default="tables")
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    nom, comp = load_components(args.result_dir)
    edges = bin_edges(len(nom))
    aleph = load_aleph_2004_result(args.aleph_csv)
    a_by_lo = {round(float(lo), 4): i for i, lo in enumerate(aleph["lows"])}
    pct = lambda a, i: 100.0 * a[i]  # noqa: E731

    # ---- Table 1: our per-bin breakdown -----------------------------------
    rows = []
    for i, (lo, hi) in enumerate(edges):
        if nom[i] <= 0:
            continue
        c = "" if lo >= T_REPORT_MIN - 1e-9 else "% "
        rows.append(
            f"{c}{{[{lo:.2f},{hi:.2f})}} & {fmt_value(nom[i])} & "
            f"{pct(comp['stat'],i):.1f} & {pct(comp['mcstat'],i):.1f} & "
            f"{pct(comp['iter'],i):.1f} & "
            f"{pct(comp['exp'],i):.1f} & {pct(comp['theory'],i):.1f} & "
            f"{pct(comp['hadronic'],i):.1f} & {pct(comp['isr'],i):.1f} & "
            f"{pct(comp['total'],i):.1f} \\\\"
        )
    write_table(
        os.path.join(args.outdir, "per_bin_uncertainty_table.tex"),
        "\\begin{tabular}{c r c c c c c c c c}\n\\hline\n"
        "$T$ range & $(1/\\sigma)\\,\\mathrm{d}\\sigma/\\mathrm{d}T$ & Stat. & MC stat. & Iter. & Exp. & Theory & Had.\\ corr. & ISR & Total \\\\\n"
        " & & [\\%] & [\\%] & [\\%] & [\\%] & [\\%] & [\\%] & [\\%] & [\\%] \\\\\n",
        rows,
        "Per-bin fractional uncertainties for bins with non-zero unfolded spectrum. "
        "The second column is the nominal $(1/\\sigma)\\,\\mathrm{d}\\sigma/\\mathrm{d}T$; "
        "the rest are fractional uncertainties in percent. \\textit{Stat.} is the data "
        "statistical uncertainty and \\textit{MC stat.} the response-matrix statistical "
        "uncertainty from the Poisson bootstrap. \\textit{Exp.} is the total "
        "experimental component, \\textit{Had.\\ corr.} the hadronic event-selection "
        "correction, and \\textit{ISR} the initial-state-radiation correction.",
        "tab:per_bin_uncertainty",
    )

    # ---- Table 2: ours vs ALEPH 2004, value and total ----------------------
    rows = []
    for i, (lo, hi) in enumerate(edges):
        if nom[i] <= 0:
            continue
        j = a_by_lo.get(round(lo, 4))
        if j is None:
            av, au = r"\multicolumn{1}{c}{---}", r"\multicolumn{1}{c}{---}"
        else:
            av = fmt_value(float(aleph["values"][j]))
            au = f"{100.0*aleph['total'][j]/aleph['values'][j]:.1f}" if aleph["values"][j] > 0 else r"\multicolumn{1}{c}{---}"
        c = "" if lo >= T_REPORT_MIN - 1e-9 else "% "
        rows.append(f"{c}{{[{lo:.2f},{hi:.2f})}} & {fmt_value(nom[i])} & "
                    f"{pct(comp['total'],i):.1f} & {av} & {au} \\\\")
    write_table(
        os.path.join(args.outdir, "per_bin_uncertainty_table_aleph.tex"),
        "\\begin{tabular}{c r r r r}\n\\hline\n"
        "$T$ range & Our $(1/\\sigma)\\,\\mathrm{d}\\sigma/\\mathrm{d}T$ & Our total unc.\\ [\\%] & "
        "ALEPH 2004 $(1/\\sigma)\\,\\mathrm{d}\\sigma/\\mathrm{d}T$ & ALEPH 2004 total unc.\\ [\\%] \\\\\n",
        rows,
        "Comparison of the nominal unfolded $(1/\\sigma)\\,\\mathrm{d}\\sigma/\\mathrm{d}T$ and total "
        "fractional uncertainty with the published ALEPH 2004 result (HEPData ins:636645, "
        "Table~54) for bins with non-zero unfolded spectrum. The ALEPH 2004 total uncertainty "
        "combines statistical, sys$_1$, and sys$_2$ components in quadrature.",
        "tab:per_bin_uncertainty_aleph",
    )

    # ---- Table 3: component-by-component comparison ------------------------
    rows = []
    for i, (lo, hi) in enumerate(edges):
        if nom[i] <= 0:
            continue
        j = a_by_lo.get(round(lo, 4))
        dash = r"\multicolumn{1}{c}{---}"
        if j is None:
            a = [dash] * 5
        else:
            v = float(aleph["values"][j])
            a = [fmt_value(v)] + [
                (f"{100.0*aleph[k][j]/v:.1f}" if v > 0 else dash)
                for k in ("stat", "sys1", "sys2", "total")
            ]
        c = "" if lo >= T_REPORT_MIN - 1e-9 else "% "
        rows.append(
            f"{c}{{[{lo:.2f},{hi:.2f})}} & {fmt_value(nom[i])} & {a[0]} & "
            f"{pct(comp['stat'],i):.1f} & {a[1]} & {pct(comp['exp'],i):.1f} & {a[2]} & "
            f"{pct(comp['theory'],i):.1f} & {a[3]} & {pct(comp['total'],i):.1f} & {a[4]} \\\\"
        )
    write_table(
        os.path.join(args.outdir, "per_bin_uncertainty_table_comparison.tex"),
        "\\begin{tabular}{c  r r r r  r r r r  r r}\n\\hline\n"
        "& \\multicolumn{2}{c}{$(1/\\sigma)\\,\\mathrm{d}\\sigma/\\mathrm{d}T$}\n"
        " & \\multicolumn{2}{c}{Stat.\\ [\\%]}\n"
        " & \\multicolumn{2}{c}{Exp.\\ / Sys.\\,1 [\\%]}\n"
        " & \\multicolumn{2}{c}{Theory\\,/ Sys.\\,2 [\\%]}\n"
        " & \\multicolumn{2}{c}{Total [\\%]} \\\\\n"
        "\\cline{2-3}\\cline{4-5}\\cline{6-7}\\cline{8-9}\\cline{10-11}\n"
        "$T$ range & Ours & ALEPH & Ours & ALEPH & Ours & ALEPH & Ours & ALEPH & Ours & ALEPH \\\\\n",
        rows,
        "Per-bin fractional uncertainty breakdown comparison between this analysis and the "
        "published ALEPH 2004 result (HEPData ins:636645, Table~54). For this analysis, "
        "\\textit{Stat.} is derived from the RooUnfold covariance, \\textit{Exp.} is the "
        "envelope of all experimental track/event and neutral variations, and \\textit{Theory} "
        "is the max envelope of the three generator reweightings. For ALEPH 2004, Sys.\\,1 and "
        "Sys.\\,2 correspond to the two systematic components provided in the HEPData table. "
        "All values are absolute fractional uncertainties in percent; Total combines all "
        "components in quadrature.",
        "tab:per_bin_uncertainty_breakdown_comparison",
        pre="\\resizebox{\\textwidth}{!}{%\n",
        post="}% end resizebox\n",
    )


if __name__ == "__main__":
    main()
