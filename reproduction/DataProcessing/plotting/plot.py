import argparse
import os

import ROOT

from PlotConfig import plotConfig, pwflags
from makeHists import make_histograms
from style import SetALEPHStyle
from styles.canvas_utils import draw_histogram_canvas


def rvec_expr_for_pwflag(quantity, pwflag_val):
    if quantity == "pt":
        base = "sqrt(px*px + py*py)"
    elif quantity == "pmag":
        base = "sqrt(px*px + py*py + pz*pz)"
    elif quantity == "phi":
        base = "atan2(py, px)"
    elif quantity == "cosTheta":
        base = "pz / sqrt(px*px + py*py + pz*pz)"
    elif quantity == "d0":
        base = "d0"
    elif quantity == "z0":
        base = "z0"
    elif quantity == "ntpc":
        base = "ntpc"
    elif quantity == "energy":
        base = "energy"
    elif quantity == "mass":
        base = "mass"
    else:
        return None
    return f"({base})[pwflag == {pwflag_val}]"


def get_event_vars():
    return [
        ("thrust", "Thrust", "thrust"),
        ("logtau", "TMath::Log(1.0-Thrust)", "logtau"),
        ("sphericity", "Sphericity", "sphericity"),
        ("cosThetaSph", "TMath::Cos(STheta)", "cosThetaSph"),
        ("cosThetaThrust", "TMath::Cos(TTheta)", "cosThetaThrust"),
        ("eCh", "TotalTrkEnergy", "eCh"),
        ("evis", "EVis", "evis"),
        ("missP", "MissP", "missP"),
        ("sprime", "sprime", "sprime"),
        ("ntrk", "NTrk", "ntrk"),
        ("nneu", "Neu", "nneu"),
        ("ntrkPlusNeu", "NTrk+Neu", "ntrkPlusNeu"),
    ]


def get_pwflag_vars():
    vars_out = []
    for pw in range(0, 6):
        for qty in ["cosTheta", "phi", "pt", "pmag", "d0", "z0", "ntpc", "energy", "mass"]:
            vars_out.append((f"pwflag{pw}_{qty}", pw, qty))
    return vars_out


EVENT_REQUIRED_COLUMNS = {
    "thrust": ["Thrust"],
    "logtau": ["Thrust"],
    "sphericity": ["Sphericity"],
    "cosThetaSph": ["STheta"],
    "cosThetaThrust": ["TTheta"],
    "eCh": ["TotalTrkEnergy"],
    "evis": ["EVis"],
    "missP": ["MissP"],
    "sprime": ["sprime"],
    "ntrk": ["NTrk"],
    "nneu": ["Neu"],
    "ntrkPlusNeu": ["NTrk", "Neu"],
}

EVENT_BINNING = {
    "thrust": (100, 0.5, 1.0),
    "logtau": (100, -10.0, 0.0),
    "sphericity": (100, 0.0, 1.0),
    "cosThetaSph": (100, -1.0, 1.0),
    "cosThetaThrust": (100, -1.0, 1.0),
    "eCh": (200, 0.0, 200.0),
    "evis": (200, 0.0, 200.0),
    "missP": (100, 0.0, 100.0),
    "sprime": (180, 30.0, 120.0),
    "ntrk": (61, -0.5, 60.5),
    "nneu": (51, -0.5, 50.5),
    "ntrkPlusNeu": (81, -0.5, 80.5),
}

PWFLAG_BINNING = {
    "cosTheta": (200, -1.0, 1.0),
    "phi": (800, -4.0, 4.0),
    "pt": (100, 0.0, 100.0),
    "pmag": (100, 0.0, 100.0),
    "d0": (200, -5.0, 5.0),
    "z0": (200, -20.0, 20.0),
    "ntpc": (81, -0.5, 80.5),
    "energy": (120, 0.0, 120.0),
    "mass": (120, 0.0, 6.0),
}

