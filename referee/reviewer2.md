Dear Authors, Thanks for this very interesting work.
In general it seems to me the text has similar statements repeated across the paper,
- TODO (substantive). Graduate-student analogy repeats between §2 and §3. Note: "discrepancies … flagged before any result is promoted" actually occurs only once (`AIAgentUsage.tex:84`) — the repetition you sense is of the gating *idea*, not that phrase.
Some aspects and elements are discussed in the initial sections before being introduced and defined.
- Partly fixed (PR 03). MC, pwflag, N_iter, d0/z0 and the stable-hadron lifetime cut now defined at or before first use.

Abstract
"entirely" seems in contrast with "under expert physicist direction"
- TODO (substantive). Real tension: `Introduction.tex:17` says "No analysis code was written by hand", but `AIAgentUsage.tex:29` says the agent is "not an autonomous scientific decision-maker at this stage" and `:75` "Agent-generated text was treated as a draft requiring human approval." Resolving it means deciding what claim the paper makes — the central claim.
"spectrum" > "thrust spectrum"
- Fixed (PR 08).

Sec 1
"ensure robust control " is not  very clear, can you elaborate that ?
Or maybe state something simpler like  "keep the impact of theoretical systematic uncertainties at the level of the experimental uncertainties" ?
- Fixed (PR 08). Adopted essentially as you phrased it; this also drops the overclaiming "ensure".

Lessons from AI–Physicist Collaboration
I find the statements in these two paragraphs a bit vague, and maybe repetitive.
Could you try to specify better what are the methods, lessons, prospects, ..
- TODO (substantive). The `Plans/` ledgers give concrete material to replace the vague prose with.

Section 3
define "MC" here
- Fixed (PR 03).

It is not clear what are the elements, for example in the item list of 3.1,
that are not already currently used routinely by many analyst in the HEP community.
It is important to emphasise what is new and distinctive in this work.
- TODO (substantive). The most important scientific criticism of §3; needs a paragraph distinguishing what the agent did autonomously from standard tooling.

Again some repetition of previous statements, like the graduate student analogy.
- TODO (easy). `Introduction.tex:18` and `AIAgentUsage.tex:29`; keep one.

Would be good to define pwflag and/or to point to sec 6.1
- Fixed (PR 03). Forward pointer added at first use in the Introduction, to Sec. 6.1 and Table 2. Also added the missing `\label` on the Sec. 6.1 heading, which did not exist, so it could not be referenced at all.

A reference for miniDST would be good to add.
- TODO (easy but needs a source). There is no miniDST/DST entry anywhere in `biblio.bib`. The right citation (ALEPH internal note, or the open-data record DOI) is not something to guess at.

Sec 3.2
Would be nicer to have the four categorie in a enumerated list, or on a table.
- TODO (easy). Currently four consecutive sentences in one paragraph, while §3.1 and §3.3 use `itemize`.

Sec 3.3
Not clear what the chi2 is and what the "iterations 4–6." are.  Some more informations would be useful.
- TODO (easy). The χ² is refolded vs. detector-level data; 4–6 are the regularization variation passes. But see the χ² caveat under Sec 7.3 below — the "stable" claim rests on the *shape* variant.
clarify what  "pathological bins" are
- TODO (easy). Means the endpoint region T ∈ [0.99, 1.00].
clarify what are the  "checksums of key outputs"
- TODO (easy).

"discrepancies between expected and observed outputs are flagged before any result is promoted" :
this is repeated several times, but it is not very clear how it is implemented.
It also seems a procedure that would have a worrisome strong  bias to produce "expected" results.
Would be good to elaborate also on that aspect.
- TODO (substantive). Your sharpest point. Deserves a direct, non-defensive answer about how the expectation was set independently of the result.

Sec 4
for the track momentum resolution would be better  to add the multiple scattering term that is important also at pT~10 GeV
and dominates at lower pT. I should be deltaPt/pt = 5 x 10-3.
The constant terms for the energy resolutions would also be better to provide.
- TODO (easy). Correct on both counts: σ(1/p_T) ≈ 6×10⁻⁴ GeV⁻¹ is quoted as a bare number with no multiple-scattering term, and ECAL 0.18/√E and HCAL 0.85/√E are pure stochastic terms. Full expressions are in `Decamp:1990jra` / `ALEPH:1994ayc`, both already in the bib.

