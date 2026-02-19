# Physics-Tone Rewrite and Execution Plan (Sections 1-4)

## Objective
Strengthen the analysis note's physics narrative with a heavy rewrite of the Figure 1-7 discussion and deep tone retuning of Introduction, Detector, and Datasets, while preserving the current Iterative Bayesian Unfolding workflow and analysis choices.

## Scope
- In scope:
  - Deep rewrite of `AnalysisNote/sections/Introduction.tex`
  - Deep rewrite of `AnalysisNote/sections/ALEPHDetector.tex`
  - Deep rewrite of `AnalysisNote/sections/Datasets.tex`
  - Heavy physics discussion rewrite around Figures 1-7 in:
    - `AnalysisNote/sections/EventReconstructionAndSelection.tex`
    - `AnalysisNote/sections/PWFlagFullDistributions.tex`
  - Build/validation of note with bibliography pass.
- Out of scope:
  - Section 5+ structural rewrites
  - New figure generation
  - Changes to unfolding configuration or physics results.

## Writing Contract
- Conservative claim style: no over-assertive statements from visual comparisons.
- Distinguish detector-response effects vs selection-threshold effects vs underlying event-shape sensitivity.
- For each figure group: what is shown, what it tests, why it matters for thrust unfolding, conservative takeaway.
- Keep ALEPH-note style: concise, technical, and analysis-driven.

## Execution Steps
1. Retune Introduction for sharper QCD motivation and staged analysis framing.
2. Retune ALEPH detector section to focus on subsystems relevant to thrust inputs and migration control.
3. Retune datasets section with explicit synchronized-input logic (`t`, `tgen`, `tgenBefore`) and conservative theory-systematics framing.
4. Rewrite Section 4 figure discussions with substantially expanded physics interpretation, especially for Figures 1-7.
5. Verify labels/references remain stable.
6. Compile note with bibliography:
   - `pdflatex main.tex`
   - `bibtex main`
   - `pdflatex main.tex`
   - `pdflatex main.tex`
7. Report exact file-level changes and any residual warnings.

## Acceptance Criteria
- Section 4 includes substantive figure-by-figure interpretation for Figures 1-7.
- Sections 1-3 share consistent physics tone with Section 4.
- Note compiles successfully to `AnalysisNote/main.pdf`.
- No broken references; citation issues, if any, are explicitly documented.
