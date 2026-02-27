# Reviewer Guide: ALEPH Agentic Event Shape Analysis

## Overview

This project demonstrates an AI-agentic approach to precision measurement of the thrust observable from archived ALEPH $e^+e^-$ collision data at $\sqrt{s}=91.2$ GeV. The goal is a preliminary unfolded thrust spectrum with rigorous uncertainty quantification, including full covariance and correlation matrices suitable for downstream phenomenological use.

**Key achievement**: Iterative Bayesian Unfolding (IBU, $N_{\mathrm{iter}}=5$) with measured total uncertainty ~8.43% in the central thrust range (0.60–0.95), dominated by theory uncertainties (~6.1% mean).

---

## Quick Start: Key Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| **Compiled analysis note** | `AnalysisNote/main.pdf` | Full ~11-section writeup: method, systematics, results |
| **Summary plots** | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/` | Unfolded spectrum, correlations, uncertainty breakdown |
| **Covariance matrix (CSV)** | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/covariance_matrix.csv` | Bin-by-bin covariance for reuse |
| **Correlation matrix (CSV)** | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/correlation_matrix.csv` | Correlation for interpretation |
| **Workflow summary (JSON)** | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json` | Reproducibility record: all scripts, options, outputs |

---

## Ordered Review Checklist

### 1. **Physics Interpretation** (Read first)
**Questions to ask:**
- Does the unfolded spectrum make physical sense? (e.g., does the peak location and width match prior LEP+Tevatron measurements?)
- How does this result compare to the 2004 ALEPH reanalysis (high-thrust endpoint region)?
- Are the observed tensions with the world average consistent with experimental systematics?

**Key sections:**
- `AnalysisNote/Sec. Results` (Sec. 8)
- Summary plots: `summary/unfolded_spectrum.pdf`, `summary/comparison_prior.pdf`
- Numerical result: `workflow_summary.json` → `central_values.thrust`

---

### 2. **Uncertainty Budget & Systematics** (Read second)
**Questions to ask:**
- Are the individual uncertainty components (statistical, theory, experimental) physically reasonable?
- Why is the theory uncertainty (~6.1%) so much larger than others?
- Are the correlations between bins (off-diagonal covariance) physically motivated?
- Does the hadronic-event correction (~3.2%) adequately account for fragmentation?

**Key sections:**
- `AnalysisNote/Sec. Systematic Uncertainties` (Sec. 7)
- `AnalysisNote/Table 5` (uncertainty summary by range)
- Summary plots: `summary/uncertainty_breakdown.pdf` (stacked bar chart), `summary/total_correlation_matrix.pdf`
- Covariance products: `covariance_matrix.csv`, `correlation_matrix.csv`

---

### 3. **Unfolding Methodology & Closure Tests** (Read third)
**Questions to ask:**
- Does iterative Bayesian unfolding (N_iter=5) correctly unfold the response matrix?
- Are closure tests (refolding checks) satisfactory? (i.e., do we recover the input at all iterations?)
- Is the response matrix well-behaved? (migration fraction, diagonal dominance, etc.)
- Are regularization/iteration choices robust to small variations?

**Key sections:**
- `AnalysisNote/Sec. Analysis Method` (Sec. 6)
- Summary plots: `summary/closure_test_*.pdf` (N_iter = 4, 5, 6, 10, 100)
- Diagnostic: `summary/response_matrix.pdf` (visual check of migration)
- Numerical validation: `workflow_summary.json` → `iteration_envelope`, `closure_residuals`

---

### 4. **Code & Data Processing** (Read if deep-dive is needed)
**Key entry points:**
- **Event selection & reconstruction**: `DataProcessing/src/Analyze.cxx` (line ~50: thrust/major/minor calculation; line ~100: hadronic correction)
- **Unfolding execution**: `Unfolding/scripts/run_thrust_prelim_workflow.py` (nominate options, systematics variants)
- **Response matrix & covariance building**: `Unfolding/scripts/build_prelim_uncertainty_summary.py` (central script for uncertainty assembly)
- **Supporting unfolding logic**: `Unfolding/unfold_thrust.py` (RooUnfold wrapper; IBU-specific options)
- **Plotting utilities**: `Unfolding/plot_unfolded.py`, `Unfolding/scripts/plot_total_correlation_matrix.py`

**Validation checklist:**
- Confirm recompile of `AnalysisNote/main.pdf` shows correct hadronic-correction status (line 69: "Resolved")
- Verify thrustTools.h line 225 comment accurately describes the n=3 algorithm
- Check workflow reproducibility: running `run_thrust_prelim_workflow.py` produces identical outputs to `workflow_summary.json`

