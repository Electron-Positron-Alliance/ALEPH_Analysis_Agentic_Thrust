# Skills Development and C-Parameter Measurement Plan (2026-03-06)

## 1. Purpose of This Document

This document serves three purposes:

1. **Record the process** by which the ALEPH analysis skill file was developed, including the iterative physicist-advisor feedback loop that produced it
2. **Assess the current skill** — its verifiable strengths and documented limitations — as a baseline before the next measurement
3. **Plan the C-parameter measurement** as the proving ground, with explicit supervisor checkpoints and an evaluation framework for measuring whether agent performance improved from the thrust measurement to C-parameter

The underlying question this document is designed to answer over time: **does an AI agent with a well-constructed skills file perform a new measurement better than it performed the previous one, in the same way a student improves from their first experiment to their second?**

---

## 2. Skills Development Process

### 2.1 Starting Point

The initial skill file (`skill.md`) was a monolithic ~200-line document covering identity, authority structure, event selection, thrust analysis, systematics, validation gates, output conventions, figure style, and analysis note traceability. It was written from memory and from reading the analysis note — not from reading the source code.

### 2.2 First Round of Physicist Feedback

The physicist identified three generalization requirements:

- **Multiple energies**: the skill was hardcoded to √s = 91.2 GeV; the program intends to cover a range of CM energies
- **Multiple observables**: the skill was thrust-only; C-parameter, HJM, and others need to be supported
- **Broader scope**: plotting preferences and analysis note structure needed to be explicitly documented

The skill was rewritten to generalize on all three axes. Observable definitions for C and HJM were added as stubs. The plotting style section was expanded using the actual source files (`style.py`, `canvas_utils.py`, `PlotConfig.py`).

### 2.3 Second Round: Reading the Source Code

After the generalization rewrite, the source files `analysisTypes.h` and `analysisCompute.h` were read for the first time. This revealed **three factual errors** that had persisted from the original skill and were carried forward into the rewrite:

| Error | Consequence if uncorrected |
|-------|---------------------------|
| pwflag table inverted (1=Photons, 2=Neutral hadrons) | Agent would apply wrong particle categories to phase-space checks, misinterpret Data/MC comparisons |
| Phase space described as "pwflag=0 + pwflag=1,2" | Agent would not understand that muons and electrons (pwflag 1,2) enter the observable |
| Event selection described as thrust-axis cut at 0.9 | Agent would misdiagnose any event selection issue; wrong axis, wrong threshold |

These errors originated in the analysis note itself, which uses informal language that does not precisely match the code. The skill had been written from the note rather than from the code. This is a general risk: **analysis notes lag the code** and should not be the primary source of truth for a skills file.

Additional omissions identified: MC-type-specific data cleaning (beam-pipe artifacts, conversion electrons, PYTHIA8 photon exclusion), the `passesNTupleAfterCut` pre-filter, and the hardcoded `passEventSelection=true` for gen-level trees.

### 2.4 Factorization

The physicist proposed factorizing the monolithic skill into a compact core (`skill.md`) plus five supplementary files:

- `physics_concepts.md` — observable definitions, correction formulas, physics rationale for cuts, comparison targets
- `expert_supervisor.md` — validation diagnostics, Data/MC judgment calls, failure mode playbook, communication log requirements
- `code_reference.md` — full pipeline, all selection parameters, MC-specific cleaning, plotting scripts
- `plotting_style.md` — complete ALEPH style guide, color conventions, canvas layout
- `analysis_note.md` — LaTeX structure, table regeneration, traceability rules

The core `skill.md` became a command center: always-loaded authority structure, corrected quick-reference tables, critical pitfall table, and an explicit file index telling the agent which supplementary file to load for which task.

The `expert_supervisor.md` is the most novel component — it encodes judgment that was entirely absent before: step-by-step diagnostics per validation gate, acceptable vs. unacceptable Data/MC discrepancy thresholds, response matrix inspection criteria, ISR sanity checks, and a decision table (proceed vs. stop) for borderline cases.

### 2.5 Current State

The skill suite now lives at `~/.claude/skills/aleph-ee-analysis/` with six files totaling approximately 760 lines. The corrected pwflag table and event selection axis appear in both `skill.md` (pitfall table) and `physics_concepts.md` (authoritative definitions). The expert supervisor content is completely new relative to the original skill.

---

## 3. Skill Strengths and Limitations

### 3.1 Verifiable Strengths

