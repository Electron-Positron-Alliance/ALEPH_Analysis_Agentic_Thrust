import os
import sys

import ROOT

# Input locations come from analysis/inputs.json via paths.py, not from
# absolute paths baked in here.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from paths import temp  # noqa: E402

# config
config = []
config.append({
    # "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250625/2/LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root",
    "file" : temp("LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root"),
    "legend" : "All uncorrected data", # Data 1994
    "color" : ROOT.kBlack,
    "DrawOption" : "PE",
    "MarkerStyle" : 24,
    "LineWidth" : 2,
    "LineStyle" : 2,
    "LegendDraw" : "pl"
})
config.append({
    # "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250625/2/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root",
    "file" : temp("LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root"),
    "legend" : "Selected uncorrected data", # Data 1994
    "color" : ROOT.kBlack,
    "DrawOption" : "PE",
    "MarkerStyle" : 20,
    "LineWidth" : 2,
    "LineStyle" : 1,
    "LegendDraw" : "pl"
})
config.append({
    # "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250625/2/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_t.root",
    "file" : temp("alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_t.root"),
    "legend" : "All archived MC Reco.", # Archived MC
    "DrawOption" : "HIST",
    "color" : ROOT.kRed,
    "MarkerStyle" : 24,
    "LineWidth" : 2,
    "LineStyle" : 2,
    "LegendDraw" : "l"
})
config.append({
    # "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250625/2/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root",
    "file" : temp("alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root"),
    "legend" : "Selected archived MC Reco.", # Archived MC
    "DrawOption" : "HIST",
    "color" : ROOT.kRed,
    "MarkerStyle" : 20,
    "LineWidth" : 2,
    "LineStyle" : 1,
    "LegendDraw" : "l"
})
config.append({
    "file" : temp("alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root"),
    "legend" : "Archived MC Gen.", # Archived MC
    "DrawOption" : "HIST",
    "color" : ROOT.kGreen,
    "MarkerStyle" : 20,
    "LineWidth" : 2,
    "LineStyle" : 1,
    "LegendDraw" : "l"
})
config.append({
    # "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250527/2/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgenBefore.root",
    "file" : temp("alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgenBefore.root"),
    "legend" : "Archived MC Gen. B.", # Archived MC
    "DrawOption" : "HIST",
    "color" : ROOT.kBlue,
    "MarkerStyle" : 20,
    "LineWidth" : 2,
    "LineStyle" : 2,
    "LegendDraw" : "l"
})
# config.append({
#     "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250527/2/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgenBefore.root",
#     "legend" : "Archived Pythia 6.1",
#     "DrawOption" : "HIST",
#     "color" : ROOT.kBlue,
#     "MarkerStyle" : 20,
#     "LineWidth" : 2,
#     "LegendDraw" : "l"
# })
# config.append({
#     "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250527/2/LEP1_PYTHIA8_MC_TGenBefore_NoISR_thrust_no_event_sel_tgenBefore.root",
#     "legend" : "Pythia 8",
#     "DrawOption" : "HIST",
#     "color" : ROOT.kGreen,
#     "MarkerStyle" : 20,
#     "LineWidth" : 2,
#     "LegendDraw" : "l"
# })
# config.append({
#     "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250527/2/Herwig_noISR_1000_thrust_no_event_sel_tgenBefore.root",
#     "legend" : "Herwig",
#     "DrawOption" : "HIST",
#     "color" : ROOT.kMagenta,
#     "MarkerStyle" : 20,
#     "LineWidth" : 2,
#     "LegendDraw" : "l"
# })
# config.append({
#     "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250527/2/Sherpa_noISR_100_thrust_no_event_sel_tgenBefore.root",
#     "legend" : "Sherpa",
#     "DrawOption" : "HIST",
#     "color" : ROOT.kGrape,
#     "MarkerStyle" : 20,
#     "LineWidth" : 2,
#     "LegendDraw" : "l"
# })

# pwflag
pwflags = ["Charged Tracks", "Charged Leptons 1", "Charged Leptons 2", "V0", "Photons", "Neutral Hadrons"]

# ALEPH tag upper or lower
ALEPHTagUpperLeft = 0.87
ALEPHTagLowerLeft = 0.3

# individual plot settings
plotConfig = {}
# what we are plotting reduces to the ytitle in terms of sigma: 1/N dN/dX = 1/(sigma * L) d(sigma*L)/dX = 1/sigma d(sigma)/dX
plotConfig["cosTheta"] = {
    "SetLogy" : False, "rebin" : 5, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dcos#theta", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["d0"] = {
    "SetLogy" : True, "rebin" : 2, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dd_{0}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 10,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["z0"] = {
    "SetLogy" : True, "rebin" : 20, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dz_{0}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 10,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["energy"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dE", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["mass"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dm", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["ntpc"] = {
    "SetLogy" : False, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dN_{TPC}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["phi"] = {
    "SetLogy" : False, "rebin" : 10, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/d#phi", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["pmag"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/d|#vec{p}|", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["pt"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dp_{T}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["cosThetaSph"] = {
    "SetLogy" : False, "rebin" : 5, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dcos#theta_{Sph}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.3,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["cosThetaThrust"] = {
    "SetLogy" : False, "rebin" : 5, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dcos#theta_{Thr}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.3,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["eCh"] = {
    "SetLogy" : True, "rebin" : 10, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dE_{Ch}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["evis"] = {
    "SetLogy" : True, "rebin" : 10, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dE_{Vis}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["sprime"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX",
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["logtau"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", "YTitleDifferential": "1/#sigma d#sigma/dlog(#tau)",
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["missP"] = {
    "SetLogy" : True, "rebin" : 10, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/d|#vec{p}_{miss}|", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["nneu"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dN_{Neu}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["ntrk"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dN_{Trk}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["ntrkPlusNeu"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dN_{Trk + Neu}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["sphericity"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", # "1/#sigma d#sigma/dSph", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
plotConfig["thrust"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "1/N dN/dX", "YTitleDifferential": "1/#sigma d#sigma/dT", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.62, 0.66, 0.88, 0.86]
}
