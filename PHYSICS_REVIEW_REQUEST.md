# Request for Expert Physicist Review: ALEPH Thrust Analysis (Preliminary)

## Overview

This analysis presents a preliminary unfolded thrust spectrum from archived ALEPH $e^+e^-$ collision data ($\sqrt{s}=91.2$ GeV) using iterative Bayesian unfolding with full covariance and correlation matrices. We request **structured expert physics review** in 4 key areas.

**Key Results**: Total uncertainty ~8.43% in central range (0.60–0.95), dominated by theory uncertainty (~6.1%).

---

## 📋 Review Areas & Structured Feedback Format

### 🎯 Area 1: Physics Interpretation & Comparison with Prior Measurements

**Goal**: Validate that the unfolded spectrum is physically sensible and properly positioned relative to prior work.

#### Files to Review
```
AnalysisNote/main.pdf
  → Section 1 (Introduction): Physics context
  → Section 8 (Results): Spectrum presentation, numerical comparisons
  → Table 4 (Results): Central values, uncertainties, χ²/ndf

Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/
  → unfolded_spectrum.pdf
  → comparison_prior.pdf
  → workflow_summary.json → central_values.thrust
```

#### Code References (if diving deeper)
- Event reconstruction: `DataProcessing/src/Analyze.cxx` (lines 50–150)
- Hadronic correction application: `DataProcessing/src/Analyze.cxx` (lines 100–120)

#### Specific Questions for Reviewers

1. **Spectrum shape**: Does the peak location (≈0.65) and width match expectations for hadronic Z decays? Are there anomalies in specific bins?

2. **Comparison to 2004 ALEPH reanalysis**:
   - Central range (0.60–0.95): How close are we quantitatively? (e.g., within 1σ, 2σ, >2σ?)
   - Endpoint tension: The high-thrust bins (T > 0.95) are ~30% higher. Is this plausible? Could this indicate an issue?

3. **Consistency with world average**: Does this result help or worsen the $\alpha_s$ extraction tension mentioned in the introduction?

4. **Missing comparisons**: Should we overlay any other recent measurements (LEP+LEP-II, Tevatron, LHC)?

#### Expected Feedback Format

**For each point above, please provide:**
```markdown
**Point [N]: [Title]**
- Status: ✓ Acceptable / ⚠️ Needs clarification / ❌ Concern
- Evidence: [Reference to figure/page/value]
- Comment: [1–3 sentences]
- Suggested action: [Diagnostic or follow-up if applicable]
```

**Example:**
```markdown
**Point 1: Spectrum shape**
- Status: ✓ Acceptable
- Evidence: Figure 8.1, peak at T≈0.65 matches MC expectations
- Comment: Shape looks physically reasonable. Width is consistent with fragmentation.
- Suggested action: None required
```

---

### 🔢 Area 2: Systematic Uncertainties & Correlation Structure

**Goal**: Validate that (a) individual uncertainty components are reasonable, (b) dominant sources are correctly identified, (c) bin-to-bin correlations are physically motivated.

#### Files to Review
```
AnalysisNote/main.pdf
  → Section 7 (Systematic Uncertainties): Full description
  → Table 5: Uncertainty budget summary by range
  → Section 9 (Challenges): Known approximations and open items

Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/
  → uncertainty_breakdown.pdf (stacked bar chart by component)
  → total_correlation_matrix.pdf (visual of correlations)

Numerical products:
  → correlation_matrix.csv (50×50 bin-bin correlations)
  → covariance_matrix.csv (50×50 bin-bin covariance)
  → workflow_summary.json → uncertainty_envelope (stat, theory, exp, iter, had)
```

#### Code References (if diving deeper)
- Experimental systematic sources: `DataProcessing/src/Analyze.cxx` (TPC, calorimeter, tracking systematics)
- Theory envelope (generator reweighting): `Unfolding/scripts/run_thrust_prelim_workflow.py` (lines ~150–200)
- Hadronic correction: `DataProcessing/src/Analyze.cxx` (lines ~105–120)
- Covariance assembly: `Unfolding/scripts/build_prelim_uncertainty_summary.py` (lines ~200–300)

