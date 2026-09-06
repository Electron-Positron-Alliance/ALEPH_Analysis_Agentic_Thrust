#!/usr/bin/env python3
"""Plot final-result total correlation matrix from CSV exports."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import List

import ROOT


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corr-csv",
                   default="Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/corr_total.csv",
                   help="Path to corr_total.csv")
    p.add_argument("--binning-csv",
                   default="Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv",
                   help="Path to binning.csv")
    p.add_argument("--output-pdf",
                   default="Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrix_total_correlation_final.pdf",
                   help="Output PDF path")
    p.add_argument("--title", default="Total correlation matrix (final result)")
    return p.parse_args()


def load_corr_csv(path: str) -> List[List[float]]:
    rows: List[List[float]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            rows.append([float(x) for x in row])
    if not rows:
        raise ValueError(f"Correlation CSV is empty: {path}")
    n = len(rows[0])
    if any(len(r) != n for r in rows):
        raise ValueError(f"Non-rectangular correlation CSV: {path}")
    if len(rows) != n:
        raise ValueError(f"Correlation CSV must be square, got {len(rows)}x{n}: {path}")
    return rows


def load_edges(path: str) -> List[float]:
    lows: List[float] = []
    highs: List[float] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "low" not in reader.fieldnames or "high" not in reader.fieldnames:
            raise ValueError(f"Binning CSV missing required columns 'low' and 'high': {path}")
        for row in reader:
            lows.append(float(row["low"]))
            highs.append(float(row["high"]))
    if not lows:
        raise ValueError(f"Binning CSV is empty: {path}")
    edges = [lows[0]] + highs
    return edges


def build_hist(corr: List[List[float]], edges: List[float], title: str):
    n = len(corr)
    if len(edges) != n + 1:
        raise ValueError(f"Edge count mismatch: expected {n + 1}, got {len(edges)}")
    h = ROOT.TH2D(
        "h_total_corr_final",
        title,
        n,
        array_d(edges),
        n,
        array_d(edges),
    )
    h.SetDirectory(0)
    h.SetStats(0)
    for ix in range(1, n + 1):
        for iy in range(1, n + 1):
            h.SetBinContent(ix, iy, float(corr[ix - 1][iy - 1]))
    h.GetXaxis().SetTitle("Thrust T")
    h.GetYaxis().SetTitle("Thrust T")
    h.GetZaxis().SetTitle("Correlation")
    h.GetXaxis().SetNdivisions(510)
    h.GetYaxis().SetNdivisions(510)
    h.GetZaxis().SetNdivisions(510)
    h.GetXaxis().SetTitleOffset(1.1)
    h.GetYaxis().SetTitleOffset(1.15)
    h.GetZaxis().SetTitleOffset(1.15)
    h.SetMinimum(-1.0)
    h.SetMaximum(1.0)
    return h


def array_d(vals: List[float]):
    from array import array

    return array("d", [float(v) for v in vals])


def draw_and_save(hist, out_pdf: str):
    outdir = os.path.dirname(os.path.abspath(out_pdf))
    if outdir:
        os.makedirs(outdir, exist_ok=True)

    c = ROOT.TCanvas("c_total_corr_final", "", 760, 680)
    c.SetLeftMargin(0.12)
    c.SetRightMargin(0.16)
    c.SetBottomMargin(0.12)
    c.SetTopMargin(0.08)

    hist.Draw("COLZ")

    label = ROOT.TLatex()
    label.SetNDC(True)
    label.SetTextSize(0.037)
    label.SetTextFont(42)
    # Two labels in top margin: ALEPH stamp (left) and plot title (right)
    label.DrawLatex(0.12, 0.945, "ALEPH e^{+}e^{-}, #sqrt{s}=91.2 GeV")

    c.SaveAs(out_pdf)
    c.Close()


def main():
    args = parse_args()
    corr = load_corr_csv(args.corr_csv)
    edges = load_edges(args.binning_csv)
    hist = build_hist(corr, edges, args.title)
    draw_and_save(hist, args.output_pdf)
    print(f"Wrote total-correlation plot: {args.output_pdf}")


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(0)
    ROOT.gStyle.SetPalette(ROOT.kBird)
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
