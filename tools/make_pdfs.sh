#!/usr/bin/env bash
#
# Rebuild the manuscript and a marked-up diff against a reference version.
#
#   tools/make_pdfs.sh                        # HEAD vs the HiHEP submission
#   tools/make_pdfs.sh HEAD hihep-submission-2026-06
#   tools/make_pdfs.sh fix/table-clarity      # one PR vs the submission
#   tools/make_pdfs.sh HEAD sync/arxiv-2603.05735v2   # vs the bare arXiv v2
#
# Outputs (git-ignored):
#   build/current.pdf   the manuscript as of <NEW>
#   build/diff.pdf      <NEW> marked up against <OLD>
#                       red strikeout = removed, blue underline = added
#
# Both refs are read with `git archive`, so this works in any clone with no
# dependence on files outside the repo.
#
# Requires: pdflatex, bibtex, python3. latexdiff is NOT required -- tools/texdiff.py
# does the markup (latexdiff was unavailable where this was written).

set -euo pipefail

NEW_REF="${1:-HEAD}"
OLD_REF="${2:-hihep-submission-2026-06}"

REPO="$(git rev-parse --show-toplevel)"
HERE="$REPO/tools"
cd "$REPO"

for ref in "$NEW_REF" "$OLD_REF"; do
  git rev-parse --verify --quiet "$ref" >/dev/null || {
    echo "!! no such git ref: $ref" >&2
    echo "   available tags: $(git tag -l | tr '\n' ' ')" >&2
    exit 1
  }
done

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
OLD="$WORK/old"; NEW="$WORK/new"; DIF="$WORK/diff"
mkdir -p "$OLD" "$NEW"

echo "==> new : $NEW_REF  ($(git rev-parse --short "$NEW_REF"))"
echo "==> old : $OLD_REF  ($(git rev-parse --short "$OLD_REF"))"

git archive "$NEW_REF" | tar -x -C "$NEW"
git archive "$OLD_REF" | tar -x -C "$OLD"

# Diff .tex only. Figures always come from NEW so that a figure added since the
# reference cannot break the diff build.
find "$OLD" -name '*.pdf' -delete 2>/dev/null || true
cp -r "$NEW/figures" "$OLD/figures" 2>/dev/null || true

compile() {  # compile <dir> <label>
  local d="$1" label="$2"
  ( cd "$d"
    rm -f main.aux main.bbl main.blg main.log main.out main.toc main.pdf
    pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null 2>&1 || {
      echo "!! $label: pdflatex failed"; grep -m5 '^! ' main.log || true; return 1; }
    bibtex main >/dev/null 2>&1 || true
    pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
    pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
    printf "    %s: %s pages, %s errors, %s undefined-reference warnings\n" \
      "$label" \
      "$(pdfinfo main.pdf | awk '/^Pages/{print $2}')" \
      "$(grep -c '^! ' main.log || true)" \
      "$(grep -ci undefined main.log || true)"
  )
}

echo "==> building current"
compile "$NEW" current

echo "==> generating markup diff"
python3 "$HERE/texdiff.py" "$OLD" "$NEW" "$DIF"

echo "==> building diff"
compile "$DIF" diff

mkdir -p "$REPO/build"
cp "$NEW/main.pdf" "$REPO/build/current.pdf"
cp "$DIF/main.pdf" "$REPO/build/diff.pdf"

# Faithfulness check: stripping every \DIFdel and unwrapping every \DIFadd must
# reproduce the NEW source. If it does not, the diff is lying -- do not send it.
echo "==> verifying the diff is faithful"
python3 - "$DIF" "$NEW" <<'PY'
import os, re, sys
def mb(s, i):
    d = 0
    while i < len(s):
        if s[i] == "\\": i += 2; continue
        if s[i] == "{": d += 1
        elif s[i] == "}":
            d -= 1
            if d == 0: return i + 1
        i += 1
    return -1
def resolve(t):
    for macro in ("DIFadd", "DIFdel"):
        pat = "\\" + macro + "{"
        while True:
            k = t.find(pat)
            if k == -1: break
            o = k + len("\\" + macro); e = mb(t, o)
            if e == -1: break
            t = t[:k] + (t[o+1:e-1] if macro == "DIFadd" else "") + t[e:]
    return t
def norm(s):
    s = re.sub(r"\s+", " ", s)
    # whitespace after a tie is not a content difference: emitting a never-mark
    # command bare can turn "Sec.~\ref{x}" into "Sec.~ \ref{x}", same rendering
    return re.sub(r"~\s+", "~", s).strip()
dif, new = sys.argv[1], sys.argv[2]
ok = bad = 0
for root, _, files in os.walk(dif):
    for fn in sorted(files):
        if not fn.endswith(".tex"): continue
        rel = os.path.relpath(os.path.join(root, fn), dif)
        dt = open(os.path.join(dif, rel), encoding="utf-8").read()
        if "DIFadd" not in dt and "DIFdel" not in dt: continue
        got = resolve(dt)
        if rel == "main.tex":
            got = re.sub(r"%% ---- diff markup.*?%% ---- end diff markup ----", "", got, flags=re.S)
        if norm(got) == norm(open(os.path.join(new, rel), encoding="utf-8").read()):
            ok += 1
        else:
            bad += 1; print(f"    MISMATCH {rel}")
print(f"    {ok} changed files reproduce the current source exactly"
      + (f"; {bad} MISMATCHED - inspect before sending" if bad else ""))
sys.exit(1 if bad else 0)
PY

echo
echo "==> done"
echo "    build/current.pdf"
echo "    build/diff.pdf"
