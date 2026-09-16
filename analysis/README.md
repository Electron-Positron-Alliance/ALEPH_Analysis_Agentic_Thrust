# Reproduction code

Analysis code for the thrust measurement, restored from `d075711` (the commit
that split this into a note-only repo). All files are byte-identical to the
live repo at `ALEPH/ALEPH_Analysis_Agentic_Thrust`.

## Stages

| stage | entry point | produces |
|---|---|---|
| 1. ntuples | `DataProcessing/runAnalyze.py` (+ `*.h`) | the 3 derived ROOT files |
| 2. validation plots | `DataProcessing/plotting/plot.py` | 57 figures (`pwflagN_*`, `ntrk`, `ntrkPlusNeu`, `eCh`, `cosThetaSph`) |
| 3. unfolding + result | `Unfolding/unfold_thrust.py`, `Unfolding/scripts/*.py` | 7 figures, all tables and metrics |
| 3b. component matrices | `Unfolding/scripts/plot_component_matrices.py` | `corr_matrices_per_source`, `cov_matrices_per_source`, `cov_matrix_total` |
| 4. cross-checks | `Studies/*/scripts/*.py` | 17 figures |

Figure names in stage 2 are built as `f"pwflag{pw}_{qty}"` (`plotting/plot.py:57`),
and `phi_pw{pw}_all.pdf` at `Studies/.../phi_spectrum_investigation.py:186`, so
grepping for those literal filenames finds nothing.

Appendix A of the paper lists only the four stage-3 scripts. That reproduces the
final spectrum but none of the other 74 figures.

### Stage 1 needs two ROOT binaries, not just Python

`runAnalyze.py` is a launcher. It shells out to:

- **`./Analyze.exe`** — the analyzer, built from `Analyze.cxx` by the `Makefile`.
  Run `make` in `DataProcessing/` first; the binary is gitignored, not tracked.
- **`hadd`** — ROOT's merge tool, used at `runAnalyze.py:233` whenever
  `--ndivs > 1` to combine the per-division outputs.

Neither is on `PATH` by default, which is why `env.sh` exports `$ROOTSYS/bin`.

**Do not combine `-n` with `--ndivs > 1`.** `Analyze.cxx:281-285` lets `-n`
override the division range, so every division reads events `0..n` and the
merged file contains the same events repeated once per division. Verified:
`--ndivs 2 -n 20000` yields 40,000 entries, which is 20,000 events counted
twice. Use `-n` only with the default `--ndivs 1`; for a partitioned run, drop
`-n` and let each division take its own slice.

### Why each file is here

Every file is either an entry point that produces something the paper uses, or is
imported by one. Two are kept prospectively rather than for the current paper:

- `Studies/.../thrust_resolution_1d.py` produces `thrust_resolution_1d.pdf`, which
  is **not** shipped -- the paper's Fig. 11 includes `thrust_resolution_2d.pdf`
  under the label `fig:thrust_resolution_1d`. Referee 2 asks about the resolution
  distribution peaking above zero, which is the 1D projection, so this is the
  producer for the figure that comment needs.
- `Studies/.../refolding_pull_panel.py` produces the refolded-vs-data pull panel.
  Appendix A cites refolding diagnostics for the `N_iter=5` choice but ships no
  such figure.

`DataProcessing/plotting/styles/` is imported as a package
(`from styles.canvas_utils import draw_histogram_canvas` in `plot.py`), so both
files in it are required.

## Inputs

Verify all of them with `python verify_inputs.py`.

To check that a rerun reproduces a stored result rather than asserting it:

```
python compare_runs.py <reference>/nominal/unfolded_nominal_iter5.root \
                       <rerun>/nominal/unfolded_nominal_iter5.root
```

Reports the largest relative bin difference per object and exits non-zero if
any exceeds `--tol` (default 0). Against the published nominal output all 13
objects match at zero relative difference.

