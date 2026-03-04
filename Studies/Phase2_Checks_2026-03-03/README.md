# Phase 2 Analysis Checks — 2026-03-03

Reviewer-motivated analysis checks. Run from the repo root after activating ROOT:

```bash
source ~/code/root/bin/thisroot.sh
# or: conda activate py312
```

## File structure

| File pattern | Tree | Key branches |
|---|---|---|
| `*_nominal_t.root` | `t` | `Thrust`, `passEventSelection`, `uniqueID`, `px/py/pz`, `pwflag` |
| `*_no_event_sel_t.root` | `t` | same, no passEventSelection filter applied |
| `*_no_event_sel_tgen.root` | `tgen` | `Thrust`, `uniqueID`, `STheta`, `NTrk`, `px/py/pz`, `pwflag` |
| `*_no_event_sel_tgenBefore.root` | `tgenBefore` | same (before hadronic correction) |

Events matched between reco and gen trees via `uniqueID`.

---

## Script 1: Thrust resolution study
**Reviewer: Figure 9 motivation / sec:thrust_resolution**

```bash
python Studies/Phase2_Checks_2026-03-03/scripts/thrust_resolution_study.py \
    --input-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
    --input-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
    --outdir Studies/Phase2_Checks_2026-03-03/plots/thrust_resolution
```

Outputs: `thrust_resolution_2d.pdf`, `thrust_resolution_profile.pdf`, `thrust_resolution_bias.pdf`

---

## Script 2: Miss-term plots
**Reviewer: migration / miss-term documentation**

```bash
python Studies/Phase2_Checks_2026-03-03/scripts/miss_term_plots.py \
    --input-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
    --input-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
    --outdir Studies/Phase2_Checks_2026-03-03/plots/miss_term
```

Outputs: `miss_term_thrust.pdf`, `miss_term_costheta.pdf`, `miss_term_ntrk.pdf`, `miss_term_efficiency.pdf`

---

## Script 3: pwflag=5 cos(theta) without cleaning cut
**Reviewer: sec:phi_excess / neutral hadron cleaning cut documentation**

```bash
python Studies/Phase2_Checks_2026-03-03/scripts/pwflag5_costheta_no_cut.py \
    --input-data        DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
    --input-mc          DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
    --input-data-no-sel DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_no_event_sel_t.root \
    --input-mc-no-sel   DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_t.root \
    --outdir Studies/Phase2_Checks_2026-03-03/plots/pwflag5_costheta
```

Outputs: `pwflag5_costheta_data_vs_mc.pdf`, `pwflag5_costheta_data_with_vs_without_sel.pdf`,
`pwflag5_costheta_mc_with_vs_without_sel.pdf`, `pwflag5_costheta_all_logy.pdf`

---

## Script 4: Phi spectrum investigation
**Reviewer: sec:phi_excess / 24-fold HCAL modulation check**

```bash
python Studies/Phase2_Checks_2026-03-03/scripts/phi_spectrum_investigation.py \
    --input-data    DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
    --input-mc-reco DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
    --input-mc-gen  DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_no_event_sel_tgen.root \
    --outdir Studies/Phase2_Checks_2026-03-03/plots/phi_spectrum
```

Outputs per pwflag (0,4,5): `phi_pw{N}_data_vs_mc_reco.pdf`, `phi_pw{N}_mc_reco_vs_gen.pdf`,
`phi_pw{N}_all.pdf`; plus `phi_all_pwflags_data.pdf`, `phi_all_pwflags_mc_reco.pdf`

---

## Script 5: Refolding pull panel
**Reviewer: Figure 9 pull panel**

```bash
python Studies/Phase2_Checks_2026-03-03/scripts/refolding_pull_panel.py \
    --input-data       DataProcessing/temp/LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root \
    --input-mc-nominal DataProcessing/temp/alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root \
    --outdir Studies/Phase2_Checks_2026-03-03/plots/pull_panel
```

Output: `dist_refolded_vs_data_pull.pdf`
(Expected by analysis note at this exact path)

---

## Status

| Script | Status |
|---|---|
| thrust_resolution_study.py | Scripts ready — run on Mac |
| miss_term_plots.py | Scripts ready — run on Mac |
| pwflag5_costheta_no_cut.py | Scripts ready — run on Mac |
| phi_spectrum_investigation.py | Scripts ready — run on Mac |
| refolding_pull_panel.py | Scripts ready — run on Mac |
