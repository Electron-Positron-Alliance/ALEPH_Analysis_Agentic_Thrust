# Code Review Findings (2026-02-13)

Scope reviewed:
- `DataProcessing/`
- `Unfolding/`
- `Studies/UnfoldingSystematics/`
- `Studies/UnfoldingIterationScan/`

## P0 (Critical)

1. Fixed: wrong default generator tree in unfolding
- File: `Unfolding/unfold_thrust.py:283`
- Issue: `gen_tree` default was `"t"` while generator trees are `tgen` in nominal configs.
- Risk: immediate runtime failure or accidental loading of wrong tree if config is incomplete.
- Fix: default changed to `"tgen"`.

2. Fixed: success path returned non-zero exit code in C++ analyzer
- File: `DataProcessing/src/Analyze.cxx:222`
- Issue: returned `1` on successful completion.
- Risk: wrappers/automation interpret successful jobs as failure.
- Fix: changed to `return 0;`.

## P1 (High)

1. Fixed: closure mode incorrectly required data file and data tree/branches
- File: `Unfolding/unfold_thrust.py:309-347`
- Issue: closure checks still required/opened data input and data branches even though pseudo-data is taken from reco MC.
- Risk: closure mode could fail for irrelevant missing data inputs.
- Fix: closure mode now requires only reco/gen/genBefore inputs and skips data tree/branch checks.

2. Fixed: optional selection branch could still be hard-required
- File: `Unfolding/unfold_thrust.py:342-347`
- Issue: selection branch checks were unconditional in branch validation.
- Risk: configuration with no selection branch would fail despite logic supporting it.
- Fix: selection branch checks are now conditional on non-empty branch name.

3. Fixed: `runAnalyze.py` ignored per-job failures
- File: `DataProcessing/runAnalyze.py:262-272`
- Issue: return codes from `Analyze.exe` were not propagated.
- Risk: silent partial failures in large production campaigns.
- Fix: failures are collected and script exits non-zero with failing selections listed.

4. Fixed: output directory handling missing in `runAnalyze.py`
- File: `DataProcessing/runAnalyze.py:191`
- Issue: output dir was not created proactively.
- Risk: avoidable runtime failures when output path did not exist.
- Fix: `os.makedirs(ops.outDir, exist_ok=True)` added.

5. Fixed: fragile systematic variation filename substitution
- File: `Studies/UnfoldingSystematics/scripts/run_systematic_unfolding.py:60-70`
- Issue: broad `.replace("nominal", variation)` could mutate unintended path segments.
- Risk: wrong file resolution in non-trivial paths.
- Fix: basename-scoped replacement of `"_nominal_"` with explicit error on unexpected pattern.

6. Fixed: closure output naming duplicate suffix behavior
- File: `Unfolding/unfold_thrust.py:305-312`
- Issue: closure mode always appended `_closure`, even if already present.
- Risk: confusing output naming and repeated suffixes.
- Fix: idempotent closure naming logic.

## P2 (Medium / Remaining)

1. Partially open: end-to-end observable expansion beyond thrust
- Current state: unfolding entrypoint now supports observable presets, but full
  C-parameter/heavy-jet-mass deployment still needs corresponding upstream
  derivation content and validation outputs.
- Remaining impact: additional branch production and dedicated validation runs
  are required before non-thrust observables can be promoted to nominal.
- Progress:
  - upstream branches now present in refreshed 1994 nominal/no-event-sel files.
  - nominal unfolding smoke tests for C-parameter and heavy-jet-mass succeed.

## Validation Evidence (Executed)

1. Nominal unfolding (success)
- Output: `Studies/ValidationExec_2026-02-13/unfolded_nominal_exec.root`

2. Closure unfolding (success)
- Output: `Studies/ValidationExec_2026-02-13/unfolded_closure_exec_closure.root`

3. Closure mode without data dependency + hadronic correction disabled (success)
- Command used `mode=closure`, invalid `data_file`, `apply_hadronic_event_correction=false`
- Output: `Studies/ValidationExec_2026-02-13/unfolded_closure_nocorr_exec_closure.root`

4. Iteration scan diagnostics (success)
- Output dir: `Studies/ValidationExec_2026-02-13/iteration_scan`
- Summary: recommended iteration = `7`
- Key metric: toy-closure mean chi2/ndf = `0.983`

5. Systematics subset
- Outputs: nominal, `nes_up`, `ntpc7` under `Studies/ValidationExec_2026-02-13/systematics_subset`

6. 1994 data derivations regenerated for all variations (resolved input gap)
- Source input: `/Users/anthonybadea/Documents/Documents/ALEPH/ALEPH/LEP1Data1994_recons_aftercut-MERGED.root`
- Output files now present in `DataProcessing/temp/`:
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_ntpc7_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_pt04_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_ech10_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_no_neutrals_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_with_met_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_nes_up_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_nes_down_t.root`
  - `LEP1Data1994_recons_aftercut-MERGED_thrust_ner_t.root`

7. Strict 1994 cut-based systematic check (no fallback) succeeds
- Command: `run_systematic_unfolding.py --include ntpc7 --fail-fast`
- Output: `Studies/ValidationExec_2026-02-13/systematics_strict_check/unfolded_ntpc7.root`

8. Resolved: malformed 1994 MC `no_neutrals` variation file
- Previous symptom: `Tree 't' not found` in `alephMCRecoAfterCutPaths_1994_thrust_no_neutrals_t.root` during full systematic run.
- Root cause: stale/invalid old derivation artifact (file had only `Selection` key).
- Resolution:
  - Regenerated 1994 MC derivations from `/Users/anthonybadea/Documents/Documents/ALEPH/ALEPH/alephMCRecoAfterCutPaths_1994.root` with updated analyzer.
  - Verified `no_neutrals` file now contains tree `t`.
- Validation:
  - Full strict 1994 systematic campaign completed successfully in
    `Studies/ValidationExec_2026-02-13/systematics_full_1994/`.

9. Resolved: initial observable-generalization blocker in unfolding entrypoint
- `Unfolding/unfold_thrust.py` now accepts `observable` presets:
  - `thrust`, `c_parameter`, `heavy_jet_mass`
- Added template config:
  - `Unfolding/unfold_config_template.json`
- Note:
  - Full observable expansion still requires upstream derivation branches in `DataProcessing` for non-thrust observables.

10. Resolved: upstream branch availability for C-parameter / heavy-jet-mass
- `DataProcessing` output now includes:
  - `CParameter`
  - `HeavyJetMass`
- Code updates:
  - `DataProcessing/include/analysisTypes.h`
  - `DataProcessing/include/analysisCompute.h`
  - `DataProcessing/src/Analyze.cxx`
- Sanity validation:
  - `DataProcessing/temp/test_nominal_newshapes.root` contains both branches.
