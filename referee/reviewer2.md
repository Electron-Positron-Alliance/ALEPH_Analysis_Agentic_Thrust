Dear Authors, Thanks for this very interesting work.

- In general it seems to me the text has similar statements repeated across the paper,
- Some aspects and elements are discussed in the initial sections before being introduced and defined.
  - **Response.** Partly addressed. MC, pwflag, $N_{\mathrm{iter}}$, $d_0$/$z_0$/$N_{\mathrm{TPC}}$ and the stable-hadron lifetime cut are now defined at or before first use, with forward pointers where the term first appears earlier than its definition. The remaining instances are covered by your specific comments below.

Abstract
- "entirely" seems in contrast with "under expert physicist direction"
- "spectrum" > "thrust spectrum"
  - **Response.** Changed.

Sec 1
- "ensure robust control " is not  very clear, can you elaborate that ?
  Or maybe state something simpler like  "keep the impact of theoretical systematic uncertainties at the level of the experimental uncertainties" ?
  - **Response.** Adopted your phrasing. The sentence now reads "in order to keep the impact of
    theoretical systematic uncertainties at the level of the experimental uncertainties, so that
    potential new-physics anomalies can be interpreted reliably", which also drops the
    overclaiming "ensure".

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
  - **Response.** Removed; the analogy is now made once, in Sec. 2.
- Would be good to define pwflag and/or to point to sec 6.1
  - **Response.** Added a pointer to Sec. 6.1 and Table 2 at the first use, in Sec. 2. Sec. 6.1 had no label, so it could not previously be referenced; one has been added.
- A reference for miniDST would be good to add.
  - **NEEDS AUTHOR INPUT.** There is no miniDST or DST entry anywhere in `biblio.bib`, and we are
    not able to pick the right one: it is either an ALEPH internal note or the open-data record
    DOI. miniDST is used in Sec. 2 and Sec. 3.2 and remains uncited.

Sec 3.2
- Would be nicer to have the four categorie in a enumerated list, or on a table.
  - **Response.** Done; Sec. 3.2 now uses a list, matching Sec. 3.1 and Sec. 3.3.

Sec 3.3
- Not clear what the chi2 is and what the "iterations 4–6." are.  Some more informations would be useful.
  - **Response.** Clarified: it is the refolded-to-measured $\chi^2/\mathrm{ndf}$, and 4--6 are the
    regularization variation passes about the nominal $N_{\mathrm{iter}}=5$.
- clarify what  "pathological bins" are
  - **Response.** Defined at that point as bins whose total uncertainty exceeds the spectrum
    itself.
- clarify what are the  "checksums of key outputs"
  - **Response.** Defined as hashes of the exported spectra and covariance files, used to confirm
    that a rerun reproduces a previous result byte for byte.
- "discrepancies between expected and observed outputs are flagged before any result is promoted" :
  this is repeated several times, but it is not very clear how it is implemented.
  It also seems a procedure that would have a worrisome strong  bias to produce "expected" results.
  Would be good to elaborate also on that aspect.

Sec 4
- for the track momentum resolution would be better  to add the multiple scattering term that is important also at pT~10 GeV
  - **Response.** Both added, with the coefficients taken from the ALEPH detector papers already
    cited in Sec. 4. The transverse-momentum resolution now reads
    $\delta p_T/p_T = 6\times10^{-4}\,p_T \oplus 0.005$ (GeV/$c$), the second term being the
    multiple-scattering contribution you identify, and the ECAL resolution now carries its
    constant term, $0.18/\sqrt{E} + 0.009$. The HCAL resolution has no constant term in that
    reference.
  and dominates at lower pT. I should be deltaPt/pt = 5 x 10-3.
- The constant terms for the energy resolutions would also be better to provide.
  - **Response.** See above; the ECAL constant term is now given.

Sec 5
- "corresponds to an integrated luminosity of"
  Add information on the size of the simulated sample
  - **Response.** Both are already given: Sec. 5 states approximately 40~pb$^{-1}$ and
    approximately 1.33 million selected hadronic events, and Table 1 gives the per-sample counts.
    While checking this we found Sec. 5 quoted the MC total as if it were the selected count;
    corrected to 752k, matching Table 1.
  - **NEEDS DATA MACHINE.** Event counts have since been verified against the raw data and all
    match; 40~pb$^{-1}$ still has no source. Detail in the marker above the sentence in
    `sections/Datasets.tex`.
- Clarify if the contributions from background sources (as tau pair productions) have been considered.
- Specify the lifetime definition for the "stable-hadron level" definition (lifetime > ? )
  - **Response.** Sec. 5 now states the criterion in the prose, proper decay length $c\tau > 10$~mm, where the particle-level definition is introduced. It was previously given only as a row in Table 5.
  - **NEEDS DATA MACHINE before submission.** The $c\tau > 10$~mm value is pre-existing repo content, relocated rather than established here, and has no citation or in-repo code backing it. Confirm (a) that the generator-level selection really applies it, and (b) whether it is our choice or inherited from ALEPH's published particle-level definition, and cite accordingly. Batches with the $d_0$/$z_0$ check above -- both need the analysis code. Mirrored as a comment above the sentence in `sections/Datasets.tex`.
