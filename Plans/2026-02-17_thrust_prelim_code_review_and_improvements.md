# Thrust Preliminary Workflow: Code Review and Improvement Actions (2026-02-17)

## Scope reviewed
- `Unfolding/unfold_thrust.py`
- `Studies/UnfoldingSystematics/scripts/run_systematic_unfolding.py`
- `Studies/PreliminaryResult/scripts/run_thrust_prelim_workflow.py`
- `Studies/PreliminaryResult/scripts/build_prelim_uncertainty_summary.py`
- Runtime products under `Studies/PreliminaryResult/2026-02-17_thrust_iter5/`

## Findings (ordered by impact)

1. **Statistical covariance basis mismatch in final uncertainty combination (fixed).**
- Issue: statistical covariance was originally mixed in count-space while systematic components were in normalized differential cross-section space.
- Fix applied: `build_prelim_uncertainty_summary.py` now transforms covariance to `1/N dN/dT` basis using Jacobian propagation, including hadronic-correction scaling.
- Residual risk: RooUnfold covariance still reflects unfolding-level assumptions and does not include hadronic-correction uncertainty.

2. **Theory reweighting had no implementation path in ROOT IBU pipeline (fixed).**
- Issue: prior workflow had no dedicated theory systematic propagation through response/prior in `unfold_thrust.py`.
- Fix applied: added event-level weight loading from `.npy`, mapping `tgenBefore -> tgen` by `uniqueID`, weighted response fill/miss, weighted hadronic correction, and QA histograms (`theory_weights_tgenBefore`, `theory_weights_tgen_mapped`, `theory_weight_coverage`).
- Validation: all three theory runs completed with full mapping coverage in this dataset (`771597/771597`).

3. **Experimental systematics runner excluded `no_neutrals` by default (fixed).**
- Issue: default exclude list in `run_systematic_unfolding.py` omitted `no_neutrals`.
- Fix applied: default exclude now only skips `no_event_sel`; `no_neutrals` is executed and retained as cross-check.

4. **Environment inconsistency for production runs (partially mitigated).**
- Issue: direct system python lacked `numpy`; weighted unfolding failed if not using analysis environment.
- Mitigation applied: `run_thrust_prelim_workflow.py` now runs all jobs through `conda run --no-capture-output -n py312` by default.
- Remaining improvement: add explicit environment preflight checks for `ROOT` and `numpy` with clearer early failure message.

5. **Large per-bin fractional shifts in extreme bins (observed; not a bug by itself).**
- Observation: max fractional shifts are large in low-population edge bins (e.g., `exp_total` and `no_neutrals` maxima).
- Recommendation: add central-bin/physics-range summary metrics alongside full-range maxima to avoid overinterpreting edge-bin spikes.

## Implemented outputs in this pass
- Full workflow runner and uncertainty aggregator:
  - `Studies/PreliminaryResult/scripts/run_thrust_prelim_workflow.py`
  - `Studies/PreliminaryResult/scripts/build_prelim_uncertainty_summary.py`
  - `Studies/PreliminaryResult/README.md`
- Updated unfolding config template with theory-weight options:
  - `Unfolding/unfold_config_template.json`
- Completed run bundle:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/`
  - Includes nominal, iteration, all experimental variations, theory variations, covariance/correlation CSVs, and final plots.

## High-priority next improvements
1. Add a strict uniqueness/assertion check for `uniqueID` in `tgen` and `tgenBefore` before weight mapping.
2. Add optional clipping/robustness scan for theory weights to quantify sensitivity to large tails.
3. Include an alternative summary excluding low-stat bins (or minimum-yield mask) for stability reporting.
4. Add automated regression checks:
- expected output file matrix exists
- theory mapping coverage > 99.9%
- covariance matrix positive semidefinite tolerance checks
- uncertainty JSON schema validation.

## Medium-priority improvements
1. Add multiprocessing support for independent variations to reduce runtime.
2. Add direct matrix ROOT outputs for total covariance/correlation (currently CSV only).
3. Add summary table export for note integration (mean/max per source over central and full bin ranges).
