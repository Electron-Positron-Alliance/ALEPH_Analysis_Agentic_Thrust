#!/usr/bin/env python3
r"""Regression tests for tools/texdiff.py: does the markup still compile?

    tools/test_texdiff.py

Each case is a small (OLD, NEW) pair, run through diff_file + repair_singletons
and then through pdflatex with -halt-on-error. The bar is the one that matters
for this tool: the marked-up source must be valid LaTeX. A broken diff build is
the only failure mode that stops make_pdfs.sh from producing diff.pdf.

Every case here is a shape that has actually broken the build. Add a case when
one does, not when a shape merely looks risky.

Requires: pdflatex. Exits non-zero on any failure, so it is usable in CI.
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texdiff as T  # noqa: E402

# (name, old, new). The name is what prints, so it doubles as the description
# of the edit shape being tested.
CASES = [
    # \begin{equation} and its body are separate lines, so the body line alone
    # carries no sign that it is math: it used to land in \DIFdel in running
    # text -> "Missing $ inserted".
    ("equation block commented out", r"""
Text before.
\begin{equation}
C_{\mathrm{h}}(j) = \frac{A_{\mathrm{x}}}{B},
\end{equation}
Text after.
""", r"""
Text before.
% \begin{equation}
% C_{\mathrm{h}}(j) = \frac{A_{\mathrm{x}}}{B},
% \end{equation}
Text after.
"""),

    ("equation block revived from a comment", r"""
Before.
% \begin{equation}
% C_{\mathrm{h}} = \frac{A}{B},
% \end{equation}
After.
""", r"""
Before.
\begin{equation}
C_{\mathrm{h}} = \frac{A}{B},
\end{equation}
After.
"""),

    ("equation block added", "Text before.\nText after.\n", r"""
Text before.
\begin{equation}
E = mc^2_{\mathrm{x}},
\end{equation}
Text after.
"""),

    ("equation body edited in place",
     "\\begin{equation}\nx_{1} = a,\n\\end{equation}\n",
     "\\begin{equation}\nx_{2} = b,\n\\end{equation}\n"),

    # The float is gone from NEW, so a struck-through \caption has no float to
    # live in -> "\caption outside float". The deletion must be dropped.
    ("figure commented out", r"""
\begin{figure}[t]
\centering
\includegraphics[width=0.5\textwidth]{figures/a.pdf}
\caption{A caption with $\phi$ in it.}
\label{fig:a}
\end{figure}
After.
""", r"""
% \begin{figure}[t]
% \centering
% \includegraphics[width=0.5\textwidth]{figures/a.pdf}
% \caption{A caption with $\phi$ in it.}
% \label{fig:a}
% \end{figure}
After.
"""),

    # A lone inserted caption: \uwave around \caption boxes it and gives
    # "Missing \endgroup inserted", so the markup has to go inside the braces.
    ("caption added to an existing float", r"""
\begin{table}[t]
\begin{tabular}{lc}
A & 1 \\
\end{tabular}
\label{tab:a}
\end{table}
""", r"""
\begin{table}[t]
\begin{tabular}{lc}
A & 1 \\
\end{tabular}
\caption{A new caption with Table~\ref{tab:a} in it.}
\label{tab:a}
\end{table}
"""),

    ("caption edited in place", r"""
\begin{figure}[t]
\includegraphics[width=0.5\textwidth]{figures/a.pdf}
\caption{Old caption text.}
\end{figure}
""", r"""
\begin{figure}[t]
\includegraphics[width=0.5\textwidth]{figures/a.pdf}
\caption{New caption text.}
\end{figure}
"""),

    ("tabular row edited", r"""
\begin{tabular}{lc}
\hline
Old row & 1 \\
\hline
\end{tabular}
""", r"""
\begin{tabular}{lc}
\hline
New row & 2 \\
\hline
\end{tabular}
"""),

    # "\\[2pt]" is row spacing, not the display-math opener "\[".
    ("row spacing is not display math", r"""
\begin{tabular}{lc}
A & 1 \\[2pt]
\end{tabular}
""", r"""
\begin{tabular}{lc}
B & 2 \\[2pt]
\end{tabular}
"""),

    ("prose edited", "The old sentence here.\n", "The new sentence here.\n"),
]

# \includegraphics is stubbed so the cases need no figure files on disk.
PRE = r"""\documentclass{article}
\usepackage{amsmath}
\usepackage{graphicx}
\renewcommand{\includegraphics}[2][]{\rule{2cm}{1cm}}
""" + T.PREAMBLE + r"""
\begin{document}
"""
POST = "\n\\end{document}\n"


def run_case(name, old, new, tmp):
    T.DROPPED.clear()
    T.GUARDED.clear()
    marked, _ = T.repair_singletons(T.diff_file(old, new))
    open(os.path.join(tmp, "t.tex"), "w", encoding="utf-8").write(PRE + marked + POST)
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"],
        cwd=tmp, capture_output=True, text=True)
    log = open(os.path.join(tmp, "t.log"), encoding="utf-8", errors="replace").read()
    errors = [l for l in log.splitlines() if l.startswith("! ")]
    ok = proc.returncode == 0 and not errors
    note = ""
    if T.DROPPED:
        note += f"   dropped={len(T.DROPPED)}"
    if T.GUARDED:
        note += f"   guarded={len(T.GUARDED)}"
    print(f"{'PASS' if ok else 'FAIL'}  {name}{note}")
    if not ok:
        for e in errors[:3]:
            print(f"        {e}")
        print("        --- markup ---")
        for line in marked.splitlines():
            print(f"        {line}")
    return ok


def main():
    if subprocess.run(["which", "pdflatex"], capture_output=True).returncode != 0:
        print("!! pdflatex not found", file=sys.stderr)
        return 2
    tmp = tempfile.mkdtemp()
    failed = sum(not run_case(n, o, w, tmp) for n, o, w in CASES)
    print(f"\n{len(CASES) - failed}/{len(CASES)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
