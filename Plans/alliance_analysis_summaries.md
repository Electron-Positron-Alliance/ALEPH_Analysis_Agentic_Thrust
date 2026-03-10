# e+e- Alliance Analysis Summaries

This file contains the agent's synthesized summaries of prior e+e- alliance analyses. Each entry captures the key physics and implementation choices that would influence a new measurement. Entries are added whenever the agent is given access to a new analysis (repo, paper, or analysis note).

This is not a verbatim copy — it is the set of decisions relevant to the next measurement.

---

## ALEPH_Agentic_Event_Shape_Analysis — Thrust (T)

**Observable**: Thrust T, range [0.5, 1.0), 50 uniform bins (ΔT = 0.01)
**Repo**: `ALEPH_Agentic_Event_Shape_Analysis`
**Result directory**: `Studies/PreliminaryResult/2026-03-05_thrust_iter5/`
**Analysis note**: `AnalysisNote/main.tex`

**Key choices**:
- Unfolding: RooUnfold IBU, N_iter=5 (nominal); iteration scan at N=4,5,6,10,100
- Phase space: charged (pwflag 0–2) + neutral (pwflag 3–5), nominal selection
- Event selection: E_ch ≥ 15 GeV, |cos θ_S| ≤ 0.82, N_trk ≥ 5, N_trk+N_neu ≥ 13
- Hadronic correction: C_had(j) = N_genBefore(j)/N_gen(j), applied first post-unfolding
- ISR correction: C_ISR(j) = ISR0/ISR1 (Pythia8), pre-cached to isr_cache/isr_correction_cache.root
- Theory systematic: Particle Edge Transformer reweighting (Pythia6 → Pythia8/Herwig7/Sherpa2), event-level weights from Step2 numpy files; envelope across generators
- Experimental systematic: quadrature of ntpc7, pt04, ech10, with_met, nes_up, nes_down, ner
- Covariance: template rule Cov^(c)_ij = Δ_c(i)·Δ_c(j)·ρ^stat_ij

**Key results (central range 0.60 ≤ T < 0.95)**:
- Total uncertainty: 7.65% mean
- Theory: 6.08%, Experimental: 3.34%, Statistical: 1.71%, Iteration: 0.34%
- f_diag ≈ 0.33; stat covariance has 1980 non-zero off-diagonal entries
- Endpoint (T > 0.95): elevated uncertainty; ALEPH 2004 ratio = 1.30 ± 0.27 (expected)

**Notable findings / bugs caught**:
- Wrong default tree (`t` instead of `tgen`) in original unfold script — caught in code review
- Hadronic correction uncertainty was initially excluded from total — caught in critical review
- Systematic covariance was diagonal by construction (bug) — fixed by applying template rule
- 5 zero-variance endpoint bins in cov_total — acceptable; fit window excludes them
- Machine-local hardcoded paths in workflow scripts — must use configurable paths

---

## unfold-ee-logtau — Unbinned OmniFold Thrust

**Observable**: Thrust T (stored internally as 1−T), ALEPH data at √s = 91.2 GeV
**Repo**: `unfold-ee-logtau`
**Paper**: arXiv:2510.22038; analysis note arXiv:2507.14349
**Result directory**: `arxivPaperResults2025/`

**Key choices**:
- Unfolding: pure numpy IBU (`ibu.py`); uses bootstrap for statistical uncertainty; finite-difference Jacobian for full covariance propagation
- Theory reweighting: same Particle Edge Transformer Step2 numpy weights (Pythia8/Herwig/Sherpa); intersection of uniqueIDs between tgenBefore and tgen for alignment
- Hadronic correction: `gen_bhist / (gen_hist + 1e-50)` per bin
- ISR: pre-cached correction file

**Notes**:
- Weight files at `arxivPaperResults2025/theory_reweighting/training-bf3b5fc3/`
- IBU implemented without RooUnfold — pure numpy, bootstrap stat uncertainty

---

## ALEPH 2004 (Heister et al.) — C-Parameter Reference Measurement

**Paper**: Eur. Phys. J. C 35 (2004) 457 — "Studies of QCD at e+e- c.m. energies between 91 and 209 GeV"
**Observable coverage**: T, ρ, C, B_W, B_T, −ln y_3 at √s = 91.2–206 GeV

**C-parameter specific results at Q = 91.2 GeV**:
- αs(MZ) = 0.1225 ± 0.0001(stat) ± 0.0007(exp) ± 0.0058(pert) ± 0.0015(hadr), total ± 0.0061
- Fit range used: **C ∈ [0.26, 0.64]** (central region, ~39 bins at 1/100 spacing)
- At Q = 133 GeV: fit range C ∈ [0.18, 0.75]; at Q = 161–172 GeV: C ∈ [0.18, 0.75]
- Data corrected via multiplicative bin-by-bin factors (matrix method), not IBU

**Event selection note**:
- ALEPH 2004 uses |cos θ_sph| < 0.9 (sphericity axis) for C-parameter, not |cos θ_thrust| < 0.9
- Our existing ROOT files use |cos θ_thrust| < 0.9 (same as thrust analysis) — small analysis difference; document in note

**Key for comparison**:
- C-parameter distributions available in the paper (Fig. 11) and on HEPData/Durham database
- Binning in ALEPH 2004: not explicitly stated in paper text; fit range implies ~38 points in [0.26, 0.64]
- Unfolding: bin-by-bin matrix method (not IBU); we use IBU → binning choice governed by our resolution study (CP1)

---

*Add new entries here as additional alliance analyses are reviewed.*