| Strength | Basis |
|----------|-------|
| Correct pwflag table | Verified from PassChargedTrack, PassNeutral, IsConversionElectron, Nisr tagging, CleanDataNeutralHadron in source code |
| Correct event selection axis (sphericity, not thrust) | Verified from ComputeEventResult in analysisCompute.h |
| Complete MC-type cleaning documentation | Verified from analysisCompute.h |
| ISR direction convention (ISR0=OFF/numerator, ISR1=ON/denominator) | Verified from analysis note equations and physics argument |
| Pitfall table | Directly grounded in source code; not inferred |
| Validation gate diagnostics | Grounded in experience with the thrust measurement; specific and actionable |
| Authority structure | Stable and physicist-approved |

### 3.2 Known Limitations

| Limitation | Risk | Mitigation |
|------------|------|------------|
| `unfold_thrust.py` and workflow scripts not fully characterized in skill | Agent may generalize incorrectly without reading them first | Skill instructs: read before modifying; checkpoint required |
| Observable-specific expectations (f_diag, uncertainty budget) only documented for thrust | Agent cannot self-assess whether C or HJM response matrix is anomalous | Supervisor checkpoint required after first response matrix |
| Theory reweighting scope not confirmed for non-thrust observables | Weights derived from thrust may or may not apply to C-parameter | Physicist must confirm before systematics run |
| ISR cache only covers thrust | C-parameter ISR correction requires new cache | Pre-processing step must be identified and planned |
| Analysis note may lag code in other areas not yet discovered | Skill may contain additional inherited inaccuracies | Ongoing: always read source before trusting the note |
| No documented performance baseline | Cannot quantitatively compare thrust-era agent behavior vs. C-parameter-era | This document establishes the baseline; record outcomes against it |

### 3.3 What the Skill Does Not Cover

- Build system (Makefile) beyond a brief mention in `code_reference.md`
- File merging (the `-MERGED` convention in data file names)
- Absolute cross-section normalization (all current measurements use normalized distributions)
- Multi-observable correlation (if C and T are measured from the same dataset, are their covariances correlated?)
- Run-by-run data quality and luminosity accounting

These are acceptable gaps for the current scope. They should be added if the program extends to absolute cross-sections or correlated multi-observable fits.

---

## 4. C-Parameter Measurement: Supervisor Assessment

### 4.1 What Can Proceed Without Oversight

| Task | Confidence | Basis |
|------|-----------|-------|
| Run `runAnalyze.py` on existing data/MC files | High | CParameter branch already computed by Analyze.cxx; no code changes needed |
| Run all systematic variations | High | Variations are observable-agnostic |
| Add CParameter to plotting config | High | Boilerplate extension to PlotConfig.py, plot.py |
| Compute hadronic correction | High | C_had = N_genBefore / N_gen; formula is observable-agnostic |
| Assemble covariance components | High | Template rule is observable-agnostic |
| Write output files and workflow_summary.json | High | Mechanical |

### 4.2 Technical Risks (Require Reading Before Acting)

| Task | Risk | Required action |
|------|------|----------------|
| Generalizing `unfold_thrust.py` | Unknown degree of thrust-specific hardcoding | Read file in full; propose generalization plan; get physicist approval before modifying |
| Generalizing `run_thrust_prelim_workflow.py` and `build_prelim_uncertainty_summary.py` | Same as above | Read both; identify every observable-specific parameter |
| ISR correction for C-parameter | ISR cache is thrust-only; ISR files may not have CParameter computed | Check whether isr0_ALL.root / isr1_ALL.root have been processed through Analyze.cxx; if not, plan that step |
| Theory reweighting | Weights may be thrust-derived | Confirm with physicist whether event-level weights apply to C-parameter |

### 4.3 Physics Decisions Reserved for Physicist

These are blockers. The agent should not proceed past these points without explicit physicist input.

| Decision | Why |
|----------|-----|
| Binning for C-parameter | Distribution shape differs from thrust (peaks ~0.3, spike at C→0); bin width affects resolution and comparability to ALEPH 2004 |
| Central range definition | Equivalent of 0.60 ≤ T < 0.95 for C-parameter must be established |
| Fit window | Equivalent of 0.505 ≤ T < 1.00 for C-parameter; affects covariance invertibility check |
| Response matrix f_diag expectation | C-parameter has higher soft-particle sensitivity → more migration expected; need physicist's expected range before declaring anomaly |
| Iteration count | N_iter=5 was validated for thrust; confirm it is appropriate for C-parameter or re-run scan |
| Theory reweighting validity | Confirm event-level weights can be applied to C-parameter before running theory systematic |

