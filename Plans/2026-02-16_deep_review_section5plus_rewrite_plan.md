# Plan: Deep Rewrite of Sections 5-8 (Thrust + Iterative Bayesian Unfolding)

## Summary
This plan rewrites `AnalysisNote/sections/AnalysisMethod.tex`, `AnalysisNote/sections/SystematicUncertainties.tex`, `AnalysisNote/sections/Results.tex`, and `AnalysisNote/sections/Conclusion.tex` to match ALEPH-note style while fixing weaknesses identified by comparison with:
1. Current study artifacts in `Studies/ValidationExec_2026-02-13`.
2. Reference ALEPH note source in `/Users/anthonybadea/Downloads/LEP1_thrust_analysis_note`.
3. DELPHI reference PDF in `/Users/anthonybadea/Downloads/DELPHI_Event_Shape_260122.pdf`.

Chosen direction:
1. Section model: ALEPH-note compact structure.
2. Figure policy: main-text heavy.
3. Systematics model: grouped categories with explicit total-combination recipe.

## Current Gaps To Fix
1. Section 5 lacks publication-grade analysis-chain readability and explicit QA anchors for each correction stage.
2. Section 6 is too thin: missing category-level decomposition logic and explicit total-uncertainty construction.
3. Section 7 mixes metrics, outputs, and interpretation without a clean final-measurement package structure.
4. Some quoted numbers are not machine-traceable to dedicated summary artifacts.
5. Main text under-explains plot logic versus reference-note standard.

## Scope
1. In scope: full rewrite of Sections 5-8 plus supporting scripts/tables needed for traceability.
2. In scope: add new analysis-note input artifacts generated from `Studies` outputs.
3. In scope: thrust-only physics scope in this pass.
4. Out of scope: new C-parameter/heavy-jet-mass results in main text.

## Section 5 Rewrite Spec (`AnalysisNote/sections/AnalysisMethod.tex`)
1. Keep compact section header, with fixed subsection order:
   1. Thrust observable definitions and binning.
   2. Response construction and matching logic.
   3. Iterative Bayesian Unfolding configuration and iteration choice.
   4. Post-unfolding hadronic event-selection correction.
   5. Covariance and correlation construction.
2. Add explicit QA checkpoints after each subsection with direct artifact references.
3. Add a concise methods decision table with rows:
   1. Observable and range.
   2. Binning.
   3. Matching key.
   4. Selection branch.
   5. Nominal iterations.
   6. Hadronic correction toggle.
   7. Covariance mode.
4. Add one figure paragraph per method figure explaining what failure mode it validates against.
5. Remove statements not directly backed by current files or generated metrics.

## Section 6 Rewrite Spec (`AnalysisNote/sections/SystematicUncertainties.tex`)
1. Use compact ALEPH-style structure with subsections:
   1. Definition of systematic categories.
   2. Per-variation propagation procedure.
   3. Category grouping and combination recipe.
   4. Statistical covariance treatment and total-uncertainty assembly.
2. Define category groups and membership:
   1. Track/event selection: `ntpc7`, `pt04`, `ech10`, `with_met`.
   2. Neutral-response modeling: `nes_up`, `nes_down`, `ner`.
   3. Analysis-choice stress test: `no_neutrals` (reported separately, not merged into nominal total by default).
3. Define bin-wise combination formula:
   1. Two-sided source: max absolute of up/down.
   2. One-sided source: absolute shift to nominal.
   3. Group envelope: quadrature of member shifts.
   4. Total systematic: quadrature of group envelopes.
4. Define total covariance policy:
   1. `V_stat`: full RooUnfold covariance.
   2. `V_syst_diag`: diagonal from squared total systematic bin shifts.
   3. `V_total = V_stat + V_syst_diag`.
5. Add table of systematic sources with exact operational definitions and output files.

## Section 7 Rewrite Spec (`AnalysisNote/sections/Results.tex`)
1. Reorder into a clear measurement package:
   1. Nominal unfolded spectrum and comparison views.
   2. Iteration validation summary.
   3. Systematic impact summary and total uncertainty.
   4. Matrix products and public-use artifacts.
2. Keep main-text heavy figures, grouped by purpose:
   1. Central result panel.
   2. Iteration scan diagnostics.
   3. Systematics overlay and fractional differences.
   4. Response/covariance/correlation matrices.
3. Replace manually typed key metrics with script-generated values.
4. Add “data products for theory use” table listing ROOT outputs, CSV products, binning maps, and directories.

## Section 8 Update (`AnalysisNote/sections/Conclusion.tex`)
1. Summarize thrust-only IBU baseline deliverables.
2. Explicitly state released products for phenomenology.
3. Keep future scope paragraph for C-parameter/heavy-jet-mass and multidimensional correlation products.

## New Supporting Interfaces / Outputs
1. Add script: `Studies/ValidationExec_2026-02-13/scripts/make_note_metrics.py`.
2. Script outputs:
   1. `Studies/ValidationExec_2026-02-13/note_metrics/section5_metrics.json`.
   2. `Studies/ValidationExec_2026-02-13/note_metrics/section6_systematics_summary.json`.
   3. `Studies/ValidationExec_2026-02-13/note_metrics/section7_results_summary.json`.
3. Add generated LaTeX table fragments:
   1. `AnalysisNote/tables/method_config_table.tex`.
   2. `AnalysisNote/tables/systematics_definition_table.tex`.
   3. `AnalysisNote/tables/results_key_metrics_table.tex`.
4. Note text should reference generated products, not hard-coded numbers.

## Work Sequence
1. Build metrics-extraction script and generate JSON/table fragments from existing `Studies` outputs.
2. Rewrite Section 5 with generated method metrics and QA anchors.
3. Rewrite Section 6 with grouped systematics and fixed covariance/total-combination policy.
4. Rewrite Section 7 with reorganized flow and script-backed numbers.
5. Update Section 8 language and outlook.
6. Rebuild PDF and run consistency checks.
7. Produce/update review artifact with remaining issues.

## Validation
1. Build: run `pdflatex -interaction=nonstopmode -halt-on-error main.tex` twice.
2. Consistency: every quoted number in Sections 5-7 must appear in generated JSON/table artifacts.
3. Traceability: every method/systematic/result claim must cite a concrete file path in `Studies/ValidationExec_2026-02-13`.
4. Structure: section ordering and subsection titles remain ALEPH-compact.
5. Warnings: no cross-reference rerun warnings after second compile.
6. Physics scope: thrust-only corrected measurement results in main text.

## Acceptance Criteria
1. Sections 5-7 are clear, structured, and publication-ready in ALEPH-note style.
2. Section 6 provides explicit grouped decomposition and total combination model.
3. Section 7 presents a coherent final measurement package with main-text-heavy diagnostics.
4. Key numbers are script-traceable and reproducible from current `Studies` artifacts.
5. Conclusion states delivered thrust baseline and next-step expansion scope.

## Assumptions and Defaults
1. Nominal thrust baseline remains 1994 with `N_iter = 7`.
2. Existing `Studies/ValidationExec_2026-02-13` artifacts are authoritative.
3. No new unfolding production is required unless a hard traceability gap is found.
4. `no_neutrals` is treated as a stress-test variation and reported separately by default.
