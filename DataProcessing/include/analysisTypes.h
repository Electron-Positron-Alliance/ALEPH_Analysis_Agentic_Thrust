#ifndef ANALYSIS_TYPES_H
#define ANALYSIS_TYPES_H

#include "TMath.h"
#include "TVector3.h"

#include "ROOT/RVec.hxx"

#include <vector>

struct Selections {
  int nTPCcut = 0;
  float chargedTracksAbsCosThCut = 0.0f;
  float ptCut = 0.0f;
  float d0Cut = 0.0f;
  float z0Cut = 0.0f;
  float ECut = 0.0f;
  float neutralTracksAbsCosThCut = 0.0f;
  float TotalTrkEnergyCut = 0.0f;
  float AbsCosSThetaCut = 0.0f;
  float NTrkCut = 0.0f;
  float NeuNchCut = 0.0f;
  float EVisCut = 0.0f;
  float MissPCut = 0.0f;
  float NES = -1.0f;
  float NER = -1.0f;
  bool keepChargedTracks = false;
  bool keepNeutralTracks = false;
  bool doMET = false;
};

inline bool PassChargedTrack(Short_t pwflag, float theta, float pt, float d0, float z0, Short_t ntpc, const Selections& sel) {
  return (pwflag >= 0 && pwflag <= 2) &&
         (TMath::Abs(cos(theta)) <= sel.chargedTracksAbsCosThCut) &&
         (pt >= sel.ptCut) &&
         (TMath::Abs(d0) <= sel.d0Cut) &&
         (TMath::Abs(z0) <= sel.z0Cut) &&
         (ntpc >= sel.nTPCcut);
}

inline bool PassNeutral(Short_t pwflag, float energy, float theta, const Selections& sel) {
  return (pwflag >= 3 && pwflag <= 5) &&
         (energy >= sel.ECut) &&
         (TMath::Abs(cos(theta)) <= sel.neutralTracksAbsCosThCut);
}

inline bool IsConversionElectron(int iP,
                                 const ROOT::RVec<Short_t>& pwflag,
                                 const ROOT::RVec<Short_t>& charge,
                                 const ROOT::RVec<float>& theta,
                                 const ROOT::RVec<float>& phi) {
  if (iP <= 0) return false;
  if (pwflag[iP] != 2) return false;
  if (pwflag[iP - 1] != 2) return false;
  if (charge[iP] != -(charge[iP - 1])) return false;
  const float conversionDPhi = 0.05f;
  const float conversionDTheta = 0.05f;
  if (TMath::Abs(theta[iP] - theta[iP - 1]) > conversionDTheta) return false;
  if (TMath::ACos(TMath::Cos(phi[iP] - phi[iP - 1])) > conversionDPhi) return false;
  return true;
}

inline bool CleanDataNeutralHadron(Short_t pwflag, float theta) {
  const float ctheta = cos(theta);
  return (pwflag == 5) && (-0.19f <= ctheta && ctheta < -0.18f);
}

struct EventResult {
  unsigned long long uniqueID = 0;
  float Thrust = 0.0f;
  float RivetThrust = 0.0f;
  float ChargedThrust = 0.0f;
  float TotalTrkEnergy = 0.0f;
  float STheta = 0.0f;
  float Sphericity = 0.0f;
  float MissP = 0.0f;
  float EVis = 0.0f;
  float TTheta = 0.0f;
  float sprime = 0.0f;
  int NTrk = 0;
  int Neu = 0;
  int Nisr = 0;
  bool passEventSelection = false;
  int NSelectedParticles = 0;
  std::vector<float> px;
  std::vector<float> py;
  std::vector<float> pz;
  std::vector<Short_t> pwflag;
  std::vector<float> conversionElectronTheta;
  std::vector<float> conversionElectronPhi;
  std::vector<float> conversionElectronPt;
};

#endif