| input | location |
|---|---|
| raw data (8.4 G) | `ALEPH/LEP1Data1994_recons_aftercut-MERGED.root` |
| raw MC (28 G) | `ALEPH/alephMCRecoAfterCutPaths_1994.root` |
| derived ntuples | `ALEPH_Analysis_Agentic_Thrust/DataProcessing/temp/` |
| ALEPH 2004 reference | `ALEPH/HEPData-ins636645-v1-Table_54.csv` |
| prior IBU | `unfold-ee-logtau/Results/ibu_results.npz` |
| prior OmniFold | `unfold-ee-logtau/Results/unfold_thrust_ee_ZPole_ALEPH.h5` |
| theory weights | `unfold-ee-logtau/arxivPaperResults2025/theory_reweighting/training-bf3b5fc3` |

The theory-weights tag is the one the published run used; Appendix A writes only
`training-<tag>`. The derived ntuples let stage 1 be skipped, which avoids
re-reading 36 G.

## Environment

```
source env.sh
python verify_inputs.py
```

Python and all pip dependencies are uv-managed. ROOT is not a pip package: it
comes from an existing install, and `env.sh` wires its PyROOT into the uv venv
via `PYTHONPATH`. All four stages run under this one environment.

`ROOTSYS` defaults to the conda `py312` install, which is the ROOT that works
here. `env.sh` reads the Python version ROOT was built against from
`root-config` and pins uv to match; a mismatch fails with
`ImportError: symbol not found in flat namespace '__Py_HashPointer'`.

`ROOUNFOLD_LIB` defaults to `~/code/RooUnfold/build/libRooUnfold.dylib`, which
links `libCore.6.36` and so matches that ROOT. Both variables are overridable.

### Why not ROOT 6.38

`~/code/root` (6.38.00) does not work on this machine. Its cling modulemap
references libc++ headers that AppleClang 21 reorganised:

```
etc/cling/std_darwin.modulemap:73: error: header '__type_traits/add_lvalue_reference.h' not found
```

Dictionary generation for templated classes then fails, so RooUnfold loads but
cannot be used:

```
TypeError: cannot instantiate incomplete class 'RooUnfoldBayesT<TH1,TH2>'
```

Its `libXMLParser.so` also has a dangling `/opt/local/lib/libxml2.2.dylib`
(MacPorts) dependency. RooUnfold *was* rebuilt against 6.38 and links it
correctly (`build-root638/`), which confirms the ROOT install is the problem
rather than RooUnfold. Fixing it needs ROOT 6.38 rebuilt against the current
toolchain; the 6.36.06 install is fully functional in the meantime.

## Running on open data alone

The theory variations and the ISR correction need samples that are not in the
open dataset, so both stages must be skipped explicitly:

```
source env.sh
python Unfolding/scripts/run_thrust_prelim_workflow.py \
  --config <run>/unfold_config.json --outdir <run> \
  --python "$(which python)" --conda-env "" \
  --nominal-iter 5 --iter-down 4 --iter-up 6 \
  --skip-theory --skip-isr
python Unfolding/scripts/build_prelim_uncertainty_summary.py \
  --base-dir <run> --outdir <run>/summary \
  --aleph-csv <ALEPH>/HEPData-ins636645-v1-Table_54.csv \
  --skip-theory --include-of-ibu-comparison \
  --legacy-results-dir <unfold-ee-logtau>/Results
```

`--conda-env ""` is required when `--python` already points at a working
interpreter; the default is `py312`, which otherwise wraps every step in
`conda run`.

**A `--skip-theory` summary is not comparable to a full run.** Theory dominates
the off-diagonal correlation structure, so with it zeroed the totals shift
substantially -- `corr_total_max_abs_offdiag` reads 0.975 instead of 0.887. The
output JSON records this: `diagnostics.theory_uncertainty_included` is `false`,
`theory_definition` is empty, and `theory_uncertainty_note` says so. Check those
before quoting any number out of a summary.

## Not reproducible from open data alone

- **theory uncertainty** and **ISR correction** — need the PYTHIA 8.3 / Herwig 7.3 /
  Sherpa 2.2 `tgenBefore` samples, which are not in the open dataset.
