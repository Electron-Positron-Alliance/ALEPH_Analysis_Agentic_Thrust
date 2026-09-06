#include <vector>
#include <algorithm>
#include <cmath>
#include <iostream>
#include "TVector3.h"

using namespace std;
using Vector3 = TVector3;

////////// BELOW HERE COPY-PASTED FROM RIVET
// https://rivet.hepforge.org/code/1.6.0/a00503_source.html#l00010
// note rivet uses its own vector class https://rivet.hepforge.org/code/1.6.0/a00527_source.html
//// the following updates were made to handle use TVector3 instead: .unit() -> .Unit(), .dot() -> .Dot(), .mod2() -> .Mag2(), .mod() -> .Mag()

inline bool mod2Cmp(const Vector3& a, const Vector3& b) {
  return a.Mag2() > b.Mag2();  // EDITED .mod2() -> .Mag2()
 }

// Do the general case thrust calculation
void _calcT(const vector<Vector3>& momenta, double& t, Vector3& taxis) {
  /* This function implements the iterative algorithm as described in the
   * Pythia manual. We take eight (four) different starting vectors
   * constructed from the four (three) leading particles to make sure that
   * we don't find a local maximum.
   */
  vector<Vector3> p = momenta;
  assert(p.size() >= 3);
  unsigned int n = 3;
  if (p.size() == 3) n = 3;
  vector<Vector3> tvec;
  vector<double> tval;
  std::sort(p.begin(), p.end(), mod2Cmp);
  for (unsigned int i=0 ; i<pow(2,n-1) ; i++) {
    // Create an initial vector from the leading four jets
    Vector3 foo(0,0,0);
    int sign=i;
    for (unsigned int k=0 ; k<n ; k++) {
      (sign%2)==1 ? foo+=p[k] : foo-=p[k];
      sign/=2;
    }
    foo=foo.Unit(); // EDITED .unit() -> .Unit()
    // Iterate
    double diff=999.;
    while (diff>1e-5) {
      Vector3 foobar(0,0,0);
      for (unsigned int k=0 ; k<p.size() ; k++)
        foo.Dot(p[k])>0 ? foobar+=p[k] : foobar-=p[k]; // EDITED .dot() -> .Dot()
      diff=(foo-foobar.Unit()).Mag(); // EDITED .unit() -> .Unit(), .mod() -> .Mag()
      foo=foobar.Unit(); // EDITED .unit() -> .Unit()
    }
    // Calculate the thrust value for the vector we found
    t=0.;
    for (unsigned int k=0 ; k<p.size() ; k++)
      t+=fabs(foo.Dot(p[k])); // EDITED .dot() -> .Dot()
    // Store everything
    tval.push_back(t);
    tvec.push_back(foo);
  }
  // Pick the solution with the largest thrust
  t=0.;
  for (unsigned int i=0 ; i<tvec.size() ; i++)
    if (tval[i]>t){
      t=tval[i];
      taxis=tvec[i];
    }
}
