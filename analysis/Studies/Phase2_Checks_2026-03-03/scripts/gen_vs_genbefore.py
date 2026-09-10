#!/usr/bin/env python3
"""
tgen vs tgenBefore: why the two generator-level references in Fig. 9 overlap.

Referee question (R2, Sec. 6.4): the tgenBefore multiplicity and energy
distributions were expected to sit above tgen, and only cos(theta_Sph)
differs. This script checks the three statements the answer rests on,
reading the archived MC ntuple directly:

  1. tgen is an exact subset of tgenBefore in (RunNo, EventNo).
  2. The acceptance tgen/tgenBefore is flat in generator multiplicity but
     falls sharply outside |cos(theta_Sph)| < 0.8, so normalized
     multiplicity and charged-energy spectra coincide.
  3. The generator-level charged multiplicity has the same parity as the
     summed charge of the counted particles, which drives the even-odd
     modulation seen in the N_trk panel.

Particle counting follows Analyze.cxx at generator level: no object-level
cuts, beam-pipe radiation artifacts removed, charged = pwflag 0-2,
neutral = pwflag 3-5.

Usage (from repo root):
    python analysis/Studies/Phase2_Checks_2026-03-03/scripts/gen_vs_genbefore.py \
        --input /path/to/alephMCRecoAfterCutPaths_1994.root

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-09-10
"""

import argparse
import sys

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

# beam-pipe radiation artifacts, as removed in Analyze.cxx for generator trees
KEEP = "!(abs(phi)<=0.001f && pt>0.00099f && pt<0.001009f && charge==0)"


def define(tree, path):
    df = ROOT.RDataFrame(tree, path)
    df = df.Define("keep", KEEP)
    df = df.Define("isch", "keep && pwflag>=0 && pwflag<=2")
    df = df.Define("isne", "keep && pwflag>=3 && pwflag<=5")
    df = df.Define("en", "sqrt(pmag*pmag+mass*mass)")
    df = df.Define("gNTrk", "(int)Sum(isch)")
    df = df.Define("gNNeu", "(int)Sum(isne)")
    df = df.Define("gECh", "Sum(en[isch])")
    df = df.Define("gQ", "(int)Sum(charge[isch])")
    df = df.Define("cosThetaSph", "cos(STheta)")
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="archived ALEPH MC ntuple")
    p.add_argument("--nthreads", type=int, default=4)
    args = p.parse_args()

    if args.nthreads > 1:
        ROOT.EnableImplicitMT(args.nthreads)

    dfs = {t: define(t, args.input) for t in ("tgen", "tgenBefore")}
    bookings = {}
    for t, df in dfs.items():
        bookings[t] = dict(
            n=df.Count(),
            ntrk=df.Mean("gNTrk"),
            nneu=df.Mean("gNNeu"),
            ech=df.Mean("gECh"),
            h_ntrk=df.Histo1D((f"ntrk_{t}", "", 61, -0.5, 60.5), "gNTrk"),
            h_cos=df.Histo1D((f"cos_{t}", "", 20, -1.0, 1.0), "cosThetaSph"),
            n_odd_ntrk=df.Filter("gNTrk % 2 != 0").Count(),
            n_odd_q=df.Filter("abs(gQ) % 2 != 0").Count(),
            n_zero_q=df.Filter("gQ == 0").Count(),
            n_parity_mismatch=df.Filter("(gNTrk - gQ) % 2 != 0").Count(),
        )

    print("=== event counts and generator-level means ===")
    for t, b in bookings.items():
        print(f"  {t:11s} N={b['n'].GetValue():>8d}  <NTrk>={b['ntrk'].GetValue():7.4f}"
              f"  <NNeu>={b['nneu'].GetValue():7.4f}  <ECh>={b['ech'].GetValue():8.4f} GeV")

    print("\n=== 1. subset check on (RunNo, EventNo) ===")
    ids = {}
    for t in dfs:
        cols = ROOT.RDataFrame(t, args.input).AsNumpy(["RunNo", "EventNo"])
        ids[t] = set(zip(cols["RunNo"].tolist(), cols["EventNo"].tolist()))
    subset = ids["tgen"] <= ids["tgenBefore"]
    extra = len(ids["tgenBefore"] - ids["tgen"])
    print(f"  tgen unique={len(ids['tgen'])}  tgenBefore unique={len(ids['tgenBefore'])}")
    print(f"  tgen subset of tgenBefore: {subset}   events only in tgenBefore: {extra}")

    print("\n=== 2. acceptance tgen/tgenBefore ===")
    for label, key, fmt in (("N_trk", "h_ntrk", "{:5.1f}"), ("cos(theta_Sph)", "h_cos", "{:+5.2f}")):
        a = bookings["tgen"][key].GetValue()
        b = bookings["tgenBefore"][key].GetValue()
        print(f"  vs {label}:")
        for i in range(1, a.GetNbinsX() + 1):
            nb, na = b.GetBinContent(i), a.GetBinContent(i)
            if nb < 100:
                continue
            print(f"    {fmt.format(a.GetBinCenter(i))}  tgen/tgenBefore={na/nb:6.4f}")

    print("\n=== 3. parity of the counted charged multiplicity ===")
    b = bookings["tgen"]
    tot = b["n"].GetValue()
    mismatch = b["n_parity_mismatch"].GetValue()
    print(f"  fraction of events with odd N_trk = {b['n_odd_ntrk'].GetValue()/tot:.5f}")
    print(f"  fraction of events with odd summed charge = {b['n_odd_q'].GetValue()/tot:.5f}")
    print(f"  fraction with zero summed charge = {b['n_zero_q'].GetValue()/tot:.5f}")
    print(f"  events where N_trk and summed charge differ in parity = {mismatch}")
    if mismatch:
        print("  MISMATCH: N_trk parity does not track the summed charge", file=sys.stderr)
        return 1
    print("  N_trk parity tracks the summed charge exactly, as charge conservation requires")
    return 0


if __name__ == "__main__":
    sys.exit(main())
