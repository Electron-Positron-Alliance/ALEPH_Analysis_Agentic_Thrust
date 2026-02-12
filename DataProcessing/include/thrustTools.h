#ifndef THRUSTTOOLS
#define THRUSTTOOLS

//c++ dependencies
#include <vector>
#include <iostream>

//ROOT dependencies
#include "TVector3.h"
#include "TMath.h"

inline TVector3 getPerpVector(TVector3 v) {
  TVector3 tempV = v;
  tempV.Rotate(TMath::Pi() / 2.0, TVector3(0, 0, 1).Cross(tempV.Unit()));
  if (TMath::Abs(tempV.Phi() - v.Phi()) > 1) tempV = -tempV;
  return tempV;
}

inline double ptFromThrust(TVector3 thrust, TVector3 p, bool doPerpThrust = false) {
  if (doPerpThrust) thrust = getPerpVector(thrust);
  return p.Perp(thrust);
}

inline double thetaFromThrust(TVector3 thrust, TVector3 p, bool doPerpThrust = false) {
  if (doPerpThrust) thrust = getPerpVector(thrust);
  return p.Angle(thrust);
}

inline bool checkEtaThrustPIs1(TVector3 thrust, TVector3 p)
{
  Double_t minDel = 0.01;
  Double_t thrust0 = thrust[0] / p[0];
  Double_t thrust1 = thrust[1] / p[1];
  Double_t thrust2 = thrust[2] / p[2];

  return TMath::Abs(thrust0 - thrust1) < minDel && TMath::Abs(thrust0 - thrust2) < minDel && TMath::Abs(thrust1 - thrust2) < minDel;
}

//this is actually rapidity w/ mass given
inline double rapFromThrust(TVector3 thrust, TVector3 p, float mass, bool doPerpThrust = false) {
  if (doPerpThrust) thrust = getPerpVector(thrust);
  //  Double_t minDel = 0.01;
  //  if(mass < minDel && checkEtaThrustPIs1(thrust, p)) return 99.;
  float pl = p * (thrust.Unit()); //logitudinal momentum component
  float E = TMath::Power(p.Mag2() + mass * mass, 0.5); //energy
  double rap = 0.5 * TMath::Log((E + pl) / (E - pl));
  if (rap > 99.) rap = 99.;
  else if (rap < -99.) rap = -99.;
  return rap;//rapidity
}

inline double etaFromThrust(TVector3 thrust, TVector3 p, bool doPerpThrust = false) {
  if (doPerpThrust) thrust = getPerpVector(thrust);
  //  Double_t minDel = 0.000001;
  //  if(TMath::Abs(thrust[0]) < minDel && TMath::Abs(thrust[1]) < minDel && TMath::Abs(thrust[2]) < minDel) return 99.;
  //  else if(checkEtaThrustPIs1(thrust, p)) return 99.;
  double eta = -TMath::Log( TMath::Tan( thetaFromThrust(thrust, p) / 2.0));
  if (eta > 99.) eta = 99.;
  else if (eta < -99.) eta = -99.;
  return -TMath::Log( TMath::Tan( thetaFromThrust(thrust, p) / 2.0));
}

inline double phiFromThrust(TVector3 thrust, TVector3 p, bool doPerpThrust = false) {
  if (doPerpThrust) thrust = getPerpVector(thrust);
  TVector3 pt = p - ((p * thrust.Unit()) * (thrust.Unit())); //pt vector
  TVector3 z = TVector3(0, 0, 1);
  TVector3 phiOrigin = thrust.Unit().Cross((thrust.Unit().Cross(z)));//vector that will be phi=0 (in plane of thrust and beam line
  double phi = pt.Angle(phiOrigin);//get phi from 0 to pi

  //determine sign of phi based on cross product of pt and origin
  if ( (phiOrigin.Cross(pt.Unit()))*thrust >= 0) return phi;
  else return -phi;
}

