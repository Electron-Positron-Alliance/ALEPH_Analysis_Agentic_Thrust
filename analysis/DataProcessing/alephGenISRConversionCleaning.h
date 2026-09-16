#ifndef ALEPHGENISRCONVERSIONCLEANING_H
#define ALEPHGENISRCONVERSIONCLEANING_H

// ---------------------------------------------------------------------------
// Photon-conversion cleaning study (preliminary in-simulation cleaning, used
// as a cross-check against the adopted KKMCee C_ISR correction).
//
// The pairing is the verbatim ed28add "isConversionElectron" condition:
// consecutive particles in the record, same pwflag, opposite charge, collinear
// (|dtheta| <= 0.05 and acos(cos dphi) <= 0.05). It is applied twice: for
// pwflag==1 (electron, the physical conversion selector) and pwflag==2 (muon,
// the value the previous cleaning actually used). Unlike ed28add -- which
// removed only the earlier track -- BOTH tracks of a pair are masked here,
// since a photon conversion produces two fake tracks.
//
// computeConvClean() runs over the raw particle record and returns the two
// removal masks (indexed by raw particle index; apply with maskedThrust from
// thrustTools.h) plus per-track / per-pair diagnostic kinematics. Note the
// archived reco assigns the pion mass to all charged tracks, so the pair
// invariant mass floors near 2*m_pi and is a kinematic proxy, not a true
// conversion tagger.
// ---------------------------------------------------------------------------

#include <vector>
#include <cstdint>

#include "TMath.h"

namespace convCleanTools {

  struct ConvClean {
    // Removal masks over the raw particle record (1 = drop), one per pwflag.
    std::vector<uint8_t> mask1;   // pwflag==1 (electron)
    std::vector<uint8_t> mask2;   // pwflag==2 (muon)
    // Per removed track (both tracks of each pair pushed), split by pwflag.
    std::vector<float> trkE1, trkPt1, trkCosTheta1;
    std::vector<float> trkE2, trkPt2, trkCosTheta2;
    // Per removed pair, split by pwflag.
    std::vector<float> pairOpen1, pairMass1;
    std::vector<float> pairOpen2, pairMass2;
  };

  inline ConvClean computeConvClean(int nParticle,
                                    const short* pwflag,
                                    const short* charge,
                                    const float* theta,
                                    const float* phi,
                                    const float* px,
                                    const float* py,
                                    const float* pz,
                                    const float* pt,
                                    const float* mass) {
    ConvClean out;
    out.mask1.assign(nParticle, 0);
    out.mask2.assign(nParticle, 0);

    for (int iP = 1; iP < nParticle; ++iP) {
      for (int flag = 1; flag <= 2; ++flag) {
        bool isConversionElectron = (pwflag[iP] == flag)
          && (pwflag[iP - 1] == flag)
          && (charge[iP] == -(charge[iP - 1]))
          && (TMath::Abs(theta[iP] - theta[iP - 1]) <= 0.05)
          && (TMath::ACos(TMath::Cos(phi[iP] - phi[iP - 1])) <= 0.05);
        if (!isConversionElectron) {
          continue;
        }

        std::vector<uint8_t>& mask = (flag == 1) ? out.mask1 : out.mask2;
        mask[iP] = 1;
        mask[iP - 1] = 1;

        // Removed-pair kinematics (both tracks) for diagnostics.
        const int a = iP - 1;
        const int b = iP;
        const float Ea = TMath::Sqrt(px[a]*px[a] + py[a]*py[a] + pz[a]*pz[a] + mass[a]*mass[a]);
        const float Eb = TMath::Sqrt(px[b]*px[b] + py[b]*py[b] + pz[b]*pz[b] + mass[b]*mass[b]);
        const float dot = px[a]*px[b] + py[a]*py[b] + pz[a]*pz[b];
        const float pa = TMath::Sqrt(px[a]*px[a] + py[a]*py[a] + pz[a]*pz[a]);
        const float pb = TMath::Sqrt(px[b]*px[b] + py[b]*py[b] + pz[b]*pz[b]);
        const float openAng = TMath::ACos(TMath::Max(-1.0f, TMath::Min(1.0f, dot / (pa * pb))));
        const float m2 = (Ea + Eb)*(Ea + Eb)
                       - (px[a] + px[b])*(px[a] + px[b])
                       - (py[a] + py[b])*(py[a] + py[b])
                       - (pz[a] + pz[b])*(pz[a] + pz[b]);
        const float pairMass = (m2 > 0.0f) ? TMath::Sqrt(m2) : 0.0f;

        std::vector<float>& vE   = (flag == 1) ? out.trkE1 : out.trkE2;
        std::vector<float>& vPt  = (flag == 1) ? out.trkPt1 : out.trkPt2;
        std::vector<float>& vCth = (flag == 1) ? out.trkCosTheta1 : out.trkCosTheta2;
        std::vector<float>& vOp  = (flag == 1) ? out.pairOpen1 : out.pairOpen2;
        std::vector<float>& vM   = (flag == 1) ? out.pairMass1 : out.pairMass2;
        vE.push_back(Ea);
        vE.push_back(Eb);
        vPt.push_back(pt[a]);
        vPt.push_back(pt[b]);
        vCth.push_back(TMath::Cos(theta[a]));
        vCth.push_back(TMath::Cos(theta[b]));
        vOp.push_back(openAng);
        vM.push_back(pairMass);
      }
    }
    return out;
  }

} // namespace convCleanTools

#endif // ALEPHGENISRCONVERSIONCLEANING_H