### 4.4 Supervisor Checkpoints

The following are mandatory stops where the agent reports findings and waits for physicist approval before continuing:

| Checkpoint | Trigger | What agent reports |
|------------|---------|-------------------|
| **CP1: Binning and ranges** | Before any unfolding | Proposed C-parameter binning, central range, fit window |
| **CP2: Unfolding script plan** | After reading `unfold_thrust.py` and workflow scripts | List of every thrust-specific hardcoded element; proposed generalization approach |
| **CP3: ISR preprocessing** | Before building ISR cache | Whether ISR files have CParameter; proposed processing steps |
| **CP4: First response matrix** | After first unfolding run | f_diag, miss rate distribution, diagonal fraction plot |
| **CP5: First unfolded spectrum** | Before running systematics | Comparison with ALEPH 2004 C-parameter; any anomalies flagged |
| **CP6: Full uncertainty budget** | After all systematics assembled | Per-component breakdown; comparison with thrust budget magnitudes |
| **CP7: Result promotion** | Before creating a dated result directory | All validation gates passed; physicist sign-off |

---

## 5. Evaluation Framework: Did the Agent Improve?

### 5.1 Motivation

The thrust measurement was the agent's first full measurement in this framework, performed without a formalized skill file. C-parameter will be the second, performed with the skill suite developed in this session. The question is whether the skills file produces measurable improvement — and how to quantify it.

### 5.2 Dimensions of Improvement

| Dimension | How to assess |
|-----------|--------------|
| **Factual accuracy** | Did the agent apply the correct pwflag mapping, event selection axis, and ISR direction on the first attempt without being corrected? (For thrust these were errors discovered late.) |
| **Proactive identification of unknowns** | Did the agent flag the unfolding script scope, ISR cache gap, and theory reweighting validity before being prompted? |
| **Checkpoint discipline** | Did the agent stop at the defined checkpoints without physicist prompting, or did it proceed past them? |
| **Pitfall avoidance** | Did any pitfall from the pitfall table manifest during the C-parameter measurement? Which ones? |
| **Supervisor intervention count** | How many mid-task corrections did the physicist need to make, compared to the thrust measurement? |
| **Time to valid result** | How many back-and-forth iterations were required to produce a result that passed all validation gates? |

### 5.3 Baseline from Thrust Measurement

Known corrections that were required during the thrust measurement (from Plans/ records):
- Wrong default generator tree in unfolding script (P0 bug, 2026-02-13)
- Closure mode incorrectly required data file (P1 bug, 2026-02-13)
- Analysis note language on event selection axis did not match code

These represent the baseline: a measurement where significant implementation errors were discovered during execution and required physicist intervention. The goal is that the C-parameter measurement has fewer such corrections, particularly for issues that are now documented in the skill.

### 5.4 Recording Outcomes

After the C-parameter measurement is complete, add a section to this document recording:

1. Which checkpoints triggered physicist corrections (and what the corrections were)
2. Which pitfalls from the pitfall table were encountered
3. Which pitfalls were avoided that would likely have been hit without the skill
4. Any new pitfalls discovered that should be added to the skill
5. Any skill content that turned out to be incorrect or incomplete
6. An overall qualitative assessment: did the agent perform more like a senior graduate student (anticipating problems, asking the right questions) or a first-year student (catching problems only after they cause failures)?

---

## 6. Next Immediate Actions

In order:

1. **Physicist confirms** C-parameter binning, central range, fit window (CP1)
2. **Agent reads** `unfold_thrust.py`, `run_thrust_prelim_workflow.py`, `build_prelim_uncertainty_summary.py` in full and produces a generalization plan (CP2)
3. **Agent checks** whether ISR files have been processed for CParameter (CP3)
4. **Physicist confirms** theory reweighting validity for C-parameter
5. **Agent begins** data processing and detector-level comparison plots
6. **Proceed through checkpoints CP4–CP7** in sequence

---

## 7. Open Questions for Future Skill Iteration

These are things this session did not resolve that should inform the next revision of the skill file:

- What is the expected f_diag range for C-parameter and HJM at ALEPH?
- Are the theory generator weights event-level (universal) or observable-specific?
- What is the correct fit window and central range for C-parameter and HJM?
- Does the `-MERGED` convention need to be documented for automation scripts?
- Are there additional analysis note vs. code discrepancies beyond the three found this session?
- How should the skill handle absolute cross-sections if the program extends there?
- When C-parameter and thrust are measured from the same dataset, should the skill document correlated covariance treatment?
