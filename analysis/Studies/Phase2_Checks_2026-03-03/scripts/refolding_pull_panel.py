#!/usr/bin/env python3
"""
Produce a pull-panel companion to Figure 9 (refolded vs data comparison).

For each selected iteration N, the refolded histogram R_N(i) is compared
bin-by-bin with the detector-level data histogram D(i) via a pull:

    pull_N(i) = (D(i) - R_N(i)) / sqrt(D_err(i)^2 + R_err_N(i)^2)

The upper panel shows D and R_N overlaid (same as Fig. 9, but compact).
The lower pull panel shows the per-bin pulls for each selected iteration.

Usage:
    python refolding_pull_panel.py \
        --input-data  /path/to/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
        --input-mc    /path/to/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
        --iter-files  iter4=/path/to/iter4/t.root iter5=/path/to/iter5/t.root ... \
        --outdir Studies/Phase2_Checks_2026-03-03/plots/pull_panel

Requires ROOT. Run with a ROOT-enabled Python environment.

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-03-03
"""

import argparse
import os
import sys

import ROOT

# Input locations come from analysis/inputs.json via paths.py, not from a fixed
# directory, so a rerun does not silently read another run's ntuples.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))


def _temp(name):
    try:
        import paths
        return paths.temp(name)
    except Exception:
        return os.path.join("DataProcessing", "temp", name)
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.TH1.AddDirectory(False)  # prevent histograms from being owned by TFile directories

# Thrust histogram binning matching the analysis nominal
T_MIN   = 0.5
T_MAX   = 1.0
N_BINS  = 50


def parse_args():
    p = argparse.ArgumentParser(description="Refolding pull panel")
    p.add_argument("--input-data",
                   default=_temp("LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root"),
                   help="Data ROOT file (t tree, reco level)")
    p.add_argument("--input-mc-nominal",
                   default=_temp("alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root"),
                   help="MC reco ROOT file for nominal unfolded result (t tree)")
    p.add_argument("--iter-files", nargs="+", default=[],
                   help="Additional iteration ROOT files as key=path pairs, "
                        "e.g. iter4=/path/to/file.root iter6=/path.root")
    p.add_argument("--treename", default="t",
                   help="Tree name (default: t)")
    p.add_argument("--outdir", default="Studies/Phase2_Checks_2026-03-03/plots/pull_panel")
    return p.parse_args()


def fill_thrust_hist(tree, label, pass_event_sel=True, scale=True):
    """Fill the detector-level thrust histogram from tree."""
    h = ROOT.TH1F(f"h_thrust_{label}",
                  ";Thrust T;Entries per bin",
                  N_BINS, T_MIN, T_MAX)
    for ev in tree:
        if pass_event_sel and not ev.passEventSelection:
            continue
        try:
            t_val = float(ev.t)
        except AttributeError:
            break
        h.Fill(t_val)
    if scale and h.Integral(1, h.GetNbinsX()) > 0:
        h.Scale(1.0 / h.Integral(1, h.GetNbinsX()))
    return h


def compute_pulls(h_data, h_refold, label):
    """Compute per-bin pull: (data - refold) / sigma."""
    n = h_data.GetNbinsX()
    h_pull = ROOT.TH1F(f"h_pull_{label}",
                       ";Thrust T;Pull (data - refold)/#sigma",
                       n, T_MIN, T_MAX)
    for i in range(1, n + 1):
        d   = h_data.GetBinContent(i)
        d_e = h_data.GetBinError(i)
        r   = h_refold.GetBinContent(i)
        r_e = h_refold.GetBinError(i)
        denom = (d_e**2 + r_e**2)**0.5
        if denom > 0:
            pull = (d - r) / denom
            h_pull.SetBinContent(i, pull)
            h_pull.SetBinError(i, 0)
    return h_pull