/* Almost a direct copy and paste from Belle standard Thrust axis algorithm */
template <class Iterator, class Function>
TVector3 thrustBelleSTD(Iterator begin, Iterator end, Function func)
{
  // Temporary variables
  Iterator p, q;
  TVector3 rvec, Axis;

  double sump = 0;
  for (p = begin; p != end; p++)
    sump += ((TVector3)func(*p)).Mag();

  // Thrust and thrust vectors

  double Thru = 0;
  for (p = begin; p != end; p++) {
    TVector3 rvec(func(*p));
    if (rvec.z() <= 0.0) rvec = -rvec;

    double s = rvec.Mag();
    if (s != 0.0) rvec *= (1 / s);

    for (Iterator loopcount = begin; loopcount != end; loopcount++) {
      TVector3 rprev(rvec);
      rvec = TVector3(); // clear

      for (q = begin; q != end; q++) {
        const TVector3 qvec(func(*q));
        rvec += (qvec.Dot(rprev) >= 0) ? qvec : - qvec;
      }

      for (q = begin; q != end; q++) {
        const TVector3 qvec(func(*q));
        if (qvec.Dot(rvec) * qvec.Dot(rprev) < 0) break;
      }

      if (q == end) break;
    }

    double ttmp = 0.0;
    for (q = begin; q != end; q++) {
      const TVector3 qvec = func(*q);
      ttmp += std::fabs(qvec.Dot(rvec));
    }
    ttmp /= (sump * rvec.Mag());
    rvec *= 1 / rvec.Mag();
    if (ttmp > Thru) {
      Thru = ttmp;
      Axis = rvec;
    }
  }
  Axis *= Thru;
  return Axis;
}

// ----------------------------------------------------------------------
// SelfFunc - retrieve the pointer to a function which returns itself
// example:
//   list<Vector3> vl;
//   Vector3 t = thrust(vl.begin(), vp.end(), SelfFunc(Vector3()));
//
//   list<Vector3 *> vp;
//   Vector3 t = thrust(vp.begin(), vp.end(), SelfFunc(Vector3()));
// ----------------------------------------------------------------------

template <class T>
class ptr_to_self_func {
protected:
  typedef T (*pfun)(T &);
public:
  ptr_to_self_func() : ptr(NULL) {};
  T operator()(T& t) const { return t; };
  T operator()(T *t) const { return *t; };
  const T operator()(const T& t) const { return t; };
  const T operator()(const T *t) const { return *t; };
protected:
  const pfun ptr;
};

template <class T>
ptr_to_self_func<T> SelfFunc(const T &) {
  return ptr_to_self_func<T>();
}

/* wrapper of the Belle thrust axis algorithm */
TVector3 getThrustBelle(int n, float *px, float *py, float *pz, bool doWeight = false, bool doInvertWeight = false, float* weight = NULL) {
  std::vector<TVector3> momenta;
  for (int i = 0; i < n; ++i) {
    if (doWeight && (!doInvertWeight)) {
      momenta.push_back(TVector3(px[i]*weight[i], py[i]*weight[i], pz[i]*weight[i]));
      continue;
    }
    if (doWeight && doInvertWeight) {
      momenta.push_back(TVector3(px[i] / weight[i], py[i] / weight[i], pz[i] / weight[i]));
      continue;
    }
    momenta.push_back(TVector3(px[i], py[i], pz[i]));
  }
  return thrustBelleSTD(momenta.begin(), momenta.end(), SelfFunc(TVector3()));
}

TVector3 getSpecialThrustBelle(int n, float *px, float *py, float *pz, Short_t *pwflag, bool doCharged = true) {
  std::vector<TVector3> momenta;
  for (int i = 0; i < n; ++i) {
    if (!(pwflag[i] == 0 || pwflag[i] == 1 || pwflag[i] == 2) && doCharged) continue;
    if (pwflag[i] <= 2 && !doCharged) continue;
    momenta.push_back(TVector3(px[i], py[i], pz[i]));
  }
  return thrustBelleSTD(momenta.begin(), momenta.end(), SelfFunc(TVector3()));
}

