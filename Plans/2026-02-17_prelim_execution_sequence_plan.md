# Execution Sequence Plan (Post-Plan-Mode)

## Order requested
1. Update plotting behavior for the final result uncertainty breakdown figure.
2. Regenerate outputs and stop for user visual review.
3. Continue to core-code migration from `Studies/` into the analysis software stack.
4. Continue to analysis-note rewrite (Sections 5 onward).

## Step 1 scope (this pass)
- In `Studies/PreliminaryResult/scripts/build_prelim_uncertainty_summary.py`:
  - Ratio panel denominator: unfolded result.
  - Ratio shown: ALEPH 2004 / unfolded.
  - Build ratio via ROOT histogram division with propagated errors.
  - Draw a gray band around 1 in ratio panel using unfolded total relative uncertainty.
  - Improve style consistency with `Unfolding/plot_unfolded.py`.
  - Use ratio y-range `[0.8, 1.2]`.
- Regenerate:
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/final_result_uncertainty_breakdown.pdf`
  - `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_breakdown.json`

## Step 2 checkpoint
- Share exact output paths for plot review.
- Wait for user feedback before proceeding to migration and note rewrite.

## Next phases (after review)
- Move core workflow scripts into `Unfolding/scripts` with wrappers in `Studies/PreliminaryResult/scripts`.
- Rewrite `AnalysisNote/sections/AnalysisMethod.tex`, `AnalysisNote/sections/SystematicUncertainties.tex`, `AnalysisNote/sections/Results.tex`, `AnalysisNote/sections/Conclusion.tex` against `Studies/PreliminaryResult/2026-02-17_thrust_iter5`.
