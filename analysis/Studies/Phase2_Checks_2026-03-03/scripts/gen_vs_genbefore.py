#!/usr/bin/env python3
"""
tgen vs tgenBefore: why the two generator-level references in Fig. 9 overlap.

Referee question (R2, Sec. 6.4): the tgenBefore multiplicity and energy
distributions were expected to sit above tgen, and only cos(theta_Sph)
differs. This script checks the statements the answer rests on, reading the
archived MC ntuple directly. Each is asserted, and the script exits non-zero
if any fails.

  1. tgen is an exact subset of tgenBefore in (RunNo, EventNo).
  2. The acceptance tgen/tgenBefore varies little across generator
     multiplicity but collapses outside |cos(theta_Sph)| < 0.8, so the
     normalized multiplicity and charged-energy spectra coincide through
     the bulk and only cos(theta_Sph) separates the two curves. The
     agreement is asserted over the bulk of each spectrum, not over the
     sparse tails: a small residual depletion survives at low charged
     energy, near the hadronic charged-energy selection boundary, and is
     reported rather than asserted on.
  3. The even-odd modulation in the N_trk panel comes from charge
     conservation: without the conversion-electron cleaning the charged
     multiplicity has exactly the same parity as the summed charge of the
     counted particles, which vanishes for most events. The cleaning
     removes one member of each identified pair from the count and dilutes
     the modulation to the strength seen in the figure.

Particle counting follows Analyze.cxx at generator level: the kinematic
track and neutral selections are applied at detector level only, while the
beam-pipe radiation artifact removal and the conversion-electron cleaning
apply to the generator trees as well. Charged = pwflag 0-2, neutral =
pwflag 3-5. The cleaning is applied in the "cleaned" counting and omitted in
the "raw" counting so its effect on the parity is visible.

cos(theta_Sph) is read from the tree's STheta branch, whereas Analyze.cxx
recomputes the sphericity axis from its own selected particle list. Pass
--analyze-output with an Analyze.exe no_event_sel tgen file to assert the
two agree; without it the check is skipped and the difference is noted.

Usage (from repo root):
    python analysis/Studies/Phase2_Checks_2026-03-03/scripts/gen_vs_genbefore.py \
        --input /path/to/alephMCRecoAfterCutPaths_1994.root \
        [--analyze-output /path/to/..._thrust_no_event_sel_tgen.root]

Author: AI agent (Claude), physicist direction: Anthony Badea
Date: 2026-09-15
"""

import argparse
import sys

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

# beam-pipe radiation artifacts, as removed in Analyze.cxx for generator trees
KEEP = "!(abs(phi)<=0.001 && pt>0.00099 && pt<0.001009 && charge==0)"

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

# Statement 2 thresholds. The multiplicity acceptance must stay within
# MULT_SPREAD_MAX max/min across populated bins, while the outermost
# cos(theta_Sph) bins must fall to below COS_COLLAPSE_MAX of the central
# plateau. Measured on the archived 1994 MC: 1.10 and 0.09.
MULT_SPREAD_MAX = 1.25
COS_COLLAPSE_MAX = 0.5
# max allowed per-bin deviation between the two normalized charged-energy
# spectra, over bulk bins (those holding at least BULK_FRAC of the sample).
# Tail bins below that occupancy are reported but not asserted on: they carry
# a genuine low-energy depletion from the charged-energy selection boundary.
ECH_SHAPE_MAX = 0.05
BULK_FRAC = 1e-3
# agreement required between the STheta branch and Analyze.cxx's recomputed
# cos(theta_Sph), per bin, when --analyze-output is given
COS_DEF_TOL = 0.05
MIN_BIN = 100