- Would it be better to distinguish the detector-level data and MC with different labels (like tdata and tmc)  ?
  - **Response.** Both detector-level samples are stored in trees named `t`, so rather than invent
    tree names we state that and label the curves *Data reco* and *MC reco* throughout.

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
  - **Response.** They are not. The Table 3 criteria are imposed on the reconstructed collection
    only; the generator-level particles of the same events are retained without them, so the
    particle-level target is set by the stable-hadron criterion alone. Now stated with Table 3.
- Table 4 : why are inactive cuts listed ? Explain their role.
  - **Response.** The caption now states that the last two rows reject no events in the nominal configuration, are listed so the nominal setup is fully specified, and are the hooks used by the missing-momentum variation in Table 7.

Sec 6.3
- Fig 1 Can you comment on why we have enhancements at costheta=0 (also for gen) ?
  What are the peaks at p=E=45 GeV and why are they not there at gen level ?
- Fig 3 the phi structure, only at gen level, is suprising, can you comment on that ?
- Fig 4 : the peaks here at E~p=45 GeV for V0 collection should also be explained (and why they are only in the reco)
- page 18 : comments on fig 1 : "The NTPC distribution shows good overall agree-
  - **Response.** Right on both counts. Only the archived JETSET sample is shown, and
    $N_{\mathrm{TPC}}$ is a detector hit count rather than a generator observable; the sentence is
    rewritten accordingly.
  ment between generators, with small differences between JETSET and modern generators"
  but the figure shows only one MC prediction.
  It is also not clear why NTPC would be a sensitive observable for that.
- There are other comments in the text referring to comparisons to different generators for other figures 2,3,4,5,6
  - **Response.** Removed. Those passages were wrong: Pythia 8, Herwig and Sherpa are generated
    at particle level only, so they have no reconstructed objects and cannot appear in the
    pwflag figures. They enter the analysis solely as event-level reweighting for the theory
    uncertainty. Five such passages are corrected.
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
  - **Response.** "Before" refers to the detector-level event selection, not to particle-level cuts;
    the two trees receive identical particle-level treatment, the kinematic selections being applied
    at detector level only. In the archived ntuples \texttt{tgen}
    is an exact subset of \texttt{tgenBefore}, and the missing events are removed almost entirely
    by polar-angle acceptance, with only weak dependence on multiplicity, so
    $\cos\theta_{\mathrm{Sph}}$ is the only panel where the two clearly separate; a small
    depletion also survives in the sparse low-$E_{\mathrm{Ch}}$ tail. Stated in Sec. 6.4.
- What is also strange is the up-down oscillating pattern in the MC/Data for the (upper-left) Ntrk plot : how is that happening ?
  - **Response.** The modulation is in the generator-level curves, not in data or MC reco. Charge
    conservation fixes the parity of the charged multiplicity to that of the summed charge, which
    vanishes for most generated events; the conversion-electron cleaning removes one track per
    identified pair and dilutes the effect to the size seen. Track inefficiency randomizes the parity
    at detector level. Noted in Sec. 6.4.
  - **AUTHOR DECISION NEEDED.** That cleaning drops the pair from the saved particle list but leaves
    one member in $N_{\mathrm{trk}}$, $E_{\mathrm{Ch}}$ and $E_{\mathrm{vis}}$, so the selection
    counters and the thrust particle list differ by one track per pair. Confirm the intent.
- define "IBU" on page 20
  - **Response.** IBU is already defined, at first use in Sec. 2: "Iterative Bayesian Unfolding (IBU) implemented in RooUnfold". No change made.

Sec 7
- explain better  what is  "systematic execution" and "the correction" ?
  - **Response.** The Sec. 7 lead-in now names them: the execution of the systematic variation
    branches, and the post-unfolding hadronic and ISR corrections with the covariance assembly.
- define "Niter "
  - **Response.** Defined at first use in Sec. 7.1 as the number of Iterative Bayesian Unfolding iterations.

Sec 7.3
- Would be good to add some references for the unfolding procedure
  - **Response.** Sec. 7.3 previously contained no citations. The iteration formula now cites
    D'Agostini's original method paper together with the later note on improvements, and
    RooUnfold cites Adye. OmniFold is cited at first use in Sec. 3.3 and at the comparisons in
    Sec. 9.1 and App. B.
- Can you quantify better how small is the iteration-to-iteration change ?
- Can you quantify how much is the migration driven separately by the charged particle momentum resolution, and by the soft particles acceptance ?
  I would guess the latter is dominant.
- Fig 10. What are the (huge) error bars on the efficiency plot ?
  - **Response.** The uncertainty was propagated as if numerator and denominator were
    independent, but the numerator is a subset of the denominator. Using binomial uncertainties,
    the efficiency plateau is $0.931 \pm 0.003$. The figure has been regenerated.
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
  - **Response.** The Sec. 5 sentence was stale and has been corrected. The ISR correction is
    applied, as Sec. 7.6 describes.
  - **NEEDS DATA MACHINE before submission.** With Sec. 5 corrected, the remaining gap is that
    Sec. 8.7 writes the total with a $\Delta_{\mathrm{ISR}}$ term while Table 8, Table 6's
    formula and Fig. 18's legend carry no ISR component. Regenerating those needs the
    isr0/isr1 samples.
  Can you clarify ?
