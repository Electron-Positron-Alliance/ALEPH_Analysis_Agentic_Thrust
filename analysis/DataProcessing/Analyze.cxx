/*
Author: Anthony Badea
Purpose: Self-contained event loop for thrust analysis.
         Computes: Thrust, RivetThrust, ChargedThrust, CParameter, HeavyJetMass, Sphericity
         for a single mass scheme (p-scheme or e-scheme), selected via --mass-scheme flag.
         The mass scheme is applied before particle and event selections.
         Saves scheme-modified particle kinematics and event-level quantities.
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
#include "genISRTools.h"
#include "alephGenISRConversionCleaning.h"
#include "neutralSystematics.h"

// C++ standard
#include <vector>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <map>
#include <algorithm>
#include <cmath>

// ======================== pwflag derivation for external generators ============
// Maps PDG ID + charge to the ALEPH pwflag scheme used by the archived MC:
//   0 = charged hadron,  1 = electron,  2 = muon,
//   4 = photon,          5 = neutral hadron
// Called per-particle for external generators (PYTHIA8, Herwig, Sherpa)
// where the input ROOT files store pdgid but not a reliable pwflag.
Short_t pwflagFromPdgId(int pdgid, Short_t charge) {
  int abspid = TMath::Abs(pdgid);
  if (abspid == 11) return 1;   // electron / positron
  if (abspid == 13) return 2;   // muon
  if (abspid == 22) return 4;   // photon
  if (charge == 0)  return 5;   // neutral hadron (K0L, neutron, etc.)
  return 0;                     // charged hadron
}

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
  std::string inFileName, outFileName, configStr, massScheme;
  int doNEvents = -1;
  bool debug = false;
  bool genIsr = false;
  bool convClean = false;
  unsigned long long randomSeed = 12345ULL;
  size_t divide = 1;
  size_t thisdiv = 0;
  for (int i = 1; i < argc; i++) {
    if (strncmp(argv[i], "-i", 2) == 0) inFileName = argv[i + 1];
    if (strncmp(argv[i], "-o", 2) == 0) outFileName = argv[i + 1];
    if (strncmp(argv[i], "-c", 2) == 0) configStr = argv[i + 1];
    if (strncmp(argv[i], "-n", 2) == 0) doNEvents = std::stoi(argv[i + 1]);
    if (strncmp(argv[i], "--debug", 7) == 0) debug = true;
    if (strncmp(argv[i], "--gen-isr", 9) == 0) genIsr = true;
    if (strncmp(argv[i], "--conv-clean", 12) == 0) convClean = true;
    if (strncmp(argv[i], "--divide", 8) == 0) divide = (size_t)(std::atoi(argv[i + 1]));
    if (strncmp(argv[i], "--thisdiv", 9) == 0) thisdiv = (size_t)(std::atoi(argv[i + 1]));
    if (strncmp(argv[i], "--mass-scheme", 13) == 0) massScheme = argv[i + 1];
    if (strncmp(argv[i], "--seed", 6) == 0) randomSeed = std::stoull(argv[i + 1]);
  }
  if (massScheme != "p" && massScheme != "e" && massScheme != "none") {
    std::cerr << "ERROR: must specify --mass-scheme p|e|none." << std::endl;
    return 2;
  }
  bool pScheme = (massScheme == "p");
  bool noScheme = (massScheme == "none");
  if (inFileName.empty()) {
    std::cerr << "ERROR: no input file name provided." << std::endl;
    return 2;
  }
  if (outFileName.empty()) {
    outFileName = inFileName;
    outFileName.erase(outFileName.length() - 5);
    outFileName += "_thrust.root";
  }
  if (configStr.empty()) {
    std::cerr << "ERROR: no configuration string provided." << std::endl;
    return 2;
  }
  if (divide == 0 || thisdiv >= divide) {
    std::cerr << "ERROR: require --divide > 0 and --thisdiv < --divide." << std::endl;
    return 2;
  }
  if (doNEvents < -1) {
    std::cerr << "ERROR: -n must be -1 (all events) or non-negative." << std::endl;
    return 2;
  }

  ConfigParams config = parseConfigString(configStr);
  std::map<std::string, float> selMap = config.selections;
  std::string inFileType = config.strings["inFileType"];
  std::string tree = config.strings["treeNames"];
  bool neeEnabled = selMap["NEE_PHOTON"] > 0.0f
      || selMap["NEE_HADRON"] > 0.0f;

  // ======================== Input File ========================
  std::unique_ptr<TFile> f(TFile::Open(inFileName.c_str(), "READ"));
  if (!f || f->IsZombie()) {
    std::cerr << "ERROR: could not open input ROOT file: " << inFileName << std::endl;
    return 2;
  }
  TTree* t = nullptr;
  f->GetObject(tree.c_str(), t);
  if (!t) {
    std::cerr << "ERROR: input tree '" << tree << "' not found in " << inFileName << std::endl;
    return 2;
  }

  const int maxPart = 500;
  unsigned long long uniqueID;
  int nParticle;
  bool passesNTupleAfterCut;
  Short_t pwflag[maxPart];
  float theta[maxPart];
  float phi[maxPart];
  float pt[maxPart];
  float d0[maxPart];
  float z0[maxPart];
  Short_t ntpc[maxPart];
  float px[maxPart];
  float py[maxPart];
  float pz[maxPart];
  float pmag[maxPart];
  float mass[maxPart];
  Short_t charge[maxPart];
  int status[maxPart] = {};
  int pdgid[maxPart] = {};
  // ISR-study arrays (only populated when --gen-isr is passed)
  int mother1[maxPart] = {};
  int mother2[maxPart] = {};
  int daughter1[maxPart] = {};
  int daughter2[maxPart] = {};
  float energyBr[maxPart] = {};

  // ======================== Output File ========================
  std::unique_ptr<TFile> fout(TFile::Open(outFileName.c_str(), "RECREATE"));
  if (!fout || fout->IsZombie()) {
    std::cerr << "ERROR: could not create output ROOT file: " << outFileName << std::endl;
    return 2;
  }

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
  // Store mass scheme as an integer: 0 = p-scheme, 1 = e-scheme, 2 = none (raw)
  int s_massScheme = noScheme ? 2 : (pScheme ? 0 : 1);
  varDefs->Branch("massScheme", &s_massScheme);
  varDefs->Fill();
  varDefs->Write();

  // ======================== Analysis Loop ========================

  std::chrono::time_point<std::chrono::system_clock> time_start;
  std::chrono::duration<double> elapsed_seconds;

  std::cout << TString::Format("Looping over tree: %s", tree.c_str()) << std::endl;
  bool genTree = tree == "tgen" || tree == "tgenBefore";
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
  // Map the file type to a generator enum once; the set of known external
  // generators lives solely in genISRTools::parseGenerator (Unknown => not one).
  // This also gives the final-state predicate below a valid enum even when
  // --gen-isr is off (the ISR-study branches are only read under genIsr).
  genISRTools::Generator genEnum = genISRTools::parseGenerator(inFileType);
  bool hasGenealogy = genISRTools::hasGenealogy(genEnum);
  // The archived ALEPH Pythia 6.1 MC is not an "external generator" (no particle
  // genealogy in the ntuple), but its ISR photons can be groomed by a kinematic tag.
  bool alephGenIsr = (genEnum == genISRTools::Generator::ALEPHMC);
  if (hasGenealogy) {
    t->SetBranchAddress("status", &status);
    t->SetBranchAddress("pdgid", &pdgid);
  }

  // --gen-isr is valid only on the gen-level tree, for an external generator OR the
  // archived ALEPHMC (which uses the kinematic ISR-placeholder tag instead of the walk).
  if (genIsr && (!genTree || !(hasGenealogy || alephGenIsr))) {
    std::cerr << "ERROR: --gen-isr requires tree=tgenBefore (or tgen) with an external MC generator or the archived ALEPHMC (see genISRTools::parseGenerator)." << std::endl;
    return 2;
  }
  // The genealogy branches exist only for external generators; the ALEPHMC tag needs none.
  if (genIsr && hasGenealogy) {
    t->SetBranchAddress("mother1",   &mother1);
    t->SetBranchAddress("mother2",   &mother2);
    t->SetBranchAddress("daughter1", &daughter1);
    t->SetBranchAddress("daughter2", &daughter2);
    t->SetBranchAddress("energy",    &energyBr);
  }

  // Selected particle vectors (scheme-modified)
  std::vector<float> selectedPx, selectedPy, selectedPz;
  std::vector<float> selectedE, selectedMass;
  std::vector<float> selectedD0, selectedZ0;
  std::vector<Short_t> selectedNtpc, selectedPwflag;

  // Charged-only 3-momenta (scheme-modified)
  std::vector<float> selectedChargedPx, selectedChargedPy, selectedChargedPz;

  // Original input-tree index for each selected particle (filled when --gen-isr
  // or --conv-clean). Parallel to selectedPx/Py/Pz; used by maskedThrust to look
  // up the per-raw-index removal masks (isrEvt.cascadeMask / conversion masks).
  std::vector<int> selectedIdx;

  // Create output tree
  std::unique_ptr<TTree> tout(new TTree(tree.c_str(), ""));
  unsigned long long uniqueIDCopy;
  // Event-level quantities (scheme-independent, from raw kinematics)
  float TotalTrkEnergy;
  float STheta;
  float MissP;
  float EVis;
  int NTrk;
  int Neu;
  int Nphoton;
  int Nhadron;
  int Nisr;
  int NSelectedParticles;
  bool passEventSelection;
  // Observables (single scheme)
  float Thrust;
  float RivetThrust;
  float ChargedThrust;
  float CParameter;
  float HeavyJetMass;
  float Sphericity_val;
  float TTheta;
  float sprime;

  // Event-level branches
  tout->Branch("uniqueID", &uniqueIDCopy);
  tout->Branch("TotalTrkEnergy", &TotalTrkEnergy);
  tout->Branch("NTrk", &NTrk);
  tout->Branch("Neu", &Neu);
  tout->Branch("Nisr", &Nisr);
  tout->Branch("STheta", &STheta);
  tout->Branch("MissP", &MissP);
  tout->Branch("EVis", &EVis);
  tout->Branch("passEventSelection", &passEventSelection);
  tout->Branch("NSelectedParticles", &NSelectedParticles);
  // Observable branches (single scheme)
  tout->Branch("Thrust", &Thrust);
  tout->Branch("RivetThrust", &RivetThrust);
  tout->Branch("ChargedThrust", &ChargedThrust);
  tout->Branch("CParameter", &CParameter);
  tout->Branch("HeavyJetMass", &HeavyJetMass);
  tout->Branch("Sphericity", &Sphericity_val);
  tout->Branch("TTheta", &TTheta);
  tout->Branch("sprime", &sprime);
  // Raw particle kinematics
  tout->Branch("px", &selectedPx);
  tout->Branch("py", &selectedPy);
  tout->Branch("pz", &selectedPz);
  tout->Branch("energy", &selectedE);
  tout->Branch("mass", &selectedMass);
  tout->Branch("d0", &selectedD0);
  tout->Branch("z0", &selectedZ0);
  tout->Branch("ntpc", &selectedNtpc);
  tout->Branch("pwflag", &selectedPwflag);

  // ISR-study branches (only written when --gen-isr)
  int Nisr_cls = 0, Nisr_hard = 0, Ndesc = 0;
  float Thrust_GroomedISR = 1.0f;
  std::vector<float> isrE, isrCosTh;
  std::vector<int>   descPdgId;
  if (genIsr) {
    tout->Branch("Nisr_cls",         &Nisr_cls);
    tout->Branch("Nisr_hard",        &Nisr_hard);
    tout->Branch("Ndesc",            &Ndesc);
    tout->Branch("Thrust_GroomedISR",&Thrust_GroomedISR);
    tout->Branch("isrE",             &isrE);
    tout->Branch("isrCosTh",         &isrCosTh);
    tout->Branch("descPdgId",        &descPdgId);
  }

  // Conversion-cleaning study branches (only written when --conv-clean): the thrust
  // recomputed after removing reconstructed photon-conversion pairs, under pwflag==1
  // (electron, the physical selector) and pwflag==2 (muon, the previously used one).
  float Thrust_ConvClean1 = 1.0f;
  float Thrust_ConvClean2 = 1.0f;
  // Diagnostic: kinematics of the tracks the conversion cleaning removes. Per removed
  // track (energy, pt, cos(theta)) and per removed pair (opening angle, invariant mass),
  // filled in the same loop that builds the removal mask, separately for pwflag==1/2.
  std::vector<float> convTrkE1, convTrkPt1, convTrkCosTheta1;
  std::vector<float> convTrkE2, convTrkPt2, convTrkCosTheta2;
  std::vector<float> convPairOpen1, convPairMass1;
  std::vector<float> convPairOpen2, convPairMass2;
  if (convClean) {
    tout->Branch("Thrust_ConvClean1", &Thrust_ConvClean1);
    tout->Branch("Thrust_ConvClean2", &Thrust_ConvClean2);
    tout->Branch("convTrkE1", &convTrkE1);
    tout->Branch("convTrkPt1", &convTrkPt1);
    tout->Branch("convTrkCosTheta1", &convTrkCosTheta1);
    tout->Branch("convTrkE2", &convTrkE2);
    tout->Branch("convTrkPt2", &convTrkPt2);
    tout->Branch("convTrkCosTheta2", &convTrkCosTheta2);
    tout->Branch("convPairOpen1", &convPairOpen1);
    tout->Branch("convPairMass1", &convPairMass1);
    tout->Branch("convPairOpen2", &convPairOpen2);
    tout->Branch("convPairMass2", &convPairMass2);
  }

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
  hists[{0, "nphoton"}] = new TH1D("h_nphoton", ";N_{photon};Entries", 51, -0.5, 50.5);
  hists[{0, "nhadron"}] = new TH1D("h_nhadron", ";N_{neutral hadron};Entries", 51, -0.5, 50.5);
  hists[{0, "ntrkPlusNeu"}] = new TH1D("h_ntrkPlusNeu", ";N_{Trk+Neu};Entries", 81, -0.5, 80.5);
  hists[{0, "eCh"}] = new TH1D("h_eCh", ";E_{Ch} [GeV];Entries", 200, 0, 200);
  hists[{0, "cosThetaSph"}] = new TH1D("h_cosThetaSph", ";cos#theta_{Sph};Entries", 100, -1, 1);
  hists[{0, "sphericity"}] = new TH1D("h_sphericity", ";Sphericity;Entries", 100, 0, 1);
  hists[{0, "thrust"}] = new TH1D("h_thrust", ";Thrust;Entries", 100, 0.5, 1);
  hists[{0, "tau"}] = new TH1D("h_tau", ";#tau;Entries", 100, 0, 0.5);
  hists[{0, "logtau"}] = new TH1D("h_logtau", ";log(#tau);Entries", 100, -10, 0);
  hists[{0, "missP"}] = new TH1D("h_missP", ";|#vec{p}_{MET}| [GeV];Entries", 100, 0, 100);
  hists[{0, "evis"}] = new TH1D("h_evis", ";E_{Vis} [GeV];Entries", 200, 0, 200);
  hists[{0, "sprime"}] = new TH1D("h_sprime", ";#sqrt{s'} [GeV];Entries", 180, 30, 120);
  hists[{0, "cosThetaThrust"}] = new TH1D("h_cosThetaThrust", ";cos#theta_{Thr};Entries", 100, -1, 1);

  // ======================== Event range ========================
  int nEvents = t->GetEntries();
  // -n is a global prefix limit for this input, not a per-worker limit. Split
  // that prefix into disjoint contiguous ranges, preserving the historical
  // convention that any remainder belongs to the last division.
  int nRequested = (doNEvents == -1) ? nEvents : std::min(doNEvents, nEvents);
  int evtperdiv = nRequested / divide;
  int startevt = evtperdiv * thisdiv;
  int endevt = (divide == (thisdiv + 1)) ? nRequested : evtperdiv * (thisdiv + 1);
  int ntotal = endevt - startevt;
  std::cout << TString::Format("Total events %d, Requested events %d, Events per division %d, Start event %d, End event %d, Analysing %d events",
                                nEvents, nRequested, evtperdiv, startevt, endevt, ntotal) << std::endl;
  time_start = std::chrono::system_clock::now();

  // ======================== Event loop ========================
  for (int iE = startevt; iE < endevt; iE++) {

    if (!debug) {
      elapsed_seconds = (std::chrono::system_clock::now() - time_start);
      pbftp(elapsed_seconds.count(), iE + 1 - startevt, ntotal);
    }

    t->GetEntry(iE);
    uniqueIDCopy = uniqueID;
    if (!genTree && neeEnabled) {
      ULong_t eventSeed = static_cast<ULong_t>(randomSeed + uniqueID);
      gRandom->SetSeed(eventSeed == 0 ? 1 : eventSeed);
    }

    // Reset per-event variables
    TotalTrkEnergy = 0;
    NTrk = 0;
    Neu = 0;
    Nphoton = 0;
    Nhadron = 0;
    Nisr = 0;
    EVis = 0;
    selectedPx.clear(); selectedPy.clear(); selectedPz.clear();
    selectedE.clear(); selectedMass.clear();
    selectedD0.clear(); selectedZ0.clear();
    selectedNtpc.clear(); selectedPwflag.clear();
    selectedChargedPx.clear(); selectedChargedPy.clear(); selectedChargedPz.clear();
    // selectedIdx is parallel to the selected* vectors and must reset every event
    // for BOTH studies (was previously cleared only under --gen-isr, corrupting
    // --conv-clean-only runs where it accumulated across events).
    if (genIsr || convClean) selectedIdx.clear();

    // ISR-study per-event reset + classification
    genISRTools::EventISR isrEvt;
    if (genIsr) {
      Nisr_cls = 0;
      Nisr_hard = 0;
      Ndesc = 0;
      Thrust_GroomedISR = 1.0f;
      isrE.clear();
      isrCosTh.clear();
      descPdgId.clear();
      if (hasGenealogy) {
        // External generators: classify ISR by walking the particle genealogy.
        isrEvt = genISRTools::computeEventISR(
            genEnum, nParticle,
            pdgid, status, mother1, mother2, daughter1, daughter2,
            px, py, pz, energyBr);
      } else if (alephGenIsr) {
        // Archived ALEPHMC: no genealogy in the ntuple, so tag ISR photons
        // kinematically (beam-collinear placeholder photons). See genISRTools.h.
        isrEvt = genISRTools::computeEventISR_ALEPHMC(
            nParticle, pwflag, charge, phi, pt, pmag, mass, theta);
      }
      Nisr_cls  = isrEvt.nIsr;
      Nisr_hard = isrEvt.nIsrHard;
      Ndesc     = isrEvt.nDesc;
      isrE      = isrEvt.isrE;
      isrCosTh  = isrEvt.isrCosTh;
      descPdgId = isrEvt.descPdgId;
    }

    // Conversion-pair cleaning study: build the two removal masks + diagnostic
    // kinematics over the raw particle record (see alephGenISRConversionCleaning.h).
    // The masks are applied at thrust time via maskedThrust; the diagnostics are
    // copied into the persistent branch vectors so the output tree carries them.
    convCleanTools::ConvClean cc;
    if (convClean) {
      cc = convCleanTools::computeConvClean(nParticle, pwflag, charge, theta, phi,
                                            px, py, pz, pt, mass);
      convTrkE1 = cc.trkE1;
      convTrkPt1 = cc.trkPt1;
      convTrkCosTheta1 = cc.trkCosTheta1;
      convTrkE2 = cc.trkE2;
      convTrkPt2 = cc.trkPt2;
      convTrkCosTheta2 = cc.trkCosTheta2;
      convPairOpen1 = cc.pairOpen1;
      convPairMass1 = cc.pairMass1;
      convPairOpen2 = cc.pairOpen2;
      convPairMass2 = cc.pairMass2;
    }

    // ======================== Particle loop ========================
    for (int iP = 0; iP < nParticle; iP++) {

      if (debug) std::cout << TString::Format("iP %d, pwflag %d, theta %f, pt %f, d0 %f, z0 %f, ntpc %d, charge %i, status %d",
                                               iP, pwflag[iP], theta[iP], pt[iP], d0[iP], z0[iP], ntpc[iP], charge[iP], status[iP]) << std::endl;

      // External generators store the full event record; skip non-final particles.
      // Final-state rule is centralized in genISRTools::isFinalState (PYTHIA8/KKMCee/
      // Vincia: status>0; Herwig/Sherpa HepMC: status==1).
      if (hasGenealogy && genTree) {
        if (!genISRTools::isFinalState(genEnum, status[iP])) continue;
      }

      // Derive pwflag from pdgid for external generators.
      // The generator ROOT files store pdgid; pwflag is an ALEPH reconstruction
      // concept that we map onto here for consistency with archived MC selections.
      if (hasGenealogy) {
        pwflag[iP] = pwflagFromPdgId(pdgid[iP], charge[iP]);
      }

      // Physical energy
      float energy = TMath::Sqrt(pmag[iP] * pmag[iP] + mass[iP] * mass[iP]);
      float pxVal = px[iP];
      float pyVal = py[iP];
      float pzVal = pz[iP];
      bool saveParticle = false;

      if (genTree) saveParticle = true;

      // Count ISR near beampipe
      if (pwflag[iP] == 4 && charge[iP] == 0 && phi[iP] == 0 && TMath::Abs(TMath::Cos(theta[iP])) > 0.98) Nisr++;

      // // ALEPH MC gen-level: remove beam-pipe radiation artifacts
      // if (inFileType == "ALEPHMC" && genTree && charge[iP] == 0 && std::abs(phi[iP]) <= 0.001 && pt[iP] > 0.00099 && pt[iP] < 0.001009){
      // 	saveParticle = false;
      // }

      // Per-pwflag Neutral Energy Scale (NES) variation (reco only,
      // before mass scheme). Photons (pwflag 4) and neutral hadrons
      // (pwflag 5) are scaled independently; V0s (pwflag 3) are
      // reconstructed via charged decay tracks and are intentionally
      // not subject to a calorimetric-scale uncertainty.
      if (!genTree) {
        float nes_scale = neutralSystematics::nesScale(
            pwflag[iP], selMap["NES_PHOTON"], selMap["NES_HADRON"]);
        if (nes_scale != 1.0) {
          energy *= nes_scale;
          pxVal  *= nes_scale;
          pyVal  *= nes_scale;
          pzVal  *= nes_scale;
        }
      }

      // Apply mass scheme transformation (before all selections)
      if (!noScheme) {
        float pMag_i = std::sqrt(pxVal*pxVal + pyVal*pyVal + pzVal*pzVal);
        if (pScheme) {
          energy = pMag_i;  // E = |p|
        } else {
          if (pMag_i > 0.0f) {
            float scale = energy / pMag_i;
            pxVal *= scale;
            pyVal *= scale;
            pzVal *= scale;
          }
        }
      }

      // Reco-level selections (using scheme-modified quantities)
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

        // Neutral particle selection
        bool passNeuPartSel =
          (pwflag[iP] >= 3 && pwflag[iP] <= 5)
          && (energy >= selMap["ECut"])
          && (TMath::Abs(cos(theta[iP])) <= selMap["neutralTracksAbsCosThCut"]);

        // Per-pwflag Neutral Energy Efficiency (NEE) variation. Photons
        // (pwflag 4) and neutral hadrons (pwflag 5) get independent drop
        // probabilities; V0s (pwflag 3) are not subject to a calorimetric
        // efficiency uncertainty and are not dropped.
        if (passNeuPartSel && neutralSystematics::dropForNEE(
            pwflag[iP], selMap["NEE_PHOTON"], selMap["NEE_HADRON"])) {
          passNeuPartSel = false;
        }

        // Previous-ALEPH neutral cross-check: exclude neutral energy-flow
        // objects with 1 < E < 2 GeV, reproducing the 2004 ALEPH measurement
        // (Heister et al., Eur. Phys. J. C 35:457). Applied to all neutral
        // objects (pwflag 3-5). Used only as a cross-check, not in the band.
        if (passNeuPartSel && selMap["excludeNeutral1to2GeV"] == 1 && energy >= 1.0 && energy <= 2.0) {
          passNeuPartSel = false;
        }

        if (passNeuPartSel && selMap["keepNeutralTracks"]) {
          if (debug) std::cout << "Passed neutral track selection" << std::endl;
          saveParticle = true;
          EVis += energy;
          Neu += 1;
          if (pwflag[iP] == 4) {
            Nphoton += 1;
          } else if (pwflag[iP] == 5) {
            Nhadron += 1;
          }
        }
      }

      // Gen-level: count charged/neutral for event quantities
      if (genTree && saveParticle) {
        if (pwflag[iP] >= 0 && pwflag[iP] <= 2) {
          TotalTrkEnergy += energy;
          EVis += energy;
          NTrk += 1;
        } else if (pwflag[iP] >= 3 && pwflag[iP] <= 5) {
          EVis += energy;
          Neu += 1;
          if (pwflag[iP] == 4) {
            Nphoton += 1;
          } else if (pwflag[iP] == 5) {
            Nhadron += 1;
          }
        }
      }

      // Save scheme-modified particle
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

        // Charged-only 3-momenta (scheme-modified)
        if (pwflag[iP] >= 0 && pwflag[iP] <= 2) {
          selectedChargedPx.push_back(pxVal);
          selectedChargedPy.push_back(pyVal);
          selectedChargedPz.push_back(pzVal);
        }

        // Record original index so Thrust_GroomedISR / Thrust_ConvClean can look up
        // the per-particle removal masks directly at thrust time.
        if (genIsr || convClean) {
          selectedIdx.push_back(iP);
        }

        // Fill particle histograms
        if (!hasGenealogy && pwflag[iP] >= 0 && pwflag[iP] <= 5) {
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

    // ================================================================
    // Observables (scheme already applied to selectedPx/Py/Pz/E)
    // ================================================================

    // Sphericity
    Sphericity spher(nSel, selectedPx.data(), selectedPy.data(), selectedPz.data(), selectedPwflag.data(), false);
    STheta = spher.sphericityAxis().Theta();  // used for event selection
    Sphericity_val = spher.sphericity();
    CParameter = (nSel >= 2) ? spher.linC() : 0.0f;

    // Missing momentum
    TVector3 met(0, 0, 0);
    for (int it = 0; it < nSel; it++) {
      met += TVector3(selectedPx[it], selectedPy[it], selectedPz[it]);
    }
    met = -met;
    MissP = met.Mag();

    // sprime
    TLorentzVector Ptot(0, 0, 0, 0);
    for (int it = 0; it < nSel; it++) {
      TLorentzVector p4;
      p4.SetPxPyPzE(selectedPx[it], selectedPy[it], selectedPz[it], selectedE[it]);
      Ptot += p4;
    }
    sprime = Ptot.M();

    // Thrust (+ optional MET pseudo-particle)
    std::vector<float> thrPx(selectedPx), thrPy(selectedPy), thrPz(selectedPz);
    std::vector<float> thrE(selectedE);
    if (selMap["doMET"]) {
      thrPx.push_back(met.X());
      thrPy.push_back(met.Y());
      thrPz.push_back(met.Z());
      thrE.push_back(met.Mag());
    }
    int nSelWithMET = (int)thrPx.size();

    TVector3 thrustVec = getThrust(nSelWithMET, thrPx.data(), thrPy.data(), thrPz.data(), THRUST::OPTIMAL);
    Thrust = thrustVec.Mag();
    TTheta = thrustVec.Theta();

    // ISR-cascade-removed thrust: selected momenta minus the tagged ISR photons.
    if (genIsr) {
      Thrust_GroomedISR = maskedThrust(selectedPx, selectedPy, selectedPz,
                                       selectedIdx, isrEvt.cascadeMask);
    }

    // Conversion-cleaned thrusts: selected momenta minus the flagged conversion
    // pairs, for the pwflag==1 and pwflag==2 masks respectively.
    if (convClean) {
      Thrust_ConvClean1 = maskedThrust(selectedPx, selectedPy, selectedPz,
                                       selectedIdx, cc.mask1);
      Thrust_ConvClean2 = maskedThrust(selectedPx, selectedPy, selectedPz,
                                       selectedIdx, cc.mask2);
    }

    // Charged thrust
    int nChg = (int)selectedChargedPx.size();
    TVector3 chgThrustVec = getThrust(nChg, selectedChargedPx.data(), selectedChargedPy.data(), selectedChargedPz.data(), THRUST::OPTIMAL);
    ChargedThrust = chgThrustVec.Mag();

    // Rivet thrust
    std::vector<TVector3> fsmom;
    double momSum = 0;
    for (int it = 0; it < nSelWithMET; it++) {
      fsmom.push_back(TVector3(thrPx[it], thrPy[it], thrPz[it]));
      momSum += fsmom.back().Mag();
    }
    if (nSelWithMET >= 3 && momSum > 0.0) {
      TVector3 axis(0, 0, 0);
      double val = 0;
      _calcT(fsmom, val, axis);
      RivetThrust = val / momSum;
    } else {
      RivetThrust = Thrust;
    }

    // Heavy jet mass
    HeavyJetMass = ComputeHeavyJetMass(nSelWithMET, thrPx.data(), thrPy.data(),
                                         thrPz.data(), thrE.data(), thrustVec);

    // ======================== Event selection ========================
    // Uses scheme-modified quantities (STheta, MissP, EVis, TotalTrkEnergy)
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
      hists[{0, "nphoton"}]->Fill(Nphoton);
      hists[{0, "nhadron"}]->Fill(Nhadron);
      hists[{0, "ntrkPlusNeu"}]->Fill(NTrk + Neu);
      hists[{0, "eCh"}]->Fill(TotalTrkEnergy);
      hists[{0, "cosThetaSph"}]->Fill(TMath::Cos(STheta));
      hists[{0, "sphericity"}]->Fill(Sphericity_val);
      hists[{0, "thrust"}]->Fill(Thrust);
      hists[{0, "tau"}]->Fill(1 - Thrust);
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
  return 0;
}