//based on code from herwig: http://herwig.hepforge.org/svn/tags/herwig-2-0-beta/Analysis/EventShapes.cc
//ported by A. Baty
//n is number of particles, px,py,pz are arrays of momentum components
TVector3 getThrustHerwig(int n, float *px, float *py, float *pz, bool doWeight = false, bool doInvertWeight = false, float* weight = NULL, bool doMET = false, Short_t *pwflag = NULL) {
  TVector3 thrust = TVector3(0, 0, 0);
  float pSum = 0;

  if (doWeight && (!doInvertWeight)) {
    for (int t = 0; t < n; t++) {
      px[t] *= weight[t];
      py[t] *= weight[t];
      pz[t] *= weight[t];
    }
  }
  if (doWeight && doInvertWeight) {
    for (int t = 0; t < n; t++) {
      px[t] /= weight[t];
      py[t] /= weight[t];
      pz[t] /= weight[t];
    }
  }

  TVector3 met = TVector3(0, 0, 0);
  for (int t = 0; t < n; t++) {
    if (pwflag != NULL && pwflag[t] < 0) continue;
    pSum += TVector3(px[t], py[t], pz[t]).Mag();
    met += (TVector3(px[t], py[t], pz[t]));
  }

  if (n <= 0) return thrust;
  else if (n == 1) { //thrust is just the particle
    thrust = TVector3(px[0], py[0], pz[0]);
  }
  else if (n == 2) { //special case for 2 particles
    bool pick0 = TMath::Power(px[0], 2) + TMath::Power(py[0], 2) + TMath::Power(pz[0], 2) >= TMath::Power(px[1], 2) + TMath::Power(py[1], 2) + TMath::Power(pz[1], 2);

    if (pick0) thrust = TVector3(px[0], py[0], pz[0]);
    else thrust = TVector3(px[1], py[1], pz[1]);
  }
  else if (n == 3) { //combine lowest 2 magnitude momentum, then use same algo as n=2 CHRIS: SOMETHING SEEMS WRONG HERE BASED ON DESCRIPTION? No combination is done, just picking mag max
    bool pick0Over1 = TMath::Power(px[0], 2) + TMath::Power(py[0], 2) + TMath::Power(pz[0], 2) >= TMath::Power(px[1], 2) + TMath::Power(py[1], 2) + TMath::Power(pz[1], 2);

    if (pick0Over1) {
      bool pick0Over2 = TMath::Power(px[0], 2) + TMath::Power(py[0], 2) + TMath::Power(pz[0], 2) >= TMath::Power(px[2], 2) + TMath::Power(py[2], 2) + TMath::Power(pz[2], 2);

      if (pick0Over2) thrust = TVector3(px[0], py[0], pz[0]);
      else thrust = TVector3(px[2], py[2], pz[2]);
    }
    else {
      bool pick1Over2 = TMath::Power(px[1], 2) + TMath::Power(py[1], 2) + TMath::Power(pz[1], 2) >= TMath::Power(px[2], 2) + TMath::Power(py[2], 2) + TMath::Power(pz[2], 2);

      if (pick1Over2) thrust = TVector3(px[1], py[1], pz[1]);
      else thrust = TVector3(px[2], py[2], pz[2]);
    }
  }
  else if (n > 3) {
    //make vector of TVector3's of each particle
    std::vector< TVector3 > pVec;
    for (int i = 0; i < n; i++) {
      if (pwflag != NULL && pwflag[i] < 0) continue;
      pVec.push_back(TVector3(px[i], py[i], pz[i]));
    }
    //std::cout << pVecs.at(0).x();
    //reset n because it might be smaller from skipping neutrinos
    if (pwflag != NULL) n = pVec.size();

    //add MET vector to list
    if (doMET) {
      n = n + 1;
      pVec.push_back(-met);
      pSum += met.Mag();
    }

    TVector3 cross;
    float t = 0;
    for (int i = 1; i < n; i++) { //loop through all possible cross products of 2 unique vectors
      for (int j = 0; j < i; j++) {
        cross = pVec.at(i).Cross(pVec.at(j));
        TVector3 ptot = TVector3(0, 0, 0);

        for (int k = 0; k < n; k++) { //loop through all 3rd particles not used for the cross product
          if (k != i && k != j) {
            if (pVec.at(k)*cross > 0) { //if dot product is >0
              ptot += pVec.at(k);
            }
            else {
              ptot -= pVec.at(k);
            }
          }
        }

        std::vector< TVector3 > cpm;//add or subtract in last 2 vectors used for cross product
        cpm.push_back(ptot - pVec.at(j) - pVec.at(i));
        cpm.push_back(ptot - pVec.at(j) + pVec.at(i));
        cpm.push_back(ptot + pVec.at(j) - pVec.at(i));
        cpm.push_back(ptot + pVec.at(j) + pVec.at(i));
        for (std::vector<TVector3>::iterator it = cpm.begin(); it != cpm.end(); it++) {
          float tval = (*it).Mag2();
          if (tval > t) {
            t = tval;
            thrust = *it;
          }
        }
      }
    }
  }

  if (doWeight && (!doInvertWeight)) {
    for (int t = 0; t < n; t++) {
      px[t] /= weight[t];
      py[t] /= weight[t];
      pz[t] /= weight[t];
    }
  }
  if (doWeight && doInvertWeight) {
    for (int t = 0; t < n; t++) {
      px[t] *= weight[t];
      py[t] *= weight[t];
      pz[t] *= weight[t];
    }
  }

  thrust.SetMag(thrust.Mag() / pSum);
  return thrust;
}

