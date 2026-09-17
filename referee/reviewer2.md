Dear Authors, Thanks for this very interesting work.

- In general it seems to me the text has similar statements repeated across the paper,
  - We worked on fixing this.

- Some aspects and elements are discussed in the initial sections before being introduced and defined.
  - Addressed in the initial sections and more specific comments followed up in later comments.




---------------------------------------------
Abstract
- "entirely" seems in contrast with "under expert physicist direction"
  - Reworded.

- "spectrum" > "thrust spectrum"
  - Changed.





---------------------------------------------
Sec 1
- "ensure robust control " is not  very clear, can you elaborate that ?
  Or maybe state something simpler like  "keep the impact of theoretical systematic uncertainties at the level of the experimental uncertainties" ?
  - Updated the first paragraph

Lessons from AI–Physicist Collaboration
- I find the statements in these two paragraphs a bit vague, and maybe repetitive. Could you try to specify better what are the methods, lessons, prospects, ..
 - Tried to improve this, but maybe you have more suggestions.





---------------------------------------------
Section 3
- define "MC" here
  - Expanded to "Monte Carlo (MC)" at first use, in Sec. 3.

- It is not clear what are the elements, for example in the item list of 3.1, that are not already currently used routinely by many analyst in the HEP community. It is important to emphasise what is new and distinctive in this work.
  - The goal of this list is that the agent controls known elements which the HEP community uses all the time. There are not new underlying tools/elements, but rather the new thing is that the agent can manipulate and orchestrate all existing tools.

- Again some repetition of previous statements, like the graduate student analogy.
  - Removed; the analogy is now made once, in Sec. 2.

- Would be good to define pwflag and/or to point to sec 6.1
  - Added a pointer to Sec. 6.1 and Table 2 at the first use, in Sec. 2. Sec. 6.1 had no label, so it could not previously be referenced; one has been added.

- A reference for miniDST would be good to add.
  - Done added reference to https://aleph-new.docs.cern.ch and cleaned up use of miniDST.

Sec 3.2
- Would be nicer to have the four categorie in a enumerated list, or on a table.
  - Done; Sec. 3.2 now uses a list, matching Sec. 3.1 and Sec. 3.3.

Sec 3.3
- Not clear what the chi2 is and what the "iterations 4–6." are.  Some more informations would be useful.
  - This information was not needed there and better to have in the analysis method section.

- clarify what "pathological bins" are
  - Removed this confusing text.

- clarify what are the "checksums of key outputs"
  - Done.

- "discrepancies between expected and observed outputs are flagged before any result is promoted": this is repeated several times, but it is not very clear how it is implemented. It also seems a procedure that would have a worrisome strong  bias to produce "expected" results. Would be good to elaborate also on that aspect.
  - This is a good point. We believe that the question of verification is unsolved problem generally and extremely important going forward. We clarified the sentence to say that we cheked the results before allowing the analysis to continue, removing the mention of expected.





---------------------------------------------
Sec 4
- for the track momentum resolution would be better to add the multiple scattering term that is important also at pT~10 GeV
  - Done.

- The constant terms for the energy resolutions would also be better to provide.
  - Done.





---------------------------------------------
Sec 5
- "corresponds to an integrated luminosity of" Add information on the size of the simulated sample
  - Done.

- Clarify if the contributions from background sources (as tau pair productions) have been considered.
  - Sentence added.

- Specify the lifetime definition for the "stable-hadron level" definition (lifetime > ? )
  - Removed this text and instead cited aleph documentation. This cut is not used in our analysis.

- Would it be better to distinguish the detector-level data and MC with different labels (like tdata and tmc)  ?
  - Both detector-level samples are stored in trees named `t`, so we prefer to leave it as is and label the curves *Data reco* and *MC reco* throughout. We agree with your comment for future works.




---------------------------------------------
Sec 6
- Table 2 . Suggest to modify the text in : 0 charged hadrons, 1 electrons (tracker + ECAL category), 2 muons (tracker + muon category)
  -  Adopted verbatim. The previous labels called pwflag 1 and 2 both "charged leptons", which did not distinguish them.