Sec 5
"corresponds to an integrated luminosity of"
Add information on the size of the simulated sample
- No change needed. Both are already present: ~40 pb⁻¹ at `Datasets.tex:4`, and 771,597 MC reco events in Table 1 (vs 1,326,312 data), with the data/MC ratio discussed at `:34`.
Clarify if the contributions from background sources (as tau pair productions) have been considered.
- TODO (substantive). Not discussed anywhere; only fakes are mentioned (`AnalysisMethod.tex:34`). A literature-based statement (ALEPH quotes ≲0.5%) is easy; an actual estimate is not possible from the synchronized sample set, which has no τ-pair MC.
Specify the lifetime definition for the "stable-hadron level" definition (lifetime > ? )
- Fixed (PR 03). The criterion cτ > 10 mm existed but only as a row in Table 5; now stated in Sec. 5 where the particle-level definition is introduced.
Would it be better to distinguish the detector-level data and MC with different labels (like tdata and tmc)  ?
- TODO (easy, presentational).

Sec 6
Table 2 . Suggest to modify the text in :
0 charged hadrons
1 electrons (tracker + ECAL category)
2 muons (tracker + muon category)
- Fixed (PR 05). Adopted verbatim. The old labels called pwflag 1 and 2 both "charged leptons", which did not distinguish them.

Would be good to explain what are the tracks d0 and z0 and how they are evaluated (wrt to which vertex)
- Fixed (PR 03). Both defined in Sec. 6.2 as distances of closest approach to the **nominal e+e− interaction point** (not a per-event reconstructed primary vertex). N_TPC defined while there.

Table 3 maybe should clarify if and how these criteria are applied at gen level
- TODO (easy, but get it right). Per `runAnalyze.py:219` and `analysisCompute.h:118` (cuts inside `if (!genTree)`), object-level cuts are **not** applied at gen level. One sentence, but it interacts with the no_neutrals issue below.

Table 4 : why are inactive cuts listed ? Explain their role.
- Fixed (PR 05). Caption now states the last two rows reject no events nominally, are listed so the configuration is fully specified, and are the hooks used by the missing-E_T variation in Table 7.

Sec 6.3
Fig 1 Can you comment on why we have enhancements at costheta=0 (also for gen) ?
What are the peaks at p=E=45 GeV and why are they not there at gen level ?
- TODO (substantive). The 45 GeV reco-only peaks are most likely the beam-energy-constrained / kinematic-fit edge, but this should be verified rather than asserted.

Fig 3 the phi structure, only at gen level, is suprising, can you comment on that ?
- TODO (substantive — and note the reading). The comb is in **Data reco and MC reco**, with MC gen flat; the legend is correctly colour-coded, so the misreading comes from the paper's own text, which claims the opposite (see Fig 8 below).

Fig 4 : the peaks here at E~p=45 GeV for V0 collection should also be explained (and why they are only in the reco)
- TODO (substantive). Same as Fig 1.

page 18 : comments on fig 1 : "The NTPC distribution shows good overall agree-
ment between generators, with small differences between JETSET and modern generators"
but the figure shows only one MC prediction.
It is also not clear why NTPC would be a sensitive observable for that.
- TODO (substantive, and you are right on both). Figs 1–6 show exactly four curves (Data, MC Reco, MC Gen, MC GenBefore) — one MC, the archived JETSET sample. **No figure in §6.3 contains Pythia 8, Herwig or Sherpa.** This cannot be fixed by re-plotting: `runAnalyze.py:16-27` configures those three with `treeNames: ['tgenBefore']` only, so they have no reco and hence no pwflag at all; `Datasets.tex:32` confirms they enter only as event-level reweighting. Six passages must be deleted or retargeted (`EventReconstructionAndSelection.tex:115-117, 122-124, 129-130, 156-160, 171-172, 189-190`). Separately, N_TPC is a *detector* hit-count quantity, so it is not a generator observable — that claim should go.

There are other comments in the text referring to comparisons to different generators for other figures 2,3,4,5,6
that are not visible in the figures.
- TODO. Same root cause; all six passages listed above.

Fig 2,3 : "Differences between the archived MC and modern generators (Pythia 8, Herwig, Sherpa) are visible in.. "
- TODO. Same.

Fig 4 " "Generator differences are more visible than for charged tracks, reflecting differences in strange-particle production modeling"
"The ϕ spectrum (Fig. 5) shows a modulation in the generator-level distribution"
I'm guessing all this discussion on generators across pages 18-19-20 refers to some other figures.
- TODO. Same. Your guess is right that the text does not match the figures shipped.
The comment "(see Sec. 6.3)" is awkward as it is written inside Sec. 6.3
- Fixed (PR 02). The label was set 26 lines later in the same subsection; retargeted to the figure that actually shows the investigation.

