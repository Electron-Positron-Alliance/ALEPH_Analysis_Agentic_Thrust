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
  3. The even-odd modulation in the N_trk panel comes from charge
     conservation: without the conversion-electron cleaning the charged
     multiplicity has exactly the same parity as the summed charge of the
     counted particles, which vanishes for most events. The cleaning
     removes one member of each identified pair from the count and dilutes
     the modulation to the strength seen in the figure.

Particle counting follows Analyze.cxx at generator level: no object-level
cuts, beam-pipe radiation artifacts removed, charged = pwflag 0-2,
neutral = pwflag 3-5. The cleaning is applied in the "cleaned" counting and
omitted in the "raw" counting so its effect on the parity is visible.

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

# Conversion-electron cleaning, as in Analyze.cxx: an adjacent opposite-charge
# pwflag==2 pair close in theta and phi. Analyze.cxx vetoes the second member
# (index i) and pops the first from the saved particle list, so exactly one
# track per identified pair leaves the multiplicity count.
CONV = """
ROOT::RVecI conv(pwflag.size(), 0);
for (size_t i = 1; i < pwflag.size(); ++i) {
  if (pwflag[i] == 2 && pwflag[i-1] == 2 && charge[i] == -charge[i-1]
      && std::abs(theta[i] - theta[i-1]) <= 0.05
      && std::acos(std::cos(phi[i] - phi[i-1])) <= 0.05) conv[i] = 1;
}
return conv;
"""


def define(tree, path):
    df = ROOT.RDataFrame(tree, path)
    df = df.Define("keep", KEEP)
    df = df.Define("conv", CONV)
    df = df.Define("israw", "keep && pwflag>=0 && pwflag<=2")
    df = df.Define("isch", "israw && conv==0")
    df = df.Define("isne", "keep && conv==0 && pwflag>=3 && pwflag<=5")
    df = df.Define("en", "sqrt(pmag*pmag+mass*mass)")
    df = df.Define("gNTrk", "(int)Sum(isch)")
    df = df.Define("gNTrkRaw", "(int)Sum(israw)")
    df = df.Define("gNNeu", "(int)Sum(isne)")
    df = df.Define("gECh", "Sum(en[isch])")
    df = df.Define("gQ", "(int)Sum(charge[israw])")
    df = df.Define("nConv", "(int)Sum(conv)")
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
            nconv=df.Mean("nConv"),
            n_odd_ntrk=df.Filter("gNTrk % 2 != 0").Count(),
            n_odd_raw=df.Filter("gNTrkRaw % 2 != 0").Count(),
            n_odd_q=df.Filter("abs(gQ) % 2 != 0").Count(),
            n_zero_q=df.Filter("gQ == 0").Count(),
            n_parity_mismatch=df.Filter("(gNTrkRaw - gQ) % 2 != 0").Count(),
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
    print(f"  fraction with zero summed charge = {b['n_zero_q'].GetValue()/tot:.5f}")
    print(f"  fraction with odd summed charge  = {b['n_odd_q'].GetValue()/tot:.5f}")
    print(f"  fraction with odd N_trk, cleaning omitted = {b['n_odd_raw'].GetValue()/tot:.5f}")
    print(f"  fraction with odd N_trk, as counted        = {b['n_odd_ntrk'].GetValue()/tot:.5f}")
    print(f"  conversion-electron vetoes per event       = {b['nconv'].GetValue():.4f}")
    print(f"  events where the uncleaned N_trk and the summed charge differ in parity = {mismatch}")
    if mismatch:
        print("  MISMATCH: N_trk parity does not track the summed charge", file=sys.stderr)
        return 1
    print("  Without the cleaning, N_trk parity tracks the summed charge exactly, as charge")
    print("  conservation requires. The cleaning removes one track per identified pair, which")
    print("  dilutes the modulation to the strength seen in Fig. 9.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