X_TITLES = {
    "thrust": "Thrust",
    "logtau": "log(#tau)",
    "sphericity": "Sphericity",
    "cosThetaSph": "cos#theta_{Sph}",
    "cosThetaThrust": "cos#theta_{Thr}",
    "eCh": "E_{Ch} [GeV]",
    "evis": "E_{Vis} [GeV]",
    "missP": "|#vec{p}_{miss}| [GeV]",
    "sprime": "#sqrt{s'} [GeV]",
    "ntrk": "N_{Trk}",
    "nneu": "N_{Neu}",
    "ntrkPlusNeu": "N_{Trk}+N_{Neu}",
    "cosTheta": "cos#theta",
    "phi": "#phi",
    "pt": "p_{T} [GeV]",
    "pmag": "|#vec{p}| [GeV]",
    "d0": "d_{0} [cm]",
    "z0": "z_{0} [cm]",
    "ntpc": "N_{TPC}",
    "energy": "E [GeV]",
    "mass": "m [GeV]",
}


PWFLAG_REQUIRED_COLUMNS = {
    "cosTheta": ["px", "py", "pz", "pwflag"],
    "phi": ["px", "py", "pz", "pwflag"],
    "pt": ["px", "py", "pz", "pwflag"],
    "pmag": ["px", "py", "pz", "pwflag"],
    "d0": ["d0", "pwflag"],
    "z0": ["z0", "pwflag"],
    "ntpc": ["ntpc", "pwflag"],
    "energy": ["energy", "pwflag"],
    "mass": ["mass", "pwflag"],
}


def parse_args():
    parser = argparse.ArgumentParser(description="Plot distributions from analysis ROOT files")
    parser.add_argument("--files", nargs="+", help="Input ROOT files (simple overlay mode)")
    parser.add_argument("--labels", nargs="+", default=None, help="Labels for --files")
    parser.add_argument("--data", help="Data reco file (tree t)")
    parser.add_argument("--mc-reco", help="MC reco file (tree t)")
    parser.add_argument("--mc-gen", help="MC gen file (tree tgen)")
    parser.add_argument("--mc-genbefore", help="MC gen-before file (tree tgenBefore)")
    parser.add_argument("--outDir", default="plots", help="Output directory")
    parser.add_argument("--no-normalize", action="store_true", help="Disable normalization")
    parser.add_argument("--no-selection", action="store_true", help="Disable passEventSelection filter")
    parser.add_argument("--include-pwflag", action="store_true", help="Include pwflag particle plots")
    parser.add_argument("--only", nargs="+", default=None, help="Only plot these variables")
    return parser.parse_args()


def build_samples(args):
    samples = []
    if args.files:
        labels = args.labels or [os.path.basename(f) for f in args.files]
        if len(labels) != len(args.files):
            raise ValueError("Number of labels must match number of files")
        for i, fpath in enumerate(args.files):
            samples.append(
                {
                    "key": f"file{i}",
                    "label": labels[i],
                    "file": fpath,
                    "tree": "t",
                    "color": ROOT.kBlack if i == 0 else (ROOT.kRed + i),
                    "is_data": i == 0,
                }
            )
    else:
        if args.data:
            samples.append({"key": "data", "label": "Data", "file": args.data, "tree": "t", "color": ROOT.kBlack, "is_data": True})
        if args.mc_reco:
            samples.append({"key": "mc_reco", "label": "MC Reco", "file": args.mc_reco, "tree": "t", "color": ROOT.kRed + 1, "is_data": False})
        if args.mc_gen:
            samples.append({"key": "mc_gen", "label": "MC Gen", "file": args.mc_gen, "tree": "tgen", "color": ROOT.kGreen + 2, "is_data": False})
        if args.mc_genbefore:
            samples.append({"key": "mc_genbefore", "label": "MC GenBefore", "file": args.mc_genbefore, "tree": "tgenBefore", "color": ROOT.kBlue + 1, "is_data": False})

    if not samples:
        raise ValueError("Provide --files or at least one of --data/--mc-reco/--mc-gen/--mc-genbefore")
    return samples


def filter_requested_vars(event_vars, pwflag_vars, only):
    if not only:
        return event_vars, pwflag_vars
    only_set = set(only)
    event_vars = [v for v in event_vars if v[0] in only_set]
    pwflag_vars = [v for v in pwflag_vars if v[0] in only_set]
    return event_vars, pwflag_vars


