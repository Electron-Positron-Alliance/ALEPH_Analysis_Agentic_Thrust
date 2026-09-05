Dear Authors, Thanks for this very interesting work.

- In general it seems to me the text has similar statements repeated across the paper,
- Some aspects and elements are discussed in the initial sections before being introduced and defined.

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
- It is not clear what are the elements, for example in the item list of 3.1,
  that are not already currently used routinely by many analyst in the HEP community.
  It is important to emphasise what is new and distinctive in this work.
- Again some repetition of previous statements, like the graduate student analogy.
- Would be good to define pwflag and/or to point to sec 6.1
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
- Clarify if the contributions from background sources (as tau pair productions) have been considered.
- Specify the lifetime definition for the "stable-hadron level" definition (lifetime > ? )
- Would it be better to distinguish the detector-level data and MC with different labels (like tdata and tmc)  ?

Sec 6
- Table 2 . Suggest to modify the text in :
  0 charged hadrons
  1 electrons (tracker + ECAL category)
  2 muons (tracker + muon category)
- Would be good to explain what are the tracks d0 and z0 and how they are evaluated (wrt to which vertex)
- Table 3 maybe should clarify if and how these criteria are applied at gen level
- Table 4 : why are inactive cuts listed ? Explain their role.

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
- Fig 7 :  It would be interesting to see the MC (no-sel) prediction to justify the cut.

Sec 6.4
- Fig 9 : It seems surprising that there seems to be almost no difference in the Gen and GenBefore predictions  except for the theta distribution.
  The GenBefore distributions should have larger particle multiplicities and total energy.
- What is also strange is the up-down oscillating pattern in the MC/Data for the (upper-left) Ntrk plot : how is that happening ?
- define "IBU" on page 20

Sec 7
- explain better  what is  "systematic execution" and "the correction" ?
- define "Niter "

Sec 7.3
- Would be good to add some references for the unfolding procedure
- Can you quantify better how small is the iteration-to-iteration change ?
- Can you quantify how much is the migration driven separately by the charged particle momentum resolution, and by the soft particles acceptance ?
  I would guess the latter is dominant.
- Fig 10. What are the (huge) error bars on the efficiency plot ?
- Fig 11. The distribution seems in fact to peak above zero, as if there is a bias.
  can you comment on that ?
- Table 6. Several entries in the table are not very clear or have not been defined, like input labels "ntpc7, pt04, ech10, with met  "
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
- Fig 19. How is it that the ALEPH measurements seem to have larger uncertainties over most of the bins ?  Can you comment on that ?
- Table 9 : Are the ALEPH uncertainties the same as plotted in Fig 19 ?
  Just looking at the endpoint bin the table quotes 15% but the plot seems to show 20-25%
- Fig 21. Would it be better to have these plots with the y axis upwards as usual (like in Fig 20) ?
- Fig 22-23 visual information in these plots is very scarce,  they are almost completely uniform, can you try to improve that  ?
