# ALEPH Agentic Event Shape Analysis

Proof-of-concept AI-agentic measurement of event-shape observables (thrust) using archived ALEPH $e^+e^-$ data at $\sqrt{s} = 91.2$ GeV. The full analysis chain — particle selection, hadronic event filtering, detector-level response construction, iterative Bayesian unfolding (IBU), and systematic uncertainty propagation — is driven by an AI agent under physicist supervision. Results are documented in `AnalysisNote/`.

---

## Table of Contents

1. [Physics context](#physics-context)
2. [Data samples required](#data-samples-required)
3. [Software requirements](#software-requirements)
4. [Repository structure](#repository-structure)
5. [Full analysis chain](#full-analysis-chain)
   - [Step 1 — Build the C++ analysis code](#step-1--build-the-c-analysis-code)
   - [Step 2 — Produce derived ROOT files](#step-2--produce-derived-root-files)
   - [Step 3 — Run the unfolding workflow](#step-3--run-the-unfolding-workflow)
   - [Step 4 — Build the uncertainty summary](#step-4--build-the-uncertainty-summary)
   - [Step 5 — Produce cross-check plots](#step-5--produce-cross-check-plots)
6. [Configuration reference](#configuration-reference)
7. [Output structure](#output-structure)
8. [Analysis note](#analysis-note)

---

## Physics context

Thrust $T$ is defined as

$$T = \max_{\hat{n}} \frac{\sum_i |\vec{p}_i \cdot \hat{n}|}{\sum_i |\vec{p}_i|}$$

and is measured in 50 uniform bins over $0.50 \le T < 1.0$ ($\Delta T = 0.01$). The dijet limit $T \to 1$ probes soft-gluon resummation; the three-jet region $T \lesssim 0.85$ is sensitive to $\alpha_s$. The archived ALEPH 1994 dataset provides a clean $e^+e^-$ initial state with well-understood detector response, making it an ideal testbed for AI-driven precision measurements.

---

## Data samples required

All input files are ROOT TTrees. The analysis requires **three independent sample types** plus **variation files** for systematic uncertainties.

### Primary inputs

| Sample | File naming pattern | Tree(s) | Description |
|--------|--------------------|---------|----|
| ALEPH archived data | `LEP1Data1994_recons_aftercut-MERGED_thrust_<var>_t.root` | `t` | Detector-level reconstructed hadronic events, 1994 run |
| ALEPH archived MC (reco) | `alephMCRecoAfterCutPaths_1994_thrust_<var>_t.root` | `t` | JETSET 7.4 detector simulation, same format as data |
| ALEPH archived MC (gen) | `alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root` | `tgen`, `tgenBefore` | Generator-level particles before and after hadronic event selection; used to build the response matrix and hadronic correction $C_\mathrm{had}(j) = N_\mathrm{genBefore}(j)/N_\mathrm{gen}(j)$ |

The archived ALEPH data and MC are obtained from the ALEPH open-data release and CERN analysis preservation infrastructure. Contact the analysis team for access paths on CERN/local storage.

### Systematic variation files

The `<var>` token in the naming pattern above is replaced by the variation name. All variation files are produced automatically by `DataProcessing/runAnalyze.py` (Step 2 below).

| Variation tag | Type | Description |
|---------------|------|-------------|
| `nominal` | baseline | Standard selection (see `runAnalyze.py` `DEFAULT_SELECTION`) |
| `ntpc7` | experimental | Require $N_\mathrm{TPC} \ge 7$ (tighter track quality) |
| `pt04` | experimental | Require charged $p_T \ge 0.4$ GeV |
| `ech10` | experimental | Require total charged energy $E_\mathrm{ch} \ge 10$ GeV |
| `with_met` | experimental | Include missing-momentum term in thrust sum |
| `nes_up` | neutral response | Scale all neutral particle energies up by 5% |
| `nes_down` | neutral response | Scale all neutral particle energies down by 5% |
| `ner` | neutral response | Random neutral particle efficiency drop (throw-based) |
| `no_neutrals` | cross-check | Remove all neutral objects from thrust inputs |

### Theory reweighting arrays

Generator reweighting weights are stored as NumPy `.npy` files, one per MC generator. These must be placed in a single directory and passed via `--theory-weights-dir`:

| File | Generator |
|------|-----------|
| `Reweight_Step2_Ensemble_Pythia8.npy` | Pythia 8 |
| `Reweight_Step2_Ensemble_Herwig.npy` | Herwig 7.3 |
| `Reweight_Step2_Ensemble_Sherpa.npy` | Sherpa |

---

## Software requirements

| Package | Version tested | Notes |
|---------|---------------|-------|
| ROOT | 6.36 | Must include `root-config` on `PATH` |
| RooUnfold | any recent | Must be loadable as `libRooUnfold` |
| Python | 3.10+ | Conda environment `py312` used by default |
| numpy | any | Required for uncertainty assembly |
| pandas | any | Required for uncertainty assembly and plots |
| matplotlib | any | Required for uncertainty plots |
| C++ compiler | g++ with C++17 | For `DataProcessing` binary |

Set up a conda environment with the required Python packages:

```bash
conda create -n py312 python=3.12
conda activate py312
pip install numpy pandas matplotlib
```

---

## Repository structure

```
ALEPH_Agentic_Event_Shape_Analysis/
├── DataProcessing/
│   ├── src/Analyze.cxx          # C++/RDataFrame event-shape analysis
│   ├── include/                 # thrust, sphericity, analysis utilities
│   ├── runAnalyze.py            # Python wrapper: runs all selection variations
│   ├── plotting/plot.py         # particle-level data/MC validation plots
│   └── Makefile
├── Unfolding/
│   ├── unfold_thrust.py         # RooUnfold IBU unfolding (single job)
│   ├── unfold_config.json       # paths + binning config (edit before running)
│   ├── unfold_config_template.json
│   ├── plot_unfolded.py         # single-job result plot
│   └── scripts/
│       ├── run_thrust_prelim_workflow.py       # orchestrates all unfolding jobs
│       ├── build_prelim_uncertainty_summary.py # assembles covariances + final result
│       ├── check_prelim_summary_outputs.py     # validates summary outputs
│       └── plot_total_correlation_matrix.py    # correlation matrix visualization
├── Studies/
│   ├── PreliminaryResult/        # dated result snapshots
│   ├── Phase2_Checks_2026-03-03/ # cross-check scripts and plots
│   └── UnfoldingIterationScan/   # regularization scan
├── AnalysisNote/                 # LaTeX analysis note (main.tex)
└── Plans/                        # agent planning documents
```

---

## Full analysis chain

The chain has five sequential steps. Steps 1–2 produce the derived ROOT files; Steps 3–5 perform unfolding and assemble the result.

### Step 1 — Build the C++ analysis code

```bash
cd DataProcessing
make
# produces bin/Analyze.exe
```

### Step 2 — Produce derived ROOT files

Run the analysis over each input file (data, MC reco, MC gen) to produce derived ROOT files containing thrust and other event-shape observables.

**Nominal data:**
```bash
python DataProcessing/runAnalyze.py \
    -i /path/to/LEP1Data1994_recons_aftercut.root \
    --outDir DataProcessing/temp/ \
    -j 8
```

**Nominal MC (reco + gen):**
```bash
python DataProcessing/runAnalyze.py \
    -i /path/to/alephMCRecoAfterCutPaths_1994.root \
    --outDir DataProcessing/temp/ \
    -j 8
```

A single invocation of `runAnalyze.py` automatically runs **all** selection variations, producing one output ROOT file per variation. Generator-level trees (`tgen`, `tgenBefore`) are produced only for `no_event_sel`.

**Key output files expected by the unfolding workflow** (paths configured in `Unfolding/unfold_config.json`):

```
DataProcessing/temp/
  LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root       # data nominal
  LEP1Data1994_recons_aftercut-MERGED_thrust_ntpc7_t.root         # data ntpc7 variation
  ...                                                              # one file per variation
  alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root             # MC reco nominal
  alephMCRecoAfterCutPaths_1994_thrust_ntpc7_t.root               # MC reco ntpc7
  ...                                                              # one file per variation
  alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root     # MC gen (response + hadronic correction)
```

> **Note:** The unfolding workflow derives variation file paths from the nominal path by replacing `_nominal_` with `_<variation>_`. The naming convention from `runAnalyze.py` must be preserved.

### Step 3 — Run the unfolding workflow

Edit `Unfolding/unfold_config.json` to point to your derived ROOT files:

```json
{
  "data_file":    "../DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root",
  "reco_mc_file": "../DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root",
  "gen_mc_file":  "../DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root",
  "bins": 50, "xmin": 0.5, "xmax": 1.0, "iterations": 5
}
```

Then run the workflow orchestrator from the repo root:

```bash
python Unfolding/scripts/run_thrust_prelim_workflow.py \
    --config Unfolding/unfold_config.json \
    --theory-weights-dir /path/to/theory_weights/ \
    --conda-env py312
```

This executes **14 unfolding jobs** (1 nominal + 2 iteration + 8 experimental + 3 theory) and writes outputs to a dated directory:

```
Studies/PreliminaryResult/<YYYY-MM-DD>_thrust_iter5/
  nominal/unfolded_nominal_iter5.root
  iteration/unfolded_iter{4,6}.root
  experimental/unfolded_{ntpc7,pt04,ech10,with_met,nes_up,nes_down,ner,no_neutrals}.root
  theory/unfolded_theory_{pythia8,herwig,sherpa}.root
  workflow_summary.json
```

To skip individual groups during development:
```bash
python Unfolding/scripts/run_thrust_prelim_workflow.py \
    --config Unfolding/unfold_config.json \
    --skip-theory --skip-plots
```

### Step 4 — Build the uncertainty summary

Assembles per-bin fractional uncertainties, full covariance matrices, and final result plots:

```bash
python Unfolding/scripts/build_prelim_uncertainty_summary.py \
    --base_dir Studies/PreliminaryResult/<date>_thrust_iter5/
```

Outputs written to `<base_dir>/summary/`:

| File | Description |
|------|-------------|
| `cov_{stat,iter,exp,theory,hadronic,total}.csv` | 50×50 covariance matrices in differential cross-section basis |
| `corr_total.csv` | Total bin-to-bin correlation matrix |
| `cov_total_fitwindow.csv` | Covariance restricted to $\alpha_s$ fit window ($0.505 \le T < 1.00$, 45 bins) |
| `binning.csv` | Bin edges, centers, nominal differential cross-section per bin |
| `fit_mask.csv` | Boolean mask identifying fit-window bins |
| `uncertainty_components_*.pdf` | Per-component fractional uncertainty plots |
| `final_result_uncertainty_breakdown.pdf` | Final result vs ALEPH 2004 with uncertainty band |

Validate all outputs:
```bash
python Unfolding/scripts/check_prelim_summary_outputs.py \
    --summary-dir Studies/PreliminaryResult/<date>_thrust_iter5/summary/
```

### Step 5 — Produce cross-check plots

Run from the repo root. Each script reads from the `Studies/PreliminaryResult/` directory.

```bash
# Per-bin uncertainty breakdown (stat / exp / theory panels + grouped summary)
python Studies/Phase2_Checks_2026-03-03/scripts/per_bin_uncertainty_plot.py \
    --result-dir Studies/PreliminaryResult/<date>_thrust_iter5/ \
    --outdir     Studies/Phase2_Checks_2026-03-03/plots/uncertainty_breakdown/

# Charged-only vs energy-flow cross-check
python Studies/Phase2_Checks_2026-03-03/scripts/charged_only_vs_energy_flow.py

# phi-spectrum modulation study (HCAL 24-module boundaries)
python Studies/Phase2_Checks_2026-03-03/scripts/phi_spectrum_investigation.py

# pwflag=5 neutral hadron cos(theta) cleaning cut study
python Studies/Phase2_Checks_2026-03-03/scripts/pwflag5_costheta_no_cut.py

# Refolding pull panel (IBU closure diagnostic)
python Studies/Phase2_Checks_2026-03-03/scripts/refolding_pull_panel.py

# Thrust resolution vs bin width
python Studies/Phase2_Checks_2026-03-03/scripts/thrust_resolution_study.py
```

Data/MC validation plots (per-`pwflag` kinematic distributions):
```bash
python DataProcessing/plotting/plot.py \
    --data    DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
    --mc-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root
```

---

## Configuration reference

`Unfolding/unfold_config.json` — primary config read by `unfold_thrust.py` and `run_thrust_prelim_workflow.py`:

| Key | Type | Description |
|-----|------|-------------|
| `data_file` | path | Nominal data ROOT file |
| `reco_mc_file` | path | Nominal MC reco ROOT file |
| `gen_mc_file` | path | Generator-level MC ROOT file |
| `data_tree`, `reco_tree`, `gen_tree` | string | TTree names (`t`, `t`, `tgen`) |
| `data_branch`, `reco_branch`, `gen_branch` | string | Observable branch name (`Thrust`) |
| `bins`, `xmin`, `xmax` | int/float | Binning: 50 bins over $[0.5, 1.0)$ |
| `iterations` | int | IBU iteration count (nominal = 5) |
| `calculate_covariance` | bool | Set `true` for nominal run only |
| `out_root` | path | Output ROOT file |

Per-job overrides can be passed with `--set key=value` to `unfold_thrust.py`, or are injected automatically by the workflow orchestrator.

---

## Output structure

The canonical preliminary result is stored in:

```
Studies/PreliminaryResult/2026-02-17_thrust_iter5/
```

For a new result, the workflow creates a dated directory automatically. For downstream $\alpha_s$ theory fits, use **`summary/cov_total_fitwindow.csv`** (45-bin fit-window covariance) rather than the full 50-bin covariance.

---

## Analysis note

The full analysis note is compiled with:

```bash
cd AnalysisNote
latexmk -pdf main.tex
```

It documents the measurement method, detector simulation validation, systematic uncertainty model, and final results with comparison to the published ALEPH 2004 result (HEPData ins:636645, Table 54).
