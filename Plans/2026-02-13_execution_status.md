# Execution Status (2026-02-13)

## Completed

1. Plan and review artifacts created
- `Plans/2026-02-13_thrust_review_and_note_plan.md`
- `Plans/2026-02-13_code_review_findings.md`

2. Core code fixes implemented
- `Unfolding/unfold_thrust.py`
- `DataProcessing/src/Analyze.cxx`
- `DataProcessing/runAnalyze.py`
- `Studies/UnfoldingSystematics/scripts/run_systematic_unfolding.py`
- `DataProcessing/include/analysisCompute.h`
- `Unfolding/unfold_config_template.json`

3. 1994 data and MC variation derivations regenerated
- Source data input:
  - `/Users/anthonybadea/Documents/Documents/ALEPH/ALEPH/LEP1Data1994_recons_aftercut-MERGED.root`
- Source MC input:
  - `/Users/anthonybadea/Documents/Documents/ALEPH/ALEPH/alephMCRecoAfterCutPaths_1994.root`
- Outputs written in `DataProcessing/temp/` for all variations.

4. Validation runs completed
- Nominal unfolding:
  - `Studies/ValidationExec_2026-02-13/unfolded_nominal_exec.root`
- Closure unfolding:
  - `Studies/ValidationExec_2026-02-13/unfolded_closure_exec_closure.root`
- Iteration scan:
  - `Studies/ValidationExec_2026-02-13/iteration_scan/iteration_scan_summary.json`
  - Recommended iteration: `7`

5. Full strict 1994 systematics unfolding completed
- Output dir:
  - `Studies/ValidationExec_2026-02-13/systematics_full_1994`
- Variations produced:
  - `nominal`, `ntpc7`, `pt04`, `ech10`, `no_neutrals`, `with_met`, `nes_up`, `nes_down`, `ner`
- Summary plots:
  - `unfolded_all_variations_ratio_nominal.pdf`
  - `unfolded_all_variations_fractional_diff.pdf`

6. Observable-aware unfolding configuration support added
- `unfold_thrust.py` now supports:
  - `observable = thrust | c_parameter | heavy_jet_mass`
  - default branch/range/label presets with override via config
- Backward compatibility preserved for existing thrust config.

7. DataProcessing now writes additional event-shape branches
- Added branches in output trees:
  - `CParameter`
  - `HeavyJetMass`
- Verified on a 50k-event nominal test output:
  - `DataProcessing/temp/test_nominal_newshapes.root`

8. End-to-end nominal unfolding smoke tests for new observables
- Using refreshed 1994 nominal/no\_event\_sel files with new branches:
  - `Studies/ValidationExec_2026-02-13/unfolded_c_parameter_nominal.root`
  - `Studies/ValidationExec_2026-02-13/unfolded_heavy_jet_mass_nominal.root`

6. Analysis note scaffold created and compiled
- Source tree:
  - `AnalysisNote/`
- Compile check:
  - `AnalysisNote/main.pdf`

## Remaining (next)

1. Add explicit acceptance thresholds and pass/fail statements for closure/refold/iteration checks in note text.
2. Run full validation + systematics campaigns for `C-parameter`.
3. Run full validation + systematics campaigns for `heavy_jet_mass`.

## Update (2026-02-14)

1. Nominal thrust covariance/correlation export added
- `Unfolding/unfold_thrust.py` now writes:
  - `unfold_covariance`
  - `unfold_correlation`

2. Nominal thrust covariance-enabled run completed at selected iteration
- Output:
  - `Studies/ValidationExec_2026-02-13/unfolded_nominal_iter7_cov.root`

3. Matrix artifacts generated for note/theory interfaces
- Output dir:
  - `Studies/ValidationExec_2026-02-13/matrices_nominal_iter7/`
- Includes:
  - response/covariance/correlation PDFs
  - covariance/correlation CSV files and binning maps

4. Analysis note sections expanded
- Added full text and figures for:
  - detector, samples, reconstruction/selection, method, uncertainties, results, and appendix
- Added table of contents in `AnalysisNote/main.tex`.

5. Sections up to Analysis Method strengthened with full particle-category validation
- Updated note sections:
  - `AnalysisNote/sections/Introduction.tex`
  - `AnalysisNote/sections/ALEPHDetector.tex`
  - `AnalysisNote/sections/Datasets.tex`
  - `AnalysisNote/sections/EventReconstructionAndSelection.tex`
  - `AnalysisNote/sections/AnalysisMethod.tex`
- Added appendix:
  - `AnalysisNote/appendix/App_ParticleKinematics.tex`
- Added complete `pwflag` kinematics figure bundle:
  - `Studies/ValidationExec_2026-02-13/pwflag_kinematics/`

6. DataProcessing outputs extended for full `pwflag` kinematics
- Added selected-particle branches in output trees:
  - `mass`, `energy`, `d0`, `z0`, `ntpc`
- Implemented in:
  - `DataProcessing/include/analysisTypes.h`
  - `DataProcessing/include/analysisCompute.h`
  - `DataProcessing/src/Analyze.cxx`
- Regenerated 1994 nominal reco files for data and MC to populate new branches.
