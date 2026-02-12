#ifndef ANALYSIS_COMPUTE_H
#define ANALYSIS_COMPUTE_H

#include "analysisEvent.h"
#include "analysisTypes.h"
#include "rivetThrust.h"
#include "sphericityTools.h"
#include "thrustTools.h"

#include "TMath.h"
#include "TString.h"
#include "TRandom3.h"
#include "TVector3.h"
#include "TLorentzVector.h"

#include <cmath>
#include <iostream>
#include <string>
#include <vector>

EventResult ComputeEventResult(unsigned int slot,
                               const EventData& ev,
                               const Selections& sel,
                               const std::string& inFileType,
                               bool genTree,
                               bool debug,
                               std::vector<TRandom3>& rngs) {
  EventResult out;
  out.uniqueID = ev.uniqueID;

  // vectors for selected objects (single selection now) -> charged and neutral particles
  int selectedParts = 0;
  std::vector<float> selectedPx, selectedPy, selectedPz;
  std::vector<float> selectedE;
  std::vector<Short_t> selectedPwflag;

  // vectors for selected objects -> charged particle only
  int selectedChargedParts = 0;
  std::vector<float> selectedChargedPx, selectedChargedPy, selectedChargedPz;

  // reset variables for single selection
  float TotalTrkEnergy = 0.0f;
  int NTrk = 0;
  int Neu = 0;
  int Nisr = 0;
  float EVis = 0.0f;
  out.conversionElectronTheta.clear();
  out.conversionElectronPhi.clear();
  out.conversionElectronPt.clear();

  // loop over particles
  for (int iP = 0; iP < ev.nParticle; iP++) {
    if (debug) {
      std::cout << TString::Format("iP %d, pwflag %d, theta %f, pt %f, d0 %f, z0 %f, ntpc %d, charge %i",
                                   iP, ev.pwflag[iP], ev.theta[iP], ev.pt[iP], ev.d0[iP], ev.z0[iP], ev.ntpc[iP], ev.charge[iP]) << std::endl;
    }

    // compute the particle energy
    float energy = TMath::Sqrt(ev.pmag[iP] * ev.pmag[iP] + ev.mass[iP] * ev.mass[iP]);
    float pxVal = ev.px[iP];
    float pyVal = ev.py[iP];
    float pzVal = ev.pz[iP];

    // fill and save
    bool saveParticle = false;

    // nominally all gen passes
    if (genTree) saveParticle = true;

    // pythia8 only save final state particles
    if (inFileType == "PYTHIA8") {
      if (ev.statusSafe[iP] < 0) saveParticle = false;
      if (ev.pwflag[iP] == 4) saveParticle = false;
    }

    // count number of ISR near to beampipe
    if (ev.pwflag[iP] == 4 && ev.charge[iP] == 0 && ev.phi[iP] == 0 && TMath::Abs(TMath::Cos(ev.theta[iP])) > 0.98) Nisr++;

    // special cleaning for ALEPH MC
    if (inFileType == "ALEPHMC") {
      // gen only cleaning neutral cleaning around phi = 0 for photon radiation along beam pipe
      if (genTree && ev.charge[iP] == 0 && std::abs(ev.phi[iP]) <= 0.001 && ev.pt[iP] > 0.00099 && ev.pt[iP] < 0.001009)
        saveParticle = false;

      // apply conversion cleaning only to archived aleph MC reco and gen
      if (IsConversionElectron(iP, ev.pwflag, ev.charge, ev.theta, ev.phi)) {
        // if conversion electron then don't save particle and remove previous particle also
        saveParticle = false;
        if (!selectedPx.empty()) {
          selectedParts -= 1;
          selectedPx.pop_back();
          selectedPy.pop_back();
          selectedPz.pop_back();
          selectedPwflag.pop_back();
        }
        // conversion electrons
        out.conversionElectronTheta.push_back(ev.theta[iP]);
        out.conversionElectronPhi.push_back(ev.phi[iP]);
        out.conversionElectronPt.push_back(ev.pt[iP]);
      }
    }

    // apply reco level selections
    if (!genTree) {
      // charged particle selections
      bool passChgTrkSel = PassChargedTrack(ev.pwflag[iP], ev.theta[iP], ev.pt[iP], ev.d0[iP], ev.z0[iP], ev.ntpc[iP], sel);

      if (passChgTrkSel && sel.keepChargedTracks) {
        if (debug) std::cout << "Passed charged track selection" << std::endl;
        saveParticle = true;
        TotalTrkEnergy += energy;
        EVis += energy;
        NTrk += 1;
      }

      // perform neutral particle energy scaling
      if (sel.NES != -1 && (ev.pwflag[iP] >= 3 && ev.pwflag[iP] <= 5)) {
        energy *= sel.NES;
        pxVal *= sel.NES;
        pyVal *= sel.NES;
        pzVal *= sel.NES;
      }

      // neutral particle selections
      bool passNeuPartSel = PassNeutral(ev.pwflag[iP], energy, ev.theta[iP], sel);

      // add cleaning for data neutral hadrons (pwflag 5) -0.19 <= cos(theta) < -0.18
      passNeuPartSel = passNeuPartSel && !CleanDataNeutralHadron(ev.pwflag[iP], ev.theta[iP]);

      // neutral particle efficiency variation
      if (sel.NER != -1) {
        if (passNeuPartSel) {
          TRandom3& rng = rngs[slot < rngs.size() ? slot : 0];
          double r = rng.Uniform(); // uniform random number between 0 and 1
          if (r <= sel.NER) {
            passNeuPartSel = false;
          }
        }
      }

      if (passNeuPartSel && sel.keepNeutralTracks) {
        if (debug) std::cout << "Passed neutral track selection" << std::endl;
        saveParticle = true;
        EVis += energy;
        Neu += 1;
      }
    }

    // save the particle
    if (saveParticle) {
      // save for event shape variables
      selectedParts += 1;
      selectedE.push_back(energy);
      selectedPx.push_back(pxVal);
      selectedPy.push_back(pyVal);
      selectedPz.push_back(pzVal);
      selectedPwflag.push_back(ev.pwflag[iP]);

      // save charged particles only (pwflag == 0)
      if (ev.pwflag[iP] == 0) {
        selectedChargedParts += 1;
        selectedChargedPx.push_back(pxVal);
        selectedChargedPy.push_back(pyVal);
        selectedChargedPz.push_back(pzVal);
      }
    }
  }

  // calculate total momentum vector
  TLorentzVector Ptot(0, 0, 0, 0);
  for (int t = 0; t < selectedParts; t++) {
      TLorentzVector p4;
      p4.SetPxPyPzE(selectedPx.at(t), selectedPy.at(t), selectedPz.at(t), selectedE.at(t));
      Ptot += p4;
    }
  // Effective invariant mass
  out.sprime = Ptot.M(); // sqrt(s')
  // out.sprime2 = Ptot.M2(); // s'

  // sphericity
  auto spher = Sphericity(selectedParts, selectedPx.data(), selectedPy.data(), selectedPz.data(), selectedPwflag.data(), false);
  out.STheta = spher.sphericityAxis().Theta();
  out.Sphericity = spher.sphericity();

  // calculate the missing momentum vector
  TVector3 met(0, 0, 0);
  for (int t = 0; t < selectedParts; t++) {
    met += TVector3(selectedPx.at(t), selectedPy.at(t), selectedPz.at(t));
  }
  met = -met;
  out.MissP = met.Mag();

  // include missing momentum vector in thrust calculation
  if (sel.doMET) {
    selectedParts += 1;
    selectedPx.push_back(met.X());
    selectedPy.push_back(met.Y());
    selectedPz.push_back(met.Z());
    selectedPwflag.push_back(-1);
  }

  // thrust
  TVector3 thrust = getThrust(selectedParts, selectedPx.data(), selectedPy.data(), selectedPz.data(), THRUST::OPTIMAL);
  out.Thrust = thrust.Mag();
  out.TTheta = thrust.Theta();

  // charged particle only thrust
  TVector3 charged_thrust = getThrust(selectedChargedParts, selectedChargedPx.data(), selectedChargedPy.data(), selectedChargedPz.data(), THRUST::OPTIMAL);
  out.ChargedThrust = charged_thrust.Mag();

  // rivet thrust
  std::vector<TVector3> fsmomenta;
  double momentumSum = 0;
  for (int t = 0; t < selectedParts; t++) {
    fsmomenta.push_back(TVector3(selectedPx.at(t), selectedPy.at(t), selectedPz.at(t)));
    momentumSum += fsmomenta.at(t).Mag();
  }
  TVector3 axis(0, 0, 0);
  double val = 0;
  _calcT(fsmomenta, val, axis);
  out.RivetThrust = val / momentumSum;

  // compute event selection passes
  bool eventSelection =
      ev.passesNTupleAfterCut == 1 && (TotalTrkEnergy >= sel.TotalTrkEnergyCut) &&
      (TMath::Abs(TMath::Cos(out.STheta)) <= sel.AbsCosSThetaCut) && (NTrk >= sel.NTrkCut) &&
      ((NTrk + Neu) >= sel.NeuNchCut) && (EVis >= sel.EVisCut) && (out.MissP < sel.MissPCut);

  // gen always passes event selection
  eventSelection = eventSelection || genTree;

  out.passEventSelection = eventSelection;
  out.TotalTrkEnergy = TotalTrkEnergy;
  out.NTrk = NTrk;
  out.Neu = Neu;
  out.Nisr = Nisr;
  out.EVis = EVis;

  out.NSelectedParticles = selectedParts;
  out.px = std::move(selectedPx);
  out.py = std::move(selectedPy);
  out.pz = std::move(selectedPz);
  out.pwflag = std::move(selectedPwflag);
  return out;
}

#endif