- Would be good to explain what are the tracks d0 and z0 and how they are evaluated (wrt to which vertex)
  - Defined in Sec. 6.2 as the transverse and longitudinal distance of closest approach of the track helix to the per-event reconstructed primary vertex. Both are read as stored in the archived ALEPH reconstruction and are not recomputed here. $N_{\mathrm{TPC}}$, the number of TPC coordinates on the track, is defined alongside, and Sec. 4, where they first appear, now points there.

- Table 3 maybe should clarify if and how these criteria are applied at gen level
  - They are not. The Table 3 criteria are imposed on the reconstructed collection only; the generator-level particles of the same events are retained without them. Now stated with Table 3.

- Table 4 : why are inactive cuts listed ? Explain their role.
  - Those were used as cross checks at the time of analysis so the agent chose to list them. They are now removed.

Sec 6.3
- Fig 1 Can you comment on why we have enhancements at costheta=0 (also for gen) ?
  - Thanks for pointing this out. This is actually an artifact of the fixed floating point precision in the reprocessing of the archived sample. It does not have a significant effect on the result and will be fixed in the future.

- Fig 1 What are the peaks at p=E=45 GeV and why are they not there at gen level ?
  - This is a reco-level MC effect in the archived sample that is not fully understood and under active study. The impact of removing the peak was checked and is negligible.

- Fig 3 the phi structure, only at gen level, is suprising, can you comment on that ?
  - This is believed to be artifact of how the archived MC was processed and is being investigated still. We checked the impact of removing this contribution and the impact is negligible. 

- Fig 4 : the peaks here at E~p=45 GeV for V0 collection should also be explained (and why they are only in the reco)
  - This is a reco-level MC effect in the archived sample that is not fully understood and under active study. The impact of removing the peak was checked and is negligible.

- page 18 : comments on fig 1 : "The NTPC distribution shows good overall agreement between generators, with small differences between JETSET and modern generators" but the figure shows only one MC prediction. It is also not clear why NTPC would be a sensitive observable for that.
  - Thanks for catching this. It is now fixed.
  
- There are other comments in the text referring to comparisons to different generators for other figures 2,3,4,5,6
  that are not visible in the figures.
  - Removed. Those passages were wrong: Pythia 8, Herwig and Sherpa are generated at particle level only, so they have no reconstructed objects and cannot appear in the pwflag figures. They enter the analysis solely as event-level reweighting for the theory uncertainty. Six such passages are corrected.

- Fig 2,3 : "Differences between the archived MC and modern generators (Pythia 8, Herwig, Sherpa) are visible in.. "
  - Removed; only the archived MC is shown in these figures.

- Fig 4 " "Generator differences are more visible than for charged tracks, reflecting differences in strange-particle production modeling" ... "The ϕ spectrum (Fig. 5) shows a modulation in the generator-level distribution" I'm guessing all this discussion on generators across pages 18-19-20 refers to some other figures.
  - Yes thank you for the catch. The statements are re-written. 

- The comment "(see Sec. 6.3)" is awkward as it is written inside Sec 6.3
  - Removed.

- Fig 7: It would be interesting to see the MC (no-sel) prediction to justify the cut.
  - That is shown for the generator level spectrum in Figure 6. Figure 7 and Figure 8 are now removed.

Sec 6.4
- Fig 9 : It seems surprising that there seems to be almost no difference in the Gen and GenBefore predictions  except for the theta distribution. The GenBefore distributions should have larger particle multiplicities and total energy.
  - "Before" refers to the detector-level event selection, not to particle-level cuts; the two trees receive identical particle-level treatment, the kinematic selections being applied at detector level only. In the archived ntuples \texttt{tgen} is an exact subset of \texttt{tgenBefore}, and the missing events are removed almost entirely by polar-angle acceptance, with only weak dependence on multiplicity, so $\cos\theta_{\mathrm{Sph}}$ is the only panel where the two clearly separate; a small depletion also survives in the sparse low-$E_{\mathrm{Ch}}$ tail. Stated in Sec. 6.4.