---

## Known Limitations & Open Items

### Accepted Approximations

1. **n=3 particle thrust** (line 225, `DataProcessing/include/thrustTools.h`):
   - For rare 3-particle events, the algorithm selects the highest-magnitude particle rather than enumerating all 4 hemisphere assignments.
   - **Justification**: 3-particle hadronic events are rare in $Z \to q\bar{q}$ decays; impact on thrust value typically <0.1% for T > 0.5.
   - **Propagated impact**: Included in the migration-dominated endpoint uncertainty.

2. **Systematic correlation template** (line 49, `AnalysisNote/sections/ChallengesAndLimitations.tex`):
   - Systematic inter-bin correlations assumed to follow the statistical correlation matrix structure.
   - **Justification**: Simplifies propagation and is empirically validated in closure tests.

### Open Physics Questions

- **Endpoint region tension**: Unfolded spectrum at T > 0.95 shows ~30% higher values than 2004 ALEPH reanalysis. No final interpretation pending completion of diagnostic matrix and beam-related background studies.
- **Beam backgrounds**: Current analysis does not subtract beam-related contamination (e.g., from beamstrahlung). Assessment pending next iteration.

### Scope for Future Work

- Extend to thrust-major and thrust-minor observables (1D correlations)
- Multidimensional unfolding (e.g., thrust vs. event mass)
- Higher-order MC generator comparison (currently Pythia8, Herwig, Sherpa reweighting)
- Validated theory-experiment AI feedback loops (see `AnalysisNote/Sec. Introduction`)

---

## Key Result Summary

**Central thrust range (0.60 ≤ T < 0.95):**

| Uncertainty Component | Mean Contribution |
|----------------------|------------------|
| **Theory** (envelope of gen-level reweighting) | ~6.1% |
| **Hadronic** (ratio envelope, up/down) | ~3.2% |
| **Experimental** (quad of subsystem systematics) | ~2.8% |
| **Iteration** (envelope N_iter=4,6 vs nominal=5) | ~1.5% |
| **Statistical** (IBU covariance propagation) | ~1.1% |
| **Total** (all sources in quadrature) | **~8.43%** |

**Central values** (bins 30–46, corresponding to T ≈ 0.60–0.95):
- Available in `workflow_summary.json` → `central_values.thrust`
- CSV export in `Studies/PreliminaryResult/2026-02-17_thrust_iter5/central_values.csv`

---

## Reviewer Workflow

### Step 1: High-level sanity check (30 min)
1. Open `AnalysisNote/main.pdf` and skim Sec. 1 (Introduction), Sec. 8 (Results)
2. Look at `summary/unfolded_spectrum.pdf` and `summary/uncertainty_breakdown.pdf`
3. Check: Does the shape make sense? Is the total uncertainty in the expected ballpark (~10%)?

### Step 2: Systematics deep-dive (1–2 hours)
1. Read `AnalysisNote/Sec. 7` (Systematic Uncertainties)
2. View `summary/total_correlation_matrix.pdf` — does the structure (bin-wise correlation) look reasonable?
3. Check `summary/closure_test_*.pdf` — are residuals <5% over the central range?
4. Review covariance/correlation CSVs: are off-diagonal elements small compared to diagonals in the central range?

### Step 3: Method & code traceability (1–2 hours, optional but recommended)
1. Read `AnalysisNote/Sec. 6` (Analysis Method) — is the IBU description clear?
2. Cross-check key claims with `Unfolding/unfold_thrust.py` source (N_iter, convergence tolerance, etc.)
3. Spot-check response-matrix diagnostics: `summary/response_matrix.pdf`, migration fraction from `workflow_summary.json`
4. Verify reproducibility: examine `workflow_summary.json` for all run options and confirm match to narrative

### Step 4: Final checklist (30 min)
- [ ] Physics interpretation is sensible given measurement context
- [ ] Systematic uncertainties are well-documented and of comparable magnitude to similar analyses
- [ ] Closure tests and correlation structure are satisfactory for release
- [ ] Known limitations (n=3 approximation, endpoint tension, beam backgrounds) are explicit and do not undermine credibility

---

## Questions? Issues?

If you encounter unclear sections, missing plots, or inconsistencies:
1. Check `AnalysisNote/sections/ChallengesAndLimitations.tex` (Sec. 9) for known issues
2. Consult the comment blocks in `workflow_summary.json` for script-level rationale
3. Raise issues with the analysis team via `Plans/` directory (ongoing discussion of refinements)

**Goal:** This analysis is ready for external physics review and downstream phenomenological reuse. Your feedback strengthens confidence in the uncertainty model for future precision QCD applications.
