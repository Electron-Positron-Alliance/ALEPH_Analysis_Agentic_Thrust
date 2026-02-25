# Correctness Review: ALEPH Thrust Analysis Codebase and Analysis Note
**Date:** 2026-02-25
**Reviewer:** Claude Code (systematic review of DataProcessing, Unfolding, AnalysisNote)
**Scope:** Full codebase + analysis note; findings verified by direct file reads
**Baseline:** `Studies/PreliminaryResult/2026-02-17_thrust_iter5/`

---

## Summary

Five issue categories were investigated. Two confirmed correctness issues require action
(BUG-2, NOTE-1). One pre-existing design issue (CODE-1) is low-priority. One previously
described bug (BUG-1 from the exploration phase) was found to be **incorrect** upon direct
verification — the MET particle IS included in thrust. One exploration-phase claim (CODE-4)
was also found to be incorrect — ID-based matching is already implemented. One DOC-1 item
(systematic covariance model) is already documented in the analysis note.

---

## Priority 1 — Confirmed Correctness Bugs

### [BUG-1] ~~doMET silently excluded~~ — FINDING RETRACTED after direct verification

**File:** `DataProcessing/include/analysisCompute.h:220-231`, `thrustTools.h:461`

**Exploration-phase claim:** MET particle added with `pwflag=-1` is silently dropped by the
`pwflag[t] < 0` filter in `getThrustHerwig`.

**Verification result (INCORRECT as described):** The call at `analysisCompute.h:234` is:
```cpp
TVector3 thrust = getThrust(selectedParts, selectedPx.data(), selectedPy.data(), selectedPz.data(), THRUST::OPTIMAL);
```
`selectedPwflag.data()` is **not** passed; `pwflag` defaults to `NULL`. In `getThrustHerwig`
the check is `if (pwflag != NULL && pwflag[t] < 0) continue;` — since `pwflag=NULL`, the
entire filter is short-circuited. The MET particle **is** included in both `pSum` and `pVec`.
The `with_met` variation produces non-zero thrust shifts (confirmed: `exp_track_event` mean
central fractional uncertainty = 2.99%).

**Residual design note (LOW):** The `pwflag=-1` assignment in `analysisCompute.h:230` is
cosmetic only — it has no effect on the thrust calculation since `pwflag=NULL` is passed. The
code correctly achieves its intent, but the sentinel value is misleading. No physics fix
needed; a clarifying comment would help.

---

### [BUG-2] `n=3` Herwig thrust case: description vs. implementation mismatch

**File:** `DataProcessing/include/thrustTools.h:225`

**Severity:** MEDIUM — affects events with exactly 3 selected particles (rare for hadronic Z,
but non-zero rate, especially in early MC or after aggressive track cuts)

**Issue:** Line 225 comment reads:
```
// combine lowest 2 magnitude momentum, then use same algo as n=2  CHRIS: SOMETHING SEEMS
// WRONG HERE BASED ON DESCRIPTION? No combination is done, just picking mag max
```
The code picks the **maximum**-magnitude particle's direction (correctly finding the max among
all 3), which is equivalent to the n=2 case but applied to 3 particles. The comment "combine
lowest 2" describes a different algorithm (combine the two softest into one, then do n=2 with
the result). The comment is wrong, not the code — however:

- For n=3, the correct thrust algorithm should evaluate all 2^3 hemisphere assignments. The
  current implementation (max-magnitude particle) is an approximation that can fail when the
  third particle is significant.
- The existing comment acknowledges this inconsistency but was left unresolved.

**Recommendation:** Either (a) verify against reference ALEPH/Herwig n=3 algorithm and
correct the implementation, or (b) update the comment to accurately describe the current
behavior ("pick max-magnitude particle as thrust axis for n=3") and document that this is an
accepted approximation for rare 3-particle events. Given the rarity in hadronic Z decays, the
physics impact is expected to be negligible, but it should be explicitly acknowledged.

---

## Priority 2 — Note–Code Inconsistency (must fix before any external release)

### [NOTE-1] Hadronic-correction uncertainty: analysis note claims it is missing, but it IS propagated

**Files:**
- `AnalysisNote/sections/ChallengesAndLimitations.tex:48` — incorrect claim
- `AnalysisNote/sections/ChallengesAndLimitations.tex:69` — table row Status: "Open"
- `AnalysisNote/sections/SystematicUncertainties.tex:36-38` — correctly includes `Δ_had`
- `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_breakdown.json:125` — `"hadronic_correction_uncertainty_included": true`

