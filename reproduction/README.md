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
| 4. cross-checks | `Studies/*/scripts/*.py` | 17 figures |

Figure names in stage 2 are built as `f"pwflag{pw}_{qty}"` (`plotting/plot.py:57`),
and `phi_pw{pw}_all.pdf` at `Studies/.../phi_spectrum_investigation.py:186`, so
grepping for those literal filenames finds nothing.

Appendix A of the paper lists only the four stage-3 scripts. That reproduces the
final spectrum but none of the other 74 figures.

## Inputs

Verify all of them with `python verify_inputs.py`.

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

## Not reproducible from open data alone

- **theory uncertainty** and **ISR correction** — need the PYTHIA 8.3 / Herwig 7.3 /
  Sherpa 2.2 `tgenBefore` samples, which are not in the open dataset.
- **Figs. 21–23** (`corr_matrices_per_source`, `cov_matrices_per_source`,
  `cov_matrix_total`) — **no producer script exists anywhere**. Regenerating them,
  which Referee 2 asks for, means writing the producer.
