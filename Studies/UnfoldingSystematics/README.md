# Unfolding Systematic Variations Study

This folder now uses a thin wrapper script that only orchestrates existing code:
- `Unfolding/unfold_thrust.py`
- `Unfolding/plot_unfolded.py`

## How it runs

```bash
python3 Studies/UnfoldingSystematics/scripts/run_systematic_unfolding.py
```

For each discovered variation file
`DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_<variation>_t.root`,
the wrapper runs:
1. `unfold_thrust.py` with `--set reco_mc_file=...`, `--set data_file=...`, and `--set out_root=...`
2. `plot_unfolded.py` on that output ROOT file

Variation rules match `../unfold-ee-logtau/run_ibu.py`:
- Cut-based variations (`ntpc7`, `pt04`, `ech10`, `no_neutrals`, `with_met`): vary both data and reco MC.
- Neutral-response variations (`nes_up`, `nes_down`, `ner`): vary reco MC only; keep nominal data.

If cut-based data files are not available, the wrapper fails by default.
You can opt into nominal-data fallback with:

```bash
python3 Studies/UnfoldingSystematics/scripts/run_systematic_unfolding.py --allow-missing-cut-data
```

## Outputs

All outputs are written to `Studies/UnfoldingSystematics/results/`:
- `unfolded_<variation>.root`
- `unfolded_<variation>.pdf`
