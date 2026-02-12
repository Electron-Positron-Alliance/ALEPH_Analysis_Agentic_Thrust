/*
Author: Anthony Badea
Date: January 26, 2026
Analysis: RDataFrame-based thrust analysis (lighter than Thrust.cxx)
*/

// ROOT dependencies
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "TString.h"
#include "TError.h"
#include "TRandom3.h"

// thrust code
#include "thrustTools.h"
#include "sphericityTools.h"

// local utilities
#include "analysisCompute.h"
#include "analysisConfig.h"
#include "analysisEvent.h"
#include "analysisIO.h"
#include "analysisTypes.h"

// c++ code
#include <vector>
#include <string>
#include <iostream>
#include <cmath>
#include <utility>

int main(int argc, char* argv[]) {
  gErrorIgnoreLevel = kError; // suppress warnings from Eigen/TMatrix operations

  // #%%%%%%%%%%%%%%%%%%%%%%%%%% User Input %%%%%%%%%%%%%%%%%%%%%%%%%%#
  Options opts = ParseOptions(argc, argv);
  if (opts.inFileName == "") {
    std::cout << "No input file name provided. Exiting" << std::endl;
    return 0;
  }
  if (opts.outFileName == "" && opts.inFileName != "") {
    opts.outFileName = opts.inFileName;
    opts.outFileName.erase(opts.outFileName.length() - 5); // strip .root
    opts.outFileName += "_thrust.root";
  }

  if (!opts.configPath.empty()) {
    opts.configStr = ReadConfigFile(opts.configPath);
  }

  // Parse configuration string
  if (opts.configStr.empty()) {
    std::cout << "No configuration string provided. Exiting" << std::endl;
    return 0;
  }
  ConfigParams config = parseConfigString(opts.configStr);
  Selections sel = BuildSelections(config.selections);

  // Extract file type and tree name from configuration
  std::string inFileType = config.strings["inFileType"];
  std::string tree = config.strings["treeNames"]; // Single tree name

  // #%%%%%%%%%%%%%%%%%%%%%%%%%% Input Data %%%%%%%%%%%%%%%%%%%%%%%%%%#
  InputData input = OpenInput(opts.inFileName, tree);
  if (!input.file || input.file->IsZombie()) {
    std::cout << "Failed to open input file: " << opts.inFileName << std::endl;
    return 0;
  }
  TTree* tin = input.tree;
  if (!tin) {
    std::cout << "Failed to find tree: " << tree << std::endl;
    return 0;
  }
  const bool genTree = input.genTree;
  const bool hasStatus = input.hasStatus;

  const Long64_t nEvents = input.nEvents;
  Long64_t startevt = 0;
  Long64_t endevt = nEvents;
  if (opts.doNEvents != -1) {
    endevt = opts.doNEvents;
  }
  if (endevt > nEvents) endevt = nEvents;

  std::cout << TString::Format("Total events %lld, Start event %lld, End event %lld, Analysing %lld events",
                              nEvents, startevt, endevt, (endevt - startevt)) << std::endl;

  // #%%%%%%%%%%%%%%%%%%%%%%%%%% Output File %%%%%%%%%%%%%%%%%%%%%%%%%%#
  if (!WriteSelectionTree(opts.outFileName, sel)) {
    std::cout << "Failed to write selection tree to output: " << opts.outFileName << std::endl;
    return 0;
  }

  // #%%%%%%%%%%%%%%%%%%%%%%%%%% Analysis Loop (RDataFrame) %%%%%%%%%%%%%%%%%%%%%%%%%%#
  const bool useRange = (startevt != 0) || (endevt != nEvents);
  if (!opts.debug) {
    if (useRange) {
      std::cout << "ImplicitMT disabled because Range is in use." << std::endl;
    } else if (opts.nThreads > 0) {
      ROOT::EnableImplicitMT(opts.nThreads);
      std::cout << TString::Format("ImplicitMT enabled with %u threads", ROOT::GetThreadPoolSize()) << std::endl;
    } else {
      ROOT::EnableImplicitMT();
      std::cout << TString::Format("ImplicitMT enabled with %u threads", ROOT::GetThreadPoolSize()) << std::endl;
    }
  } else {
    std::cout << "Debug mode: ImplicitMT disabled" << std::endl;
  }

  ROOT::RDataFrame df(tree, opts.inFileName);
  ROOT::RDF::RNode dfRange = df;
  if (useRange) {
    dfRange = df.Range(startevt, endevt);
  }

  ROOT::RDF::RNode dfStatus = dfRange;
  if (hasStatus) {
    dfStatus = dfRange.Define("statusSafe", [](const ROOT::RVec<int>& status) { return status; }, {"status"});
  } else {
    dfStatus = dfRange.Define("statusSafe", [](int n) { return ROOT::RVec<int>(n, 1); }, {"nParticle"});
  }

  const unsigned int nSlots = ROOT::GetThreadPoolSize();
  std::vector<TRandom3> rngs;
  rngs.reserve(nSlots > 0 ? nSlots : 1);
  for (unsigned int i = 0; i < (nSlots > 0 ? nSlots : 1); ++i) {
    rngs.emplace_back(0x1234 + i);
  }

  const std::vector<std::string> eventInputs = {
      "uniqueID",
      "nParticle",
      "passesNTupleAfterCut",
      "pwflag",
      "theta",
      "phi",
      "pt",
      "d0",
      "z0",
      "ntpc",
      "px",
      "py",
      "pz",
      "pmag",
      "mass",
      "charge",
      "statusSafe"};

  auto dfWithEvent = dfStatus.Define("event", MakeEventData, eventInputs);

  auto dfWithResult = dfWithEvent.DefineSlot(
      "result",
      [sel, inFileType, genTree, opts, &rngs](unsigned int slot, const EventData& ev) {
        return ComputeEventResult(slot, ev, sel, inFileType, genTree, opts.debug, rngs);
      },
      {"event"});

  auto defineOrRedefine = [](ROOT::RDF::RNode df, const std::string& name, auto&& fn) {
    if (df.HasColumn(name)) {
      return df.Redefine(name, std::forward<decltype(fn)>(fn), {"result"});
    }
    return df.Define(name, std::forward<decltype(fn)>(fn), {"result"});
  };

  auto dfOut = dfWithResult;
  dfOut = defineOrRedefine(dfOut, "Thrust", [](const EventResult& r) { return r.Thrust; });
  dfOut = defineOrRedefine(dfOut, "RivetThrust", [](const EventResult& r) { return r.RivetThrust; });
  dfOut = defineOrRedefine(dfOut, "ChargedThrust", [](const EventResult& r) { return r.ChargedThrust; });
  dfOut = defineOrRedefine(dfOut, "TotalTrkEnergy", [](const EventResult& r) { return r.TotalTrkEnergy; });
  dfOut = defineOrRedefine(dfOut, "NTrk", [](const EventResult& r) { return r.NTrk; });
  dfOut = defineOrRedefine(dfOut, "Neu", [](const EventResult& r) { return r.Neu; });
  dfOut = defineOrRedefine(dfOut, "Nisr", [](const EventResult& r) { return r.Nisr; });
  dfOut = defineOrRedefine(dfOut, "STheta", [](const EventResult& r) { return r.STheta; });
  dfOut = defineOrRedefine(dfOut, "Sphericity", [](const EventResult& r) { return r.Sphericity; });
  dfOut = defineOrRedefine(dfOut, "MissP", [](const EventResult& r) { return r.MissP; });
  dfOut = defineOrRedefine(dfOut, "EVis", [](const EventResult& r) { return r.EVis; });
  dfOut = defineOrRedefine(dfOut, "TTheta", [](const EventResult& r) { return r.TTheta; });
  dfOut = defineOrRedefine(dfOut, "sprime", [](const EventResult& r) { return r.sprime; });
  dfOut = defineOrRedefine(dfOut, "passEventSelection", [](const EventResult& r) { return r.passEventSelection; });
  dfOut = defineOrRedefine(dfOut, "NSelectedParticles", [](const EventResult& r) { return r.NSelectedParticles; });
  dfOut = defineOrRedefine(dfOut, "px", [](const EventResult& r) { return r.px; });
  dfOut = defineOrRedefine(dfOut, "py", [](const EventResult& r) { return r.py; });
  dfOut = defineOrRedefine(dfOut, "pz", [](const EventResult& r) { return r.pz; });
  dfOut = defineOrRedefine(dfOut, "pwflag", [](const EventResult& r) { return r.pwflag; });
  dfOut = defineOrRedefine(dfOut, "conversionElectronTheta", [](const EventResult& r) { return r.conversionElectronTheta; });
  dfOut = defineOrRedefine(dfOut, "conversionElectronPhi", [](const EventResult& r) { return r.conversionElectronPhi; });
  dfOut = defineOrRedefine(dfOut, "conversionElectronPt", [](const EventResult& r) { return r.conversionElectronPt; });

  std::vector<std::string> outCols = {
      "uniqueID",
      "Thrust",
      "RivetThrust",
      "ChargedThrust",
      "TotalTrkEnergy",
      "NTrk",
      "Neu",
      "Nisr",
      "STheta",
      "Sphericity",
      "MissP",
      "EVis",
      "TTheta",
      "sprime",
      "passEventSelection",
      "NSelectedParticles",
      "px",
      "py",
      "pz",
      "pwflag",
      "conversionElectronTheta",
      "conversionElectronPhi",
      "conversionElectronPt"};

  ROOT::RDF::RSnapshotOptions snapshotOpts;
  snapshotOpts.fMode = "UPDATE";
  dfOut.Snapshot(tree, opts.outFileName, outCols, snapshotOpts);

  std::cout << "Done." << std::endl;
  return 1;
}
