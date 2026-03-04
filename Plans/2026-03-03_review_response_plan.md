# Review Response Plan — 02/27/26 Comments + ALEPH Paper Cross-Reference

Date: 2026-03-03

This plan addresses the reviewer comments in `AnalysisNote/REVIEWS/022726.md` and incorporates insights from reading the two previous ALEPH publications:
- **Paper I (1996)**: CERN/PPE 96-186, "Studies of QCD with the ALEPH Detector," Phys. Reports 294 (1998)
- **Paper II (2004)**: EPJC 35, 457–486, "Studies of QCD at e+e- centre-of-mass energies between 91 and 209 GeV"

---

## A. Abstract and Introduction Rewrite (Comments 1–15)

### A1. Abstract revision
- Reframe the opening motivation: progress in LLMs for fundamental physics is currently on the theoretical side (Google, OpenAI, etc.). Real advancement requires "precision AI" — reliably trustworthy calculations and predictions. The experimental side of that program is missing. Our work with open data + precision QCD provides an excellent testing ground.
- Reframe the agent narrative: the physicist opened Codex/Claude Code, brainstormed the analysis, then prompted the agent iteratively. No code was written by the physicist; the perspective is to see how far AI can be pushed with expert physicist instruction (analogous to advising a student).
- L23: "explicit physicist control" → "expert physicist prompting and feedback"
- L28: "validating the reliability of AI in science" → "platform for systematically developing precision AI systems for fundamental physics and science"
- Favor commas over hyphens throughout.

### A2. Introduction restructure (L99–168)
- L99: "where AI discovers new physics" → "where AI rapidly accelerates the discovery of new physics"
- L99: use "AI-assisted scientific workflows" everywhere
- "across both precision theory and experiment"
- L103: add sentence that pursuing the theory-experimental interface will inevitably lead to deeper understanding of AI capabilities and potential improvements for science domains where precision matters.
- L110: "deploy robotic particle detectors" → "deploy robotic particle detectors (yet)"
- L111: "the wealth of" → "the emergence of, partially enabled by the e+e- alliance,"
- L112: use "AI-assisted" rather than "LLM-assisted" globally.
- **L117–141 major restructure**: The logical flow should be:
  1. For AI to analyze experimental data, a logical first step is an agentic analysis with expert physicist oversight (connect to abstract motivation).
  2. Introduce precision QCD as an excellent domain because of the combination of high-precision e+e- data AND sophisticated high-precision theory calculations.
  3. Then introduce thrust as an ideal first variable.
  4. Then one paragraph on why thrust is interesting on its own for physics.
- L142: reconsider whether this paragraph fits the new flow.
- L155–168: combine into one paragraph about what the agent is asked to do. Mention that we gave the AI previous analysis code, analysis note, and paper. Cite zero-shot and few-shot learning literature — the logic is that supplying examples should yield better results.

---

## B. AI Agent Section (Section 2) Improvements (Comments 16–20)

### B1. Section 2.1 — expand operating model
- Specify that the agent is interfaced through Codex or Claude Code.
- The workflow is: physicist prompts LLM → agent executes → physicist reviews → repeat.
- Add more detail about the iterative prompt-execute-review loop.

### B2. Section 2.2 — reproducibility (L202)
- Remove the explicit file path line.
- Instead, discuss the ways reproducibility is accomplished and how physicist information/oversight is useful (version control, run contracts, artifact traceability).

### B3. L206 — broaden AI framing
- AI is used beyond theory calculations. The goal is to accelerate fundamental physics by leveraging AI agents, LLMs, and other advanced models.
- This requires AI application for BOTH theoretical calculations and experimental analysis, ideally with a loop between them.
- **Add a diagram** showing the loop: theory prediction → experimental analysis → further proposals, with human-in-the-loop at each stage.

### B4. L210 — reduce verbosity.

### B5. Section 2.3 + Table 1 — remove or substantially improve
- The scorecard table as-is is not informative. Remove unless it can be made genuinely useful with meaningful metrics.

---

## C. Detector Section (Section 3) Improvements (Comments 21–22)

### C1. L236 — remove p_T-to-thrust resolution claim
- The translation from single-track p_T resolution to thrust resolution is not straightforward. Remove this claim.

### C2. L226 — improve detector description
- Read the ALEPH section of arXiv:2507.14349 and use it as a better reference for the detector description.
- **Key addition from ALEPH papers**: explicitly mention the energy-flow algorithm. Both Paper I (Sec. 1.2.6) and Paper II (Sec. 2.1) describe how tracking and calorimetric information is combined into energy-flow objects with resolution σ(E) = (0.59±0.03)√(E/GeV) + (0.6±0.3) GeV. This is the actual particle-level input used for event shapes in the 2004 paper and in our analysis.
- Mention that the 2004 paper uses energy-flow objects (charged + neutral) while the 1996 paper used charged-only, and our analysis follows the 2004 approach.

---

## D. Dataset and Selection Sections (Comments 23–28)

