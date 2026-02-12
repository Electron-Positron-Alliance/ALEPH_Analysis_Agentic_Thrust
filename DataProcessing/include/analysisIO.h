#ifndef ANALYSIS_IO_H
#define ANALYSIS_IO_H

#include "analysisTypes.h"

#include "TFile.h"
#include "TTree.h"

#include <memory>
#include <string>

struct InputData {
  std::unique_ptr<TFile> file;
  TTree* tree = nullptr;
  bool genTree = false;
  bool hasStatus = false;
  Long64_t nEvents = 0;
};

inline InputData OpenInput(const std::string& inFileName, const std::string& treeName) {
  InputData in;
  in.file = std::make_unique<TFile>(inFileName.c_str(), "READ");
  if (!in.file || in.file->IsZombie()) {
    return in;
  }
  in.tree = static_cast<TTree*>(in.file->Get(treeName.c_str()));
  if (!in.tree) {
    return in;
  }
  in.genTree = (treeName == "tgen" || treeName == "tgenBefore");
  in.hasStatus = (in.tree->GetBranch("status") != nullptr);
  in.nEvents = in.tree->GetEntries();
  return in;
}

inline bool WriteSelectionTree(const std::string& outFileName, const Selections& sel) {
  TFile fout(outFileName.c_str(), "RECREATE");
  if (fout.IsZombie()) {
    return false;
  }

  TTree varDefs("Selection", "");
  int s_nTPC = sel.nTPCcut;
  float s_AbsCosThetaChg = sel.chargedTracksAbsCosThCut;
  float s_ptChg = sel.ptCut;
  float s_d0 = sel.d0Cut;
  float s_z0 = sel.z0Cut;
  float s_ENeu = sel.ECut;
  float s_AbsCosThetaNeu = sel.neutralTracksAbsCosThCut;
  float s_Ech = sel.TotalTrkEnergyCut;
  float s_AbsCosSTheta = sel.AbsCosSThetaCut;
  float s_NTrk = sel.NTrkCut;
  float s_NTrkPlusNeu = sel.NeuNchCut;
  float s_EVis = sel.EVisCut;
  float s_MissP = sel.MissPCut;
  bool s_ThrCh = sel.keepChargedTracks;
  bool s_ThrNeu = sel.keepNeutralTracks;
  bool s_ThrMissP = sel.doMET;

  varDefs.Branch("nTPC", &s_nTPC);
  varDefs.Branch("AbsCosThetaChg", &s_AbsCosThetaChg);
  varDefs.Branch("ptChg", &s_ptChg);
  varDefs.Branch("d0", &s_d0);
  varDefs.Branch("z0", &s_z0);
  varDefs.Branch("ENeu", &s_ENeu);
  varDefs.Branch("AbsCosThetaNeu", &s_AbsCosThetaNeu);
  varDefs.Branch("Ech", &s_Ech);
  varDefs.Branch("AbsCosSTheta", &s_AbsCosSTheta);
  varDefs.Branch("NTrk", &s_NTrk);
  varDefs.Branch("NTrkPlusNeu", &s_NTrkPlusNeu);
  varDefs.Branch("EVis", &s_EVis);
  varDefs.Branch("MissP", &s_MissP);
  varDefs.Branch("ThrCh", &s_ThrCh);
  varDefs.Branch("ThrNeu", &s_ThrNeu);
  varDefs.Branch("ThrMissP", &s_ThrMissP);

  varDefs.Fill();
  varDefs.Write();
  return true;
}

#endif
