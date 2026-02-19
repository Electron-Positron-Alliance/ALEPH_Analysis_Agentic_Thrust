# Next Steps Execution Plan (2026-02-17)

## Goal
Consolidate the thrust IBU(5) preliminary result into a reproducible and publication-ready package, then harden the analysis note sections 5 onward around that package.

## Phase 1: Provenance and Output Consolidation
1. Replace all remaining `ValidationExec_2026-02-13` references in the note with maintained outputs.
2. Mirror key validation plots into a single run-owned directory:
   - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/validation/iteration_scan/`
   - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/validation/systematics/`
3. Add a compact `README.md` under `.../validation/` documenting exact source scripts and commands.

## Phase 2: Analysis Workflow Hardening
1. Add one command entry-point that regenerates:
   - nominal unfold (iter=5),
   - iter envelope (4,6),
   - experimental variations,
   - theory variations,
   - covariance + uncertainty summary.
2. Ensure output contracts are validated with `Unfolding/scripts/check_prelim_summary_outputs.py` in CI-like style (fail on missing artifacts).
3. Add explicit hadronic-event selection correction audit output (before/after histogram + applied correction factors csv/json).

## Phase 3: Validation Upgrades
1. Re-run iteration scan with current nominal binning/config and save to the run-owned `validation/iteration_scan` folder.
2. Regenerate per-variation fractional-difference and ratio diagnostics under `validation/systematics`.
3. Add one summary table (JSON + LaTeX table source) listing worst-bin impacts per component family.

## Phase 4: Analysis Note Rewrite (Sections 5+)
1. Rewrite Section 5 (Analysis method) around executable workflow:
   - response construction,
   - IBU procedure,
   - nominal iteration choice (5),
   - hadronic correction ordering.
2. Rewrite Section 6 (Uncertainties):
   - statistical, iteration, experimental components, theory components,
   - covariance construction and combination assumptions.
3. Rewrite Section 7 (Results):
   - central result plot + ALEPH ratio,
   - uncertainty decomposition figures,
   - key quantitative metrics table.
4. Keep appendix as support; move only high-value diagnostics to main body.

## Phase 5: Delivery Criteria
1. Full `AnalysisNote/main.pdf` compiles without missing figures.
2. All figures in Sections 5--7 come from `Studies/PreliminaryResult/2026-02-17_thrust_iter5/`.
3. A single command can regenerate core thrust preliminary outputs and summary files.

## Immediate Execution Order
1. Compile note after the reference migration and confirm no old provenance links remain.
2. Create run-owned `validation/` subdirectories and copy linked diagnostics there.
3. Repoint note to those run-owned validation paths.
4. Recompile and freeze this as the baseline for the Section 5--7 rewrite pass.