### D1. Various language cleanups
- L248: remove "so detector ..."
- L253: remove "as baseline"
- L280: "conditioned on" → simplify to "corresponding generator level from the reco selection" or similar.

### D2. L256 — verify event counts
- **Action item**: Check the ROOT files to verify whether 1.33 million is selected hadronic events or total events before selection. Cross-reference with Table in current note (1,365,440 total, 1,326,312 selected).
- Compare with Paper II: ~1.1 million events from 1994+1995 at 41.48 pb⁻¹. Our 1994-only sample should be a subset.

### D3. L267 — ctau > 10mm
- Remove the cτ > 10mm detail unless it is essential. If kept, add a citation (Paper I defines stable particles as those with mean lifetime < 10⁻⁹ seconds).

### D4. L272 — ISR correction
- Add a separate line about the ISR correction, analogous to the hadronic correction.
- Define C_ISR = N(no ISR) / N(ISR) as a displayed TeX equation.
- Make the hadronic correction also a displayed TeX equation rather than inline math.
- **Cross-reference**: Paper I Eq. 19 defines C = X_generator / X_{MC+det.sim.} where the generator has ISR turned off. Paper II uses KORALZ for ISR treatment. Our approach should be clearly compared.

---

## E. Event Reconstruction and Validation (Comments 29–34)

### E1. Language cleanups
- L292: remove "high-thrust", just say "thrust bins where"
- L292: remove sentence "The experimental systematic ..."
- L296: restructure to avoid "how ...", just say "we show ..."

### E2. L321 — pwflag 5 cos(theta) suppression
- In Figure 6 (pwflag=5 cos(theta)), there is a visible suppression in a region of cos(theta).
- **Action item**: produce an additional plot showing the distribution WITHOUT the neutral hadron cleaning cut to see the raw feature.

### E3. L344 onwards — restructure discussion
- Have separate paragraphs for each pwflag category shown in Figures 1–6.
- Simplify the language.
- Do NOT discuss impact on thrust specifically (we want to expand to other event shapes too).
- Focus only on: data/MC agreement, differences between MC generators, and bulk behavior.

### E4. Figure 3 — phi spectrum excess
- **Action item**: investigate the excess in generator-level particles in the phi spectrum. Is this a known feature of the MC? A binning artifact? Needs explanation.

---

## F. Analysis Method (Section 6) Improvements (Comments 35–44)

### F1. Code references to appendix (L469, 520–534)
- Move all explicit analysis code discussion (script paths, command-line examples, workflow commands) to an appendix.
- The main body should contain physics, discussion, and figures only.

### F2. L469 — binning discussion cleanup
- Combine and clean up. State clearly: we first use identical bins as the previous ALEPH result (Paper II) for direct comparison, then test fine bins throughout the space.
- **Cross-reference**: Paper I Table 2 has bins of width 0.005 in 1−T. Paper II used similar fine binning at M_Z. Our comparison should map directly to the Paper II bins.

### F3. L474 — N_iter=5 discussion
- Move the iteration choice discussion to its own subsection about IBU implementation/regularization.

### F4. L482 — miss term
- **Action item**: produce plots showing the events that contribute to the miss term (events in generator-level that have no match at reco level). This is important for understanding edge-of-acceptance and low-multiplicity losses.

### F5. Section 6.4 — thrust resolution study (NEW)
- **Major new study**: use the matched reco/gen events to study thrust resolution as a function of thrust.
- Plot (T_reco − T_gen) vs T_gen in 2D, and extract the resolution σ(T) as a function of T_gen.
- This should inform the finest binning usable in different regions, particularly in the high-thrust (low τ = 1−T) regime near the peak and deep in the non-perturbative region.
- **Cross-reference**: Paper I Sec. 2.2 says the matrix method bin sizes were chosen to be "somewhat smaller than twice the corresponding detector resolution." Paper II uses similar philosophy. Our IBU approach is less sensitive to binning but the resolution study still informs interpretation.

### F6. Figure 9 — add pull panel
- Add a second version of Figure 9 showing a pull panel (difference/uncertainty) instead of ratio panel.
- Make the figure smaller.

### F7. Figure 10 — make larger
- Increase figure size to 2 plots per line instead of current layout. Consider combining with Figure 9 if useful.

### F8. Figure 11 — workflow diagram confusion
- The track/event component arrow pointing to theory component is confusing.
- **Replace** with a table, pseudocode, or set of equations that clearly show the systematic variation flow.

---

## G. Systematics Section (Section 6.7 → restructure) (Comment 44)

### G1. Restructure into three clear subsections:
1. **Hadronic event correction** — the C_had correction and its uncertainty propagation.
2. **ISR correction** — currently NOT implemented. This is a significant gap.
   - **Cross-reference**: Both ALEPH papers correct for ISR. Paper I uses the ratio C̄_i = D^MC_{gen}(no cuts, no ISR) / D^MC_{gen}(cuts, ISR). Paper II uses KORALZ specifically because of its more accurate ISR description.
   - **Action item**: implement ISR correction or document clearly why it is deferred and what the expected impact is.
