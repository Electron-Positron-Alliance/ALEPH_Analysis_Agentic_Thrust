# Referee 1 — comments, assessment and response

Each entry keeps the referee's wording verbatim in the blockquote. `Assessment` is what we found when we checked the claim against the source and the code. `Response to referee` is the text destined for the response letter. `Change` records the PR/commit that implements it.

## Status

| status | count |
|---|---|
| Fixed | 2 |
| Partly fixed | 2 |
| No change needed | 1 |
| Open - easy | 4 |
| Open - substantive | 10 |
| Open - needs data machine | 2 |
| **total** | **21** |

---

### R1-01 — Open - substantive

> This paper presents a re-analysis of ALEPH entirely done with AI agents. The result is impressive, even if the quality of the AI-based publication is not great. Given that the most interesting part is not concerning physics, but the fact that the AI-agents did the work, it would be nice to have an evaluation, with some metric, of the amount of human intervention.

**Assessment.** TODO (substantive). Nothing quantitative exists in the paper today. Buildable from `manuscript local save/Plans/` without new data: 20 dated review artifacts (2026-02-13 to 2026-03-05), a P0/P1 defect ledger with file:line and fix status, two agent findings explicitly retracted on verification (BUG-1, CODE-4) giving a false-positive rate, and an S0/S1 gate decision (`Conditional-go` / `No-go (theory-facing release)`). Must separate physics interventions from cosmetic ones. See §7 of REVIEW_TRIAGE_2026-09-05.md.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-02 — Open - needs data machine

> Here are some comments about the text itself:
> You should write ALEPH archived data on all histograms

**Assessment.** TODO (needs data machine). Currently only on Fig. 18's four panels, via `ALEPH_LABEL` at `per_bin_uncertainty_plot.py:123`. Requires re-running the plotting scripts. Note the label also renders as "e + e 91.2 GeV" — the √s symbol is missing.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-03 — Open - substantive

> page 1 precision QCD is not where theoretical uncertainties become limiting.

**Assessment.** TODO (substantive). Physics framing objection to the sentence following the one we reworded; needs a considered reply, not a reword.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-04 — Open - easy

> page 2 how the physicists brainstormed the AI Agent ? In English ?

**Assessment.** TODO (easy). Answer literally: natural-language English prompts, corpus described in §3.2. One sentence.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-05 — Fixed

> page 5 lines 13-14 Section 1 was before, not in the remainder of the document

**Assessment.** Fixed (PR 02). Dropped the Sec. 1 entry; the list now starts at Sec. 3.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-06 — Fixed

> page 5 start of Section 3 “This internal note” if you wish to publish it is a paper (this error is recurring)

**Assessment.** Fixed (PR 01). 16 occurrences reworded across 8 files. One instance deliberately left: `ChallengesAndLimitations.tex:4` "Because this document is an internal note rather than a final publication…" — that is the framing of Sec. 11, which your last comment says should not be published at all, so a word swap would leave it incoherent.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-07 — Open - easy

> page 6 lines 4 - 5 this is a repetition of page 3

**Assessment.** TODO (easy). Could not verify against printed page numbers; needs a look at the PDF. The graduate-student analogy does repeat between §2 and §3.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-08 — Open - substantive

> page 8 line 5 I did not catch the proof of concept, where is it ?

**Assessment.** TODO (substantive). The title promises a proof of concept but the paper never states the success criterion. Needs an explicit sentence.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-09 — Open - easy

> page 9 line 2, quote table 2 here

**Assessment.** TODO (easy). Add a `\ref` to Table 2 at the start of §5.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-10 — Open - substantive

> page 9 “Two generator-level corrections are applied after unfolding” : it seems that the second (ISR) is not applied from what is written at the end of the page.

**Assessment.** TODO (substantive, and worse than you flag). `Datasets.tex:20` says the ISR correction is "not yet implemented"; §7.6, §8.5, §9 and the Conclusion all say it is. Beyond that, §8.7 writes a six-component total including Δ²_ISR, but Table 8 has no ISR column, Table 6's formula omits it, Fig. 18's legend omits it, and App. A's pseudocode omits it. We verified Table 8's totals reproduce across all 44 rows *without* ISR. So the paper writes a six-component total and tabulates five.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-11 — Open - substantive

> page 9 two lines after 5.1 I do not understand what you mean, unless it is something obvious, if you do not do unfolding and do not use the generator for that, you are not generator dependent …

**Assessment.** TODO (substantive). Needs rewrite.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-12 — Open - easy

> page 9-10 what is it a “tree” in this context ?

**Assessment.** TODO (easy). ROOT TTree — the `t` / `tgen` / `tgenBefore` branches. Define on first use.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-13 — Open - needs data machine

> table 4 it seems that the Sphericity axis acceptance cut is sculpting the thrust distribution, could you comment about that ?

