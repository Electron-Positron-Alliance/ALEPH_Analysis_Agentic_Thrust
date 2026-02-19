# Thrust Preliminary Result Workflow

This workflow runs the thrust-only preliminary measurement package with:
- Nominal IBU unfolding (`N_iter = 5`)
- Iteration systematic (`N_iter = 4, 6`)
- Experimental systematics (track/event + neutral-response + `no_neutrals` cross-check)
- Theory systematics from event-level reweighting arrays applied to `tgenBefore` and mapped to `tgen`
- Post-unfolding hadronic-event selection correction (`tgenBefore / tgen`)

## 1) Run the full workflow

```bash
python3 Unfolding/scripts/run_thrust_prelim_workflow.py \
  --theory-weights-dir /path/to/theory_reweighting/training-<tag>
```

Key options:
- `--outdir <path>`: explicit output directory
- `--nominal-iter 5 --iter-down 4 --iter-up 6`
- `--theory-weights-dir <path>`: required unless `--skip-theory` is set
- `--skip-plots` to skip per-run PDF generation

## 2) Build uncertainty summary and final plots

```bash
python3 Unfolding/scripts/build_prelim_uncertainty_summary.py \
  --base-dir Studies/PreliminaryResult/<run_dir> \
  --aleph-csv /path/to/HEPData-ins636645-v1-Table_54.csv \
  --central-range-min 0.60 \
  --central-range-max 0.95
```

Outputs under `<run_dir>/summary/`:
- `uncertainty_breakdown.json`
- `cov_stat.csv`, `cov_iter.csv`, `cov_exp.csv`, `cov_theory.csv`, `cov_total.csv`
- `corr_total.csv`
- `binning.csv`
- `uncertainty_components_statistical.pdf`
- `uncertainty_components_unfolding.pdf`
- `uncertainty_components_experimental.pdf`
- `uncertainty_components_theory.pdf`
- `final_result_uncertainty_breakdown.pdf`

Notes:
- Non-statistical component plots show signed shifts relative to nominal.
- Component-plot y-axis is display-clipped to `[-50%, +50%]` for readability.
- `uncertainty_breakdown.json` now contains both full-range and central-range uncertainty summaries.

## 3) Validate summary outputs

```bash
python3 Unfolding/scripts/check_prelim_summary_outputs.py \
  --base-dir Studies/PreliminaryResult/<run_dir>
```

## Compatibility wrappers

Legacy entry points are preserved as thin wrappers:
- `Studies/PreliminaryResult/scripts/run_thrust_prelim_workflow.py`
- `Studies/PreliminaryResult/scripts/build_prelim_uncertainty_summary.py`