def get_hist_output_path(input_file, out_dir):
    base_name = os.path.basename(input_file)
    if base_name.endswith(".root"):
        out_name = f"{base_name[:-5]}_hists.root"
    else:
        out_name = f"{base_name}_hists.root"
    return os.path.join(out_dir, out_name)


def init_hist_output_files(samples, out_dir):
    out_files = {}
    for sample in samples:
        out_path = get_hist_output_path(sample["file"], out_dir)
        out_file = ROOT.TFile(out_path, "RECREATE")
        if not out_file or out_file.IsZombie():
            raise OSError(f"Failed to create histogram output file: {out_path}")
        out_files[sample["key"]] = out_file
    return out_files


def write_sample_hists(hists, var_name, hist_out_files):
    for hist, sample, _, _ in hists:
        out_file = hist_out_files.get(sample["key"])
        if out_file is None:
            continue
        out_file.cd()
        hist_copy = hist.Clone(var_name)
        hist_copy.SetDirectory(out_file)
        hist_copy.Write("", ROOT.TObject.kOverwrite)


def main():
    args = parse_args()

    os.makedirs(args.outDir, exist_ok=True)
    ROOT.gROOT.SetBatch(True)
    SetALEPHStyle()

    samples = build_samples(args)
    hist_out_files = init_hist_output_files(samples, args.outDir)
    event_vars = get_event_vars()
    pwflag_vars = get_pwflag_vars() if args.include_pwflag else []
    event_vars, pwflag_vars = filter_requested_vars(event_vars, pwflag_vars, args.only)

    try:
        for var_name, expr, cfg_key in event_vars:
            if cfg_key not in plotConfig or cfg_key not in EVENT_BINNING:
                continue
            cfg = plotConfig[cfg_key]
            nbins, xmin, xmax = EVENT_BINNING[cfg_key]
            hists, max_bin = make_histograms(
                samples=samples,
                var_name=var_name,
                expr=expr,
                cfg=cfg,
                nbins=nbins,
                xmin=xmin,
                xmax=xmax,
                xtitle=X_TITLES.get(cfg_key, ""),
                required_columns=EVENT_REQUIRED_COLUMNS.get(cfg_key, []),
                no_selection=args.no_selection,
                no_normalize=args.no_normalize,
            )
            if not hists:
                print(f"[warn] No valid samples for '{var_name}'. Skipping plot.")
                continue
            draw_histogram_canvas(
                var_name=var_name,
                cfg=cfg,
                xtitle=X_TITLES.get(cfg_key, ""),
                hists=hists,
                max_bin=max_bin,
                out_path=os.path.join(args.outDir, f"{var_name}.pdf"),
                header_text="ALEPH e^{+}e^{-}, #sqrt{s} = 91.2 GeV",
            )
            write_sample_hists(hists, var_name, hist_out_files)

        for var_name, pwflag_val, qty in pwflag_vars:
            if qty not in plotConfig or qty not in PWFLAG_BINNING:
                continue
            expr = rvec_expr_for_pwflag(qty, pwflag_val)
            if expr is None:
                continue
            cfg = plotConfig[qty]
            nbins, xmin, xmax = PWFLAG_BINNING[qty]
            hists, max_bin = make_histograms(
                samples=samples,
                var_name=var_name,
                expr=expr,
                cfg=cfg,
                nbins=nbins,
                xmin=xmin,
                xmax=xmax,
                xtitle=X_TITLES.get(qty, ""),
                required_columns=PWFLAG_REQUIRED_COLUMNS.get(qty, ["pwflag"]),
                no_selection=args.no_selection,
                no_normalize=args.no_normalize,
            )
            if not hists:
                print(f"[warn] No valid samples for '{var_name}'. Skipping plot.")
                continue
            draw_histogram_canvas(
                var_name=var_name,
                cfg=cfg,
                xtitle=X_TITLES.get(qty, ""),
                hists=hists,
                max_bin=max_bin,
                out_path=os.path.join(args.outDir, f"{var_name}.pdf"),
                header_text=f"ALEPH e^{{+}}e^{{-}}, #sqrt{{s}} = 91.2 GeV, {pwflags[pwflag_val]}",
            )
            write_sample_hists(hists, var_name, hist_out_files)
    finally:
        for out_file in hist_out_files.values():
            out_file.Close()


if __name__ == "__main__":
    main()
