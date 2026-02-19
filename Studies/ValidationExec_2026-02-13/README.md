# ValidationExec_2026-02-13

Execution bundle for thrust IBU validation and systematics.

## Core outputs
- Nominal unfolding:
  - `unfolded_nominal_exec.root`
  - `unfolded_nominal_iter7_cov.root`
- Closure unfolding:
  - `unfolded_closure_exec_closure.root`
- Closure (hadronic correction disabled):
  - `unfolded_closure_nocorr_exec_closure.root`

## Iteration scan
- Directory: `iteration_scan/`
- Key summary: `iteration_scan/iteration_scan_summary.json`
- Recommended iterations: `7`
- Distribution and response plots:
  - `iteration_scan/dist_inputs_data_mcreco_mcgen.pdf`
  - `iteration_scan/dist_unfolded_selected_iterations.pdf`
  - `iteration_scan/dist_refolded_vs_data_selected_iterations.pdf`
  - `iteration_scan/dist_response_counts_matrix.pdf`

## Matrix exports
- Directory: `matrices_nominal_iter7/`
- Matrix figures:
  - `matrix_response_counts.pdf`
  - `matrix_response_probability.pdf`
  - `matrix_unfold_covariance.pdf`
  - `matrix_unfold_correlation.pdf`
- Matrix CSV artifacts:
  - `matrix_unfold_covariance.csv`
  - `matrix_unfold_correlation.csv`
  - `matrix_unfold_covariance_binning.csv`
  - `matrix_unfold_correlation_binning.csv`

## Particle-category (`pwflag`) kinematics
- Directory: `pwflag_kinematics/`
- Includes:
  - event-level observables used in selection (`ntrk`, `ntrkPlusNeu`, `eCh`, `cosThetaSph`, etc.)
  - detector-level thrust inputs (`thrust`, `logtau`)
  - full per-category sets:
    - `pwflag{0..5}_{cosTheta,phi,pt,pmag,d0,z0,ntpc,energy,mass}.pdf`

## Systematics
1. Subset checks:
- Directory: `systematics_subset/`

2. Full strict 1994 campaign:
- Directory: `systematics_full_1994/`
- Variations present:
  - `nominal`
  - `ntpc7`
  - `pt04`
  - `ech10`
  - `no_neutrals`
  - `with_met`
  - `nes_up`
  - `nes_down`
  - `ner`
- Summary plots:
  - `systematics_full_1994/unfolded_all_variations_ratio_nominal.pdf`
  - `systematics_full_1994/unfolded_all_variations_fractional_diff.pdf`
