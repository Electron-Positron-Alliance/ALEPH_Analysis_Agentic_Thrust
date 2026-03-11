#include "core/analysisDriver.h"
#include "thrustCompute.h"

int main(int argc, char* argv[]) {
  return RunAnalysis<ThrustResult>(argc, argv, "thrust", ComputeThrustResult,
      [](ROOT::RDF::RNode df) {
        df = DefineOrRedefineColumn(df, "Thrust",        [](const ThrustResult& r) { return r.Thrust; });
        df = DefineOrRedefineColumn(df, "RivetThrust",   [](const ThrustResult& r) { return r.RivetThrust; });
        df = DefineOrRedefineColumn(df, "ChargedThrust", [](const ThrustResult& r) { return r.ChargedThrust; });
        df = DefineOrRedefineColumn(df, "CParameter",    [](const ThrustResult& r) { return r.CParameter; });
        df = DefineOrRedefineColumn(df, "HeavyJetMass",  [](const ThrustResult& r) { return r.HeavyJetMass; });
        df = DefineOrRedefineColumn(df, "TTheta",        [](const ThrustResult& r) { return r.TTheta; });
        return std::make_pair(df, std::vector<std::string>{
            "Thrust", "RivetThrust", "ChargedThrust", "CParameter", "HeavyJetMass", "TTheta"});
      });
}
