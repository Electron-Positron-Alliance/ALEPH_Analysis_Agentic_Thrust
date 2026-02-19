# Plan: Section 5 Hardening + Sections 1–5 Review (IBU Thrust Note)

## Summary
Strengthen `AnalysisNote/sections/AnalysisMethod.tex` so it is technically decision-complete for the thrust workflow using Iterative Bayesian Unfolding, then perform a strict review pass of Sections 1–5 for physics logic, code-traceability, and presentation quality.
Implementation order is fixed: write this plan to `Plans/` first, then execute edits.

## Step 0: Write Plan File Before Any Implementation
1. Create `Plans/2026-02-16_section5_hardening_and_sections1to5_review_plan.md`.
2. Copy this full plan into that file.
3. Do not edit any analysis/note code before this file exists.

## Scope
In scope:
1. `AnalysisNote/sections/AnalysisMethod.tex` rewrite/expansion.
2. Cross-references in Sections 1–4 only where needed for consistency with Section 5 wording.
3. Figure captions and method text alignment for existing thrust/response/covariance plots.
4. Review findings for Sections 1–5 in a separate review artifact.

Out of scope:
1. New unfolding runs.
2. New observables (C-parameter, heavy-jet mass).
3. Systematics or results section rework beyond wording consistency.

## Required Changes in Section 5 (`AnalysisNote/sections/AnalysisMethod.tex`)
1. Add a short “workflow overview” paragraph listing exact stages:
   - detector-level thrust build,
   - response construction from matched MC,
   - Iterative Bayesian Unfolding,
   - hadronic selection correction,
   - covariance/correlation export.
2. Thrust construction subsection must include:
   - thrust definition equation,
   - exact observable forms used in plots (`T`, `\\tau=1-T`, `\\log\\tau`),
   - explicit statement that selected particles after Section 4 cuts are inputs.
3. Response construction subsection must explicitly define:
   - matched event key logic (as implemented in code),
   - reco/gen fill logic,
   - handling of misses and fakes,
   - matrix normalization convention used for probability view.
4. Iterative Bayesian Unfolding subsection must include:
   - Bayesian update equation and symbol definitions,
   - prior choice for iteration 0,
   - stopping/selection criteria wording tied to current validation artifacts,
   - explicit nominal setting: `N_iter = 7`.
5. Hadronic event-selection correction subsection must include:
   - exact correction formula from `tgenBefore/tgen`,
   - where it is applied relative to unfolding,
   - short rationale for phase-space correction.
6. Covariance/correlation subsection must include:
   - source of statistical covariance used in RooUnfold,
   - exported products (ROOT + CSV),
   - statement of intended downstream use (theory comparisons).
7. Terminology constraint:
   - use “Iterative Bayesian Unfolding” explicitly,
   - do not use collaboration-style method labels (e.g., “DELPHI-style”).

## Cross-Section Consistency Edits (Sections 1–4)
1. Ensure Section 1 motivation text and Section 5 method text use consistent language for:
   - perturbative/non-perturbative QCD context,
   - alphaS precision motivation,
   - thrust-first scope.
2. Ensure Section 4 references to distributions and selections naturally lead into Section 5 workflow wording.
3. Keep Section 5 start on a fresh page after Section 4 (`\\FloatBarrier` + single `\\clearpage`).

## Public Interfaces / Types / Outputs
1. No C++/Python API or type changes are required in this pass.
2. Note-facing interface expectations:
   - existing figures under `Studies/ValidationExec_2026-02-13/...` remain canonical inputs,
   - captions in Section 5 must map one-to-one to these artifacts.
3. New output artifacts for this pass:
   - `Plans/2026-02-16_section5_hardening_and_sections1to5_review_plan.md`,
   - `Plans/2026-02-16_sections1to5_review_findings.md` (review checklist + findings).

## Review Pass Spec (After Section 5 Rewrite)
Create `Plans/2026-02-16_sections1to5_review_findings.md` with findings ordered by severity.

Required review checks:
1. Physics logic continuity from Introduction through Analysis Method.
2. Every major method claim in Section 5 is traceable to code/output artifact.
3. Figure discussion quality in Section 4 (what each plot validates and why it matters for event-shape reconstruction).
4. Notation consistency (`T`, `\\tau`, `\\log\\tau`, bin indices, response symbols).
5. No banned shorthand method labels.
6. LaTeX structure quality (page break, float placement, references, compile cleanliness).

## Validation and Test Cases
1. Compile test:
   - run `pdflatex -interaction=nonstopmode -halt-on-error main.tex` in `AnalysisNote/`.
2. Document structure test:
   - confirm Section 5 begins on a new page.
3. Content test:
   - verify each Section 5 subsection contains the required items listed above.
4. Traceability test:
   - verify each Section 5 figure references existing files in `Studies/ValidationExec_2026-02-13/`.
5. Style test:
   - verify no use of forbidden shorthand method labels.
6. Review artifact test:
   - confirm findings file exists and includes severity-ranked issues or explicit “no findings” statement.

## Acceptance Criteria
1. Section 5 is technically complete at analysis-note depth with clear equations, definitions, and configuration choices.
2. Sections 1–5 read as a coherent thrust-first IBU analysis narrative.
3. PDF compiles cleanly with Section 5 on a fresh page.
4. Review findings file exists and is actionable for next iteration.

## Assumptions and Defaults
1. Current nominal thrust workflow and figures in `Studies/ValidationExec_2026-02-13/` are the authoritative baseline.
2. Nominal unfolding configuration remains `N_iter = 7` for this pass.
3. This pass is note-focused and does not trigger new production runs.
4. If any code-text mismatch is found during review, it is logged in findings rather than silently reinterpreted.
