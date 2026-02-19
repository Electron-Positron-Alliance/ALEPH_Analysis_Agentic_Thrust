# Figure Checklist (Thrust, Iterative Bayesian Unfolding)

## Primary workflow bundle
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/`

## Section 5 (Analysis method)
- Response matrices:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrices_nominal_iter5/matrix_response_counts.pdf`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrices_nominal_iter5/matrix_response_probability.pdf`
- Covariance/correlation matrices:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrices_nominal_iter5/matrix_unfold_covariance.pdf`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrices_nominal_iter5/matrix_unfold_correlation.pdf`

## Section 6 (Systematic uncertainties)
- Statistical component:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_statistical.pdf`
- Unfolding components:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_unfolding.pdf`
- Experimental components:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_experimental.pdf`
- Theory components:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_theory.pdf`

## Section 7 (Results)
- Final unfolded result with ALEPH ratio panel:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/final_result_uncertainty_breakdown.pdf`

## Additional release artifacts
- Covariance/correlation CSVs and binning:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/cov_stat.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/cov_iter.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/cov_exp.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/cov_theory.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/cov_total.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/corr_total.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/binning.csv`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_breakdown.json`
- Output integrity check:
  - `python3 Unfolding/scripts/check_prelim_summary_outputs.py --base-dir Studies/PreliminaryResult/2026-02-17_thrust_iter5`
