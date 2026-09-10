/*
Author: Anthony Badea
Purpose: Self-contained event loop for thrust analysis.
         Computes: Thrust, RivetThrust, ChargedThrust, CParameter, HeavyJetMass, Sphericity
         Saves selected particle kinematics and event-level quantities.
*/

// ROOT dependencies
#include "TTree.h"
#include "TFile.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "TString.h"
#include "TH1D.h"
#include "TError.h"
#include "TRandom.h"

// Observable headers (local copies)
#include "thrustTools.h"
#include "sphericityTools.h"
#include "rivetThrust.h"
#include "heavyJetMass.h"

// C++ standard
#include <vector>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <map>
#include <algorithm>
#include <cmath>

// ======================== Config parsing ========================

struct ConfigParams {
  std::map<std::string, float> selections;
  std::map<std::string, std::string> strings;
};

ConfigParams parseConfigString(const std::string& configStr) {
  ConfigParams result;
  std::stringstream ss(configStr);
  std::string item;
  while (std::getline(ss, item, ';')) {
    size_t pos = item.find('=');
    if (pos == std::string::npos) continue;
    std::string key = item.substr(0, pos);
    std::string valueStr = item.substr(pos + 1);
    if (key == "inFileType" || key == "treeNames") {
      result.strings[key] = valueStr;
    } else {
      float value;
      if (valueStr == "true") value = true;
      else if (valueStr == "false") value = false;
      else value = std::stof(valueStr);
      result.selections[key] = value;
    }
  }
  return result;
}

// ======================== Progress bar ========================

void pbftp(double time_diff, int nprocessed, int ntotal) {
  double rate = (double)(nprocessed + 1) / time_diff;
  std::cout << "\r > " << nprocessed << " / " << ntotal
            << " | "   << std::fixed << std::setprecision(1) << 100 * (double)(nprocessed) / (double)(ntotal) << "%"
            << " | "   << std::fixed << std::setprecision(1) << rate << "Hz"
            << " | "   << std::fixed << std::setprecision(1) << time_diff / 60 << "m elapsed"
            << " | "   << std::fixed << std::setprecision(1) << (double)(ntotal - nprocessed) / (rate * 60) << "m remaining";
  std::cout << std::flush;
}

// ======================== Main ========================