**Assessment.** TODO (needs data machine — largest job on the list). Legitimate concern: the sphericity axis is strongly correlated with the thrust axis, and Fig. 10 (right) shows the miss term concentrated at low thrust, exactly where sculpting would bite. There is currently **no** `cosThetaSph` variation — `runAnalyze.py:86-143` defines only `no_event_sel, nominal, ntpc7, pt04, ech10, no_neutrals, with_met, nes_up, nes_down, ner`. Needs a new `sph070`/`sph090` branch, a re-run of `runAnalyze.py` over the raw ntuples, and a full unfolding re-run.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-14 — No change needed

> page 13-14-15-16-17 there is a mis-matching between the figure number in the figure itself and in the caption.

**Assessment.** No change needed. We checked every `Figure N` string in the compiled PDF and every plotting script: all are LaTeX captions or `\ref`s, with no figure numbers baked into the plots. No mismatch found. Worth asking which figures you meant.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-15 — Open - substantive

> page 15 what is the MC excess in phi around -1.5 ?

**Assessment.** TODO (substantive — and the paper's current answer is backwards). The text says the modulation is "primarily of generator (JETSET 7.4) origin rather than a detector φ-acceptance effect" and "cancels between MC reco and gen". The rendered Fig. 8 shows the comb in **Data reco and MC reco** with **MC gen flat** — the signature of a *detector* φ-modulation, which also destroys the cancellation argument.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-16 — Partly fixed

> page 19 , neutral hadron, nothing is visible in figure 6 and the so-called cleaning cut of figure 7 is very badly explained, this part is not understandable it must be rewritten

**Assessment.** Partly fixed (PR 06), rest TODO. You are understating it: `pwflag5_costheta_no_cut.py:53-64` toggles only `passEventSelection`; the cleaning cut is hard-wired at object level in C++ (`analysisCompute.h:142`), so it is present in **both** curves. The caption now says so, and "yellow band" is corrected to "dotted line". Still TODO: the body text at `EventReconstructionAndSelection.tex:147-149` still falsely claims to compare "with and without the cleaning cut", and the "structural gap in the detector" justification is unreferenced (ALEPH's HCAL cracks are in φ, not at a single cosθ ≈ −0.185). A genuine cut-on/cut-off comparison needs a new config flag and a re-run.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-17 — Open - substantive

> page 19 also Fig. 8 must be understood before publication (or removed, it seems a detail on MC-data corrections done in the nineties).

**Assessment.** TODO (substantive). See the phi comment above — agreed it cannot stand as written.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-18 — Open - substantive

> page 23 first paragraph, I do not understand the text.

**Assessment.** TODO (substantive). `AnalysisMethod.tex:34` asserts phase-space consistency then immediately describes two ways the phase spaces differ; "handled by RooUnfold's efficiency correction" is vague (it is `response.Miss()`, stated three paragraphs later); the fakes dismissal is unquantified.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-19 — Open - substantive

> page 25 last paragraph I do not understand how ISR is treated and if corrections are applied or not, please rewrite in a less obscure way.

**Assessment.** TODO (substantive). Same root cause as the page 9 ISR comment.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-20 — Partly fixed

> page 39-40 Table 9, 10 there are considerable differences between the ALEPH original uncertainties and your number, in some cases there are even new rows at the start of the table, can you comment in the paper ?

**Assessment.** Partly fixed (PR 05), rest TODO. Fixed: dropped the all-dashes `[0.55,0.56)` rows from Tables 8/9/10 — every column was "---". Still TODO: rows `[0.56,0.57)`, `[0.57,0.58)`, `[0.58,0.59)` quote totals of 500.9%, 97.2%, 82.7%; suppressing them narrows the reported range, which is your decision. Also still TODO, and the more important half: *why* the uncertainties differ. ALEPH's total exceeds ours in **31 of 42** bins. The mechanism is visible in Table 10 — ALEPH's Sys.2 column is assigned in coarse blocks of identical values (20.3×3, 7.8×3, 7.1×3, 5.5×3, …) whereas our theory envelope is a per-bin max. Our missing components (ISR in the total, response-matrix statistics, correlated-branch treatment) all push the same way.

**Response to referee.** _to write_

**Change.** _none yet_

---

### R1-21 — Open - substantive

> page 45 Section 11 and following pages do not seem for publication, in any case they are far below publication quality

**Assessment.** TODO (substantive, agreed). §11 self-identifies as internal and §11.3 is a maintenance instruction to future authors. Recommend: keep §11.1 (real limitations) in §9/§10, keep ~1 paragraph of §11.4, cut the rest. App. C should be cut in full — it states it is "not a verbatim message log" but a reconstruction from the artifact trail, which is the wrong evidentiary basis for the paper's central claim. App. A's reproduction contract is not reproducible by a reader; replace with a DOI. App. B is closest to publishable but needs real numbers and a real PSD test (the authors' own notes record `cov_total` with min eigenvalue 0.0 and condition number ~8.6e16).

**Response to referee.** _to write_

**Change.** _none yet_

---