Fig 7 :  It would be interesting to see the MC (no-sel) prediction to justify the cut.
- Already available. `pwflag5_costheta_mc_with_vs_without_sel.pdf` is already rendered in `manuscript local save/Studies/Phase2_Checks_2026-03-03/` and was simply never shipped. Note also (PR 06) that the cleaning cut is applied at object level in both curves of the existing right panel, so it never showed the cut's effect at all.
Sec 6.4

Fig 9 : It seems surprising that there seems to be almost no difference in the Gen and GenBefore predictions  except for the theta distribution.
The GenBefore distributions should have larger particle multiplicities and total energy.
- TODO (substantive, possibly a real bug). GenBefore *is* displaced from Gen in N_trk, N_trk+N_neu and E_Ch; the suspicious part is that **MC Gen tracks Data/MC Reco almost exactly**, when gen-level multiplicity should sit above reco (gen histograms are built without the object-level cuts). Worth checking which tree/branch each curve is filled from.
What is also strange is the up-down oscillating pattern in the MC/Data for the (upper-left) Ntrk plot : how is that happening ?
- TODO (easy, text answer). Our first guess (misaligned bin edges) was wrong: `plot.py:86` sets `"ntrk": (61, -0.5, 60.5)`, already one integer per bin. The surviving explanation is that charge conservation favours even N_ch, so any data/MC difference in the even-odd structure shows up as an alternating ratio.

define "IBU" on page 20
- No change needed. IBU is already defined, in Sec. 2: "Iterative Bayesian Unfolding (IBU) implemented in RooUnfold".

Sec 7
explain better  what is  "systematic execution" and "the correction" ?
- TODO (easy). Undefined boilerplate in the §7 lead-in (`AnalysisMethod.tex:4-6`).
define "Niter "
- Fixed (PR 03). Defined at first use in Sec. 7.1; previously only implied by a row in Table 5.

Sec 7.3
Would be good to add some references for the unfolding procedure
- Fixed (PR 07). §7.3 had zero `\cite` commands. Added D'Agostini (key was already in `biblio.bib`, uncited), RooUnfold/Adye (had **no** bib entry — created), and OmniFold (also already in the bib, uncited, despite being the main cross-check).

Can you quantify better how small is the iteration-to-iteration change ?
- TODO (easy — numbers exist locally). `mean_abs_fractional_central/iteration = 0.339%`, `max = 0.855%` over 0.60 ≤ T < 0.95; `iter_delta_chi2_ndf = 0.204`. **Two caveats before quoting:** (i) the scan's own recommendation is iteration **7**, not the nominal 5, which the paper never mentions; (ii) the "stable closure-shape χ²/ndf" is the *shape* variant (~2×10⁻⁶, meaningless) — the *counts* refold χ²/ndf is 2.73 at N=5 (2.28 at N=7), i.e. the refold does not describe the data within statistics, contradicting App. B.1.

Can you quantify how much is the migration driven separately by the charged particle momentum resolution, and by the soft particles acceptance ?
I would guess the latter is dominant.
- TODO (needs data machine; worth doing). Requires a new MC-truth ablation on matched reco-gen pairs: truth momenta with smearing only, vs. reco acceptance/thresholds without smearing, vs. both. Nothing existing does this. Your guess is probably right and worth confirming.

Fig 10. What are the (huge) error bars on the efficiency plot ?
- TODO (needs data machine — confirmed bug). Efficiency sits at 0.95–1.0 but bars span ~the full 0–1 range, impossible at ~10⁵ events/bin. Cause: `h_eff.Divide(h_den)` at `miss_term_plots.py:187` omits the binomial `"B"` option. Fix with `Divide(h1,h2,1,1,"B")` or `TEfficiency`.

Fig 11. The distribution seems in fact to peak above zero, as if there is a bias.
can you comment on that ?
- Partly fixed (PR 06). You are right, and there was also a caption/figure mismatch: the shipped file is the **2D** map while the caption and `\label` described the 1D projection. Caption, text and label now describe the 2D map, and the unsupported "centered at zero, confirming no significant systematic bias" claim is removed. The 1D projection and a bias profile are already rendered locally (`thrust_resolution_1d.pdf`, `_bias.pdf`) and could be shipped.

Table 6. Several entries in the table are not very clear or have not been defined, like input labels "ntpc7, pt04, ech10, with met  "
- Fixed (PR 05). These were bare on p. 25 while defined only in Table 7 on p. 28. The Table 6 caption now defines each branch and points to Table 7.

