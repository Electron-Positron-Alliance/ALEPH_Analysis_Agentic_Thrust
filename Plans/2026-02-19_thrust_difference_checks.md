# Thrust Difference Checks: Current Result vs Prior OF/IBU

## Objective
Identify and rank the causes of differences between:
- current thrust result in this repository (IBU nominal, `N_iter=5`);
- prior IBU result in `unfold-ee-logtau/Results/ibu_results.npz`;
- prior OmniFold result reconstructed from `unfold-ee-logtau/Results/unfold_thrust_ee_ZPole_ALEPH.h5`;
- ALEPH 2004 published result.

The goal is causal attribution, not only visual agreement.

## Current Observations (from existing outputs)
Source: `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/of_ibu_comparison_metrics.json`

- `chi2/ndf`:
  - ALEPH vs current: `0.361`
  - OF vs current: `0.663`
  - IBU vs current: `0.421`
- Highest thrust-bin ratio (`curve/current`, `0.99<T<1.00`):
  - ALEPH/current: `1.301 +/- 0.275`
  - OF/current: `1.129 +/- 0.246`
  - IBU/current: `1.091 +/- 0.497`
- Largest max absolute deviation from unity appears for OF/current (`~0.505`), indicating localized shape tension despite globally acceptable `chi2/ndf`.

## Investigation Strategy
Use staged checks that isolate one effect at a time:
1. Align basis and conventions (binning, normalization, ratio definition).
2. Separate central-value differences from uncertainty-model differences.
3. Compare event/sample synchronization and response regularization.
4. Quantify endpoint sensitivity explicitly.

## Hypotheses and Checks

### H1: Binning/rebinning basis drives part of the discrepancy
Check:
- Run current pipeline directly in ALEPH 42-bin mode (native, not post hoc rebin).
- Compare current(42) vs current(50 rebinned to 42), OF, and prior IBU.

Implementation notes:
- Add/use config with ALEPH edges for unfolding and summary.
- Produce overlay plot and bin-by-bin ratio CSV.

Evidence signature:
- If discrepancy reduces materially when current is native-42, binning mismatch is a major contributor.

---

### H2: Normalization convention mismatch
Check:
- Verify all curves are compared as `1/sigma dsigma/dT` after identical normalization stage.
- Reproduce comparison with alternate normalization checkpoints:
  - before hadronic correction,
  - after hadronic correction,
  - after final normalization.

Evidence signature:
- Uniform or slowly varying ratio shifts across bins indicate normalization-stage mismatch.

---

### H3: Hadronic correction treatment differs between analyses
Check:
- Toggle hadronic correction in current workflow (on/off) for comparison-only studies.
- Compare impact on central values and endpoint bins.

Evidence signature:
- Significant shift in tail and/or global drift after toggling indicates hadronic-correction handling is a key source.

---

### H4: Uncertainty recipe differences dominate perceived disagreement
Check:
- Hold central values fixed and vary uncertainty construction:
  - current nominal uncertainty model;
  - legacy OF/IBU-style recipe;
  - reduced variants (stat-only, stat+exp).
- Recompute `chi2/ndf` and pull summaries.

Evidence signature:
- Large movement in compatibility metrics without central-value movement indicates uncertainty model is dominant.

---

### H5: Theory-envelope masking in OF reconstruction changes shape/uncertainty
Check:
- Scan `mc_bin_quality` thresholds used in OF reconstruction:
  - `rel_mc_unc_max` and `pull_abs_max`.
- Recompute OF comparison metrics per threshold point.

Evidence signature:
- Strong threshold dependence indicates theory-mask policy is a key source.

---

### H6: Event/sample synchronization mismatch between stacks
Check:
- Produce checkpoint yields for data and MC at common stages in both workflows:
  - selected data entries;
  - reco-MC entries;
  - gen-MC entries;
  - matched event counts.
- Compare branch-by-branch with explicit logs.

Evidence signature:
- Mismatched yields before unfolding indicate upstream selection/data preparation causes.

---

### H7: Regularization/iteration dependence
Check:
- Compare current IBU at `N_iter = 4,5,6,10` to prior IBU/OF with fixed binning/normalization.
- Track distance-to-reference vs iteration.

Evidence signature:
- Monotonic distance trend with iteration implies regularization choice contributes to discrepancy.

---

### H8: Endpoint instability dominates differences
Check:
- Recompute metrics excluding highest-thrust bins (e.g. `T>=0.98`).
- Repeat with merged tail bins.

Evidence signature:
- Major improvement when excluding/merging tail bins indicates endpoint-driven discrepancy.

## Priority Order
1. H1 + H2 (basis and normalization alignment).
2. H3 (hadronic correction toggle study).
3. H6 (event/sample synchronization checks).
4. H7 + H8 (regularization and endpoint sensitivity).
5. H4 + H5 (uncertainty/modeling policy scans).

## Required Outputs
- `Studies/PreliminaryResult/<run>/summary/difference_diagnosis_summary.json`
- `Studies/PreliminaryResult/<run>/summary/difference_check_matrix.csv`
- Overlay plots for each hypothesis family.
- Short conclusion note with ranked causes and confidence.

## Acceptance Criteria for Root-Cause Claim
Do not claim a root cause unless:
1. at least one hypothesis test shows a reproducible, directional effect;
2. effect size is quantified and larger than competing alternatives;
3. result is stable under a small set of robustness variations.