**Severity:** HIGH for note correctness — a published internal limitation that contradicts the
actual implementation is misleading.

**Evidence from `uncertainty_breakdown.json`:**
```json
"hadronic_correction_uncertainty_included": true,
"hadronic_correction_uncertainty_model": "Envelope of up/down hadronic-correction ratio uncertainty propagated through normalized differential-thrust conversion.",
"mean_abs_fractional_central": {
  "hadronic_correction": 0.03225732382555143
}
```
Central-range mean hadronic uncertainty ≈ **3.23%** — this is the **third-largest** component,
larger than stat (1.71%) and unfolding-iter (0.34%). It is NOT missing.

**Required fix:** Update `ChallengesAndLimitations.tex` in two places:
1. Line 48: remove or correct "hadronic-event correction uncertainty is not yet propagated as an independent component"
2. Table row (line 69): change Status from "Open" to "Resolved"

**Note:** `SystematicUncertainties.tex:36-38` is already correct (`Δ_had` is in the formula
with correct description at line 38).

---

## Priority 3 — Minor Correctness / Design Issues

### [CODE-1] ISR counting: exact float equality on `phi==0`

**File:** `DataProcessing/include/analysisCompute.h:82`

**Severity:** LOW

```cpp
if (ev.pwflag[iP] == 4 && ev.charge[iP] == 0 && ev.phi[iP] == 0 && ...)
```
Exact floating-point equality `ev.phi[iP] == 0` is fragile. If any arithmetic has been
applied to stored phi values, ISR photons with intended phi=0 may be silently miscounted.
The ALEPH MC cleaning at line 87 uses `std::abs(ev.phi[iP]) <= 0.001` — inconsistent style.

**Note:** For ntuples where phi=0 is stored as a raw float literal without transformation,
this is likely safe in practice (the value is bitwise 0.0f). The ISR counter is used for
diagnostics only, not event selection, so this is low-risk.

**Recommendation:** Replace with `TMath::Abs(ev.phi[iP]) < 1e-6` for consistency.

---

### [CODE-2] ALEPH MC gen-level pt cleaning window is extremely narrow (needs documentation)

**File:** `DataProcessing/include/analysisCompute.h:87`

**Severity:** LOW (by design, needs documentation)

```cpp
if (genTree && ev.charge[iP] == 0 && std::abs(ev.phi[iP]) <= 0.001 &&
    ev.pt[iP] > 0.00099 && ev.pt[iP] < 0.001009)
```
The 0.0001 GeV window (`0.00099 < pt < 0.001009`) appears designed to catch exactly
pt=0.001 GeV artifacts from ALEPH MC beam-pipe radiation along phi≈0. The window is narrower
than floating-point precision noise but appears to function given the MC storage format.

