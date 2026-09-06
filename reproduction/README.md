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
source env.sh          # uv venv (python 3.11) + local ROOT
python verify_inputs.py
```

`env.sh` pins **Python 3.11** because the ROOT build at `~/code/root` (6.38.00)
is compiled against 3.11.0; importing PyROOT from 3.12+ fails with
`symbol not found in flat namespace '__Py_HashPointer'`.

### Stage 3 needs a different environment

`Unfolding/unfold_thrust.py` hardcodes `~/code/RooUnfold/build/libRooUnfold.dylib`
(`unfold_thrust.py:18-22`), and that build links `libCore.6.36`. Loading it under
ROOT 6.38.00 mixes two ROOT installations and aborts:

```
Fatal in <TKey::ReadObj>: Incorrect detection of the inheritance from TObject for class TObjArray
```

The matched combination is conda `py312` (ROOT 6.36.06) + RooUnfold `build/`,
which is what Appendix A documents. Until RooUnfold is rebuilt against 6.38.00,
stages 1, 2 and 4 run under `env.sh` and stage 3 needs `conda activate py312`.

## Not reproducible from open data alone

- **theory uncertainty** and **ISR correction** — need the PYTHIA 8.3 / Herwig 7.3 /
  Sherpa 2.2 `tgenBefore` samples, which are not in the open dataset.
- **Figs. 21–23** (`corr_matrices_per_source`, `cov_matrices_per_source`,
  `cov_matrix_total`) — **no producer script exists anywhere**. Regenerating them,
  which Referee 2 asks for, means writing the producer.
