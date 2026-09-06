Dear Authors, Thanks for this very interesting work.

- In general it seems to me the text has similar statements repeated across the paper,
- Some aspects and elements are discussed in the initial sections before being introduced and defined.
  - **Response.** Partly addressed. MC, pwflag, $N_{\mathrm{iter}}$, $d_0$/$z_0$/$N_{\mathrm{TPC}}$ and the stable-hadron lifetime cut are now defined at or before first use, with forward pointers where the term first appears earlier than its definition. The remaining instances are covered by your specific comments below.

Abstract
- "entirely" seems in contrast with "under expert physicist direction"
- "spectrum" > "thrust spectrum"

Sec 1
- "ensure robust control " is not  very clear, can you elaborate that ?
  Or maybe state something simpler like  "keep the impact of theoretical systematic uncertainties at the level of the experimental uncertainties" ?

Lessons from AI–Physicist Collaboration
- I find the statements in these two paragraphs a bit vague, and maybe repetitive.
  Could you try to specify better what are the methods, lessons, prospects, ..

Section 3
- define "MC" here
  - **Response.** Expanded to "Monte Carlo (MC)" at first use, in Sec. 3.
- It is not clear what are the elements, for example in the item list of 3.1,
  that are not already currently used routinely by many analyst in the HEP community.
  It is important to emphasise what is new and distinctive in this work.
- Again some repetition of previous statements, like the graduate student analogy.
- Would be good to define pwflag and/or to point to sec 6.1
  - **Response.** Added a pointer to Sec. 6.1 and Table 2 at the first use, in Sec. 2. Sec. 6.1 had no label, so it could not previously be referenced; one has been added.
- A reference for miniDST would be good to add.

Sec 3.2
- Would be nicer to have the four categorie in a enumerated list, or on a table.

Sec 3.3
- Not clear what the chi2 is and what the "iterations 4–6." are.  Some more informations would be useful.
- clarify what  "pathological bins" are
- clarify what are the  "checksums of key outputs"
- "discrepancies between expected and observed outputs are flagged before any result is promoted" :
  this is repeated several times, but it is not very clear how it is implemented.
  It also seems a procedure that would have a worrisome strong  bias to produce "expected" results.
  Would be good to elaborate also on that aspect.

Sec 4
- for the track momentum resolution would be better  to add the multiple scattering term that is important also at pT~10 GeV
  and dominates at lower pT. I should be deltaPt/pt = 5 x 10-3.
- The constant terms for the energy resolutions would also be better to provide.

Sec 5
- "corresponds to an integrated luminosity of"
  Add information on the size of the simulated sample
  - **Response.** Both are already given: Sec. 5 states approximately 40~pb$^{-1}$ and
    approximately 1.33 million selected hadronic events, and Table 1 gives the per-sample counts.
    While checking this we found Sec. 5 quoted the MC total as if it were the selected count;
    corrected to 752k, matching Table 1.
  - **NEEDS DATA MACHINE.** The counts were checked only for internal consistency against Table 1,
    not against the production. No source was found for 40~pb$^{-1}$, and the data-side counts
    (1,365,440 / 1,326,312) and MC reco counts (771,597 / 751,861) are not in
    `workflow_summary.json`, which carries only the two generator-level trees (771,597 and
    973,769). Verify all of them against the production once on the analysis machine. Mirrored as a
    comment above the sentence in `sections/Datasets.tex`.
- Clarify if the contributions from background sources (as tau pair productions) have been considered.
- Specify the lifetime definition for the "stable-hadron level" definition (lifetime > ? )
  - **Response.** Sec. 5 now states the criterion in the prose, proper decay length $c\tau > 10$~mm, where the particle-level definition is introduced. It was previously given only as a row in Table 5.
  - **NEEDS DATA MACHINE before submission.** The $c\tau > 10$~mm value is pre-existing repo content, relocated rather than established here, and has no citation or in-repo code backing it. Confirm (a) that the generator-level selection really applies it, and (b) whether it is our choice or inherited from ALEPH's published particle-level definition, and cite accordingly. Batches with the $d_0$/$z_0$ check above -- both need the analysis code. Mirrored as a comment above the sentence in `sections/Datasets.tex`.
- Would it be better to distinguish the detector-level data and MC with different labels (like tdata and tmc)  ?

Sec 6
- Table 2 . Suggest to modify the text in :
  - **Response.** Adopted verbatim. The previous labels called pwflag 1 and 2 both "charged leptons", which did not distinguish them.
  0 charged hadrons
  1 electrons (tracker + ECAL category)
  2 muons (tracker + muon category)
