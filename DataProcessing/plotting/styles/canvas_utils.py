import ROOT

from style import ALEPHCanvas, ALEPHLegend, myText, style_ratio
from utils import build_safe_ratio_hist, find_data_hist


def draw_histogram_canvas(var_name, cfg, xtitle, hists, max_bin, out_path, header_text):
    canvas = ALEPHCanvas(var_name)
    ratio_mode = any(s.get("is_data") for _, s, _, _ in hists) and len(hists) > 1

    if ratio_mode:
        pad1 = ROOT.TPad(f"pad1_{var_name}", "", 0, 0.3, 1, 1.0)
        pad1.SetBottomMargin(0)
        pad1.SetTopMargin(0.1)
        pad1.SetLeftMargin(0.20)
        pad1.SetRightMargin(0.05)
        # pad1.SetGridx()
        # pad1.SetGridy()
        pad1.Draw()
        pad1.cd()
        if cfg["SetLogy"]:
            pad1.SetLogy()
    elif cfg["SetLogy"]:
        canvas.SetLogy()

    n_entries = len(hists)
    legend_text_size = 0.04 if n_entries > 3 else 0.05
    legend = ALEPHLegend(loc=cfg["legloc"], textsize=legend_text_size)
    for h, sample, legopt, is_fallback in hists:
        if h.GetMaximum() > 0:
            h.SetMaximum(cfg["scale_max_bin_content"] * max_bin)
        drawopt = "PE" if sample["is_data"] else "HIST"
        if h != hists[0][0]:
            drawopt += " SAME"
        h.Draw(drawopt)
        legend_label = sample["label"] + (" (missing -> 0)" if is_fallback else "")
        legend.AddEntry(h, legend_label, legopt)

    legend.Draw()
    myText(0.2, 0.925, header_text, size=0.045)

    if ratio_mode:
        data_hist = find_data_hist(hists)
        if data_hist:
            canvas.cd()
            pad2 = ROOT.TPad(f"pad2_{var_name}", "", 0, 0.05, 1, 0.3)
            pad2.SetTopMargin(0)
            pad2.SetBottomMargin(0.4)
            pad2.SetLeftMargin(0.20)
            pad2.SetRightMargin(0.05)
            # pad2.SetGridx()
            # pad2.SetGridy()
            pad2.Draw()
            pad2.cd()
            ratio_frame = data_hist.Clone(f"ratio_frame_{var_name}")
            ratio_frame.Reset("ICESM")
            style_ratio(ratio_frame, xtitle)
            ratio_frame.Draw("AXIS")

            ratio_idx = 0
            for h, sample, _, _ in hists:
                if sample.get("is_data"):
                    continue
                ratio = build_safe_ratio_hist(h, data_hist, f"ratio_{h.GetName()}")
                ratio.SetLineColor(sample["color"])
                ratio.SetMarkerColor(sample["color"])
                ratio.SetMarkerStyle(20 + ratio_idx)
                ratio.SetLineStyle(1 + ratio_idx)
                style_ratio(ratio, xtitle)
                ratio.Draw("E SAME")
                ratio_idx += 1

    canvas.Print(out_path)
    canvas.Close()