//almost a straight copy of above, but filter for pwflag==0 (tracks)
TVector3 getSpecialThrustHerwig(int n, float *px, float *py, float *pz, Short_t *pwflag, bool doCharged = true) {
  float nTrk = 0;
  float pSum = 0;
  for (int t = 0; t < n; t++) {
    if (!(pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && doCharged) continue;
    if (pwflag[t] <= 2 && !doCharged) continue;
    pSum += TVector3(px[t], py[t], pz[t]).Mag();
    nTrk++;
  }

  TVector3 thrust = TVector3(0, 0, 0);
  if (nTrk <= 0) return thrust;

  if (nTrk == 1) { //thrust is just the particle
    for (int t = 0; t < n; t++) {
      if ((pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && doCharged) {
        TVector3 thrust = TVector3(px[t], py[t], pz[t]);
        thrust.SetMag(thrust.Mag() / pSum);
        return thrust;
      }
      if (pwflag[t] > 2 && !doCharged) {
        TVector3 thrust = TVector3(px[t], py[t], pz[t]);
        thrust.SetMag(thrust.Mag() / pSum);
        return thrust;
      }
    }
  }

  if (nTrk == 2) { //special case for 2 particles
    int n1 = -1, n2 = -1;
    for (int t = 0; t < n; t++) {
      if (doCharged) {
        if ((pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && n1 == -1) { n1 = t; continue;}
        if ((pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && n1 != -1 && n2 == -1) { n2 = t;}
      }
      if (!doCharged) {
        if (pwflag[t] > 2 && n1 == -1) { n1 = t; continue;}
        if (pwflag[t] > 2 && n1 != -1 && n2 == -1) { n2 = t;}
      }
    }

    if (TMath::Power(px[n1], 2) + TMath::Power(py[n1], 2) + TMath::Power(pz[n1], 2) >= TMath::Power(px[n2], 2) + TMath::Power(py[n2], 2) + TMath::Power(pz[n2], 2)) {
      TVector3 thrust = TVector3(px[n1], py[n1], pz[n1]);
      thrust.SetMag(thrust.Mag() / pSum);
      return thrust;
    }
    else {
      TVector3 thrust = TVector3(px[n2], py[n2], pz[n2]);
      thrust.SetMag(thrust.Mag() / pSum);
      return thrust;
    }
  }

  if (nTrk == 3) { //combine lowest 2 magnitude momentum, then use same algo as n=2
    int n1 = -1, n2 = -1, n3 = -1;
    for (int t = 0; t < n; t++) {
      if (doCharged) {
        if ((pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && n1 == -1) { n1 = t; continue;}
        if ((pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && n1 != -1 && n2 == -1) { n2 = t;  continue;}
        if ((pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && n1 != -1 && n2 != -1) n3 = t;
      }
      if (!doCharged) {
        if (pwflag[t] > 2 && n1 == -1) { n1 = t; continue;}
        if (pwflag[t] > 2 && n1 != -1 && n2 == -1) { n2 = t;  continue;}
        if (pwflag[t] > 2 && n1 != -1 && n2 != -1) n3 = t;
      }
    }
    if (TMath::Power(px[n1], 2) + TMath::Power(py[n1], 2) + TMath::Power(pz[n1], 2) >= TMath::Power(px[n2], 2) + TMath::Power(py[n2], 2) + TMath::Power(pz[n2], 2)) {
      if (TMath::Power(px[n1], 2) + TMath::Power(py[n1], 2) + TMath::Power(pz[n1], 2) >= TMath::Power(px[n3], 2) + TMath::Power(py[n3], 2) + TMath::Power(pz[n3], 2)) {
        TVector3 thrust = TVector3(px[n1], py[n1], pz[n1]); //n1 is largest p
        thrust.SetMag(thrust.Mag() / pSum);
        return thrust;
      }
      else {
        TVector3 thrust = TVector3(px[n3], py[n3], pz[n3]); //n3 is largest p
        thrust.SetMag(thrust.Mag() / pSum);
        return thrust;
      }
    }
    else {
      if (TMath::Power(px[n2], 2) + TMath::Power(py[n2], 2) + TMath::Power(pz[n2], 2) >= TMath::Power(px[n3], 2) + TMath::Power(py[n3], 2) + TMath::Power(pz[n3], 2)) {
        TVector3 thrust = TVector3(px[n2], py[n2], pz[n2]); //n3 is largest p
        thrust.SetMag(thrust.Mag() / pSum);
        return thrust;
      }
      else {
        TVector3 thrust = TVector3(px[n3], py[n3], pz[n3]); //n3 is largest p
        thrust.SetMag(thrust.Mag() / pSum);
        return thrust;
      }
    }
  }

  if (nTrk > 3) {
    //make vector of TVector3's of each particle
    std::vector< TVector3 > pVec;
    for (int i = 0; i < n; i++) {
      if (!(pwflag[i] == 0 || pwflag[i] == 1 || pwflag[i] == 2) && doCharged) continue;
      if (pwflag[i] <= 2 && !doCharged) continue;
      TVector3 v = TVector3(px[i], py[i], pz[i]);
      pVec.push_back(v);
    }
    //std::cout << pVecs.at(0).x();

    TVector3 cross;
    float t = 0;
    for (unsigned int i = 1; i < pVec.size(); i++) { //loop through all possible cross products of 2 unique vectors
      for (unsigned int j = 0; j < i; j++) {
        cross = pVec.at(i).Cross(pVec.at(j));
        TVector3 ptot = TVector3(0, 0, 0);

        for (unsigned int k = 0; k < pVec.size(); k++) { //loop through all 3rd particles not used for the cross product
          if (k != i && k != j) {
            if (pVec.at(k)*cross > 0) { //if dot product is >0
              ptot += pVec.at(k);
            }
            else {
              ptot -= pVec.at(k);
            }
          }
        }

        std::vector< TVector3 > cpm;//add or subtract in last 2 vectors used for cross product
        cpm.push_back(ptot - pVec.at(j) - pVec.at(i));
        cpm.push_back(ptot - pVec.at(j) + pVec.at(i));
        cpm.push_back(ptot + pVec.at(j) - pVec.at(i));
        cpm.push_back(ptot + pVec.at(j) + pVec.at(i));
        for (std::vector<TVector3>::iterator it = cpm.begin(); it != cpm.end(); it++) {
          float tval = (*it).Mag2();
          if (tval > t) {
            t = tval;
            thrust = *it;
          }
        }
      }
    }
  }
  thrust.SetMag(thrust.Mag() / pSum);
  return thrust;
}


struct THRUST
{
  enum algorithm {HERWIG, BELLE, OPTIMAL};
};

// Interface to the different algorithm to compute thrust axis
TVector3 getThrust(int n, float *px, float *py, float *pz, THRUST::algorithm algo = THRUST::HERWIG, bool doWeight = false, bool doInvertWeight = false, float* weight = NULL, bool doMET = false, Short_t *pwflag = NULL) {
  TVector3 thrustAxis(0, 0, 0);
  switch (algo) {
  case THRUST::HERWIG: thrustAxis = getThrustHerwig(n, px, py, pz, doWeight, doInvertWeight, weight, doMET, pwflag); break;
  case THRUST::BELLE: thrustAxis = getThrustBelle(n, px, py, pz, doWeight, doInvertWeight, weight); break;
  case THRUST::OPTIMAL: {
    if (n < 4) {
      thrustAxis = getThrustBelle(n, px, py, pz, doWeight, doInvertWeight, weight);
    } else {
      thrustAxis = getThrustHerwig(n, px, py, pz, doWeight, doInvertWeight, weight, doMET, pwflag);
    }
    break;
  }
  default:
    break;
  }
  return thrustAxis;
}

TVector3 getSpecialThrust(int n, float *px, float *py, float *pz, Short_t *pwflag, bool doCharged = true, THRUST::algorithm algo = THRUST::HERWIG) {
  float nTrk = 0;
  for (int t = 0; t < n; t++) {
    if (!(pwflag[t] == 0 || pwflag[t] == 1 || pwflag[t] == 2) && doCharged) continue;
    if (pwflag[t] <= 2 && !doCharged) continue;
    nTrk++;
  }

  TVector3 thrustAxis(0, 0, 0);
  switch (algo) {
  case THRUST::HERWIG: thrustAxis = getSpecialThrustHerwig(n, px, py, pz, pwflag, doCharged); break;
  case THRUST::BELLE: thrustAxis = getSpecialThrustBelle(n, px, py, pz, pwflag, doCharged); break;
  case THRUST::OPTIMAL: {
    if (nTrk < 4) {
      thrustAxis = getSpecialThrustBelle(n, px, py, pz, pwflag, doCharged);
    } else {
      thrustAxis = getSpecialThrustHerwig(n, px, py, pz, pwflag, doCharged);
    }
    break;
  }
  default:
    break;
  }
  return thrustAxis;
}

//Thrust major as defined in http://cds.cern.ch/record/690637/files/ep-2003-084.pdf, p.14
//Simple Algo:
// Take thrust and subtract off thrust component of all particles
// Then just call standard getThrust to find maximum in plane
// Note that this implementation will handle standard and charged thrust (add boolean, if charged not used set pwflag to null
TVector3 getThrustMajor(TVector3 thrust, int n, float *px, float *py, float *pz, Short_t *pwflag, THRUST::algorithm algo = THRUST::HERWIG, bool doCharged = false)
{
  //check first that we are safely calling doCharged
  if (doCharged && pwflag == NULL) {
    std::cout << "THRUSTTOOLS.H: GETTHRUSTMAJOR ERROR: Calling with \'doCharged\' option but with pwflag set to NULL. return 0 vector" << std::endl;
    return TVector3(0, 0, 0);
  }

  //check that we have already calculated thrust, if not get thrust
  if (thrust.Px() < 0.001 && thrust.Py() < 0.001 && thrust.Pz() < 0.001) {
    if (doCharged) thrust = getSpecialThrust(n, px, py, pz, pwflag, true, algo);
    else thrust = getThrust(n, px, py, pz, algo);
  }

  //renormalize thrust to unity for correct projections
  thrust.SetMag(1.);

  const int nInternal = n;
  float pxInternal[nInternal];
  float pyInternal[nInternal];
  float pzInternal[nInternal];
  double pSum = 0.;

  //Now set all particles to their corresponding thrust-perp projections
  for (int i = 0; i < n; ++i) {
    TVector3 temp(px[i], py[i], pz[i]);
    if (doCharged) {
      if (pwflag[i] == 0 || pwflag[i] == 1 || pwflag[i] == 2) pSum += temp.Mag();
    }
    else pSum += temp.Mag();

    TVector3 thrustComponent = thrust;
    thrustComponent.SetMag(thrustComponent.Dot(temp));

    temp -= thrustComponent;
    pxInternal[i] = temp.Px();
    pyInternal[i] = temp.Py();
    pzInternal[i] = temp.Pz();
  }

  TVector3 thrustMajorAxis(0, 0, 0);

  if (!doCharged) {
    switch (algo) {
    case THRUST::HERWIG: thrustMajorAxis = getThrustHerwig(n, pxInternal, pyInternal, pzInternal); break;
    case THRUST::BELLE: thrustMajorAxis = getThrustBelle(n, pxInternal, pyInternal, pzInternal); break;
    case THRUST::OPTIMAL: {
      if (n < 4) thrustMajorAxis = getThrustBelle(n, pxInternal, pyInternal, pzInternal);
      else thrustMajorAxis = getThrustHerwig(n, pxInternal, pyInternal, pzInternal);
      break;
    }
    default:
      break;
    }
  }
  else {
    switch (algo) {
    case THRUST::HERWIG: thrustMajorAxis = getSpecialThrustHerwig(n, pxInternal, pyInternal, pzInternal, pwflag, true); break;
    case THRUST::BELLE: thrustMajorAxis = getSpecialThrustBelle(n, pxInternal, pyInternal, pzInternal, pwflag, true); break;
    case THRUST::OPTIMAL: {
      if (n < 4) thrustMajorAxis = getSpecialThrustBelle(n, pxInternal, pyInternal, pzInternal, pwflag, true);
      else thrustMajorAxis = getSpecialThrustHerwig(n, pxInternal, pyInternal, pzInternal, pwflag, true);
      break;
    }
    default:
      break;
    }
  }

  //we have found the direction of the vector but the magnitude is wrong; reloop to fix the magnitude
  thrustMajorAxis.SetMag(1.);
  double thrustMajorProj = 0.;

  for (int i = 0; i < n; ++i) {
    if (doCharged) {
      if (!(pwflag[i] == 0 || pwflag[i] == 1 || pwflag[i] == 2)) continue;
    }

    TVector3 temp(px[i], py[i], pz[i]);
    thrustMajorProj += TMath::Abs(temp.Dot(thrustMajorAxis));
  }

  thrustMajorAxis.SetMag(thrustMajorProj / pSum);
  return thrustMajorAxis;
}


TVector3 getThrustMinor(TVector3 thrust, TVector3 thrustMajor, int n, float *px, float *py, float *pz, Short_t *pwflag, THRUST::algorithm algo = THRUST::HERWIG, bool doCharged = false)
{
  //check first that we are safely calling doCharged
  if (doCharged && pwflag == NULL) {
    std::cout << "THRUSTTOOLS.H: GETTHRUSTMINOR ERROR: Calling with \'doCharged\' option but with pwflag set to NULL. return 0 vector" << std::endl;
    return TVector3(0, 0, 0);
  }

  //check that we have already calculated thrust, if not get thrust
  if (thrust.Px() < 0.001 && thrust.Py() < 0.001 && thrust.Pz() < 0.001) {
    if (doCharged) thrust = getSpecialThrust(n, px, py, pz, pwflag, algo);
    else thrust = getThrust(n, px, py, pz, algo);
  }

  //check that we have already calculated thrustMajor, if not get thrustMajor
  if (thrustMajor.Px() < 0.001 && thrustMajor.Py() < 0.001 && thrustMajor.Pz() < 0.001) thrustMajor = getThrustMajor(thrust, n, px, py, pz, pwflag, algo, doCharged);

  //Get thrustMinor and renormalize to 1 for correct projections, then calculate magnitude
  TVector3 thrustMinorAxis = thrust.Cross(thrustMajor);
  thrustMinorAxis.SetMag(1.);
  double thrustMinorProj = 0.;
  double pSum = 0.;

  for (int i = 0; i < n; ++i) {
    if (doCharged) {
      if (!(pwflag[i] == 0 || pwflag[i] == 1 || pwflag[i] == 2)) continue;
    }

    TVector3 temp(px[i], py[i], pz[i]);
    thrustMinorProj += TMath::Abs(temp.Dot(thrustMinorAxis));
    pSum += temp.Mag();
  }

  thrustMinorAxis.SetMag(thrustMinorProj / pSum);
  return thrustMinorAxis;
}

#endif