#### Specific Questions for Reviewers

1. **Total uncertainty (8.43% mean)**: Is this realistic for a precision thrust measurement at LEP with stat + theory + experimental systematics included?

2. **Theory dominance (6.1% mean)**:
   - Why is theory (~6.1%) so much larger than experimental systematics (~2.8%)?
   - Is this typical for thrust extractions? Does the literature agree?
   - Which generator (Pythia, Herwig, Sherpa) drives the envelope spread?

3. **Experimental breakdown (2.8% mean)**:
   - Are the subsystems (TPC, calorimeter, tracking) weighted appropriately?
   - Are there systematics we're missing (beam energy, beam divergence, backgrounds)?

4. **Hadronic correction (3.2% mean)**:
   - Is the up/down ratio envelope (post-MC correction) a valid proxy for fragmentation uncertainty?
   - Should we include MC-generator-dependent fragmentation models explicitly?

5. **Correlation structure**:
   - Why are off-diagonal correlations small in the central range (ρ < 0.3)?
   - Is the bin-to-bin migration (33% diagonal) the dominant driver of correlation structure?
   - Have you validated this with closure tests or mock data?

6. **Missing systematics**:
   - Beam-related backgrounds (beamstrahlung, radiative effects)?
   - ISR/FSR modeling differences?
   - Selection efficiency uncertainties?

#### Expected Feedback Format

**For each point, please provide a structured comment:**
```markdown
**Uncertainty Component: [Name]**
- Magnitude: [OK / Too large / Too small] (estimate by how much if concern)
- Physics: [Brief assessment of treatment]
- Evidence: [Reference to figure/table or external reference]
- Recommendation: [Accept as-is / Investigate further / Revise]
```

**Example:**
```markdown
**Uncertainty Component: Theory**
- Magnitude: Too large (by ~1.5×)
- Physics: Generator envelope typically ~3–4% for thrust, not 6%
- Evidence: OPAL 1997 and DELPHI 1999 thrust measurements show similar precision with ~4% theory uncertainty
- Recommendation: Investigate which generator drives envelope; consider excluding outlier(s) if justified
```

---

### ✔️ Area 3: Unfolding Methodology & Validation Tests

**Goal**: Confirm that iterative Bayesian unfolding (IBU, N_iter=5) is appropriate, well-validated, and stable.

#### Files to Review
```
AnalysisNote/main.pdf
  → Section 6 (Analysis Method): IBU description, response matrix, regularization
  → Table 2 (Workflow): Method configuration summary
  → Section 9 (Challenges): Known limitations (n=3 particle case)

Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/
  → response_matrix.pdf (visualization, migration structure)
  → closure_test_4iter.pdf, closure_test_5iter.pdf, closure_test_6iter.pdf
  → closure_test_10iter.pdf, closure_test_100iter.pdf
  → workflow_summary.json → {iteration_envelope, closure_residuals, response_diagnostics}

Source code:
  → Unfolding/unfold_thrust.py (RooUnfold IBU configuration, lines ~50–120)
  → Unfolding/scripts/run_thrust_prelim_workflow.py (run configuration, lines ~1–100)
  → Unfolding/scripts/build_prelim_uncertainty_summary.py (output assembly, lines ~50–150)
```

#### Specific Questions for Reviewers

1. **IBU method choice**:
   - Is iterative Bayesian unfolding the right choice for this measurement?
   - Alternative: Would SVD, matrix inversion, or bin-by-bin unfolding be more appropriate?
   - Is there any reason to expect bias or instability in IBU for this response matrix (f_diag=0.33)?

2. **Iteration plateau (N_iter=5)**:
   - Does the spectrum visibly stabilize by N_iter=5? Or does it oscillate?
   - Closure test residuals: Are they <5% in the central range and <10% in the wings?
   - Is the iteration envelope (N=4,6) sufficiently narrow to justify the nominal choice?

