#!/usr/bin/env python3
r"""
Minimal latexdiff replacement: word-level LaTeX markup diff.

latexdiff is not installed in this environment and cannot be fetched, so this
does the same job for the subset of LaTeX this manuscript uses.

Design notes / safety rules:
  * Tokenises into "atoms": inline math ($...$), LaTeX commands with their
    braced arguments, braced groups, alignment/row separators (& and \\),
    comments, whitespace, and words.
  * Never splits inside inline math or inside a command's argument list --
    such an atom is replaced wholesale if it changed.
  * Never wraps markup ACROSS a structural separator (&, \\, \begin, \end,
    \item, blank line, or a display-math delimiter). Changes are emitted per
    segment, so a table row or an equation body can never be broken.
  * Segments containing display math or verbatim-like environments are marked
    at segment granularity rather than word granularity.
  * Display-math nesting is tracked ACROSS lines, because \begin{equation} and
    its body are separate lines. A math body never receives \DIFadd/\DIFdel
    (text-mode macros); it gets \DIFaddmath/\DIFdelmath, and a deletion whose
    environment is gone from NEW is re-wrapped in its own \[...\].

Output: for each changed file, a copy with \DIFadd{...} / \DIFdel{...} markup.
The preamble is injected into main.tex.
"""

import os
import re
import shutil
import sys
from difflib import SequenceMatcher

PREAMBLE = r"""
%% ---- diff markup (latexdiff-compatible macro names) ----
\usepackage{color}
\usepackage[normalem]{ulem}
\providecommand{\DIFadd}[1]{{\protect\color{blue}\uwave{#1}}}
\providecommand{\DIFdel}[1]{{\protect\color{red}\sout{#1}}}
\providecommand{\DIFaddbegin}{}
\providecommand{\DIFaddend}{}
\providecommand{\DIFdelbegin}{}
\providecommand{\DIFdelend}{}
% Math-mode variants: \uwave and \sout are text-mode only, so display-math
% bodies are coloured instead of underlined/struck.
\providecommand{\DIFaddmath}[1]{{\protect\color{blue}#1}}
\providecommand{\DIFdelmath}[1]{{\protect\color{red}#1}}
% Float indicator. The body of a figure/table cannot carry \DIFadd: \uwave
% boxes a subfigure parbox into an LR box, so side-by-side panels each take
% their own line and overflow the margin. Layout changes inside a float are
% therefore emitted verbatim and flagged here instead.
\providecommand{\DIFfigchanged}{{\protect\color{blue}\bfseries [CHANGED]\space}}
% A deleted heading. \section cannot carry markup -- \uwave around a
% page-level command that also writes the .toc is fatal -- but dropping it
% loses the document outline silently. Rendered as struck body text where the
% heading used to sit: no \addcontentsline, so the table of contents and the
% section numbering of the NEW version are untouched.
\providecommand{\DIFdelhead}[1]{%
  \par\medskip\noindent{\protect\color{red}\bfseries\sout{#1}}\par\medskip}
%% ---- end diff markup ----
"""

# True structural separators: markup must never span these.
# NB: commands that own a braced argument (\caption, \label, \includegraphics,
# \multicolumn, ...) are deliberately NOT listed. Splitting there would sever a
# command from its own argument and emit e.g. a bare \caption.
SEPARATOR_RE = re.compile(
    # \begin and \end take their {env} argument with them: matching the bare
    # command would let the {env} group become a separate atom, and wrapping it
    # yields \begin\DIFadd{itemize}, which is a "Missing \endcsname" error.
    # The float placement spec goes with it too: "[t!]" left as its own segment
    # gets word-diffed against "[ht!]" and printed as struck-through literal
    # text beside the float. Placement is layout, not content -- NEW's value is
    # carried along with the separator and never marked.
    r"(\\\\|&|\\begin\s*\{[^}]*\}(?:\[[^\]]*\])?|\\end\s*\{[^}]*\}"
    r"|\\begin\b|\\end\b|\\item\b|\\hline\b|\\cline\b|\n\s*\n)"
)

# Environments whose bodies we diff only at segment granularity.
FRAGILE_ENV = re.compile(r"\\begin\{(equation|align|eqnarray|tabular|tabularx|verbatim|lstlisting|tikzpicture)\*?\}")

# Commands where a changed argument must be diffed INSIDE the braces. Replacing
# the whole atom would emit the command twice -- two \caption's in one float, or
# a \abstract inside \DIFdel in the preamble.
# Sectioning commands. Deleted, these become \DIFdelhead rather than vanishing.
HEAD_CMDS = {"section", "subsection", "subsubsection", "paragraph",
             "subparagraph"}

# Deleted headings rendered as struck body text, for the report.
DELETED_HEADS = []

RECURSE_CMDS = {
    "abstract", "caption", "title", "section", "subsection", "subsubsection",
    "paragraph", "textbf", "textit", "emph", "texttt", "footnote", "keywords",
}

# Commands that must never carry markup: wrapping them breaks the reference,
# the float, or the build. If changed, the new value is emitted unmarked.
NEVER_MARK_CMDS = {
    "label", "ref", "eqref", "cite", "input", "include", "includegraphics",
    "bibliography", "bibliographystyle", "author", "affiliation", "emailAdd",
    "documentclass", "usepackage", "newcommand", "renewcommand",
    "providecommand", "setcounter", "usetikzlibrary", "definecolor",
    # tabular primitives: these must be the first token in a cell and cannot
    # appear inside another command's argument
    "multicolumn", "multirow", "multispan", "hline", "cline",
    # environment delimiters: wrapping one detaches it from its {env} argument
    "begin", "end", "item",
    # page/display-level commands: these trigger TeX page machinery (\prevdepth,
    # \par, float placement) that is illegal inside an LR box like \uwave.
    # Wrap them in \DIFadd/\DIFdel would cause "Improper \prevdepth" or
    # "Missing $ inserted" errors. Keep them bare for additions, drop for deletions.
    "FloatBarrier", "clearpage", "cleardoublepage", "newpage", "pagebreak",
    "noindent", "nobreak", "allowbreak",
    "appendix", "par", "centering",
    "hfill", "vfill", "hspace", "vspace",
    # float-body commands: \caption invokes \caption@hrule -> \hrule which is a
    # vertical-mode primitive and fails inside an LR box (\uwave). \section and
    # friends invoke \addcontentsline / page-level hooks. Wrapping any of these
    # in \DIFadd{...} is fatal. The 1:1 REPLACE case in diff_segment is handled
    # via RECURSE_CMDS (checked first) so caption text diffs still work; only
    # INSERT/DELETE runs hitting mark_run need the bare-or-drop behaviour here.
    "caption", "abstract", "title",
    "section", "subsection", "subsubsection",
    "subcaption", "captionof",
}