Sec 7.6 previously it was stated that "The ISR correction is not yet implemented in the current analysis and represents a systematic gap relative to the published results;"  but here is seems it is implemented.
Can you clarify ?
- TODO (substantive, and worse than you flag). `Datasets.tex:20` is stale — the correction *is* applied. But separately, the ISR component is **missing from the per-bin quadrature total**: no column in Table 8, absent from Table 6's formula, absent from Fig. 18's legend, absent from App. A's pseudocode. We verified Table 8's totals reproduce across all 44 rows without it, while §8.7 writes a six-component total including Δ²_ISR. `uncertainty_components_isr.pdf` was rendered but never shipped.

Why is the ISR uncertainty only taken from the finite MC statistics ?
- TODO (substantive, paper already concedes it). §8.5: "the Pythia8 generator used here differs from the KORALZ generator used in the ALEPH 2004 analysis… This difference in generator is not propagated as an additional systematic in the current release." Full KORALZ generation is likely out of scope for a revision; recommend bounding it and quoting it as an explicit component.

Sec 8.

I'm wondering how the MC stat fluctuations (that should be larger than the data ones) are being taken into account. Can you elaborate ?
- TODO (substantive — the paper's claim is not implemented). §8.6 and §7.6 state the chain "propagates Poisson uncertainties in the data **and response histograms**". `unfold_thrust.py:788` has the only covariance call, `Eunfold(RooUnfold.kCovariance)`, with **no `IncludeSystematics()` and no `SetNToys()` anywhere in the file**. `kCovariance` propagates the measurement covariance only. So response/MC statistics are not propagated. Related: §8.1 quoted "~700,000" for the data sample, which is the MC count — fixed in PR 04 to 1,326,312.

Fig 14. Could be nice to show also a zoom of the y axis on both plots to show better the uncertainties in the higher T regions.
- TODO (needs data machine). Agreed: the iteration panel is hard-coded to ±50 while actual shifts are ≤7% and mostly <1%, so it reads as a flat line. Also fixed in PR 06: the caption promised an "envelope (dashed black)" that is not drawn.

Why does the unfolding uncertainty flip sign several times across the T range ?
- TODO (easy, text answer). Iter-4 and iter-6 bracket the nominal with opposite sign; the bin-to-bin alternation at low T is regularization-induced anti-correlation between neighbouring bins. Undiscussed at present.
8.2
Fig 16 the charged/EF ratio is interesting, it seems the leading effect is a shift of the charged to lower values:
is there any understanding for that ?
- TODO (substantive).

Could you perform the No-neutrals xcheck measurement unfolding to the same T particle level definition as the reference analysis, so it is indeed the measurement of the same observable (with a reduced reco particle collection) ?

This should represent a more meaningful and stringent xcheck of the results.
- TODO (substantive — and this is arguably already what was done, which inverts the paper's argument). §8.2 and the Fig. 16 caption claim "separate response matrices for each particle-level definition." **They are not.** `run_thrust_prelim_workflow.py:411-431` overrides only `reco_mc_file` and `data_file` for cut-based variations; `gen_mc_file` is never overridden, and the gen file (`..._no_event_sel_tgen.root`) has no `_nominal_` token so `variation_file()` could not substitute it anyway. `runAnalyze.py:219` produces exactly one gen file, with neutrals kept. So the `no_neutrals` branch already unfolds charged-only reco to the nominal energy-flow particle level — your requested cross-check. But then the ~23% shift **cannot** be attributed to "two distinct observables", because the particle-level target is identical, and Fig. 16 becomes evidence of a 23% sensitivity to neutral-object modelling rather than a refutation of it. Text must be rewritten first; a genuinely *different* comparison (unfolding to a charged-only particle level) would need a new gen-level production.

8.3 "at lower thrust where soft-gluon emission and hadronization effects are largest"
isn't lower thrust where hard gluon emissions are relevant ?
- TODO (substantive — you are right, the physics is backwards). Low T (large τ) is the multi-jet / **hard**, wide-angle gluon region. Soft-gluon resummation and non-perturbative power corrections (~Λ/Qτ) are largest at **high** T, at the dijet endpoint. Suggested rewrite: "…diverge progressively at lower thrust, where multi-jet configurations and hard, wide-angle gluon emission dominate and the parton-shower / matrix-element matching differs between generators." (`Results.tex:25-27` attributes the *endpoint* discrepancy to soft hadrons, which is correct — the error does not propagate there.)

Fig 17. The difference at low values look mostly like fluctuations. At higher values there is maybe a shift of T to lower values for the new models ?
- TODO (substantive).

8.5 Do we have any idea of how large / relevant could be the difference of ISR effects evaluated with pythia and koralz ?
- TODO. See the ISR uncertainty comment above.

8.7 could you add some justification to combine in quadrature ?
- TODO (substantive). No independence argument is given anywhere. Three specific things to address: (i) §8.1 itself calls the regularization uncertainty "closely related" to the statistical one, then adds them in quadrature; (ii) `ntpc7`, `pt04`, `ech10` are re-selections of the *same* events and are strongly correlated, and each branch shift carries its own data-statistical noise counted as systematic (`ntpc7` has `max_abs_fractional_diff = 3.74`, i.e. 374%); (iii) theory uses an envelope while experimental uses quadrature, with the mixed convention unexplained.

Fig 18 : What is the nature of the asymmetric NES uncertainties ?
- TODO (easy — quantifiable now). `nes_up` mean|Δ| = 1.34% (max 10.5%), `nes_down` 0.80% (max 5.1%) — a factor ~2, consistent with a ±5% scale acting on a steeply falling spectrum. (These are from the 2026-02-13 run; re-derive before quoting.)

Why does the track pt cut uncertainty jump to 12-13 % in the T~1 last bin
- TODO (easy, text answer). Raising the track p_T threshold removes soft tracks, which at T → 1 directly moves events across the dijet endpoint boundary. Confirming the exact per-branch number needs the run directory.

Sec 9.1
"largest discrepancy at the endpoint"  reported to be 1.30+-0.27, but on the plot appear to be at a lower value.
- TODO (easy). The numbers are self-consistent: Table 9 gives ours 1.01, ALEPH 1.31 → 1.297; error 14.5% ⊕ 15.4% ≈ 21% of 1.30 = 0.27. `uncertainty_breakdown.json` confirms `ratio_mode: aleph_over_unfolded`. The actual defect is that **the text never says which way the ratio goes** — that needs fixing.

Fig 19. How is it that the ALEPH measurements seem to have larger uncertainties over most of the bins ?  Can you comment on that ?
- TODO (substantive — the single most important paragraph to write well). ALEPH's total exceeds ours in **31 of 42** bins. Mechanism visible in Table 10: ALEPH's Sys.2 is assigned in coarse blocks of identical values (20.3×3, 7.8×3, 7.1×3, 5.5×3, 3.7×3, 3.1×3, …), i.e. band-wise, whereas our theory envelope is a per-bin max that happens to be small in the bulk. An honest answer must also note that our missing components (ISR in the total, response-matrix statistics, correlated-branch treatment, singular covariance) all push the same way.

Table 9 : Are the ALEPH uncertainties the same as plotted in Fig 19 ?
Just looking at the endpoint bin the table quotes 15% but the plot seems to show 20-25%
- TODO (easy). They are the same; the apparent conflict is a plotting convention. In the ratio panel the error bar is 1.30 × 15.4% = 0.20 in absolute ratio units. State the ratio direction and that ratio-panel bars are scaled by the ratio value.

Fig 21. Would it be better to have these plots with the y axis upwards as usual (like in Fig 20) ?
- TODO (needs data machine — and there is a deeper problem). Yes: Fig. 20 is ROOT `COLZ` with y up and axes in thrust units; Figs. 21–23 are matplotlib with y **down** and axes in bin index. But more seriously, **all six panels of Fig. 21 are identical by construction**: under §8.6's model `Cov^(c)_ij = Δ_c(i)Δ_c(j)ρ^stat_ij`, the derived correlation is `ρ^stat_ij` for every component regardless of Δ_c. So §9.2's statements ("the theory component shows the strongest and most extended off-diagonal correlations", "ISR is nearly diagonal") describe structure that cannot exist. §9.2 needs rewriting or deleting.

Fig 22-23 visual information in these plots is very scarce,  they are almost completely uniform, can you try to improve that  ?
- TODO (needs data machine, blocked twice). Confirmed: a single shared *linear* scale set by the endpoint bin (Fig. 22 spans ±0.0012; Fig. 23 shows one visible 3×3 corner block). Fix with `SymLogNorm`, per-panel normalisation, or better, plot fractional covariance Cov_ij/(x_i·x_j). Blocked because (a) the producer script for Figs. 21–23 is **not present** in `manuscript local save` and must be located first, and (b) its `cov_*.csv` inputs are absent.
