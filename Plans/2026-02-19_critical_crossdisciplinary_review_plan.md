# Critical Cross-Disciplinary Review Plan (2026-02-19)

## Objective
Run a full-gate critical review of the thrust preliminary workflow and internal note from three perspectives:
1. Experimental physics validity.
2. Theoretical physics usability.
3. AI/ML workflow rigor and auditability.

## Deliverables
1. `Plans/2026-02-19_critical_crossdisciplinary_review_plan.md` (this file).
2. `Plans/2026-02-19_critical_crossdisciplinary_review_findings.md` (severity-ranked findings with evidence).
3. `Plans/2026-02-19_critical_crossdisciplinary_review_tasks.md` (prioritized post-review actions).

## Review Scope
- Workflow scripts:
  - `Unfolding/scripts/run_thrust_prelim_workflow.py`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py`
  - `Unfolding/scripts/check_prelim_summary_outputs.py`
  - `Unfolding/unfold_thrust.py`
- Result artifacts:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/*`
- Internal note sections/tables:
  - `AnalysisNote/sections/AnalysisMethod.tex`
  - `AnalysisNote/sections/SystematicUncertainties.tex`
  - `AnalysisNote/sections/Results.tex`
  - `AnalysisNote/sections/AIAgentUsage.tex`
  - `AnalysisNote/sections/ChallengesAndLimitations.tex`
  - `AnalysisNote/appendix/App_CommunicationSummary.tex`

## Severity Rubric
- `S0`: scientific-invalidating correctness failure.
- `S1`: major risk for interpretation/reuse/release quality.
- `S2`: important clarity/portability/maintenance gap.

## Evidence Standard
Every finding must include:
1. Perspective tag (`EXP`, `TH`, `AIML`).
2. Exact `path:line` references.
3. Quantitative evidence when available.
4. Required fix and a concrete verification test.

## Execution Procedure
1. Validate generated artifacts and checker pass status.
2. Cross-check note claims against script behavior and JSON metadata.
3. Evaluate covariance/correlation suitability for theory reuse.
4. Evaluate AI-agent section against auditable evidence criteria.
5. Produce integrated findings and release gate decision.
6. Convert findings into implementation-ready tasks grouped by priority.

## Non-Mutating Validation Commands Used
1. `python3 Unfolding/scripts/check_prelim_summary_outputs.py --base-dir Studies/PreliminaryResult/2026-02-17_thrust_iter5`
2. Matrix sanity probes (symmetry, diagonal positivity count, eigenvalues, condition number) on `cov_total.csv` and `corr_total.csv`.
3. JSON metric extraction from `summary/uncertainty_breakdown.json`.
4. Source inspections with `nl -ba` and `rg -n` for note/script consistency checks.

## Gate Definition
- `No-go` if unresolved `S0` exists.
- `Conditional-go` if no `S0`, but unresolved `S1` items remain.
- `Go` only if all must-fix (`S1`) items are closed with verification evidence.

## Default Decisions Locked
1. Review depth: full gate.
2. Output format: one integrated findings register, one task backlog.
3. Baseline artifact set: `Studies/PreliminaryResult/2026-02-17_thrust_iter5`.