# A line containing any of these is structural: it cannot be struck through as
# a unit, so deletions are dropped and insertions emitted unmarked.
TABULAR_LINE_RE = re.compile(r"(&|\\\\\s*$|\\multicolumn|\\multirow|\\hline|\\cline)")

# --- environment tracking -------------------------------------------------
#
# Markup decisions need to know which environments are open at a given line,
# and one line on its own does not say: \begin{equation}, its body and
# \end{equation} are three separate lines, so a body line carries no sign that
# it is math. Both sides are tracked, because the question for every deletion
# is "does the environment this old line lived in still exist where the
# deletion lands?" -- if NEW commented the whole block out, it does not.

ENV_BEGIN_RE = re.compile(r"\\begin\s*\{([^}]*)\}")
ENV_END_RE = re.compile(r"\\end\s*\{([^}]*)\}")
# (?<!\\) so that the row-spacing form "\\[2pt]" is not read as display math.
MATH_OPEN_RE = re.compile(r"(?<!\\)\\\[")
MATH_CLOSE_RE = re.compile(r"(?<!\\)\\\]")

# Environments whose body is math mode. \DIFadd and \DIFdel are built on
# \uwave and \sout, which are text-mode only: inside math they give
# "Missing $ inserted". Those lines get \DIFaddmath / \DIFdelmath instead.
MATH_ENVS = frozenset("""
    math displaymath equation eqnarray align alignat flalign gather multline
    split aligned gathered array matrix pmatrix bmatrix vmatrix cases
    smallmatrix
""".split())

# Environments whose content cannot be rendered outside them: a \caption needs
# its float, a row needs its tabular. If OLD had one and NEW does not -- the
# block was deleted or commented out wholesale -- the deletion cannot be shown
# at all, and emitting it gives "\caption outside float" or a stray row.
UNRENDERABLE_ENVS = frozenset("""
    figure table tabular tabularx wrapfigure wraptable subfigure minipage
    tikzpicture lstlisting verbatim
    itemize enumerate description
""".split())

NOT_ENV, ENV_BODY, ENV_DELIM = 0, 1, 2

# Floats whose body is layout: panels positioned relative to one another. Not
# the same set as UNRENDERABLE_ENVS -- itemize content, for instance, is prose
# and marks up fine. subfigure/minipage are here because they are what \uwave
# actually breaks, and they nest inside the outer float.
FLOAT_ENVS = frozenset("""
    figure table wrapfigure wraptable subfigure minipage tikzpicture
""".split())

# A line inside a float that is nothing but macro calls, whitespace and ties:
# "\pwpanel[0.495]{pwflag4}{cosTheta}\hfill". Nested braces defeat the simple
# {[^{}]*} argument pattern, which is deliberate -- a \caption holding \vec{p}
# is prose and must stay diffable.
FLOAT_LAYOUT_ONLY_RE = re.compile(
    r"^(?:\s|\\[a-zA-Z@]+\*?(?:\[[^\]]*\])*(?:\{[^{}]*\})*|[%~]|\\\\)+$")

# Tokens that place or size material. Any of these on a line inside a float
# means the line is layout even if prose sits beside it.
FLOAT_LAYOUT_TOKEN_RE = re.compile(
    r"\\(?:includegraphics|hfill|vfill|hspace|vspace|centering|resizebox"
    r"|adjustbox|subfloat|rule|raisebox|parbox|begin|end)\b"
    r"|\\\\|(?<!\\)&")

# Floats whose body changed but carries no markup, reported because the change
# is real and only the [CHANGED] tag hints at it in the PDF.
FLOAT_CHANGED = []

# Inert marker: a comment, so a float we fail to tag degrades to a no-op rather
# than a stray token in the output.
FLOAT_SENTINEL = "%__DIFFLOATCHANGED__"


def is_float_layout(line):
    r"""Is this line inside-a-float layout rather than caption prose?

    A \caption line is always prose: its argument is the one part of a float
    body that renders as text and so is the one part markup can survive in.
    """
    if "\\caption" in line:
        return False
    if not line.strip():
        return False
    return bool(FLOAT_LAYOUT_ONLY_RE.match(line)
                or FLOAT_LAYOUT_TOKEN_RE.search(line))

# Deletions dropped because their environment is gone from NEW: real changes
# that cannot appear in diff.pdf, so they are reported rather than swallowed.
DROPPED = []

# Plumbing inside a dropped float. Its loss is implied by the float's own
# removal, so it is not worth naming in the warning -- only prose and captions
# are, because those are what a reader would look for in diff.pdf.
FLOAT_PLUMBING_RE = re.compile(
    r"^\s*\\(centering|label|includegraphics|hline|toprule|midrule|bottomrule"
    r"|rowcolor|captionsetup)\b[^%]*$")


def strip_comment(line):
    r"""Drop a trailing % comment. An escaped \% is not a comment."""
    return re.sub(r"(?<!\\)%.*$", "", line)


def in_math(stack):
    """Is a line with this environment stack in math mode?

    Tests the whole stack, not the innermost name: an array inside an equation
    is still math.
    """
    return any(name in MATH_ENVS for name in stack)


def orphaned(stack, ctx):
    """Can OLD content from `stack` be rendered where `ctx` is what is open?"""
    return any(name in UNRENDERABLE_ENVS and name not in ctx for name in stack)