def define(tree, path):
    df = ROOT.RDataFrame(tree, path)
    df = df.Define("keep", KEEP)
    df = df.Define("conv", CONV)
    df = df.Define("israw", "keep && pwflag>=0 && pwflag<=2")
    df = df.Define("isch", "israw && conv==0")
    df = df.Define("isne", "keep && pwflag>=3 && pwflag<=5")
    df = df.Define("en", "sqrt(pmag*pmag+mass*mass)")
    df = df.Define("gNTrk", "(int)Sum(isch)")
    df = df.Define("gNTrkRaw", "(int)Sum(israw)")
    df = df.Define("gNNeu", "(int)Sum(isne)")
    df = df.Define("gECh", "Sum(en[isch])")
    df = df.Define("gQ", "(int)Sum(charge[israw])")
    df = df.Define("nConv", "(int)Sum(conv)")
    # archived sphericity axis; see the module docstring on how this differs
    # from the axis Analyze.cxx recomputes and fills into h_cosThetaSph
    df = df.Define("cosThetaSphTree", "cos(STheta)")
    return df


def acceptance(a, b, label, fmt):
    """Print the per-bin ratio a/b and return it for populated bins."""
    print(f"  vs {label}:")
    out = []
    for i in range(1, a.GetNbinsX() + 1):
        na, nb = a.GetBinContent(i), b.GetBinContent(i)
        if nb < MIN_BIN:
            continue
        out.append((a.GetBinCenter(i), na / nb))
        print(f"    {fmt.format(a.GetBinCenter(i))}  tgen/tgenBefore={na/nb:6.4f}")
    return out


