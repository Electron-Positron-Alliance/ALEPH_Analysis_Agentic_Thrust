# Analysis Note Layout & Figure Improvement Plan
**Date:** 2026-03-05
**Primary file:** `AnalysisNote/sections/Results.tex`

---

## TIER 1 — Critical (Do First)

### 1. Split Figure 25 into two full-width flagship figures

**File:** `AnalysisNote/sections/Results.tex`

The main physics results are squeezed into a 2-panel `0.48\textwidth` layout. Split into two separate `[p!]` figures at `0.95\textwidth` each.

**Find this block (approx lines 107-114):**
```latex
\begin{figure}[h!]
\centering
\includegraphics[width=0.48\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/final_result_uncertainty_breakdown.pdf}%
\hfill%
\includegraphics[width=0.48\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/final_result_of_ibu_comparison.pdf}
\caption{...}
\label{fig:final_thrust_result}
\end{figure}
```

**Replace with two figures:**

```latex
\begin{figure}[p!]
\centering
\includegraphics[width=0.95\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/final_result_uncertainty_breakdown.pdf}
\caption{Final unfolded thrust distribution with total uncertainty band compared to the published ALEPH 2004 result. The ratio panel shows bin-by-bin agreement, with the gray band representing the total uncertainty envelope.}
\label{fig:final_thrust_result}
\end{figure}

\begin{figure}[p!]
\centering
\includegraphics[width=0.95\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/final_result_of_ibu_comparison.pdf}
\caption{Comparison of the current IBU result with OmniFold and prior IBU spectra. The ratio panel shows each method relative to the current unfolded nominal, with the gray band representing the total uncertainty.}
\label{fig:final_thrust_comparison}
\end{figure}
```

**IMPORTANT:** After splitting, search the entire `AnalysisNote/` directory for any `\ref{fig:final_thrust_result}` references that may need updating or splitting to also reference `fig:final_thrust_comparison`.

---

### 2. Enlarge Figures 19–22 (uncertainty breakdowns)

**File:** `AnalysisNote/sections/Results.tex`

These four single-panel figures are currently `0.72\textwidth`. Increase each to `0.85\textwidth`.

**For each of Figures 19, 20, 21, 22, find:**
```latex
\includegraphics[width=0.72\textwidth]{...}
```

**Replace with:**
```latex
\includegraphics[width=0.85\textwidth]{...}
```

There should be 4 occurrences of `width=0.72` in Results.tex.

---

### 3. Split Figure 23 (four-panel uncertainty components) into two 2-panel figures

**File:** `AnalysisNote/sections/Results.tex`

The current Figure 23 packs 4 panels at `0.48\textwidth` into a single figure. Split into two figures: (a) statistical + unfolding, (b) experimental + theory.

**Find this block (approx lines 73-82):** The figure containing four `\includegraphics` calls for:
- `uncertainty_components_statistical.pdf`
- `uncertainty_components_unfolding.pdf`
- `uncertainty_components_experimental.pdf`
- `uncertainty_components_theory.pdf`

**Replace with two figures:**

```latex
\begin{figure}[t!]
\centering
\includegraphics[width=0.49\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_statistical.pdf}%
\hfill%
\includegraphics[width=0.49\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_unfolding.pdf}
\caption{Per-bin uncertainty components: statistical (left) and unfolding iteration (right). The unfolding panel shows signed variation for $N_{\mathrm{iter}}=4$ and $6$ relative to the nominal $N_{\mathrm{iter}}=5$, with the iteration envelope.}
\label{fig:uncertainty_components_stat_iter}
\end{figure}

\begin{figure}[t!]
\centering
\includegraphics[width=0.49\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_experimental.pdf}%
\hfill%
\includegraphics[width=0.49\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_components_theory.pdf}
\caption{Per-bin uncertainty components: experimental variations (left) and theory reweighting (right). The experimental panel shows seven individual detector-variation branches with envelope; the theory panel shows Pythia, Herwig, and Sherpa reweighting shifts.}
\label{fig:uncertainty_components_exp_theory}
\end{figure}
```

**IMPORTANT:** Search for any `\ref` to the old Figure 23 label and update to reference both new labels as appropriate.

---

### 4. Enlarge Figure 24 (correlation matrix)

**File:** `AnalysisNote/sections/Results.tex`

**Find:**
```latex
\includegraphics[width=0.82\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrix_total_correlation_final.pdf}
```

**Replace with:**
```latex
\includegraphics[width=0.95\textwidth]{../Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/matrix_total_correlation_final.pdf}
```

---

## TIER 2 — High Priority

### 5. Move Figures 2–7 (pwflag kinematic validation) to appendix

**File:** `AnalysisNote/sections/EventReconstructionAndSelection.tex`

Figures 2–7 are large 9-panel grids (one per pwflag category) that each occupy nearly a full page with minimal surrounding discussion. This creates 6 consecutive orphan-figure pages (pages 11–16).

**Action:**
- Cut the six `\begin{figure}...\end{figure}` blocks for Figures 2–7 from `EventReconstructionAndSelection.tex`
- Create a new appendix file `AnalysisNote/appendix/App_KinematicValidation.tex` containing these figures with a brief introductory paragraph
- Add `\input{appendix/App_KinematicValidation}` to `main.tex` after the existing appendix inputs
- In `EventReconstructionAndSelection.tex`, replace the figure blocks with a single sentence referencing the appendix: "Per-category kinematic distributions are shown in Appendix~\ref{app:kinematic_validation}."

---

### 6. Standardize float placement in Results section

**File:** `AnalysisNote/sections/Results.tex`

Apply consistent float specifiers:
- Uncertainty breakdown figures (19–23): `[t!]`
- Correlation matrix (24): `[t!]`
- Flagship results (25a, 25b): `[p!]` (own page)

---

## TIER 3 — Polish

### 7. Add `\FloatBarrier` between Results subsections

**File:** `AnalysisNote/sections/Results.tex`

Add `\usepackage{placeins}` to `main.tex` preamble (if not already present), then add `\FloatBarrier` between the uncertainty discussion, correlation matrix, and final result subsections to prevent figures from drifting past their discussion.

### 8. Consider moving large per-bin tables (9–11) to appendix

These tables span multiple pages. If they are currently in Results.tex, consider moving to an appendix with a summary sentence in the main text. This is lower priority and should only be done if it improves page flow after the above changes.

---

## Execution Notes

- After all edits, recompile with: `cd AnalysisNote && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex`
- Two passes needed to stabilize cross-references after figure renumbering
- Verify no broken `\ref{}` remain by checking the log for "undefined"
- The figure numbering will shift throughout the document after these changes — this is expected and correct