def env_lines(text):
    r"""Track environment nesting line by line.

    Returns (codes, stacks, math):
      codes[i]   NOT_ENV / ENV_BODY / ENV_DELIM (the line opens or closes one)
      stacks[i]  environment names open BEFORE line i. len == nlines + 1, so an
                 index one past the last line is legal -- that is where a
                 deletion at the end of a file lands.
      math[i]    the line is display math: inside a math environment, or a
                 delimiter of one.

    Commented-out markup counts for nothing: a \begin{equation} behind a % opens
    no environment. That is exactly the case that used to leave a bare math body
    inside \DIFdel.
    """
    codes, stacks, math, stack = [], [], [], []
    for line in text.split("\n"):
        src = strip_comment(line)
        events = [(m.start(), 1, m.group(1).rstrip("*").strip())
                  for m in ENV_BEGIN_RE.finditer(src)]
        events += [(m.start(), -1, m.group(1).rstrip("*").strip())
                   for m in ENV_END_RE.finditer(src)]
        events += [(m.start(), 1, "math") for m in MATH_OPEN_RE.finditer(src)]
        events += [(m.start(), -1, "math") for m in MATH_CLOSE_RE.finditer(src)]
        events.sort()
        stacks.append(tuple(stack))
        codes.append(ENV_DELIM if events else (ENV_BODY if stack else NOT_ENV))
        math.append(in_math(stack) or any(n in MATH_ENVS for _p, _d, n in events))
        for _pos, delta, name in events:
            if delta == 1:
                stack.append(name)
            elif name in stack:
                # pop to the matching name; a stray \end must not desynchronise
                while stack.pop() != name:
                    pass
    stacks.append(tuple(stack))
    return codes, stacks, math


def wrap_math(macro, line, standalone):
    r"""Mark one line of display math with a math-safe macro.

    standalone re-opens display math around the line. That is for a deletion
    whose \begin{equation} ... \end{equation} is gone from NEW: the delimiters
    are dropped as structural, so without this the body would land in running
    text and every _ and \frac in it would be a "Missing $ inserted" error.
    """
    core = line.strip()
    if not core:
        return line
    if not _brace_balanced(core):
        GUARDED.append(core[:60])
        return line if macro == "DIFaddmath" else ""
    # & and \\ are alignment separators in LaTeX even inside {groups}: wrapping
    # a line that contains them in \DIFaddmath{...} splits the cell (&) or
    # generates a misplaced \cr (\\), both causing "Missing }" or
    # "Misplaced \cr" errors at \end{align}.
    if re.search(r"(?<!\\)&|\\\\", core):
        GUARDED.append(core[:60])
        return line if macro == "DIFaddmath" else ""
    # a % inside the run would comment out our own closing brace
    sep = "\n" if re.search(r"(?<!\\)%", core) else ""
    marked = "\\%s{%s%s}" % (macro, core, sep)
    return "\\[" + marked + "\\]" if standalone else marked


CMD_HEAD_RE = re.compile(r"^\\([A-Za-z@]+)\*?")


def cmd_name(atom):
    m = CMD_HEAD_RE.match(atom)
    return m.group(1) if m else None


def is_comment(atom):
    """A % comment atom. Wrapping one in markup comments out the closing brace."""
    return atom.lstrip().startswith("%")


def split_cmd_arg(atom):
    """Split '\\name[opt]{body}' into ('\\name[opt]{', body, '}'). None if not that shape."""
    if not atom.startswith("\\") or not atom.endswith("}"):
        return None
    i = atom.find("{")
    if i == -1:
        return None
    depth = 0
    for j in range(i, len(atom)):
        if atom[j] == "{":
            depth += 1
        elif atom[j] == "}":
            depth -= 1
            if depth == 0:
                if j != len(atom) - 1:
                    return None  # multiple args - too risky to recurse
                return atom[: i + 1], atom[i + 1 : j], atom[j:]
    return None

ATOM_RE = re.compile(
    r"""
      (?P<comment>(?<!\\)%[^\n]*\n?)
    | (?P<dmath>\$\$.*?\$\$)
    | (?P<imath>(?<!\\)\$(?:\\.|[^$\\])*\$)
    | (?P<cmd>\\[A-Za-z@]+\*?(?:\s*\[[^\]]*\])*(?:\s*\{(?:[^{}]|\{[^{}]*\})*\})*(?:\[[^\]]*\])*)
    | (?P<esc>\\[^A-Za-z])
    | (?P<group>\{(?:[^{}]|\{[^{}]*\})*\})
    | (?P<space>\s+)
    | (?P<word>[^\s\\${}&%]+)
    | (?P<other>.)
    """,
    re.VERBOSE | re.DOTALL,
)


def atomise(text):
    return [m.group(0) for m in ATOM_RE.finditer(text)]


def split_segments(text):
    """Split into segments at structural separators, keeping the separators."""
    parts = SEPARATOR_RE.split(text)
    return [p for p in parts if p is not None]


def is_separator(s):
    return bool(SEPARATOR_RE.fullmatch(s))


def is_blank(s):
    return s.strip() == ""


# Runs that wrap() refused because they straddle a brace boundary. Reported at the
# end of a run so an unmarked change cannot pass unnoticed.
GUARDED = []

# Preamble lines whose change is real but is emitted unmarked. Nothing before
# \begin{document} can carry markup: \DIFadd expands to \uwave, which starts
# typesetting, so one marked preamble line aborts the build with
# "Missing \begin{document}". latexdiff has the same rule. The new preamble is
# copied verbatim and only the body is diffed -- reported, not silent, because
# an unmarked change is invisible in diff.pdf.
PREAMBLE_CHANGED = []

# Preamble commands that only STORE their argument for \maketitle to typeset
# later, inside the document. jheppub does
#     \renewcommand{\abstract}[1]{\gdef\@abstract{#1}}
# and emits \@abstract in text mode well after \begin{document}, so markup
# inside the braces is legal -- unlike markup anywhere else in the preamble,
# which starts typesetting and gives "Missing \begin{document}". Without this
# the abstract is the single biggest change a reader would look for and never
# see marked in diff.pdf.
PREAMBLE_DIFF_CMDS = ("title", "abstract", "keywords")

