# ALEPH LEP1 Event-Shape Reanalysis (IBU-First): Execution Plan

## Summary
Build a thrust-first, DELPHI-style iterative Bayesian unfolding workflow in ROOT/RooUnfold, perform a full-code audit across data processing/unfolding/systematics, and produce a JHEP-style analysis note scaffold (matching ALEPH note structure) with a clear roadmap to add C-parameter and heavy-jet mass next.

Chosen scope:
- Review scope: full audit
- Note scope: thrust-first with expansion roadmap
- Validation bar: DELPHI-style suite

## Public Interfaces / Config / Outputs
1. Stabilize unfolding config contract in `Unfolding/unfold_config.json`:
- Keep: `data_file`, `reco_mc_file`, `gen_mc_file`, tree/branch names, binning, `iterations`
- Add over time: `observable`, hadronic-correction toggle, regularization-scan config, validation thresholds, systematic controls

2. Unfolding execution modes:
- Nominal unfolding
- Closure mode
- Iteration scan and diagnostics
- Systematic variation runs

3. Output contract:
- ROOT objects: unfolded nominal/corrected, response, covariance/diagnostics
- JSON summaries: matching stats, iteration recommendation, chi2 diagnostics, pass/fail checks

4. Analysis note artifacts:
- `AnalysisNote/main.tex`
- `AnalysisNote/sections/*.tex`
- Figure checklist and script-to-figure traceability

## Phase 1: Full Code Review
1. Audit `DataProcessing` for selection logic, return codes, reproducibility.
2. Audit `Unfolding/unfold_thrust.py` for tree defaults, matching semantics, closure path, correction propagation.
3. Audit `Studies/UnfoldingSystematics` and `Studies/UnfoldingIterationScan` for variation logic and iteration recommendation behavior.
4. Produce severity-ranked findings with file/line references and required tests.

Deliverable:
- `Plans/2026-02-13_code_review_findings.md`

## Phase 2: Validation Standardization (DELPHI-style)
1. Define and run nominal validation suite:
- Closure (MC reco pseudo-data -> MC truth)
- Refolding (unfolded data -> reco vs measured data)
- Iteration stability (`N` vs `N-1`, counts and shape)
- Toy closure and over-regularization checks
- Systematic stability checks

2. Capture acceptance thresholds and recommended nominal iteration.

Deliverables:
- Validation outputs under `Studies/UnfoldingIterationScan/`
- Summary in findings note

## Phase 3: Thrust Analysis Note Scaffold (JHEP-style)
1. Create JHEP-like section structure:
- Introduction
- ALEPH detector
- Data and simulated samples
- Event reconstruction and selection
- Analysis method (IBU)
- Systematic uncertainties
- Results
- Conclusion
- Appendices (diagnostics/implementation)

2. Ensure method text is IBU-first (no OmniFold dependency).

Deliverables:
- `AnalysisNote/` scaffold with section templates

## Phase 4: Observable Expansion Roadmap
1. Add C-parameter and heavy-jet-mass calculation to processing chain.
2. Generalize unfolding pipeline to be observable-driven.
3. Reuse validation suite and note structure for each observable.

## Test Cases
1. Static/smoke:
- Python compile checks for scripts
- CLI help checks

2. Functional:
- Nominal thrust unfolding run
- Closure run
- Iteration scan run
- Systematics run (selected and full)

3. Regression:
- Compare key metrics/plots before vs after fixes
- Ensure branch/tree misconfiguration fails fast with actionable errors

## Assumptions / Defaults
1. Nominal dataset remains LEP1 1994 due available detector-level MC.
2. RooUnfold IBU is the production unfolding method.
3. Current systematics set remains baseline: `ntpc7`, `pt04`, `ech10`, `with_met`, `nes_up`, `nes_down`, `ner`.
4. Iteration choice is metrics-driven and documented in outputs.
