#!/usr/bin/env python3
"""Check that every input the paper's result depends on is present and has the
entry counts the manuscript claims.

    source reproduction/env.sh
    python reproduction/verify_inputs.py

Exits non-zero if anything is missing or a count disagrees with Table 1.
"""
import os
import sys

ALEPH = os.environ.get("ALEPH_DATA", os.path.expanduser(
    "~/Documents/Documents/ALEPH/ALEPH"))
LIVE = os.environ.get("ALEPH_LIVE", os.path.expanduser(
    "~/Documents/Documents/ALEPH/ALEPH_Analysis_Agentic_Thrust"))
LOGTAU = os.environ.get("ALEPH_LOGTAU", os.path.expanduser(
    "~/Documents/Documents/ALEPH/unfold-ee-logtau"))

# Table 1 of the manuscript: (tree, total entries)
RAW = [
    (f"{ALEPH}/LEP1Data1994_recons_aftercut-MERGED.root", "t", 1_365_440),
    (f"{ALEPH}/alephMCRecoAfterCutPaths_1994.root", "t", 771_597),
    (f"{ALEPH}/alephMCRecoAfterCutPaths_1994.root", "tgen", 771_597),
    (f"{ALEPH}/alephMCRecoAfterCutPaths_1994.root", "tgenBefore", 973_769),
]
# Derived ntuples: (tree, total, passEventSelection==1)
DERIVED = [
    (f"{LIVE}/DataProcessing/temp/"
     "LEP1Data1994_recons_aftercut-MERGED_thrust_nominal_t.root",
     "t", 1_365_440, 1_326_312),
    (f"{LIVE}/DataProcessing/temp/"
     "alephMCRecoAfterCutPaths_1994_thrust_nominal_t.root",
     "t", 771_597, 751_861),
]
EXTERNAL = [
    (f"{ALEPH}/HEPData-ins636645-v1-Table_54.csv", "ALEPH 2004 reference"),
    (f"{LOGTAU}/Results/ibu_results.npz", "prior IBU"),
    (f"{LOGTAU}/Results/unfold_thrust_ee_ZPole_ALEPH.h5", "prior OmniFold"),
    (f"{LOGTAU}/arxivPaperResults2025/theory_reweighting/training-bf3b5fc3",
     "theory weights (tag used by the published run)"),
]

bad = 0


def check_counts(path, tree, total, selected=None):
    global bad
    import ROOT
    ROOT.gROOT.SetBatch(True)
    if not os.path.exists(path):
        print(f"  MISSING  {path}")
        bad += 1
        return
    f = ROOT.TFile.Open(path)
    t = f.Get(tree)
    if not t:
        print(f"  NO TREE {tree!r}  {path}")
        bad += 1
        f.Close()
        return
    got = t.GetEntries()
    ok = got == total
    bad += not ok
    line = (f"  {'ok  ' if ok else 'BAD '} {os.path.basename(path)[:46]:46s} "
            f"{tree:11s} {got:>9,}")
    if not ok:
        line += f"  expected {total:,}"
    if selected is not None:
        n = sum(1 for e in t if e.passEventSelection == 1)
        sok = n == selected
        bad += not sok
        line += f"  sel {n:>9,}" + ("" if sok else f" expected {selected:,}")
    print(line)
    f.Close()


print("=== raw ALEPH open data (Table 1 totals) ===")
for path, tree, total in RAW:
    check_counts(path, tree, total)

print("\n=== derived ntuples (Table 1 totals and selected) ===")
for path, tree, total, sel in DERIVED:
    check_counts(path, tree, total, sel)

print("\n=== external inputs ===")
for path, what in EXTERNAL:
    present = os.path.exists(path)
    bad += not present
    print(f"  {'ok  ' if present else 'MISSING'} {what:52s} {path}")

print("\n=== not reproducible here (needs the workstation MC) ===")
print("  theory uncertainty  PYTHIA 8.3 / Herwig 7.3 / Sherpa 2.2 tgenBefore samples")
print("  ISR correction      same modern-generator samples")

print(f"\n{'FAILED' if bad else 'ALL INPUTS PRESENT AND COUNTS MATCH'}"
      + (f" -- {bad} problem(s)" if bad else ""))
sys.exit(1 if bad else 0)