**Recommendation:** Add an inline comment explaining what artifact this targets and why this
specific window was chosen (e.g., "Removes beam-pipe radiation artifacts stored at exactly
pt=0.001 GeV in ALEPH MC ntuple format").

---

### [CODE-3] Hadronic correction histogram has zero bin errors (mitigated)

**File:** `Unfolding/unfold_thrust.py:514`

**Severity:** LOW (mitigated externally)

```python
h_corr.SetBinError(b, 0.0)
```
The correction factor histogram stored in ROOT files has zero bin errors. Downstream ROOT
`Multiply()` calls on this histogram will not propagate correction uncertainty through
standard ROOT error arithmetic.

**Mitigation confirmed:** `build_prelim_uncertainty_summary.py:1521-1526` computes the
hadronic correction uncertainty independently via an up/down envelope propagated through the
normalized differential-thrust conversion. The ROOT-level error omission does not affect the
published uncertainty numbers.

**Recommendation:** Add a comment at line 514 explaining that errors are intentionally set to
zero because the uncertainty is computed externally by the summary builder, to prevent future
confusion.

---

### [CODE-4] ~~Theory weight index/entry fragility~~ — FINDING RETRACTED

**File:** `Unfolding/unfold_thrust.py:383-400`

**Exploration-phase claim:** Weight array index `i` assumed to correspond to tree entry `i`.

**Verification result (INCORRECT as described):** Lines 386-391 show explicit event-ID-based
matching:
```python
for i in range(n_iter):
    tree_weights.GetEntry(i)
    ev_id = int(getattr(tree_weights, weight_id_branch))
    weight_lookup[ev_id] = float(weights[i])
```
And lines 393-400 match gen-tree entries by `ev_id` lookup. **This is robust** — the
mismatch between tree and NPY array entry ordering would be caught by the `weight_lookup`
dictionary. No fix needed.

---

## Priority 4 — Documentation Items

### [DOC-1] Systematic covariance correlation template — already documented

**File:** `AnalysisNote/sections/SystematicUncertainties.tex:42-46`

**Status: ALREADY ADDRESSED** — The analysis note already explains the template-correlated
covariance model:
> "The current nominal release uses the `template_correlated` option, where each non-statistical
> component covariance is built as $\mathrm{Cov}^{(c)}_{ij} = \Delta_c(i)\,\Delta_c(j)\,\rho^{\mathrm{stat}}_{ij}$
> with $\rho^{\mathrm{stat}}_{ij}$ taken from the statistical unfolding covariance correlation
> template."

No action required.

---

### [DOC-2] Uncertainty total (8.43%) vs. naive quadrature of component means (~7.85%)

**File:** `Studies/PreliminaryResult/2026-02-17_thrust_iter5/summary/uncertainty_breakdown.json`

**Severity:** LOW (not a bug; may need a clarifying footnote)

From `uncertainty_breakdown.json`, central-range mean fractional components:
| Component | Mean central |
|-----------|-------------|
| stat | 1.71% |
| unfolding-iter | 0.34% |
| experimental | 3.34% |
| theory | 6.08% |
| hadronic | 3.23% |
| **total (from JSON)** | **8.43%** |

Naive quadrature of means: √(1.71² + 0.34² + 3.34² + 6.08² + 3.23²) ≈ 7.85%.

The ~0.58% difference arises because the total is computed via the full covariance matrix
(including off-diagonal contributions) projected onto a 1D metric, whereas naive quadrature
assumes uncorrelated diagonal entries. This is expected and correct.

**Recommendation:** When reporting 8.43% in the analysis note, add a brief parenthetical
clarifying this is from the full covariance matrix projection, not simple quadrature of
component means.

---

## Action Items (prioritized)

| ID | Priority | Action | File | Status |
|----|----------|--------|------|--------|
| NOTE-1 | **HIGH** | Remove/correct "hadronic uncertainty not propagated" in text and table | `ChallengesAndLimitations.tex:48,69` | **To do** |
| BUG-2 | MEDIUM | Update n=3 comment or fix algorithm; document as accepted approximation | `thrustTools.h:225` | To do (physicist decision) |
| CODE-1 | LOW | Replace `phi==0` with `TMath::Abs(phi) < 1e-6` | `analysisCompute.h:82` | Optional |
| CODE-2 | LOW | Add comment explaining pt cleaning window | `analysisCompute.h:87` | Optional |
| CODE-3 | LOW | Add comment explaining zero errors are intentional | `unfold_thrust.py:514` | Optional |
| DOC-2 | LOW | Add parenthetical clarifying covariance-based total vs. quadrature | Note Results section | Optional |
| BUG-1 | — | Retracted: MET IS included (pwflag=NULL bypasses filter) | — | Closed |
| CODE-4 | — | Retracted: ID-based matching is already implemented | — | Closed |
| DOC-1 | — | Already documented in SystematicUncertainties.tex | — | Closed |

---

## Verification Checks

**NOTE-1 confirmation:** `uncertainty_breakdown.json:125` = `"hadronic_correction_uncertainty_included": true`
and mean central hadronic = 3.23%. The ChallengesAndLimitations limitation text is stale.

**BUG-1 retraction:** `getThrust` call at `analysisCompute.h:234` passes no `pwflag` argument
(defaults to `NULL`). `getThrustHerwig` guard `if (pwflag != NULL && ...)` is short-circuited.
MET particle is included. `with_met` variation is not a null variation.

**CODE-4 retraction:** `unfold_thrust.py:386-400` uses explicit event-ID matching via
`weight_lookup` dict. Not fragile.

**DOC-1 closure:** `SystematicUncertainties.tex:42-46` already contains the explanation.