3. **Response matrix diagnostics**:
   - The diagonal fraction is 33%, indicating significant migration. Is this physically understood?
   - Are there pathological migration patterns (e.g., unidirectional bias, long-range tails)?
   - Does the response matrix pass standard quality checks (well-conditioned, no negative entries)?

4. **Hadronic correction validation**:
   - The C_had(j) factors are applied post-unfolding. Are they smooth? Any sign flips or unphysical values?
   - Should the correction be applied before unfolding instead?
   - Is the correction correlated with the response matrix (could this bias the unfolding)?

5. **Convergence criterion**:
   - What tolerance or stopping criterion is used in IBU? (see unfold_thrust.py)
   - Is the nominal iteration number (5) chosen empirically or based on physics reasoning?

#### Expected Feedback Format

**For each concern, provide:**
```markdown
**Method Question: [Specific aspect]**
- Assessment: [Acceptable / Needs clarification / Recommend change]
- Validation: [Specific plot/number you inspected]
- Physics reasoning: [Why this choice is/isn't appropriate]
- Requested change (if any): [Specific action, e.g., "Switch to SVD with k=10"]
```

**Example:**
```markdown
**Method Question: Iteration plateau**
- Assessment: Acceptable
- Validation: Closure test residuals in central range (0.60–0.95): max |residual| = 3.2%, mean = 1.1%
- Physics reasoning: IBU is appropriate for moderate migration; convergence by N_iter=5 is standard
- Requested change: None
```

---

### 💻 Area 4: Code Reproducibility & Documentation

**Goal**: Ensure the analysis is reproducible, code is transparent, and physics claims are traceable to execution.

#### Files to Review
```
Top-level documentation:
  → REVIEWER_GUIDE.md (analysis overview and quick-start)
  → PHYSICS_REVIEW_REQUEST.md (this file)
  → README.md (repository structure)

Reproducibility record:
  → Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json
    (all script options, input files, output locations, dates)

Analysis scripts:
  → Unfolding/scripts/run_thrust_prelim_workflow.py (main orchestration)
  → Unfolding/scripts/build_prelim_uncertainty_summary.py (covariance/correlation assembly)
  → Unfolding/scripts/check_prelim_summary_outputs.py (validation)

Physics implementation:
  → DataProcessing/include/thrustTools.h (thrust algorithm, n=3 special case documented)
  → DataProcessing/src/Analyze.cxx (event reconstruction, corrections)
  → Unfolding/unfold_thrust.py (RooUnfold wrapper)

Version & dependency info:
  → See AnalysisNote/main.pdf Appendix (or scan codebase for pinned versions)
```

#### Specific Questions for Reviewers

1. **Traceability**:
   - Starting from `workflow_summary.json`, can you identify:
     - (a) All input files (MC, data)?
     - (b) All script options and parameters?
     - (c) All intermediate outputs (response matrix, unfolded spectrum)?
     - (d) Final output locations (covariance, correlation, central values)?
   - Are there any "magic numbers" in the code without explanation?

2. **Reproducibility**:
   - Assume you clone the repo, install dependencies, and run `run_thrust_prelim_workflow.py` with the options listed in `workflow_summary.json`.
   - Would you get bit-for-bit identical outputs, or are there stochastic elements (MC reweighting, random seeds)?
   - Are all external library versions (ROOT, RooUnfold, Python packages) pinned?

3. **Algorithm clarity**:
   - The n=3 particle special case (max-magnitude selection) is documented in ChallengesAndLimitations. Do you understand why it was chosen?
   - Does this approximation impact the central range (0.60–0.95) meaningfully, or is it confined to the endpoint?
   - Code comment (thrustTools.h line 225): Is it now clear what the algorithm does?

4. **Systematic propagation**:
   - In `build_prelim_uncertainty_summary.py`, how are per-systematic covariance matrices combined?
   - Are correlations between different systematic sources assumed to be zero? (If so, is this justified?)
   - Can you trace the formula from the code to the text in Section 7?

