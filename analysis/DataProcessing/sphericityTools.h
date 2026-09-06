#ifndef SPHERETOOLS
#define SPHERETOOLS
#include "TLorentzVector.h"
#include "TVector3.h"
#include "TVectorD.h"
#include "TMath.h"
#include "TMatrixD.h"
#include <iostream>

class Sphericity{

  public:
    Sphericity(int n, float *px, float *py, float *pz, Short_t *pwflag, bool onlyCharged = true);
    ~Sphericity();

    inline TVector3 sphericityAxis();
    inline TVector3 getV1();
    inline TVector3 getV2();
    inline TVector3 getV3();
    inline TVector3 linSphericityAxis();
    inline float sphericity(); 
    inline float aplanarity(); 
    inline float planarity(); 
    inline float linSphericity(); 
    inline float linAplanarity(); 
    inline float linPlanarity(); 
    inline float linC(); 
    inline float linD(); 

  private:
    bool chargedOnly;
    float l1, l2, l3;   //eigenvalues
    TVector3 v1, v2, v3;//eigenvectors

    //linearized quantities
    float linl1, linl2, linl3;  //eigenvalues
    TVector3 linv1, linv2, linv3;//eigenvectors

    void calculateSphericity(int n, float *px, float *py, float *pz, Short_t *pwflag, int r);
    inline float p2(float px,float py,float pz);
};

inline float Sphericity::p2(float px,float py,float pz){
  return px*px+py*py+pz*pz;
}

inline TVector3 Sphericity::sphericityAxis(){
  if(v1.Phi()>=0) return v1;
  else return -v1;
}

inline TVector3 Sphericity::getV1(){
  return v1;
}

inline TVector3 Sphericity::getV2(){
  return v2;
}

inline TVector3 Sphericity::getV3(){
  return v3;
}

inline TVector3 Sphericity::linSphericityAxis(){
  return linv1;
}

inline float Sphericity::sphericity(){
  return 1.5*(l2+l3);
}

inline float Sphericity::linSphericity(){
  return 1.5*(linl2+linl3);
}

inline float Sphericity::aplanarity(){
  return 1.5*l3;
}

//Added planarity as defined here: http://cds.cern.ch/record/690637/files/ep-2003-084.pdf, p.15
inline float Sphericity::planarity(){
  return l2 - l3;
}

inline float Sphericity::linAplanarity(){
  return 1.5*linl3;
}

inline float Sphericity::linPlanarity(){
  return linl2 - linl3;
}

inline float Sphericity::linC(){
  return 3*(linl1*linl2+linl2*linl3+linl1*linl3);
}

inline float Sphericity::linD(){
  return 27*linl1*linl2*linl3;
}

//where the magic happens
//refer to http://home.fnal.gov/~mrenna/lutp0613man2/node234.html
//generalized sphericity method, and sets important class member at the end for r==2 and r==1
void Sphericity::calculateSphericity(int n, float *px, float *py, float *pz, Short_t *pwflag, int r){
  float norm = 0;

  TMatrixD m = TMatrixD(3,3);
 
  float rF = r;
  //calculate matrix elements
  for(int i = 0; i<n; i++){
    if(chargedOnly && pwflag[i]!=0) continue;
    m(0,0) += px[i]*px[i]*TMath::Power(p2(px[i],py[i],pz[i]),(rF-2)/2.0);   
    m(1,1) += py[i]*py[i]*TMath::Power(p2(px[i],py[i],pz[i]),(rF-2)/2.0);   
    m(2,2) += pz[i]*pz[i]*TMath::Power(p2(px[i],py[i],pz[i]),(rF-2)/2.0);   
    m(1,0) += px[i]*py[i]*TMath::Power(p2(px[i],py[i],pz[i]),(rF-2)/2.0);   
    m(2,0) += px[i]*pz[i]*TMath::Power(p2(px[i],py[i],pz[i]),(rF-2)/2.0);   
    m(1,2) += py[i]*pz[i]*TMath::Power(p2(px[i],py[i],pz[i]),(rF-2)/2.0);
    norm += TMath::Power(p2(px[i],py[i],pz[i]),rF/2.0);   
  } 

  //normalize
  for(int i = 0; i<3; i++){
    for(int j = 0; j<3; j++){
      m(i,j) = m(i,j)/norm;
    }
  }


  //symmetrize other side of the matrix
  m(0,1) = m(1,0);
  m(0,2) = m(2,0);
  m(2,1) = m(1,2);

  //calculate eigenvalues and vectors  
  TVectorD eigenValues;
  TMatrixD eigenVectors = TMatrixD(3,3);
  eigenVectors = m.EigenVectors(eigenValues);

  //fill r==1 and r==2
  if(r==2){
    l1 = eigenValues(0);
    l2 = eigenValues(1);
    l3 = eigenValues(2);
    v1 = TVector3(eigenVectors(0,0),eigenVectors(1,0), eigenVectors(2,0));
    v2 = TVector3(eigenVectors(0,1),eigenVectors(1,1), eigenVectors(2,1));
    v3 = TVector3(eigenVectors(0,2),eigenVectors(1,2), eigenVectors(2,2));
 
  }
  if(r==1){
    linl1 = eigenValues(0);
    linl2 = eigenValues(1);
    linl3 = eigenValues(2);
    linv1 = TVector3(eigenVectors(0,0),eigenVectors(1,0), eigenVectors(2,0));
    linv2 = TVector3(eigenVectors(0,1),eigenVectors(1,1), eigenVectors(2,1));
    linv3 = TVector3(eigenVectors(0,2),eigenVectors(1,2), eigenVectors(2,2));
  }
}

Sphericity::Sphericity(int n, float *px, float *py, float *pz, Short_t *pwflag, bool onlyCharged){
  l1 = -99;
  l2 = -99;
  l3 = -99;
  v1 = TVector3(0,0,0);
  v2 = TVector3(0,0,0);
  v3 = TVector3(0,0,0);
  linl1 = -99;
  linl2 = -99;
  linl3 = -99;
  linv1 = TVector3(0,0,0);
  linv2 = TVector3(0,0,0);
  linv3 = TVector3(0,0,0);
  chargedOnly = onlyCharged; 

  calculateSphericity(n, px, py, pz, pwflag, 2);
  calculateSphericity(n, px, py, pz, pwflag, 1);
}

Sphericity::~Sphericity(){}

#endif