def normalized_shape_diff(a, b, min_frac=0.0):
    """Max |b/a - 1| over bins of a, split into bulk and tail.

    A bin is bulk if it holds at least max(MIN_BIN, min_frac * N) entries of
    a. Returns (bulk_worst, tail_worst), either None if no such bin exists.
    """
    ia, ib = a.Integral(), b.Integral()
    if ia <= 0 or ib <= 0:
        return None, None
    floor = max(MIN_BIN, min_frac * ia)
    bulk = tail = None
    for i in range(1, a.GetNbinsX() + 1):
        na = a.GetBinContent(i)
        if na < MIN_BIN:
            continue
        dev = abs((b.GetBinContent(i) / ib) / (na / ia) - 1.0)
        if na >= floor:
            bulk = dev if bulk is None else max(bulk, dev)
        else:
            tail = dev if tail is None else max(tail, dev)
    return bulk, tail


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="archived ALEPH MC ntuple")
    p.add_argument("--analyze-output", default=None,
                   help="Analyze.exe no_event_sel tgen output, to check the "
                        "cos(theta_Sph) definition against the STheta branch")
    p.add_argument("--nthreads", type=int, default=4)
    args = p.parse_args()

    if args.nthreads > 1:
        ROOT.EnableImplicitMT(args.nthreads)

    failures = []

    dfs = {t: define(t, args.input) for t in ("tgen", "tgenBefore")}
    bookings = {}
    for t, df in dfs.items():
        bookings[t] = dict(
            n=df.Count(),
            ntrk=df.Mean("gNTrk"),
            nneu=df.Mean("gNNeu"),
            ech=df.Mean("gECh"),
            h_ntrk=df.Histo1D((f"ntrk_{t}", "", 61, -0.5, 60.5), "gNTrk"),
            h_ech=df.Histo1D((f"ech_{t}", "", 100, 0.0, 100.0), "gECh"),
            h_cos=df.Histo1D((f"cos_{t}", "", 20, -1.0, 1.0), "cosThetaSphTree"),
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
    print(f"  tgen unique={len(ids['tgen'])}  tgenBefore unique={len(ids['tgenBefore'])}")
    print(f"  tgen subset of tgenBefore: {subset}   "
          f"events only in tgenBefore: {len(ids['tgenBefore'] - ids['tgen'])}")
    if not subset:
        failures.append("tgen is not a subset of tgenBefore")
    if len(ids["tgen"]) != bookings["tgen"]["n"].GetValue():
        failures.append("(RunNo, EventNo) is not unique per event in tgen")

    print("\n=== 2. acceptance tgen/tgenBefore ===")
    mult = acceptance(bookings["tgen"]["h_ntrk"].GetValue(),
                      bookings["tgenBefore"]["h_ntrk"].GetValue(), "N_trk", "{:5.1f}")
    cos = acceptance(bookings["tgen"]["h_cos"].GetValue(),
                     bookings["tgenBefore"]["h_cos"].GetValue(), "cos(theta_Sph)", "{:+5.2f}")
    if not mult or not cos:
        failures.append("no populated bins for the acceptance check")
    else:
        vals = [r for _, r in mult]
        spread = max(vals) / min(vals)
        print(f"  multiplicity acceptance spread max/min = {spread:.3f} "
              f"(allowed < {MULT_SPREAD_MAX})")
        if spread >= MULT_SPREAD_MAX:
            failures.append(f"multiplicity acceptance spread {spread:.3f} "
                            f">= {MULT_SPREAD_MAX}: the loss is not flat in multiplicity")
        central = [r for c, r in cos if abs(c) < 0.7]
        outer = [r for c, r in cos if abs(c) > 0.9]
        if not central or not outer:
            failures.append("cos(theta_Sph) binning does not cover the plateau and the edges")
        else:
            plateau = sum(central) / len(central)
            edge = max(outer)
            print(f"  cos(theta_Sph) acceptance: plateau {plateau:.4f}, edge {edge:.4f}, "
                  f"edge/plateau = {edge/plateau:.4f} (allowed < {COS_COLLAPSE_MAX})")
            if edge / plateau >= COS_COLLAPSE_MAX:
                failures.append(f"cos(theta_Sph) acceptance does not collapse at the edges "
                                f"(edge/plateau {edge/plateau:.4f})")

    bulk, tail = normalized_shape_diff(bookings["tgen"]["h_ech"].GetValue(),
                                       bookings["tgenBefore"]["h_ech"].GetValue(),
                                       min_frac=BULK_FRAC)
    if bulk is None:
        failures.append("charged-energy spectrum has no bulk bins")
    else:
        print(f"  normalized E_Ch spectrum, max |genBefore/gen - 1|: "
              f"bulk {bulk:.4f} (allowed < {ECH_SHAPE_MAX}), "
              f"tail {tail:.4f}" if tail is not None else
              f"  normalized E_Ch spectrum, max |genBefore/gen - 1|: bulk {bulk:.4f}")
        print("  the tail deviation is the low-energy depletion at the charged-energy")
        print("  selection boundary, reported rather than asserted on")
        if bulk >= ECH_SHAPE_MAX:
            failures.append(f"normalized charged-energy spectra differ by {bulk:.4f} "
                            f"in the bulk")

    print("\n=== 2b. cos(theta_Sph) definition ===")
    if args.analyze_output:
        tf = ROOT.TFile.Open(args.analyze_output, "READ")
        if not tf or tf.IsZombie():
            failures.append(f"cannot open {args.analyze_output}")
        else:
            h_recomp = tf.Get("h_cosThetaSph")
            if not h_recomp:
                failures.append(f"h_cosThetaSph not found in {args.analyze_output}")
            else:
                h_branch = bookings["tgen"]["h_cos"].GetValue()
                rebin = h_recomp.GetNbinsX() // h_branch.GetNbinsX()
                h_recomp = h_recomp.Rebin(rebin, "h_recomp") if rebin > 1 else h_recomp
                h_recomp.SetDirectory(0)
                d, _ = normalized_shape_diff(h_branch, h_recomp)
                if d is None:
                    failures.append("no populated bins to compare the two sphericity axes")
                else:
                    print(f"  STheta branch vs Analyze.cxx recomputed axis: "
                          f"max per-bin deviation {d:.4f} (allowed < {COS_DEF_TOL})")
                    if d >= COS_DEF_TOL:
                        failures.append("the STheta branch and the recomputed "
                                        "sphericity axis disagree")
            tf.Close()
    else:
        print("  skipped: pass --analyze-output to compare the STheta branch against the")
        print("  axis Analyze.cxx recomputes from its own selected particle list")

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
        failures.append(f"N_trk parity does not track the summed charge in {mismatch} events")
    else:
        print("  Without the cleaning, N_trk parity tracks the summed charge exactly, as charge")
        print("  conservation requires. The cleaning removes one track per identified pair, which")
        print("  dilutes the modulation to the strength seen in Fig. 9.")

    print()
    if failures:
        for f in failures:
            print(f"FAILED: {f}", file=sys.stderr)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
