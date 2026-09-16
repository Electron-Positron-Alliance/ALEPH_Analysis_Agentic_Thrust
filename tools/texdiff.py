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
    r"(\\\\|&|\\begin\s*\{[^}]*\}|\\end\s*\{[^}]*\}"
    r"|\\begin\b|\\end\b|\\item\b|\\hline\b|\\cline\b|\n\s*\n)"
)

# Environments whose bodies we diff only at segment granularity.
FRAGILE_ENV = re.compile(r"\\begin\{(equation|align|eqnarray|tabular|tabularx|verbatim|lstlisting|tikzpicture)\*?\}")

# Commands where a changed argument must be diffed INSIDE the braces. Replacing
# the whole atom would emit the command twice -- two \caption's in one float, or
# a \abstract inside \DIFdel in the preamble.
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
""".split())

NOT_ENV, ENV_BODY, ENV_DELIM = 0, 1, 2

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
    | (?P<cmd>\\[A-Za-z@]+\*?(?:\s*\[[^\]]*\])*(?:\s*\{(?:[^{}]|\{[^{}]*\})*\})*)
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
            if macro == "DIFadd":
                out.append(t)  # keep new structural commands, unmarked
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
                    if name in NEVER_MARK_CMDS:
                        out.append(na)
                        continue
                    if name in RECURSE_CMDS:
                        so, sn = split_cmd_arg(oa), split_cmd_arg(na)
                        if so and sn:
                            out.append(sn[0] + diff_segment(so[1], sn[1]) + sn[2])
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
                out.append(seg if (is_separator(seg) or is_blank(seg))
                           else mark_run("DIFdel", atomise(seg)))
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


def diff_file(old_text, new_text):
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

    sm = SequenceMatcher(None, ol, nl, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
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
                # tabular, else fall back to emitting the new lines
                if not any(TABULAR_LINE_RE.search(x) for x in olds + news):
                    out.append(diff_line("\n".join(olds), "\n".join(news)))
                else:
                    for line in olds:
                        if line.strip() and not TABULAR_LINE_RE.search(line):
                            out.append(mark_run("DIFdel", atomise(line)))
                    out.extend(news)
    return "\n".join(out)


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
        pat = "\\DIFdel{\\" + name + "{"
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
    # anything left here is genuinely unpaired.
    for name in REPAIR_CMDS:
        pat = "\\DIFadd{\\" + name + "{"
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
    return text, fixed


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