3. **Statistical covariance** — the covariance matrix from unfolding and its propagation.

---

## H. Systematic Uncertainties (Section 7) Improvements (Comments 45–47)

### H1. Section 7.1 — clean up math
- The current math presentation is messy. Structure better with clear equation numbering and grouping.
- Convert Table 7 from tabular format into text discussion (the table is too long and not useful).
- Move Figure 14 (uncertainty differences) higher in Section 7 to appear near the relevant discussion.

### H2. Table 8 — remove mean uncertainty across bins
- Per-bin information is what matters, not the mean.

### H3. Table 9 — convert to per-bin table + plot
- Replace with a per-bin uncertainty breakdown table.
- Add a plot showing per-bin uncertainty components.
- The current aggregate table is not useful.

---

## I. Results Section (Section 8) Improvements (Comments 48–50)

### I1. Text cleanup
- Make the results discussion significantly cleaner and more concise. Currently verbose and not optimally useful.

### I2. Figure 15 — fix formatting
- Fix the double TeX rendering issue at the top of the figure.
- Fix y/x axis legends that are too close to the numbers.

### I3. Figures 15/16 — side by side
- Put figures 15 and 16 side by side.

---

## J. New Analysis Checks Informed by ALEPH Papers

### J1. Charged-only vs. energy-flow comparison
- Paper I (1996) measured thrust using charged particles only and explicitly chose NOT to correct for neutrals to minimize model dependence.
- Paper II (2004) used energy-flow objects (charged + neutral).
- **Proposed check**: run the unfolding with charged-only input and compare to the nominal energy-flow result. This directly quantifies the neutral-particle impact and connects to the 1996 measurement.
- This is partially covered by the existing "no_neutrals" systematic variation, but a dedicated comparison figure would be valuable.

### J2. Matrix method vs. IBU cross-check
- Both ALEPH papers used a matrix method for detector correction. Our analysis uses IBU.
- **Proposed check**: implement a simple matrix-method unfolding (single application of the response inverse or pseudo-inverse) and compare bin-by-bin to the IBU result. Differences should be small for well-populated bins.

### J3. Direct numerical comparison to published ALEPH values
- Paper I Table 2 gives the (1/N)(dN/dT) values with stat ± sys at 91.2 GeV in fine bins.
- Paper II provides distributions accessible through the ALEPH QCD web site and HEPData.
- **Action item**: overlay our unfolded values directly on Paper I Table 2 values AND Paper II values. Note that:
  - Paper I is charged-only, so comparison requires our charged-only variation.
  - Paper II is energy-flow (all particles), matching our nominal.
  - The normalization convention may differ: Paper I uses (1/N)(dN/dT) while we may use (1/σ)(dσ/dT). Verify and reconcile.

### J4. Event selection comparison
- Paper I: ≥5 charged tracks, E_ch > 15 GeV, θ_sph ∈ [35°, 145°].
- Paper II: ≥5 good tracks, total charged energy > 15 GeV, |cos θ_sph| < 0.9. Uses energy-flow objects with |cos θ| < 0.95 and p_T > 200 MeV/c.
- Our analysis: similar cuts but verify exact correspondence. Any differences in cut values could cause spectrum differences.

### J5. Systematic uncertainty comparison
- Paper II at M_Z: experimental systematics on α_s are below 1%. Dominant source is neutral energy-flow simulation in 1–2 GeV range.
- Compare our systematic breakdown to theirs. Are we seeing the same dominant sources?
- Paper II groups neighbouring bins in threes to smooth statistical fluctuations in systematic estimates — consider if this is needed for our analysis.

---

## K. Execution Priority

### Phase 1 — Critical fixes (do first)
1. Abstract and introduction rewrite (A1, A2)
2. AI agent section improvements (B1–B5)
3. Code references → appendix (F1)
4. Verify event counts against ROOT files (D2)
5. ISR correction: implement or document gap (G1)

### Phase 2 — Analysis checks
6. Thrust resolution study (F5) — new study
7. Miss term plots (F4)
8. pwflag=5 cos(theta) without cleaning cut (E2)
9. phi spectrum excess investigation (E4)
10. Charged-only vs. energy-flow comparison (J1)
11. Direct comparison to ALEPH Paper I/II numerical values (J3)

### Phase 3 — Note improvements
12. Detector section rewrite with energy-flow description (C1, C2)
13. Dataset/selection language cleanups (D1, D3, D4)
14. Event reconstruction discussion restructure (E1, E3)
15. Analysis method restructure (F2, F3, F6, F7, F8)
16. Systematics section restructure (G1, H1, H2, H3)
17. Results section cleanup (I1, I2, I3)

### Phase 4 — Additional cross-checks
18. Matrix method vs. IBU comparison (J2)
19. Event selection comparison across papers (J4)
20. Systematic uncertainty comparison with published ALEPH (J5)
