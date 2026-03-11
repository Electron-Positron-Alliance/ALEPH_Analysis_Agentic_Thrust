#ifndef THRUST_COMPUTE_H
#define THRUST_COMPUTE_H

#include "core/analysisParticles.h"
#include "observables/thrustTools.h"
#include "observables/rivetThrust.h"
#include "observables/sphericityTools.h"
#include "observables/heavyJetMass.h"

struct ThrustResult : CommonResult {
  float Thrust = 0.0f, RivetThrust = 0.0f, ChargedThrust = 0.0f;
  float CParameter = 0.0f, HeavyJetMass = 0.0f, TTheta = 0.0f;
};

inline ThrustResult ComputeThrustResult(unsigned int slot, const EventData& ev,
    const Selections& sel, const std::string& inFileType,
    bool genTree, bool debug, std::vector<TRandom3>& rngs) {

  auto parts = SelectParticles(slot, ev, sel, inFileType, genTree, debug, rngs);
  ThrustResult out;

  // Thrust
  TVector3 thrust = getThrust(parts.nSelected, parts.px.data(), parts.py.data(), parts.pz.data(), THRUST::OPTIMAL);
  out.Thrust = thrust.Mag();
  out.TTheta = thrust.Theta();

  // Charged-only thrust
  out.ChargedThrust = getThrust(parts.nCharged, parts.chargedPx.data(), parts.chargedPy.data(), parts.chargedPz.data(), THRUST::OPTIMAL).Mag();

  // Rivet thrust
  std::vector<TVector3> fsmomenta;
  double momentumSum = 0;
  for (int t = 0; t < parts.nSelected; t++) {
    fsmomenta.push_back(TVector3(parts.px[t], parts.py[t], parts.pz[t]));
    momentumSum += fsmomenta.back().Mag();
  }
  if (parts.nSelected >= 3 && momentumSum > 0.0) {
    TVector3 axis; double val = 0;
    _calcT(fsmomenta, val, axis);
    out.RivetThrust = val / momentumSum;
  } else {
    out.RivetThrust = out.Thrust;
  }

  // C-parameter
  if (parts.nSelected >= 2) {
    auto spher = Sphericity(parts.nSelected, parts.px.data(), parts.py.data(), parts.pz.data(), parts.pwflag.data(), false);
    out.CParameter = spher.linC();
  }

  // Heavy jet mass
  out.HeavyJetMass = ComputeHeavyJetMass(parts.nSelected, parts.px.data(), parts.py.data(),
                                           parts.pz.data(), parts.energy.data(), thrust);

  // Fill common fields from particles
  out.FillFromParticles(ev.uniqueID, parts, sel, ev.passesNTupleAfterCut, genTree);
  return out;
}

#endif
