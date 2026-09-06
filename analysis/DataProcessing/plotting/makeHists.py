import ROOT

from style import apply_style
from utils import build_hist, get_missing_columns, get_tree_columns, make_zero_hist, normalize_hist


def _prepare_hist_axes(hist, cfg, xtitle):
    hist.GetXaxis().SetNdivisions(cfg["Ndivisions"])
    hist.GetYaxis().SetNdivisions(cfg["Ndivisions"])
    hist.GetXaxis().SetTitle(xtitle)
    hist.GetYaxis().SetTitle(cfg["YTitle"])


def _append_fallback_hist(hists, sample, var_name, cfg, nbins, xmin, xmax, xtitle, reason):
    print(
        f"[warn] Using zero histogram for '{sample['label']}' in '{var_name}' "
        f"({reason})"
    )
    h = make_zero_hist(f"h_{var_name}_{sample['key']}_fallback", nbins, xmin, xmax, cfg["rebin"])
    _prepare_hist_axes(h, cfg, xtitle)
    apply_style(h, sample["color"], 20, 1, sample["is_data"])
    hists.append((h, sample, "l", True))


def make_histograms(
    samples,
    var_name,
    expr,
    cfg,
    nbins,
    xmin,
    xmax,
    xtitle,
    required_columns,
    no_selection,
    no_normalize,
    allowed_trees=None,
):
    hists = []
    max_bin = 0.0
    use_ratio_fallback = any(s.get("is_data") for s in samples) and len(samples) > 1

    for sample in samples:
        if allowed_trees and sample["tree"] not in allowed_trees:
            continue

        columns = get_tree_columns(sample["tree"], sample["file"])
        if columns is None:
            continue

        required_cols = list(required_columns)
        if not no_selection and sample["tree"] == "t":
            required_cols.append("passEventSelection")
        missing = get_missing_columns(columns, required_cols)
        if missing:
            if use_ratio_fallback and not sample["is_data"]:
                reason = f"missing columns: {', '.join(missing)}"
                _append_fallback_hist(hists, sample, var_name, cfg, nbins, xmin, xmax, xtitle, reason)
            else:
                print(
                    f"[warn] Skipping '{sample['label']}' for '{var_name}' "
                    f"(missing columns: {', '.join(missing)})"
                )
            continue

        df = ROOT.RDataFrame(sample["tree"], sample["file"])
        if not no_selection and sample["tree"] == "t":
            df = df.Filter("passEventSelection == 1")

        try:
            h = build_hist(df, f"{var_name}_{sample['key']}", expr, nbins, xmin, xmax)
        except Exception as exc:
            if use_ratio_fallback and not sample["is_data"]:
                reason = f"failed to build histogram: {exc}"
                _append_fallback_hist(hists, sample, var_name, cfg, nbins, xmin, xmax, xtitle, reason)
            else:
                print(f"[warn] Failed to build '{var_name}' for '{sample['label']}': {exc}. Skipping sample.")
            continue

        h.Rebin(cfg["rebin"])
        _prepare_hist_axes(h, cfg, xtitle)
        if not no_normalize:
            normalize_hist(h)
        apply_style(h, sample["color"], 20, 1, sample["is_data"])
        max_bin = max(max_bin, h.GetMaximum())
        hists.append((h, sample, "pl" if sample["is_data"] else "l", False))

    return hists, max_bin
