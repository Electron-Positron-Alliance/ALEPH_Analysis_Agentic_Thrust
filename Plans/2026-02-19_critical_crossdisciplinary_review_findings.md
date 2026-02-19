# Critical Cross-Disciplinary Review Findings (2026-02-19)

## Executive Gate Decision
`Conditional-go (internal)` and `No-go (theory-facing release)`.

Rationale:
1. No `S0` correctness failures were found.
2. Multiple unresolved `S1` findings remain that materially limit interpretation portability and theory-facing reuse.

## Validation Snapshot
- Checker command passed:
  - `python3 Unfolding/scripts/check_prelim_summary_outputs.py --base-dir Studies/PreliminaryResult/2026-02-17_thrust_iter5`
- Reported by checker:
  - `cov_stat off-diagonal non-zero entries: 1980`
- Additional matrix probes (non-mutating):
  - `cov_total` shape `(50,50)`, symmetric.
  - `corr_total` shape `(50,50)`, symmetric.
  - `corr_total` max off-diagonal magnitude `0.14004751471`.
  - `cov_total` nonpositive diagonal bins: `5`.
  - `cov_total` minimum eigenvalue `0.0`, condition number (positive spectrum) `~8.59e16`.

## Findings (ordered by severity)

### F-EXP-001 (`S1`) — Hadronic-correction uncertainty is excluded from the nominal total
- Perspective: `EXP`
- Evidence:
  - `AnalysisNote/sections/SystematicUncertainties.tex:43`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:967`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_breakdown.json:112`
- Observation:
  - The note explicitly states hadronic-correction uncertainty is not propagated.
  - Summary metadata confirms `"hadronic_correction_uncertainty_included": false`.
- Impact:
  - Total uncertainty can be underestimated in bins where `tgenBefore/tgen` is nontrivial.
- Required fix:
  - Add dedicated hadronic-correction variation(s) and include them in the nominal total covariance model.
- Verification test:
  - New metadata key shows `hadronic_correction_uncertainty_included: true` and added `cov_hadronic.csv` contribution in total.

### F-TH-001 (`S1`) — Systematic covariance uses diagonal approximation while results are presented as downstream-fit ready
- Perspective: `TH`
- Evidence:
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:706`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:707`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:708`
  - `Unfolding/scripts/build_prelim_uncertainty_summary.py:962`
  - `AnalysisNote/sections/SystematicUncertainties.tex:41`
  - `AnalysisNote/sections/Results.tex:70`
- Observation:
  - Iteration/experimental/theory covariances are diagonal-by-construction (`np.diag(...)`), while note language positions products for direct theory fits.
- Impact:
  - Correlated systematics structure is likely under-modeled for precision extractions.
- Required fix:
  - Introduce correlation models for non-statistical components (or release explicit conservative alternatives with caveat labels).
- Verification test:
  - Non-statistical covariance components contain non-zero off-diagonals with documented construction rule and validation plots.

### F-TH-002 (`S1`) — Released full-range covariance is singular due zero-content bins
- Perspective: `TH`
- Evidence:
  - `AnalysisNote/sections/AnalysisMethod.tex:72`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv:2`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv:3`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv:4`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv:5`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv:7`
- Quantitative evidence:
  - `5` bins have zero nominal differential value and zero total variance.
  - `cov_total` minimum eigenvalue `0.0` and large positive-spectrum condition number `~8.59e16`.
- Impact:
  - Direct covariance inversion is unstable/undefined for many fit workflows without explicit bin masking or regularization instructions.
- Required fix:
  - Publish a recommended fit window or masked covariance product alongside full-range output.
- Verification test:
  - Added machine-readable mask (or reduced-range covariance) and documented inversion-safe usage.

### F-AIML-001 (`S1`) — Reproducibility provenance is incomplete for strict audit (missing immutable code/runtime identifiers)
- Perspective: `AIML`
- Evidence:
  - `AnalysisNote/sections/AIAgentUsage.tex:29`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json:1`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json:2`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json:3`
- Observation:
  - Artifact JSON captures paths and command overrides but not git commit hash, environment package versions, or RooUnfold/ROOT version fingerprints.
- Impact:
  - Exact rerun/audit equivalence cannot be guaranteed across machines or over time.
- Required fix:
  - Persist immutable provenance fields (`git_commit`, `python_version`, `root_version`, `roounfold_version`, env spec hash).
- Verification test:
  - `workflow_summary.json` and `uncertainty_breakdown.json` include immutable provenance keys and checker enforces presence.

### F-EXP-002 (`S2`) — Integrity checker passes despite fit-critical covariance degeneracy
- Perspective: `EXP`
- Evidence:
  - `Unfolding/scripts/check_prelim_summary_outputs.py:129`
  - `Unfolding/scripts/check_prelim_summary_outputs.py:131`
  - `Unfolding/scripts/check_prelim_summary_outputs.py:132`
  - `Unfolding/scripts/check_prelim_summary_outputs.py:158`
- Observation:
  - Checker requires only that at least one diagonal entry is positive and does not enforce diagnostics for zero-variance bins, PSD quality, or condition thresholds.
- Impact:
  - “Validated summary outputs” can be misread as fit-readiness.
- Required fix:
  - Add explicit warnings/fail modes for zero-variance bins, singularity, and large condition number.
- Verification test:
  - Checker emits structured diagnostics and nonzero exit when strict-fit mode is enabled and thresholds fail.

### F-TH-003 (`S2`) — Theory-weight coverage diagnostics are not persisted in release metadata
- Perspective: `TH`
- Evidence:
  - `Unfolding/unfold_thrust.py:782`
  - `Unfolding/unfold_thrust.py:790`
  - `Unfolding/unfold_thrust.py:793`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json:1`
- Observation:
  - Weight coverage and distribution stats are printed to stdout but not captured in the release JSON products.
- Impact:
  - Theory-variation quality cannot be audited from artifacts alone.
- Required fix:
  - Persist theory-weight mapping diagnostics into workflow summary and note-facing tables.
- Verification test:
  - Metadata contains per-theory coverage fraction, effective weight stats, and clipping/normalization flags.

### F-AIML-002 (`S2`) — Communication appendix is reconstructed rather than verbatim transcript
- Perspective: `AIML`
- Evidence:
  - `AnalysisNote/appendix/App_CommunicationSummary.tex:4`
  - `AnalysisNote/appendix/App_CommunicationSummary.tex:5`
- Observation:
  - Appendix explicitly states it is reconstructed from artifacts, not raw message logs.
- Impact:
  - Limits independent audit of agent-human interaction claims and instruction compliance.
- Required fix:
  - Add an optional machine-readable conversation manifest (timestamps, action type, files changed, command hashes), even if full raw chat is withheld.
- Verification test:
  - Appendix links to a generated manifest artifact for this run cycle.

## Cross-Check: Note Metric Consistency
The following values in `AnalysisNote/tables/results_key_metrics_table.tex` are consistent with `summary/uncertainty_breakdown.json`:
1. Mean total uncertainty central: `7.65%`.
2. Mean stat central: `1.71%`.
3. Mean unfolding central: `0.34%`.
4. Mean experimental central: `3.34%`.
5. Mean theory central: `6.08%`.
6. Highest-bin ALEPH/unfolded ratio: `1.30 ± 0.27`.

## Assumptions
1. This review targets the current thrust-only baseline (`2026-02-17_thrust_iter5`) without recomputing physics outputs.
2. Severity reflects readiness for external/theory-facing reuse, not only internal iteration speed.
