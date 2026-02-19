# Plan: Strengthen Analysis Note (Sections 1-5) with Full pwflag-Resolved Reconstruction Evidence

## Summary
Rewrite and expand the note through Analysis Method so it is scientifically complete and aligned with the previous ALEPH note style, while focused on the current thrust + Iterative Bayesian Unfolding workflow.

Key agreed decisions:
- Introduction depth: long
- pwflag figure strategy: hybrid (representative in main text, full set in appendix)
- Comparison style: Data/MC with ratio panels
- pwflag variables: full previous-note-style coverage

## Scope (This Pass)
In scope:
1. Introduction
2. ALEPHDetector
3. Datasets
4. EventReconstructionAndSelection
5. AnalysisMethod
6. New/updated figure production needed by these sections (especially full pwflag kinematics)

Out of scope for this pass:
- Systematics/Results/Conclusion rewrite (except minor cross-reference fixes)
- New unfolding algorithm changes
- Non-thrust observable narrative (C-parameter, heavy jet mass) beyond forward-looking context

## Section-by-Section Spec

### 1) Introduction (AnalysisNote/sections/Introduction.tex)
- Build a longer physics-motivated introduction:
  - Why LEP event-shape reanalysis remains relevant
  - Why thrust is central for QCD precision and hadronization studies
  - Why this note uses Iterative Bayesian Unfolding for fast iterative experimental cross-checks
  - Why covariance/correlation outputs matter for theory usage
- Explicitly state staged strategy:
  - Stage 1: thrust with IBU and cross-check to prior ALEPH-era results
  - Stage 2: thrust family (C-parameter, heavy jet mass), potential multidimensional unfolding study
- End with clear paper roadmap paragraph matching section labels.

### 2) ALEPH Detector (AnalysisNote/sections/ALEPHDetector.tex)
- Reuse prior-note detector narrative structure (short but substantive):
  - Tracking system (VDET/ITC/TPC role in charged particle reconstruction)
  - ECAL/HCAL role in neutral particle measurement
  - Muon system and trigger/luminosity references
- Keep this section concise and reference-rich (not detector-performance deep dive).
- Preserve style consistency with earlier note wording where appropriate.

### 3) Data and MC (AnalysisNote/sections/Datasets.tex)
- Clarify 1994-only choice and MC availability logic.
- Document exact analysis inputs used in current code path:
  - data reco (t)
  - MC reco (t)
  - MC gen (tgen)
  - MC gen-before (tgenBefore)
- Keep bookkeeping table with entries and selected counts.
- Add short paragraph on matching model assumptions for response construction and hadronic selection correction.

### 4) Event Reconstruction and Selection (AnalysisNote/sections/EventReconstructionAndSelection.tex)
Structure this section into four subsections:

1. Particle categories and pwflag meaning
- Explicit table mapping pwflag = 0..5 to physical object classes.
- Explain why each category can influence thrust (all selected particles contribute to event-shape calculation).

2. Object-level selections
- Charged and neutral selection equations/criteria as implemented.
- Briefly describe conversion/cleaning logic where relevant.

3. pwflag-resolved kinematic validation (core of this rewrite)
- Main text: representative figure panels for each pwflag category with Data/MC+ratio.
- Appendix: full variable grids per category.
- Required per-pwflag variable coverage (agreed full set):
  - angular/momentum: cosTheta, phi, pt, pmag
  - tracking-quality/impact: d0, z0, ntpc
  - calorimetric/kinematic: energy, mass (where meaningful)
- Narrative requirement:
  - describe agreement/mismodeling regions category-by-category
  - explicitly connect observed differences to potential thrust sensitivity

4. Event-level selection observables
- Keep event-level distributions (Ntrk, Ntrk+Neu, ECh, cosThetaSph, etc.)
- Explain how these cuts isolate hadronic Z topology relevant for event-shape analysis.

### 5) Analysis Method (AnalysisNote/sections/AnalysisMethod.tex)
Keep this section method-complete for IBU:
- Thrust definition and reconstruction details
- Response construction from matched reco/gen events
- IBU formalism and iteration regularization strategy
- Choice of nominal iteration and validation criteria references
- Hadronic event-selection correction definition
- Covariance/correlation product definition and export formats
- Include response and matrix figures already produced, with stronger interpretation text.

## Plotting/Interface Changes Required

### A) Plot-production interfaces (code-level plan)
Update plotting layer to support full per-pwflag variable outputs with ratio:
- Extend DataProcessing/plotting/plot.py:
  - rvec_expr_for_pwflag support for d0, z0, ntpc, energy, mass in addition to current set
  - variable-specific expression handling for neutral/charged categories where branch semantics differ
- Extend DataProcessing/plotting/PWFLAG_BINNING and axis-title map for new variables.
- Ensure ratio panels are enabled for all Data/MC comparisons (default style).

### B) Figure outputs and organization
- Produce canonical figure set under a dedicated output directory (e.g. Studies/ValidationExec_2026-02-13/pwflag_kinematics/).
- Add deterministic naming convention:
  - pwflag{N}_{var}.pdf
  - grouped panel outputs for note inclusion (e.g. pwflag0_corepanel.pdf, etc.)
- Main-body figure budget:
  - 1-2 multi-panel figures per charged group (0,1,2)
  - 1-2 multi-panel figures for neutral groups (3,4,5)
- Appendix:
  - full matrix of all per-pwflag variables.

## Public APIs / Interfaces / Types (What changes)
1. Plot CLI behavior
- DataProcessing/plotting/plot.py --include-pwflag will produce expanded variable set (not only 4 variables).
2. Figure contract for note
- New required figure paths for section 4 main text + appendix.
3. No change to unfolding ROOT schema for this pass.

## Validation / Test Cases

### A) Plot-generation validation
1. Run plot command on nominal data+MC inputs with --include-pwflag.
2. Verify PDFs exist for all required pwflag x variable combinations.
3. Spot-check 3 representative plots (charged, V0, neutral hadron) for:
- non-empty histograms
- valid ratio pads
- correct axis labels/units

### B) Note-compile validation
1. Compile AnalysisNote/main.tex end-to-end.
2. Verify no missing figure references in sections up to Analysis Method.
3. Verify all new labels/cross-references resolve after final LaTeX pass.

### C) Physics-content validation
1. Confirm all stated cuts match current code defaults (runAnalyze.py / C++ selection implementation).
2. Confirm all stated sample counts match current nominal files.

## Acceptance Criteria
- Sections 1-5 read as publication-grade narrative (not placeholders).
- Reconstruction section explicitly demonstrates particle-category inputs relevant to thrust.
- Full pwflag kinematic coverage exists (main text + appendix split).
- Figures are reproducible from repository scripts/commands.
- Analysis note compiles cleanly with resolved references.

## Assumptions and Defaults
- Keep focus on thrust-only for this revision pass.
- Use 1994 dataset as nominal baseline.
- Keep terminology explicit: Iterative Bayesian Unfolding (no shorthand references to prior collaborations as method labels).
- Hybrid figure strategy and Data/MC+ratio style are fixed defaults unless changed later.
