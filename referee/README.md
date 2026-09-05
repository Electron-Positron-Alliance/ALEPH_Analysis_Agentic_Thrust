# Referee response — working tracker

Live tracking for the HiHEP referee reports. The goal is that by the end of the
revision every one of the 84 comments has a written response and, where a change
is warranted, a commit that implements it.

- [`reviewer1.md`](reviewer1.md) — 21 comments
- [`reviewer2.md`](reviewer2.md) — 63 comments

## How to use it

Every comment has a stable ID (`R1-07`, `R2-42`). Each entry has four parts:

| field | meaning |
|---|---|
| blockquote | the referee's wording, **verbatim** — never edit this |
| `Assessment` | what we found when we checked the claim against the source and the code |
| `Response to referee` | the prose destined for the response letter |
| `Change` | the commit/PR that implements it, or why nothing changed |

Workflow per revision PR: pick the comment IDs it answers, write the
`Response to referee` text, make the manuscript change, and record the commit in
`Change`. Cite the IDs in the commit message so the mapping is recoverable from
`git log`. A comment is done when `Response to referee` is written *and* `Change`
is filled in — a comment we decline still needs both.

## Status

| status | R1 | R2 | total |
|---|---|---|---|
| Fixed | 2 | 12 | **14** |
| Partly fixed | 2 | 2 | **4** |
| No change needed | 1 | 2 | **3** |
| Open — easy | 4 | 18 | **22** |
| Open — substantive | 10 | 24 | **34** |
| Open — needs data machine | 2 | 5 | **7** |
| **total** | **21** | **63** | **84** |

None of the 84 has a written `Response to referee` yet. The 18 fixed/partly-fixed
have a manuscript change but no letter text.

## "Needs data machine"

Seven comments cannot be answered from this clone — they need the raw ntuples,
the plotting scripts, or a full unfolding re-run. Carrying them as a distinct
status is deliberate: they are the ones to batch when moving to the machine where
the data sits, not blockers on the text work.

Largest of them is R1-13 (sphericity-axis acceptance sculpting the thrust
distribution), which needs a new `cosThetaSph` variation branch in
`runAnalyze.py`, a re-run over the raw ntuples, and a full unfolding re-run.

## The earlier mechanical fixes

`Assessment` fields cite `(PR 01)`…`(PR 08)`. Those were a stacked set of PRs on
an older baseline, closed when `main` was reset to reproduce the June submission
exactly. The commits are intact on their branches and are being re-opened one at
a time as standalone PRs off `main`:

| cited as | branch | commit |
|---|---|---|
| PR 01 | `fix/journal-wording-internal-note` | `5e66afd` |
| PR 02 | `fix/cross-references` | `e3587f9` |
| PR 03 | `fix/define-terms-at-first-use` | `10aa6f0` |
| PR 04 | `fix/numeric-corrections` | `7b9effe` |
| PR 05 | `fix/table-clarity` | `7a648a8` |
| PR 06 | `fix/figure-captions` | `08df27a` |
| PR 07 | `fix/missing-citations` | `61a1c23` |
| PR 08 | `fix/abstract-and-intro-wording` | `9d3486f` |

PR 09 (the 12-author HiHEP list) is already on `main`, folded into the baseline.

## Reference

`main` reproduces the June 2026 HiHEP submission exactly — verified byte-for-byte
against `hihep_submission_v1.pdf`, tagged `hihep-submission-2026-06-exact`. Build
a marked-up diff of the revision against it with:

```
tools/make_pdfs.sh
```
