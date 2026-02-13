import ROOT

# config
config = []
config.append({
    # "file" : "/data/abadea/e+e-/aleph/unfold-ee-logtau/DataProcessing/20250625/2/LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root",
    "file" : "/Users/anthonybadea/Documents/Documents/ALEPH/unfold-ee-logtau/DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root",
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
    "file" : "/Users/anthonybadea/Documents/Documents/ALEPH/unfold-ee-logtau/DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root",
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
    "file" : "/Users/anthonybadea/Documents/Documents/ALEPH/unfold-ee-logtau/DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_t.root",
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
    "file" : "/Users/anthonybadea/Documents/Documents/ALEPH/unfold-ee-logtau/DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root",
    "legend" : "Selected archived MC Reco.", # Archived MC
    "DrawOption" : "HIST",
    "color" : ROOT.kRed,
    "MarkerStyle" : 20,
    "LineWidth" : 2,
    "LineStyle" : 1,
    "LegendDraw" : "l"
})
config.append({
    "file" : "/Users/anthonybadea/Documents/Documents/ALEPH/unfold-ee-logtau/DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root",
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
    "file" : "/Users/anthonybadea/Documents/Documents/ALEPH/unfold-ee-logtau/DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgenBefore.root",
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
    "SetLogy" : False, "rebin" : 5, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dcos#theta", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.5,
    "legloc" : [0.55, 0.75, 0.75, 0.9]
}
plotConfig["d0"] = {
    "SetLogy" : True, "rebin" : 2, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dd_{0}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 10,
    "legloc" : [0.59, 0.7, 0.79, 0.9]
}
plotConfig["z0"] = {
    "SetLogy" : True, "rebin" : 20, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dz_{0}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 10,
    "legloc" : [0.59, 0.7, 0.79, 0.9]
}
plotConfig["energy"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dE", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.75, 0.75, 0.9]
}
plotConfig["mass"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dm", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.75, 0.75, 0.9]
}
plotConfig["ntpc"] = {
    "SetLogy" : False, "rebin" : 1, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dN_{TPC}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.5,
    "legloc" : [0.2, 0.75, 0.5, 0.9]
}
plotConfig["phi"] = {
    "SetLogy" : False, "rebin" : 10, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/d#phi", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.5,
    "legloc" : [0.55, 0.75, 0.75, 0.9]
}
plotConfig["pmag"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/d|#vec{p}|", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.75, 0.75, 0.9]
}
plotConfig["pt"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of entries", # "1/#sigma d#sigma/dp_{T}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.75, 0.75, 0.9]
}
plotConfig["cosThetaSph"] = {
    "SetLogy" : False, "rebin" : 5, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dcos#theta_{Sph}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.3,
    "legloc" : [0.4, 0.72, 0.6, 0.92]
}
plotConfig["cosThetaThrust"] = {
    "SetLogy" : False, "rebin" : 5, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dcos#theta_{Thr}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 1.3,
    "legloc" : [0.4, 0.72, 0.6, 0.92]
}
plotConfig["eCh"] = {
    "SetLogy" : True, "rebin" : 10, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dE_{Ch}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.7, 0.75, 0.9]
}
plotConfig["evis"] = {
    "SetLogy" : True, "rebin" : 10, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dE_{Vis}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.57, 0.72, 0.77, 0.92]
}
plotConfig["sprime"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events",
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.2, 0.72, 0.45, 0.92]
}
plotConfig["logtau"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events", "YTitleDifferential": "1/#sigma d#sigma/dlog(#tau)",
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.2, 0.75, 0.4, 0.9]
}
plotConfig["missP"] = {
    "SetLogy" : True, "rebin" : 10, "YTitle": "Fraction of events", # "1/#sigma d#sigma/d|#vec{p}_{miss}|", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.7, 0.75, 0.9]
}
plotConfig["nneu"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dN_{Neu}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.57, 0.72, 0.77, 0.92]
}
plotConfig["ntrk"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dN_{Trk}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.57, 0.72, 0.77, 0.92]
}
plotConfig["ntrkPlusNeu"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dN_{Trk + Neu}", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagLowerLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.57, 0.72, 0.77, 0.92]
}
plotConfig["sphericity"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events", # "1/#sigma d#sigma/dSph", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.55, 0.7, 0.75, 0.9]
}
plotConfig["thrust"] = {
    "SetLogy" : True, "rebin" : 1, "YTitle": "Fraction of events", "YTitleDifferential": "1/#sigma d#sigma/dT", 
    "Ndivisions": 505, "ALEPHTagTop" : ALEPHTagUpperLeft, "scale_max_bin_content" : 5,
    "legloc" : [0.23, 0.7, 0.48, 0.9]
}
