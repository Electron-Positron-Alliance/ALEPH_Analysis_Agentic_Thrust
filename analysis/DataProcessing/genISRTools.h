#ifndef GENISRTOOLS_H
#define GENISRTOOLS_H

// genISRTools.h
//
// Identification of initial-state-radiation (ISR) photons (and their full
// descendant cascades) in the generator-level event record of PYTHIA 8,
// Herwig 7, and Sherpa samples.
//
// Strategy
// --------
// Walk the mother chain of every photon. A photon is "ISR" if its lineage
// reaches a beam lepton (e+/e-) without ever crossing the hard subprocess
// (Z / gamma* or one of its outgoing quarks). For PYTHIA 8 we additionally
// accept the dedicated ISR status range [41, 49] as a fast positive
// identification, falling back to the ancestor walk otherwise.
//
// All functions take flat C arrays directly as written by main304.cc and
// hepmcToRoot.cc, so no STL allocation per particle.
//
// buildISRClassification() also flags every descendant of an ISR photon, so
// the caller can subsequently exclude the entire ISR cascade from event-shape
// observables (e.g. recompute thrust without the ISR photon and any
// gamma -> e+e- conversion daughters).

#include <vector>
#include <string>
#include <cstdlib>
#include <cmath>
#include <cstdint>

namespace genISRTools {

  // ALEPHMC is the archived ALEPH Pythia 6.1 MC. It is listed here so its ISR
  // handling lives in this file, but it is NOT an "external generator": the
  // ntuple has no particle genealogy, so its ISR photons are tagged
  // kinematically (computeEventISR_ALEPHMC) rather than by the genealogy walk.
  enum class Generator { PYTHIA8, KKMCee, Vincia, Herwig, Sherpa, ALEPHMC, Unknown };

  inline Generator parseGenerator(const std::string& s) {
    if (s == "PYTHIA8") return Generator::PYTHIA8;
    if (s == "KKMCee")  return Generator::KKMCee;
    if (s == "Vincia")  return Generator::Vincia;
    if (s == "Herwig")  return Generator::Herwig;
    if (s == "Sherpa")  return Generator::Sherpa;
    if (s == "ALEPHMC") return Generator::ALEPHMC;
    return Generator::Unknown;
  }

  // True for a generator whose full particle genealogy is stored, so ISR can be
  // classified by walking mother/daughter links (and pwflag derived from pdgid,
  // final-state selected by status). This is the set of modern MCs we generate
  // and pass through the detector simulation; it excludes the archived ALEPHMC
  // (which has no genealogy and uses the kinematic ISR tag) and Unknown.
  inline bool hasGenealogy(Generator gen) {
    return gen != Generator::Unknown && gen != Generator::ALEPHMC;
  }

  // -------------------------------------------------------------------------
  // Ancestor walk: returns true if particle i descends from a beam lepton
  // (|pdgid|==11 with no further mother) without traversing the hard scatter.
  // The hard scatter is identified by encountering an ancestor with pdgid==23
  // (Z), or |pdgid| in [1,6] (a coloured parton from the hard process or its
  // shower). maxDepth bounds the chain to guard against pathological loops.
  // -------------------------------------------------------------------------
  inline bool ancestorIsBeamLepton(int i,
                                   const int* pdgid,
                                   const int* mother1,
                                   const int* mother2,
                                   int nParticle,
                                   int maxDepth = 64) {
    int cur = i;
    for (int depth = 0; depth < maxDepth; ++depth) {
      if (cur < 0 || cur >= nParticle) return false;
      int m1 = mother1[cur];
      int m2 = mother2[cur];
      bool m1Valid = (m1 > 0 && m1 < nParticle && m1 != cur);
      bool m2Valid = (m2 > 0 && m2 < nParticle && m2 != cur);
      // Top of the record: accept iff this particle itself is e+/e-.
      if (!m1Valid && !m2Valid) {
        return std::abs(pdgid[cur]) == 11;
      }
      int parent = m1Valid ? m1 : m2;
      int parentPid = std::abs(pdgid[parent]);
      if (parentPid == 23) return false;            // Z boson
      if (parentPid >= 1 && parentPid <= 6) return false; // coloured parton
      cur = parent;
    }
    return false;
  }

