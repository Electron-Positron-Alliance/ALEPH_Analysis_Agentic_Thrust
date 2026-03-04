# GitHub Issue: Request for Expert Physicist Review

**Title:** Request for Expert Physicist Review: ALEPH Thrust Analysis (Preliminary)

**Labels:** `review-requested`, `physics`, `precision-measurement`

---

## Body

This preliminary analysis presents an unfolded thrust spectrum from archived ALEPH $e^+e^-$ collision data using iterative Bayesian unfolding with full uncertainty quantification. We request **structured expert physics review** in 4 focused areas.

**Key Result:** Total uncertainty ~8.43% in central range (0.60–0.95), dominated by theory (~6.1%)

---

## 📋 Review Areas

### 1️⃣ Physics Interpretation & Prior Comparison
**What to check:** Does the spectrum shape/magnitude make sense? How does it compare to the 2004 ALEPH reanalysis and world average?

**Key files:**
- `AnalysisNote/main.pdf` Sections 1, 8 (Introduction, Results)
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/unfolded_spectrum.pdf`
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/comparison_prior.pdf`

**Questions for reviewers:**
- [ ] Does the spectrum peak (~0.65) and width match hadronic Z decay expectations?
- [ ] Central range (0.60–0.95): Within 1σ of 2004 ALEPH reanalysis?
- [ ] Endpoint region (T>0.95) is ~30% higher. Plausible or concerning?
- [ ] Are other recent measurements (LEP, Tevatron, LHC) relevant comparisons?

**Comment format:**
```markdown
**Concern:** [Issue description]
**Evidence:** [Figure/page reference]
**Assessment:** [Plausible / Needs investigation / Inconsistent with]
**Severity:** [✓ OK / ⚠️ Clarification needed / ❌ Issue]
```

---

### 2️⃣ Systematic Uncertainties & Correlations
**What to check:** Are uncertainty sizes reasonable? Are dominant sources correct? Are bin-to-bin correlations physically justified?

**Key files:**
- `AnalysisNote/main.pdf` Section 7 + Table 5 (Systematic Uncertainties)
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_breakdown.pdf`
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/total_correlation_matrix.pdf`
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/covariance_matrix.csv`
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/correlation_matrix.csv`

**Questions for reviewers:**
- [ ] **Total uncertainty (8.43%):** Realistic for precision LEP measurement?
- [ ] **Theory dominance (6.1%):** Why so large vs. experimental (~2.8%)? Expected?
- [ ] **Hadronic correction (3.2%):** Is up/down envelope (post-MC) valid?
- [ ] **Correlation structure:** Why are off-diagonals small (ρ<0.3)? Physically sound?
- [ ] **Missing systematics:** Beam backgrounds, ISR/FSR, selection efficiency?

**Comment format:**
```markdown
**Component:** [Name]
**Magnitude:** OK / Too large (by ~Nσ) / Too small
**Rationale:** [Brief physics assessment]
**Evidence:** [Table/figure/literature reference]
**Recommendation:** [Accept / Investigate further / Revise]
```

---

### 3️⃣ Unfolding Methodology & Validation
**What to check:** Is IBU appropriate? Are closure tests satisfactory? Is the response matrix well-behaved?

**Key files:**
- `AnalysisNote/main.pdf` Section 6 + Table 2 (Analysis Method)
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/response_matrix.pdf`
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/closure_test_*.pdf` (iterations 4,5,6,10,100)
- `Unfolding/unfold_thrust.py` (lines 50–120, IBU configuration)
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json`

**Questions for reviewers:**
- [ ] **Method choice:** Is iterative Bayesian unfolding appropriate? Alternative (SVD, inversion)?
- [ ] **Iteration plateau:** Spectrum stable by N_iter=5? Closure residuals <5% in central range?
- [ ] **Response matrix:** 33% diagonal = high migration. Physically understood?
- [ ] **Iteration envelope:** Difference (N=4 vs 5 vs 6) small enough to justify choice?
- [ ] **Hadronic correction:** Applied post-unfolding — sensible? Any bias risk?

**Comment format:**
```markdown
**Method aspect:** [Specific concern]
**Status:** Acceptable / Needs clarification / Recommend change
**Validation:** [Specific plot/residual value checked]
**Rationale:** [Physics reasoning]
**Requested change:** [If needed, e.g., "Switch to SVD with k=10"]
```

---

### 4️⃣ Code Reproducibility & Documentation
**What to check:** Can the analysis be reproduced? Are code and narrative aligned?

**Key files:**
- `REVIEWER_GUIDE.md` (quick-start)
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json` (reproducibility record)
- `Unfolding/scripts/run_thrust_prelim_workflow.py` (orchestration)
- `DataProcessing/include/thrustTools.h` (thrust algorithm, n=3 case documented)
- `Unfolding/scripts/build_prelim_uncertainty_summary.py` (covariance assembly)

**Questions for reviewers:**
- [ ] **Traceability:** Can you trace claims from PDF → code → outputs?
- [ ] **Reproducibility:** Run script with workflow options — identical outputs?
- [ ] **Algorithm clarity:** n=3 special case (max-magnitude) — understood? Impact on central range?
- [ ] **Systematic propagation:** Understand covariance assembly from code?
- [ ] **Documentation:** Are all significant calculations explained?

**Comment format:**
```markdown
**Issue:** [Specific concern]
**Severity:** Critical / High / Low
**Location:** [File, line number or section]
**Impact:** [Blocks reproduction / Unclear / Minor]
**Suggested fix:** [Specific change, e.g., "Add comment at line X"]
```

---

## 📤 How to Comment

**Option 1 (Preferred):** Reply on this issue with structured comments matching the format above.

**Option 2:** Create a markdown document in `Plans/physics_review_feedback_[YourName]_2026-02-27.md` following the structure of `PHYSICS_REVIEW_REQUEST.md` and submit as PR.

**Option 3:** Submit PR with suggested edits, referencing this issue.

---

## 🔗 Quick Links

| Resource | Path |
|----------|------|
| Analysis Note | `AnalysisNote/main.pdf` |
| Summary Plots | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/` |
| Detailed Review Guide | `PHYSICS_REVIEW_REQUEST.md` |
| Reproducibility Record | `Studies/PreliminaryResult/2026-02-17_thrust_iter5/workflow_summary.json` |
| Reviewer Quickstart | `REVIEWER_GUIDE.md` |

---

## 🎯 In Scope / Out of Scope

**We request feedback on:**
- Physics validity & prior comparisons
- Uncertainty sizes, correlations, treatment
- Methodology validation (IBU, closure tests)
- Reproducibility & code clarity

**Out of scope:**
- Code optimization/refactoring
- New observables (thrust-major/minor) — future work
- Full ALEPH data reanalysis

---

## ⏱️ Timeline (TBD)

- Feedback window: [Suggest timeline]
- Discussion period: [Suggest timeline]
- Resolution: [Suggest timeline]

Thank you for expert review!