- What is also strange is the up-down oscillating pattern in the MC/Data for the (upper-left) Ntrk plot : how is that happening ?
  - The modulation is in the generator-level curves, not in data or MC reco. This is perhaps a confusing plot because Ntrk is really a detector level quantity while at gen this is really N_charged particles. Since the incoming state is charge neutral, then the charged particles are made in pairs and charge conservation holds. So at gen level charge conservation requires that the particles are made in pairs at gen level so this makes a the gen plot only have filled even bins. The odd bins then result from ISR events where scattered leptons can be stored as a final state particle or other such features.

- define "IBU" on page 20
  - IBU is defined in Sec. 2: "Iterative Bayesian Unfolding (IBU) implemented in RooUnfold".





---------------------------------------------
Sec 7
- explain better  what is  "systematic execution" and "the correction" ?
  - Clarified in the text.

- define "Niter "
  - Defined at first use in Sec. 7.1 as the number of Iterative Bayesian Unfolding iterations.

Sec 7.3
- Would be good to add some references for the unfolding procedure
  - Added references where they are mentioned.

- Can you quantify better how small is the iteration-to-iteration change ?
  - Added numbers quoting the spread from the iteration variation.

- Can you quantify how much is the migration driven separately by the charged particle momentum resolution, and by the soft particles acceptance? I would guess the latter is dominant.
  - Yes, we agree with your assessment that the soft particles drive the migration effects. The figures for the momentum, translated to energy using pion mass assumption, and angular resolutions are shown in Figures 8 of https://inspirehep.net/literature/2922431. The charged particle momentum resolution is very good at moderate momentum, as also reported by the charged particle momentum resolution formula derived by ALEPH. The angular resolution is more smeared throughout the spectrum. Therefore, our understanding is that the soft particle resolution is the dominant driver of the migration. Quantitative measure of the relative contribution to the migration are not reported until the archived detector simulation is available for further studies.

- Fig 10. What are the (huge) error bars on the efficiency plot ?
  - The uncertainty was propagated as if numerator and denominator were independent, but the numerator is a subset of the denominator. Using binomial uncertainties, the efficiency plateau is $0.931 \pm 0.003$. The figure has been regenerated.

- Fig 11. The distribution seems in fact to peak above zero, as if there is a bias. can you comment on that ?
  - Yes a bias is seen at the detector level which broadens the thrust distribution. The measurements in general will act to broaden the thrsut since it makes the events more isotropic, leading to a bias towards higher thrust values. The caption is updated to be more concise as well.

- Table 6. Several entries in the table are not very clear or have not been defined, like input labels "ntpc7, pt04, ech10, with met  "
  - Cleaned this up so that there is a paragraph with bulleted list defining the labels and table 7 is deleted.

- Sec 7.6 previously it was stated that "The ISR correction is not yet implemented in the current analysis and represents a systematic gap relative to the published results;"  but here is seems it is implemented. Can you clarify ?
  - The Sec. 5 sentence was stale and has been corrected. The ISR correction is applied, as Sec. 7.6 describes.

- Why is the ISR uncertainty only taken from the finite MC statistics ?
  - This was done for simplicity and we agree that for a full thrust result the ISR uncertainty would need to include MC variations or a data-driven uncertainty.




---------------------------------------------
Sec 8.
- I'm wondering how the MC stat fluctuations (that should be larger than the data ones) are being taken into account. Can you elaborate ?
  - Thank you for pointing this point. The MC statistical uncertainty was only included from the uncertainty on the generator level archived MC used for the hadronic event selection correct. Now a toys based bootstrap is implemented to derive an uncertainty on the response matrix as well.

- Fig 14. Could be nice to show also a zoom of the y axis on both plots to show better the uncertainties in the higher T regions.
  - Figure updated.