  // -------------------------------------------------------------------------
  // PYTHIA 8 — accept photons with positive status 43 or 44.
  //   43 = "outgoing produced by a branching" — the fresh ISR emission.
  //   44 = "outgoing shifted by a branching"  — the entry for an earlier ISR
  //        photon whose kinematics were subsequently updated by a later
  //        branching. In that case the original 43 entry is rewritten with
  //        negative status (-43, "replaced") and the new positive-status
  //        record is a 44. So for every physical ISR photon emitted in the
  //        pT-ordered backward shower, exactly one positive-status entry
  //        remains in the record: 43 if it was never shifted, 44 if it was.
  //
  // Counting only status 43 undercounts multi-emission events (drops every
  // earlier photon that got shifted by a later branching). Counting the
  // negative codes on top would double-count replaced-history duplicates.
  // {43, 44} with a positive-status requirement is the correct set.
  //
  // No ancestor-walk fallback is used for PYTHIA 8: photons outside this set
  // that still trace to a beam lepton are record-bookkeeping copies (e.g.
  // 63 beam remnants, -43/-44 history) and should not be counted. Herwig
  // and Sherpa (HepMC2) keep the ancestor walk since their status codes do
  // not encode the ISR subsystem.
  // -------------------------------------------------------------------------
  inline bool isISRPhoton_PYTHIA8(int i,
                                  const int* pdgid,
                                  const int* status,
                                  const int* /*mother1*/,
                                  const int* /*mother2*/,
                                  int /*nParticle*/) {
    if (pdgid[i] != 22) return false;
    return status[i] == 43 || status[i] == 44;
  }

  // -------------------------------------------------------------------------
  // Herwig 7 — HepMC2 status does not encode ISR vs FSR; rely entirely on
  // the ancestor walk.
  // -------------------------------------------------------------------------
  inline bool isISRPhoton_Herwig(int i,
                                 const int* pdgid,
                                 const int* /*status*/,
                                 const int* mother1,
                                 const int* mother2,
                                 int nParticle) {
    if (pdgid[i] != 22) return false;
    return ancestorIsBeamLepton(i, pdgid, mother1, mother2, nParticle);
  }

  // -------------------------------------------------------------------------
  // Sherpa — same convention as Herwig (HepMC2 + YFS QED).
  // -------------------------------------------------------------------------
  inline bool isISRPhoton_Sherpa(int i,
                                 const int* pdgid,
                                 const int* /*status*/,
                                 const int* mother1,
                                 const int* mother2,
                                 int nParticle) {
    if (pdgid[i] != 22) return false;
    return ancestorIsBeamLepton(i, pdgid, mother1, mother2, nParticle);
  }

  // -------------------------------------------------------------------------
  // PYTHIA 8 Vincia — antenna shower uses different status codes than the
  // default simple shower. ISR photons appear at status 63 with non-zero
  // energy (unlike the default shower where status 63 are zero-energy
  // bookkeeping entries). The status-code shortcut (43/44) does not apply.
  // Use the ancestor walk instead, same strategy as Herwig/Sherpa.
  // The PYTHIA 8 event record structure (mother/daughter indices) is the
  // same regardless of shower model, so the walk is valid.
  // -------------------------------------------------------------------------
  inline bool isISRPhoton_Vincia(int i,
                                 const int* pdgid,
                                 const int* /*status*/,
                                 const int* mother1,
                                 const int* mother2,
                                 int nParticle) {
    if (pdgid[i] != 22) return false;
    return ancestorIsBeamLepton(i, pdgid, mother1, mother2, nParticle);
  }

  // -------------------------------------------------------------------------
  // Dispatch wrapper: pick the per-generator routine based on a Generator tag.
  // Use parseGenerator() if you only have the inFileType string.
  // -------------------------------------------------------------------------
  inline bool isISRPhoton(Generator gen, int i,
                          const int* pdgid,
                          const int* status,
                          const int* mother1,
                          const int* mother2,
                          int nParticle) {
    switch (gen) {
      case Generator::PYTHIA8:
      case Generator::KKMCee:
        // KKMCee qqbar is hadronized with PYTHIA 8, so the gen-record is
        // PYTHIA8-style. The KKMCee->Py8 driver (hadronizeKKMC) EXPLICITLY tags
        // the carried YFS ISR photons with status 43 (not relying on Py8 to
        // relabel them); validated on the production samples (status-43 photons
        // in ~59% of isr1 events, ~0 in isr0). So handle identically to PYTHIA8
        // (status 43/44). NB: the status-43 tagging is set by the KKMCee->Py8
        // hadronization driver (in the KKMCee production area, outside this
        // repo); keep that convention in sync with this branch.
        return isISRPhoton_PYTHIA8(i, pdgid, status, mother1, mother2, nParticle);
      case Generator::Vincia:
        return isISRPhoton_Vincia (i, pdgid, status, mother1, mother2, nParticle);
      case Generator::Herwig:
        return isISRPhoton_Herwig (i, pdgid, status, mother1, mother2, nParticle);
      case Generator::Sherpa:
        return isISRPhoton_Sherpa (i, pdgid, status, mother1, mother2, nParticle);
      default:
        return false;
    }
  }

