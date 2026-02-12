#ifndef ANALYSIS_CONFIG_H
#define ANALYSIS_CONFIG_H

#include "analysisTypes.h"

#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <string>

struct ConfigParams {
  std::map<std::string, float> selections;
  std::map<std::string, std::string> strings;
};

struct Options {
  std::string inFileName;
  std::string outFileName;
  std::string configStr;
  std::string configPath;
  int doNEvents = -1;
  int nThreads = 0;
  bool debug = false;
};

inline ConfigParams parseConfigString(const std::string& configStr) {
  ConfigParams result;

  std::stringstream ss(configStr);
  std::string item;

  while (std::getline(ss, item, ';')) {
    size_t pos = item.find('=');
    if (pos == std::string::npos) continue;

    std::string key = item.substr(0, pos);
    std::string valueStr = item.substr(pos + 1);

    if (key == "inFileType" || key == "treeNames") {
      result.strings[key] = valueStr;
    } else {
      float value;
      if (valueStr == "true") {
        value = true;
      } else if (valueStr == "false") {
        value = false;
      } else {
        value = std::stof(valueStr);
      }
      result.selections[key] = value;
    }
  }

  return result;
}

inline Selections BuildSelections(const std::map<std::string, float>& selMap) {
  Selections s;
  s.nTPCcut = static_cast<int>(selMap.at("nTPCcut"));
  s.chargedTracksAbsCosThCut = selMap.at("chargedTracksAbsCosThCut");
  s.ptCut = selMap.at("ptCut");
  s.d0Cut = selMap.at("d0Cut");
  s.z0Cut = selMap.at("z0Cut");
  s.ECut = selMap.at("ECut");
  s.neutralTracksAbsCosThCut = selMap.at("neutralTracksAbsCosThCut");
  s.TotalTrkEnergyCut = selMap.at("TotalTrkEnergyCut");
  s.AbsCosSThetaCut = selMap.at("AbsCosSThetaCut");
  s.NTrkCut = selMap.at("NTrkCut");
  s.NeuNchCut = selMap.at("NeuNchCut");
  s.EVisCut = selMap.at("EVisCut");
  s.MissPCut = selMap.at("MissPCut");
  s.NES = selMap.at("NES");
  s.NER = selMap.at("NER");
  s.keepChargedTracks = selMap.at("keepChargedTracks") != 0.0f;
  s.keepNeutralTracks = selMap.at("keepNeutralTracks") != 0.0f;
  s.doMET = selMap.at("doMET") != 0.0f;
  return s;
}

inline std::string ReadConfigFile(const std::string& path) {
  std::ifstream in(path);
  if (!in) return "";
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

inline Options ParseOptions(int argc, char* argv[]) {
  Options opts;
  for (int i = 1; i < argc; i++) {
    if (strncmp(argv[i], "-i", 2) == 0) opts.inFileName = argv[i + 1];
    if (strncmp(argv[i], "-o", 2) == 0) opts.outFileName = argv[i + 1];
    if (strncmp(argv[i], "-c", 2) == 0) opts.configStr = argv[i + 1];
    if (strncmp(argv[i], "-C", 2) == 0) opts.configPath = argv[i + 1];
    if (strncmp(argv[i], "--config", 8) == 0) opts.configPath = argv[i + 1];
    if (strncmp(argv[i], "-n", 2) == 0) opts.doNEvents = std::stoi(argv[i + 1]);
    if (strncmp(argv[i], "-j", 2) == 0) opts.nThreads = std::stoi(argv[i + 1]);
    if (strncmp(argv[i], "--threads", 9) == 0) opts.nThreads = std::stoi(argv[i + 1]);
    if (strncmp(argv[i], "--debug", 7) == 0) opts.debug = true;
  }
  return opts;
}

#endif
