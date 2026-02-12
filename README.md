# ALEPH_Thrust_Analysis
C++/ROOT analysis code for computing event-shape observables on archived ALEPH data.

## Primary workflow
- Run the analysis on raw data to produce derived ROOT files with observables.
- Perform unfolding/corrections in separate steps.
- Make plots from the derived files.

## Analysis entry points
- `DataProcessing/src/Analyze.cxx`: RDataFrame-based analysis (single event loop with implicit MT)
- `DataProcessing/runAnalyze.py`: Python wrapper to run multiple selection variations and trees

## Plotting
- `DataProcessing/plotting/plot.py`: Plot event-level and pwflag particle distributions from ROOT files

Example:
```bash
cd DataProcessing/plotting
python plot.py --data /path/to/data_reco.root --mc-reco /path/to/mc_reco.root
python plot.py --data /path/to/data_reco.root --mc-reco /path/to/mc_reco.root \
  --prev-data /path/to/prev_data_reco.root --prev-mc-reco /path/to/prev_mc_reco.root
```

## Example
```bash
cd DataProcessing
python runAnalyze.py -i /path/to/input.root --outDir ./out -j 8
```

Notes:
- Generator-level trees (`tgen`, `tgenBefore`) are only run for `no_event_sel`.
- Histogramming is intentionally excluded here.
