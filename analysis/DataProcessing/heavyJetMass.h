#ifndef HEAVY_JET_MASS_H
#define HEAVY_JET_MASS_H

#include "TMath.h"
#include "TVector3.h"
#include "TLorentzVector.h"

#include <algorithm>
#include <cmath>

inline float ComputeHeavyJetMass(int nParts, const float* px, const float* py, const float* pz,
                                  const float* energy, const TVector3& thrustAxis) {
  if (nParts < 2 || thrustAxis.Mag() <= 0.0f) return 0.0f;

  const TVector3 thrust_axis = thrustAxis.Unit();
  TLorentzVector hemiPos(0, 0, 0, 0);
  TLorentzVector hemiNeg(0, 0, 0, 0);
  TLorentzVector eventP4(0, 0, 0, 0);

  for (int t = 0; t < nParts; ++t) {
    TLorentzVector p4;
    p4.SetPxPyPzE(px[t], py[t], pz[t], energy[t]);
    eventP4 += p4;
    const TVector3 pvec(px[t], py[t], pz[t]);
    if (pvec.Dot(thrust_axis) >= 0.0) hemiPos += p4;
    else hemiNeg += p4;
  }

  const double eventM2 = eventP4.M2();
  if (eventM2 > 0.0) {
    const double m2Pos = std::max(0.0, static_cast<double>(hemiPos.M2()));
    const double m2Neg = std::max(0.0, static_cast<double>(hemiNeg.M2()));
    return static_cast<float>(std::max(m2Pos, m2Neg) / eventM2);
  }
  return 0.0f;
}

#endif