- Would be good to explain what are the tracks d0 and z0 and how they are evaluated (wrt to which vertex)
  - **Response.** Defined in Sec. 6.2 as the transverse and longitudinal distance of closest approach of the track helix to the per-event reconstructed primary vertex. Both are read as stored in the archived ALEPH reconstruction and are not recomputed here. $N_{\mathrm{TPC}}$, the number of TPC coordinates on the track, is defined alongside, and Sec. 4, where they first appear, now points there.
  - **NEEDS DATA MACHINE before submission.** The reference point is stated from expert recollection, not confirmed. Our analysis code only reads the stored $d_0$/$z_0$ and carries no information about what they are measured against, so this has to come from the original ALEPH data processing (miniDST production / reconstruction documentation). Mirrored as a comment above the claim in `sections/EventReconstructionAndSelection.tex`.
- Table 3 maybe should clarify if and how these criteria are applied at gen level
- Table 4 : why are inactive cuts listed ? Explain their role.
  - **Response.** The caption now states that the last two rows reject no events in the nominal configuration, are listed so the nominal setup is fully specified, and are the hooks used by the missing-momentum variation in Table 7.

Sec 6.3
- Fig 1 Can you comment on why we have enhancements at costheta=0 (also for gen) ?
  What are the peaks at p=E=45 GeV and why are they not there at gen level ?
- Fig 3 the phi structure, only at gen level, is suprising, can you comment on that ?
- Fig 4 : the peaks here at E~p=45 GeV for V0 collection should also be explained (and why they are only in the reco)
- page 18 : comments on fig 1 : "The NTPC distribution shows good overall agree-
  ment between generators, with small differences between JETSET and modern generators"
  but the figure shows only one MC prediction.
  It is also not clear why NTPC would be a sensitive observable for that.
- There are other comments in the text referring to comparisons to different generators for other figures 2,3,4,5,6
  that are not visible in the figures.
- Fig 2,3 : "Differences between the archived MC and modern generators (Pythia 8, Herwig, Sherpa) are visible in.. "
- Fig 4 " "Generator differences are more visible than for charged tracks, reflecting differences in strange-particle production modeling"
  "The ϕ spectrum (Fig. 5) shows a modulation in the generator-level distribution"
  I'm guessing all this discussion on generators across pages 18-19-20 refers to some other figures.
- The comment "(see Sec. 6.3)" is awkward as it is written inside Sec 6.3
  - **Response.** The reference pointed at a label inside the same subsection. Retargeted to the figure that shows the investigation.
- Fig 7 :  It would be interesting to see the MC (no-sel) prediction to justify the cut.

Sec 6.4
- Fig 9 : It seems surprising that there seems to be almost no difference in the Gen and GenBefore predictions  except for the theta distribution.
  The GenBefore distributions should have larger particle multiplicities and total energy.
- What is also strange is the up-down oscillating pattern in the MC/Data for the (upper-left) Ntrk plot : how is that happening ?
- define "IBU" on page 20
  - **Response.** IBU is already defined, at first use in Sec. 2: "Iterative Bayesian Unfolding (IBU) implemented in RooUnfold". No change made.

Sec 7
- explain better  what is  "systematic execution" and "the correction" ?
- define "Niter "
  - **Response.** Defined at first use in Sec. 7.1 as the number of Iterative Bayesian Unfolding iterations.

Sec 7.3
- Would be good to add some references for the unfolding procedure
- Can you quantify better how small is the iteration-to-iteration change ?
- Can you quantify how much is the migration driven separately by the charged particle momentum resolution, and by the soft particles acceptance ?
  I would guess the latter is dominant.
- Fig 10. What are the (huge) error bars on the efficiency plot ?
- Fig 11. The distribution seems in fact to peak above zero, as if there is a bias.
  can you comment on that ?
  - **Response.** You are right on both counts, and there was also a mismatch: the figure is the
    two-dimensional resolution map, while the caption, body text and label all described a
    one-dimensional projection. All three now describe the map, and the unsupported claim of no
    significant bias is removed. The one-dimensional projection and a bias profile exist and can be
    added if you would prefer them.
- Table 6. Several entries in the table are not very clear or have not been defined, like input labels "ntpc7, pt04, ech10, with met  "
  - **Response.** The Table 6 caption now defines each branch and points to Table 7. Previously the labels appeared on p. 25 while their definitions only arrived in Table 7 on p. 28.