- Why does the unfolding uncertainty flip sign several times across the T range ?
  - The $N_{\mathrm{iter}}=4$ and $6$ passes bracket the nominal, so their shifts have
    opposite sign, and the bin-to-bin alternation at low thrust is the anti-correlation that
    regularization induces between neighbouring bins. Now stated in Sec. 8.

8.2
- Fig 16 the charged/EF ratio is interesting, it seems the leading effect is a shift of the charged to lower values. is there any understanding for that ?
  - We agree this is interesting and will be followed up in further works. Our current understanding is that the charged particle only spectrum is broader because part of the event is not reflected in the observable so that broadens the topology. 

- Could you perform the No-neutrals xcheck measurement unfolding to the same T particle level definition as the reference analysis, so it is indeed the measurement of the same observable (with a reduced reco particle collection) ? This should represent a more meaningful and stringent xcheck of the results.
  - Maybe there is some confusion in the text. The cross check already unfolds both versions to the same particle level spectrum at generator level. 

- 8.3 "at lower thrust where soft-gluon emission and hadronization effects are largest". isn't lower thrust where hard gluon emissions are relevant ?
  - You are right, the attribution was inverted. Low thrust is the multi-jet region where hard, wide-angle emission dominates; the text now says so. 

- Fig 17. The difference at low values look mostly like fluctuations. At higher values there is maybe a shift of T to lower values for the new models ?
  - We agree with that generation interpretation. We are actively investigating the slight shift at high T.

- 8.5 Do we have any idea of how large / relevant could be the difference of ISR effects evaluated with pythia and koralz ?
  - From quick checks of privately generated MC this amounts to order ~10% in the peak region. For this agentic study pythia8 was ok to use, but for the full precision measurement we will use KKMCee which is the modern implementation of koralz and has higher perturbative accuracy.

- 8.7 could you add some justification to combine in quadrature ?
  - Included sentences: The quadrature sum is used since the components originate from distince sources and the covariance cross terms are expected to be small. This will be further assessed in follow up event shape measurements.

- Fig 18 : What is the nature of the asymmetric NES uncertainties ?
  - The scale variation is symmetric by construction, so the asymmetry is a non-linear response rather than an asymmetric input. It is concentrated at low thrust; across the fit window the up and down branches are much closer in size, as Fig. 18 shows. The variation scales neutral momenta and leaves the neutral multiplicity essentially unchanged, so it is not driven by objects migrating across the selection threshold.

- Why does the track pt cut uncertainty jump to 12-13 % in the T~1 last bin
  - Raising the threshold removes soft tracks, which makes events appear more collimated and moves a substantial fraction of them into the highest thrust bin. That bin sits against the kinematic boundary, so the migration is a large fractional change there. The branch is small across the fit window and larger again in the sparsely populated low-thrust tail, where the same soft-track removal acts on very few events.




---------------------------------------------
Sec 9.1
- "largest discrepancy at the endpoint"  reported to be 1.30+-0.27, but on the plot appear to be at a lower value.
  - Fixed.

- Fig 19. How is it that the ALEPH measurements seem to have larger uncertainties over most of the bins ?  Can you comment on that ?
  - The uncertainties shown in the ratio were the quadrature sum of the ALEPH and the agentic measurement since it was automatically propagated in the ratio. This is fixed now. In general the uncertainties are of comparable scale. We continue to investigate differences that can originate from the archived data processing or the handling of the theory uncertainties. 

- Table 9 : Are the ALEPH uncertainties the same as plotted in Fig 19 ? Just looking at the endpoint bin the table quotes 15% but the plot seems to show 20-25%
  - The table had the correct uncertainties. The ratio panel in Figure 19 was showing aleph/ours and the points had the quadrature sum of the two measurement errors. This is fixed.

- Fig 21. Would it be better to have these plots with the y axis upwards as usual (like in Fig 20) ?
  - Updated. 

- Fig 22-23 visual information in these plots is very scarce,  they are almost completely uniform, can you try to improve that  ?
  - Removed, leaving only the correlation matrices that are richer.