  // -------------------------------------------------------------------------
  // Per-particle classification:
  //   0 = unrelated to ISR
  //   1 = ISR photon (identified directly by isISRPhoton)
  //   2 = descendant of an ISR photon (any generation)
  //
  // Descendants are tagged by walking each particle's mother chain and
  // checking whether any ancestor is already classified as ISR. This is
  // correct for both PYTHIA 8 (where daughter1/daughter2 is a contiguous
  // [first,last] range) and HepMC2 (Herwig/Sherpa) where daughter1/daughter2
  // are only the first two specific child indices and the [d1,d2] range
  // would be meaningless. daughter1/daughter2 are accepted in the signature
  // for symmetry with the rest of the event-record API but are not consulted.
  // O(N * depth) per event, with depth ~ tens for LEP1 — negligible.
  // -------------------------------------------------------------------------
  inline std::vector<int> buildISRClassification(Generator gen,
                                                 const int* pdgid,
                                                 const int* status,
                                                 const int* mother1,
                                                 const int* mother2,
                                                 const int* /*daughter1*/,
                                                 const int* /*daughter2*/,
                                                 int nParticle) {
    std::vector<int> cls(nParticle, 0);

    // First pass: tag ISR photons.
    for (int i = 0; i < nParticle; ++i) {
      if (isISRPhoton(gen, i, pdgid, status, mother1, mother2, nParticle))
        cls[i] = 1;
    }

    // Second pass: tag descendants by walking the mother chain.
    for (int i = 0; i < nParticle; ++i) {
      if (cls[i] != 0) continue;
      int cur = i;
      for (int depth = 0; depth < 64; ++depth) {
        int m1 = mother1[cur];
        int m2 = mother2[cur];
        int parent = (m1 > 0 && m1 < nParticle && m1 != cur)
                        ? m1
                        : ((m2 > 0 && m2 < nParticle && m2 != cur) ? m2 : -1);
        if (parent < 0) break;
        if (cls[parent] == 1 || cls[parent] == 2) { cls[i] = 2; break; }
        cur = parent;
      }
    }
    return cls;
  }

  // -------------------------------------------------------------------------
  // Convenience boolean mask: true wherever the classification is non-zero
  // (ISR photon OR a descendant). This is the array you would &-out of any
  // event-shape calculation that wants to exclude the ISR cascade.
  // -------------------------------------------------------------------------
  inline std::vector<bool> buildISRMask(Generator gen,
                                        const int* pdgid,
                                        const int* status,
                                        const int* mother1,
                                        const int* mother2,
                                        const int* daughter1,
                                        const int* daughter2,
                                        int nParticle) {
    auto cls = buildISRClassification(gen, pdgid, status, mother1, mother2,
                                      daughter1, daughter2, nParticle);
    std::vector<bool> mask(nParticle, false);
    for (int i = 0; i < nParticle; ++i) mask[i] = (cls[i] != 0);
    return mask;
  }

  // -------------------------------------------------------------------------
  // Generator-specific final-state predicate, matching the convention used in
  // the gen-level ntuple writers. PYTHIA 8 uses status>0 for final-state;
  // Herwig/Sherpa (HepMC2) use status==1.
  // -------------------------------------------------------------------------
  inline bool isFinalState(Generator gen, int status) {
    if (gen == Generator::PYTHIA8 || gen == Generator::KKMCee || gen == Generator::Vincia) return status > 0;
    return status == 1;
  }