- Sec 7.6 previously it was stated that "The ISR correction is not yet implemented in the current analysis and represents a systematic gap relative to the published results;"  but here is seems it is implemented.
  Can you clarify ?
- Why is the ISR uncertainty only taken from the finite MC statistics ?

Sec 8.
- I'm wondering how the MC stat fluctuations (that should be larger than the data ones) are being taken into account. Can you elaborate ?
- Fig 14. Could be nice to show also a zoom of the y axis on both plots to show better the uncertainties in the higher T regions.
- Why does the unfolding uncertainty flip sign several times across the T range ?

8.2
- Fig 16 the charged/EF ratio is interesting, it seems the leading effect is a shift of the charged to lower values:
  is there any understanding for that ?
- Could you perform the No-neutrals xcheck measurement unfolding to the same T particle level definition as the reference analysis, so it is indeed the measurement of the same observable (with a reduced reco particle collection) ?
  This should represent a more meaningful and stringent xcheck of the results.
- 8.3 "at lower thrust where soft-gluon emission and hadronization effects are largest"
  isn't lower thrust where hard gluon emissions are relevant ?
- Fig 17. The difference at low values look mostly like fluctuations. At higher values there is maybe a shift of T to lower values for the new models ?
- 8.5 Do we have any idea of how large / relevant could be the difference of ISR effects evaluated with pythia and koralz ?
- 8.7 could you add some justification to combine in quadrature ?
- Fig 18 : What is the nature of the asymmetric NES uncertainties ?
- Why does the track pt cut uncertainty jump to 12-13 % in the T~1 last bin

Sec 9.1
- "largest discrepancy at the endpoint"  reported to be 1.30+-0.27, but on the plot appear to be at a lower value.
  - **Response.** You are right, and the text is what is wrong rather than your reading of the
    plot. The run that generated the figure gives 1.088 +- 0.229 for that bin.
  - **NEEDS DATA MACHINE.** Root cause traced. Four numbers in the Fig. 20 block disagree with the
    run that generated the figure, and the manuscript's tables and figure come from different
    vintages, so this is a re-derivation rather than a wording fix.

    | claim | paper | run output | status |
    |---|---|---|---|
    | chi2/ndf OmniFold | 0.663 | 1.4305 | no longer quoted |
    | chi2/ndf prior IBU | 0.421 | 1.2164 | no longer quoted |
    | chi2/ndf ALEPH 2004 | 0.361 | 0.2904 | no longer quoted |
    | endpoint ratio | 1.30 +- 0.27 | 1.088 +- 0.229 | still in the text |

    The three chi2/ndf values are removed from the caption rather than corrected, with a note
    there on restoring them from the run summary if wanted. The "Sub-unity chi2/ndf" sentence
    went with them: it was false against the run output and depended on those numbers.

    Verified: the chi2 convention in `build_prelim_uncertainty_summary.py` is
    `sigma2 = yerr1^2 + yerr2^2`, diagonal only, ndf = valid bins -- exactly what the caption
    claims, so the run values are computed as described and the paper's are not from that code.
    The paper's four values trace to `Plans/2026-02-19_thrust_difference_checks.md`, which cites
    `of_ibu_comparison_metrics.json` and misquotes it.

    The endpoint bin is a three-way conflict: Table 9 has ours 1.01 / ALEPH 1.31 (ratio 1.297,
    matching the text), while the run's `binning.csv` bin 50 has ours 1.2057 (ratio 1.087,
    matching the JSON). So the text and Table 9 agree with each other, the run outputs agree with
    each other, and the two groups disagree.

    Two knock-on effects: `Results.tex:32` "Sub-unity chi2/ndf values reflect the conservative
    uncertainty model" is false against the run output, where two of three exceed unity and the
    reading inverts to tension with the prior results; and Table 9's endpoint value needs
    regenerating, not editing.

    Fix requires one run regenerating tables, figure and metrics together. Deliberately not
    corrected in text, which would leave Table 9 contradicting it.

- Fig 19. How is it that the ALEPH measurements seem to have larger uncertainties over most of the bins ?  Can you comment on that ?
- Table 9 : Are the ALEPH uncertainties the same as plotted in Fig 19 ?
  Just looking at the endpoint bin the table quotes 15% but the plot seems to show 20-25%
- Fig 21. Would it be better to have these plots with the y axis upwards as usual (like in Fig 20) ?
- Fig 22-23 visual information in these plots is very scarce,  they are almost completely uniform, can you try to improve that  ?
