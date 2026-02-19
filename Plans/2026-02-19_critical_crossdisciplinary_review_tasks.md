# Post-Review Task Backlog (2026-02-19)

## Priority Legend
- `P0`: must complete before theory-facing or externally shared preliminary package.
- `P1`: should complete in next analysis iteration.
- `P2`: quality and governance hardening.

## P0 Must-Fix Tasks

### T-EXP-001 (from F-EXP-001)
- Goal: include hadronic-correction uncertainty in nominal total uncertainty model.
- Actions:
  1. Add hadronic-correction variation branch generation in workflow.
  2. Propagate resulting per-bin shifts in `build_prelim_uncertainty_summary.py`.
  3. Export `cov_hadronic.csv` and include in `cov_total`.
  4. Update note text and systematics chart to include component.
- Acceptance:
  - `uncertainty_breakdown.json` reports `hadronic_correction_uncertainty_included: true`.
  - Total covariance equals sum of all declared components including hadronic.

### T-TH-001 (from F-TH-001)
- Goal: replace diagonal-only non-statistical covariance approximation or publish explicit alternatives.
- Actions:
  1. Define correlation model for iteration/experimental/theory components (at minimum, block models by source group).
  2. Implement component covariance builders with non-zero off-diagonals where justified.
  3. Keep diagonal model as optional conservative mode for cross-check.
  4. Document chosen model and rationale in note.
- Acceptance:
  - Component covariance exports include non-zero off-diagonal structure by policy.
  - Note clearly distinguishes nominal model and alternative conservative model.

### T-TH-002 (from F-TH-002)
- Goal: make released covariance inversion-safe for theory users.
- Actions:
  1. Add machine-readable fit mask (recommended bins) and masked covariance/correlation outputs.
  2. Provide full-range outputs as auxiliary products with explicit caveat.
  3. Add note subsection describing inversion-safe usage.
- Acceptance:
  - New files: `fit_mask.csv`, `cov_total_fitwindow.csv`, `corr_total_fitwindow.csv`.
  - Checker strict mode validates positive diagonal and invertibility on fit-window covariance.

### T-AIML-001 (from F-AIML-001)
- Goal: add immutable provenance for strict reproducibility/audit.
- Actions:
  1. Capture git commit hash and dirty state at workflow start.
  2. Capture runtime versions (`python`, `ROOT`, `RooUnfold`) and environment identifier.
  3. Persist these fields in `workflow_summary.json` and `uncertainty_breakdown.json`.
  4. Extend checker to require provenance keys.
- Acceptance:
  - Both JSON artifacts include immutable provenance block.
  - Checker fails if provenance block is missing.

## P1 Next-Iteration Tasks

### T-EXP-002 (from F-EXP-002)
- Goal: strengthen checker semantics from file existence to fit-quality diagnostics.
- Actions:
  1. Add thresholds for zero-variance bins and condition number.
  2. Add PSD diagnostic output and optional strict fail behavior.
  3. Emit a compact QA report (`summary/qa_report.json`).
- Acceptance:
  - Checker reports and enforces matrix-quality thresholds under `--strict-fit`.

### T-TH-003 (from F-TH-003)
- Goal: persist theory-weight quality diagnostics in release metadata.
- Actions:
  1. Store per-theory coverage and weight-stat keys in workflow summary.
  2. Add table row in note summarizing coverage and weight spread.
- Acceptance:
  - Workflow summary contains per-theory diagnostic block.
  - Note includes reproducible citation to metadata values.

## P2 Governance/Documentation Tasks

### T-AIML-002 (from F-AIML-002)
- Goal: improve agent-human auditability without forcing raw chat publication.
- Actions:
  1. Generate conversation manifest with timestamped actions (plan, command, file edits, review decisions).
  2. Link appendix communication summary to manifest artifact.
- Acceptance:
  - Appendix includes manifest path and schema description.
  - Manifest can be regenerated from run logs and git history.

## Recommended Implementation Order
1. `T-AIML-001` (provenance) and `T-EXP-001` (hadronic component) first.
2. `T-TH-002` (fit-window products) next to unblock theory reuse.
3. `T-TH-001` (correlated systematics model) after model decision lock.
4. `T-EXP-002`, `T-TH-003`, and `T-AIML-002` in the next hardening pass.

## Exit Criteria for Next Review Gate
1. All `P0` tasks completed with checker-backed evidence.
2. No unresolved `S1` findings remain.
3. Theory-facing package includes explicit fit-window products and provenance metadata.