  // -------------------------------------------------------------------------
  // High-level per-event ISR summary:
  //   nIsr         — count of ISR photons (cls==1)
  //   nIsrHard     — ISR photons with E > hardEnergyCut
  //   nDesc        — final-state ISR-cascade descendants (cls==2 AND final)
  //   isrE / isrCosTh — per-photon arrays (size == nIsr)
  //   descPdgId    — PDG ids of the final-state descendants (size == nDesc)
  //   cascadeMask  — length nParticle, 1 if cls==1 or cls==2 (ISR or descendant)
  //
  // Single entry point so Analyze.cxx stays thin: classify once, derive all
  // per-event quantities + the cascade mask, caller uses the mask to build a
  // cascade-removed thrust input.
  // -------------------------------------------------------------------------
  struct EventISR {
    int nIsr = 0;
    int nIsrHard = 0;
    int nDesc = 0;
    std::vector<float>   isrE;
    std::vector<float>   isrCosTh;
    std::vector<int>     descPdgId;
    std::vector<uint8_t> cascadeMask;
  };

  inline EventISR computeEventISR(Generator gen,
                                  int nParticle,
                                  const int*   pdgid,
                                  const int*   status,
                                  const int*   mother1,
                                  const int*   mother2,
                                  const int*   daughter1,
                                  const int*   daughter2,
                                  const float* px,
                                  const float* py,
                                  const float* pz,
                                  const float* energy,
                                  float hardEnergyCut = 1.0f) {
    EventISR out;
    out.cascadeMask.assign(nParticle, 0);
    if (gen == Generator::Unknown || nParticle <= 0) return out;

    auto cls = buildISRClassification(gen, pdgid, status, mother1, mother2,
                                      daughter1, daughter2, nParticle);

    for (int i = 0; i < nParticle; ++i) {
      int c = cls[i];
      if (c == 0) continue;
      out.cascadeMask[i] = 1;
      if (c == 1) {
        // ISR photon (all, regardless of final-state status).
        out.nIsr += 1;
        float E = energy[i];
        out.isrE.push_back(E);
        float pmag = std::sqrt(px[i]*px[i] + py[i]*py[i] + pz[i]*pz[i]);
        out.isrCosTh.push_back(pmag > 1e-9f ? pz[i] / pmag : 0.0f);
        if (E > hardEnergyCut) out.nIsrHard += 1;
      } else if (c == 2 && isFinalState(gen, status[i])) {
        // ISR descendant, final state only.
        out.nDesc += 1;
        out.descPdgId.push_back(pdgid[i]);
      }
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // Archived ALEPH Pythia 6.1 MC ISR tag.
  //
  // The full genealogy needed by computeEventISR() is absent from the archived
  // ntuple, so ISR photons are tagged kinematically: they are stored as
  // beam-collinear placeholders -- neutral photons (pwflag==4, charge==0)
  // pinned at phi ~ 0 and pt ~ 0.001 GeV. This reproduces the implicit ISR
  // removal used by the previous (OmniFold) result.
  //
  // NOTE: there is deliberately no explicit cos(theta) cut. The tiny-pt pin
  // already forces beam-collinearity: verified on the full 1994 archived MC
  // (209,529 tagged photons), 99.8% have |cos(theta)| > 0.98, so an explicit
  // forward-direction cut would be redundant (removes ~0.2%).
  //
  // Fills the same EventISR struct as computeEventISR() (cascadeMask + nIsr,
  // nIsrHard, isrE, isrCosTh); nDesc/descPdgId stay empty (no cascade walk).
  // -------------------------------------------------------------------------
  inline EventISR computeEventISR_ALEPHMC(int nParticle,
                                          const short* pwflag,
                                          const short* charge,
                                          const float* phi,
                                          const float* pt,
                                          const float* pmag,
                                          const float* mass,
                                          const float* theta,
                                          float hardEnergyCut = 1.0f) {
    EventISR out;
    out.cascadeMask.assign(nParticle, 0);
    for (int i = 0; i < nParticle; ++i) {
      if (pwflag[i] == 4 && charge[i] == 0 && std::abs(phi[i]) <= 0.001f
          && pt[i] > 0.00099f && pt[i] < 0.001009f) {
        out.cascadeMask[i] = 1;
        out.nIsr += 1;
        float E = std::sqrt(pmag[i]*pmag[i] + mass[i]*mass[i]);
        if (E > hardEnergyCut) out.nIsrHard += 1;
        out.isrE.push_back(E);
        out.isrCosTh.push_back(std::cos(theta[i]));
      }
    }
    return out;
  }

} // namespace genISRTools

#endif // GENISRTOOLS_H
