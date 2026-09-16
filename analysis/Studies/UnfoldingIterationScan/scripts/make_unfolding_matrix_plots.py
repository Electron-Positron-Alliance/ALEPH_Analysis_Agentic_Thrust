#!/usr/bin/env python3
"""Export unfolding matrix histograms from a ROOT file to PDF plots."""

import argparse
import csv
import os
import sys

import ROOT


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", required=True, help="ROOT file from unfold_thrust.py")
    p.add_argument("--outdir", required=True, help="Output directory for PDF plots")
    p.add_argument("--response-prob-hist", default="response_prob_reco_given_gen")
    p.add_argument("--response-counts-hist", default="response_counts")
    p.add_argument("--covariance-hist", default="unfold_covariance")
    p.add_argument("--correlation-hist", default="unfold_correlation")
    return p.parse_args()


def fetch_hist(tf, name):
    obj = tf.Get(name)
    if not obj:
        return None
    h = obj.Clone(f"{name}_plot")
    h.SetDirectory(0)
    h.SetStats(0)
    return h


def save_matrix_plot(hist, outpath, zmin=None, zmax=None):
    c = ROOT.TCanvas(f"c_{hist.GetName()}", "", 760, 680)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.16)
    c.SetBottomMargin(0.12)
    c.SetTopMargin(0.08)
    if zmin is not None:
        hist.SetMinimum(zmin)
    if zmax is not None:
        hist.SetMaximum(zmax)
    hist.Draw("COLZ")
    # Drawn in the top margin to clear the COLZ palette, as in
    # Studies/Phase2_Checks_2026-03-03/scripts/thrust_resolution_study.py.
    lbl = ROOT.TLatex()
    lbl.SetNDC(True)
    lbl.SetTextFont(42)
    lbl.SetTextSize(0.037)
    lbl.DrawLatex(0.12, 0.945, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")
    c.SaveAs(outpath)
    c.Close()


def write_matrix_csv(hist, outpath):
    nb = hist.GetNbinsX()
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["row_bin"] + [f"bin_{j}" for j in range(1, nb + 1)]
        writer.writerow(header)
        for i in range(1, nb + 1):
            row = [f"bin_{i}"] + [f"{float(hist.GetBinContent(i, j)):.10e}" for j in range(1, nb + 1)]
            writer.writerow(row)


def write_bin_edges(hist, outpath):
    axis = hist.GetXaxis()
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bin", "low_edge", "high_edge", "center"])
        for i in range(1, hist.GetNbinsX() + 1):
            writer.writerow(
                [
                    f"bin_{i}",
                    f"{float(axis.GetBinLowEdge(i)):.10e}",
                    f"{float(axis.GetBinUpEdge(i)):.10e}",
                    f"{float(axis.GetBinCenter(i)):.10e}",
                ]
            )


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    tf = ROOT.TFile.Open(args.input_root, "READ")
    if not tf or tf.IsZombie():
        raise OSError(f"Failed to open ROOT file: {args.input_root}")

    payload = [
        (args.response_counts_hist, "matrix_response_counts", None, None, False),
        (args.response_prob_hist, "matrix_response_probability", None, None, False),
        (args.covariance_hist, "matrix_unfold_covariance", None, None, True),
        (args.correlation_hist, "matrix_unfold_correlation", -1.0, 1.0, True),
    ]

    wrote = 0
    wrote_csv = 0
    for hist_name, stem, zmin, zmax, export_csv in payload:
        h = fetch_hist(tf, hist_name)
        if h is None:
            print(f"Skipping missing histogram: {hist_name}")
            continue
        save_matrix_plot(h, os.path.join(args.outdir, f"{stem}.pdf"), zmin=zmin, zmax=zmax)
        if export_csv:
            write_matrix_csv(h, os.path.join(args.outdir, f"{stem}.csv"))
            write_bin_edges(h, os.path.join(args.outdir, f"{stem}_binning.csv"))
            wrote_csv += 1
        wrote += 1

    tf.Close()
    if wrote == 0:
        raise RuntimeError("No matrix histograms were found in the input ROOT file")
    print(f"Wrote {wrote} matrix plots and {wrote_csv} matrix CSV exports to: {args.outdir}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