# Names whose argument was diffed in place, for the report.
PREAMBLE_DIFFED = []

# \begin{document} on a line that is not commented out.
DOC_BEGIN_RE = re.compile(r"^(?:[^%\n]|\\%)*\\begin\{document\}", re.M)


def split_preamble(text):
    r"""Split at the line holding \begin{document}. ("", text) if there is none."""
    m = DOC_BEGIN_RE.search(text)
    if not m:
        return "", text
    nl = text.find("\n", m.end())
    i = len(text) if nl == -1 else nl + 1
    return text[:i], text[i:]


def _brace_balanced(s):
    """True if every { in s is closed within s. Escaped \\{ and \\} do not count."""
    d = 0
    i = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "{":
            d += 1
        elif s[i] == "}":
            d -= 1
            if d < 0:
                return False
        i += 1
    return d == 0


def wrap(macro, atoms):
    """Wrap a run of atoms in \\DIFadd/\\DIFdel, preserving outer whitespace."""
    s = "".join(atoms)
    if s.strip() == "":
        return s
    lead = s[: len(s) - len(s.lstrip())]
    trail = s[len(s.rstrip()):]
    core = s.strip()
    if (len(core) - len(core.rstrip("\\"))) % 2:
        # The run ended in a control space -- "Stat.\ " -- and .strip() just took
        # the space that is part of that command. Emitting "{Stat.\}" turns our
        # own closing brace into an escaped literal, so the macro runs on and
        # swallows the rest of the paragraph. Put the space back: it is part of
        # the control sequence, not layout. (\\ is two backslashes, so a line
        # break is even and never reaches here.)
        core += " "
    if not _brace_balanced(core):
        # The run straddles a brace boundary, so wrapping it would close our own
        # macro with someone else's brace. Happens when ATOM_RE cannot take a
        # command and its argument as one atom -- e.g. \caption{...} nesting two
        # or more levels -- and mark_run then splits the run at a never-mark
        # command inside it. Emitting unmarked keeps the content correct and
        # only loses the highlight; wrapping it corrupts the document.
        #
        # Recorded, not silent: an unmarked addition is invisible in diff.pdf and
        # a file left with no markup at all is skipped by the faithfulness check,
        # so it would drop out of both the diff and the verification unnoticed.
        GUARDED.append(core[:60])
        return s if macro == "DIFadd" else lead + trail
    if re.search(r"(?<!\\)%", core):
        # Defensive: some other path handed us a comment. Put the closing brace
        # on its own line so the % cannot comment it out.
        return f"{lead}\\{macro}{{{core}\n}}{trail}"
    return f"{lead}\\{macro}{{{core}}}{trail}"


def mark_run(macro, atoms):
    """Wrap a run, but emit never-mark commands bare so nothing breaks.

    A deleted \\label or \\includegraphics must not end up inside \\DIFdel: for
    deletions we drop them, for insertions we keep them unmarked.
    """
    if not any(is_comment(t) or (t.startswith("\\") and cmd_name(t) in NEVER_MARK_CMDS)
               for t in atoms):
        return wrap(macro, atoms)
    out = []
    buf = []
    for t in atoms:
        if is_comment(t):
            # A comment can never be wrapped: the % would swallow the closing
            # brace. Keep added comments verbatim, drop deleted ones.
            if buf:
                out.append(wrap(macro, buf))
                buf = []
            if macro == "DIFadd":
                out.append(t)
            continue
        if t.startswith("\\") and cmd_name(t) in NEVER_MARK_CMDS:
            if buf:
                out.append(wrap(macro, buf))
                buf = []
            if macro == "DIFadd" or cmd_name(t) == "item":
                # Keep new structural commands unmarked, and always keep \item
                # bare even in deletions: dropping \item leaves its content
                # inside \begin{itemize} without a list marker, which is a
                # hard LaTeX error ("Something's wrong--perhaps a missing \item").
                out.append(t)
            elif cmd_name(t) in HEAD_CMDS:
                # A deleted heading: show the title struck through instead of
                # dropping it, so a restructured outline is visible rather than
                # merely reported. The command itself is discarded, so nothing
                # reaches the .toc or the section counters.
                sp = split_cmd_arg(t)
                if sp and sp[1].strip():
                    out.append("\\DIFdelhead{%s}" % sp[1])
                    DELETED_HEADS.append(sp[1].strip()[:60])
        else:
            buf.append(t)
    if buf:
        out.append(wrap(macro, buf))
    return "".join(out)


def diff_segment(old, new):
    """Word-level diff of one segment. Falls back to whole-segment markup."""
    if FRAGILE_ENV.search(old) or FRAGILE_ENV.search(new):
        if old == new:
            return new
        out = ""
        if old.strip():
            out += wrap("DIFdel", [old])
        if new.strip():
            out += wrap("DIFadd", [new])
        return out or new

    a, b = atomise(old), atomise(new)
    sm = SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append("".join(b[j1:j2]))
        elif tag == "delete":
            out.append(mark_run("DIFdel", a[i1:i2]))
        elif tag == "insert":
            out.append(mark_run("DIFadd", b[j1:j2]))
        else:  # replace
            # A 1:1 command swap where only the argument changed: recurse into
            # the braces instead of duplicating or wrapping the command.
            if i2 - i1 == 1 and j2 - j1 == 1:
                oa, na = a[i1], b[j1]
                name = cmd_name(na)
                if name and name == cmd_name(oa):
                    # RECURSE before NEVER_MARK: commands like \caption are in
                    # both sets. For a 1:1 replace we can recurse into the arg
                    # and produce \caption{diff} safely; NEVER_MARK only applies
                    # to the mark_run INSERT/DELETE path where the command cannot
                    # be wrapped in an LR box at all.
                    if name in RECURSE_CMDS:
                        so, sn = split_cmd_arg(oa), split_cmd_arg(na)
                        if so and sn:
                            out.append(sn[0] + diff_segment(so[1], sn[1]) + sn[2])
                            continue
                    if name in NEVER_MARK_CMDS:
                        out.append(na)
                        continue
            # mark_run, not wrap: a replaced run can contain a never-mark
            # command. Wrapping a deleted \\ref inside \\DIFdel leaves the diff
            # citing a label that the new version removed -- an undefined
            # reference in the diff build -- and a wrapped \\label would collide
            # with the same label in the added text.
            out.append(mark_run("DIFdel", a[i1:i2]))
            out.append(mark_run("DIFadd", b[j1:j2]))
    return "".join(out)