int main(int argc, char* argv[]) {

  gErrorIgnoreLevel = kError;

  // Parse command line arguments
  std::string inFileName, outFileName, configStr;
  int doNEvents = -1;
  bool debug = false;
  size_t divide = 1;
  size_t thisdiv = 0;
  for (int i = 1; i < argc; i++) {
    if (strncmp(argv[i], "-i", 2) == 0) inFileName = argv[i + 1];
    if (strncmp(argv[i], "-o", 2) == 0) outFileName = argv[i + 1];
    if (strncmp(argv[i], "-c", 2) == 0) configStr = argv[i + 1];
    if (strncmp(argv[i], "-n", 2) == 0) doNEvents = std::stoi(argv[i + 1]);
    if (strncmp(argv[i], "--debug", 7) == 0) debug = true;
    if (strncmp(argv[i], "--divide", 8) == 0) divide = (size_t)(std::atoi(argv[i + 1]));
    if (strncmp(argv[i], "--thisdiv", 9) == 0) thisdiv = (size_t)(std::atoi(argv[i + 1]));
  }
  if (inFileName.empty()) {
    std::cout << "No input file name provided. Exiting" << std::endl;
    return 0;
  }
  if (outFileName.empty()) {
    outFileName = inFileName;
    outFileName.erase(outFileName.length() - 5);
    outFileName += "_thrust.root";
  }
  if (configStr.empty()) {
    std::cout << "No configuration string provided. Exiting" << std::endl;
    return 0;
  }

  ConfigParams config = parseConfigString(configStr);
  std::map<std::string, float> selMap = config.selections;
  std::string inFileType = config.strings["inFileType"];
  std::string tree = config.strings["treeNames"];

  // ======================== Input File ========================
  std::unique_ptr<TFile> f(new TFile(inFileName.c_str(), "READ"));

  const int maxPart = 500;
  unsigned long long uniqueID;
  int nParticle;
  bool passesNTupleAfterCut;
  Short_t pwflag[maxPart];
  float theta[maxPart], phi[maxPart], pt[maxPart];
  float d0[maxPart], z0[maxPart];
  Short_t ntpc[maxPart];
  float px[maxPart], py[maxPart], pz[maxPart], pmag[maxPart], mass[maxPart];
  Short_t charge[maxPart];
  int status[maxPart];

  // ======================== Output File ========================
  std::unique_ptr<TFile> fout(new TFile(outFileName.c_str(), "RECREATE"));

  // ======================== Selection Tree ========================
  std::unique_ptr<TTree> varDefs(new TTree("Selection", ""));
  int s_nTPC = selMap["nTPCcut"];
  float s_AbsCosThetaChg = selMap["chargedTracksAbsCosThCut"];
  float s_ptChg = selMap["ptCut"];
  float s_d0 = selMap["d0Cut"];
  float s_z0 = selMap["z0Cut"];
  float s_ENeu = selMap["ECut"];
  float s_AbsCosThetaNeu = selMap["neutralTracksAbsCosThCut"];
  float s_Ech = selMap["TotalTrkEnergyCut"];
  float s_AbsCosSTheta = selMap["AbsCosSThetaCut"];
  float s_NTrk = selMap["NTrkCut"];
  float s_NTrkPlusNeu = selMap["NeuNchCut"];
  float s_EVis = selMap["EVisCut"];
  float s_MissP = selMap["MissPCut"];
  bool s_ThrCh = selMap["keepChargedTracks"];
  bool s_ThrNeu = selMap["keepNeutralTracks"];
  bool s_ThrMissP = selMap["doMET"];
  varDefs->Branch("nTPC", &s_nTPC);
  varDefs->Branch("AbsCosThetaChg", &s_AbsCosThetaChg);
  varDefs->Branch("ptChg", &s_ptChg);
  varDefs->Branch("d0", &s_d0);
  varDefs->Branch("z0", &s_z0);
  varDefs->Branch("ENeu", &s_ENeu);
  varDefs->Branch("AbsCosThetaNeu", &s_AbsCosThetaNeu);
  varDefs->Branch("Ech", &s_Ech);
  varDefs->Branch("AbsCosSTheta", &s_AbsCosSTheta);
  varDefs->Branch("NTrk", &s_NTrk);
  varDefs->Branch("NTrkPlusNeu", &s_NTrkPlusNeu);
  varDefs->Branch("EVis", &s_EVis);
  varDefs->Branch("MissP", &s_MissP);
  varDefs->Branch("ThrCh", &s_ThrCh);
  varDefs->Branch("ThrNeu", &s_ThrNeu);
  varDefs->Branch("ThrMissP", &s_ThrMissP);
  varDefs->Fill();
  varDefs->Write();

  // ======================== Analysis Loop ========================

  std::chrono::time_point<std::chrono::system_clock> time_start;
  std::chrono::duration<double> elapsed_seconds;

  std::cout << TString::Format("Looping over tree: %s", tree.c_str()) << std::endl;
  bool genTree = tree == "tgen" || tree == "tgenBefore";
  std::unique_ptr<TTree> t((TTree*) f->Get(tree.c_str()));
  t->SetBranchAddress("uniqueID", &uniqueID);
  t->SetBranchAddress("nParticle", &nParticle);
  t->SetBranchAddress("passesNTupleAfterCut", &passesNTupleAfterCut);
  t->SetBranchAddress("pwflag", &pwflag);
  t->SetBranchAddress("theta", &theta);
  t->SetBranchAddress("phi", &phi);
  t->SetBranchAddress("pt", &pt);
  t->SetBranchAddress("d0", &d0);
  t->SetBranchAddress("z0", &z0);
  t->SetBranchAddress("ntpc", &ntpc);
  t->SetBranchAddress("px", &px);
  t->SetBranchAddress("py", &py);
  t->SetBranchAddress("pz", &pz);
  t->SetBranchAddress("pmag", &pmag);
  t->SetBranchAddress("mass", &mass);
  t->SetBranchAddress("charge", &charge);
  if (inFileType == "PYTHIA8") {
    t->SetBranchAddress("status", &status);
  }

  // Selected particle vectors (charged + neutral)
  std::vector<float> selectedPx, selectedPy, selectedPz;
  std::vector<float> selectedE, selectedMass;
  std::vector<float> selectedD0, selectedZ0;
  std::vector<Short_t> selectedNtpc, selectedPwflag;

  // Charged-only vectors
  std::vector<float> selectedChargedPx, selectedChargedPy, selectedChargedPz;

  // Create output tree
  std::unique_ptr<TTree> tout(new TTree(tree.c_str(), ""));
  unsigned long long uniqueIDCopy;
  float Thrust, TotalTrkEnergy, STheta, Sph, MissP, EVis, TTheta, RivetThrust, ChargedThrust;
  float CParameter, HeavyJetMass;
  float sprime;
  int NTrk, Neu, Nisr, NSelectedParticles;
  bool passEventSelection;
  tout->Branch("uniqueID", &uniqueIDCopy);
  tout->Branch("Thrust", &Thrust);
  tout->Branch("RivetThrust", &RivetThrust);
  tout->Branch("ChargedThrust", &ChargedThrust);
  tout->Branch("CParameter", &CParameter);
  tout->Branch("HeavyJetMass", &HeavyJetMass);
  tout->Branch("TotalTrkEnergy", &TotalTrkEnergy);
  tout->Branch("NTrk", &NTrk);
  tout->Branch("Neu", &Neu);
  tout->Branch("Nisr", &Nisr);
  tout->Branch("STheta", &STheta);
  tout->Branch("Sphericity", &Sph);
  tout->Branch("MissP", &MissP);
  tout->Branch("EVis", &EVis);
  tout->Branch("TTheta", &TTheta);
  tout->Branch("sprime", &sprime);
  tout->Branch("passEventSelection", &passEventSelection);
  tout->Branch("NSelectedParticles", &NSelectedParticles);
  tout->Branch("px", &selectedPx);
  tout->Branch("py", &selectedPy);
  tout->Branch("pz", &selectedPz);
  tout->Branch("energy", &selectedE);
  tout->Branch("mass", &selectedMass);
  tout->Branch("d0", &selectedD0);
  tout->Branch("z0", &selectedZ0);
  tout->Branch("ntpc", &selectedNtpc);
  tout->Branch("pwflag", &selectedPwflag);

  std::vector<float> conversionElectronTheta, conversionElectronPhi, conversionElectronPt;
  tout->Branch("conversionElectronTheta", &conversionElectronTheta);
  tout->Branch("conversionElectronPhi", &conversionElectronPhi);
  tout->Branch("conversionElectronPt", &conversionElectronPt);

  // ======================== Histograms ========================
  std::map<std::pair<int, std::string>, TH1D*> hists;
  for (int iP = 0; iP <= 5; iP++) {
    hists[{iP, "cosTheta"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_cosTheta").c_str(), ";cos#theta;Entries", 200, -1, 1);
    hists[{iP, "phi"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_phi").c_str(), ";#phi;Entries", 800, -4, 4);
    hists[{iP, "pt"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_pt").c_str(), ";p_{T} [GeV];Entries", 100, 0, 100);
    hists[{iP, "ntpc"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_ntpc").c_str(), ";N_{TPC};Entries", 31, -0.5, 30.5);
    hists[{iP, "d0"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_d0").c_str(), ";d_{0} [cm];Entries", 50, -2.5, 2.5);
    hists[{iP, "z0"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_z0").c_str(), ";z_{0} [cm];Entries", 300, -15, 15);
    hists[{iP, "pmag"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_pmag").c_str(), ";|#vec{p}| [GeV];Entries", 100, 0, 100);
    hists[{iP, "mass"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_mass").c_str(), ";Mass [GeV];Entries", 100, 0, 10);
    hists[{iP, "energy"}] = new TH1D(("h_pwflag" + std::to_string(iP) + "_energy").c_str(), ";Energy [GeV];Entries", 100, 0, 100);
  }
  hists[{0, "ntrk"}] = new TH1D("h_ntrk", ";N_{Trk};Entries", 61, -0.5, 60.5);
  hists[{0, "nneu"}] = new TH1D("h_nneu", ";N_{Neu};Entries", 51, -0.5, 50.5);
  hists[{0, "ntrkPlusNeu"}] = new TH1D("h_ntrkPlusNeu", ";N_{Trk+Neu};Entries", 81, -0.5, 80.5);
  hists[{0, "eCh"}] = new TH1D("h_eCh", ";E_{Ch} [GeV];Entries", 200, 0, 200);
  hists[{0, "cosThetaSph"}] = new TH1D("h_cosThetaSph", ";cos#theta_{Sph};Entries", 100, -1, 1);
  hists[{0, "sphericity"}] = new TH1D("h_sphericity", ";Sphericity;Entries", 100, 0, 1);
  hists[{0, "thrust"}] = new TH1D("h_thrust", ";Thrust;Entries", 100, 0.5, 1);
  hists[{0, "logtau"}] = new TH1D("h_logtau", ";log(#tau);Entries", 100, -10, 0);
  hists[{0, "missP"}] = new TH1D("h_missP", ";|#vec{p}_{MET}| [GeV];Entries", 100, 0, 100);
  hists[{0, "evis"}] = new TH1D("h_evis", ";E_{Vis} [GeV];Entries", 200, 0, 200);
  hists[{0, "sprime"}] = new TH1D("h_sprime", ";#sqrt{s'} [GeV];Entries", 180, 30, 120);
  hists[{0, "cosThetaThrust"}] = new TH1D("h_cosThetaThrust", ";cos#theta_{Thr};Entries", 100, -1, 1);

  // ======================== Event range ========================
  int nEvents = t->GetEntries();
  int evtperdiv = nEvents / divide;
  int startevt = evtperdiv * thisdiv;
  int endevt = (divide == (thisdiv + 1)) ? nEvents : evtperdiv * (thisdiv + 1);
  int ntotal = endevt - startevt;
  if (doNEvents != -1) {
    startevt = 0;
    endevt = doNEvents;
    ntotal = doNEvents;
  }
  std::cout << TString::Format("Total events %d, Events per division %d, Start event %d, End event %d, Analysing %d events",
                                nEvents, evtperdiv, startevt, endevt, ntotal) << std::endl;
  time_start = std::chrono::system_clock::now();

  // ======================== Event loop ========================
  for (int iE = startevt; iE < endevt; iE++) {

    if (!debug) {
      elapsed_seconds = (std::chrono::system_clock::now() - time_start);
      pbftp(elapsed_seconds.count(), iE + 1 - startevt, ntotal);
    }

    t->GetEntry(iE);
    uniqueIDCopy = uniqueID;

    // Reset per-event variables
    TotalTrkEnergy = 0; NTrk = 0; Neu = 0; Nisr = 0; EVis = 0;
    conversionElectronTheta.clear();
    conversionElectronPhi.clear();
    conversionElectronPt.clear();
    selectedPx.clear(); selectedPy.clear(); selectedPz.clear();
    selectedE.clear(); selectedMass.clear();
    selectedD0.clear(); selectedZ0.clear();
    selectedNtpc.clear(); selectedPwflag.clear();
    selectedChargedPx.clear(); selectedChargedPy.clear(); selectedChargedPz.clear();

    // ======================== Particle loop ========================
    for (int iP = 0; iP < nParticle; iP++) {

      if (debug) std::cout << TString::Format("iP %d, pwflag %d, theta %f, pt %f, d0 %f, z0 %f, ntpc %d, charge %i",
                                               iP, pwflag[iP], theta[iP], pt[iP], d0[iP], z0[iP], ntpc[iP], charge[iP]) << std::endl;

      float energy = TMath::Sqrt(pmag[iP] * pmag[iP] + mass[iP] * mass[iP]);
      float pxVal = px[iP], pyVal = py[iP], pzVal = pz[iP];
      bool saveParticle = false;

      if (genTree) saveParticle = true;

      // PYTHIA8: only save final state particles
      if (inFileType == "PYTHIA8") {
        if (status[iP] < 0) saveParticle = false;
        if (pwflag[iP] == 4) saveParticle = false;
      }

      // Count ISR near beampipe
      if (pwflag[iP] == 4 && charge[iP] == 0 && phi[iP] == 0 && TMath::Abs(TMath::Cos(theta[iP])) > 0.98) Nisr++;

      // ALEPH MC cleaning
      if (inFileType == "ALEPHMC") {
        // gen-level: remove beam-pipe radiation artifacts
        if (genTree && charge[iP] == 0 && std::abs(phi[iP]) <= 0.001 && pt[iP] > 0.00099 && pt[iP] < 0.001009)
          saveParticle = false;

        // Conversion electron cleaning
        bool isConversionElectron = (iP > 0)
          && (pwflag[iP] == 2) && (pwflag[iP - 1] == 2)
          && (charge[iP] == -(charge[iP - 1]))
          && (TMath::Abs(theta[iP] - theta[iP - 1]) <= 0.05)
          && (TMath::ACos(TMath::Cos(phi[iP] - phi[iP - 1])) <= 0.05);

        if (isConversionElectron) {
          saveParticle = false;
          if (!selectedPx.empty()) {
            selectedPx.pop_back(); selectedPy.pop_back(); selectedPz.pop_back();
            selectedE.pop_back(); selectedMass.pop_back();
            selectedD0.pop_back(); selectedZ0.pop_back();
            selectedNtpc.pop_back(); selectedPwflag.pop_back();
          }
          conversionElectronTheta.push_back(theta[iP]);
          conversionElectronPhi.push_back(phi[iP]);
          conversionElectronPt.push_back(pt[iP]);
        }
      }

      // Reco-level selections
      if (!genTree) {
        // Charged particle selection
        bool passChgTrkSel =
          (pwflag[iP] >= 0 && pwflag[iP] <= 2)
          && (TMath::Abs(cos(theta[iP])) <= selMap["chargedTracksAbsCosThCut"])
          && (pt[iP] >= selMap["ptCut"])
          && (TMath::Abs(d0[iP]) <= selMap["d0Cut"])
          && (TMath::Abs(z0[iP]) <= selMap["z0Cut"])
          && (ntpc[iP] >= selMap["nTPCcut"]);

        if (passChgTrkSel && selMap["keepChargedTracks"]) {
          if (debug) std::cout << "Passed charged track selection" << std::endl;
          saveParticle = true;
          TotalTrkEnergy += energy;
          EVis += energy;
          NTrk += 1;
        }

        // Neutral energy scale variation
        if (selMap["NES"] != -1 && (pwflag[iP] >= 3 && pwflag[iP] <= 5)) {
          energy *= selMap["NES"];
          pxVal *= selMap["NES"];
          pyVal *= selMap["NES"];
          pzVal *= selMap["NES"];
        }

        // Neutral particle selection
        bool passNeuPartSel =
          (pwflag[iP] >= 3 && pwflag[iP] <= 5)
          && (energy >= selMap["ECut"])
          && (TMath::Abs(cos(theta[iP])) <= selMap["neutralTracksAbsCosThCut"]);

        // Clean data neutral hadrons
        bool cleanDataNeutralHadron = (pwflag[iP] == 5) && (-0.19 <= cos(theta[iP]) && cos(theta[iP]) < -0.18);
        passNeuPartSel = passNeuPartSel && !cleanDataNeutralHadron;

        // Neutral efficiency variation
        if (selMap["NER"] != -1 && passNeuPartSel) {
          if (gRandom->Uniform() <= selMap["NER"]) passNeuPartSel = false;
        }

        if (passNeuPartSel && selMap["keepNeutralTracks"]) {
          if (debug) std::cout << "Passed neutral track selection" << std::endl;
          saveParticle = true;
          EVis += energy;
          Neu += 1;
        }
      }

      // Gen-level: count charged/neutral for event quantities
      if (genTree && saveParticle) {
        if (pwflag[iP] >= 0 && pwflag[iP] <= 2) {
          TotalTrkEnergy += energy; EVis += energy; NTrk += 1;
        } else if (pwflag[iP] >= 3 && pwflag[iP] <= 5) {
          EVis += energy; Neu += 1;
        }
      }

      // Save particle
      if (saveParticle) {
        selectedE.push_back(energy);
        selectedPx.push_back(pxVal);
        selectedPy.push_back(pyVal);
        selectedPz.push_back(pzVal);
        selectedMass.push_back(mass[iP]);
        selectedD0.push_back(d0[iP]);
        selectedZ0.push_back(z0[iP]);
        selectedNtpc.push_back(ntpc[iP]);
        selectedPwflag.push_back(pwflag[iP]);

        // Charged-only for charged thrust
        if (pwflag[iP] == 0) {
          selectedChargedPx.push_back(pxVal);
          selectedChargedPy.push_back(pyVal);
          selectedChargedPz.push_back(pzVal);
        }

        // Fill particle histograms
        if (inFileType != "PYTHIA8" && pwflag[iP] >= 0 && pwflag[iP] <= 5) {
          hists[{pwflag[iP], "cosTheta"}]->Fill(cos(theta[iP]));
          hists[{pwflag[iP], "phi"}]->Fill(phi[iP]);
          hists[{pwflag[iP], "pt"}]->Fill(pt[iP]);
          hists[{pwflag[iP], "ntpc"}]->Fill(ntpc[iP]);
          hists[{pwflag[iP], "d0"}]->Fill(d0[iP]);
          hists[{pwflag[iP], "z0"}]->Fill(z0[iP]);
          hists[{pwflag[iP], "pmag"}]->Fill(pmag[iP]);
          hists[{pwflag[iP], "mass"}]->Fill(mass[iP]);
          hists[{pwflag[iP], "energy"}]->Fill(energy);
        }
      }
    } // end particle loop

    int nSel = (int)selectedPx.size();

    // ======================== Sphericity ========================
    Sphericity spher(nSel, selectedPx.data(), selectedPy.data(), selectedPz.data(), selectedPwflag.data(), false);
    STheta = spher.sphericityAxis().Theta();
    Sph = spher.sphericity();

    // ======================== Missing momentum ========================
    TVector3 met(0, 0, 0);
    for (int it = 0; it < nSel; it++) {
      met += TVector3(selectedPx[it], selectedPy[it], selectedPz[it]);
    }
    met = -met;
    MissP = met.Mag();

    // ======================== Effective invariant mass ========================
    TLorentzVector Ptot(0, 0, 0, 0);
    for (int it = 0; it < nSel; it++) {
      TLorentzVector p4;
      p4.SetPxPyPzE(selectedPx[it], selectedPy[it], selectedPz[it], selectedE[it]);
      Ptot += p4;
    }
    sprime = Ptot.M();

    // ======================== C-parameter ========================
    CParameter = (nSel >= 2) ? spher.linC() : 0.0f;

    // Include MET in thrust calculation if requested
    if (selMap["doMET"]) {
      selectedPx.push_back(met.X());
      selectedPy.push_back(met.Y());
      selectedPz.push_back(met.Z());
      selectedE.push_back(met.Mag());
      selectedMass.push_back(0.0f);
      selectedD0.push_back(0.0f);
      selectedZ0.push_back(0.0f);
      selectedNtpc.push_back(-1);
      selectedPwflag.push_back(-1);
    }

    int nSelWithMET = (int)selectedPx.size();

    // ======================== Thrust ========================
    TVector3 thrustVec = getThrust(nSelWithMET, selectedPx.data(), selectedPy.data(), selectedPz.data(), THRUST::OPTIMAL);
    Thrust = thrustVec.Mag();
    TTheta = thrustVec.Theta();

    // Charged-only thrust
    int nCharged = (int)selectedChargedPx.size();
    TVector3 charged_thrust = getThrust(nCharged, selectedChargedPx.data(), selectedChargedPy.data(), selectedChargedPz.data(), THRUST::OPTIMAL);
    ChargedThrust = charged_thrust.Mag();

    // ======================== Rivet thrust ========================
    std::vector<TVector3> fsmomenta;
    double momentumSum = 0;
    for (int it = 0; it < nSelWithMET; it++) {
      fsmomenta.push_back(TVector3(selectedPx[it], selectedPy[it], selectedPz[it]));
      momentumSum += fsmomenta.back().Mag();
    }
    if (nSelWithMET >= 3 && momentumSum > 0.0) {
      TVector3 axis(0, 0, 0);
      double val = 0;
      _calcT(fsmomenta, val, axis);
      RivetThrust = val / momentumSum;
    } else {
      RivetThrust = Thrust;
    }

    // ======================== Heavy jet mass ========================
    HeavyJetMass = ComputeHeavyJetMass(nSelWithMET, selectedPx.data(), selectedPy.data(),
                                        selectedPz.data(), selectedE.data(), thrustVec);

    // ======================== Event selection ========================
    NSelectedParticles = nSel;
    bool eventSelection =
      passesNTupleAfterCut == 1
      && (TotalTrkEnergy >= selMap["TotalTrkEnergyCut"])
      && (TMath::Abs(TMath::Cos(STheta)) <= selMap["AbsCosSThetaCut"])
      && (NTrk >= selMap["NTrkCut"])
      && ((NTrk + Neu) >= selMap["NeuNchCut"])
      && (EVis >= selMap["EVisCut"])
      && (MissP < selMap["MissPCut"]);

    eventSelection = eventSelection || genTree;
    passEventSelection = eventSelection;

    if (eventSelection) {
      hists[{0, "ntrk"}]->Fill(NTrk);
      hists[{0, "nneu"}]->Fill(Neu);
      hists[{0, "ntrkPlusNeu"}]->Fill(NTrk + Neu);
      hists[{0, "eCh"}]->Fill(TotalTrkEnergy);
      hists[{0, "cosThetaSph"}]->Fill(TMath::Cos(STheta));
      hists[{0, "sphericity"}]->Fill(Sph);
      hists[{0, "thrust"}]->Fill(Thrust);
      hists[{0, "logtau"}]->Fill(TMath::Log(1 - Thrust));
      hists[{0, "missP"}]->Fill(MissP);
      hists[{0, "evis"}]->Fill(EVis);
      hists[{0, "sprime"}]->Fill(sprime);
      hists[{0, "cosThetaThrust"}]->Fill(TMath::Cos(TTheta));
    }

    tout->Fill();
  } // end event loop

  // Write output
  tout->Write();
  for (auto& entry : hists) {
    entry.second->Write();
  }

  std::cout << "\n" << std::endl;
  return 1;
}