def draw_pull_panel(h_data, refold_hists, labels, colors, outpath):
    """Draw upper-panel overlay + lower-panel pulls."""
    c = ROOT.TCanvas("c_pull", "", 900, 800)
    c.SetLeftMargin(0.12)

    # Split canvas: top 65% for spectrum, bottom 35% for pulls
    pad1 = ROOT.TPad("pad1", "", 0, 0.35, 1, 1)
    pad2 = ROOT.TPad("pad2", "", 0, 0,    1, 0.35)
    pad1.SetBottomMargin(0.02)
    pad1.SetLeftMargin(0.12)
    pad2.SetTopMargin(0.02)
    pad2.SetBottomMargin(0.30)
    pad2.SetLeftMargin(0.12)
    pad1.Draw()
    pad2.Draw()

    # Upper pad
    pad1.cd()
    pad1.SetLogy()
    h_data.SetLineColor(int(ROOT.kBlack))
    h_data.SetMarkerStyle(20)
    h_data.SetMarkerSize(0.7)
    ymax = h_data.GetMaximum() * 20  # wide log range so low-thrust bins are visible
    h_data.SetMaximum(ymax)
    h_data.SetMinimum(1e-6)
    h_data.GetXaxis().SetLabelSize(0)
    h_data.GetYaxis().SetTitle("Entries (normalized)")
    h_data.GetYaxis().SetTitleSize(0.055)
    h_data.GetYaxis().SetTitleOffset(1.10)
    h_data.Draw("E1")

    for h, lbl, col in zip(refold_hists, labels, colors):
        h.SetLineColor(col)
        h.SetLineWidth(2)
        h.Draw("HIST SAME")

    leg = ROOT.TLegend(0.55, 0.55, 0.90, 0.85)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.045)
    leg.AddEntry(h_data, "Data (reco)", "ep")
    for h, lbl in zip(refold_hists, labels):
        leg.AddEntry(h, lbl, "l")
    leg.Draw()

    # ALEPH label
    _albl = ROOT.TLatex()
    _albl.SetNDC(True)
    _albl.SetTextSize(0.050)
    _albl.SetTextFont(42)
    _albl.DrawLatex(0.14, 0.930, "ALEPH archived data, e^{+}e^{-} #sqrt{s}=91.2 GeV")

    # Lower pad: pulls
    pad2.cd()
    pull_hists = [compute_pulls(h_data, r, f"iter{i}")
                  for i, r in enumerate(refold_hists)]

    y_lo, y_hi = -4.0, 4.0
    for i, (h_pull, lbl, col) in enumerate(zip(pull_hists, labels, colors)):
        h_pull.SetLineColor(col)
        h_pull.SetLineWidth(2)
        h_pull.SetMinimum(y_lo)
        h_pull.SetMaximum(y_hi)
        if i == 0:
            h_pull.GetXaxis().SetLabelSize(0.09)
            h_pull.GetYaxis().SetLabelSize(0.09)
            h_pull.GetXaxis().SetTitleSize(0.09)
            h_pull.GetXaxis().SetTitleOffset(1.1)
            h_pull.SetTitle(";Thrust T;Pull")
            h_pull.Draw("HIST")
        else:
            h_pull.Draw("HIST SAME")

    # Reference lines at ±1 and 0
    for val, style in [(0, 1), (1, 2), (-1, 2)]:
        ref = ROOT.TLine(T_MIN, val, T_MAX, val)
        ref.SetLineColor(int(ROOT.kGray + 2))
        ref.SetLineStyle(style)
        ref.SetLineWidth(1)
        ref.Draw()

    c.SaveAs(outpath)
    c.Close()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # Open data file
    f_data = ROOT.TFile(args.input_data, "READ")
    if not f_data or f_data.IsZombie():
        sys.exit(f"Cannot open data file: {args.input_data}")
    t_data = f_data.Get(args.treename)
    if not t_data:
        sys.exit(f"Cannot find tree '{args.treename}' in data file")

    # Open MC nominal (for nominal refolded distribution)
    f_mc = ROOT.TFile(args.input_mc_nominal, "READ")
    if not f_mc or f_mc.IsZombie():
        sys.exit(f"Cannot open MC nominal file: {args.input_mc_nominal}")
    t_mc = f_mc.Get(args.treename)
    if not t_mc:
        sys.exit(f"Cannot find tree '{args.treename}' in MC file")

    print("Filling data histogram...")
    h_data = fill_thrust_hist(t_data, "data", pass_event_sel=True, scale=True)

    # Selected iteration labels
    iter_labels = ["Iter=5 (nominal)"]
    iter_trees  = [t_mc]
    iter_files  = [f_mc]
    colors      = [int(ROOT.kRed), int(ROOT.kBlue), int(ROOT.kGreen+2),
                   int(ROOT.kMagenta), int(ROOT.kOrange+7)]

    # Parse additional iteration files
    for kv in args.iter_files:
        parts = kv.split("=", 1)
        if len(parts) != 2:
            print(f"Warning: skipping malformed iter-files entry: {kv}")
            continue
        label, path = parts
        f_iter = ROOT.TFile(path, "READ")
        if not f_iter or f_iter.IsZombie():
            print(f"Warning: cannot open {path}, skipping")
            continue
        t_iter = f_iter.Get(args.treename)
        if not t_iter:
            print(f"Warning: no tree '{args.treename}' in {path}, skipping")
            continue
        iter_labels.append(label)
        iter_trees.append(t_iter)
        iter_files.append(f_iter)

    print("Filling refolded histograms for each iteration...")
    refold_hists = [
        fill_thrust_hist(t, f"iter{i}", pass_event_sel=True, scale=True)
        for i, t in enumerate(iter_trees)
    ]

    n_colors = min(len(refold_hists), len(colors))
    draw_pull_panel(
        h_data,
        refold_hists[:n_colors],
        iter_labels[:n_colors],
        colors[:n_colors],
        os.path.join(args.outdir, "dist_refolded_vs_data_pull.pdf")
    )

    # Save histograms
    out_root = os.path.join(args.outdir, "refolding_pull_histograms.root")
    fout = ROOT.TFile(out_root, "RECREATE")
    h_data.Write()
    for h in refold_hists:
        h.Write()
    fout.Close()

    for f in iter_files:
        f.Close()
    f_data.Close()

    print(f"\nDone. Pull panel saved to {args.outdir}")


if __name__ == "__main__":
    main()
