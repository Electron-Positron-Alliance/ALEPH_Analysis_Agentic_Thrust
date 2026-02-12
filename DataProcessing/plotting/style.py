import ROOT

TOP_X_TICK_LENGTH = 0.03
TOP_Y_TICK_LENGTH = 0.03
RATIO_X_TICK_LENGTH = 0.09
RATIO_Y_TICK_LENGTH = 0.05

def SetALEPHStyle():
    """Applies ALEPH style settings in PyROOT."""
    print("\nApplying ALEPH style settings...\n")
    aleph_style = aleph_style_settings()
    ROOT.gROOT.SetStyle("ALEPH")
    ROOT.gROOT.ForceStyle()

def aleph_style_settings():
    """Defines and returns the ALEPH style settings."""
    aleph_style = ROOT.TStyle("ALEPH", "ALEPH style")

    # Use plain black on white colors
    icol = 0  # WHITE
    aleph_style.SetFrameBorderMode(icol)
    aleph_style.SetFrameFillColor(icol)
    aleph_style.SetCanvasBorderMode(icol)
    aleph_style.SetCanvasColor(icol)
    aleph_style.SetPadBorderMode(icol)
    aleph_style.SetPadColor(icol)
    aleph_style.SetStatColor(icol)

    # Set the paper & margin sizes
    aleph_style.SetPaperSize(20, 26)

    # Set margin sizes
    aleph_style.SetPadTopMargin(0.05)
    aleph_style.SetPadRightMargin(0.05)
    aleph_style.SetPadBottomMargin(0.16)
    aleph_style.SetPadLeftMargin(0.16)

    # Set title offsets (for axis labels)
    aleph_style.SetTitleXOffset(1.4)
    aleph_style.SetTitleYOffset(1.4)

    # Use large fonts
    font = 42  # Helvetica
    tsize = 0.05
    aleph_style.SetTextFont(font)
    aleph_style.SetTextSize(tsize)
    aleph_style.SetLabelFont(font, "x")
    aleph_style.SetTitleFont(font, "x")
    aleph_style.SetLabelFont(font, "y")
    aleph_style.SetTitleFont(font, "y")
    aleph_style.SetLabelFont(font, "z")
    aleph_style.SetTitleFont(font, "z")

    aleph_style.SetLabelSize(tsize, "x")
    aleph_style.SetTitleSize(tsize, "x")
    aleph_style.SetLabelSize(tsize, "y")
    aleph_style.SetTitleSize(tsize, "y")
    aleph_style.SetLabelSize(tsize, "z")
    aleph_style.SetTitleSize(tsize, "z")

    # Use bold lines and markers
    aleph_style.SetMarkerStyle(20)
    aleph_style.SetMarkerSize(1.2)
    aleph_style.SetHistLineWidth(2)
    aleph_style.SetLineStyleString(2, "[12 12]")  # Postscript dashes

    # Get rid of X error bars and error bar caps
    aleph_style.SetEndErrorSize(0.)

    # Do not display standard histogram decorations
    aleph_style.SetOptTitle(0)
    aleph_style.SetOptStat(0)
    aleph_style.SetOptFit(0)

    # Put tick marks on top and RHS of plots
    aleph_style.SetPadTickX(1)
    aleph_style.SetPadTickY(1)

    return aleph_style

def ALEPHCanvas(name):
    return ROOT.TCanvas(f"c_{name}", name, 50, 50, 500, 500)

def ALEPHLegend(loc=[0.68, 0.8, 0.88, 0.9], textsize=0.04):
    legend = ROOT.TLegend(loc[0], loc[1], loc[2], loc[3]) # 0.68, 0.8, 0.88, 0.9)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(textsize)
    return legend 

def myText(x, y, text, color=ROOT.kBlack, align=12, size=0.03):
    """
    Draws a text label on a ROOT canvas at position (x, y) in NDC coordinates.

    Parameters:
    - x, y: Position in NDC coordinates (0-1)
    - color: ROOT color (e.g., ROOT.kBlack, ROOT.kRed)
    - text: The text string to be displayed
    """
    l = ROOT.TLatex()
    l.SetTextAlign(align)
    l.SetTextSize(size) 
    l.SetNDC()
    l.SetTextColor(color)
    l.DrawLatex(x, y, text)


def apply_style(hist, color, marker, line_style, is_data):
    hist.SetStats(0)
    hist.SetLineColor(color)
    hist.SetMarkerColor(color)
    hist.SetMarkerStyle(marker if is_data else 20)
    hist.SetMarkerSize(1.0 if is_data else 0.0)
    hist.SetLineWidth(2)
    hist.SetLineStyle(line_style)
    hist.GetYaxis().SetTitleOffset(1.15)
    hist.GetXaxis().SetTitleOffset(1.2)
    hist.GetYaxis().SetMaxDigits(3)
    hist.GetXaxis().SetTitleSize(0.06)
    hist.GetYaxis().SetTitleSize(0.07)
    hist.GetXaxis().SetLabelSize(0.055)
    hist.GetYaxis().SetLabelSize(0.055)
    hist.GetXaxis().SetTickLength(TOP_X_TICK_LENGTH)
    hist.GetYaxis().SetTickLength(TOP_Y_TICK_LENGTH)


def style_ratio(ratio, xtitle):
    ratio.SetStats(0)
    ratio.SetMarkerSize(1.4)
    ratio.GetXaxis().SetTitle(xtitle)
    ratio.GetXaxis().SetTitleSize(0.2)
    ratio.GetXaxis().SetTitleOffset(0.9)
    ratio.GetXaxis().SetLabelSize(0.15)
    ratio.GetXaxis().SetTickLength(RATIO_X_TICK_LENGTH)
    ratio.GetXaxis().SetNdivisions(505)
    # ratio.GetYaxis().CenterTitle()
    ratio.GetYaxis().SetTitle("MC / Data")
    ratio.GetYaxis().SetTitleSize(0.16)
    ratio.GetYaxis().SetTitleOffset(0.5)
    ratio.GetYaxis().SetLabelSize(0.13)
    ratio.GetYaxis().SetTickLength(RATIO_Y_TICK_LENGTH)
    ratio.GetYaxis().SetRangeUser(0.10, 1.9)
    ratio.GetYaxis().SetNdivisions(505)
