# Section 5+ Deep Review: Current State and Outstanding Tasks

## Scope of this review
This review compares the current note content (Sections 5-8) to:
1. The generated study artifacts in `Studies/ValidationExec_2026-02-13`.
2. The ALEPH-style internal note structure and text depth in `/Users/anthonybadea/Downloads/LEP1_thrust_analysis_note`.
3. The thrust paper draft context in `/Users/anthonybadea/Downloads/LEP1_thrust_paper-4/AlephLep1Thrust.tex`.

## What is now implemented (completed)
1. Sections 5-8 were rewritten around Iterative Bayesian Unfolding (IBU) and no OmniFold method text remains in these sections.
2. Response, covariance, and correlation matrix products are now explicitly documented and shown with nominal figures.
3. Systematics section now has a grouped combination model with explicit equations and stress-test handling (`no_neutrals` separated).
4. Results are reorganized around a measurement package: nominal spectrum, iteration validation, systematics impact, and release products.
5. Script-backed metrics/tables are in place:
   - `Studies/ValidationExec_2026-02-13/scripts/make_note_metrics.py`
   - `AnalysisNote/tables/method_config_table.tex`
   - `AnalysisNote/tables/systematics_definition_table.tex`
   - `AnalysisNote/tables/results_key_metrics_table.tex`
6. Build status is stable (`pdflatex` runs successfully).

## High-priority outstanding tasks
1. Per-bin publication table is missing.
   - Add a machine-generated table (or external CSV reference) with bin edges, central values, stat uncertainty, syst uncertainty, and total uncertainty.
   - Include an explicit map to covariance/correlation matrix bin order.
2. Systematic uncertainty interpretation needs stronger physics guidance.
   - Current summaries include very large tail fractions in some bins (from low-population regions).
   - Add explicit handling policy in text: tail-bin interpretation, optional reporting masks, and whether any bins are excluded from key quoted aggregates.
3. Comparison-to-reference measurement narrative is still thin in Section 7.
   - Add a dedicated result comparison subsection against previous ALEPH thrust publication in matching binning, with ratio and uncertainty context.
4. Correlation-matrix usability text should be expanded for theory users.
   - Include exact instructions for consuming `matrix_unfold_covariance.csv`, `matrix_unfold_correlation.csv`, and binning maps.

## Medium-priority outstanding tasks
1. Add a dedicated uncertainty-breakdown figure in the main text for grouped components (`track/event`, `neutral-response`, total systematic, statistical).
2. Add one short subsection clarifying regularization bias-variance logic behind the chosen iteration (`N_iter = 7`) beyond threshold criteria.
3. Add explicit closure/refolding acceptance criteria table (what thresholds are required to accept nominal).
4. Add short reproducibility note: exact commands used to regenerate note metrics/tables and output hashes (or timestamps).

## Lower-priority editorial tasks
1. Tighten captions in Sections 6-7 to explicitly state what each panel validates or falsifies.
2. Reduce remaining LaTeX table underfull warnings by minor table-format tuning.

## Recommended next implementation order
1. Generate per-bin result and uncertainty table from nominal ROOT + grouped systematics JSON.
2. Add ALEPH-comparison plot/subsection in Section 7.
3. Add grouped uncertainty breakdown figure and explanation in Section 6/7.
4. Add theory-user instructions for matrix products and bin maps.
