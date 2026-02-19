# Critical Review Assessment Plan (2026-02-18)

## Scope
- Review target: internal note + thrust result package + reproducibility chain.
- Artifacts reviewed:
  - `AnalysisNote/main.tex` and section/table sources.
  - `AnalysisNote/main.pdf` (layout/float/line-width behavior).
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/*`.
  - Producer scripts in `Unfolding/scripts/` and matrix exporter helper.
- Severity mode: high-rigor (any ambiguity/traceability gap is a finding).

## Severity Rubric
- `S0` Critical correctness/reproducibility failure.
- `S1` Major scientific communication or traceability defect.
- `S2` Medium clarity/structure issue that can mislead or slow reproduction.
- `S3` Minor cleanup/consistency improvement.

## Review Checklist
1. Scientific consistency:
- Nominal configuration consistency (`N_iter=5`, 4/6 systematic, uncertainty model) across Methods/Systematics/Results.
- Values stated in text cross-checked with `uncertainty_breakdown.json`.
2. Result artifact consistency:
- Final plot, component plots, covariance/correlation CSVs, binning CSV, metadata JSON present.
- Reproducibility checker outcome reviewed (`check_prelim_summary_outputs.py`).
3. Reproducibility traceability:
- Claims in note mapped to concrete scripts and output locations.
- Hidden environment/path assumptions identified.
4. Note quality:
- Internal-note style (method detail, explicit caveats, decision transparency).
- Float/layout quality and line-width integrity.

## Validation Run (executed)
- Command:
  - `conda run --no-capture-output -n py312 python Unfolding/scripts/check_prelim_summary_outputs.py --base-dir Studies/PreliminaryResult/2026-02-17_thrust_iter5`
- Outcome:
  - Summary outputs validated.
  - Statistical covariance off-diagonal entries reported as non-zero (`1980`).

## Findings (ordered by severity)

### F-001 (`S1`) — Reproducibility depends on machine-specific default paths
- Location:
  - `Unfolding/scripts/run_thrust_prelim_workflow.py:43`
  - `Unfolding/scripts/run_thrust_prelim_workflow.py:45`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:39`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:104`
- Issue:
  - Defaults include machine-local absolute paths for theory-weight inputs and implicit sibling-repo ALEPH CSV fallback.
- Evidence:
  - Workflow default `--theory-weights-dir` is an absolute local path.
  - Summary builder candidate path includes `../ALEPH/HEPData-ins636645-v1-Table_54.csv` fallback.
- Risk:
  - Reproduction can fail or silently diverge on another machine without explicit overrides.
- Fix direction:
  - Make defaults repository-relative or required CLI arguments.
  - Add explicit preflight error messages with remediation hints.

### F-002 (`S1`) — Note claims reproducibility but does not provide command-level rerun contract
- Location:
  - `AnalysisNote/sections/AIAgentUsage.tex:29`
  - `AnalysisNote/sections/AnalysisMethod.tex:8`
  - `AnalysisNote/sections/AnalysisMethod.tex:18`
- Issue:
  - The note states results are reproducible from artifacts/entrypoints but omits exact command invocations, required environment activation, and mandatory external inputs.
- Evidence:
  - Script names are listed, but no explicit rerun command block or required argument list is included in the note.
- Risk:
  - A reader cannot deterministically regenerate the release package from note text alone.
- Fix direction:
  - Add a compact “Reproduction contract” subsection with exact commands, env requirements, and required data/weights paths.

### F-003 (`S1`) — AI-agent feasibility section lacks measurable evaluation criteria
- Location:
  - `AnalysisNote/sections/AIAgentUsage.tex:4`
  - `AnalysisNote/sections/AIAgentUsage.tex:36`
- Issue:
  - Section frames the “can an agent carry out research” question but concludes feasibility without quantitative criteria or scored outcomes.
- Evidence:
  - No metrics for task success rate, correction count, failure classes, or human intervention load.
- Risk:
  - The central methodological claim is not auditable and reads as narrative assertion.
- Fix direction:
  - Add an evaluation table: task category, attempted, passed, required human correction, residual risk.

### F-004 (`S2`) — Matrix export is outside canonical workflow orchestration
- Location:
  - `AnalysisNote/sections/AnalysisMethod.tex:106`
  - `Unfolding/scripts/run_thrust_prelim_workflow.py:126`
- Issue:
  - Matrix visualization/export is documented as part of deliverables but is not executed by `run_thrust_prelim_workflow.py`; it requires separate manual/helper-script execution.
- Evidence:
  - No matrix-export call in workflow driver; matrices are produced by a separate script path.
- Risk:
  - Incomplete outputs if analyst runs only the canonical workflow command.
- Fix direction:
  - Either integrate matrix export into workflow driver or document it as a required explicit second command in note and README.

### F-005 (`S2`) — Statistical covariance fallback behavior is under-documented in note
- Location:
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:660`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:664`
  - `AnalysisNote/sections/AnalysisMethod.tex:103`
- Issue:
  - If raw unfolding covariance is missing, builder falls back to diagonal covariance from bin errors; note currently describes transformed unfolding covariance path only.
- Evidence:
  - Fallback path exists and is silent relative to note-level description.
- Risk:
  - Potential unnoticed downgrade in correlation realism in future reruns.
- Fix direction:
  - Document fallback explicitly and/or fail hard by default when covariance is expected but absent.

### F-006 (`S3`) — Obsolete table sources remain and can confuse maintenance
- Location:
  - `AnalysisNote/tables/workflow_map_table.tex`
  - `AnalysisNote/tables/systematics_execution_map_table.tex`
  - `AnalysisNote/tables/results_figure_provenance_table.tex`
- Issue:
  - These files remain in tree though corresponding rendered content has shifted to schematics/lists.
- Risk:
  - Future editors may update stale files and expect note changes that do not appear.
- Fix direction:
  - Remove or archive unused table files and update note README with current source-of-truth list.

## Open Questions / Assumptions
- Assumption A1: Current nominal numbers in Results are authoritative from `summary/uncertainty_breakdown.json` and do not require recomputation in this review pass.
- Assumption A2: The current thrust release is intentionally workstation-coupled for development speed, but next iteration should harden portability.

## Tasks After Review

### P0 tasks (must complete before claiming reproducible internal release)
1. `T-001` (from F-001): Replace machine-local defaults with explicit CLI requirements. `Status: Completed (2026-02-18)`
- Owner: TBD
- Steps:
  - Remove absolute default for `--theory-weights-dir`.
  - Require `--aleph-csv` when not found in repository-local default.
  - Add clear preflight failure messages.
- Done when:
  - Workflow and summary scripts run on a fresh machine with only documented repo inputs.

2. `T-002` (from F-002): Add note-level reproduction contract section. `Status: Completed (2026-02-18)`
- Owner: TBD
- Steps:
  - Add subsection in `AnalysisMethod` with exact commands:
    - workflow run,
    - summary build,
    - matrix export,
    - output checker.
  - Include environment requirements (`conda` env / ROOT setup).
- Done when:
  - Another analyst can regenerate `summary/` outputs from note instructions only.

3. `T-003` (from F-003): Add AI-agent evaluation scorecard. `Status: Completed (2026-02-18)`
- Owner: TBD
- Steps:
  - Add table with task categories (workflow execution, plotting revisions, note edits, consistency checks), pass/fail counts, and required human interventions.
  - Add residual-risk statement.
- Done when:
  - “Agent feasibility” section has auditable quantitative basis.

### P1 tasks (should complete next cycle)
4. `T-004` (from F-004): Close matrix-export orchestration gap.
- Owner: TBD
- Steps:
  - Option A: integrate matrix export into `run_thrust_prelim_workflow.py` behind a flag.
  - Option B: keep separate, but add explicit required step in note/README and fail checker if matrix products missing.
- Done when:
  - No ambiguity about required commands to generate matrix products.

5. `T-005` (from F-005): Harden covariance expectation.
- Owner: TBD
- Steps:
  - Add `--require-covariance` mode defaulting to true for nominal release builds.
  - Document fallback behavior only for exploratory/debug runs.
- Done when:
  - Release pipeline cannot silently fall back to diagonal covariance.

### P2 tasks (cleanup)
6. `T-006` (from F-006): Remove/archive stale note table files.
- Owner: TBD
- Steps:
  - Delete or move unused tables to `archive/`.
  - Add short source-of-truth list in `AnalysisNote/README.md`.
- Done when:
  - No dead note sources remain in active table directory.

## Exit Criteria
- No open `S0` and no unresolved `S1` without explicit acceptance rationale.
- Reproduction contract exists in note and is executable end-to-end.
- AI-agent feasibility section contains quantitative evidence, not only narrative claims.
- Required outputs and checker pass for the target run directory.