def diff_line(old, new):
    """Diff one physical line, segment by segment, never spanning separators."""
    so, sn = split_segments(old), split_segments(new)
    sm = SequenceMatcher(None, so, sn, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append("".join(sn[j1:j2]))
        elif tag == "delete":
            for seg in so[i1:i2]:
                # A deleted separator is DROPPED, never echoed. Every other
                # branch below emits NEW's separators, so echoing OLD's too
                # would put both sides' & in one row: when a table gains a
                # column, the marked row ends up with more cells than the
                # tabular has, and stripping the \DIFdel groups no longer
                # reproduces the new source. Only the cell CONTENT is struck.
                if is_separator(seg) or is_blank(seg):
                    continue
                out.append(mark_run("DIFdel", atomise(seg)))
        elif tag == "insert":
            for seg in sn[j1:j2]:
                out.append(seg if (is_separator(seg) or is_blank(seg))
                           else mark_run("DIFadd", atomise(seg)))
        else:
            olds, news = so[i1:i2], sn[j1:j2]
            if len(olds) == len(news):
                for o, n in zip(olds, news):
                    out.append(n if (o == n or is_separator(n) or is_blank(n))
                               else diff_segment(o, n))
            else:
                for seg in olds:
                    if not (is_separator(seg) or is_blank(seg)):
                        out.append(mark_run("DIFdel", atomise(seg)))
                for seg in news:
                    out.append(seg if (is_separator(seg) or is_blank(seg))
                               else mark_run("DIFadd", atomise(seg)))
    return "".join(out)


def diff_body(old_text, new_text):
    r"""Line-level diff, with word-level markup inside changed lines.

    Line granularity at the top level is what keeps tabular material safe: a
    deleted table row is dropped rather than struck through, because
    \multicolumn cannot survive inside \DIFdel and a half-struck row has the
    wrong number of & separators.

    Display-math lines are routed to \DIFaddmath / \DIFdelmath, and deletions
    whose environment is gone from NEW are dropped: both are decided from the
    cross-line environment state, not from the line's own text.
    """
    ol, nl = old_text.split("\n"), new_text.split("\n")
    ocode, ostack, omath = env_lines(old_text)
    ncode, nstack, nmath = env_lines(new_text)
    out = []

    def ctx_at(at):
        """What NEW has open where a deletion landing before line `at` goes."""
        return nstack[min(at, len(nl))]

    def del_line(k, at):
        line = ol[k]
        if omath[k]:
            if ocode[k] == ENV_DELIM:
                return  # \begin/\end of a removed display block: structural
            # Re-open display math only when the environment that held this
            # body is not open where the deletion lands.
            out.append(wrap_math("DIFdelmath", line, not in_math(ctx_at(at))))
            return
        if orphaned(ostack[k], ctx_at(at)):
            if (line.strip() and ocode[k] != ENV_DELIM
                    and not FLOAT_PLUMBING_RE.match(line)):
                DROPPED.append(line.strip()[:60])
            return
        if line.strip() and not TABULAR_LINE_RE.search(line):
            marked = mark_run("DIFdel", atomise(line))
            # A deleted comment marks up to nothing. Appending "" would put a
            # blank line in the output, and a blank line inside an equation is
            # a \par in math mode: "Missing $ inserted".
            if marked.strip():
                out.append(marked)
        # structural / blank deleted lines: dropped

    def add_line(k):
        line = nl[k]
        if nmath[k]:
            # a \begin{equation} line cannot be wrapped at all; a body line
            # takes the math-safe macro. Its own environment is in NEW, so the
            # line is never standalone.
            marked = (line if ncode[k] == ENV_DELIM
                      else wrap_math("DIFaddmath", line, False))
            # An old and a new formula in one display run together into a
            # single unreadable line. The gap goes INSIDE the preceding
            # \DIFdelmath so that the faithfulness check, which deletes that
            # whole group, still reproduces the new source exactly.
            if (out and marked.startswith("\\DIFaddmath{")
                    and out[-1].startswith("\\DIFdelmath{")
                    and out[-1].endswith("}")):
                out[-1] = out[-1][:-1] + "\\qquad}"
            out.append(marked)
        elif line.strip() and not TABULAR_LINE_RE.search(line):
            out.append(mark_run("DIFadd", atomise(line)))
        else:
            out.append(line)

    def in_float(at, stacks, lines):
        return any(n in FLOAT_ENVS for n in stacks[min(at, len(lines))])

    def float_layout_block(i1, i2, j1, j2):
        r"""Is this changed block layout inside a float?

        True when either side sits in a float and any line involved is layout
        rather than caption prose. Markup there is not merely ugly: \DIFadd
        around a subfigure makes an LR box of a parbox, which breaks the
        side-by-side layout and runs the panels off the page. The panels also
        get line-matched against unrelated old caption prose, so the markup
        would be meaningless even if it typeset.
        """
        if not (in_float(i1, ostack, ol) or in_float(j1, nstack, nl)):
            return False
        return (any(is_float_layout(x) for x in ol[i1:i2])
                or any(is_float_layout(x) for x in nl[j1:j2]))

    def emit_float_verbatim(i1, i2, j1, j2):
        """Emit NEW's lines untouched and flag the float for a caption tag."""
        for line in ol[i1:i2]:
            if (line.strip() and not FLOAT_PLUMBING_RE.match(line)
                    and not is_float_layout(line)):
                FLOAT_CHANGED.append(line.strip()[:60])
        out.append(FLOAT_SENTINEL)
        out.extend(nl[j1:j2])

    sm = SequenceMatcher(None, ol, nl, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        # j2 > j1 only: the overflow this guards against comes from \DIFadd
        # wrapping NEW panel lines, and from old float prose being line-matched
        # against them. A pure deletion inside a float produces no \DIFadd, and
        # del_line already strikes it where that renders or drops it into the
        # DROPPED report where it does not -- which is better than dropping it
        # here, because a deleted float in a still-\input file can be shown.
        if tag != "equal" and j2 > j1 and float_layout_block(i1, i2, j1, j2):
            emit_float_verbatim(i1, i2, j1, j2)
        elif tag == "equal":
            out.extend(nl[j1:j2])
        elif tag == "delete":
            for k in range(i1, i2):
                del_line(k, j1)
        elif tag == "insert":
            for k in range(j1, j2):
                add_line(k)
        else:
            olds, news = ol[i1:i2], nl[j1:j2]
            # Math, or an old line whose environment is gone: word-level markup
            # cannot be used, so those lines fall back to whole-line del + add,
            # which keeps each side in a legal mode.
            special = [k for k in range(i1, i2)
                       if omath[k] or orphaned(ostack[k], ctx_at(j1))]
            if len(olds) == len(news):
                for k in range(i1, i2):
                    j = j1 + (k - i1)
                    if k in special or nmath[j]:
                        del_line(k, j)
                        add_line(j)
                    else:
                        out.append(nl[j] if ol[k] == nl[j] else diff_line(ol[k], nl[j]))
            elif special or any(nmath[j1:j2]):
                for k in range(i1, i2):
                    del_line(k, j1)
                for j in range(j1, j2):
                    add_line(j)
            else:
                # unequal block: word-diff the joined text if neither side is
                # tabular and neither side introduces structural separators
                # (\begin{...}, \end{...}, \\). When the new content contains
                # such separators, diff_line would wrap figure/table body lines
                # in \DIFadd{\uwave{...}} which is invalid LaTeX. Fall back to
                # per-line del + verbatim new in that case.
                if (not any(TABULAR_LINE_RE.search(x) for x in olds + news)
                        and not any(SEPARATOR_RE.search(x) for x in olds + news)):
                    out.append(diff_line("\n".join(olds), "\n".join(news)))
                else:
                    for line in olds:
                        if line.strip() and not TABULAR_LINE_RE.search(line):
                            out.append(mark_run("DIFdel", atomise(line)))
                    out.extend(news)
    return "\n".join(out)


def find_cmd_arg(text, name):
    r"""Span of the argument of \name{...}: (start, end) of the body, or None.

    Skips an occurrence that is commented out, so the block of alternative
    \title candidates parked behind % in main.tex cannot be picked up instead
    of the live one.
    """
    for m in re.finditer(r"\\" + name + r"\s*\{", text):
        bol = text.rfind("\n", 0, m.start()) + 1
        if re.search(r"(?<!\\)%", text[bol:m.start()]):
            continue
        o = m.end() - 1
        e = _match_brace(text, o)
        if e != -1:
            return o + 1, e - 1
    return None


def diff_preamble(opre, npre):
    r"""Mark up the text-bearing preamble commands; leave the rest verbatim.

    Returns the new preamble with those arguments diffed in place, plus the
    masked (opre, npre) pair for the unmarked-change report, so a line that
    IS now marked is not also reported as invisible.
    """
    omask, nmask = opre, npre
    for name in PREAMBLE_DIFF_CMDS:
        oa, na = find_cmd_arg(opre, name), find_cmd_arg(npre, name)
        if not (oa and na):
            continue
        oarg, narg = opre[oa[0]:oa[1]], npre[na[0]:na[1]]
        if oarg == narg:
            continue
        marked = diff_line(oarg, narg)
        # Splice into npre last-first is unnecessary: one command is handled
        # per iteration and the spans are recomputed from the ORIGINAL npre
        # each time, so do the substitution on a fresh copy and rebuild.
        npre = npre[:na[0]] + marked + npre[na[1]:]
        omask = omask[:oa[0]] + "\x00" + omask[oa[1]:]
        nmask = nmask[:na[0]] + "\x00" + nmask[na[1]:]
        PREAMBLE_DIFFED.append(name)
    return npre, omask, nmask


def diff_file(old_text, new_text):
    r"""Diff a file. Only \maketitle-deferred commands are marked in the preamble."""
    npre, nbody = split_preamble(new_text)
    if not npre:
        return diff_body(old_text, new_text)
    opre, obody = split_preamble(old_text)
    omask, nmask = opre, npre
    if opre.strip() and opre != npre:
        npre, omask, nmask = diff_preamble(opre, npre)
    if omask.strip() and omask != nmask:
        sm = SequenceMatcher(None, omask.split("\n"), nmask.split("\n"),
                             autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            for line in nmask.split("\n")[j1:j2] or omask.split("\n")[i1:i2]:
                if line.strip():
                    PREAMBLE_CHANGED.append(line.strip()[:60])
    return npre + diff_body(obody, nbody)


def _match_brace(s, i):
    """i points at '{'. Return index just past the matching '}', or -1."""
    depth = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


REPAIR_CMDS = ("caption", "abstract", "title", "section", "subsection",
               "subsubsection", "paragraph", "keywords")


def repair_singletons(text):
    """Undo any \\DIFdel{\\cmd{A}}\\DIFadd{\\cmd{B}} that would emit \\cmd twice.

    Rewrites to \\cmd{<word-diff of A vs B>}. A float with two \\caption's, or a
    duplicated \\abstract, is a hard LaTeX error, so this is a correctness pass,
    not cosmetics.
    """
    fixed = 0
    for name in REPAIR_CMDS:
        for star in ("", "*"):
            pat = "\\DIFdel{\\" + name + star + "{"
            while True:
                k = text.find(pat)
                if k == -1:
                    break
                # outer \DIFdel{...}
                dopen = k + len("\\DIFdel")
                dend = _match_brace(text, dopen)
                if dend == -1:
                    break
                inner_del = text[dopen + 1 : dend - 1]           # \cmd{A}
                rest = text[dend:]
                m = re.match(r"(\s*)\\DIFadd\{", rest)
                if not m:
                    # deletion with no paired insertion: keep the command, drop markup
                    text = text[:k] + inner_del + rest
                    fixed += 1
                    continue
                aopen = dend + m.end() - 1
                aend = _match_brace(text, aopen)
                if aend == -1:
                    break
                inner_add = text[aopen + 1 : aend - 1]           # \cmd{B}
                sa, sb = split_cmd_arg(inner_del), split_cmd_arg(inner_add)
                if sa and sb:
                    repl = sb[0] + diff_segment(sa[1], sb[1]) + sb[2]
                else:
                    repl = inner_add
                text = text[:k] + repl + text[aend:]
                fixed += 1

    # A lone \DIFadd{\caption{...}} -- an inserted caption, with no deletion
    # beside it for the loop above to pair it with. \uwave around a \caption
    # boxes the whole float caption and gives "Missing \endgroup inserted", so
    # the markup moves inside the braces. This runs after the pairing loop, so
    # anything left here is genuinely unpaired. Both plain and starred command
    # variants (e.g. \subsection*) are handled.
    for name in REPAIR_CMDS:
        for star in ("", "*"):
            pat = "\\DIFadd{\\" + name + star + "{"
            at = 0
            while True:
                k = text.find(pat, at)
                if k == -1:
                    break
                aopen = k + len("\\DIFadd")
                aend = _match_brace(text, aopen)
                if aend == -1:
                    break
                inner = text[aopen + 1 : aend - 1]          # \cmd{B}
                sb = split_cmd_arg(inner)
                if sb:
                    repl = sb[0] + wrap("DIFadd", [sb[1]]) + sb[2]
                else:
                    repl = inner                            # keep it, unmarked
                text = text[:k] + repl + text[aend:]
                at = k + len(repl)
                fixed += 1

    # Emitting a never-mark command bare can leave a stray space after a
    # non-breaking tilde ("Sec.~ \ref{...}"), which prints a double space.
    text = re.sub(r"~[ \t]+(\\(?:ref|eqref|cite|citep|citet)\b)", r"~\1", text)

    # Dropping a never-mark command out of a DELETED run splits one deletion
    # into two \DIFdel groups with OLD's surrounding space stranded between
    # them, unmarked: "\DIFdel{...Sec.~} \DIFdel{informs...}". That space is
    # deleted content, so it belongs inside the strikeout -- otherwise the rule
    # visibly breaks mid-sentence, and stripping the groups to recover the new
    # source leaves a space the new source does not have. Merge the pair.
    # Horizontal whitespace only: joining across a newline would run two source
    # lines together, and a blank line is a paragraph break, not a space.
    merge_del = re.compile(r"\\DIFdel\{((?:[^{}\\]|\\.|\{[^{}]*\})*)\}[ \t]+\\DIFdel\{")
    # Not counted in `fixed`: that number is reported as "singleton repairs"
    # and merging is a normalisation, not a repair of a singleton command.
    while True:
        text, n = merge_del.subn(lambda m: "\\DIFdel{" + m.group(1) + " ", text)
        if not n:
            break
    return text, fixed


CAPTION_RE = re.compile(r"\\caption\*?\s*(?:\[[^\]]*\])?\s*\{")
INNER_FLOAT = frozenset(("subfigure", "minipage"))


def tag_changed_floats(text):
    r"""Turn each float sentinel into a [CHANGED] tag on that float's caption.

    Returns (text, n_tagged, n_untagged). A sentinel with no reachable caption
    is dropped and counted: the change is still named in the FLOAT_CHANGED
    report, so it is not lost, just not tagged in the PDF.
    """
    if FLOAT_SENTINEL not in text:
        return text, 0, 0
    lines = text.split("\n")
    _codes, stacks, _math = env_lines(text)

    def floaty(i):
        return any(n in FLOAT_ENVS for n in stacks[min(i, len(lines))])

    targets, untagged = set(), 0
    for i, line in enumerate(lines):
        if FLOAT_SENTINEL not in line:
            continue
        # A deletion can land just before the \begin{figure} it belongs to, so
        # look a little way forward before giving up.
        at = next((k for k in range(i, min(i + 4, len(lines))) if floaty(k)), None)
        if at is None:
            untagged += 1
            continue
        a = at
        while a > 0 and floaty(a - 1):
            a -= 1
        b = at
        while b + 1 < len(lines) and floaty(b + 1):
            b += 1
        # The float's own caption, not a panel's: prefer a \caption outside any
        # subfigure/minipage. \pwpanel hides its \caption{} inside the macro,
        # but an explicit panel in the source would otherwise steal the tag.
        outer = [k for k in range(a, b + 1)
                 if CAPTION_RE.search(lines[k])
                 and not any(n in INNER_FLOAT for n in stacks[k])]
        inner = [k for k in range(a, b + 1) if CAPTION_RE.search(lines[k])]
        cap = (outer or inner)
        if not cap:
            untagged += 1
            continue
        targets.add(cap[-1])

    for k in sorted(targets):
        m = CAPTION_RE.search(lines[k])
        lines[k] = lines[k][:m.end()] + "\\DIFfigchanged " + lines[k][m.end():]

    kept = [l for l in lines if FLOAT_SENTINEL not in l]
    return "\n".join(kept), len(targets), untagged


def inject_preamble(text):
    m = re.search(r"(\\documentclass[^\n]*\n)", text)
    if not m:
        return PREAMBLE + text
    i = m.end()
    return text[:i] + PREAMBLE + text[i:]


def main():
    if len(sys.argv) != 4:
        print("usage: texdiff.py <OLD_dir> <NEW_dir> <OUT_dir>")
        return 2
    old_dir, new_dir, out_dir = (os.path.abspath(p) for p in sys.argv[1:4])

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(new_dir, out_dir)

    def tex_files(root_dir):
        found = []
        for root, _dirs, files in os.walk(root_dir):
            for fn in sorted(files):
                if fn.endswith(".tex"):
                    found.append(os.path.relpath(os.path.join(root, fn), root_dir))
        return sorted(found)

    new_rel = tex_files(new_dir)
    old_rel = tex_files(old_dir)

    changed, added, removed = [], [], []
    float_tags = float_untagged = 0
    for rel in new_rel:
        o, n = os.path.join(old_dir, rel), os.path.join(new_dir, rel)
        nt = open(n, encoding="utf-8").read()
        if os.path.exists(o):
            ot = open(o, encoding="utf-8").read()
        else:
            # A file with no counterpart in OLD is entirely new. Diffing it
            # against the empty string routes it through the same line-level
            # logic as any other change, so every line lands in \DIFadd and
            # tabular rows are still emitted unmarked rather than struck.
            ot = ""
            added.append(rel)
        if ot == nt:
            continue
        marked = diff_file(ot, nt)
        marked, nrep = repair_singletons(marked)
        marked, ntag, nuntag = tag_changed_floats(marked)
        float_tags += ntag
        float_untagged += nuntag
        open(os.path.join(out_dir, rel), "w", encoding="utf-8").write(marked)
        na = marked.count("\\DIFadd{")
        nd = marked.count("\\DIFdel{")
        changed.append((rel, na, nd, nrep))

    # Files deleted since OLD. out_dir is a copy of new_dir, so they are absent
    # from it and their removal would otherwise never appear anywhere in the
    # markup. Write the old body marked as deleted; it renders only if NEW's
    # main.tex still \input's the path, so say which case each one is.
    main_new = ""
    mp = os.path.join(new_dir, "main.tex")
    if os.path.exists(mp):
        main_new = open(mp, encoding="utf-8").read()
    for rel in old_rel:
        if rel in new_rel:
            continue
        stem = re.sub(r"\.tex$", "", rel)
        still_input = bool(re.search(
            r"\\(?:input|include)\s*\{\s*" + re.escape(stem) + r"(?:\.tex)?\s*\}", main_new))
        ot = open(os.path.join(old_dir, rel), encoding="utf-8").read()
        marked = diff_file(ot, "")
        marked, _ = repair_singletons(marked)
        marked, _, _ = tag_changed_floats(marked)
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w", encoding="utf-8").write(marked)
        removed.append((rel, len(ot.splitlines()), still_input))

    mainp = os.path.join(out_dir, "main.tex")
    t = open(mainp, encoding="utf-8").read()
    open(mainp, "w", encoding="utf-8").write(inject_preamble(t))

    print(f"changed files: {len(changed)}")
    tot_a = tot_d = tot_r = 0
    for rel, na, nd, nrep in changed:
        flag = f"   (repaired {nrep})" if nrep else ""
        print(f"  {rel:48s} +{na:<4d} -{nd}{flag}")
        tot_a += na
        tot_d += nd
        tot_r += nrep
    print(f"  {'TOTAL':48s} +{tot_a:<4d} -{tot_d}   singleton repairs: {tot_r}")
    if GUARDED:
        print(f"  WARN {len(GUARDED)} run(s) left UNMARKED: they straddle a brace boundary, so")
        print(f"       the change is real but is not highlighted in diff.pdf. Shorten or")
        print(f"       simplify the surrounding command if the highlight matters:")
        for g in GUARDED:
            print(f"         {g!r}")
    if DELETED_HEADS:
        print(f"  NOTE {len(DELETED_HEADS)} deleted heading(s) shown as struck body")
        print(f"       text: \\section cannot carry markup, so the title is struck in")
        print(f"       place and kept out of the table of contents:")
        for h in DELETED_HEADS:
            print(f"         {h!r}")
    if PREAMBLE_DIFFED:
        names = ", ".join("\\" + n for n in sorted(set(PREAMBLE_DIFFED)))
        print(f"  NOTE preamble {names} marked up in place: these store their")
        print(f"       argument for \\maketitle to typeset inside the document, so")
        print(f"       unlike the rest of the preamble they can carry markup.")
    if PREAMBLE_CHANGED:
        print(f"  NOTE {len(PREAMBLE_CHANGED)} preamble line(s) changed and are "
              f"emitted UNMARKED: markup")
        print(f"       before \\begin{{document}} does not compile, so the change is "
              f"real but is")
        print(f"       not highlighted in diff.pdf; see `git diff`:")
        for g in PREAMBLE_CHANGED:
            print(f"         {g!r}")
    if float_tags or FLOAT_CHANGED:
        print(f"  NOTE {float_tags} float(s) tagged [CHANGED] in diff.pdf: a figure or")
        print(f"       table body cannot carry markup -- \\DIFadd around a subfigure")
        print(f"       boxes it and runs the panels off the page -- so the body is")
        print(f"       emitted verbatim and only its caption is tagged.")
        if float_untagged:
            print(f"       {float_untagged} more had no caption to tag; see `git diff`.")
        if FLOAT_CHANGED:
            print(f"       old content replaced inside those floats, not shown struck:")
            for g in FLOAT_CHANGED:
                print(f"         {g!r}")
    if DROPPED:
        print(f"  WARN {len(DROPPED)} deleted line(s) DROPPED: the figure, table or")
        print(f"       tabular that held them is gone from the new version, so they")
        print(f"       cannot be shown struck through anywhere; see `git diff`:")
        for d in DROPPED:
            print(f"         {d!r}")
    for rel in added:
        print(f"  NOTE {rel}: new file - every line marked as added")
    for rel, nlines, still_input in removed:
        if still_input:
            print(f"  NOTE {rel}: deleted ({nlines} lines) - body marked as deleted "
                  f"and still \\input, so it renders struck through")
        else:
            print(f"  WARN {rel}: deleted ({nlines} lines) and no longer \\input by "
                  f"main.tex, so its body CANNOT appear in the diff PDF; "
                  f"see `git diff` for what was cut")
    return 0


if __name__ == "__main__":
    sys.exit(main())