5. **Documentation completeness**:
   - Are there any significant calculations or decisions made in the code that are not explained in the narrative?
   - Would a new reader be able to follow the analysis from start to finish using only the PDF + code?

#### Expected Feedback Format

**For reproducibility/documentation issues, provide:**
```markdown
**Issue: [Specific concern]**
- Severity: [Critical / High / Low]
- Location: [File, line number or section]
- Impact: [Prevents reproduction / Makes code hard to understand / Minor]
- Suggested fix: [Specific change (e.g., "Add comment explaining X at line Y")]
```

**Example:**
```markdown
**Issue: Response matrix seed not documented**
- Severity: High
- Location: run_thrust_prelim_workflow.py, line 45 (MC generation)
- Impact: Makes it difficult to reproduce covariance matrix exactly
- Suggested fix: Add line: "np.random.seed(12345); torch.manual_seed(12345)" before MC sampling, document in workflow_summary.json
```

---

## 📤 How to Provide Feedback

Please choose **one of these options**:

### Option A: GitHub Issue Comments (Preferred for Discussion)
1. Comment on this issue with your feedback
2. Use the structure above: quote the area number and question, provide your response
3. Use markdown for readability (tables, code blocks, links)

### Option B: Structured Markdown Document
1. Create a `.md` file in `Plans/` directory (e.g., `Plans/physics_review_feedback_[YourName]_2026-02-27.md`)
2. Structure it with sections matching the 4 areas above
3. For each point, include:
   - **Concern**: Clear statement of issue
   - **Evidence**: Reference to figure, table, code line, or external citation
   - **Suggested action**: (if applicable)
4. Submit as a new commit or via pull request

### Option C: Pull Request with Suggested Changes
1. Fork the repo, make edits (e.g., add clarifying comments, revise uncertainty treatment)
2. Submit PR with detailed description linking to this issue
3. Example: "Addresses physics review feedback on theory uncertainty (Area 2, Point 2)"

---

## 📦 Quick Links to Key Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Analysis Note (PDF) | `AnalysisNote/main.pdf` | Full writeup with method, systematics, results (45 pages) |
| Summary Plots | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/` | 7 core figures (spectrum, breakdown, closures, matrix) |
| Reviewer Guide | `REVIEWER_GUIDE.md` | Quick-start checklist for reviewers |
| Covariance (CSV) | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/covariance_matrix.csv` | 50×50 bin-by-bin covariance |
| Correlation (CSV) | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/correlation_matrix.csv` | 50×50 bin-by-bin correlations |
| Reproducibility Record | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json` | All script options, inputs, outputs (canonical) |

---

## 🎯 Review Scope & Expectations

**We request expert feedback on:**
- Physics validity: Do results match expectations and prior work?
- Uncertainties: Are magnitudes, correlations, and treatment appropriate?
- Methodology: Is IBU well-validated? Are there methodological red flags?
- Reproducibility: Can the analysis be understood, reproduced, and extended?

**Out of scope (for this round):**
- Detailed code optimization or refactoring
- Adding new observables (thrust-major/minor) — see Future Work
- Full reanalysis of ALEPH data — this is based on archived analysis

---

## 🔗 Context & Related Documents

- **Internal correctness review** (completed): `Plans/review_correctness_2026-02-25.md`
- **Known open items**: Section 9, `AnalysisNote/main.pdf` (Challenges & Limitations)
- **AI-theory-experiment vision**: Section 1, `AnalysisNote/main.pdf` (Introduction)
- **Future work**: Multidimensional unfolding, validated AI loops, thrust-family observables

---

## ⏰ Timeline (Suggested)

- **Feedback window**: [TBD — suggest 2–4 weeks]
- **Issue discussion**: [TBD]
- **Resolution/iteration**: [TBD]
- **Target for publication/sharing**: [TBD]

---

## ✉️ Questions?

If clarification is needed on any of the 4 review areas, please comment on this issue or contact the analysis team.

**Thank you for your expert review!**
