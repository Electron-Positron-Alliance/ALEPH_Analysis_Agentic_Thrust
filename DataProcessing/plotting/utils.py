import ROOT


def build_hist(df, name, expr, nbins, xmin, xmax):
    df_var = df.Define(name, expr)
    return df_var.Histo1D((f"h_{name}", "", nbins, xmin, xmax), name).GetValue()


def normalize_hist(hist):
    integral = hist.Integral("width")
    if integral > 0:
        hist.Scale(1.0 / integral)


def make_zero_hist(name, nbins, xmin, xmax, rebin):
    hist = ROOT.TH1D(name, "", nbins, xmin, xmax)
    hist.SetDirectory(0)
    if rebin > 1:
        hist.Rebin(rebin)
    return hist


def build_safe_ratio_hist(numerator, denominator, name):
    ratio = numerator.Clone(name)
    ratio.SetDirectory(0)
    ratio.Reset("ICESM")
    for ibin in range(1, ratio.GetNbinsX() + 1):
        num = numerator.GetBinContent(ibin)
        den = denominator.GetBinContent(ibin)
        if den > 0:
            ratio.SetBinContent(ibin, num / den)
        else:
            ratio.SetBinContent(ibin, 0.0)
        ratio.SetBinError(ibin, 0.0)
    return ratio


def find_data_hist(hists):
    for entry in hists:
        if len(entry) < 2:
            continue
        h, s = entry[0], entry[1]
        if s.get("key") == "data" or s.get("label") == "Data" or s.get("is_data"):
            return h
    return None


def get_tree_columns(tree_name, file_path):
    try:
        df = ROOT.RDataFrame(tree_name, file_path)
        return {str(c) for c in df.GetColumnNames()}
    except Exception as exc:
        print(f"[warn] Could not open tree '{tree_name}' in '{file_path}': {exc}. Skipping sample.")
        return None


def get_missing_columns(columns, required):
    return [c for c in required if c not in columns]
