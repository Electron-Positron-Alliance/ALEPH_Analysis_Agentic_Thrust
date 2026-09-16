#!/usr/bin/env python3
"""Compare two unfolding outputs object by object.

    source analysis/env.sh
    python analysis/compare_runs.py <reference.root> <candidate.root>

Reports, for every TH1/TH2 the reference contains, the largest relative bin
difference against the candidate. Exits non-zero if any object differs by more
than --tol (default 0), so a rerun that should reproduce a stored result can be
checked rather than asserted.

This is the check behind the claim that the restored code reproduces the
published nominal output exactly: all 13 objects at zero relative difference.
"""
import argparse
import sys


def bins(h):
    cls = h.ClassName()
    if cls.startswith("TH1"):
        return [(h.GetBinContent(i),) for i in range(1, h.GetNbinsX() + 1)]
    if cls.startswith("TH2"):
        return [(h.GetBinContent(i, j),)
                for i in range(1, h.GetNbinsX() + 1)
                for j in range(1, h.GetNbinsY() + 1)]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--tol", type=float, default=0.0,
                    help="max allowed relative difference (default 0, i.e. bit-exact)")
    a = ap.parse_args()

    import ROOT
    ROOT.gROOT.SetBatch(True)
    ref = ROOT.TFile.Open(a.reference)
    cand = ROOT.TFile.Open(a.candidate)
    if not ref or ref.IsZombie():
        sys.exit(f"cannot open reference: {a.reference}")
    if not cand or cand.IsZombie():
        sys.exit(f"cannot open candidate: {a.candidate}")

    bad = 0
    print(f"  {'object':34s} {'max rel diff':>13} {'bins':>7}  verdict")
    for key in ref.GetListOfKeys():
        name = key.GetName()
        h_ref, h_cand = ref.Get(name), cand.Get(name)
        if not h_cand:
            print(f"  {name:34s} {'-':>13} {'-':>7}  ABSENT from candidate")
            bad += 1
            continue
        pr, pc = bins(h_ref), bins(h_cand)
        if pr is None:
            continue
        if len(pr) != len(pc):
            print(f"  {name:34s} {'-':>13} {'-':>7}  BINNING differs")
            bad += 1
            continue
        worst, nz = 0.0, 0
        for (x,), (y,) in zip(pr, pc):
            if abs(x) > 1e-12:
                nz += 1
                worst = max(worst, abs(y - x) / abs(x))
        ok = worst <= a.tol
        bad += not ok
        print(f"  {name:34s} {worst:13.3e} {nz:7d}  "
              + ("EXACT" if worst == 0 else ("within tol" if ok else "DIFFERS")))

    print(f"\n{'FAILED' if bad else 'ALL OBJECTS MATCH'}"
          + (f" -- {bad} object(s) outside tolerance" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
