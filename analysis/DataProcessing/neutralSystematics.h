#ifndef NEUTRAL_SYSTEMATICS_H
#define NEUTRAL_SYSTEMATICS_H

#include "TRandom.h"

namespace neutralSystematics {

constexpr int kPhotonPwflag = 4;
constexpr int kNeutralHadronPwflag = 5;

inline float nesScale(int pwflag, float photonScale, float hadronScale) {
  if (pwflag == kPhotonPwflag && photonScale != -1.0f) return photonScale;
  if (pwflag == kNeutralHadronPwflag && hadronScale != -1.0f) return hadronScale;
  return 1.0f;
}

inline bool dropForNEE(int pwflag, float photonProbability,
                       float hadronProbability) {
  if (pwflag == kPhotonPwflag && photonProbability > 0.0f) {
    return gRandom->Uniform() < photonProbability;
  }
  if (pwflag == kNeutralHadronPwflag && hadronProbability > 0.0f) {
    return gRandom->Uniform() < hadronProbability;
  }
  return false;
}

}  // namespace neutralSystematics

#endif  // NEUTRAL_SYSTEMATICS_H