- Why is the ISR uncertainty only taken from the finite MC statistics ?

Sec 8.
- I'm wondering how the MC stat fluctuations (that should be larger than the data ones) are being taken into account. Can you elaborate ?
- Fig 14. Could be nice to show also a zoom of the y axis on both plots to show better the uncertainties in the higher T regions.
- Why does the unfolding uncertainty flip sign several times across the T range ?
  - **Response.** The $N_{\mathrm{iter}}=4$ and $6$ passes bracket the nominal, so their shifts have
    opposite sign, and the bin-to-bin alternation at low thrust is the anti-correlation that
    regularization induces between neighbouring bins. Now stated in Sec. 8.

8.2
- Fig 16 the charged/EF ratio is interesting, it seems the leading effect is a shift of the charged to lower values:
  is there any understanding for that ?
- Could you perform the No-neutrals xcheck measurement unfolding to the same T particle level definition as the reference analysis, so it is indeed the measurement of the same observable (with a reduced reco particle collection) ?
  This should represent a more meaningful and stringent xcheck of the results.
  - **Response.** That is already what the cross-check does. Both the energy-flow and
    charged-only spectra are unfolded to the same energy-flow particle level; only the
    reconstructed particle collection differs. We had described it as using separate response
    matrices per particle-level definition, which was incorrect, and Sec. 8.2 and the Fig. 16
    caption are corrected accordingly.
  - **AUTHOR DECISION NEEDED.** Verified in the code and the run output: only reco and data
    inputs are varied, never the generator-level file, and the generator-level histograms are
    bit-identical between the two unfoldings. The central-range shift is therefore a
    sensitivity to neutral-object reconstruction against a single particle-level target, not a
    difference of observables -- which inverts the argument Sec. 8.2 currently makes from it.
    The shift itself is confirmed at the quoted magnitude. Rewriting that conclusion is a
    physics decision; the factual claim has been corrected and the interpretation left for the
    authors. Mirrored in `sections/SystematicUncertainties.tex`.
- 8.3 "at lower thrust where soft-gluon emission and hadronization effects are largest"
  - **Response.** You are right, the attribution was inverted. Low thrust is the multi-jet region
    where hard, wide-angle emission dominates; the text now says so.
  isn't lower thrust where hard gluon emissions are relevant ?
- Fig 17. The difference at low values look mostly like fluctuations. At higher values there is maybe a shift of T to lower values for the new models ?
- 8.5 Do we have any idea of how large / relevant could be the difference of ISR effects evaluated with pythia and koralz ?
- 8.7 could you add some justification to combine in quadrature ?
- Fig 18 : What is the nature of the asymmetric NES uncertainties ?
  - **Response.** The scale variation is symmetric by construction, so the asymmetry is a
    non-linear response rather than an asymmetric input. It is concentrated at low thrust; across
    the fit window the up and down branches are much closer in size, as Fig. 18 shows. The
    variation scales neutral momenta and leaves the neutral multiplicity essentially unchanged,
    so it is not driven by objects migrating across the selection threshold.
- Why does the track pt cut uncertainty jump to 12-13 % in the T~1 last bin
  - **Response.** Raising the threshold removes soft tracks, which makes events appear more
    collimated and moves a substantial fraction of them into the highest thrust bin. That bin
    sits against the kinematic boundary, so the migration is a large fractional change there.
    The branch is small across the fit window and larger again in the sparsely populated
    low-thrust tail, where the same soft-track removal acts on very few events.

Sec 9.1
- "largest discrepancy at the endpoint"  reported to be 1.30+-0.27, but on the plot appear to be at a lower value.
  - **Response.** You are right that the two disagree, but neither number is wrong: Table 9 and
    the text quote the spectrum before the ISR correction, and the figure shows it after. The
    endpoint bin is 1.008 pre-ISR and 1.206 post-ISR, giving ALEPH/ours ratios of 1.30 and 1.09.
    We will state the correction stage explicitly for every spectrum, table and figure.
  - **NEEDS DATA MACHINE.** Verified by rerunning from raw data; deferred until the ISR code is
    available, since the wording depends on it. Detail and the separate, still-unexplained
    chi2/ndf discrepancy are in the marker above the figure block in `sections/Results.tex`.

- Fig 19. How is it that the ALEPH measurements seem to have larger uncertainties over most of the bins ?  Can you comment on that ?
- Table 9 : Are the ALEPH uncertainties the same as plotted in Fig 19 ?
  Just looking at the endpoint bin the table quotes 15% but the plot seems to show 20-25%
- Fig 21. Would it be better to have these plots with the y axis upwards as usual (like in Fig 20) ?
- Fig 22-23 visual information in these plots is very scarce,  they are almost completely uniform, can you try to improve that  ?
