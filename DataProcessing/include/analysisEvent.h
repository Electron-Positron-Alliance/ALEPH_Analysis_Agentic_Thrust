#ifndef ANALYSIS_EVENT_H
#define ANALYSIS_EVENT_H

#include "ROOT/RVec.hxx"

struct EventData {
  unsigned long long uniqueID = 0;
  int nParticle = 0;
  bool passesNTupleAfterCut = false;
  ROOT::RVec<Short_t> pwflag;
  ROOT::RVec<float> theta;
  ROOT::RVec<float> phi;
  ROOT::RVec<float> pt;
  ROOT::RVec<float> d0;
  ROOT::RVec<float> z0;
  ROOT::RVec<Short_t> ntpc;
  ROOT::RVec<float> px;
  ROOT::RVec<float> py;
  ROOT::RVec<float> pz;
  ROOT::RVec<float> pmag;
  ROOT::RVec<float> mass;
  ROOT::RVec<Short_t> charge;
  ROOT::RVec<int> statusSafe;
};

inline EventData MakeEventData(unsigned long long uniqueID,
                               int nParticle,
                               bool passesNTupleAfterCut,
                               const ROOT::RVec<Short_t>& pwflag,
                               const ROOT::RVec<float>& theta,
                               const ROOT::RVec<float>& phi,
                               const ROOT::RVec<float>& pt,
                               const ROOT::RVec<float>& d0,
                               const ROOT::RVec<float>& z0,
                               const ROOT::RVec<Short_t>& ntpc,
                               const ROOT::RVec<float>& px,
                               const ROOT::RVec<float>& py,
                               const ROOT::RVec<float>& pz,
                               const ROOT::RVec<float>& pmag,
                               const ROOT::RVec<float>& mass,
                               const ROOT::RVec<Short_t>& charge,
                               const ROOT::RVec<int>& statusSafe) {
  EventData ev;
  ev.uniqueID = uniqueID;
  ev.nParticle = nParticle;
  ev.passesNTupleAfterCut = passesNTupleAfterCut;
  ev.pwflag = pwflag;
  ev.theta = theta;
  ev.phi = phi;
  ev.pt = pt;
  ev.d0 = d0;
  ev.z0 = z0;
  ev.ntpc = ntpc;
  ev.px = px;
  ev.py = py;
  ev.pz = pz;
  ev.pmag = pmag;
  ev.mass = mass;
  ev.charge = charge;
  ev.statusSafe = statusSafe;
  return ev;
}

#endif
